import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.command("scans", short_help="[CWPP] Retrieves scan reports for images scanned by the Jenkins plugin or twistcli")
@click.option("-l", "--limit", help="Number of documents to return")
@click.option("-s", "--search", help="Search term")
@pass_environment
def cli(ctx, limit, search):
    result = pc_api.get_endpoint("scans", {"limit": limit, "search": search, "sort": "time", "reverse": "true"})
    cli_output(result)
