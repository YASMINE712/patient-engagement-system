"""Explicit data contracts, conservative feature selection, and quality reports."""
import hashlib
import math
import pandas as pd

PIPELINE_VERSION = '1.0.0'
HEARTSTEPS_FEATURES = ['age', 'gender', 'planned_slot', 'study_day', 'steps_previous_30m']
KEYS = ['participant_id', 'decision_id']
USER_COLUMNS = ['user.index', 'age', 'gender', 'intake.survey.utime']
DECISION_COLUMNS = [
    'user.index', 'decision.index', 'sugg.select.utime', 'sugg.decision.utime',
    'sugg.context.utime', 'sugg.gmtoff', 'sugg.select.slot', 'avail', 'send',
    'send.active', 'send.sedentary', 'jbsteps30pre', 'jbsteps30', 'response', 'dec.temperature',
]
ADVICE_COLUMNS = ['Stress Management', 'Sleep Hygiene', 'Exercise and Physical Activity', 'Diet and Nutrition']
LEGACY_NUMBERS = ['Age', 'Sleep Duration', 'Quality of Sleep', 'Physical Activity Level',
                  'Stress Level', 'Heart Rate', 'Daily Steps']
LEGACY_PROFILE = ['Gender', 'Age', 'Occupation', 'Sleep Duration', 'Quality of Sleep',
                  'Physical Activity Level', 'Stress Level', 'BMI Category', 'Blood Pressure',
                  'Heart Rate', 'Daily Steps', 'Sleep Disorder']


def require_columns(frame, columns, label):
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise ValueError(f'{label}: missing required columns: {missing}')


def numeric(series, label, integer=False, minimum=None, maximum=None, required=False):
    values = pd.to_numeric(series, errors='coerce')
    if (series.notna() & values.isna()).any():
        raise ValueError(f'{label}: nonnumeric values')
    if values.dropna().map(lambda x: not math.isfinite(x)).any():
        raise ValueError(f'{label}: nonfinite values')
    if required and values.isna().any():
        raise ValueError(f'{label}: missing required values')
    if minimum is not None and values.lt(minimum).any():
        raise ValueError(f'{label}: values below {minimum}')
    if maximum is not None and values.gt(maximum).any():
        raise ValueError(f'{label}: values above {maximum}')
    if integer and values.dropna().mod(1).ne(0).any():
        raise ValueError(f'{label}: expected whole numbers')
    return values.astype('Int64' if integer else 'Float64')


def boolean(series, label):
    text = series.astype('string').str.strip().str.lower()
    invalid = text.notna() & ~text.isin(['true', 'false', '1', '0'])
    if invalid.any():
        raise ValueError(f'{label}: invalid boolean value')
    return text.map({'true': True, 'false': False, '1': True, '0': False}).astype('boolean')


def timestamp(series, label, required=False):
    values = pd.to_datetime(series, errors='coerce', utc=True, format='mixed')
    if (series.notna() & values.isna()).any() or (required and values.isna().any()):
        raise ValueError(f'{label}: invalid or missing timestamp')
    return values


def assign_participant_splits(ids, seed=2026):
    users = sorted(set(int(x) for x in ids))
    if len(users) < 3:
        raise ValueError('At least three participants are required for train/validation/test splits')
    ranked = sorted(users, key=lambda user: hashlib.sha256(f'{seed}:{user}'.encode()).hexdigest())
    n_test = max(1, round(len(users) * 0.15))
    n_validation = max(1, round(len(users) * 0.15))
    return {user: ('test' if index < n_test else 'validation' if index < n_test + n_validation else 'train')
            for index, user in enumerate(ranked)}


