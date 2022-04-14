import click

from pc.cli import cli_output, pass_environment
from pc.cli.api import pc_api


@click.command("settings", short_help="[CWPP] Shows CWPP settings.")
@pass_environment
def cli(ctx):
    result = pc_api.get_endpoint("settings/defender")
    cli_output(result)
