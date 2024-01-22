""" Prisma Cloud CLI Configuration and Output """

import logging
import os
import sys
import warnings
import re
import textwrap
import json
import ast


import click
import click_completion
import coloredlogs
import pandas as pd
from click_help_colors import HelpColorsMultiCommand
from pydantic_settings import BaseSettings
from typing import Optional
from tabulate import tabulate
from update_checker import UpdateChecker

import prismacloud.cli.version as cli_version

click_completion.init()

# Set defaults
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", 400)
pd.set_option("display.width", 1000)
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
    except Exception:  # pylint:disable=broad-except
        update_available = False

    if update_available:
        update_available_text_block = """\b
Update available: {} -> {}
Run {} to update
        """.format(
            cli_version.version, update_available, click.style("pip3 install -U prismacloud-cli", fg="red")
        )
    else:
        update_available_text_block = ""

    return update_available_text_block


class Settings(BaseSettings):  # pylint:disable=too-few-public-methods
    """Prisma Cloud CLI Settings"""

    app_name: str = "Prisma Cloud CLI"
    max_columns: int = 7
    max_rows: int = 1000000
    max_width: int = 25
    max_levels: int = 2
    max_lines: int = 10

    url: Optional[str] = None
    identity: Optional[str] = None
    secret: Optional[str] = None


settings = Settings()


CONTEXT_SETTINGS = dict(auto_envvar_prefix="PC")


class Environment:
    """Initialize environment and define logging"""

    def __init__(self):
        """Initialize environment"""
        self.verbose = False
        self.home = os.getcwd()

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
    help_headers_color="yellow",
    help_options_color="green",
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
@click.option("--filter", "query_filter", help="Add search filter")
@click.option(
    "-o",
    "--output",
    type=click.Choice(["text", "csv", "json", "html", "clipboard", "markdown", "columns", "raw", "count"]),
    default="text",
)
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
def cli(ctx, very_verbose, verbose, configuration, output, query_filter, columns=None):
    """Define the command line"""
    ctx.configuration = configuration
    ctx.output = output
    log_format = "%(asctime)s - %(levelname)s - %(message)s"

    if verbose:
        coloredlogs.install(level="INFO", fmt=log_format)
    elif very_verbose:
        coloredlogs.install(level="DEBUG", fmt=log_format)
    else:
        coloredlogs.install(level="ERROR", fmt=log_format)


def get_parameters():
    """Get parameters from command line"""

    # Retrieve parameters
    params = click.get_current_context().find_root().params

    # If there is a parameter columns, split it into a list
    if params["columns"]:
        columns = params["columns"].split(",")
    else:
        columns = False

    return params, columns


def log_settings():
    """Log settings"""
    logging.debug("Settings:")
    logging.debug("  Max columns: %s", settings.max_columns)
    logging.debug("  Max rows: %s", settings.max_rows)
    logging.debug("  Max width: %s", settings.max_width)
    logging.debug("  Max levels: %s", settings.max_levels)


