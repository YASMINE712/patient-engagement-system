import os
from pathlib import Path
import sys
import uuid
import sqlite3
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pandas

temporary = ROOT / '.test-runs' / uuid.uuid4().hex
temporary.mkdir(parents=True)
os.environ['DATABASE_URL'] = 'sqlite:///' + (temporary / 'test.db').as_posix()
os.environ['Q_TABLE_PATH'] = str(temporary / 'q_table.json')
os.environ['SECRET_KEY'] = 'isolated-test-key'
# A synthetic legacy record tests preservation without reading private data.
with sqlite3.connect(temporary / 'test.db') as connection:
    connection.execute('CREATE TABLE questionnaire (id INTEGER PRIMARY KEY, legacy_note TEXT)')
    connection.execute("INSERT INTO questionnaire VALUES (1, 'synthetic legacy fixture')")
connection.close()
legacy_count = 1
from health_friend import web
from health_friend import recommendations as engine
web.app.config.update(TESTING=True)

def tearDownModule():
    with web.app.app_context():
        web.db.session.remove()
        web.db.engine.dispose()
    # Delete only explicitly created test files inside this run's workspace.
    for name in ('test.db', 'test.db-shm', 'test.db-wal', 'test.db-journal', 'q_table.json'):
        (temporary / name).unlink(missing_ok=True)
    temporary.rmdir()

