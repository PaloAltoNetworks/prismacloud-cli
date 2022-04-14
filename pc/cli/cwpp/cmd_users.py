import click

from pc.cli import cli_output, pass_environment
from pc.cli.api import pc_api


@click.command("users", short_help="[CWPP] Retrieves a list of all users")
@pass_environment
def cli(ctx):
    result = pc_api.get_endpoint("users")
    cli_output(result)
