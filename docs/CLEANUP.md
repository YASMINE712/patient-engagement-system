# Cleanup record

The active project is now `my-health-friend`. The original `projetnw/projetnw` folder remains untouched as a recoverable backup, including its Git history.

## Renamed and retained

| Original | Active location |
|---|---|
| app_folder/app.py | health_friend/web.py |
| app_folder/bbl3.py | health_friend/recommendations.py |
| templates (six active pages) | health_friend/templates |
| static/css/main.css | health_friend/static/css/main.css |
| Scientifically_Grounded_Dataset.csv | data/raw/legacy_wellness.csv |
| app_folder/instance/users.db | instance/users.db (private and ignored) |
| app_folder/instance/q_table.json, if present | instance/q_table.json (private and ignored) |

## Excluded from the active folder

- `.env`, `.venv`, `venv`, and `newenv`: old Python environments.
- `__pycache__`: generated cache files.
- `models.py/model1.py` and `rl_model.py/rlmodel.py`: empty files.
- `database.db`: legacy export script and notebook, retained in the backup.
- Root `instance`, `updated_users.db`, `questionnaire_data.csv`, and root `q_table.json`: inactive duplicate or legacy data, retained in the backup.
- `templates/index.html`, `static/js/code.js`, `static/css/style.css`, and empty `static/image/img`: not used by the current routes and templates.
- `.vscode`: machine-specific editor settings.
- Old `.git`: retained with the original project; not imported into the new repository because it tracks environments and may include private data.

## Added

- Clear package and entry-point names.
- Minimal current runtime dependency ranges and an isolated environment.
- Portable regression tests using synthetic legacy database fixtures.
- Git ignore rules for private data, environments, and generated files.
- CI workflow using an explicitly synthetic software-test dataset.
- Project instructions, data provenance notes, and implementation roadmap.

No old files or user records were deleted. New ML experiments have not yet been implemented.
