import json
from pathlib import Path
import tempfile
import unittest
import pandas as pd
from health_friend.data_pipeline.sources import acquire_heartsteps, sha256
from health_friend.data_pipeline.transform import (
    clean_heartsteps, clean_legacy, assign_participant_splits, HEARTSTEPS_FEATURES, ADVICE_COLUMNS,
)


def fixtures():
    users = pd.DataFrame([
        {'user.index': i, 'age': 30 + i, 'gender': 'female', 'intake.survey.utime': '2020-01-01 08:00:00'}
        for i in range(1, 5)
    ])
    decisions = pd.DataFrame([
        {'user.index': i, 'decision.index': j, 'sugg.select.utime': f'2020-01-0{j+2} 10:00:00',
         'sugg.decision.utime': f'2020-01-0{j+2} 10:01:00',
         'sugg.context.utime': f'2020-01-0{j+2} 10:01:00', 'sugg.gmtoff': -14400,
         'sugg.select.slot': 1, 'avail': True, 'send': True, 'send.active': True,
         'send.sedentary': False, 'jbsteps30pre': 12, 'jbsteps30': 50,
         'response': 'good', 'dec.temperature': 20}
        for i in range(1, 5) for j in range(2)
    ])
    return users, decisions


class ETLTests(unittest.TestCase):
    def test_missing_is_not_zero_or_negative(self):
        users, decisions = fixtures()
        decisions.loc[0, 'jbsteps30'] = float('nan')
        decisions.loc[0, 'response'] = 'no_response'
        clean, report = clean_heartsteps(users, decisions)
        self.assertTrue(pd.isna(clean.loc[0, 'steps_next_30m']))
        self.assertTrue(pd.isna(clean.loc[0, 'usefulness_rating']))
        self.assertFalse(clean.loc[0, 'eligible_outcome_analysis'])
        self.assertEqual(report['missing_outcomes'], 1)

    def test_duplicate_and_orphan_keys_fail(self):
        users, decisions = fixtures()
        with self.assertRaisesRegex(ValueError, 'duplicate participant/decision'):
            clean_heartsteps(users, pd.concat([decisions, decisions.iloc[:1]]))
        with self.assertRaisesRegex(ValueError, 'duplicate participant keys'):
            clean_heartsteps(pd.concat([users, users.iloc[:1]]), decisions)
        decisions.loc[0, 'user.index'] = 99
        with self.assertRaisesRegex(ValueError, 'missing from users'):
            clean_heartsteps(users, decisions)

    def test_invalid_numeric_boolean_and_timestamp_fail(self):
        for column, value in [('jbsteps30', -1), ('avail', 'maybe'), ('sugg.context.utime', 'not-a-time')]:
            users, decisions = fixtures()
            decisions[column] = decisions[column].astype(object)
            decisions.loc[0, column] = value
            with self.subTest(column=column), self.assertRaises(ValueError):
                clean_heartsteps(users, decisions)

    def test_future_context_rejected(self):
        users, decisions = fixtures()
        decisions.loc[0, 'sugg.context.utime'] = '2020-02-01 12:00:00'
        with self.assertRaisesRegex(ValueError, 'after the observed decision'):
            clean_heartsteps(users, decisions)

    def test_intake_after_decision_rejected(self):
        users, decisions = fixtures()
        users.loc[0, 'intake.survey.utime'] = '2021-01-01 00:00:00'
        with self.assertRaisesRegex(ValueError, 'Intake features'):
            clean_heartsteps(users, decisions)

    def test_unknown_action_and_unavailable_not_used_for_learning(self):
        users, decisions = fixtures()
        decisions['send.active'] = decisions['send.active'].astype(object)
        decisions.loc[0, 'send.active'] = None
        decisions.loc[1, 'avail'] = False
        clean, report = clean_heartsteps(users, decisions)
        self.assertEqual(clean.loc[0, 'action'], 'unknown')
        self.assertFalse(clean.loc[:1, 'eligible_decision'].any())
        self.assertEqual(report['sent_while_unavailable'], 1)

    def test_group_splits_stable_and_disjoint(self):
        users, decisions = fixtures()
        a, _ = clean_heartsteps(users, decisions)
        b, _ = clean_heartsteps(users.sample(frac=1, random_state=2), decisions.sample(frac=1, random_state=4))
        self.assertTrue(a.equals(b))
        self.assertTrue(a.groupby('participant_id')['split'].nunique().eq(1).all())
        self.assertEqual(set(a['split']), {'train', 'validation', 'test'})

    def test_feature_allowlist_excludes_outcomes(self):
        forbidden = {'action', 'steps_next_30m', 'usefulness_rating', 'response', 'participant_id'}
        self.assertFalse(forbidden.intersection(HEARTSTEPS_FEATURES))
        users, decisions = fixtures()
        decisions['exit.survey.score'] = 100
        clean, _ = clean_heartsteps(users, decisions)
        self.assertNotIn('exit.survey.score', clean.columns)

    def test_temperature_and_offsets_reported(self):
        users, decisions = fixtures()
        decisions.loc[0, 'dec.temperature'] = -1024
        _, report = clean_heartsteps(users, decisions)
        self.assertEqual(report['invalid_temperature_measurements_excluded_from_features'], 1)
        self.assertEqual(report['offset_values_exceeding_plausible_minutes'], 8)

    def test_legacy_normalization_and_none_category(self):
        row = {'Person ID': 1, 'Gender': 'Female', 'Age': 30, 'Occupation': 'Engineer',
               'Sleep Duration': 7, 'Quality of Sleep': 7, 'Physical Activity Level': 40,
               'Stress Level': 5, 'BMI Category': 'Normal Weight', 'Blood Pressure': '120/80',
               'Heart Rate': 70, 'Daily Steps': 6000, 'Sleep Disorder': 'None'}
        row.update({key: 'Sample suggestion' for key in ADVICE_COLUMNS})
        second = dict(row, **{'Person ID': 2, 'BMI Category': 'Normal', 'Stress Management': 'Alternative'})
        clean, report = clean_legacy(pd.DataFrame([row, second]))
        self.assertEqual(clean.loc[0, 'Sleep Disorder'], 'None')
        self.assertEqual(clean.loc[0, 'systolic'], 120)
        self.assertEqual(report['unique_profiles'], 1)
        self.assertEqual(report['profiles_with_differing_advice'], 1)

    def test_source_tampering_detected_without_network(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'data/raw/heartsteps-v1'
            source.mkdir(parents=True)
            file = source / 'users.csv'
            file.write_text('original', encoding='utf-8')
            manifest = {'commit': 'test', 'files': [{'filename': 'users.csv', 'sha256': sha256(file)}]}
            (root / 'data/sources').mkdir()
            (root / 'data/sources/heartsteps-v1.json').write_text(json.dumps(manifest), encoding='utf-8')
            acquire_heartsteps(root)
            file.write_text('modified', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'modified'):
                acquire_heartsteps(root)
