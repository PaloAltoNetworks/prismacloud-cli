import click

from pc.cli import cli_output, pass_environment
from pc.cli.api import pc_api


@click.command("version", short_help="[CWPP] Shows CWPP version.")
@pass_environment
def cli(ctx):
    version = pc_api.get_endpoint("version")
    cli_output(version)
