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


@click.command(name="entities")
def list_entities():
    result = pc_api.cloud_discovery_entities()
    cli_output(result)


@click.command(name="vms")
@click.option("-a", "--account", help="Cloud Account", multiple=True, is_flag=False)
@click.option("-t", "--type", help="Cloud Type", multiple=True, is_flag=False)
@click.option("-r", "--region", help="Cloud Region", multiple=True, is_flag=False)
def vms_discovery(type, region, account):

    query_param = ""
    if region:
        region_string = ",".join(r for r in region)
        region_filters = f"&region={region_string}"
        query_param += region_filters

    if type:
        provider_string = ",".join(t for t in type)
        type_filters = f"&provider={provider_string}"
        query_param += type_filters

    if account:
        account_string = ",".join(a for a in account)
        account_filters = f"&accountIDs={account_string}"
        query_param += account_filters

    logging.info("API - Query Params: %s", query_param)

    result = pc_api.cloud_discovery_vms(query_param)

    cli_output(result)


cli.add_command(list_discovery)
cli.add_command(list_entities)
cli.add_command(vms_discovery)
