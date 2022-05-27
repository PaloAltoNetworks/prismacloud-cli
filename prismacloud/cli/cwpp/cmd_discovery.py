import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.command("discovery", short_help="[CWPP] Returns a list of all cloud discovery scan results.")
@pass_environment
def cli(ctx):
    result = pc_api.get_endpoint("cloud/discovery")
    cli_output(result)
