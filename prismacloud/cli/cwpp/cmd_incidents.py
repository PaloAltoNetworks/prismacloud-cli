import click
import logging
from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.group("incidents", short_help="Retrieves a list of incidents that are not acknowledged.")
@pass_environment
def cli(ctx):
    """Main command for interacting with incidents."""
    pass


@click.command(name="list")
@click.option("--limit", type=int, default=50, help="Number of reports to retrieve.")
@click.option("--search", type=str, help="Search term for the results.")
@click.option("--sort", type=str, help="Sort key for the results.")
@click.option("--reverse", is_flag=True, help="Flag to sort the results in reverse order.")
@click.option("--archived", is_flag=True, help="Flag to list archived incidents.")
@click.option("--host", type=str, help="Host for the incidents.")
@click.option("--cluster", type=str, help="Cluster for the incidents.")
@click.option("--type", type=str, help="Type of the incidents.")
@click.option("--category", type=str, help="Category of the incidents.")
@click.option("--collection", type=str, help="Collection for the incidents.")
@click.option("--provider", type=str, help="Provider for the incidents.")
@click.option("--from", "from_date", type=str, help="Starting date for the incidents.")
@click.option("--to", "to_date", type=str, help="Ending date for the incidents.")
def list_incidents(
    limit, search, sort, reverse, archived, host, cluster, type, category, collection, provider, from_date, to_date
):
    """List incidents based on the provided filters."""
    logging.debug("Preparing to retrieve incidents")
    query_params = {
        "limit": limit,
        "search": search,
        "sort": sort,
        "reverse": reverse,
        "archived": archived,
        "host": host,
        "cluster": cluster,
        "type": type,
        "category": category,
        "collection": collection,
        "provider": provider,
        "from": from_date,
        "to": to_date,
    }

    result = pc_api.execute_compute("GET", "api/v1/audits/incidents", query_params=query_params, paginated=True)

    logging.debug(f"Retrieved {len(result)} incidents")
    cli_output(result)


def handle_incidents(id, category, type, operation, all_flag):
    """
    Function to handle incidents based on the provided arguments.

    :param id: ID of the incident
    :param category: Category of the incident
    :param type: Type of the incident
    :param operation: Operation to perform on the incident
    :param all_flag: Flag indicating whether to perform the operation on all incidents
    """
    logging.debug(f"{operation.capitalize()} incidents...")
    changed_incidents = []
    if id:
        logging.debug(f"Handling single incident with ID: {id}")
        pc_api.execute_compute(
            "PATCH", f"api/v1/audits/incidents/acknowledge/{id}", body_params={"acknowledged": operation == "archive"}
        )
    else:
        # Get all incidents
        logging.debug("Retrieving all incidents...")
        incidents = pc_api.execute_compute("GET", "api/v1/audits/incidents", paginated=True)
        logging.debug(f"Retrieved {len(incidents)} incidents")

        unchanged_incidents_count = 0

        for incident in incidents:
            logging.debug(f"Inspecting incident with ID: {incident['_id']}")
            if category and incident.get("category") != category:
                logging.debug(f"Skipping incident {incident['_id']} due to category mismatch.")
                unchanged_incidents_count += 1
                continue
            if type and incident.get("type") != type:
                logging.debug(f"Skipping incident {incident['_id']} due to type mismatch.")
                unchanged_incidents_count += 1
                continue
            if "archived" in incident:
                if (operation == "archive" and incident["archived"]) or (operation == "restore" and not incident["archived"]):
                    logging.debug(f"Skipping incident {incident['_id']} due to archived status.")
                    unchanged_incidents_count += 1
                    continue
            logging.debug(f"{operation.capitalize()} incident: {incident['_id']}")
            pc_api.execute_compute(
                "PATCH",
                f"api/v1/audits/incidents/acknowledge/{incident['_id']}",
                body_params={"acknowledged": operation == "archive"},
            )
            changed_incidents.append(incident)

        logging.debug(f"Number of changed incidents: {len(changed_incidents)}")
        logging.debug(f"Number of unchanged incidents: {unchanged_incidents_count}")

    logging.debug(f"Finished {operation} incidents.")

    result = changed_incidents
    cli_output(result)


@click.command(name="archive")
@click.option("--id", type=str, help="ID of the incident to archive.")
@click.option("--category", type=str, help="Category of the incidents to archive.")
@click.option("--type", type=str, help="Type of the incidents to archive.")
@click.option("--all", "all_flag", is_flag=True, help="Flag to archive all incidents.")
def archive_incidents(id, category, type, all_flag):
    """Archive incidents based on the provided arguments."""
    if not any([id, category, type, all_flag]):
        logging.error("Please provide an option or use --all to archive all incidents.")
        return
    handle_incidents(id, category, type, "archive", all_flag)


@click.command(name="restore")
@click.option("--id", type=str, help="ID of the incident to restore.")
@click.option("--category", type=str, help="Category of the incidents to restore.")
@click.option("--type", type=str, help="Type of the incidents to restore.")
@click.option("--all", "all_flag", is_flag=True, help="Flag to restore all incidents.")
def restore_incidents(id, category, type, all_flag):
    """Restore incidents based on the provided arguments."""
    if not any([id, category, type, all_flag]):
        logging.error("Please provide an option or use --all to restore all incidents.")
        return
    handle_incidents(id, category, type, "restore", all_flag)


cli.add_command(list_incidents)
cli.add_command(archive_incidents)
cli.add_command(restore_incidents)
