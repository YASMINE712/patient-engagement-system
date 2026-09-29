"""Seeded user simulator with private response parameters."""
from collections import deque
from dataclasses import asdict, dataclass
import random

GENERATOR_VERSION = '1.0.0'
GOALS = ('stress', 'sleep', 'activity', 'nutrition')
FORMATS = ('guided', 'self_directed', 'social')


@dataclass(frozen=True)
class Action:
    id: str
    goal: str
    format: str
    minutes: int
    text: str


CATALOG = tuple(
    Action(f'{goal}_{style}', goal, style, 15 if style == 'social' else 5,
           f'Synthetic demo: explore a {style.replace("_", " ")} {goal} planning activity.')
    for goal in GOALS for style in FORMATS
)
ACTION_IDS = {action.id for action in CATALOG}


@dataclass(frozen=True)
class Context:
    goal: str
    budget_minutes: int
    preferred_format: str

    @property
    def key(self):
        return f'{self.goal}|{self.budget_minutes}|{self.preferred_format}'


def eligible_actions(context):
    return tuple(action for action in CATALOG if action.goal == context.goal and action.minutes <= context.budget_minutes)


class SyntheticEnvironment:
    """Only context and observed feedback are passed to policies by the runner.

    Response probabilities and oracle values exist solely for benchmark scoring.
    They are a stated generative assumption, not evidence about health behavior.
    """
    def __init__(self, seed, users=60, scenario='stationary', horizon=2000):
        if users < 1 or horizon < 1 or scenario not in ('stationary', 'preference_shift', 'high_nonresponse'):
            raise ValueError('Invalid simulator configuration')
        self.rng = random.Random(seed)
        self.scenario, self.horizon, self.step_index = scenario, horizon, 0
        self.contexts, self._hidden_formats, self._biases, self._history = [], [], [], []
        for _ in range(users):
            goal, preferred = self.rng.choice(GOALS), self.rng.choice(FORMATS)
            self.contexts.append(Context(goal, self.rng.choice((5, 20)), preferred))
            # Individual behavior is not always identical to stated preference.
            hidden = preferred if self.rng.random() < 0.65 else self.rng.choice(FORMATS)
            self._hidden_formats.append(hidden)
            self._biases.append(self.rng.uniform(-0.08, 0.08))
            self._history.append(deque(maxlen=5))
        self._current_user = None

    def context(self):
        if self._current_user is None:
            self._current_user = self.rng.randrange(len(self.contexts))
        return self.contexts[self._current_user]

    def expected_reward(self, action):
        context = self.context()
        if action not in eligible_actions(context):
            raise ValueError('Action is not eligible for this context')
        user = self._current_user
        preferred = self._hidden_formats[user]
        if self.scenario == 'preference_shift' and self.step_index >= self.horizon // 2:
            preferred = FORMATS[(FORMATS.index(preferred) + 1) % len(FORMATS)]
        fatigue = 0.055 * sum(item == action.id for item in self._history[user])
        probability = 0.40 + 0.36 * (action.format == preferred) + self._biases[user] - fatigue
        return max(0.03, min(0.97, probability))

    def respond(self, action):
        probability = self.expected_reward(action)
        oracle = max(self.expected_reward(candidate) for candidate in eligible_actions(self.context()))
        utility = int(self.rng.random() < probability)
        response_rate = 0.45 if self.scenario == 'high_nonresponse' else 0.85
        feedback = utility if self.rng.random() < response_rate else None
        user = self._current_user
        self._history[user].append(action.id)
        self.step_index += 1
        self._current_user = None
        # The runner strips oracle/evaluation fields before updating the learner.
        return {'feedback': feedback, 'evaluation_reward': utility,
                'expected_reward': probability, 'oracle_expected_reward': oracle,
                'participant': user, 'repeated_in_last_five': self._history[user].count(action.id) > 1}


def catalog_records():
    return [dict(asdict(action), source='synthetic_demo_catalog', review_status='not_clinically_reviewed',
                 generator_version=GENERATOR_VERSION) for action in CATALOG]
