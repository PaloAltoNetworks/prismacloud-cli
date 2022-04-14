import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.command("license", short_help="[CWPP] Returns the license stats including the credit per defender")
@pass_environment
def cli(ctx):
    result = pc_api.get_endpoint("stats/license")
    cli_output(result)
