import os
import pandas as pd
import random
import json
alpha = 0.1  # Learning rate (0 < alpha ≤ 1)
gamma = 0.9  # Discount factor (0 ≤ gamma ≤ 1)
epsilon = 0.3  # Increase exploration probability

# Load dataset and initialize parameters
dataset_path = os.path.join(os.path.dirname(__file__), "Scientifically_Grounded_Dataset.csv")
data = pd.read_csv(dataset_path)

recommendation_columns = ['Stress Management', 'Sleep Hygiene', 'Exercise and Physical Activity', 'Diet and Nutrition']

# Q-table (can be loaded or updated dynamically)
q_table = {}

def preprocess_state(user_data):
    """
    Converts user data into a state representation for the RL agent.
    """
    state = [
        user_data['Age'],
        1 if user_data['Gender'] == 'Male' else 0,
        {'Underweight': 0, 'Normal': 1, 'Overweight': 2, 'Obese': 3}[user_data['BMI Category']],
        user_data['Stress Level'],
        user_data['Sleep Duration']
    ]
    return tuple(state)

def choose_action(state):
    """
    Chooses an action based on the current state using an epsilon-greedy policy.
    """
    state_key = str(state)
    if random.uniform(0, 1) < epsilon:  # Explore
        return random.choice(data.index)
    else:  # Exploit
        if state_key in q_table:
            return max(q_table[state_key], key=q_table[state_key].get)
        else:
            return random.choice(data.index)

def preprocess_state(user_data):
    """
    Converts user data into a state representation for the RL agent.
    """
    state = [
        user_data['Age'],
        1 if user_data['Gender'] == 'Male' else 0,
        {'Underweight': 0, 'Normal': 1, 'Overweight': 2, 'Obese': 3}[user_data['BMI Category']],
        user_data['Stress Level'],
        user_data['Sleep Duration']
    ]
    return tuple(state)


def generate_recommendations(user_data):
    """
    Generate up to two unique recommendations for each category.
    """
    state = preprocess_state(user_data)
    action_index = choose_action(state)

    # Dictionary to store recommendations for each category
    recommendations = {}

    for category in recommendation_columns:
        # Sample up to 2 unique recommendations from the dataset
        unique_recommendations = data[category].drop_duplicates().sample(n=2, replace=False).tolist()
        recommendations[category] = unique_recommendations

    return recommendations


def update_q_table(state, action, reward, next_state):
    state_key = str(state)
    next_state_key = str(next_state)

    if state_key not in q_table:
        q_table[state_key] = {a: 0 for a in range(len(data))}

    if next_state_key not in q_table:
        q_table[next_state_key] = {a: 0 for a in range(len(data))}

    best_next_action = max(q_table[next_state_key], key=q_table[next_state_key].get)
    q_table[state_key][action] += alpha * (
        reward + gamma * q_table[next_state_key][best_next_action] - q_table[state_key][action]
    )
