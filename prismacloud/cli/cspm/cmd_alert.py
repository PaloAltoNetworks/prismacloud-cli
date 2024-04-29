import logging
import click
import datetime

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api
from urllib.parse import quote


# Helper function to convert epoch (in milliseconds) to a datetime object
def convert_epoch_to_datetime(epoch_ms):
    return datetime.datetime.fromtimestamp(int(epoch_ms) / 1000)


# Helper function to convert datetime to human-readable format
def datetime_to_readable(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")


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
@click.option("--cloud-account", help="Cloud Account Name, e.g.: 'MyCloudAccount'")
@click.option("--account-group", help="Account Group ID, e.g.: 'MyAccountGroup'")
@click.option("--amount", default="1", help="Number of units selected with --unit")
@click.option(
    "--unit", default="day", type=click.Choice(["minute", "hour", "day", "week", "month", "year"], case_sensitive=False)
)
@click.option(
    "--status", default="open", type=click.Choice(["open", "resolved", "snoozed", "dismissed"], case_sensitive=False)
)
@click.option("--detailed/--no-detailed", default=False)
@click.option("--days-ahead", default=0, type=int, help="Filter alerts that are dismissing until the next X days.")
def list_alerts(
    compliance_standard, cloud_account, account_group, amount, unit, status, detailed, policy_id, alert_rule, days_ahead
):
    """Returns a list of alerts from the Prisma Cloud platform"""
    data = {
        "alert.status": status,
        "alertRule.name": alert_rule,
        "detailed": detailed,
        "limit": "10000",
        "policy.complianceStandard": compliance_standard,
        "timeAmount": amount,
        "timeType": "relative",
        "timeUnit": unit,
    }

    if policy_id:
        data["policy.id"] = policy_id

    if cloud_account:
        data["cloud.account"] = cloud_account

    if account_group:
        data["account.group"] = account_group

    # Fetch the alerts
    alerts = pc_api.get_endpoint("alert", query_params=data, api="cspm")

    if days_ahead > 0 and status == "snoozed":
        # Calculate future date for filter only if days_ahead > 0 and status is 'snoozed'
        future_date = datetime.datetime.now() + datetime.timedelta(days=days_ahead)

        # Filter alerts where dismissalUntilTs is before the future date
        alerts = [
            alert
            for alert in alerts
            if "dismissalUntilTs" in alert and convert_epoch_to_datetime(alert["dismissalUntilTs"]) < future_date
        ]

    # Try to add a new column with a url to the alert investigate page
    base_url = f"https://{pc_api.api.replace('api', 'app')}/alerts/overview?viewId=default"

    for alert in alerts:
        try:
            alert_id = alert["id"]

            for key in ["firstSeen", "lastSeen", "alertTime", "lastUpdated", "eventOccurred", "dismissalUntilTs"]:
                if key in alert:
                    alert[key] = datetime_to_readable(convert_epoch_to_datetime(alert[key]))

            # Correctly using double braces for literal curly braces in f-string
            filters = (
                f'{{"timeRange":{{"type":"to_now","value":"epoch"}},'
                f'"timeRange.type":"ALERT_OPENED","alert.status":["open"],'
                f'"alert.id":["{alert_id}"]}}'
            )
            # Encoding the filters part
            encoded_filters = quote(filters)

            # Constructing the full URL
            alert_url = f"{base_url}&filters={encoded_filters}"
            alert["alert.resource.url"] = alert_url
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
                alert["policy.severity"] = policy["severity"]
                alert["policy.description"] = policy["description"]
    logging.debug("Done iterating through alerts and adding policy information")

    cli_output(alerts)


cli.add_command(list_alerts)
