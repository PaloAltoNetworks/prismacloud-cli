import logging

import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.group("policy", short_help="[CSPM] Returns available policies, both system default and custom.")
@pass_environment
def cli(ctx):
    pass


@click.command("list", short_help="[CSPM] Returns available policies, both system default and custom")
def list_policies():
    result = pc_api.policy_list_read()
    cli_output(result)


@click.command("set", short_help="[CSPM] Turn on and off policies")
@click.option(
    "--policy_severity",
    default="high",
    type=click.Choice(["low", "medium", "high"]),
    help="Enable or disable Policies by Policy Severity.",
)
@click.option("--all_policies", is_flag=True, help="Enable or disable all Policies.")
@click.option(
    "--cloud_type",
    type=click.Choice(["aws", "azure", "gcp", "oci", "alibaba_cloud"]),
    help="Enable or disable Policies by Cloud Type.",
)
@click.option(
    "--policy_type",
    type=click.Choice(["config", "network", "audit_event", "anomaly"]),
    help="Enable or disable Policies by Policy Type.",
)
@click.option(
    "--compliance_standard",
    default=None,
    help="Enable or disable Policies by Compliance Standard, e.g.: 'CIS v1.4.0 (AWS)'",
)
@click.option("--status", type=click.Choice(["enable", "disable"]), help="Policy status to set (enable or disable).")
def enable_or_disable_policies(policy_severity, all_policies, cloud_type, policy_type, status, compliance_standard):
    """Enable or Disable policies"""
    specified_policy_status = bool(status.lower() == "enable")
    specified_policy_status_string = str(specified_policy_status).lower()
    logging.info("API - Getting list of Policies ...")
    policy_list = pc_api.policy_v2_list_read()
    logging.info("API - All policies have been fetched.")

    policy_list_to_update = []
    if compliance_standard is not None:
        logging.info("API - Getting list of Policies by Compliance Standard: %s", compliance_standard)
        policy_list = pc_api.compliance_standard_policy_v2_list_read(compliance_standard)
        logging.info("API - Done")
        for policy in policy_list:
            # Do not update a policy if it is already in the desired state.
            if policy["enabled"] is not specified_policy_status:
                policy_list_to_update.append(policy)
    else:
        if all_policies:
            for policy in policy_list:
                # Do not update a policy if it is already in the desired state.
                if policy["enabled"] is not specified_policy_status:
                    policy_list_to_update.append(policy)
        elif cloud_type is not None:
            cloud_type = cloud_type.lower()
            for policy in policy_list:
                if policy["enabled"] is not specified_policy_status:
                    if cloud_type == policy["cloudType"]:
                        policy_list_to_update.append(policy)
        elif policy_severity is not None:
            policy_severity = policy_severity.lower()
            for policy in policy_list:
                if policy["enabled"] is not specified_policy_status:
                    if policy_severity == policy["severity"]:
                        policy_list_to_update.append(policy)
        elif policy_type is not None:
            policy_type = policy_type.lower()
            for policy in policy_list:
                if policy["enabled"] is not specified_policy_status:
                    if policy_type == policy["policyType"]:
                        policy_list_to_update.append(policy)

    if policy_list_to_update:
        logging.info("API - Updating Policies ...")
        for policy in policy_list_to_update:
            logging.info("API - Updating Policy: %s", policy["name"])
            pc_api.policy_status_update(policy["policyId"], specified_policy_status_string)
        logging.info("API - All policies have been updated.")
    else:
        logging.info("API - No Policies match the specified parameter, or all matching Policies are already in desired status")


cli.add_command(list_policies)
cli.add_command(enable_or_disable_policies)
