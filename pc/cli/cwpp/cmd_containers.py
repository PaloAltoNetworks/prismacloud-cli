import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.group("containers", short_help="[CWPP] Container scan reports.")
@pass_environment
def cli(ctx):
    pass


@click.command(name="list")
def list_containers():
    result = pc_api.get_endpoint("containers")
    cli_output(result)


@click.command()
def names():
    result = pc_api.get_endpoint("containers/names")
    cli_output(result)


@click.command()
def count():
    result = pc_api.get_endpoint("containers/count")
    cli_output(result)


cli.add_command(list_containers)
cli.add_command(names)
cli.add_command(count)
