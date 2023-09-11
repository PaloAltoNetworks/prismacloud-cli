import logging
import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api

@click.group("discovery", short_help="[CWPP] Returns a list of all cloud discovery scan results.")
@pass_environment
def cli(ctx):
    pass


@click.command(name="list")
def list_discovery(): 
    result = pc_api.cloud_discovery_read()
    cli_output(result)


@click.command(name="vms")
@click.option(
    "-a",
    "--account",
    help="Cloud Account",
    multiple=True,
)
@click.option(
    "-t",
    "--type",
    help="Cloud Type",
    multiple=True,
)
@click.option(
    "-r",
    "--region",
    help="Cloud Region",
    multiple=True,
)
def vms_discovery(type, region, account):  

    region_string = ",".join(r for r in region)
    region_filters = f"region={region_string}"

    provider_string = ",".join(t for t in type)
    type_filters = f"provider={provider_string}"

    account_string = ",".join(a for a in account)
    account_filters = f"accountIDs={account_string}"

    query_param = f"{type_filters}&{region_filters}&{account_filters}"

    logging.info("API - Query Params: %s", query_param)

    result = pc_api.cloud_discovery_vms(query_param)

    cli_output(result)


cli.add_command(list_discovery)
cli.add_command(vms_discovery)