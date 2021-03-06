import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.group("cwpp_registry", short_help="[CWPP] Scan reports for images in your registry.")
@pass_environment
def cli(ctx):
    pass


@click.command()
@click.option("--field", default="")
def runtimecontainer(field=""):
    result = pc_api.get_endpoint("registry")

    if field == "":
        cli_output(result)
    else:
        # We have field as input to select a deeper level of data.
        # Our main result returns data on the query and the results are in one of the main field.
        # This option gives the ability to retrieve that data.
        field_path = field.split(".")
        for _field in field_path:
            result = result[_field]

        cli_output(result)


cli.add_command(runtimecontainer)
