import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.command("version", short_help="[CWPP] Shows CWPP version.")
@pass_environment
def cli(ctx):
    version = pc_api.get_endpoint("version")
    cli_output(version)
