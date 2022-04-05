import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.command("intelligence", short_help="[CWPP] Output details about the intelligence stream")
@pass_environment
def cli(ctx):
    result = pc_api.statuses_intelligence()
    cli_output(result)
