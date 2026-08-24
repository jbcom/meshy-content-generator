# Contributing

See the [contribution guide](https://jonbogaty.com/meshy-content-generator/contributing/) for setup, validation, supported change boundaries, and pull-request expectations.

Use Conventional Commit messages. Paid API tests are forbidden by default; exercise pipelines through `--dry-run` or `--fixture-image` instead.

Pull requests and `main` receive SonarQube Cloud analysis in the repository CI
workflow after the normal test and coverage command succeeds. No scanner token
is needed for local work.
