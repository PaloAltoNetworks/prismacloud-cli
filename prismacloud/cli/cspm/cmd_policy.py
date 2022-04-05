import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.command("policy", short_help="[CSPM] Returns available policies, both system default and custom")
@pass_environment
def cli(ctx):
    result = pc_api.policy_list_read()
    cli_output(result)
