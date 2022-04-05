import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.command("settings", short_help="[CWPP] Shows CWPP settings.")
@pass_environment
def cli(ctx):
    result = pc_api.get_endpoint("settings/defender")
    cli_output(result)
