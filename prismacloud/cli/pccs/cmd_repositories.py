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
            if repository.get("lastScanDate") is not None and repository.get("source") in integration_type:
                logging.info(
                    "ID for the repository %s, Name of the Repository to scan: %s, Type=%s, \
                        default branch=%s, repo_full_name=%s",
                    repository.get("id"),
                    repository.get("repository"),
                    repository.get("source"),
                    repository.get("defaultBranch"),
                    repository.get("fullRepositoryName"),
                )

                parameters = {
                    "filters": {
                        "repositories": [repository.get("id")],
                        "branch": repository.get("scannedBranch"),
                        "checkStatus": "Error",
                    },
                    "offset": 0,
                    "search": {"scopes": [], "term": ""},
                    "sortBy": [{"key": "Count", "direction": "DESC"}, {"key": "Severity", "direction": "DESC"}],
                }

                impacted_resources = pc_api.resources_list(body_params=parameters)

                for resource in impacted_resources["data"]:
                    logging.info("API - resource impacted: %s", resource.get("filePath"))
                    # if details and resource.get("codeCategory") in types:
                    if details or full_details:
                        logging.debug("API - Imapcted resource: %s", resource)
                        parameters = {
                            "filters": {
                                "repositories": [repository.get("id")],
                                "branch": repository.get("scannedBranch"),
                                "checkStatus": "Error",
                            },
                            "codeCategory": resource.get("codeCategory"),
                            "offset": 0,
                            "sortBy": [],
                            "search": {"scopes": [], "term": ""},
                        }
                        impacted_resources_with_details = pc_api.policies_list(
                            resource_uuid=resource.get("resourceUuid"), body_params=parameters
                        )

                        for details in impacted_resources_with_details.get("data"):
                            logging.debug("======= details  %s", details)
                            if resource.get("codeCategory") == "Vulnerabilities":
                                data = data + [
                                    {
                                        "repository": repository.get("fullRepositoryName"),
                                        "repositoryId": repository.get("id"),
                                        "source": repository.get("source"),
                                        "branch": repository.get("defaultBranch"),
                                        "scannedBranch": repository.get("scannedBranch"),
                                        "isPublic": repository.get("isPublic"),
                                        "owner": repository.get("owner"),
                                        "sourceType": resource.get("sourceType"),
                                        "frameworkType": resource.get("frameworkType"),
                                        "resourceName": resource.get("resourceName"),
                                        "filePath": resource.get("filePath"),
                                        "codeCategory": resource.get("codeCategory"),
                                        "counter": resource.get("counter"),
                                        "fixableIssuesCount": resource.get("fixableIssuesCount"),
                                        "violationId": details.get("violationId"),
                                        "policy": details.get("policy"),
                                        "severity": details.get("severity"),
                                        "firstDetected": details.get("firstDetected"),
                                        "fixVersion": details.get("fixVersion"),
                                        "causePackageName": details.get("causePackageName"),
                                        "cvss": details.get("cvss"),
                                        "riskFactors": ", ".join(details.get("riskFactors")),
                                    }
                                ]
                            elif resource.get("codeCategory") == "Licenses":
                                data = data + [
                                    {
                                        "repository": repository.get("fullRepositoryName"),
                                        "repositoryId": repository.get("id"),
                                        "source": repository.get("source"),
                                        "branch": repository.get("defaultBranch"),
                                        "scannedBranch": repository.get("scannedBranch"),
                                        "isPublic": repository.get("isPublic"),
                                        "owner": repository.get("owner"),
                                        "sourceType": resource.get("sourceType"),
                                        "frameworkType": resource.get("frameworkType"),
                                        "resourceName": resource.get("resourceName"),
                                        "filePath": resource.get("filePath"),
                                        "codeCategory": resource.get("codeCategory"),
                                        "counter": resource.get("counter"),
                                        "fixableIssuesCount": resource.get("fixableIssuesCount"),
                                        "policy": details.get("policy"),
                                        "license": details.get("license"),
                                        "isIndirectPackage": details.get("isIndirectPackage"),
                                        "causePackageName": details.get("causePackageName"),
                                        "severity": details.get("severity"),
                                        "firstDetected": details.get("firstDetected"),
                                        "violationId": details.get("violationId"),
                                    }
                                ]
                            elif resource.get("codeCategory") == "Secrets":
                                data = data + [
                                    {
                                        "repository": repository.get("fullRepositoryName"),
                                        "repositoryId": repository.get("id"),
                                        "source": repository.get("source"),
                                        "branch": repository.get("defaultBranch"),
                                        "scannedBranch": repository.get("scannedBranch"),
                                        "isPublic": repository.get("isPublic"),
                                        "owner": repository.get("owner"),
                                        "sourceType": resource.get("sourceType"),
                                        "frameworkType": resource.get("frameworkType"),
                                        "resourceName": resource.get("resourceName"),
                                        "filePath": resource.get("filePath"),
                                        "codeCategory": resource.get("codeCategory"),
                                        "counter": resource.get("counter"),
                                        "fixableIssuesCount": resource.get("fixableIssuesCount"),
                                        "policy": details.get("policy"),
                                        "resourceId": details.get("resourceId"),
                                        "severity": details.get("severity"),
                                        "firstDetected": details.get("firstDetected"),
                                        "violationId": details.get("violationId"),
                                    }
                                ]
                            elif resource.get("codeCategory") == "Weaknesses":
                                # Initialize default values for location-related fields in case they're not available
                                default_location = {
                                    "codeBlock": "",
                                    "start": {"row": 0, "column": 0},
                                    "end": {"row": 0, "column": 0},
                                }
                                
                                # Safely get the first location, or use a default structure if unavailable
                                first_location = details.get("locations", [default_location])[0]
                                data = data + [
                                    {
                                        "repository": repository.get("fullRepositoryName"),
                                        "repositoryId": repository.get("id"),
                                        "source": repository.get("source"),
                                        "branch": repository.get("defaultBranch"),
                                        "scannedBranch": repository.get("scannedBranch"),
                                        "isPublic": repository.get("isPublic"),
                                        "owner": repository.get("owner"),
                                        "sourceType": resource.get("sourceType"),
                                        "frameworkType": resource.get("frameworkType"),
                                        "resourceName": resource.get("resourceName"),
                                        "filePath": resource.get("filePath"),
                                        "codeCategory": resource.get("codeCategory"),
                                        "counter": resource.get("counter"),
                                        "fixableIssuesCount": resource.get("fixableIssuesCount"),
                                        "author": details.get("author"),
                                        "commitHash": details.get("commitHash"),
                                        "policy": details.get("policy"),
                                        "severity": details.get("severity"),
                                        "violationId": details.get("violationId"),
                                        "isCustom": details.get("isCustom"),
                                        "description": details.get("description"),
                                        "guideline": details.get("guideline"),
                                        "fileName": details.get("fileName"),
                                        "filePath": details.get("filePath"),
                                        "fileType": details.get("fileType"),
                                        "CWE": ", ".join(details.get("CWE", [])),
                                        "codeBlock": first_location.get("codeBlock", ""),
                                        "start_row": first_location.get("start", {}).get("row", 0),
                                        "end_row": first_location.get("end", {}).get("row", 0),
                                        "start_column": first_location.get("start", {}).get("column", 0),
                                        "end_column": first_location.get("end", {}).get("column", 0),
                                    }
                                ]
                            elif resource.get("codeCategory") == "IacMisconfiguration":
                                if full_details:
                                    policy = pc_api.code_policies_list_read(policy_id=details.get("violationId"))
                                    # Assuming policy.get("benchmarkChecks") is your input list of dictionaries
                                    benchmark_checks = policy.get("benchmarkChecks")

                                    # Extract unique benchmark.id values
                                    unique_benchmark_ids = list({check["benchmark"]["id"] for check in benchmark_checks})

                                    data = data + [
                                        {
                                            "repository": repository.get("fullRepositoryName"),
                                            "repositoryId": repository.get("id"),
                                            "source": repository.get("source"),
                                            "branch": repository.get("defaultBranch"),
                                            "scannedBranch": repository.get("scannedBranch"),
                                            "isPublic": repository.get("isPublic"),
                                            "owner": repository.get("owner"),
                                            "sourceType": resource.get("sourceType"),
                                            "frameworkType": resource.get("frameworkType"),
                                            "resourceName": resource.get("resourceName"),
                                            "filePath": resource.get("filePath"),
                                            "codeCategory": resource.get("codeCategory"),
                                            "counter": resource.get("counter"),
                                            "fixableIssuesCount": resource.get("fixableIssuesCount"),
                                            "author": details.get("author"),
                                            "violationId": details.get("violationId"),
                                            "policy": details.get("policy"),
                                            "resourceScanType": details.get("resourceScanType"),
                                            "severity": details.get("severity"),
                                            "labels": ", ".join(details.get("labels")),
                                            "title": policy.get("title"),
                                            "isCustom": policy.get("isCustom"),
                                            "checkovCheckId": policy.get("checkovCheckId"),
                                            "provider": policy.get("provider"),
                                            "frameworks": ", ".join(policy.get("frameworks")),
                                            "pcGuidelines": policy.get("pcGuidelines"),
                                            "benchmarkChecks": ", ".join(unique_benchmark_ids),
                                        }
                                    ]
                                else:
                                    for policy in policies:
                                        if details.get("violationId") == policy.get("incidentId"):
                                            break
                                    data = data + [
                                        {
                                            "repository": repository.get("fullRepositoryName"),
                                            "repositoryId": repository.get("id"),
                                            "source": repository.get("source"),
                                            "branch": repository.get("defaultBranch"),
                                            "scannedBranch": repository.get("scannedBranch"),
                                            "isPublic": repository.get("isPublic"),
                                            "owner": repository.get("owner"),
                                            "sourceType": resource.get("sourceType"),
                                            "frameworkType": resource.get("frameworkType"),
                                            "resourceName": resource.get("resourceName"),
                                            "filePath": resource.get("filePath"),
                                            "codeCategory": resource.get("codeCategory"),
                                            "counter": resource.get("counter"),
                                            "fixableIssuesCount": resource.get("fixableIssuesCount"),
                                            "author": details.get("author"),
                                            "violationId": details.get("violationId"),
                                            "policy": details.get("policy"),
                                            "resourceScanType": details.get("resourceScanType"),
                                            "severity": details.get("severity"),
                                            "labels": ", ".join(details.get("labels")),
                                            "title": policy.get("title"),
                                            "isCustom": policy.get("isCustom"),
                                            "checkovCheckId": policy.get("checkovCheckId"),
                                            "provider": policy.get("provider"),
                                            "frameworks": ", ".join(policy.get("frameworks")),
                                            "pcGuidelines": policy.get("pcGuidelines"),
                                        }
                                    ]
                            else:
                                data = data + [
                                    {
                                        "repository": repository.get("fullRepositoryName"),
                                        "repositoryId": repository.get("id"),
                                        "source": repository.get("source"),
                                        "branch": repository.get("defaultBranch"),
                                        "scannedBranch": repository.get("scannedBranch"),
                                        "isPublic": repository.get("isPublic"),
                                        "owner": repository.get("owner"),
                                        "sourceType": resource.get("sourceType"),
                                        "frameworkType": resource.get("frameworkType"),
                                        "resourceName": resource.get("resourceName"),
                                        "filePath": resource.get("filePath"),
                                        "severity": resource.get("severity"),
                                        "codeCategory": resource.get("codeCategory"),
                                        "counter": resource.get("counter"),
                                        "fixableIssuesCount": resource.get("fixableIssuesCount"),
                                    }
                                ]
                    else:
                        data = data + [
                            {
                                "repository": repository.get("fullRepositoryName"),
                                "repositoryId": repository.get("id"),
                                "source": repository.get("source"),
                                "branch": repository.get("defaultBranch"),
                                "scannedBranch": repository.get("scannedBranch"),
                                "isPublic": repository.get("isPublic"),
                                "owner": repository.get("owner"),
                                "sourceType": resource.get("sourceType"),
                                "frameworkType": resource.get("frameworkType"),
                                "resourceName": resource.get("resourceName"),
                                "filePath": resource.get("filePath"),
                                "severity": resource.get("severity"),
                                "codeCategory": resource.get("codeCategory"),
                                "counter": resource.get("counter"),
                                "fixableIssuesCount": resource.get("fixableIssuesCount"),
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
        if repository.get("source") in integration_type:
            logging.info(
                "ID for the repository %s, Name of the Repository to scan: %s, Type=%s, default branch=%s",
                repository.get("id"),
                repository.get("repository"),
                repository.get("source"),
                repository.get("defaultBranch"),
            )
            query_params = {
                "fullRepoName": "%s/%s" % (repository.get("owner"), repository.get("repository")),
                "sourceType": repository.get("source"),
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
            repo_full_name = f'{repository.get("owner")}/{repository.get("repository")}'
            if repository.get("source") in integration_type and (not repository_list or repo_full_name in repository_list):
                logging.info(
                    "ID for the repository %s, Name of the Repository to scan: %s, Type=%s, default branch=%s",
                    repository.get("id"),
                    repo_full_name,
                    repository.get("source"),
                    repository.get("defaultBranch"),
                )

                parameters = {}
                parameters["filters"] = {
                    "repositories": [repository.get("id")],
                    "branch": repository.get("defaultBranch"),
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
                        "repositories": [repository.get("id")],
                        "branch": repository.get("defaultBranch"),
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
                    issues = pc_api.policies_list(resource_uuid=resource.get("resourceUuid"), body_params=parameters)
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

                        if issue["affectedCvesCounter"] == resource.get("fixableIssuesCount"):
                            vulnerabilities = pc_api.vulnerabilities_list(
                                resource_uuid=resource.get("resourceUuid"), query_params=None
                            )

                            risk_factors = issue["riskFactors"]
                            formatted_risk_factors = ", ".join(risk_factors)
                            dataTmp = [
                                {
                                    "repository": "%s/%s" % (repository.get("owner"), repository.get("repository")),
                                    "repositoryId": repository.get("id"),
                                    "branch": repository.get("defaultBranch"),
                                    "sourceType": resource.get("sourceType"),
                                    "frameworkType": resource.get("frameworkType"),
                                    "filePath": resource.get("filePath"),
                                    "resourceName": resource.get("resourceName"),
                                    "severity": resource.get("severity"),
                                    "fixableIssuesCount": resource.get("fixableIssuesCount"),
                                    "resourceUuid": resource.get("resourceUuid"),
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
