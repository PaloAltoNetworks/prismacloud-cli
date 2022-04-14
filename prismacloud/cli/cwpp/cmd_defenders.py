import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.group("defenders", short_help="[CWPP] Retrieves Defenders information.")
@pass_environment
def cli(ctx):
    pass


@click.command(name="list")
def list_defenders():
    result = pc_api.get_endpoint("defenders")
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
