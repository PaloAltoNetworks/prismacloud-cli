import logging

import csv
from colorama import Fore, Style
import click


from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


def validate_csv(ctx, param, value):
    if value:
        if not value.name.endswith(".csv"):
            raise click.BadParameter("CSV file extension must be '.csv'")
        return value


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
    "--csv",
    "csv_file",  # Add this line to map the option to the parameter
    type=click.File("r"),
    callback=validate_csv,
    help="CSV file containing policyId and enabled columns.",
)
@click.option("--dry-run", is_flag=True, help="Preview changes without actually making them.")
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
def enable_or_disable_policies(
    policy_severity, all_policies, cloud_type, policy_type, status, compliance_standard, csv_file, dry_run
):
    """Enable or Disable policies"""

    logging.debug("API - Getting list of Policies ...")
    policy_list = pc_api.policy_v2_list_read()
    logging.debug("API - All policies have been fetched.")

    # Initialize counters to keep track of planned actions
    total_fetched_policies = len(policy_list)  # Count the total number of fetched policies
    total_policies_csv = 0
    policies_to_update = 0
    policies_no_change = 0
    changes_true_to_false = 0
    changes_false_to_true = 0

    # Ensure that the --dry-run flag is only used in conjunction with the --csv option.
    if dry_run and not csv_file:
        logging.error("The --dry-run option is only valid when --csv is provided.")
        return

    if dry_run:
        logging.info(f"{Fore.MAGENTA}=== DRY-RUN SUMMARY ==={Style.RESET_ALL}")

    # When --csv is provided, the function follows a different logic path for updating policies,
    # and the --status option becomes optional.
    if csv_file:
        logging.debug("Processing CSV file: %s", csv_file.name)
        reader = csv.DictReader(csv_file)  # Use csv directly as file object
        for row in reader:
            total_policies_csv += 1  # Increment total count for each row in CSV
            policy_id = row.get("policyId")
            required_status = row.get("enabled").lower() == "true"
            policy = next((p for p in policy_list if p["policyId"] == policy_id), None)
            logging.debug(f"Policy ID: {policy_id}, ({policy['enabled']}->{required_status}), Name: {policy['name']}")
            if policy:
                if policy["enabled"] != required_status:
                    logging.debug(f"API - Updating Policy:, ({policy['enabled']}->{required_status}), Name: {policy['name']}")

                    if dry_run:
                        # Check if the policy's current status matches the required status
                        if policy["enabled"] != required_status:
                            policies_to_update += 1
                            action = "-" if policy["enabled"] else "+"
                            if action == "-":
                                changes_true_to_false += 1
                            else:
                                changes_false_to_true += 1

                            # Log the planned action with color coding
                            color = Fore.LIGHTGREEN_EX if action == "+" else Fore.LIGHTRED_EX
                            logging.info(f"{color}[{action}] Policy: {policy['name']}{Style.RESET_ALL}")
                    else:
                        try:
                            pc_api.policy_status_update(policy_id, required_status.lower())
                        except Exception as exc:  # pylint:disable=broad-except
                            logging.error(
                                f"Unable to update Policy ID: {policy_id}. It may have been changed in the past 4 hours."
                            )
                            logging.info("Error:: %s", exc)
                else:
                    if dry_run:
                        policies_no_change += 1  # Increment if no change is needed

                        # Log that no changes are needed for this policy
                        action = "="
                        color = Fore.LIGHTYELLOW_EX if action == "=" else Fore.CYAN
                        logging.info(f"{color}[{action}] Policy: {policy['name']}{Style.RESET_ALL}")

        # Show summary of actions based on CSV input
        if dry_run and csv_file:
            logging.info(f"{Fore.MAGENTA}=== DRY-RUN COMPLETE ==={Style.RESET_ALL}")
            logging.info(f"{Fore.CYAN}Total Policies Fetched: {total_fetched_policies}{Style.RESET_ALL}")
            logging.info(f"{Fore.CYAN}Policies in CSV: {total_policies_csv}{Style.RESET_ALL}")
            logging.info(
                f"{Fore.LIGHTGREEN_EX}To Update: {policies_to_update} "
                f"({Fore.LIGHTRED_EX}Disabling: {changes_true_to_false}, "
                f"{Fore.LIGHTGREEN_EX}Enabling: {changes_false_to_true})"
                f"{Style.RESET_ALL}"
            )

            logging.info(f"{Fore.LIGHTYELLOW_EX}No Changes: {policies_no_change}{Style.RESET_ALL}")
        else:
            logging.info("API - All policies from CSV have been updated.")
        return

    specified_policy_status = bool(status.lower() == "enable")
    specified_policy_status_string = str(specified_policy_status).lower()

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
