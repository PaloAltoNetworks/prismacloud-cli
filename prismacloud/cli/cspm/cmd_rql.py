import logging

import click
import yaml

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.command(
    "rql", short_help="[CSPM] Returns a list of alerts that match the constraints specified in the query parameters."
)
@click.option("--query", help="RQL Query", required=False)
@click.option("--file", help="RQL Queries File (yaml format)", required=False)
@click.option("--amount", default="1", help="Number of units selected with --unit")
@click.option(
    "--unit", default="day", type=click.Choice(["minute", "hour", "day", "week", "month", "year"], case_sensitive=False)
)
@click.option("--field", default="")
@pass_environment
def cli(ctx, query, amount, unit, field="", file=False):
    """
    Returns the results of a RQL query from the Prisma Cloud
    platform Sample queries:
    \b
    Config:  "config from cloud.resource where api.name = 'aws-ec2-describe-instances'"
    Network: "network from vpc.flow_record where bytes > 0 AND threat.source = 'AutoFocus' AND threat.tag.group = 'Cryptominer'"
    Event:   "event from cloud.audit_logs where operation IN ( 'AddUserToGroup', 'AttachGroupPolicy', 'AttachUserPolicy' , 'AttachRolePolicy' , 'CreateAccessKey', 'CreateKeyPair', 'DeleteKeyPair', 'DeleteLogGroup' )"
    """  # noqa
    search_params = {}
    search_params["limit"] = 1000
    search_params["timeRange"] = {}
    search_params["timeRange"]["type"] = "relative"
    search_params["timeRange"]["value"] = {}
    search_params["timeRange"]["value"]["unit"] = unit
    search_params["timeRange"]["value"]["amount"] = amount

    search_params["withResourceJson"] = False
    search_params["query"] = query

    # Check if we have a file as input
    if file:
        logging.debug("Parsing file: " + file)

        # Try to open file and iterate through the items
        try:
            with open(file) as file:
                items = yaml.safe_load(file)

            for item in items:
                name = item["name"]
                query = item["query"]
                search_params["query"] = query
                click.secho("\nRQL Query name: " + name, fg="green")
                click.secho("RQL Query: " + query, fg="green")
                logging.debug("API - Getting the RQL results ...")
                if query.startswith("config from iam"):
                    search_params["searchType"] = "iam"
                    search_params["timeRange"] = {"type": "to_now", "value": "epoch"}  # Latest results
                    result_list = pc_api.search_iam_read(search_params=search_params)
                elif query.startswith("config from"):
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
        except Exception as exc:  # pylint:disable=broad-except
            logging.error("An error has occured: %s", exc)
    else:
        logging.debug("API - Getting the RQL results ...")
        if query.startswith("config from iam"):
            search_params["searchType"] = "iam"
            search_params["timeRange"] = {"type": "to_now", "value": "epoch"}  # Latest results
            result_list = pc_api.search_iam_read(search_params=search_params)
        elif query.startswith("config from"):
            result_list = pc_api.search_config_read(search_params=search_params)
        elif query.startswith("network from"):
            # For a network query, focus on field data.nodes
            field = "data.nodes"
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
