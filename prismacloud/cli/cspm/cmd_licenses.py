# import logging
import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.group("licenses", short_help="[CSPM] Retrieve licences information")
@pass_environment
def cli(ctx):
    pass


@click.command("list", short_help="Get license per account")
@click.option("--amount", default="1", help="Number of units selected with --unit")
@click.option(
    "--unit", default="month", type=click.Choice(["minute", "hour", "day", "week", "month", "year"], case_sensitive=False)
)
def list_license(amount, unit):
    data = []
    accountIds = []

    query_params = {"includeGroupInfo": True}
    cloud_accounts = pc_api.cloud_accounts_list_read(query_params=query_params)

    body_params = {
        "cloudTypes": ["aws", "azure", "oci", "alibaba_cloud", "gcp", "others"],
        "accountIds": [],
        "timeRange": {"type": "relative", "value": {"unit": unit, "amount": amount}},
    }
    usage = pc_api.resource_usage_by_cloud_type_v2(body_params=body_params)

    for item in usage["items"]:
        for account in cloud_accounts:
            for group in account["groups"]:
                accountId = account["accountId"]
                if accountId == item["account"]["id"]:
                    data = data + [
                        {
                            "accountId": accountId,
                            "account_name": account["name"],
                            "group_name": group["name"],
                            "cloud_type": item["cloudType"],
                            "total": item["total"],
                            "resource_type_count": item["resourceTypeCount"],
                        }
                    ]
                    accountIds.append(accountId)

    body_params = {
        "cloudTypes": ["repositories"],
        "accountIds": [],
        "timeRange": {"type": "relative", "value": {"unit": unit, "amount": amount}},
    }
    usage = pc_api.resource_usage_by_cloud_type_v2(body_params=body_params)
    for item in usage["items"]:
        accountId = item["account"]["id"]
        if accountId not in accountIds:
            data = data + [
                {
                    "accountId": accountId,
                    "account_name": item["account"]["name"],
                    "group_name": "na",
                    "cloud_type": item["cloudType"],
                    "total": item["total"],
                    "resource_type_count": item["resourceTypeCount"],
                }
            ]
            accountIds.append(accountId)

    cli_output(data)


cli.add_command(list_license)
