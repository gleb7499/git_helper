# Git Helper

Git Helper is a personal Windows automation toolkit I built to remove repetitive setup work from my Git and SSH workflow. It is useful when several GitHub identities have to be managed on one machine.

## The problem

Repository setup used to require repeating the same fragile steps: generating an SSH key, editing `~/.ssh/config`, adding the key to GitHub, cloning with the right host alias, and configuring the Git identity. Small mistakes in those steps are expensive when the same workflow is repeated across many projects.

## The solution

Git Helper turns that workflow into a guided command-line menu backed by focused Python modules. It validates input, configures SSH and Git, and keeps the routine steps reproducible.

## Included tools

- `git_helper.bat`: interactive entry point and virtual-environment bootstrap;
- `ssh_manager.py`: Ed25519 key generation and SSH config management;
- `create_ssh_key.py`: guided GitHub key setup that copies the public key to the clipboard and opens the GitHub key settings page;
- `delete_ssh_key.py`: removes a key together with its SSH config entry;
- `clone_repository.py`: SSH cloning that picks the key by the repository owner and configures the Git identity.

## Quick start

Requirements: Python 3.8+ and Git.

```bat
git_helper.bat
```

The menu covers SSH key creation, SSH key removal, and repository cloning. Individual scripts can also be run from an activated virtual environment:

```bat
python src/create_ssh_key.py
python src/delete_ssh_key.py
python src/clone_repository.py
```

## Documentation

A detailed guide is available in [doc/README.md](doc/README.md).

## Security

The toolkit never stores passwords or private keys in the repository. SSH material stays under the user's home directory, sensitive folders are ignored, and input is validated before changes are made. Never commit tokens, private keys, or personal credentials.

## License

This personal utility is available under the [Creative Commons Attribution-NonCommercial 4.0 International license](LICENSE). Non-commercial sharing and adaptation are welcome with attribution to Loginov Gleb; commercial use requires prior written permission.
