import logging

import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.group("iam", short_help="[IAM] Investiguate on the IAM Permissions.")
@pass_environment
def cli(ctx):
    """IAM"""


@click.option("--details", is_flag=True, help="Include the Azure Services in the output")
@click.option("--amount", default="1", help="Number of units selected with --unit")
@click.option(
    "--unit", default="week", type=click.Choice(["minute", "hour", "day", "week", "month", "year"], case_sensitive=False)
)
@click.command(name="azure-guest")
def azure_guest(details, amount, unit):
    """List Azure guest accounts with wildcard permissions"""
    data = []

    query = "config from cloud.resource where cloud.type = 'azure' AND api.name = 'azure-active-directory-user' AND json.rule = userType equals \"Guest\""  # noqa: E501
    search_params = {}
    search_params["limit"] = 1000
    search_params["timeRange"] = {}
    search_params["timeRange"]["type"] = "relative"
    search_params["timeRange"]["relativeTimeType"] = "BACKWARD"
    search_params["timeRange"]["value"] = {}
    search_params["timeRange"]["value"]["unit"] = unit
    search_params["timeRange"]["value"]["amount"] = amount
    search_params["withResourceJson"] = False
    search_params["heuristicSearch"] = True
    search_params["query"] = query

    config_result_list = pc_api.search_config_read(search_params=search_params)

    for result in config_result_list:
        asset_id = result["assetId"]
        query = f"config from iam where source.cloud.resource.uai = '{asset_id}'"
        logging.debug(f"API - IAM RQL: {query}")
        search_params = {}
        search_params["limit"] = 1000
        search_params["searchType"] = "iam"
        search_params["query"] = query
        user_permissions = pc_api.search_iam_granter_to_dest(search_params=search_params)
        for permission in user_permissions:
            if permission["destCloudResourceName"] == "*":
                data_entry = {
                    "name": result["name"],
                    "accountId": result["accountId"],
                    "accountName": result["accountName"],
                    "service": result["service"],
                    "grantedByEntityType": permission["grantedByEntityType"],
                    "grantedByEntityName": permission["grantedByEntityName"],
                    "destCloudResourceName": permission["destCloudResourceName"],
                }
                if details:
                    data_entry["destCloudServiceName"] = permission.get("destCloudServiceName")

                data += [data_entry]

    cli_output(data)


cli.add_command(azure_guest)
