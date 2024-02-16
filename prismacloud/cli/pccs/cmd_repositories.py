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


@click.group("repositories", short_help="[APPSEC] Interact with repositories")
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
    "--repo",
    "-r",
    help="Search repositories",
)
@click.option(
    "--max",
    default=0,
    help="Maximum repository to return",
)
@click.option("--details", is_flag=True, default=False, help="Get the details per alert")
@click.option("--full-details", is_flag=True, default=False, help="Get the full details per alert and include IaC Frameworks.")
def global_search(integration_type, details, repo, max, full_details):
    """Search across all repositories"""
    data = []
    policies = []
    logging.info("API - Fetch all code policies ...")
    policies = pc_api.code_policies_list_read()

    logging.info("API - Search across all repositories ...")
    if repo:
        repositories = pc_api.repositories_list_read_v2(query_params={"errorsCount": "true", "search": repo})
    else:
        repositories = pc_api.repositories_list_read_v2(query_params={"errorsCount": "true"})

    i = 1
    with click.progressbar(repositories["repositories"]) as repositories_bar:
        for repository in repositories_bar:
            logging.debug(f"API - Search across all repositories ...{repository}")
            if repository["lastScanDate"] is not None and repository["source"] in integration_type:
                logging.info(
                    "ID for the repository %s, Name of the Repository to scan: %s, Type=%s, \
                        default branch=%s, repo_full_name=%s",
                    repository["id"],
                    repository["repository"],
                    repository["source"],
                    repository["defaultBranch"],
                    repository["fullRepositoryName"],
                )

                parameters = {
                    "filters": {
                        "repositories": [repository["id"]],
                        "branch": repository["scannedBranch"],
                        "checkStatus": "Error",
                    },
                    "offset": 0,
                    "search": {"scopes": [], "term": ""},
                    "sortBy": [{"key": "Count", "direction": "DESC"}, {"key": "Severity", "direction": "DESC"}],
                }

                impacted_resources = pc_api.resources_list(body_params=parameters)

                for resource in impacted_resources["data"]:
                    logging.info("API - resource impacted: %s", resource["filePath"])
                    # if details and resource["codeCategory"] in types:
                    if details or full_details:
                        logging.info("API - Imapcted resource: %s", resource)
                        parameters = {
                            "filters": {
                                "repositories": [repository["id"]],
                                "branch": repository["scannedBranch"],
                                "checkStatus": "Error",
                            },
                            "codeCategory": resource["codeCategory"],
                            "offset": 0,
                            "sortBy": [],
                            "search": {"scopes": [], "term": ""},
                        }
                        impacted_resources_with_details = pc_api.policies_list(
                            resource_uuid=resource["resourceUuid"], body_params=parameters
                        )

                        for details in impacted_resources_with_details["data"]:
                            # logging.debug("======= details  %s", details)
                            if resource["codeCategory"] == "Vulnerabilities":
                                data = data + [
                                    {
                                        "repository": repository["fullRepositoryName"],
                                        "repositoryId": repository["id"],
                                        "source": repository["source"],
                                        "branch": repository["defaultBranch"],
                                        "scannedBranch": repository["scannedBranch"],
                                        "isPublic": repository["isPublic"],
                                        "owner": repository["owner"],
                                        "sourceType": resource["sourceType"],
                                        "frameworkType": resource["frameworkType"],
                                        "resourceName": resource["resourceName"],
                                        "filePath": resource["filePath"],
                                        "codeCategory": resource["codeCategory"],
                                        "counter": resource["counter"],
                                        "fixableIssuesCount": resource["fixableIssuesCount"],
                                        "violationId": details["violationId"],
                                        "policy": details["policy"],
                                        "severity": details["severity"],
                                        "firstDetected": details["firstDetected"],
                                        "fixVersion": details["fixVersion"],
                                        "causePackageName": details["causePackageName"],
                                        "cvss": details["cvss"],
                                        "riskFactors": ", ".join(details["riskFactors"]),
                                    }
                                ]
                            elif resource["codeCategory"] == "Licenses":
                                data = data + [
                                    {
                                        "repository": repository["fullRepositoryName"],
                                        "repositoryId": repository["id"],
                                        "source": repository["source"],
                                        "branch": repository["defaultBranch"],
                                        "scannedBranch": repository["scannedBranch"],
                                        "isPublic": repository["isPublic"],
                                        "owner": repository["owner"],
                                        "sourceType": resource["sourceType"],
                                        "frameworkType": resource["frameworkType"],
                                        "resourceName": resource["resourceName"],
                                        "filePath": resource["filePath"],
                                        "codeCategory": resource["codeCategory"],
                                        "counter": resource["counter"],
                                        "fixableIssuesCount": resource["fixableIssuesCount"],
                                        "policy": details["policy"],
                                        "license": details["license"],
                                        "isIndirectPackage": details["isIndirectPackage"],
                                        "causePackageName": details["causePackageName"],
                                        "severity": details["severity"],
                                        "firstDetected": details["firstDetected"],
                                        "violationId": details["violationId"],
                                    }
                                ]
                            elif resource["codeCategory"] == "Secrets":
                                data = data + [
                                    {
                                        "repository": repository["fullRepositoryName"],
                                        "repositoryId": repository["id"],
                                        "source": repository["source"],
                                        "branch": repository["defaultBranch"],
                                        "scannedBranch": repository["scannedBranch"],
                                        "isPublic": repository["isPublic"],
                                        "owner": repository["owner"],
                                        "sourceType": resource["sourceType"],
                                        "frameworkType": resource["frameworkType"],
                                        "resourceName": resource["resourceName"],
                                        "filePath": resource["filePath"],
                                        "codeCategory": resource["codeCategory"],
                                        "counter": resource["counter"],
                                        "fixableIssuesCount": resource["fixableIssuesCount"],
                                        "policy": details["policy"],
                                        "resourceId": details["resourceId"],
                                        "severity": details["severity"],
                                        "firstDetected": details["firstDetected"],
                                        "violationId": details["violationId"],
                                    }
                                ]
                            elif resource["codeCategory"] == "IacMisconfiguration":
                                if full_details:
                                    policy = pc_api.code_policies_list_read(policy_id=details["violationId"])
                                    # Assuming policy["benchmarkChecks"] is your input list of dictionaries
                                    benchmark_checks = policy["benchmarkChecks"]

                                    # Extract unique benchmark.id values
                                    unique_benchmark_ids = list({check["benchmark"]["id"] for check in benchmark_checks})

                                    data = data + [
                                        {
                                            "repository": repository["fullRepositoryName"],
                                            "repositoryId": repository["id"],
                                            "source": repository["source"],
                                            "branch": repository["defaultBranch"],
                                            "scannedBranch": repository["scannedBranch"],
                                            "isPublic": repository["isPublic"],
                                            "owner": repository["owner"],
                                            "sourceType": resource["sourceType"],
                                            "frameworkType": resource["frameworkType"],
                                            "resourceName": resource["resourceName"],
                                            "filePath": resource["filePath"],
                                            "codeCategory": resource["codeCategory"],
                                            "counter": resource["counter"],
                                            "fixableIssuesCount": resource["fixableIssuesCount"],
                                            "author": details["author"],
                                            "violationId": details["violationId"],
                                            "policy": details["policy"],
                                            "resourceScanType": details["resourceScanType"],
                                            "severity": details["severity"],
                                            "labels": ", ".join(details["labels"]),
                                            "title": policy["title"],
                                            "isCustom": policy["isCustom"],
                                            "checkovCheckId": policy["checkovCheckId"],
                                            "provider": policy["provider"],
                                            "frameworks": ", ".join(policy["frameworks"]),
                                            "pcGuidelines": policy["pcGuidelines"],
                                            "benchmarkChecks": ", ".join(unique_benchmark_ids),
                                        }
                                    ]
                                else:
                                    for policy in policies:
                                        if details["violationId"] == policy["incidentId"]:
                                            break
                                    data = data + [
                                        {
                                            "repository": repository["fullRepositoryName"],
                                            "repositoryId": repository["id"],
                                            "source": repository["source"],
                                            "branch": repository["defaultBranch"],
                                            "scannedBranch": repository["scannedBranch"],
                                            "isPublic": repository["isPublic"],
                                            "owner": repository["owner"],
                                            "sourceType": resource["sourceType"],
                                            "frameworkType": resource["frameworkType"],
                                            "resourceName": resource["resourceName"],
                                            "filePath": resource["filePath"],
                                            "codeCategory": resource["codeCategory"],
                                            "counter": resource["counter"],
                                            "fixableIssuesCount": resource["fixableIssuesCount"],
                                            "author": details["author"],
                                            "violationId": details["violationId"],
                                            "policy": details["policy"],
                                            "resourceScanType": details["resourceScanType"],
                                            "severity": details["severity"],
                                            "labels": ", ".join(details["labels"]),
                                            "title": policy["title"],
                                            "isCustom": policy["isCustom"],
                                            "checkovCheckId": policy["checkovCheckId"],
                                            "provider": policy["provider"],
                                            "frameworks": ", ".join(policy["frameworks"]),
                                            "pcGuidelines": policy["pcGuidelines"],
                                        }
                                    ]
                            else:
                                data = data + [
                                    {
                                        "repository": repository["fullRepositoryName"],
                                        "repositoryId": repository["id"],
                                        "source": repository["source"],
                                        "branch": repository["defaultBranch"],
                                        "scannedBranch": repository["scannedBranch"],
                                        "isPublic": repository["isPublic"],
                                        "owner": repository["owner"],
                                        "sourceType": resource["sourceType"],
                                        "frameworkType": resource["frameworkType"],
                                        "resourceName": resource["resourceName"],
                                        "filePath": resource["filePath"],
                                        "severity": resource["severity"],
                                        "codeCategory": resource["codeCategory"],
                                        "counter": resource["counter"],
                                        "fixableIssuesCount": resource["fixableIssuesCount"],
                                    }
                                ]
                    else:
                        data = data + [
                            {
                                "repository": repository["fullRepositoryName"],
                                "repositoryId": repository["id"],
                                "source": repository["source"],
                                "branch": repository["defaultBranch"],
                                "scannedBranch": repository["scannedBranch"],
                                "isPublic": repository["isPublic"],
                                "owner": repository["owner"],
                                "sourceType": resource["sourceType"],
                                "frameworkType": resource["frameworkType"],
                                "resourceName": resource["resourceName"],
                                "filePath": resource["filePath"],
                                "severity": resource["severity"],
                                "codeCategory": resource["codeCategory"],
                                "counter": resource["counter"],
                                "fixableIssuesCount": resource["fixableIssuesCount"],
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


@click.command("resources", short_help="Get impacted resources")
@click.option(
    "--integration_type",
    "-i",
    type=click.Choice(
        [
            "Github",
            "Bitbucket",
            "Gitlab",
            "AzureRepos",
        ]
    ),
    multiple=True,
    help="Type of the integration to search",
)
@click.option(
    "-t",
    "--types",
    type=click.Choice(["Vulnerabilities"]),
    multiple=True,
    default=["Vulnerabilities"],
    help="Filter the result per type of finding",
)
@click.option(
    "-s",
    "--severity",
    default=["critical"],
    type=click.Choice(["low", "medium", "high", "critical"]),
    help="Filter the vulnerable package per severity",
    multiple=True,
)
@click.option(
    "-r",
    "--repository-list",
    help="Enter the name of the repository, eg: owner/reponame",
    multiple=True,
)
@click.option("--fix", is_flag=True, default=False, help="Enable or disable all Policies.")
@click.option(
    "--max",
    default=0,
    help="Maximum repository to return",
)
def fix_automatic_cves(integration_type, types, severity, repository_list, fix, max):
    """Search across all repositories"""
    data = []
    logging.info("API - Search across all repositories ...")
    repositories = pc_api.repositories_list_read(query_params={"errorsCount": "true"})

    i = 1
    with click.progressbar(repositories) as repositories_bar:
        for repository in repositories_bar:
            # Create the variable to store the concatenated string
            repo_full_name = f'{repository["owner"]}/{repository["repository"]}'
            if repository["source"] in integration_type and (not repository_list or repo_full_name in repository_list):
                logging.info(
                    "ID for the repository %s, Name of the Repository to scan: %s, Type=%s, default branch=%s",
                    repository["id"],
                    repo_full_name,
                    repository["source"],
                    repository["defaultBranch"],
                )

                parameters = {}
                parameters["filters"] = {
                    "repositories": [repository["id"]],
                    "branch": repository["defaultBranch"],
                    "checkStatus": "Error",
                    "codeCategories": types,
                    "severities": [level.upper() for level in severity],
                    "vulnerabilityRiskFactors": ["HasFix"],
                }
                parameters["offset"] = 0
                parameters["limit"] = 50
                parameters["search"] = {"scopes": [], "term": ""}

                resources = pc_api.resources_list(body_params=parameters)

                for resource in resources["data"]:
                    logging.info(f"API - Repository: {resource['repository']}")
                    logging.info(f"API - resourceUuid: {resource['resourceUuid']}")
                    logging.info(f"API - frameworkType: {resource['frameworkType']}")
                    logging.info(f"API - resourceName: {resource['resourceName']}")
                    logging.info(f"API - filePath: {resource['filePath']}")

                    parameters = {}
                    parameters["filters"] = {
                        "repositories": [repository["id"]],
                        "branch": repository["defaultBranch"],
                        "checkStatus": "Error",
                        "codeCategories": types,
                        "vulnerabilityRiskFactors": ["HasFix"],
                        "severities": [level.upper() for level in severity],
                    }
                    parameters["codeCategory"] = "Vulnerabilities"
                    parameters["offset"] = 00
                    parameters["limit"] = 100
                    parameters["sortBy"] = [{"key": "cvss", "direction": "DESC"}]
                    parameters["search"] = {"scopes": [], "term": ""}

                    dataTmp = []
                    issues = pc_api.policies_list(resource_uuid=resource["resourceUuid"], body_params=parameters)
                    for issue in issues["data"]:
                        logging.info(
                            "API - ISSUE impacted:  %s, firstDetected: %s, policy= %s, fixVersion=%s, severity=%s, cvss=%s",
                            issue["repository"],
                            issue["firstDetected"],
                            issue["policy"],
                            issue["fixVersion"],
                            issue["severity"],
                            issue["cvss"],
                        )

                        if issue["affectedCvesCounter"] == resource["fixableIssuesCount"]:
                            vulnerabilities = pc_api.vulnerabilities_list(
                                resource_uuid=resource["resourceUuid"], query_params=None
                            )

                            risk_factors = issue["riskFactors"]
                            formatted_risk_factors = ", ".join(risk_factors)
                            dataTmp = [
                                {
                                    "repository": "%s/%s" % (repository["owner"], repository["repository"]),
                                    "repositoryId": repository["id"],
                                    "branch": repository["defaultBranch"],
                                    "sourceType": resource["sourceType"],
                                    "frameworkType": resource["frameworkType"],
                                    "filePath": resource["filePath"],
                                    "resourceName": resource["resourceName"],
                                    "severity": resource["severity"],
                                    "fixableIssuesCount": resource["fixableIssuesCount"],
                                    "resourceUuid": resource["resourceUuid"],
                                    "firstDetected": issue["firstDetected"],
                                    "cve": issue["policy"],
                                    "cvss": issue["cvss"],
                                    "causePackageName": issue["causePackageName"],
                                    "packageName": issue["causePackageName"].split()[0],
                                    "violationId": issue["violationId"],
                                    "packageVersion": vulnerabilities["summary"]["packageVersion"],
                                    "fixVersion": vulnerabilities["summary"]["fixVersion"],
                                    "isPrivateRegistry": vulnerabilities["summary"]["isPrivateRegistry"],
                                    "isPrivateRegistryFix": vulnerabilities["summary"]["isPrivateRegistryFix"],
                                    "affectedCvesCounter": issue["affectedCvesCounter"],
                                    "riskFactors": formatted_risk_factors,
                                }
                            ]

                    data = data + dataTmp

            if max > 0 and i == max:
                break
            i = i + 1

        resourcesToFix = {}
        for package in data:
            if fix:
                cves = pc_api.list_cves_per_package(package["resourceUuid"])
                for cve in cves["data"]:
                    if cve["cveId"] == package["cve"]:
                        logging.info(
                            "API - FIX - violationId: %s, name= %s, version= %s, fix in=%s, id=%s, shouldBeFixed=%s",
                            package["violationId"],
                            cve["packageName"],
                            package["packageVersion"],
                            package["fixVersion"],
                            cve["uuid"],
                            fix,
                        )
                        if package["repository"] not in resourcesToFix:
                            resourcesToFix[package["repository"]] = []
                        resourcesToFix[package["repository"]].append(
                            {
                                "id": cve["uuid"],
                                "violationId": package["violationId"],
                                "packageName": cve["packageName"],
                                "packageVersion": package["fixVersion"],
                            }
                        )

        for repository, resource_list in resourcesToFix.items():
            criteria = {"resourcesToFix": resource_list}
            logging.info(f"Triggering fix for repository: {repository}")
            logging.info(f"Criteria: {criteria}")
            response = pc_api.fixed_resource(criteria)
            logging.info(
                f"API - Create a PR on the Repository: {repository} with {resource_list} and the response is {response}"
            )

        logging.info("API - All done !")

    cli_output(data)


cli.add_command(list_repositories)
cli.add_command(repository_update)
cli.add_command(global_search)
cli.add_command(fix_automatic_cves)
cli.add_command(count_git_authors)
