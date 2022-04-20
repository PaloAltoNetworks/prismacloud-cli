""" Prisma Cloud CLI Configuration and Output """

import logging
import os
import sys
import warnings

import click
import click_completion
import coloredlogs
import pandas as pd
from click_help_colors import HelpColorsMultiCommand
from pydantic import BaseSettings
from tabulate import tabulate
from update_checker import UpdateChecker

import prismacloud.cli.version as cli_version

click_completion.init()

# Set defaults
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", 4)
pd.set_option("display.width", 100)
pd.set_option("display.colheader_justify", "center")
pd.set_option("display.precision", 3)
warnings.simplefilter(action="ignore", category=FutureWarning)


def get_available_version():
    # Get available python package version
    try:
        checker = UpdateChecker()
        result = checker.check("prismacloud-cli", cli_version.version)
        # Show available version
        logging.debug("Available version: %s", result.available_version)
        update_available = result.available_version
    except Exception:  # nosec
        update_available = False

    if update_available:
        update_available_text = """\b
Update available: {} -> {}
Run {} to update
        """.format(cli_version.version, update_available, click.style("pip3 install -U prismacloud-cli", fg="red"))
    else:
        update_available_text = ""

    return update_available_text


class Settings(BaseSettings):
    """ Prisma Cloud CLI Settings """

    app_name: str = "Prisma Cloud CLI"
    max_columns: int = 7
    max_rows: int = 1000000
    max_width: int = 25


settings = Settings()


CONTEXT_SETTINGS = dict(auto_envvar_prefix="PC")


class Environment:
    """Initialize environment and define logging"""

    def __init__(self):
        """Initialize environment"""
        self.verbose = False
        self.home = os.getcwd()

    # pylint: disable=R0201
    def log(self, msg, *args):
        """Logs a message to stderr"""
        if args:
            msg %= args
        click.echo(msg, file=sys.stderr)

    def vlog(self, msg, *args):
        """Logs a message to stderr only if verbose is enabled"""
        if self.verbose:
            self.log(msg, *args)


pass_environment = click.make_pass_decorator(Environment, ensure=True)
cwpp_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "cwpp"))
cspm_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "cspm"))
pccs_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "pccs"))


class PrismaCloudCLI(HelpColorsMultiCommand):
    """Collect commands"""

    def list_commands(self, ctx):
        """Read commands from command files"""
        commands = []

        # Iterate through cwpp commands
        for filename in os.listdir(cwpp_folder):
            if filename.endswith(".py") and filename.startswith("cmd_"):
                commands.append(filename[4:-3])
        # Iterate through cspm commands
        for filename in os.listdir(cspm_folder):
            if filename.endswith(".py") and filename.startswith("cmd_"):
                commands.append(filename[4:-3])
        # Iterate through pccs commands
        for filename in os.listdir(pccs_folder):
            if filename.endswith(".py") and filename.startswith("cmd_"):
                commands.append(filename[4:-3])

        commands.sort()
        return commands

    # pylint: disable=R1710
    def get_command(self, ctx, cmd_name):
        """Import command"""

        # Find the command file and import it.
        # This file can be in the cwpp folder, cspm folder, or pccs folder.

        module_types = ["cwpp", "cspm", "pccs"]

        for module_type in module_types:
            try:
                mod = __import__(f"prismacloud.cli.{module_type}.cmd_{cmd_name}", None, None, ["cli"])
            except ImportError:
                continue
            return mod.cli


@click.command(
    cls=PrismaCloudCLI,
    context_settings=CONTEXT_SETTINGS,
    help_headers_color='yellow',
    help_options_color='green',
    help="""
\b
Prisma Cloud CLI (version: {0})
{1}
""".format(
        cli_version.version, get_available_version()
    ),
)
@click.option("-v", "--verbose", is_flag=True, help="Enables verbose mode")
@click.option("-vv", "--very_verbose", is_flag=True, help="Enables very verbose mode")
@click.option("--filter", help="Add search filter")
@click.option("-o", "--output", type=click.Choice(["text", "csv", "json", "html", "columns"]), default="text")
@click.option(
    "-c",
    "--config",
    "configuration",
    help="Select configuration file in ~/.prismacloud/[CONFIGURATION].json",
    default="credentials",
)
@click.option("--columns", "columns", help="Select columns for output", default=None)
@pass_environment
# pylint: disable=W0613
def cli(ctx, very_verbose, verbose, configuration, output, filter, columns=None):
    """Define the command line"""
    ctx.configuration = configuration
    ctx.output = output

    if verbose:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
        coloredlogs.install(level="INFO")
    elif very_verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
        coloredlogs.install(level="DEBUG")
    else:
        logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")
        coloredlogs.install(level="ERROR")