def clean_heartsteps(users, decisions, seed=2026):
    require_columns(users, USER_COLUMNS, 'users')
    require_columns(decisions, DECISION_COLUMNS, 'suggestions')
    u, d = users[USER_COLUMNS].copy(), decisions[DECISION_COLUMNS].copy()
    u['user.index'] = numeric(u['user.index'], 'user.index', integer=True, minimum=1, required=True)
    d['user.index'] = numeric(d['user.index'], 'user.index', integer=True, minimum=1, required=True)
    d['decision.index'] = numeric(d['decision.index'], 'decision.index', integer=True, minimum=0, required=True)
    if u['user.index'].duplicated().any():
        raise ValueError('users: duplicate participant keys')
    if d.duplicated(['user.index', 'decision.index']).any():
        raise ValueError('suggestions: duplicate participant/decision keys')
    u['age'] = numeric(u['age'], 'age', integer=True, minimum=0, maximum=120, required=True)
    u['gender'] = u['gender'].astype('string').str.strip().str.lower()
    if not u['gender'].isin(['male', 'female', 'transgender']).all():
        raise ValueError('users: unknown or missing gender category')
    u['intake.survey.utime'] = timestamp(u['intake.survey.utime'], 'intake time', required=True)
    merged = d.merge(u, on='user.index', how='left', validate='many_to_one', indicator=True)
    if merged['_merge'].ne('both').any():
        raise ValueError('suggestions: participant is missing from users table')

    out = pd.DataFrame({'participant_id': merged['user.index'], 'decision_id': merged['decision.index']})
    out['scheduled_at_utc'] = timestamp(merged['sugg.select.utime'], 'scheduled time')
    out['decision_at_utc'] = timestamp(merged['sugg.decision.utime'], 'decision time')
    out['context_at_utc'] = timestamp(merged['sugg.context.utime'], 'context time')
    if (out['scheduled_at_utc'] < merged['intake.survey.utime']).any():
        raise ValueError('Intake features recorded after a scheduled decision')
    if (out['context_at_utc'] > out['decision_at_utc']).any():
        raise ValueError('Context timestamp occurs after the observed decision')
    out['age'], out['gender'] = merged['age'], merged['gender']
    out['planned_slot'] = numeric(merged['sugg.select.slot'], 'planned slot', integer=True, minimum=1, maximum=5, required=True)
    first_date = out.groupby('participant_id')['scheduled_at_utc'].transform('min').dt.normalize()
    out['study_day'] = (out['scheduled_at_utc'].dt.normalize() - first_date).dt.days + 1
    out['steps_previous_30m'] = numeric(merged['jbsteps30pre'], 'previous steps', integer=True, minimum=0)
    out['steps_next_30m'] = numeric(merged['jbsteps30'], 'next steps', integer=True, minimum=0)
    out['available'] = boolean(merged['avail'], 'availability')
    if out['available'].isna().any():
        raise ValueError('Availability must be known')
    sent = boolean(merged['send'], 'send')
    active, sedentary = boolean(merged['send.active'], 'send.active'), boolean(merged['send.sedentary'], 'send.sedentary')
    out['notification_sent'] = sent
    out['action'] = pd.Series('unknown', index=out.index, dtype='string')
    no_message = (sent.eq(False) & active.eq(False) & sedentary.eq(False)).fillna(False)
    walking = (sent.eq(True) & active.eq(True) & sedentary.eq(False)).fillna(False)
    interrupt = (sent.eq(True) & active.eq(False) & sedentary.eq(True)).fillna(False)
    out.loc[no_message, 'action'] = 'no_suggestion'
    out.loc[walking, 'action'] = 'walking'
    out.loc[interrupt, 'action'] = 'sedentary_break'
    out['response'] = merged['response'].astype('string')
    known_responses = ['good', 'bad', 'no_response', 'snoozed_for_4_hours', 'snoozed_for_12_hours']
    if (out['response'].notna() & ~out['response'].isin(known_responses)).any():
        raise ValueError('Unexpected response category')
    # No response, no notification, and snoozing are not negative labels.
    out['usefulness_rating'] = out['response'].map({'good': 1, 'bad': 0}).astype('Int64')
    if (out['usefulness_rating'].notna() & ~sent.fillna(False)).any():
        raise ValueError('Usefulness rating exists without a sent notification')
    out['outcome_observed'] = out['steps_next_30m'].notna()
    out['eligible_decision'] = out['available'] & out['action'].ne('unknown') & out['decision_at_utc'].notna() & out['scheduled_at_utc'].notna()
    out['eligible_outcome_analysis'] = out['eligible_decision'] & out['outcome_observed']
    out['source'] = 'heartsteps_v1_observed'
    split_map = assign_participant_splits(out['participant_id'], seed)
    out['split'] = out['participant_id'].map(split_map)
    temperature = numeric(merged['dec.temperature'], 'temperature')
    invalid_temperature = temperature.notna() & ~temperature.between(-90, 60)
    offset = numeric(merged['sugg.gmtoff'], 'GMT offset')
    report = {
        'rows': len(out), 'participants': int(out['participant_id'].nunique()),
        'source_columns': {'users': len(users.columns), 'suggestions': len(decisions.columns)},
        'duplicate_decision_keys': 0,
        'available_decisions': int(out['available'].sum()),
        'eligible_decisions': int(out['eligible_decision'].sum()),
        'eligible_outcome_rows': int(out['eligible_outcome_analysis'].sum()),
        'missing_previous_steps': int(out['steps_previous_30m'].isna().sum()),
        'missing_outcomes': int(out['steps_next_30m'].isna().sum()),
        'missing_decision_timestamps': int(out['decision_at_utc'].isna().sum()),
        'missing_scheduled_timestamps': int(out['scheduled_at_utc'].isna().sum()),
        'available_unknown_actions': int((out['available'] & out['action'].eq('unknown')).sum()),
        'sent_while_unavailable': int((~out['available'] & sent.fillna(False)).sum()),
        'explicit_usefulness_ratings': int(out['usefulness_rating'].notna().sum()),
        'action_counts': {str(k): int(v) for k, v in out['action'].value_counts().items()},
        'invalid_temperature_measurements_excluded_from_features': int(invalid_temperature.sum()),
        'offset_values_exceeding_plausible_minutes': int(offset.abs().gt(14 * 60).sum()),
        'split_participants': {key: int(value) for key, value in out.groupby('split')['participant_id'].nunique().items()},
        'split_rows': {key: int(value) for key, value in out['split'].value_counts().items()},
        'feature_missingness': {key: int(out[key].isna().sum()) for key in HEARTSTEPS_FEATURES},
        'warnings': [
            'Naive source utime strings are interpreted as UTC; no local-time conversion is performed.',
            'GMT offset magnitudes disagree with the documented minute units; offset-derived features are excluded.',
            'Temperature is excluded from this conservative baseline, including out-of-range values.',
            'Missing step outcomes are preserved, not replaced by zero.',
            'Recorded action flags describe delivery, not verified assignment propensities; off-policy evaluation is not enabled.',
            'Study day uses UTC calendar days since the first observed scheduled slot, not travel-adjusted study days.',
        ],
    }
    return out.sort_values(KEYS).reset_index(drop=True), report


