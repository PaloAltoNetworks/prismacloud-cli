import logging
import datetime
import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.group("suppressions", short_help="[APPSEC] List suppression rules")
@pass_environment
def cli(ctx):
    pass


@click.command("list", short_help="List suppression rules")
def list_suppressions():
    """List suppression rules"""
    suppressions = pc_api.suppressions_list_read()
    cli_output(suppressions)


@click.command("justifications", short_help="Get suppressions justifications for all policy id and accounts")
def list_justifications():
    """Get suppressions justifications for all policy id and accounts"""
    data = []
    suppressions = pc_api.suppressions_list_read()
    for suppression in suppressions:
        logging.info("Get policy ID: %s", suppression["id"])
        if "resources" in suppression:
            accounts = []
            for account in suppression["resources"]:
                accounts.append(account["accountId"])

            query_params = {
                "accounts": accounts,
            }
            justifications = pc_api.suppressions_justifications_list_read(suppression["policyId"], query_params=query_params)
            for justification in justifications:
                if "resources" in justification and "origin" in justification:
                    data = data + [
                        {
                            "accounts": accounts,
                            "resources": justification["resources"],
                            "active": justification["active"],
                            "comment": justification["comment"],
                            "date": justification["date"],
                            "suppressionType": justification["suppressionType"],
                            "violationId": justification["violationId"],
                            "origin": justification["origin"],
                            "type": justification["type"],
                            "customer": justification["customer"],
                            "id": justification["id"],
                            "policyId": suppression["policyId"],
                        }
                    ]

    cli_output(data)


@click.command("create", short_help="Create new suppression")
@click.option(
    "-i",
    "--integration-type",
    type=click.Choice(
        [
            "Github",
            "Bitbucket",
            "Gitlab",
            "AzureRepos",
            "cli",
            "AWS",
            "Azure",
            "GCP",
            "Docker",
            "githubEnterprise",
            "gitlabEnterprise",
            "bitbucketEnterprise",
            "terraformCloud",
            "githubActions",
            "circleci",
            "codebuild",
            "jenkins",
            "tfcRunTasks",
            "admissionController",
            "terraformEnterprise",
        ]
    ),
    required=True,
    help="Type of the integration to update",
)
@click.option("-r", "--repository", required=True, help="Repository Name. e.g.: 'SimOnPanw/my-terragoat'")
@click.option("-f", "--files", multiple=True, help="File Name. Can specify multiple. e.g.: '-f s3.tf -f sns.tf'")
def create(integration_type, repository, files):
    """Create new suppression"""
    data = []
    current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    parameters = {}
    parameters["sourceTypes"] = [integration_type]
    parameters["repository"] = repository

    # Get all the files that contain errors in them
    all_repo_file_error_summaries = pc_api.errors_files_list(criteria=parameters)["data"]

    for file_summary in all_repo_file_error_summaries:
        # Process all files if no specific files are provided,
        # or just the specific ones if they are provided and match the current file path
        if not files or any(file_summary["filePath"].endswith(f) for f in files):
            if files:  # This check ensures we only log for specific files, not all files
                logging.info(f"Parsing this specific files: {file_summary['filePath']}")

            parameters["filePath"] = file_summary["filePath"]
            parameters["types"] = ["Errors"]

            impacted_files = pc_api.errors_file_list(criteria=parameters)
            for error_in_file in impacted_files:
                resource_id = f"{error_in_file['errorId']}::{repository}::{error_in_file['resourceId']}"
                body_data = {
                    "comment": f"{current_date} - Suppressed via Prisma Cloud CLI.",
                    "origin": "Platform",
                    "resources": {"id": resource_id, "accountId": repository},
                    "suppressionType": "Resources",
                }
                try:
                    pc_api.suppressions_create(error_in_file["errorId"], body_data)
                    data = data + [
                        {
                            "action": "Suppresed by Policy",
                            "policy": error_in_file["errorId"],
                            "repository": repository,
                            "file": error_in_file["resourceId"],
                            "comment": f"{current_date} - Suppressed via Prisma Cloud CLI.",
                        }
                    ]
                    logging.info(f"Suppression created for {error_in_file['resourceId']} in repository {repository}")
                except Exception as e:
                    logging.error(f"An error occurred while creating suppression: {e}")
                    data = data + [
                        {
                            "action": "Error during suppression",
                            "policy": error_in_file["errorId"],
                            "repository": repository,
                            "file": error_in_file["resourceId"],
                            "comment": f"{current_date} - Suppressed via Prisma Cloud CLI.",
                        }
                    ]

    cli_output(data)


cli.add_command(create)
cli.add_command(list_suppressions)
cli.add_command(list_justifications)
