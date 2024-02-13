import subprocess
import os
import json
from pathlib import Path
import pytest

commands = [
    ["-o", "csv", "policy"],
    ["stats", "vulnerabilities", "--cve", "CVE-2022-0847"],
    ["-o", "json", "policy", "list"],
    ["tags"],
    ["stats", "dashboard"],
    ["-o", "json", "stats", "dashboard"],
    ["cloud", "names"],
    ["cloud", "type"],
    ["--columns", "defendersSummary.host", "stats", "dashboard"],
]


@pytest.fixture(scope="session", autouse=True)
def check_env_vars_or_credentials_file():
    required_env_vars = {
        "PC_ACCESS_KEY": "access_key_id",
        "PC_SAAS_API_ENDPOINT": "api_endpoint",
        "PC_SECRET_KEY": "secret_key",
    }

    env_vars_set = all(os.environ.get(env_var) for env_var in required_env_vars)

    credentials_file = Path("~/.prismacloud/credentials.json").expanduser()

    if not env_vars_set:
        if credentials_file.is_file():
            with open(credentials_file, "r") as json_file:
                data = json.load(json_file)
                for env_var, alternative_key in required_env_vars.items():
                    value = data.get(env_var) or data.get(alternative_key)
                    if value is not None:
                        os.environ[env_var] = value

    env_vars_set = all(os.environ.get(env_var) for env_var in required_env_vars)
    if not env_vars_set:
        r = "Environment variables are not set, and ~/.prismacloud/credentials.json does not exist. Stopping the test suite."
        pytest.exit(r)


@pytest.mark.parametrize("command", commands, ids=[str(command) for command in commands])
def test_cli_commands(command, benchmark):
    """Test various CLI commands and check if they run successfully."""

    def run_command():
        try:
            result = subprocess.run(
                ["python3", "bin/pc", "--config", "env"] + command, capture_output=True, text=True, check=True
            )
            assert result.returncode == 0
        except subprocess.CalledProcessError as test_error:
            pytest.fail(
                f"Command {' '.join(command)} failed with return code {test_error.returncode} "
                f"and output:\\n{test_error.output}"
            )

    if os.environ.get("SKIP_BENCHMARK") == "1":
        run_command()
    else:
        benchmark(run_command)
