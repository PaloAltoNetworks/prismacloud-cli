import subprocess
import os
import pytest
from pathlib import Path


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
    required_env_vars = ["PC_ACCESS_KEY", "PC_SAAS_API_ENDPOINT", "PC_SECRET_KEY"]
    env_vars_set = all(os.environ.get(env_var) for env_var in required_env_vars)

    credentials_file = Path("~/.prismacloud/credentials.json").expanduser()
    file_exists = credentials_file.is_file()

    if not env_vars_set and not file_exists:
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
