import logging

import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.group("stats", short_help="[CWPP] Retrieve statistics for the resources protected by Prisma Cloud")
@pass_environment
def cli(ctx):
    pass


@click.command()
def daily():
    result = pc_api.get_endpoint("stats/daily")
    cli_output(result)


@click.command()
def dashboard():
    result = pc_api.get_endpoint("stats/dashboard")
    cli_output(result)


@click.command()
def events():
    result = pc_api.get_endpoint("stats/events")
    cli_output(result)


@click.command(name="license")
def license_stats():
    result = pc_api.get_endpoint("stats/license")
    cli_output(result)


@click.command()
@click.option("-cve", "--cve")
def vulnerabilities(cve):

    if not cve:
        result = pc_api.get_endpoint("stats/vulnerabilities")
        exit()
    else:
        cves = cve.split(",")
        logging.debug("CVEs to search for: {cves}")

        # Get impacted resources for each cve in cves
        result_tree = {}
        for cve in cves:
            result = pc_api.get_endpoint("stats/vulnerabilities/impacted-resources", {"cve": cve})
            result_tree[cve] = result

        cli_output(result_tree)
        exit()


cli.add_command(daily)
cli.add_command(dashboard)
cli.add_command(events)
cli.add_command(license_stats)
cli.add_command(vulnerabilities)
