# Prisma Cloud CLI in GitHub Actions

## How to Use
1. **Setup GitHub Secrets** for `PC_ACCESS_KEY`, `PC_SAAS_API_ENDPOINT`, and `PC_SECRET_KEY`.
2. Add the [pc-cli-example.yml](/.github/workflows/pc-cli-example.yml) to your `.github/workflows` directory, or see the example below.
3. Trigger the workflow manually or automatically.

**Make sure to run the pc command with ```--config environment```**

## Example

```
name: Prisma Cloud CLI run

on:
  workflow_dispatch:

jobs:
  prismacloud-cli:
    runs-on: ubuntu-latest
    env:
      PC_ACCESS_KEY: ${{ secrets.PC_ACCESS_KEY }}
      PC_SAAS_API_ENDPOINT: ${{ secrets.PC_SAAS_API_ENDPOINT }}
      PC_SECRET_KEY: ${{ secrets.PC_SECRET_KEY }}

    steps:
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Check for required environment variables
        run: |
          required_env_vars=("PC_ACCESS_KEY" "PC_SAAS_API_ENDPOINT" "PC_SECRET_KEY")
          for env_var in "${required_env_vars[@]}"; do
            if [[ -z "${!env_var}" ]]; then
              echo "Error: $env_var is not set"
              exit 1
            fi
          done

      - name: Cache pip dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      - name: Install or Upgrade pip
        run: |
          if [[ ! -d "~/.cache/pip" ]]; then
            python -m pip install --upgrade pip
          fi

      - name: Environment Setup
        run: |
          if [[ ! -d "~/.cache/pip" ]]; then
            sudo pip3 install prismacloud-cli -U
            mkdir ~/.prismacloud
            touch ~/.prismacloud/.community_supported_accepted
          fi

      - name: Run command
        run: pc --config environment version
```
