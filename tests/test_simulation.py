import json
from pathlib import Path
import tempfile
import unittest
from health_friend.simulation.environment import Context, SyntheticEnvironment, eligible_actions, CATALOG
from health_friend.simulation.policies import TabularBandit, ProfilePolicy
from health_friend.simulation.benchmark import demo, run_episode


class SimulationTests(unittest.TestCase):
    def test_reproducible_demo(self):
        self.assertEqual(demo(seed=4, steps=60), demo(seed=4, steps=60))

    def test_context_has_no_hidden_reward(self):
        context = SyntheticEnvironment(1).context()
        self.assertEqual(set(context.__dict__), {'goal', 'budget_minutes', 'preferred_format'})

    def test_eligibility_respects_goal_and_budget(self):
        context = Context('sleep', 5, 'social')
        actions = eligible_actions(context)
        self.assertTrue(actions)
        self.assertTrue(all(action.goal == 'sleep' and action.minutes <= 5 for action in actions))
        env = SyntheticEnvironment(4)
        context = env.context()
        forbidden = next(action for action in CATALOG if action.goal != context.goal)
        with self.assertRaisesRegex(ValueError, 'eligible'):
            env.respond(forbidden)

    def test_feedback_updates_only_observed_action(self):
        policy = TabularBandit(alpha=0.2)
        context = Context('sleep', 20, 'guided')
        action = eligible_actions(context)[0]
        policy.update(context, action, None)
        self.assertEqual(policy.q, {})
        policy.update(context, action, 1)
        self.assertAlmostEqual(policy.q[context.key][action.id], 0.6)
        self.assertEqual(len(policy.q[context.key]), 1)

    def test_propensity_matches_epsilon_greedy(self):
        policy = TabularBandit(seed=5, epsilon=0.2)
        context = Context('sleep', 20, 'guided')
        actions = eligible_actions(context)
        greedy_id = min(action.id for action in actions)
        for _ in range(25):
            chosen, probability = policy.choose(context, actions)
            expected = 0.2 / len(actions) + (0.8 if chosen.id == greedy_id else 0)
            self.assertAlmostEqual(probability, expected)

    def test_frozen_evaluation_does_not_learn(self):
        policy = TabularBandit(epsilon=0)
        run_episode(policy, SyntheticEnvironment(3, horizon=50), 50, learn=False)
        self.assertEqual(policy.q, {})

    def test_save_load_preserves_deterministic_choice(self):
        policy = TabularBandit(epsilon=0)
        context = Context('activity', 20, 'guided')
        action = eligible_actions(context)[1]
        policy.update(context, action, 1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'policy.json'
            policy.save(path)
            restored = TabularBandit.load(path)
            self.assertEqual(restored.choose(context, eligible_actions(context)), policy.choose(context, eligible_actions(context)))
            self.assertEqual(restored.q, policy.q)

    def test_shift_changes_private_response_model(self):
        stationary = SyntheticEnvironment(4, scenario='stationary', horizon=20)
        shifted = SyntheticEnvironment(4, scenario='preference_shift', horizon=20)
        context = stationary.context()
        self.assertEqual(context, shifted.context())
        shifted.step_index = 11
        differences = [stationary.expected_reward(action) != shifted.expected_reward(action) for action in eligible_actions(context)]
        self.assertTrue(any(differences))

    def test_demo_input_bounds(self):
        for kwargs in ({'steps': 0}, {'steps': 1001}, {'seed': -1}, {'scenario': 'unknown'}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                demo(**kwargs)
