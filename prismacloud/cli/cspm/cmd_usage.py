import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.command("usage", short_help="[CSPM] Retrieve credits usage information")
@pass_environment
def cli(ctx):
    body_params = {"accountIds": [], "timeRange": {"type": "relative", "value": {"unit": "day", "amount": 90}}}
    result = pc_api.resource_usage_over_time(body_params=body_params)
    cli_output(result)
