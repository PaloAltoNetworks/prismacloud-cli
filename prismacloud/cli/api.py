""" CLI Configuration and Prisma Cloud API Library Wrapper """

import json
import logging
import os
import sys
import types

try:
    from pathlib import Path

    home_directory = str(Path.home())
except Exception as _exc:  # pylint:disable=broad-except
    logging.debug("Error identifying home directory: %s", _exc)
    if "USERPROFILE" in os.environ:
        home_directory = os.environ["USERPROFILE"]
    else:
        home_directory = os.environ["HOME"]

import click

# pylint: disable=import-error,no-name-in-module
from prismacloud.api import pc_api, PrismaCloudUtility as pc_util
import prismacloud.api.version as api_version
import prismacloud.cli.version as cli_version


""" CLI Configuration """


def community_supported():
    """If the community supported message has not been accepted yet,
    it must be shown with the possibility to accept."""

    community_supported_message = """
# Community Supported

This solution is released under an as-is, best-effort, support policy.

This solution should be seen as community-supported, and Palo Alto Networks will
contribute our expertise as and when possible. We do not provide technical support
or help in using or troubleshooting the components of this solution through our normal
support options such as Palo Alto Networks support teams, Authorized Support Centers,
partners, and backline support options. The underlying product (Prisma Cloud) used
by these scripts is still supported, but the support is only for the product
functionality itself and not for help in using this solution itself.

Unless explicitly tagged, all projects or work posted in our GitHub organization
(at https://github.com/PaloAltoNetworks) or sites other than our official Downloads page
(on https://support.paloaltonetworks.com) are provided under this policy.
"""

    # Check if the message already has been accepted.
    config_directory = home_directory + "/.prismacloud/"
    community_support_accepted = config_directory + ".community_supported_accepted"
    if os.path.exists(community_support_accepted):
        return True
    print(community_supported_message)
    answer = input("Enter 'y' or 'yes' to confirm you have read the message above: ")
    print()
    if any(answer.lower() == f for f in ["y", "yes"]):
        print("Message confirmed.")
        print()
        # Create file to verify that the message already has been accepted.
        if not os.path.exists(config_directory):
            logging.info("Configuration directory does not exist, creating %s", config_directory)
            try:
                os.makedirs(config_directory)
            except Exception as exc:  # pylint:disable=broad-except
                logging.info("Error creating configuration directory: %s", exc)
        with open(community_support_accepted, "w") as _accepted:
            _accepted.write("Yes")
    else:
        print("You need to confirm the message above to use this command. Exiting.")
        print()
        sys.exit(1)
    return True


def read_cli_config_from_environment():
    """Read configuration from environment"""
    logging.debug("Reading configuration from environment")
    settings = {}
    try:
        # API Key              Current CLI ENV VAR           Deprecated CLI ENV VAR(s)
        settings["name"] = os.environ.get("PC_NAME", "")
        settings["url"] = os.environ.get(
            "PC_URL", os.environ.get("PC_SAAS_API_ENDPOINT", os.environ.get("PC_COMPUTE_API_ENDPOINT", ""))
        )
        settings["identity"] = os.environ.get("PC_IDENTITY", os.environ.get("PC_ACCESS_KEY", ""))
        settings["secret"] = os.environ.get("PC_SECRET", os.environ.get("PC_SECRET_KEY", ""))
        settings["verify"] = os.environ.get("PC_VERIFY", os.environ.get("PC_CA_BUNDLE", False))
        # Normalize URL.
        settings["url"] = pc_util.normalize_api(settings["url"])
        # Mask all except the first two characters of keys when debugging.
        masked_identity = settings["identity"][:3] + "*" * (len(settings["identity"]) - 4)
        masked_secret = settings["secret"][:3] + "*" * (len(settings["secret"]) - 4)
        logging.debug("Environment variable found: PC_URL/PC_SAAS_API_ENDPOINT/PC_COMPUTE_API_ENDPOINT: %s", settings["url"])
        logging.debug("Environment variable found: PC_IDENTITY/PC_ACCESS_KEY: %s", masked_identity)
        logging.debug("Environment variable found: PC_SECRET/PC_SECRET_KEY: %s", masked_secret)
    except Exception as exc:  # pylint:disable=broad-except
        logging.debug("Error reading configuration from environment: %s", exc)
    logging.debug("Configuration read from environment")
    return settings


