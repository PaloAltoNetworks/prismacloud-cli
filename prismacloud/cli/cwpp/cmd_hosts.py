import click
import re

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.group("hosts", short_help="[CWPP] Retrieves all host scan reports.")
@pass_environment
def cli(ctx):
    pass


@click.command(name="report", help="Full report for each hosts")
@click.option("--complianceids", "compliance_ids", help="Filter by compliance id.")
def report(compliance_ids=""):

    query_param = {"sort": "complianceRiskScore", "reverse": "true"}
    if compliance_ids:
        query_param = {"complianceIDs": compliance_ids, "sort": "complianceRiskScore", "reverse": "true"}
    result = pc_api.hosts_list_read(query_param)
    cli_output(result)


@click.command(name="compliances", help="Get a report for compliance issues for each hosts")
def compliances():

    query_param = {"sort": "complianceRiskScore", "reverse": "true"}
    hosts = pc_api.hosts_list_read(query_param)

    data = []

    for host in hosts:
        if not host["complianceIssues"]:
            continue
        for issue in host["complianceIssues"]:

            # Extract compliance framework from title
            match = re.search(r"\(([^)]+)\)", issue["title"])
            if match:
                compliance_framework = match.group(1)
            else:
                continue  # Skip this issue if no compliance framework found

            data.append(
                {
                    "hostname": host["hostname"],
                    "account_id": host["cloudMetadata"]["accountID"],
                    "collections": host["collections"],
                    "scanTime": host["scanTime"],
                    "complianceIssuesCount": host["complianceIssuesCount"],
                    "complianceRiskScore": host["complianceRiskScore"],
                    "compliance_framework": compliance_framework,
                    "id": issue["id"],
                    "severity": issue["severity"],
                    "cause": issue["cause"],
                    "description": issue["description"],
                    "title": issue["title"],
                }
            )

    cli_output(data)


@click.command(name="vulnerabilities", help="Get a report for vulnerability issues for each hosts")
def vulnerabilities():

    query_param = {"sort": "vulnerabilityRiskScore", "reverse": "true"}
    hosts = pc_api.hosts_list_read(query_param)

    data = []

    for host in hosts:
        if not host["vulnerabilities"]:
            continue
        for issue in host["vulnerabilities"]:
            data.append(
                {
                    "hostname": host["hostname"],
                    "account_id": host["cloudMetadata"]["accountID"],
                    "collections": host["collections"],
                    "scanTime": host["scanTime"],
                    "vulnerabilitiesCount": host["vulnerabilitiesCount"],
                    "vulnerabilityRiskScore": host["vulnerabilityRiskScore"],
                    "cve": issue["cve"],
                    "severity": issue["severity"],
                    "cvss": issue["cvss"],
                    "packageName": issue["packageName"],
                    "packageVersion": issue["packageVersion"],
                    "status": issue["status"],
                }
            )

    cli_output(data)


cli.add_command(report)
cli.add_command(compliances)
cli.add_command(vulnerabilities)
