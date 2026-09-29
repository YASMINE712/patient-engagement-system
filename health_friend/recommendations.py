import json
import os
import math
from pathlib import Path
from threading import RLock
import pandas as pd

alpha, gamma = 0.1, 0.9
POLICY_VERSION = 2
PROJECT_ROOT = Path(__file__).resolve().parents[1]
data = pd.read_csv(PROJECT_ROOT / 'data' / 'raw' / 'legacy_wellness.csv', keep_default_na=False)
recommendation_columns = ['Stress Management', 'Sleep Hygiene', 'Exercise and Physical Activity', 'Diet and Nutrition']
q_path = Path(os.environ.get('Q_TABLE_PATH', str(PROJECT_ROOT / 'instance' / 'q_table.json')))
lock = RLock()

def load_q_table():
    if not q_path.exists():
        return {}
    stored = json.loads(q_path.read_text(encoding='utf-8'))
    return {state: {int(action): float(score) for action, score in actions.items()}
            for state, actions in stored.items()}

q_table = load_q_table()

def preprocess_state(user_data):
    return (user_data['Age'], 1 if user_data['Gender'] == 'Male' else 0,
            {'Underweight': 0, 'Normal': 1, 'Normal Weight': 1, 'Overweight': 2, 'Obese': 3}[user_data['BMI Category']],
            user_data['Stress Level'], user_data['Sleep Duration'])

def profile_similarity(state, row):
    """Equal-weight profile similarity; numeric differences use fixed scales.

    These are transparent engineering defaults, not clinical weights.
    """
    profile = preprocess_state(row)
    differences = (
        min(abs(float(state[0]) - float(profile[0])) / 82.0, 1.0),
        float(state[1] != profile[1]),
        min(abs(float(state[2]) - float(profile[2])) / 3.0, 1.0),
        min(abs(float(state[3]) - float(profile[3])) / 9.0, 1.0),
        min(abs(float(state[4]) - float(profile[4])) / 6.0, 1.0),
    )
    return 1.0 - sum(differences) / len(differences)

def choose_action(state, candidates=None):
    candidates = list(data.index if candidates is None else candidates)
    if not candidates:
        raise ValueError('No recommendation candidates available')
    with lock:
        scores = q_table.get(str(tuple(state)), {})
        def ranking(action):
            similarity = profile_similarity(state, data.iloc[int(action)])
            # Bound feedback influence so old Q-values cannot dominate matching.
            learned_bonus = 0.25 * math.tanh(scores.get(int(action), 0.0))
            return (similarity + learned_bonus, similarity, -int(action))
        return int(max(candidates, key=ranking))

def generate_recommendations(user_data, return_actions=False):
    state = preprocess_state(user_data)
    recommendations, actions = {}, {}
    for category in recommendation_columns:
        candidates = list(data.index[data[category].notna()])
        recommendations[category], actions[category] = [], []
        for _ in range(2):
            if not candidates:
                break
            action = choose_action(state, candidates)
            text = str(data.iloc[action][category])
            recommendations[category].append(text)
            actions[category].append(action)
            candidates = [i for i in candidates if str(data.iloc[i][category]) != text]
    return (recommendations, actions) if return_actions else recommendations

def update_q_table(state, action, reward, next_state):
    if action not in data.index:
        raise ValueError('Unknown recommendation action')
    with lock:
        state_key, next_key = str(tuple(state)), str(tuple(next_state))
        scores = q_table.setdefault(state_key, {})
        next_scores = q_table.get(next_key, {})
        best_next = max(next_scores.get(int(i), 0.0) for i in data.index)
        old = scores.get(action, 0.0)
        scores[action] = old + alpha * (reward + gamma * best_next - old)
        q_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = q_path.with_suffix('.tmp')
        temporary.write_text(json.dumps(q_table), encoding='utf-8')
        temporary.replace(q_path)
