import click
import logging
from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api

@click.group("incidents", short_help="Retrieves a list of incidents that are not acknowledged.")
@pass_environment
def cli(ctx):
    pass

@click.command(name="list")
@click.option('--offset', type=int, default=0, help="Offset for the report count.")
@click.option('--limit', type=int, default=50, help="Number of reports to retrieve.")
@click.option('--search', type=str, help="Search term for the results.")
@click.option('--sort', type=str, help="Sort key for the results.")
@click.option('--reverse', is_flag=True, help="Flag to sort the results in reverse order.")
@click.option('--archived', is_flag=True, help="Flag to list archived incidents.")
def list_incidents(offset, limit, search, sort, reverse, archived):
    logging.debug("Preparing to retrieve incidents")
    query_params = {
        'offset': offset,
        'limit': limit,
        'search': search,
        'sort': sort,
        'reverse': reverse,
        'archived': archived
    }
    result = pc_api.get_endpoint("audits/incidents", query_params=query_params)
    logging.debug(f"Retrieved {len(result)} incidents")
    cli_output(result)

def handle_incidents(id, category, type, operation):
    logging.debug(f"{operation.capitalize()} incidents...")
    if id:
        pc_api.execute_compute('PATCH', f"api/v1/audits/incidents/acknowledge/{id}", body_params={"acknowledged": operation == 'archive'})
    else:
        # Get all incidents
        incidents = pc_api.get_endpoint("audits/incidents")
        for incident in incidents:
            if category and incident['category'] != category:
                continue
            if type and incident['type'] != type:
                continue
            logging.debug(f"{operation.capitalize()} incident: {incident['_id']}")
            pc_api.execute_compute('PATCH', f"api/v1/audits/incidents/acknowledge/{incident['_id']}", body_params={"acknowledged": operation == 'archive'})

@click.command(name="archive")
@click.option('--id', type=str, help="ID of the incident to acknowledge.")
@click.option('--category', type=str, help="Category of incidents to acknowledge.")
@click.option('--type', type=str, help="Type of incidents to acknowledge.")
def archive_incidents(id, category, type):
    handle_incidents(id, category, type, 'archive')

@click.command(name="restore")
@click.option('--id', type=str, help="ID of the incident to restore.")
@click.option('--category', type=str, help="Category of incidents to restore.")
@click.option('--type', type=str, help="Type of incidents to restore.")
def restore_incidents(id, category, type):
    handle_incidents(id, category, type, 'restore')

cli.add_command(list_incidents)
cli.add_command(archive_incidents)
cli.add_command(restore_incidents)
import click
import logging
import json
from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api

@click.group("incidents", short_help="Retrieves a list of incidents that are not acknowledged.")
@pass_environment
def cli(ctx):
    pass

@click.command(name="list")
@click.option('--offset', type=int, default=0, help="Offset for the report count.")
@click.option('--limit', type=int, default=50, help="Number of reports to retrieve.")
@click.option('--search', type=str, help="Search term for the results.")
@click.option('--sort', type=str, help="Sort key for the results.")
@click.option('--reverse', is_flag=True, help="Flag to sort the results in reverse order.")
@click.option('--archived', is_flag=True, help="Flag to list archived incidents.")
def list_incidents(offset, limit, search, sort, reverse, archived):
    logging.debug("Preparing to retrieve incidents")
    query_params = {
        'offset': offset,
        'limit': limit,
        'search': search,
        'sort': sort,
        'reverse': reverse,
        'archived': archived
    }
    result = pc_api.get_endpoint("audits/incidents", query_params=query_params)
    logging.debug(f"Retrieved {len(result)} incidents")
    cli_output(result)

def handle_incidents(id, category, type, operation):
    logging.debug(f"{operation.capitalize()} incidents...")
    changed_incidents = []
    if id:
        pc_api.execute_compute('PATCH', f"api/v1/audits/incidents/acknowledge/{id}", body_params={"acknowledged": operation == 'archive'})
    else:
        # Get all incidents
        incidents = pc_api.get_endpoint("audits/incidents")
        for incident in incidents:
            if category and incident['category'] != category:
                continue
            if type and incident['type'] != type:
                continue
            logging.debug(f"{operation.capitalize()} incident: {incident['_id']}")
            pc_api.execute_compute('PATCH', f"api/v1/audits/incidents/acknowledge/{incident['_id']}", body_params={"acknowledged": operation == 'archive'})
            changed_incidents.append(incident)

    result = changed_incidents
    cli_output(result)

@click.command(name="archive")
@click.option('--id', type=str, help="ID of the incident to acknowledge.")
@click.option('--category', type=str, help="Category of incidents to acknowledge.")
@click.option('--type', type=str, help="Type of incidents to acknowledge.")
def archive_incidents(id, category, type):
    handle_incidents(id, category, type, 'archive')

@click.command(name="restore")
@click.option('--id', type=str, help="ID of the incident to restore.")
@click.option('--category', type=str, help="Category of incidents to restore.")
@click.option('--type', type=str, help="Type of incidents to restore.")
def restore_incidents(id, category, type):
    handle_incidents(id, category, type, 'restore')

cli.add_command(list_incidents)
cli.add_command(archive_incidents)
cli.add_command(restore_incidents)
