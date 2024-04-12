import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.group("inventory", short_help="[CSPM] Returns asset inventory pass/fail data for the specified time period.")
@pass_environment
def cli(ctx):
    """Inventory"""


@click.command(name="list")
def inventory():
    """Returns Cloud Accounts."""
    query_params = {"timeType": "relative", "timeAmount": "24", "timeUnit": "hour"}
    result = pc_api.asset_inventory_list_read_v3(query_params=query_params)
    cli_output(result)


cli.add_command(inventory)
