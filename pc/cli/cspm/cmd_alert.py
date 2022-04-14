import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.group(
    "alert", short_help="[CSPM] Returns a list of alerts that match the constraints specified in the query parameters."
)
@pass_environment
def cli(ctx):
    pass


@click.command(name="list")
@click.option("--compliance-standard", help="Compliance standard, e.g.: 'CIS v1.4.0 (AWS)'")
@click.option("--amount", default="1", help="Number of units selected with --unit")
@click.option(
    "--unit", default="day", type=click.Choice(["minute", "hour", "day", "week", "month", "year"], case_sensitive=False)
)
@click.option(
    "--status", default="open", type=click.Choice(["open", "resolved", "snoozed", "dismissed"], case_sensitive=False)
)
@click.option("--detailed/--no-detailed", default=False)
def list_alerts(compliance_standard, amount, unit, status, detailed):
    """Returns a list of alerts from the Prisma Cloud platform"""
    data = {
        "alert.status": status,
        "detailed": detailed,
        "limit": "10",
        "policy.complianceStandard": compliance_standard,
        "timeAmount": amount,
        "timeType": "relative",
        "timeUnit": unit,
    }
    result = pc_api.alert_v2_list_read(body_params=data)
    cli_output(result)


cli.add_command(list_alerts)