def clean_legacy(frame):
    require_columns(frame, ['Person ID'] + LEGACY_PROFILE + ADVICE_COLUMNS, 'legacy wellness')
    clean = frame.copy()
    clean['Person ID'] = numeric(clean['Person ID'], 'Person ID', integer=True, minimum=1, required=True)
    if clean['Person ID'].duplicated().any():
        raise ValueError('Legacy Person ID must be unique')
    for name in LEGACY_NUMBERS:
        clean[name] = numeric(clean[name], name, minimum=0, required=True)
    for name in ['Gender', 'Occupation', 'BMI Category', 'Sleep Disorder'] + ADVICE_COLUMNS:
        clean[name] = clean[name].astype('string').str.strip()
        if clean[name].isna().any() or clean[name].eq('').any():
            raise ValueError(f'Legacy {name}: missing or blank values')
    clean['BMI Category'] = clean['BMI Category'].replace({'Normal Weight': 'Normal'})
    if not clean['BMI Category'].isin(['Underweight', 'Normal', 'Overweight', 'Obese']).all():
        raise ValueError('Legacy unknown BMI category')
    pressure = clean['Blood Pressure'].astype('string').str.extract(r'^\s*(\d+)\s*/\s*(\d+)\s*$')
    if pressure.isna().any().any():
        raise ValueError('Blood Pressure must have systolic/diastolic format')
    clean['systolic'] = numeric(pressure[0], 'systolic', integer=True, minimum=1, required=True)
    clean['diastolic'] = numeric(pressure[1], 'diastolic', integer=True, minimum=1, required=True)
    clean['Blood Pressure'] = clean['systolic'].astype('string') + '/' + clean['diastolic'].astype('string')
    clean['profile_group_id'] = clean[LEGACY_PROFILE].astype(str).apply(
        lambda row: hashlib.sha256('\x1f'.join(row).encode()).hexdigest()[:20], axis=1)
    clean['source'] = 'legacy_wellness_unverified'
    report = {
        'rows': len(clean), 'columns_original': len(frame.columns),
        'unique_profiles': int(clean['profile_group_id'].nunique()),
        'repeated_profile_rows': int(clean['profile_group_id'].duplicated().sum()),
        'profiles_with_differing_advice': int(clean.groupby('profile_group_id')[ADVICE_COLUMNS].nunique().max(axis=1).gt(1).sum()),
        'unique_suggestions': {name: int(clean[name].nunique()) for name in ADVICE_COLUMNS},
        'provenance': 'Original source, recommendation-label method, and redistribution rights are unverified.',
        'note': 'Literal None in Sleep Disorder is a category, not a missing value. Duplicate profiles are retained and grouped.',
    }
    return clean, report
