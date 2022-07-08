import logging
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
@click.option("--policy-id", help="Policy ID, e.g.: '6c561dd0-e24b-4afe-b1fd-78808a45956d'")
@click.option("--alert-rule", help="Alert rule name, e.g.: 'alertrule-1'")
@click.option("--amount", default="1", help="Number of units selected with --unit")
@click.option(
    "--unit", default="day", type=click.Choice(["minute", "hour", "day", "week", "month", "year"], case_sensitive=False)
)
@click.option(
    "--status", default="open", type=click.Choice(["open", "resolved", "snoozed", "dismissed"], case_sensitive=False)
)
@click.option("--detailed/--no-detailed", default=False)
def list_alerts(compliance_standard, amount, unit, status, detailed, policy_id, alert_rule):
    """Returns a list of alerts from the Prisma Cloud platform"""
    data = {
        "alert.status": status,
        "alertRule.name": alert_rule,
        "detailed": detailed,
        "limit": "10000",
        "policy.complianceStandard": compliance_standard,
        "policy.id": policy_id,
        "timeAmount": amount,
        "timeType": "relative",
        "timeUnit": unit,
    }

    # Fetch the alerts
    alerts = pc_api.get_endpoint("alert", query_params=data, api="cspm")

    # Try to add a new column with a url to the alert investigate page
    url = "https://app.eu.prismacloud.io/investigate/details?resourceId="
    for alert in alerts:
        try:
            alert["alert.resource.url"] = f"{url}{alert['resource']['rrn']}"
        except Exception:  # pylint:disable=broad-except
            pass

    # We want to get the related policy information so fetch the policies
    policies = pc_api.policy_list_read()

    # Iterate through alerts and add the policy description
    logging.debug("Iterating through alerts and adding policy information")
    for alert in alerts:
        for policy in policies:
            if policy["policyId"] == alert["policyId"]:
                alert["policy.name"] = policy["name"]
                alert["policy.description"] = policy["description"]
    logging.debug("Done iterating through alerts and adding policy information")

    cli_output(alerts)


cli.add_command(list_alerts)
