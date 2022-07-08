import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.group("monitor", short_help="[CWPP] Retrieves monitor data")
@pass_environment
def cli(ctx):
    pass


@click.command()
@click.option("--complianceids", "compliance_ids", help="Filter by compliance id.")
def compliance(compliance_ids=""):
    result_hosts = pc_api.get_endpoint(
        "hosts", {"complianceIDs": compliance_ids, "sort": "complianceIssuesCount", "reverse": "true"}
    )
    result_containers = pc_api.get_endpoint(
        "containers", {"complianceIDs": compliance_ids, "sort": "info.complianceIssuesCount", "reverse": "true"}
    )
    result_serverless = pc_api.get_endpoint(
        "serverless", {"complianceIDs": compliance_ids, "sort": "complianceIssuesCount", "reverse": "true"}
    )

    # Concatenate results
    result = result_hosts + result_containers + result_serverless
    cli_output(result)


cli.add_command(compliance)
