import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.group("defenders", short_help="[CWPP] Retrieves Defenders information.")
@pass_environment
def cli(ctx):
    pass


@click.command(name="list")
@click.option("--connected", is_flag=True, help="Print Summary of Connected defenders only")
def list_defenders(connected):
    query_param = ""
    if connected is True:
        query_param = {"connected": "true"}
    result = pc_api.defenders_list_read(query_param)

    cli_output(result)


@click.command()
def names():
    result = pc_api.defenders_names_list_read()
    cli_output(result)


@click.command()
def summary():
    result = pc_api.get_endpoint("defenders/summary")
    cli_output(result)


cli.add_command(list_defenders)
cli.add_command(names)
cli.add_command(summary)
