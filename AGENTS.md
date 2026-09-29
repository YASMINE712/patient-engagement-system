# Project instructions

- Never use emojis in messages, code, comments, documentation, UI text, filenames, or generated content. This is an explicit user requirement.
- Keep real observations and synthetic data separate. Label generated records with source, seed, and generator version.
- Do not present simulated improvements as clinical outcomes.
- Preserve local databases and secrets; never commit them or generated environment folders.
- Keep training and evaluation separated by participant and time where appropriate. Do not give simulator hidden reward parameters to a learner.
- Run the relevant tests after changes. Use isolated test databases rather than the local user's database.
- Mark planned work as planned until implementation and evaluation are complete.
