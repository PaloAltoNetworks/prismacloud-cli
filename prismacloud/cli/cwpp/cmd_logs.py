import datetime
import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.group("logs", short_help="[CWPP] Retrieve logs for Prisma Cloud")
@pass_environment
def cli(ctx):
    pass


@click.command()
@click.option("-l", "--limit", default=150, help="Number of documents to return")
@click.option("--hostname", help="Defender hostname", required=True)
def defender(limit=150, hostname=""):
    result = pc_api.get_endpoint("logs/defender", {"lines": limit, "hostname": hostname})
    cli_output(result)


@click.command()
@click.option("-l", "--limit", default=150, help="Number of documents to return")
def console(limit=150):
    result = pc_api.get_endpoint("logs/console", {"lines": limit})
    cli_output(result)


@click.command()
@click.option(
    "-t",
    "--type",
    "type_",
    type=click.Choice(["login", "profile", "settings", "rule", "user", "group", "credential", "tag"], case_sensitive=True),
    help="Type of log to retrieve",
    required=False,
)
@click.option("-h", "--hours", default=1, help="Show results for last n hours")
def audit(type_="", hours=1):
    # Calculate utc time since x hours ago (default 1)
    utc_time = datetime.datetime.utcnow() - datetime.timedelta(hours=hours)
    from_ = utc_time

    # Convert from_ to isoformat and add a Z at the end
    from_ = from_.isoformat() + "Z"

    result = pc_api.get_endpoint("audits/mgmt", {"type": type_, "from": from_, "reverse": "true", "sort": "time"})
    cli_output(result)


cli.add_command(console)
cli.add_command(defender)
cli.add_command(audit)
