import click

from pc.cli import cli_output, pass_environment
from pc.cli.api import pc_api


@click.command("check", short_help="[CSPM] Output details about the current user")
@pass_environment
def cli(ctx):
    result = pc_api.current_user()
    cli_output(result)
