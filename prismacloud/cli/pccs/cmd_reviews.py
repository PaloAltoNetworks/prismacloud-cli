import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.group("reviews", short_help="Get Code review runs data")
@pass_environment
def cli(ctx):
    pass


@click.command("list", short_help="List Code review runs data")
def list_codereviews():
    result = pc_api.get_endpoint("code/api/v1/development-pipeline/code-review/runs/data", api="code")
    cli_output(result)


cli.add_command(list_codereviews)
