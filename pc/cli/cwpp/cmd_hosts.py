import click

from pc.cli import cli_output, pass_environment
from pc.cli.api import pc_api


@click.command("hosts", short_help="[CWPP] Retrieves all host scan reports.")
@click.option("--complianceids", "compliance_ids", help="Filter by compliance id.")
@click.option("-l", "--limit")
@pass_environment
def cli(ctx, limit, compliance_ids=''):
    result = pc_api.get_endpoint("hosts", {"limit": limit, "complianceIDs": compliance_ids, "sort": "complianceIssuesCount", "reverse": "true"})
    cli_output(result)
