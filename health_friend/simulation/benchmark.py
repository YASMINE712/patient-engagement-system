"""Reproducible comparisons with independent users and explicit simulation labels."""
import argparse
import copy
import csv
import json
import math
from pathlib import Path
import statistics
from .environment import SyntheticEnvironment, eligible_actions, catalog_records, GENERATOR_VERSION
from .policies import RandomPolicy, ProfilePolicy, TabularBandit

SCENARIOS = ('stationary', 'preference_shift', 'high_nonresponse')


def run_episode(policy, environment, steps, learn=True, keep_log=False):
    total, expected, regret, observed, positive, repeats = 0, 0.0, 0.0, 0, 0, 0
    actions_seen, records, curve = set(), [], []
    for index in range(steps):
        context = environment.context()
        action, propensity = policy.choose(context, eligible_actions(context))
        result = environment.respond(action)
        if learn:
            policy.update(context, action, result['feedback'])
        total += result['evaluation_reward']
        expected += result['expected_reward']
        regret += result['oracle_expected_reward'] - result['expected_reward']
        repeats += result['repeated_in_last_five']
        observed += result['feedback'] is not None
        positive += result['feedback'] == 1
        actions_seen.add(action.id)
        if keep_log:
            records.append({'step': index + 1, 'participant': result['participant'],
                            'context': context.key, 'action_id': action.id,
                            'selection_probability': propensity, 'feedback': result['feedback'],
                            'source': 'synthetic_simulator', 'generator_version': GENERATOR_VERSION})
        if (index + 1) % max(1, steps // 50) == 0 or index + 1 == steps:
            curve.append({'step': index + 1, 'mean_reward': total / (index + 1),
                          'mean_expected_reward': expected / (index + 1), 'cumulative_regret': regret})
    metrics = {'mean_reward': total / steps, 'mean_expected_reward': expected / steps,
               'cumulative_regret': regret, 'feedback_count': observed,
               'positive_feedback_rate': positive / observed if observed else None,
               'repeat_rate': repeats / steps, 'actions_seen': len(actions_seen)}
    return {'metrics': metrics, 'curve': curve, 'interactions': records}


def demo(seed=2026, steps=300, scenario='stationary'):
    if not isinstance(seed, int) or not 0 <= seed <= 2**31 - 1 or not isinstance(steps, int) or not 20 <= steps <= 1000:
        raise ValueError('Use a seed from 0 to 2147483647 and 20 to 1000 interactions')
    results = {}
    for policy in (RandomPolicy(seed + 1), ProfilePolicy(), TabularBandit(seed + 2)):
        result = run_episode(policy, SyntheticEnvironment(seed, users=12, scenario=scenario, horizon=steps), steps)
        results[policy.name] = {'metrics': result['metrics'], 'curve': result['curve']}
        if isinstance(policy, TabularBandit):
            results[policy.name]['q_table'] = policy.q
    return {'source': 'synthetic_simulator', 'generator_version': GENERATOR_VERSION,
            'seed': seed, 'steps': steps, 'scenario': scenario, 'results': results}


def benchmark(root, seeds=(11, 22, 33, 44, 55), train_steps=8000, evaluation_steps=2000):
    root = Path(root)
    output = root / 'reports/generated'
    output.mkdir(parents=True, exist_ok=True)
    synthetic = root / 'data/synthetic'
    synthetic.mkdir(parents=True, exist_ok=True)
    (synthetic / 'catalog.json').write_text(json.dumps(catalog_records(), indent=2) + '\n', encoding='utf-8')
    rows, selected_alphas = [], []
    for seed in seeds:
        candidates = []
        # Hyperparameter selection uses validation users only.
        for alpha in (0.05, 0.15):
            policy = TabularBandit(seed, alpha=alpha)
            training = run_episode(policy, SyntheticEnvironment(seed, users=200, horizon=train_steps), train_steps, keep_log=alpha == 0.05)
            if alpha == 0.05:
                path = synthetic / f'training_interactions_seed_{seed}.csv'
                with path.open('w', newline='', encoding='utf-8') as stream:
                    records = training['interactions']
                    writer = csv.DictWriter(stream, fieldnames=list(records[0]) + ['seed', 'split'])
                    writer.writeheader()
                    writer.writerows(dict(record, seed=seed, split='train') for record in records)
            frozen = copy.deepcopy(policy)
            frozen.epsilon = 0
            validation = run_episode(frozen, SyntheticEnvironment(seed + 10000, users=60, horizon=evaluation_steps), evaluation_steps, learn=False)
            candidates.append((validation['metrics']['mean_reward'], alpha, policy))
        _, selected_alpha, trained = max(candidates, key=lambda item: (item[0], -item[1]))
        selected_alphas.append({'seed': seed, 'alpha': selected_alpha})
        trained.save(root / 'artifacts' / f'bandit_seed_{seed}.json')
        for scenario in SCENARIOS:
            for mode in ('frozen', 'online_adaptation'):
                adaptive = copy.deepcopy(trained)
                adaptive.epsilon = 0 if mode == 'frozen' else 0.1
                for policy in (RandomPolicy(seed + 3), ProfilePolicy(), adaptive):
                    environment = SyntheticEnvironment(seed + 20000, users=60, scenario=scenario, horizon=evaluation_steps)
                    result = run_episode(policy, environment, evaluation_steps, learn=mode == 'online_adaptation')
                    rows.append({'seed': seed, 'scenario': scenario, 'mode': mode, 'policy': policy.name, **result['metrics']})
    aggregates = []
    for scenario in SCENARIOS:
        for mode in ('frozen', 'online_adaptation'):
            for name in ('random', 'profile_matcher', 'tabular_bandit'):
                group = [row for row in rows if (row['scenario'], row['mode'], row['policy']) == (scenario, mode, name)]
                values = [row['mean_reward'] for row in group]
                aggregates.append({'scenario': scenario, 'mode': mode, 'policy': name,
                                   'mean_reward': statistics.mean(values),
                                   'reward_sd_across_seeds': statistics.stdev(values) if len(values) > 1 else 0,
                                   'mean_cumulative_regret': statistics.mean(row['cumulative_regret'] for row in group)})
    report = {'source': 'synthetic_simulator', 'generator_version': GENERATOR_VERSION,
              'config': {'seeds': list(seeds), 'train_steps': train_steps, 'evaluation_steps': evaluation_steps,
                         'train_users': 200, 'validation_users': 60, 'test_users': 60,
                         'validation_seed_offset': 10000, 'test_seed_offset': 20000,
                         'alpha_candidates': [0.05, 0.15], 'training_epsilon': 0.1},
              'selected_alphas': selected_alphas, 'aggregates': aggregates, 'runs': rows}
    (output / 'simulation_benchmark.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    with (output / 'simulation_runs.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    lines = ['# Synthetic recommendation benchmark', '',
             'All users, response probabilities and outcomes in this report are simulated. No clinical effectiveness is measured.', '',
             '| Scenario | Evaluation mode | Policy | Mean reward | SD across seeds | Mean cumulative regret |',
             '|---|---|---|---:|---:|---:|']
    for row in aggregates:
        lines.append(f"| {row['scenario']} | {row['mode']} | {row['policy']} | {row['mean_reward']:.4f} | {row['reward_sd_across_seeds']:.4f} | {row['mean_cumulative_regret']:.2f} |")
    lines += ['', '## Protocol', '',
              '- Train and validation environments use different seeds and newly generated people. Test uses a third seed range.',
              '- Alpha is chosen using validation reward; test scenarios and seeds are fixed before comparison.',
              '- Frozen mode does not update on test responses. Online adaptation is a separate experiment where each prediction precedes its feedback update.',
              '- The simulator hides individual response preferences from the learner. Regret is against the best immediate expected action for the current history, not a long-term optimal policy.',
              '- Missing feedback causes no Q update. Evaluation-only utility is retained by the runner, never passed to the learner.',
              '- Reward SD measures variation across simulation seeds; it is not a clinical confidence interval.',
              '- Repeated suggestions influence future response probabilities, so different policies can produce different histories.',
              '- The strongest result need not come from the learned policy. This benchmark is intended to expose both gains and failures.',
              '- The saved interaction CSVs come from the alpha=0.05 training runs; per-seed selected policy artifacts may use another alpha.',
              '- Catalog content is a set of synthetic placeholders. No observed HeartSteps records were mixed into this experiment.']
    (output / 'SIMULATION_BENCHMARK.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--quick', action='store_true', help='Small smoke run; not the full benchmark')
    args = parser.parse_args()
    report = benchmark(args.root, seeds=(11, 22) if args.quick else (11, 22, 33, 44, 55),
                       train_steps=400 if args.quick else 8000, evaluation_steps=200 if args.quick else 2000)
    print(json.dumps(report['aggregates'], indent=2))


if __name__ == '__main__':
    main()
