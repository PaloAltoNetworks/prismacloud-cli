import click
import re

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.command("saas_version", short_help="[CSPM] Shows SaaS (CSPM and CWPP) version")
@pass_environment
def cli(ctx):
    version_string = pc_api.get_endpoint("version", api="cspm")
    version_tag = "unknown"
    version_sha = "unknown"
    if version_string:
        try:
            results = re.search(r"Tag: (.+?), Version:\s+(.+)", version_string)
            if results:
                version_tag = results.group(1)
                version_sha = results.group(2)
        except AttributeError:
            pass
    compute_version = pc_api.get_endpoint("version", api="cwpp")
    version = {"cspm_tag": version_tag, "cspm_sha": version_sha, "cwpp_version": compute_version}
    cli_output(version)
