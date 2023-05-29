import click

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
def list_incidents(offset, limit, search, sort, reverse):
    query_params = {
        'offset': offset,
        'limit': limit,
        'search': search,
        'sort': sort,
        'reverse': reverse
    }
    result = pc_api.get_endpoint("audits/incidents", query_params=query_params)
    cli_output(result)

cli.add_command(list_incidents)
