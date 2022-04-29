import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.group(
    "config", short_help="[CLI] Returns a list of configs that match the constraints specified in the query parameters."
)
@pass_environment
def cli(ctx):
    pass


@click.command(name="list")
@click.option("--config", help="Show a specific config")
def list_configs(config):
    """Returns a list of configs from the Prisma Cloud platform"""
    data = {
        "alert.status": status,
        "detailed": detailed,
        "limit": "10",
        "policy.complianceStandard": compliance_standard,
        "timeAmount": amount,
        "timeType": "relative",
        "timeUnit": unit,
    }
    result = pc_api.alert_v2_list_read(body_params=data)
    cli_output(result)


cli.add_command(list_configs)