def process_data_frame(data):
    params, columns = get_parameters()
    # https://pandas.pydata.org/docs/reference/api/pandas.json_normalize.html
    # json_normalize() requires a dictionary or list of dictionaries
    # normalize = False
    # if isinstance(data, dict):
    #     normalize = True
    # if isinstance(data, list):
    #     if all(isinstance(item, dict) for item in data)
    #         normalize = True
    try:
        data_frame_normalized = pd.json_normalize(data)
    except Exception as _exc:  # pylint:disable=broad-except
        logging.error("Error converting data via json_normalize(): %s", _exc)
        sys.exit(1)

    # If the size of our normalized data is 0, something went wrong but no exception was raised.
    if data_frame_normalized.size > 0:
        logging.debug("Using json_normalize() data")
        # data_frame = flatten_nested_json_df(data_frame_normalized)
        data_frame = data_frame_normalized
    else:
        try:
            data_frame = pd.DataFrame(data)
        except Exception as _exc:  # pylint:disable=broad-except
            logging.error("Error converting data via DataFrame(): %s", _exc)
            sys.exit(1)

    # If a column contains time, try convert it to datetime
    for column in str(data_frame.columns):
        if column.lower() in ["time", "lastmodified", "availableasof"]:
            try:
                data_frame[column] = pd.to_datetime(data_frame[column], unit="ms")
            except Exception as _exc2:  # pylint:disable=broad-except
                logging.debug("Error converting column to milliseconds: %s", _exc2)
                try:
                    data_frame[column] = pd.to_datetime(data_frame[column], unit="s")
                except Exception as _exc3:  # pylint:disable=broad-except
                    logging.debug("Error converting column to seconds: %s", _exc3)

    data_frame.fillna("", inplace=True)

    # If a filter is set, try to apply it
    if params["query_filter"]:
        try:
            data_frame = data_frame.query(params["query_filter"])
        except Exception as _exc:  # pylint:disable=broad-except
            logging.error("Error applying query filter: %s", _exc)
            logging.error("You might be filtering on a dynamic column.")
            logging.error("For example, if a certain tag does not exist, there is no way to filter on it.")
            logging.error("The given filter has not been applied.")

    # The usage command generates columns starting with dataPoints
    try:
        # If we have one or more columns with dataPoints.counts,
        # calculate the sum of all columns starting with dataPoints.counts
        if len(data_frame.filter(regex="dataPoints.counts").columns) > 0:
            data_frame["used"] = data_frame.filter(regex="dataPoints.counts").sum(axis=1)
        # Calculate a new column usage based as percentage on column used and column workloadsPurchased
        # If we have a column named workloadsPurchased, we can calculate the percentage
        if "workloadsPurchased" in data_frame.columns:
            data_frame["usage"] = data_frame["used"] / data_frame["workloadsPurchased"] * 100
        # Extra columns are added, proceed.
    except Exception as _exc:  # pylint:disable=broad-except
        logging.debug("Error calculating columns: %s", _exc)

    # Change all nan values to empty string
    data_frame = data_frame.fillna("")

    # We have a dataframe, output here after we have dropped all but the selected columns
    if params["columns"]:
        # logging.debug("Dropping these columns: %s", data_frame.columns.difference(columns))
        # data_frame.drop(columns=data_frame.columns.difference(columns),
        #                 axis=1, inplace=True, errors="ignore")

        # Find columns in data_frame whose name contains one of the
        # values of parameter columns and filter on the resulting columns
        regex_ = r"(" + "|".join(columns) + ")"
        logging.debug("Filtering columns based on case-insensitive regex: %s", regex_)
        data_frame = data_frame.filter(regex=re.compile("(" + "|".join(columns) + ")", re.I))

    # Before we show the output, remove the index column (which is not data_frame.index),
    # but only if the column exists.
    if "index" in data_frame.columns:
        data_frame.drop(columns=["index"], inplace=True)

    # Before we show the output, try to remove duplicate rows
    try:
        # Convert all columns to string
        data_frame = data_frame.applymap(str)
        data_frame = data_frame.drop_duplicates()
    except Exception as _exc:  # pylint:disable=broad-except
        logging.debug("Error dropping duplicates: %s", _exc)

    return data_frame


def cli_output(data, sort_values=False):
    """Parse data and formay output, except if we"""
    """want to see raw json."""
    params = get_parameters()[0]
    log_settings()  # Log settings in debug level

    if params["output"] == "raw":
        click.secho(json.dumps(data))
        sys.exit(1)

    # Read data, convert to dataframe and process it
    data_frame = process_data_frame(data)

    # Generate and show the output
    show_output(data_frame, params, data)


def json_parse(json_data, level=0):
    if isinstance(json_data, (dict, list)):
        json_obj = json.loads(json.dumps(json_data))
    else:
        json_obj = json.loads(json_data)

    output_str = ""
    indent = "  " * level
    if isinstance(json_obj, list):
        for item in json_obj:
            output_str += json_parse(item, level)
    elif isinstance(json_obj, dict):
        for key, value in json_obj.items():
            if isinstance(value, (dict, list)):
                output_str += f"{indent}{key}:\n"
                output_str += json_parse(value, level + 1)
            else:
                output_str += f"{indent}{key}: {value}\n"

    return output_str + "\n" * (level == 0)


