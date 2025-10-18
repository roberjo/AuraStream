<!--
Thank you for your contribution! Please fill out the sections below.
-->

## Summary
Brief description of the change.

## Related issue
Closes # (if applicable)

## What changed
- Bullet list of changes

## How to test locally
- Setup steps
- Commands to run:
  ```bash
  # create venv, install deps
  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  pip install -r requirements-dev.txt

  # run linters
  pre-commit run --all-files
  flake8 src

  # run tests
  pytest -q
  ```

## Checklist
- [ ] Tests added / updated
- [ ] Linting passes (pre-commit)
- [ ] Documentation updated (README or docs/)
- [ ] No secrets committed

## Notes
Any additional notes for reviewers.