import logging
import click

# from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli import pass_environment
from prismacloud.cli.api import pc_api


@click.group("pov", short_help="[CSPM] Set best practice settings for a project")
@pass_environment
def cli(ctx):
    pass


@click.command(name="start")
def start_pov():
    """Set best practice settings for a project"""

    body_params = {
        "sessionTimeout": 30,
        "userAttributionInNotification": True,
        "requireAlertDismissalNote": True,
        "defaultPoliciesEnabled": {"low": True, "medium": True, "high": True},
        "applyDefaultPoliciesEnabled": True,
        "alarmEnabled": True,
        "accessKeyMaxValidity": -1,
    }
    pc_api.enterprise_settings_config(body_params=body_params)
    logging.info("API - Changed enterprise settings.")

    # Changed Account hijacking attempts policy
    policy_id = "e12e1b44-3018-11e7-93ae-92361f002671"
    body_params = {"alertDisposition": "aggressive", "trainingModelThreshold": "low"}

    pc_api.anomaly_settings_config(body_params=body_params, policy_id=policy_id)
    logging.info("API - Changed Account hijacking attempts policy.")

    # Changed Anomalous compute provisioning activity policy.
    policy_id = "e64fb48f-7d36-2309-dda2-2304c689116c"
    body_params = {"alertDisposition": "aggressive"}

    pc_api.anomaly_settings_config(body_params=body_params, policy_id=policy_id)
    logging.info("API - Changed Anomalous compute provisioning activity policy.")

    # Changed Unusual user activity policy.
    policy_id = "e12e1edc-3018-11e7-93ae-92361f002671"
    body_params = {"alertDisposition": "aggressive", "trainingModelThreshold": "low"}

    pc_api.anomaly_settings_config(body_params=body_params, policy_id=policy_id)
    logging.info("API - Changed Unusual user activity policy.")


cli.add_command(start_pov)
