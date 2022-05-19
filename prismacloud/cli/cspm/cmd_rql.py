import logging

import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.command(
    "rql", short_help="[CSPM] Returns a list of alerts that match the constraints specified in the query parameters."
)
@click.option("--query", help="RQL Query", required=True)
@click.option("--amount", default="1", help="Number of units selected with --unit")
@click.option(
    "--unit", default="day", type=click.Choice(["minute", "hour", "day", "week", "month", "year"], case_sensitive=False)
)
@click.option("--field", default="")
@pass_environment
def cli(ctx, query, amount, unit, field=""):
    """
    Returns the results of a RQL query from the Prisma Cloud
    platform Sample queries:
    \b
    Config:  "config from cloud.resource where api.name = 'aws-ec2-describe-instances'"
    Network: "network from vpc.flow_record where bytes > 0 AND threat.source = 'AutoFocus' AND threat.tag.group = 'Cryptominer'"
    Event:   "event from cloud.audit_logs where operation IN ( 'AddUserToGroup', 'AttachGroupPolicy', 'AttachUserPolicy' , 'AttachRolePolicy' , 'CreateAccessKey', 'CreateKeyPair', 'DeleteKeyPair', 'DeleteLogGroup' )"
    """  # noqa
    search_params = {}
    search_params["limit"] = 10000
    search_params["timeRange"] = {}
    search_params["timeRange"]["type"] = "relative"
    search_params["timeRange"]["value"] = {}
    search_params["timeRange"]["value"]["unit"] = unit
    search_params["timeRange"]["value"]["amount"] = amount
    search_params["withResourceJson"] = False
    search_params["query"] = query

    logging.debug("API - Getting the RQL results ...")
    if query.startswith("config from"):
        result_list = pc_api.search_config_read(search_params=search_params)
    elif query.startswith("network from"):
        result_list = pc_api.search_network_read(search_params=search_params)
    elif query.startswith("event from"):
        result_list = pc_api.search_event_read(search_params=search_params)
    else:
        logging.error("Unknown RQL query type (limited to: config|network|event).")

    if field == "":
        cli_output(result_list)
    else:
        # We have field as input to select a deeper level of data.
        # Our main result returns data on the query and the results are in one of the main field.
        # This option gives the ability to retrieve that data.
        field_path = field.split(".")
        for _field in field_path:
            result_list = result_list[_field]

        cli_output(result_list)
