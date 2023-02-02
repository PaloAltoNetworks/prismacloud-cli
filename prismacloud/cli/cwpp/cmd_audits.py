from datetime import datetime, timedelta

import click
import logging

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

    pc --config local --columns os,msg,type,attackType,severity,containerName,hostname audits container

    """
    last_hour_date_time = datetime.now() - timedelta(hours=3)
    from_field = last_hour_date_time.strftime("%Y-%m-%dT%H:%M:%S.%f%z")[:-3] + "Z"
    to_field = "2030-01-01T00:00:00.000Z"
    result = pc_api.get_endpoint(
        "audits/runtime/container", {"from": from_field, "to": to_field, "sort": "time", "reverse": "true"}
    )
    cli_output(result)


@click.command()
@click.option("-l", "--limit", default=5, help="Number of documents to return")
def firewall(limit=5):
    """

    Sample usage:

    pc --config local --columns ruleName,msg,containerName,requestHost,subnet audits firewall

    """
    last_hour_date_time = datetime.now() - timedelta(hours=3)
    from_field = last_hour_date_time.strftime("%Y-%m-%dT%H:%M:%S.%f%z")[:-3] + "Z"
    to_field = "2030-01-01T00:00:00.000Z"
    result = pc_api.get_endpoint(
        "audits/firewall/app/container", {"from": from_field, "to": to_field, "sort": "time", "reverse": "true"}
    )
    cli_output(result)


@click.command()
@click.option("-l", "--limit", default=5, help="Number of documents to return")
def incidents(limit=5):
    last_hour_date_time = datetime.now() - timedelta(days=7)
    from_field = last_hour_date_time.strftime("%Y-%m-%dT%H:%M:%S.%f%z")[:-3] + "Z"
    to_field = "2030-01-01T00:00:00.000Z"
    result = pc_api.get_endpoint("audits/incidents", {"from": from_field, "to": to_field, "sort": "time", "reverse": "true"})
    cli_output(result)


@click.command()
@click.option("-i", "--id", help="Incident ID")
@click.option("-l", "--limit", default=5, help="Number of documents to return")
def snapshot(id="", limit=5):
    # We have an incident ID that we want to get the snapshot for
    # First we need to find the profile ID
    result = pc_api.get_endpoint("audits/incidents", {"id": id})
    profileID = result[0]["profileID"]

    # Log profileID found for incident ID
    logging.debug("Profile ID found for incident ID: " + str(profileID))

    # Now get the forensic snapshot
    result = pc_api.get_endpoint("profiles/container/" + profileID + "/forensic", {"incidentID": id})
    cli_output(result)


cli.add_command(container)
cli.add_command(firewall)
cli.add_command(incidents)
cli.add_command(snapshot)
