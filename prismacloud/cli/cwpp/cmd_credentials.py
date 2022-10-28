import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.command("credentials", short_help="[CWPP] Returns the credentials")
@pass_environment
def cli(ctx):
    result = pc_api.credential_list_read()
    cli_output(result)