def get_cli_config():
    """
    Try to access params["configuration"].
    If it is equal to env or environment, try to read the following environment variables.

        # Current CLI ENV VAR      Deprecated CLI ENV VAR(s)
        PC_URL                     PC_SAAS_API_ENDPOINT, PC_COMPUTE_API_ENDPOINT
        PC_IDENTITY                PC_ACCESS_KEY
        PC_SECRET                  PC_SECRET_KEY
        PC_VERIFY                  PC_CA_BUNDLE

    If PC_URL, PC_IDENTITY and PC_SECRET are not set, try to read the configuration file specified by params["configuration"].
    The PC_VERIFY setting can be a boolean or a string path to a file, as per the 'verify' parameter of requests.request().
    """

    logging.info("Running prismacloud-cli version %s / prismacloud-api version %s", cli_version.version, api_version.version)

    community_supported()  # Check if support message has been shown and accepted

    params = {}
    try:
        params = click.get_current_context().find_root().params
    except Exception as exc:  # pylint:disable=broad-except
        logging.debug("Error getting current context to find root params: %s", exc)
        params["configuration"] = "credentials"

    # To fix calling 'pc' without a command.
    if "configuration" not in params:
        params["configuration"] = "credentials"

    # Try to read configuration from environment.
    if params["configuration"] in ["env", "environment"]:
        config_env_settings = read_cli_config_from_environment()
        if config_env_settings:
            return config_env_settings

    # Read (or write) configuration from (or to) a file.
    config_directory = home_directory + "/.prismacloud/"
    config_file_name = config_directory + params["configuration"] + ".json"
    if not os.path.exists(config_file_name):
        config_file_name = config_directory + params["configuration"] + ".conf"

    if os.path.exists(config_file_name):
        settings = read_cli_config_file(config_file_name)
        # API Key              Current CLI Key               Deprecated CLI Key(s)
        settings["url"] = settings.get(
            "url",
            settings.pop(
                "api_endpoint", settings.pop("api", settings.pop("pcc_api_endpoint", settings.pop("api_compute", "")))
            ),
        )
        settings["identity"] = settings.get("identity", settings.pop("access_key_id", settings.pop("username", "")))
        settings["secret"] = settings.get("secret", settings.pop("secret_key", settings.pop("password", "")))
        settings["verify"] = settings.get("verify", settings.pop("ca_bundle", False))
        # Normalize URL.
        settings["url"] = pc_util.normalize_api(settings["url"])
    else:
        if not os.path.exists(config_directory):
            logging.info("Configuration directory does not exist, creating %s", config_directory)
            try:
                os.makedirs(config_directory)
            except Exception as exc:  # pylint:disable=broad-except
                logging.info("Error creating configuration directory: %s", exc)
        settings = {
            "url": input(
                "Prisma Cloud Tenant (or Compute Console, if PCCE) URL, eg: api.prismacloud.io or twistlock.example.com"
            ),
            "identity": input("Access Key (or Compute Username, if PCCE): "),
            "secret": input("Secret Key (or Compute Password, if PCCE): "),
            "verify": False,
        }
        # Normalize URL.
        settings["url"] = pc_util.normalize_api(settings["url"])
        write_cli_config_file(config_file_name, settings)
    return settings


def map_cli_config_to_api_config():
    """Map keys between the Prisma Cloud API package and Prisma Cloud CLI package"""
    try:
        click.get_current_context()
    except Exception as exc:  # pylint:disable=broad-except
        logging.debug("Error getting current context: %s", exc)
    settings = get_cli_config()
    return {
        # API Key      Current CLI Key          Deprecated CLI Key(s)
        "name": settings.get("name", ""),
        "url": settings.get(
            "url",
            settings.get(
                "api_endpoint", settings.get("api", settings.get("pcc_api_endpoint", settings.get("api_compute", "")))
            ),
        ),
        "identity": settings.get("identity", settings.get("access_key_id", settings.get("username", ""))),
        "secret": settings.get("secret", settings.get("secret_key", settings.get("password", ""))),
        "verify": settings.get("verify", settings.get("ca_bundle", False)),
    }


def read_cli_config_file(config_file_name):
    """Read cli configuration from a file"""
    logging.debug("Reading configuration from file: %s", config_file_name)
    config_file_settings = {}
    try:
        with open(config_file_name, "r") as config_file:
            config_file_settings = json.load(config_file)
    except Exception as exc:  # pylint:disable=broad-except
        logging.info("Error reading configuration from file: %s", exc)
    logging.debug("Configuration read from file: %s", config_file_name)
    return config_file_settings


def write_cli_config_file(config_file_name, config_file_settings):
    """Write cli configuration to a file"""
    logging.debug("Writing configuration to file: %s", config_file_name)
    try:
        json_string = json.dumps(config_file_settings, sort_keys=True, indent=4)
        with open(config_file_name, "w") as config_file:
            config_file.write(json_string)
    except Exception as exc:  # pylint:disable=broad-except
        logging.info("Error writing configuration to file: %s", exc)
    logging.debug("Configuration written to file: %s", config_file_name)


""" Prisma Cloud API Library Wrapper """


def get_endpoint(_self, endpoint, query_params=None, api="cwpp", request_type="GET"):
    """Make a request without using an endpoint-specific method"""
    pc_api.configure(map_cli_config_to_api_config())
    logging.debug("Calling API Endpoint (%s): %s", request_type, endpoint)
    result = None
    if api == "cspm":
        try:
            result = pc_api.execute(request_type, endpoint, query_params)
        except Exception as exc:  # pylint:disable=broad-except
            logging.error(
                "There was an error executing the request. Check if this API (CSPM) is available in your environment."
            )  # noqa: E501
            logging.error("Please check your config and try again. Error: %s", exc)  # noqa: E501
            sys.exit(1)
    if api == "cwpp":
        if not endpoint.startswith("api"):
            endpoint = "api/v1/%s" % endpoint
            try:
                result = pc_api.execute_compute(request_type, endpoint, query_params)
            except Exception as exc:  # pylint:disable=broad-except
                logging.error(
                    "There was an error executing the request. Check if this API (CWP) is available in your environment."
                )  # noqa: E501
                logging.error("Please check your config and try again. Error: %s", exc)  # noqa: E501
                sys.exit(1)
    if api == "code":
        try:
            result = pc_api.execute_code_security(request_type, endpoint, query_params)
        except Exception as exc:  # pylint:disable=broad-except
            logging.error(
                "There was an error executing the request. Check if this API (CCS) is available in your environment."
            )  # noqa: E501
            logging.error("Please check your config and try again. Error: %s", exc)  # noqa: E501
            sys.exit(1)
    return result


""" Instance of the Prisma Cloud API """

pc_api.configure(map_cli_config_to_api_config())
# Add the get_endpoint method to this instance.
pc_api.get_endpoint = types.MethodType(get_endpoint, pc_api)
