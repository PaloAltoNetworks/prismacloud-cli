import logging
import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.group(
    "compliance", short_help="[CSPM] Returns a list of alerts based on compliance related findings in Prisma Cloud."
)
@pass_environment
def cli(ctx):
    pass


@click.command(name="export")
@click.option("--compliance-standard", help="Compliance standard, e.g.: 'CIS v1.4.0 (AWS)'")
@click.option("--account-group", help="Account Group ID, e.g.: 'MyAccountGroup'")
def compliance_exporter(compliance_standard, account_group):
    """Returns a list of alerts based on compliance related findings in Prisma Cloud."""

    cli_output(alerts)


cli.add_command(compliance_exporter)
