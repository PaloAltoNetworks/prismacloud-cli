import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.command("check", short_help="[CSPM] Check and see if the Prisma Cloud API is up and running")
@pass_environment
def cli(ctx):
    result = pc_api.get_endpoint("check", api="cspm")
    cli_output(result)
