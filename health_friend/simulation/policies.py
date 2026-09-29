"""Baseline policies and immediate-reward action values (gamma=0 bandit)."""
import json
from pathlib import Path
import random
from .environment import ACTION_IDS


class RandomPolicy:
    name = 'random'

    def __init__(self, seed=0):
        self.rng = random.Random(seed)

    def choose(self, context, actions):
        return self.rng.choice(actions), 1 / len(actions)

    def update(self, context, action, feedback):
        pass


class ProfilePolicy:
    name = 'profile_matcher'

    def choose(self, context, actions):
        chosen = min(actions, key=lambda action: (action.format != context.preferred_format, action.minutes, action.id))
        return chosen, 1.0

    def update(self, context, action, feedback):
        pass


class TabularBandit:
    name = 'tabular_bandit'
    schema_version = 1

    def __init__(self, seed=0, epsilon=0.1, alpha=0.15):
        if not 0 <= epsilon <= 1 or not 0 < alpha <= 1:
            raise ValueError('Invalid bandit parameters')
        self.rng = random.Random(seed)
        self.epsilon, self.alpha, self.q, self.counts = epsilon, alpha, {}, {}

    def choose(self, context, actions):
        if not actions:
            raise ValueError('No eligible actions')
        scores = self.q.get(context.key, {})
        best = min(actions, key=lambda action: (-scores.get(action.id, 0.5), action.id))
        chosen = self.rng.choice(actions) if self.rng.random() < self.epsilon else best
        probability = self.epsilon / len(actions) + (1 - self.epsilon if chosen.id == best.id else 0)
        return chosen, probability

    def update(self, context, action, feedback):
        if feedback is None:
            return
        if feedback not in (0, 1) or action.id not in ACTION_IDS:
            raise ValueError('Invalid feedback or action')
        scores = self.q.setdefault(context.key, {})
        counts = self.counts.setdefault(context.key, {})
        old = scores.get(action.id, 0.5)
        scores[action.id] = old + self.alpha * (feedback - old)
        counts[action.id] = counts.get(action.id, 0) + 1

    def payload(self):
        return {'schema_version': self.schema_version, 'policy': self.name, 'alpha': self.alpha,
                'epsilon': self.epsilon, 'q': self.q, 'counts': self.counts,
                'source': 'synthetic_benchmark', 'reward_type': 'simulated_usefulness'}

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.payload(), indent=2, sort_keys=True) + '\n', encoding='utf-8')

    @classmethod
    def load(cls, path, seed=0, epsilon=0):
        stored = json.loads(Path(path).read_text(encoding='utf-8'))
        if stored.get('schema_version') != cls.schema_version or stored.get('source') != 'synthetic_benchmark':
            raise ValueError('Unsupported policy artifact')
        policy = cls(seed=seed, epsilon=epsilon, alpha=stored['alpha'])
        for scores in stored['q'].values():
            if any(action not in ACTION_IDS or not 0 <= value <= 1 for action, value in scores.items()):
                raise ValueError('Invalid stored Q-values')
        policy.q, policy.counts = stored['q'], stored['counts']
        return policy
