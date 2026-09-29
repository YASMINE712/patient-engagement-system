# Implementation plan

Status: the local baseline, source audit, ETL, synthetic environment, policies, evaluation, and Learning Lab are implemented. Reproducible report snapshots and local tests are available. The existing YASMINE712/patient-engagement-system repository is the chosen destination; the updated source is published on main and [merged pull request 1](https://github.com/YASMINE712/patient-engagement-system/pull/1) records the migration. Hosted checks run through GitHub Actions; Docker configuration is provided but unverified on this host.

The steps below record the agreed responsibilities and acceptance criteria. The implemented reward learner is a contextual bandit. Full sequential Q-learning and automatic production promotion remain explicitly outside this version.

## 0. Establish the working baseline

Assistant: organize active files, preserve the original project, create an isolated environment, run portable regression tests, document dependencies, and add CI configuration. Keep the current application working.

User: use the new project folder from now on. No action is required to delete the old copy; keep it as the backup.

Done when: the app imports, its pages and static files respond, and regression tests pass with isolated data.

## 1. Audit sources and design the data contract

Assistant: verify HeartSteps documentation, license and citation; inspect source tables and choose a narrowly defined decision task. Produce a schema, provenance manifest and data-quality report. Audit the old CSV without assuming its added advice is validated.

User: share the original CSV source if known. If unknown, keep it local and do not claim a source or license.

Done when: every field has a documented meaning, source and availability time; downloaded files have hashes; missingness and repeated observations are reported.

## 2. Build ETL

Assistant: implement extraction, type checks, missingness rules, duplicate checks, normalized categories, timestamp handling and reproducible processed outputs. Preserve raw inputs. Join HeartSteps tables using documented identifiers; exclude post-decision features from model input.

User: no coding work required.

Done when: one documented command rebuilds processed data, validation fails clearly for invalid input, and tests cover joins and leakage boundaries.

## 3. Build the synthetic environment

Assistant: create a clearly labeled demo catalog and simulated users with goals, preferences, time constraints and engagement. Generate probabilistic responses, nonresponse, repetition fatigue and configurable preference drift. Keep hidden preferences inaccessible to the learner. Save generator version, configuration and seeds.

User: optionally choose the demo categories and review how the demo is described. Default: preserve the four existing categories as simulation categories, with no clinical-efficacy claims.

Done when: fixed seeds reproduce a run; changed preferences affect rewards; no-response is distinct from negative feedback; simulated and observed data are never silently merged.

## 4. Implement policies

Assistant: compare a random policy, fixed profile matcher and tabular contextual bandit using coarse profile groups and stable suggestion IDs. Use an immediate-reward update for the bandit. Keep exploration confined to the explicitly labeled simulator; the existing app baseline remains deterministic. Log chosen actions and selection probabilities where stochastic policies are used.

Full Q-learning is a separate optional experiment only if actions genuinely change simulated future states and the objective includes delayed rewards. Do not call a static rating loop a validated sequential health intervention.

Done when: reward changes update the intended action, policy save/load works, and tests prevent hidden simulator information from reaching policies.

## 5. Evaluate without promising an improvement

Assistant: use held-out simulated users, fresh seeds and changed scenarios. Report average reward, cumulative regret relative to the simulator's best available action, repetition, action coverage and uncertainty across runs. Include ablations and failures. Fix evaluation scenarios before tuning final candidates.

For HeartSteps: split by participant and/or time according to the stated task. Predictive outcome accuracy does not establish treatment benefit. Any off-policy evaluation needs verified behavior probabilities, supported actions, appropriate estimators and uncertainty; do not turn logged data into an unrestricted simulator with invented outcomes for unobserved actions.

User: no metrics need to be invented. Review the resulting explanation rather than choosing a desired score.

Done when: all comparison tables and figures can be regenerated and any claimed improvement is supported by measurements under explicitly stated conditions.

## 6. Integrate a demo

Assistant: add an explicit Simulation mode, show recommended actions and explanation, visualize learning history, and expose model save/load and feedback logging. Preserve separation between simulated users and real accounts. Add provenance labels to generated outputs.

User: try the demo and report confusing behavior or preferred presentation changes.

Done when: the full ETL-to-policy-to-feedback loop works and end-to-end tests cover it.

## 7. Package for GitHub and the CV

Assistant: finalize README, architecture, setup commands, model/data cards, metrics, limitations, Docker configuration, dependency lock, portable tests and CI. Scan the publishable tree for private files and credentials. Prepare an honest CV bullet based only on completed work.

User: provide a GitHub repository destination when ready and explicitly request publishing. Confirm rights before assigning a license to inherited code or redistributing old data. No credentials should be pasted into chat.

Done when: a fresh checkout reproduces the demo and published experiments without private account data or undocumented local dependencies.

## Intended portfolio claim

Adaptive wellness recommendation prototype with reproducible ETL, analysis of public intervention data, and a synthetic-user benchmark for feedback-driven policies. Simulation improvements are not clinical validation.

## Non-negotiable style rule

No emojis anywhere, including code, comments, documentation, UI text, plots, generated records, filenames and user-facing messages.
