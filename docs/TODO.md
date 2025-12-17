# TODO

## Random

- [X] create pyproject.toml cli
- [ ] convert click to argparse
- [ ] add argcomplete
    ```python
    uv pip add argcomplete
    ```
- [ ] add register command for tab complete
    - ```python
      import argcomplete, argparse
      parser = argparse.ArgumentParser()
      # ... define your args ...
      argcomplete.autocomplete(parser) # Or just add PYTHON_ARGCOMPLETE_OK marker
      args = parser.parse_args()
      ```
    - ```powershell
      # update registry
      register-python-argcomplete --shell powershell my-awesome-script | Out-String | Invoke-Expression
      # create new registration
      register-python-argcomplete --shell powershell my-awesome-script > ~/my-awesome-script.psm1
      # add to user profile
      Import-Module  "~/my-awesome-script.psm1"
      ```
    - [create powershell profile](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_profiles?view=powershell-7.3#how-to-create-a-profile)
    - [argcomplete](https://github.com/kislyuk/argcomplete/tree/main/contrib)

- [ ] standardize on loguru

# Import

- [ ] imports approve multiple eg 2 4 5
- [ ] better interactivity for imports
- [ ] import list available importers
- [ ] verbosity to show more details
- [ ] better table based display
- [ ] review - `import id` optional