def wrap_text(text):
    """Truncate a string to max_width characters"""

    try:
        data = json.loads(text)
        if isinstance(data, (list, dict)):
            text = json_parse(data)
    except json.decoder.JSONDecodeError:
        pass

    try:
        data = ast.literal_eval(text)
        if isinstance(data, (list, dict)):
            text = json_parse(data)
    except (SyntaxError, ValueError):
        pass
    wrapped_text = textwrap.fill(text=text, width=settings.max_width, max_lines=settings.max_lines, replace_whitespace=False)
    return wrapped_text


def show_output(data_frame, params, data):
    try:
        if params["output"] == "count":
            click.secho(data_frame.shape[0], fg="red")
        if params["output"] == "text":
            # Drop all rows after max_rows
            data_frame = data_frame.iloc[: settings.max_rows]

            # Drop all but first settings.max_columns columns from data_frame
            data_frame = data_frame.iloc[:, : settings.max_columns]

            # Wrap all cells
            data_frame_truncated = data_frame.applymap(wrap_text, na_action="ignore")

            # Wrap column names
            data_frame_truncated.columns = list(map(wrap_text, data_frame_truncated.columns))

            table_output = tabulate(data_frame_truncated, headers="keys", tablefmt="fancy_grid", showindex=False)
            click.secho(table_output, fg="green")
        if params["output"] == "json":
            # Cannot use 'index=False' here, otherwise '.to_json' returns a hash instead of an array of hashes.
            # But '.to_json' does not output the index anyway.
            click.secho(data_frame.to_json(orient="records"), fg="green")
        if params["output"] == "csv":
            click.secho(data_frame.to_csv(index=False), fg="green")
        if params["output"] == "clipboard":
            click.secho(data_frame.to_clipboard(index=False), fg="green")
        if params["output"] == "markdown":
            # Drop all rows after max_rows
            data_frame = data_frame.iloc[: settings.max_rows]

            # Drop all but first settings.max_columns columns from data_frame
            data_frame = data_frame.iloc[:, : settings.max_columns]

            # Wrap all cells
            data_frame_truncated = data_frame.applymap(wrap_text, na_action="ignore")

            # Wrap column names
            data_frame_truncated.columns = list(map(wrap_text, data_frame_truncated.columns))

            click.secho(data_frame_truncated.to_markdown(index=False), fg="green")
        if params["output"] == "html":
            # pre-table-html
            pre_table_html = """

<html>
<head>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" integrity="sha384-T3c6CoIi6uLrA9TneNEoa7RxnatzjcDSCmG1MXxSR1GAsXEV/Dwwykc2MPK8M2HN" crossorigin="anonymous">

</head>
<body>
                """  # noqa
            click.secho(pre_table_html)
            click.secho(
                data_frame.to_html(
                    index=False,
                    max_cols=settings.max_columns,
                    na_rep="",
                    classes="table table-sm table-striped text-left",
                    justify="left",
                ),
                fg="green",
            )
            # post-table-html
            post_table_html = """

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js" integrity="sha384-C6RzsynM9kWDrMNeT87bh95OGNyZPhcTNXj1NW7RuBCsyN/o0jlpcV8Qyq46cDfL" crossorigin="anonymous"></script>
</body>
</html>

                """  # noqa
            click.secho(post_table_html)
        if params["output"] == "columns":
            for column in data_frame.columns:
                click.secho(column, fg="green")
    except Exception as _exc:  # pylint:disable=broad-except
        # There is no dataframe, might be just a single value, like version.
        click.echo(data)
        logging.debug("Error: %s", _exc)
        # We have shown normal data through this exception.
        # Exit with code 0 instead of 1.
        sys.exit(0)


if __name__ == "__main__":
    try:
        # Get update_available_text
        update_available_text = get_available_version()

        # pylint: disable=E1120
        cli()
    except Exception as exc:  # pylint:disable=broad-except
        logging.error("An error has occured: %s", exc)
