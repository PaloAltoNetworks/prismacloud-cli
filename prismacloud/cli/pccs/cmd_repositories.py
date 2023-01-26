import logging

import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


class MyHelper:
    def unique(self, list1):

        # initialize a null list
        unique_list = []

        # traverse for all elements
        for x in list1:
            # check if exists in unique_list or not
            if x not in unique_list:
                unique_list.append(x)

        return unique_list

    def flatten(self, origin_list):
        flat_list = [item for sublist in origin_list for item in sublist]
        return flat_list


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
    "-i",
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
    "-c",
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
    help="Category of the findings.",
)
@click.option(
    "--types",
    "-t",
    type=click.Choice(
        [
            "violation",
            "dockerCve",
            "packageCve",
        ]
    ),
    multiple=True,
    default=None,
    help="Filter the result per type of finding",
)
@click.option(
    "--max",
    default=0,
    help="Maximum repository to return",
)
@click.option("--details", is_flag=True, default=False, help="Get the details per alert")
def global_search(integration_type, categories, details, types, max):
    """Search across all repositories"""
    data = []
    logging.info("API - Search across all repositories ...")
    repositories = pc_api.repositories_list_read(query_params={"errorsCount": "true"})

    impacted_files = []
    i = 1
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
                if details and file["type"] in types:
                    logging.info("API - Imapcted file: %s", file)
                    parameters = {}
                    parameters["sourceTypes"] = [repository["source"]]
                    parameters["filePath"] = file["filePath"]
                    parameters["repository"] = "%s/%s" % (repository["owner"], repository["repository"])
                    parameters["repositoryId"] = repository["id"]
                    parameters["branch"] = repository["defaultBranch"]
                    impacted_files_with_details = pc_api.errors_file_list(criteria=parameters)

                    for details in impacted_files_with_details:
                        if "cves" in details:
                            for cve in details["cves"]:
                                data = data + [
                                    {
                                        "repository": "%s/%s" % (repository["owner"], repository["repository"]),
                                        "repositoryId": repository["id"],
                                        "branch": repository["defaultBranch"],
                                        "categories": list(categories),
                                        "filePath": file["filePath"],
                                        "errorsCount": file["errorsCount"],
                                        "type": file["type"],
                                        "author": details["author"],
                                        "sourceType": details["sourceType"],
                                        "scannerType": details["scannerType"],
                                        "frameworkType": details["frameworkType"],
                                        "error_category": details["category"],
                                        "resourceId": details["resourceId"],
                                        "resourceType": details["resourceType"],
                                        "errorId": details["errorId"],
                                        "fixedCode": details["fixedCode"],
                                        "lines": details["lines"],
                                        "cveId": cve["cveId"],
                                        "cveLink": cve["link"],
                                        "cveStatus": cve["cveStatus"],
                                        "cveSeverity": cve["severity"],
                                        "cvss": cve["cvss"],
                                        "packageName": cve["packageName"],
                                        "packageVersion": cve["packageVersion"],
                                        "fixVersion": cve["fixVersion"],
                                        "cveDescription": cve["description"],
                                    }
                                ]
                        else:
                            data = data + [
                                {
                                    "repository": "%s/%s" % (repository["owner"], repository["repository"]),
                                    "repositoryId": repository["id"],
                                    "branch": repository["defaultBranch"],
                                    "categories": list(categories),
                                    "filePath": file["filePath"],
                                    "errorsCount": file["errorsCount"],
                                    "type": file["type"],
                                    "author": details["author"],
                                    "sourceType": details["sourceType"],
                                    "scannerType": details["scannerType"],
                                    "frameworkType": details["frameworkType"],
                                    "error_category": details["category"],
                                    "resourceId": details["resourceId"],
                                    "resourceType": details["resourceType"],
                                    "errorId": details["errorId"],
                                    "fixedCode": details["fixedCode"],
                                    "lines": details["lines"],
                                }
                            ]
                else:
                    data = data + [
                        {
                            "repository": "%s/%s" % (repository["owner"], repository["repository"]),
                            "repositoryId": repository["id"],
                            "branch": repository["defaultBranch"],
                            "categories": list(categories),
                            "filePath": file["filePath"],
                            "errorsCount": file["errorsCount"],
                            "type": file["type"],
                        }
                    ]
        if max > 0 and i == max:
            break
        i = i + 1

    cli_output(data)


@click.command("count-git-authors", short_help="Count number of unique git authors")
@click.option(
    "--integration_type",
    "-i",
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
    "--max",
    default=0,
    help="Maximum repository to return",
)
def count_git_authors(integration_type, max):
    """Search across all repositories"""
    data = []
    total_git_authors = 0
    list_git_authors = []
    logging.info("API - Count number of unique git authors ...")
    repositories = pc_api.repositories_list_read()

    i = 1
    for repository in repositories:
        if repository["source"] in integration_type:
            logging.info(
                "ID for the repository %s, Name of the Repository to scan: %s, Type=%s, default branch=%s",
                repository["id"],
                repository["repository"],
                repository["source"],
                repository["defaultBranch"],
            )
            query_params = {
                "fullRepoName": "%s/%s" % (repository["owner"], repository["repository"]),
                "sourceType": repository["source"],
            }
            git_authors = pc_api.errors_list_last_authors(query_params=query_params)
            total_git_authors = total_git_authors + len(git_authors)
            list_git_authors.append(git_authors)

        if max > 0 and i == max:
            break
        i = i + 1

    helper = MyHelper()
    flat_list = helper.flatten(list_git_authors)
    unique_developers = helper.unique(flat_list)
    data = data + [
        {
            "unique_developer": len(unique_developers),
            "unique_git_authors": unique_developers,
            "number_of_repositories": len(repositories),
        }
    ]

    cli_output(data)


cli.add_command(list_repositories)
cli.add_command(repository_update)
cli.add_command(global_search)
cli.add_command(count_git_authors)
