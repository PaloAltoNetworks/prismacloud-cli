import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.group("logs", short_help="[CWPP] Retrieve logs for Prisma Cloud")
@pass_environment
def cli(ctx):
    pass


@click.command()
@click.option("-l", "--limit", default=150, help="Number of documents to return")
@click.option("--hostname", help="Defender hostname", required=True)
def defender(limit=150, hostname=""):
    result = pc_api.get_endpoint("logs/defender", {"lines": limit, "hostname": hostname})
    cli_output(result)


@click.command()
@click.option("-l", "--limit", default=150, help="Number of documents to return")
def console(limit=150):
    result = pc_api.get_endpoint("logs/console", {"lines": limit})
    cli_output(result)


@click.command()
def audit():
    result = pc_api.get_endpoint("audits/mgmt")
    cli_output(result)


cli.add_command(console)
cli.add_command(defender)
cli.add_command(audit)