def cli_output(data, sort_values=False):
    """ Parse data and format output """
    # Retrieve parameters
    params = click.get_current_context().find_root().params
    if params["columns"]:
        columns = params["columns"].split(",")
    # Check type of data
    if isinstance(data, list):
        data_frame = pd.DataFrame(data)

    # If we are in debugging mode, show settings for output
    logging.debug("Settings: maximum width: %s", settings.max_width)
    logging.debug("Settings: maximum number of rows: %s", settings.max_rows)
    logging.debug("Settings: maximum number of columns: %s", settings.max_columns)

    # We have data from our request, send to dataframe
    try:
        data_frame_normalized = pd.json_normalize(data)

        # If the size of our normalized data is 0, something went wrong
        # and we don't use the normalized data.
        # Otherwise, use the normalized data.
        if data_frame_normalized.size > 0:
            logging.debug("Using normalized data")
            data_frame = data_frame_normalized
            # Flatten nested json
            data_frame = flatten_nested_json_df(data_frame)

        # Do some optimization on our dataframe
        try:
            data_frame["time"] = pd.to_datetime(data_frame.time)
            data_frame["lastModified"] = pd.to_datetime(data_frame.time)
            data_frame.fillna("", inplace=True)
        except Exception:  # pylint:disable=broad-except
            logging.debug("No time field")

        # If column name contains time or lastModified, convert values to datetime
        for column in data_frame.columns:
            if "time" in column.lower() or "lastmodified" in column.lower() or "availableAsOf" in column.lower():
                try:
                    data_frame[column] = pd.to_datetime(data_frame[column], unit='ms')
                except Exception as _exc:
                    logging.debug("Error: %s", _exc)
                try:
                    data_frame[column] = pd.to_datetime(data_frame[column], unit='s')
                except Exception as _exc:
                    logging.debug("Error: %s", _exc)

        # If a filter is set, apply it
        if params["filter"]:
            try:
                data_frame = data_frame.query(params["filter"])
            except Exception as _exc:
                logging.error("Error: %s", _exc)
                exit(1)

        # Drop all rows after max_rows
        data_frame = data_frame.head(settings.max_rows)

        # We have a dataframe, output here after we have dropped
        # all but the selected columns
        if params["columns"]:
            logging.debug("Dropping these columns: %s", data_frame.columns.difference(columns))
            data_frame.drop(columns=data_frame.columns.difference(columns),
                            axis=1, inplace=True, errors="ignore")
        else:
            pass

        if params["output"] == "text":
            # Drop all but first settings.max_columns columns from data_frame
            data_frame.drop(data_frame.columns[settings.max_columns:], axis=1, inplace=True)

            # Truncate all cells
            data_frame_truncated = data_frame.applymap(do_truncate, na_action='ignore')
            click.secho(tabulate(data_frame_truncated, headers="keys", tablefmt="table"),
                        fg="green")
        if params["output"] == "json":
            click.secho(data_frame.to_json(orient="records"), fg="green")
        if params["output"] == "csv":
            click.secho(data_frame.to_csv(), fg="green")
        if params["output"] == "html":
            # pre-table-html
            pre_table_html = """

<html>
<head>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.0.0/dist/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">
</head>
                """  # noqa
            click.secho(pre_table_html)
            click.secho(
                data_frame.to_html(
                    max_cols=settings.max_columns,
                    na_rep='',
                    classes="table table-sm table-striped text-left",
                    justify="left"
                    ),
                fg="green")
            # post-table-html
            post_table_html = """

    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.2/js/bootstrap.min.js"></script>
</html>

                """  # noqa
            click.secho(post_table_html)
        if params["output"] == "columns":
            for column in data_frame.columns:
                click.secho(column, fg="green")
    except Exception as _exc:  # pylint:disable=broad-except
        # There is no dataframe, might be just a single value, like version.
        click.echo(data)
        logging.debug("Error ingesting data into dataframe: %s", _exc)


def flatten_nested_json_df(data_frame):
    """ Flatten nested json in our dataframe """
    logging.debug("Flatten nested json")
    data_frame = data_frame.reset_index()
    temp_s = (data_frame.applymap(type) == list).all()
    list_columns = temp_s[temp_s].index.tolist()

    temp_s = (data_frame.applymap(type) == dict).all()
    dict_columns = temp_s[temp_s].index.tolist()

    while len(list_columns) > 0 or len(dict_columns) > 0:
        new_columns = []

        for col in dict_columns:
            horiz_exploded = pd.json_normalize(data_frame[col]).add_prefix(f'{col}.')
            horiz_exploded.index = data_frame.index
            data_frame = pd.concat([data_frame, horiz_exploded], axis=1).drop(columns=[col])
            new_columns.extend(horiz_exploded.columns)  # inplace

        for col in list_columns:
            logging.debug(f"exploding: {col}")
            data_frame = data_frame.drop(columns=[col]).join(data_frame[col].explode().to_frame())
            new_columns.append(col)

        temp_s = (data_frame[new_columns].applymap(type) == list).all()
        list_columns = temp_s[temp_s].index.tolist()

        temp_s = (data_frame[new_columns].applymap(type) == dict).all()
        dict_columns = temp_s[temp_s].index.tolist()
    return data_frame


def do_truncate(truncate_this):
    """Truncate a string to max_width characters"""
    try:
        truncate_this = str(truncate_this)
        if len(truncate_this) > settings.max_width:
            return truncate_this[:settings.max_width] + "..."
        return truncate_this
    except Exception as _exc:  # pylint:disable=broad-except
        logging.debug("Error truncating: %s", _exc)


if __name__ == "__main__":
    try:
        # Get update_available_text
        update_available_text = get_available_version()

        # pylint: disable=E1120
        cli()
    except Exception as exc:  # pylint:disable=broad-except
        logging.error("An error has occured: %s", exc)
