# Contributing to AuraStream

Thanks for your interest in contributing! This document explains how to get the project running locally, how to run tests and linters, and the preferred workflow for issues and pull requests.

## Code of conduct
Please follow common courtesy and respect. If you'd like to add a formal Code of Conduct, we can add a CODE_OF_CONDUCT.md.

## Development setup

1. Clone the repo:
   ```bash
   git clone https://github.com/roberjo/AuraStream.git
   cd AuraStream
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # POSIX
   .venv\Scripts\activate      # Windows
   ```

3. Install runtime and dev dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. Install pre-commit hooks:
   ```bash
   pre-commit install
   pre-commit run --all-files
   ```

## Running tests

- Run the unit tests:
  ```bash
  pytest -q
  ```
- Run the tests with coverage:
  ```bash
  coverage run -m pytest
  coverage report
  ```

If the repository lacks tests for a particular module, please add tests under `tests/` following the existing naming pattern.

## Linting and formatting

- flake8 is configured. Run:
  ```bash
  flake8 src
  ```
- pre-commit will run configured linters and formatters automatically on commit.

## Working on issues & pull requests

1. Fork the repository and create a feature branch:
   ```bash
   git checkout -b feat/my-feature
   ```

2. Make small, focused commits with clear messages.

3. Ensure all tests pass and linters are green:
   ```bash
   pre-commit run --all-files
   pytest
   flake8 src
   ```

4. Push your branch and open a pull request against `main`. In the PR description, include:
   - What the change is and why it's needed
   - How to run and test the change locally
   - Any design decisions or trade-offs

### PR checklist (maintainers/contributors)
- [ ] Tests added or updated
- [ ] Linting passes (pre-commit)
- [ ] Documentation is updated (README or docs/)
- [ ] No secrets or credentials included

## Local SAM / AWS testing
If you use AWS SAM for local testing, install `aws-sam-cli` and follow the README steps for running Lambdas locally (if applicable). Avoid committing local AWS credentials; use environment variables or the AWS CLI credential store.

## Questions
If you're unsure about any changes or need help writing tests, open an issue and tag it `help-wanted`.