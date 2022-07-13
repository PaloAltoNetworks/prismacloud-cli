import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.command("version", short_help="[CWPP] Shows CWPP version.")
@pass_environment
def cli(ctx):
    compute_version = pc_api.get_endpoint("version", api="cwpp")
    version = {"cwpp_version": compute_version}
    cli_output(version)
