from datetime import datetime, timedelta

import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.group("audits", short_help="[CWPP] Retrieve audits for Prisma Cloud")
@pass_environment
def cli(ctx):
    pass


@click.command()
@click.option("-l", "--limit", default=5, help="Number of documents to return")
def container(limit=5):
    """

    Sample usage:

    pc --config local --columns ruleName,msg,containerName,requestHost,subnet audits container

    """
    last_hour_date_time = datetime.now() - timedelta(hours=3)
    from_field = last_hour_date_time.strftime("%Y-%m-%dT%H:%M:%S.%f%z")[:-3] + "Z"
    to_field = "2030-01-01T00:00:00.000Z"
    result = pc_api.get_endpoint(
        "audits/firewall/app/container", {"from": from_field, "to": to_field, "sort": "time", "reverse": "true"}
    )
    cli_output(result)


cli.add_command(container)
