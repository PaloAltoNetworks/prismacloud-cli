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
    logging.info("API - Implementing best practices on your Prisma Cloud tenant.")

    body_params = {
        "sessionTimeout": 60,
        "userAttributionInNotification": False,
        "requireAlertDismissalNote": True,
        "autoEnableAttackPathAndModulePolicies": True,
        "defaultPoliciesEnabled": {"informational": True, "low": True, "medium": True, "high": True, "critical": True},
        "alarmEnabled": True,
        "applyDefaultPoliciesEnabled": True,
        "accessKeyMaxValidity": -1,
        "auditLogSiemIntgrIds": [],
        "auditLogsEnabled": False,
        "unsubscribeChronicles": False,
        "namedUsersAccessKeysExpiryNotificationsEnabled": False,
        "serviceUsersAccessKeysExpiryNotificationsEnabled": False,
        "notificationThresholdAccessKeysExpiry": 0,
    }
    pc_api.enterprise_settings_config(body_params=body_params)
    logging.info("API - Changed enterprise settings and enabled all policies.")

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

    # Get the resource list
    resource_lists = pc_api.resource_list_read()

    # Initialize the flag to False
    found = False
    compute_resource_list_id = ""

    # Iterate through each resource in the list
    for resource in resource_lists:
        if resource["name"] == "Compute Alert Rule":
            found = True
            compute_resource_list_id = resource["id"]
            break

    # Add a resource list if flag is false
    if found:
        logging.info(f"API - Resource List 'Compute Alert Rule' exists. Compute Alert List ID is {compute_resource_list_id}")
    else:
        logging.info("API - Resource List 'Compute Alert Rule' does not exist.")
        body_params = {
            "name": "Compute Alert Rule",
            "resourceListType": "COMPUTE_ACCESS_GROUP",
            "description": "Created by Prisma Cloud CLI",
            "members": [
                {
                    "appIDs": ["*"],
                    "clusters": ["*"],
                    "codeRepos": ["*"],
                    "containers": ["*"],
                    "functions": ["*"],
                    "hosts": ["*"],
                    "images": ["*"],
                    "labels": ["*"],
                    "namespaces": ["*"],
                }
            ],
        }
        compute_resource_list = pc_api.resource_list_create(body_params)
        compute_resource_list_id = compute_resource_list["id"]
        logging.info(f"API - Add a resource list 'Compute Alert Rule'. Compute Alert List ID is {compute_resource_list_id}")

    # Get the alert rule list
    alert_rules = pc_api.alert_rule_list_read()

    # Get the account groups list
    account_groups = pc_api.cloud_account_group_list_read()

    # Initialize alert_rule_id
    alert_rule_id = None

    # Find the alert rule id for 'Prisma Default Alert Rule'
    for alert_rule in alert_rules:
        if alert_rule["name"] == "Prisma Default Alert Rule":
            alert_rule_id = alert_rule["policyScanConfigId"]
            break

    # Check if the alert rule was found
    if alert_rule_id is None:
        raise ValueError("Alert rule 'Prisma Default Alert Rule' not found")

    # Extract all account group ids
    account_group_ids = [group["id"] for group in account_groups]

    # Prepare the body parameters for the update
    body_params = {
        "policyScanConfigId": alert_rule_id,
        "name": "Prisma Default Alert Rule",
        "description": "Prisma Default alert rule to scan all policies associated with label Prisma_Cloud and all account added to 'Default Account Group' - Updated with Prisma Cloud CLI",  # noqa: E501
        "enabled": True,
        "scanAll": True,
        "deleted": False,
        "alertRuleNotificationConfig": [],
        "allowAutoRemediate": False,
        "delayNotificationMs": 0,
        "scanConfigType": "STANDARD",
        "notifyOnOpen": True,
        "notifyOnSnoozed": False,
        "notifyOnDismissed": False,
        "notifyOnResolved": False,
        "readOnly": False,
        "policies": [],
        "target": {
            "alertRulePolicyFilter": {},
            "accountGroups": account_group_ids,
            "excludedAccounts": [],
            "regions": [],
            "tags": [],
        },
    }

    # Update the alert rule
    pc_api.alert_rule_update(alert_rule_id, body_params)
    logging.info("API - Update default alert rule")

    # Initialize the flag to False
    found = False

    # Iterate through each resource in the list
    for alert_rule in alert_rules:
        if alert_rule["name"] == "Compute Alert Rule":
            found = True
            alert_rule_id = alert_rule["policyScanConfigId"]
            break

    # Add a resource list if flag is false
    if found:
        logging.info("API - Alert Rule 'Compute Alert Rule' exists.")
    else:
        # Prepare the body parameters for the update
        body_params = {
            "name": "Compute Alert Rule",
            "description": "Compute Alert Rule created by Prisma Cloud CLI",
            "enabled": True,
            "scanAll": False,
            "alertRuleNotificationConfig": [],
            "notifyOnOpen": True,
            "policies": [
                "2f6a1ddf-d2f2-40c8-8598-c52f3438d0dc",
                "30cfde92-4a3f-4f1d-966b-08c42b8b0f26",
                "45905e17-b6f4-485a-9bbe-6610a417a8e6",
                "287de5f8-f5e6-4908-bdad-50c48e71a5da",
                "34c1e0fd-f516-4b46-8d59-f69b6f28a504",
                "1a3c9450-ffa3-427b-8bc4-d6a8bfdb0f36",
                "0452698b-cd31-4f99-8ed4-9337b1ec6451",
            ],
            "target": {
                "alertRulePolicyFilter": {},
                "accountGroups": [],
                "excludedAccounts": [],
                "includedResourceLists": {"computeAccessGroupIds": [compute_resource_list_id]},
                "regions": [],
            },
        }

        # Update the alert rule
        pc_api.alert_rule_create(body_params)
        logging.info("API - Create compute alert rule")

    # Add current user to SSO Bypass List
    current_user = pc_api.current_user()
    logging.info(f"API - Current user email address: {current_user['email']}")

    body_params = [current_user["email"]]
    # Update the alert rule
    pc_api.user_bypass_sso(body_params)
    logging.info("API - Current user added to SSO Bypass list")

    # Create Cloud Security report with a schedule
    users = pc_api.user_list_read()
    user_emails = [user["email"] for user in users]
    logging.info(f"API - List email addresses: {user_emails}")

    # Get the cloud security reports
    reports = pc_api.adoptionadvisor_report_read()
    logging.info("API - Get existing cloud security reports")

    # Initialize the flag to False
    found = False

    # Iterate through each resource in the list
    for report in reports:
        if report["name"] == "Scheduled Cloud Security Report":
            found = True
            break

    # Add a resource list if flag is false
    if found:
        logging.info("API - Cloud Security Report exists.")
    else:
        # Prepare the body parameters for the update
        body_params = {
            "emailIds": user_emails,
            "name": "Scheduled Cloud Security Report",
            "widgetDays": 30,
            "isRecurring": True,
            "target": {
                "scheduleEnabled": True,
                "schedule": "DTSTART;TZID=Europe/Brussels:20240701T000000\nINTERVAL=1;FREQ=WEEKLY;BYHOUR=3;BYMINUTE=0;BYSECOND=0;BYDAY=MO",  # noqa: E501
            },
            "ruleOptions": {
                "target": {
                    "schedule": {"interval": "1", "frequency": 2, "weekday": [0], "hour": 3, "timezone": "Europe/Brussels"}
                }
            },
            "schedule": "DTSTART;TZID=Europe/Brussels:20240701T000000\nINTERVAL=1;FREQ=WEEKLY;BYHOUR=3;BYMINUTE=0;BYSECOND=0;BYDAY=MO",  # noqa: E501
            "enabled": True,
        }

        # Update the alert rule
        pc_api.adoptionadvisor_report_create(report_to_add=body_params)
        logging.info("API - Created Cloud Security Report")

    # Prepare the body parameters for the update
    body_params = {
        "id": "8d57f69b-fbe6-4749-b53c-1e0f0881ad3d",
        "name": "Security default findings",
        "repositories": [],
        "codeCategories": {
            "LICENSES": {"softFailThreshold": "LOW", "hardFailThreshold": "OFF", "commentsBotThreshold": "LOW"},
            "VULNERABILITIES": {"softFailThreshold": "LOW", "hardFailThreshold": "OFF", "commentsBotThreshold": "LOW"},
            "IAC": {"softFailThreshold": "INFO", "hardFailThreshold": "OFF", "commentsBotThreshold": "INFO"},
            "WEAKNESSES": {"softFailThreshold": "OFF", "hardFailThreshold": "OFF", "commentsBotThreshold": "OFF"},
            "SECRETS": {"softFailThreshold": "LOW", "hardFailThreshold": "OFF", "commentsBotThreshold": "LOW"},
            "BUILD_INTEGRITY": {"softFailThreshold": "OFF", "hardFailThreshold": "OFF", "commentsBotThreshold": "OFF"},
        },
    }

    # Update the alert rule
    pc_api.enforcement_rules_update(rules=body_params)
    logging.info("API - Enforcement rules updated")

    logging.info("API - === END ===")


cli.add_command(start_pov)
