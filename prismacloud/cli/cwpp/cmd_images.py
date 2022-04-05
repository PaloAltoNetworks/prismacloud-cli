import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.command("images", short_help="[CWPP] Retrieves deployed images scan reports")
@click.option("-l", "--limit")
@pass_environment
def cli(ctx, limit):
    result = pc_api.images_list_read(query_params={"limit": limit})
    cli_output(result)
