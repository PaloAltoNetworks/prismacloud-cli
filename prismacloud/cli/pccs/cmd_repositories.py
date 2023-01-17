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


@click.command("search", short_help="Search accross all repositories")
@click.option(
    "--integration_type",
    default="github",
    type=click.Choice(
        ["Github", "Bitbucket", "Gitlab", "AzureRepos", "cli", "AWS", "Azure", "GCP", "Docker", "githubEnterprise", "gitlabEnterprise", "bitbucketEnterprise", "terraformCloud", "githubActions", "circleci", "codebuild", "jenkins", "tfcRunTasks", "admissionController", "terraformEnterprise"]
    ),
    help="Type of the integration to update",
)
def global_search(integration_type):
    """Search accross all repositories"""
    logging.info("API - Search accross all repositories ...")
    repositories = pc_api.repositories_list_read(query_params={"errorsCount": "true"})
    
    for repository in repositories:      
        if repository["source"] == integration_type:  
            logging.info("ID for the repository %s, Name of the Repository to scan: %s, Type=%s, default branch=%s", repository["id"], repository["repository"], repository["source"], repository["defaultBranch"] )

            body_params = []
            parameters = {}
            parameters["sourceTypes"] = [repository["source"]]
            parameters["types"] = ["Errors"]
            parameters["repository"] = repository["repository"]
            # parameters["repositoryId"] = repository["id"]
            # parameters["branch"] = repository["defaultBranch"]
            parameters["search"] = "{\"text\":\"Entropy Strings\", \"options\":[\"path\",\"code\"], \"title\":\"descriptive_title\"}"
            body_params.append(parameters)    
            logging.info("API - body_params ======== %s", parameters)

            impacted_repositories = pc_api.errors_files_list(criteria=body_params)
            logging.info("Return %s", impacted_repositories)        


cli.add_command(list_repositories)
cli.add_command(repository_update)
cli.add_command(global_search)
