import click

from pc.cli import cli_output, pass_environment
from pc.cli.api import pc_api


@click.command("tags", short_help="[CWPP] Retrieves a list of tags")
@pass_environment
def cli(ctx):
    result = pc_api.get_endpoint("tags")
    cli_output(result)
