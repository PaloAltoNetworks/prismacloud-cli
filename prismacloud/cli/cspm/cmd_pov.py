import logging
import click

# from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli import pass_environment
from prismacloud.cli.api import pc_api


@click.group("pov", short_help="[CSPM] Set default settings to kick-off POV with customers")
@pass_environment
def cli(ctx):
    pass


@click.command(name="start")
def start_pov():
    """Returns Cloud Accounts."""

    body_params = {
        'sessionTimeout': 30,
        'userAttributionInNotification': True,
        'requireAlertDismissalNote': True,
        'defaultPoliciesEnabled': {'low': True, 'medium': True, 'high': True},
        'applyDefaultPoliciesEnabled': True,
        'alarmEnabled': True,
        'accessKeyMaxValidity': -1
    }
    pc_api.enterprise_settings_config(body_params=body_params)
    logging.info("API - Changed enterprise settings.")

    policy_id = 'e12e1b44-3018-11e7-93ae-92361f002671'
    body_params = {
         'alertDisposition': "aggressive",
         'trainingModelThreshold': "low"
    }

    pc_api.anomaly_settings_config(body_params=body_params, policy_id=policy_id)
    logging.info("API - Changed Account hijacking attempts.")


cli.add_command(start_pov)
