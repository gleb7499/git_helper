# Git Helper

Git Helper is a personal Windows automation toolkit I built to remove repetitive setup work from my Git and SSH workflow. It is useful when several repositories, GitHub identities, upstream forks, branches, and code-quality checks must be managed consistently.

## The problem

Repository setup used to require repeating the same fragile steps: generating an SSH key, editing `~/.ssh/config`, cloning with the right host alias, configuring Git identity, synchronizing an upstream repository, and creating a working branch. Small mistakes in those steps are expensive when the same workflow is repeated across many projects.

## The solution

Git Helper turns that workflow into a guided command-line menu backed by focused Python modules. It validates input, derives repository information from the working path, configures SSH and Git, and keeps the routine steps reproducible.

## Included tools

- `git_helper.bat`: interactive entry point and virtual-environment bootstrap;
- `ssh_manager.py`: Ed25519 key generation, SSH config, and ssh-agent integration;
- `create_ssh_key.py`: guided GitHub key setup;
- `clone_repository.py`: SSH cloning with repository and identity configuration;
- `sync_upstream.py`: update the local `main` branch from an upstream repository;
- `create_branch.py`: synchronize `main`, create a branch, and publish it;
- `run_linter.py`: Docker-based Super-Linter launcher;
- `git_docker_utils.py`: shared Docker and Git helpers.

## Quick start

Requirements: Python 3.8+, Git, Git Bash for Windows, and Docker Desktop for linting.

```bat
git_helper.bat
```

The menu covers SSH key creation, repository cloning, upstream synchronization, branch creation, and linting. Individual scripts can also be run from an activated virtual environment:

```bat
python src/create_ssh_key.py
python src/clone_repository.py
python src/sync_upstream.py
python src/create_branch.py
```

## Documentation

Detailed guides are available in `doc/`, including the quick lint workflow, linter configuration, testing notes, and architecture notes.

## Security

The toolkit never stores passwords or private keys in the repository. SSH material stays under the user's home directory, sensitive folders are ignored, and input paths are validated before changes are made. Never commit tokens, private keys, or personal credentials.

## License

This personal utility is available under the [Creative Commons Attribution-NonCommercial 4.0 International license](LICENSE). Non-commercial sharing and adaptation are welcome with attribution to Loginov Gleb; commercial use requires prior written permission.