class RegressionTests(unittest.TestCase):
    def setUp(self):
        with web.app.app_context():
            web.db.drop_all()
            web.db.create_all()
        engine.q_table.clear()
        self.client = web.app.test_client()
        self.register(self.client, 'first')
        self.form = dict(gender='Female', age='29', occupation='Engineer',
                         sleep_duration='7', quality_of_sleep='7', physical_activity_level='40',
                         stress_level='5', bmi_category='Normal', blood_pressure='120/80',
                         heart_rate='70', daily_steps='6000', sleep_disorder='None')

    def register(self, client, name):
        self.assertEqual(client.post('/signup', data=dict(username=name, email=name+'@example.com', password='test-password')).status_code, 302)
        self.assertEqual(client.post('/login', data=dict(username=name, password='test-password')).status_code, 302)

    def submit(self, client=None):
        client = client or self.client
        response = client.post('/questionnaire', data=self.form, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        return response

    def test_questionnaire_saved_and_displayed(self):
        response = self.submit()
        self.assertIn(b'Your Recommendations', response.data)
        with web.app.app_context():
            record = web.Questionnaire.query.one()
            self.assertEqual(record.occupation, 'Engineer')
            self.assertEqual(record.daily_steps, 6000)
            self.assertEqual(record.sleep_duration, 7)
        response = self.client.get('/your-data')
        self.assertIn(b'Engineer', response.data)
        self.assertEqual(response.data.count(b'<!DOCTYPE html>'), 1)

    def test_feedback_targets_displayed_actions_and_persists(self):
        self.submit()
        with self.client.session_transaction() as session:
            context = session['recommendation_context']
        ratings = {f'feedback[{category}][{index}]': '1'
                   for category, actions in context['actions'].items()
                   for index, action in enumerate(actions)}
        self.assertEqual(self.client.post('/feedback', data=ratings).status_code, 302)
        expected = {action for actions in context['actions'].values() for action in actions}
        scores = engine.q_table[str(tuple(context['state']))]
        self.assertEqual(set(scores), expected)
        self.assertTrue(all(score > 0 for score in scores.values()))
        self.assertEqual(engine.load_q_table(), engine.q_table)
        with self.client.session_transaction() as session:
            self.assertNotIn('recommendation_context', session)

    def test_learned_choice_controls_recommendations(self):
        user = {'Age': 29, 'Gender': 'Female', 'BMI Category': 'Normal', 'Stress Level': 5, 'Sleep Duration': 7.0}
        fixture = pandas.DataFrame([
            dict(user, **{category: f'Suggestion {i} for {category}' for category in engine.recommendation_columns})
            for i in range(3)
        ])
        engine.q_table[str(engine.preprocess_state(user))] = {1: 1.0}
        with patch.object(engine, 'data', fixture):
            recommendations, actions = engine.generate_recommendations(user, return_actions=True)
        for category in engine.recommendation_columns:
            self.assertEqual(actions[category][0], 1)
            self.assertEqual(recommendations[category][0], fixture.iloc[1][category])
            self.assertEqual(len(set(recommendations[category])), 2)

    def test_cold_start_matches_profile_and_is_repeatable(self):
        fixture = pandas.DataFrame([
            {'Age': 25, 'Gender': 'Female', 'BMI Category': 'Normal', 'Stress Level': 3, 'Sleep Duration': 8},
            {'Age': 60, 'Gender': 'Male', 'BMI Category': 'Obese', 'Stress Level': 9, 'Sleep Duration': 4},
        ])
        with patch.object(engine, 'data', fixture):
            for index, row in fixture.iterrows():
                state = engine.preprocess_state(row)
                self.assertEqual([engine.choose_action(state) for _ in range(10)], [index] * 10)
            self.assertEqual(engine.choose_action(engine.preprocess_state(fixture.iloc[0]), [1]), 1)

    def test_negative_feedback_changes_equal_match_ranking(self):
        row = {'Age': 29, 'Gender': 'Female', 'BMI Category': 'Normal', 'Stress Level': 5, 'Sleep Duration': 7.0}
        state = engine.preprocess_state(row)
        with patch.object(engine, 'data', pandas.DataFrame([row, row])):
            self.assertEqual(engine.choose_action(state, [1, 0]), 0)
            engine.update_q_table(state, 0, -1, state)
            self.assertEqual(engine.choose_action(state), 1)

    def test_real_dataset_is_deterministic_and_bmi_alias_supported(self):
        user = {'Age': 29, 'Gender': 'Female', 'BMI Category': 'Normal', 'Stress Level': 5, 'Sleep Duration': 7.0}
        first = engine.generate_recommendations(user, return_actions=True)
        self.assertEqual(first, engine.generate_recommendations(user, return_actions=True))
        alias = dict(user, **{'BMI Category': 'Normal Weight'})
        self.assertEqual(engine.preprocess_state(user), engine.preprocess_state(alias))

    def test_old_session_recommendations_refreshed(self):
        self.submit()
        with self.client.session_transaction() as session:
            context = dict(session['recommendation_context'])
            context.pop('policy_version')
            session['recommendation_context'] = context
        self.assertEqual(self.client.get('/thank-you').status_code, 200)
        with self.client.session_transaction() as session:
            self.assertEqual(session['recommendation_context']['policy_version'], engine.POLICY_VERSION)

    def test_user_isolation(self):
        self.submit()
        with self.client.session_transaction() as session:
            original = session['recommendation_context']
        other = web.app.test_client()
        self.register(other, 'second')
        self.assertNotIn(b'Engineer', other.get('/your-data').data)
        self.assertEqual(other.get('/thank-you').status_code, 302)
        self.form['age'] = '40'
        self.submit(other)
        with self.client.session_transaction() as session:
            self.assertEqual(session['recommendation_context'], original)
        self.client.get('/thank-you')
        with self.client.session_transaction() as session:
            self.assertEqual(session['recommendation_context'], original)

    def test_missing_data_and_authentication(self):
        self.assertEqual(self.client.get('/thank-you').status_code, 302)
        self.assertIn(b'not submitted', self.client.get('/your-data').data)
        anonymous = web.app.test_client()
        for path in ['/questionnaire', '/thank-you', '/your-data']:
            self.assertEqual(anonymous.get(path).status_code, 302)
        self.assertEqual(anonymous.post('/feedback').status_code, 302)

    def test_invalid_input_and_feedback_do_not_write(self):
        self.form['sleep_duration'] = 'nan'
        self.assertEqual(self.client.post('/questionnaire', data=self.form).status_code, 400)
        with web.app.app_context():
            self.assertEqual(web.Questionnaire.query.count(), 0)
        self.form['sleep_duration'] = '7'
        self.submit()
        self.assertEqual(self.client.post('/feedback', data={}).status_code, 400)
        self.assertEqual(engine.q_table, {})

    def test_static_and_logout(self):
        with self.client.get('/static/css/main.css') as response:
            self.assertEqual(response.status_code, 200)
        self.submit()
        self.client.get('/logout')
        with self.client.session_transaction() as session:
            self.assertNotIn('user_id', session)
            self.assertNotIn('recommendation_context', session)

    def test_legacy_records_preserved(self):
        self.submit()
        with sqlite3.connect(temporary / 'test.db') as connection:
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM questionnaire').fetchone()[0], legacy_count)
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM health_questionnaire').fetchone()[0], 1)
        connection.close()

    def test_learning_lab_and_simulation_api(self):
        response = self.client.get('/simulation')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Your own pace.', response.data)
        self.assertNotIn(b'All sandbox users and rewards are simulated', response.data)
        research = self.client.get('/research')
        self.assertEqual(research.status_code, 200)
        self.assertIn(b'Reproducible benchmark', research.data)
        payload = {'seed': 12, 'steps': 30, 'scenario': 'stationary'}
        first = self.client.post('/simulation/run', json=payload)
        second = self.client.post('/simulation/run', json=payload)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json, second.json)
        self.assertEqual(first.json['source'], 'synthetic_simulator')

    def test_simulation_bounds_and_report_allowlist(self):
        for payload in ({'steps': 100000}, {'seed': True}, {'scenario': 'unknown'}, {'steps': '30'}):
            self.assertEqual(self.client.post('/simulation/run', json=payload).status_code, 400)
        self.assertEqual(self.client.post('/simulation/run', data='not JSON').status_code, 400)
        self.assertEqual(self.client.get('/simulation/report/users.db').status_code, 404)

if __name__ == '__main__':
    unittest.main(verbosity=2)
