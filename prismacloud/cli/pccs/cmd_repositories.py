import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.command("repositories", short_help="[PCCS] Output details about the repositories onboardes to PCCS")
@pass_environment
def cli(ctx):  # pylint: disable=no-value-for-parameter
    result = pc_api.repositories_list_read(query_params={"errorsCount": "true"})
    cli_output(result)
