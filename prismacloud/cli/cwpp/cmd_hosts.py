import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.group("hosts", short_help="[CWPP] Retrieves all host scan reports.")
@pass_environment
def cli(ctx):
    pass


@click.command()
@click.option("--complianceids", "compliance_ids", help="Filter by compliance id.")
def compliance(compliance_ids=""):
    result = pc_api.get_endpoint(
        "hosts", {"complianceIDs": compliance_ids, "sort": "comptrimlianceIssuesCount", "reverse": "true"}
    )
    cli_output(result)


cli.add_command(compliance)
