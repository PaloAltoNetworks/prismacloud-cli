import logging

import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.group("repositories", short_help="[PCCS] Interact with repositories")
@pass_environment
def cli(ctx):
    pass


@click.command("list", short_help="Output details about the repositories onboardes to PCCS")
def list_repositories():
    result = pc_api.repositories_list_read(query_params={"errorsCount": "true"})
    cli_output(result)


@click.command("update", short_help="Update repository")
@click.option(
    "--integration_type",
    default="github",
    type=click.Choice(
        ["github", "githubEnterprise", "gitlab", "gitlabEnterprise", "bitbucket", "bitbucketEnterprise", "azureRepos"]
    ),
    help="Type of the integration to update",
)
@click.option(
    "--integration_id",
    default=None,
    help="ID of the integration to update",
)
@click.option(
    "--repositories",
    default=None,
    help="List of repositories separated by #. The seperator can be customize with --seperator option.",
)
@click.option(
    "--separator",
    default="#",
    help="Use different separator than #",
)
def repository_update(integration_type, integration_id, repositories, separator):
    """Update repository"""
    logging.info("API - Updating repositories ...")

    body_params = {}

    if integration_id is None:
        logging.info("API - Using the integration type of %s", integration_type)
        body_params["type"] = integration_type
    else:
        logging.info("API - Using the integration ID: %s", integration_id)
        body_params["id"] = integration_id

    body_params["data"] = repositories.split(separator)

    logging.info("API - List of repositories to be updated: %s", body_params["data"])
    result = pc_api.repositories_update(body_params=body_params)
    logging.info("API - Repository has been updated: %s", result)


@click.command("search", short_help="Search across all repositories")
@click.option(
    "--integration_type",
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
    multiple=True,
    help="Type of the integration to update",
)
@click.option(
    "--categories",
    type=click.Choice(
        [
            "IAM",
            "Compute",
            "Monitoring",
            "Networking",
            "Kubernetes",
            "General",
            "Storage",
            "Secrets",
            "Public",
            "Vulnerabilities",
            "Drift",
            "BuildIntegrity",
            "Licenses",
        ]
    ),
    multiple=True,
    help="Category of teh findings.",
)
def global_search(integration_type, categories):
    """Search across all repositories"""
    data = []
    logging.info("API - Search across all repositories ...")
    repositories = pc_api.repositories_list_read(query_params={"errorsCount": "true"})

    impacted_files = []
    for repository in repositories:
        if repository["source"] in integration_type:
            logging.info(
                "ID for the repository %s, Name of the Repository to scan: %s, Type=%s, default branch=%s",
                repository["id"],
                repository["repository"],
                repository["source"],
                repository["defaultBranch"],
            )

            parameters = {}
            parameters["sourceTypes"] = [repository["source"]]
            parameters["categories"] = categories
            parameters["types"] = ["Errors"]
            parameters["repository"] = "%s/%s" % (repository["owner"], repository["repository"])
            parameters["repositoryId"] = repository["id"]
            parameters["branch"] = repository["defaultBranch"]

            impacted_files = pc_api.errors_files_list(criteria=parameters)

            for file in impacted_files["data"]:
                logging.info("API - File impacted: %s", file["filePath"])
                data = data + [
                    {
                        "repository": "%s/%s" % (repository["owner"], repository["repository"]),
                        "repositoryId": repository["id"],
                        "branch": repository["defaultBranch"],
                        "categories": categories,
                        "filePath": file["filePath"],
                        "errorsCount": file["errorsCount"],
                        "type": file["type"],
                    }
                ]

    cli_output(data)


cli.add_command(list_repositories)
cli.add_command(repository_update)
cli.add_command(global_search)
