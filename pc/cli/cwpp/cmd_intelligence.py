import click

from pc.cli import cli_output, pass_environment
from pc.cli.api import pc_api


@click.command("intelligence", short_help="[CWPP] Output details about the intelligence stream")
@pass_environment
def cli(ctx):
    result = pc_api.statuses_intelligence()
    cli_output(result)
