""" CLI Configuration and Prisma Cloud API Library Wrapper """

import json
import logging
import os
import types

try:
    from pathlib import Path
    home_directory = str(Path.home())
except Exception as _exc:  # pylint:disable=broad-except
    logging.debug("Error identifying home directory using pathlib: %s", _exc)
    if "USERPROFILE" in os.environ:
        home_directory = os.environ["USERPROFILE"]
    else:
        home_directory = os.environ["HOME"]

import click
from prismacloud.api import pc_api, PrismaCloudUtility as pc_util
import prismacloud.api.version as api_version
import prismacloud.cli.version as cli_version


""" CLI Configuration """


def map_cli_config_to_api_config():
    """Map cli configuration to api configuration"""
    try:
        click.get_current_context()
    except Exception as exc:  # pylint:disable=broad-except
        logging.debug("Error getting current context: %s", exc)
    settings = get_cli_config()
    # Map keys between API and CLI.
    return {
        "api":         settings["api_endpoint"],
        "api_compute": settings["pcc_api_endpoint"],
        "username":    settings["access_key_id"],
        "password":    settings["secret_key"],
        "ca_bundle":   settings["ca_bundle"],
    }


def community_supported():
    """If the community supported message has not been accepted yet, it must be shown
    with the possibility to accept."""
    community_supported_message = """# Community Supported
This template/solution is released under an as-is, best effort,
support policy. These scripts should be seen as community
supported and Palo Alto Networks will contribute our expertise as
and when possible. We do not provide technical support or help in
using or troubleshooting the components of the project through our
normal support options such as Palo Alto Networks support teams,
or ASC (Authorized Support Centers) partners and backline support
options. The underlying product used (Prisma Cloud) by the scripts
or templates are still supported, but the support is only for the
product functionality and not for help in deploying or using the
template or script itself.

Unless explicitly tagged, all projects or work posted in our
GitHub repository (at https://github.com/PaloAltoNetworks) or
sites other than our official Downloads page on
https://support.paloaltonetworks.com are provided under the best
effort policy.
"""

    # Check if message already has been accepted
    config_directory = home_directory + "/.prismacloud/"
    community_support_accepted = config_directory + ".community_supported_accepted"
    if os.path.exists(community_support_accepted):
        return True
    else:
        print(community_supported_message)
        answer = input("Type yes to confirm you have read the message above: ")
        if any(answer.lower() == f for f in ["yes", 'y']):
            print("Message accepted.")
            # Create file to check next time
            if not os.path.exists(config_directory):
                os.mkdir(config_directory)
            with open(community_support_accepted, "w") as _accepted:
                _accepted.write("Yes")
        else:
            print("You need to confirm you have read the message above.")
            exit(1)


def get_cli_config():
    '''
    Try to access params["configuration"].
    If it is equal to env or environment, try to read the following environment variables.

        PC_SAAS_API_ENDPOINT
        PC_COMPUTE_API_ENDPOINT
        PC_ACCESS_KEY
        PC_SECRET_KEY

    If all of those are not set, try to read the config file specified by params["configuration"].
    '''

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

    # Try to read environment variables.
    if params["configuration"] in ["env", "environment"]:
        config_env_settings = read_cli_config_from_environment()
        if config_env_settings:
            return config_env_settings

    # Read or write configuration from or to a file.
    config_directory = home_directory + "/.prismacloud/"
    config_file_name = config_directory + params["configuration"] + ".json"

    # Fallback to the API file extension.
    if not os.path.exists(config_file_name):
        config_file_name = config_directory + params["configuration"] + ".conf"

    if os.path.exists(config_file_name):
        config_file_settings = read_cli_config_file(config_file_name)
        # Normalize keys between API and CLI.
        if "api_endpoint" not in config_file_settings and "api" in config_file_settings:
            config_file_settings["api_endpoint"] = config_file_settings.pop("api")
        if "pcc_api_endpoint" not in config_file_settings and "api_compute" in config_file_settings:
            config_file_settings["pcc_api_endpoint"] = config_file_settings.pop("api_compute")
        if "access_key_id" not in config_file_settings and "username" in config_file_settings:
            config_file_settings["access_key_id"] = config_file_settings.pop("username")
        if "secret_key" not in config_file_settings and "password" in config_file_settings:
            config_file_settings["secret_key"] = config_file_settings.pop("password")
        # Note that, with PCCE, api_endpoint is unspecified.
        # But the API needs it to be defined at least as an empty string.
        if not ("api_endpoint" in config_file_settings and config_file_settings["api_endpoint"]):
            config_file_settings["api_endpoint"] = ""
        # Note that, with PCEE, pcc_api_endpoint can be retrieved via CSPM API call, so it is optional.
        # But the API needs it to be defined at least as an empty string.
        if not ("pcc_api_endpoint" in config_file_settings and config_file_settings["pcc_api_endpoint"]):
            config_file_settings["pcc_api_endpoint"] = ""
        # ca_bundle can be True, False, or the path to a file.
        if not ("ca_bundle" in config_file_settings):
            config_file_settings["ca_bundle"] = False
        # Normalize URLs.
        config_file_settings["api_endpoint"] = pc_util.normalize_api(config_file_settings.get("api_endpoint"))
        config_file_settings["pcc_api_endpoint"] = pc_util.normalize_api_compute(config_file_settings.get("pcc_api_endpoint"))
    else:
        if not os.path.exists(config_directory):
            logging.info("Configuration directory does not exist, creating %s", config_directory)
            try:
                os.makedirs(config_directory)
            except Exception as exc:  # pylint:disable=broad-except
                logging.info("Error creating configuration directory: %s", exc)
        config_file_settings = {
            "api_endpoint":
                input("Enter your CSPM API URL (Optional if PCCE), eg: api.prismacloud.io: "),
            "pcc_api_endpoint":
                input("Enter your CWPP API URL (Optional if PCEE), eg: example.twistlock.com/tenant or twistlock.example.com: "),  # noqa: E501
            "access_key_id":
                input("Enter your Access Key (or Username if PCCE): "),
            "secret_key":
                input("Enter your Secret Key (or Password if PCCE): "),
            "ca_bundle":
                False
        }
        # Normalize URLs.
        config_file_settings["api_endpoint"] = pc_util.normalize_api(config_file_settings["api_endpoint"])
        config_file_settings["pcc_api_endpoint"] = pc_util.normalize_api_compute(config_file_settings["pcc_api_endpoint"])
        write_cli_config_file(config_file_name, config_file_settings)
    return config_file_settings


def read_cli_config_from_environment():
    """Read cli configuration from environment"""
    logging.debug("Reading configuration from environment")
    config_env_settings = {}
    try:
        config_env_settings["api_endpoint"] = os.environ.get("PC_SAAS_API_ENDPOINT", "")
        config_env_settings["pcc_api_endpoint"] = os.environ.get("PC_COMPUTE_API_ENDPOINT", "")
        config_env_settings["access_key_id"] = os.environ.get("PC_ACCESS_KEY", "")
        config_env_settings["secret_key"] = os.environ.get("PC_SECRET_KEY", "")
        config_env_settings["ca_bundle"] = False
        # Normalize URLs.
        config_env_settings["api_endpoint"] = pc_util.normalize_api(config_env_settings["api_endpoint"])
        config_env_settings["pcc_api_endpoint"] = pc_util.normalize_api_compute(config_env_settings["pcc_api_endpoint"])
        # Mask all except the first two characters of keys when debugging.
        masked_access_key = config_env_settings["access_key_id"][:3] + "*" * (len(config_env_settings["access_key_id"]) - 4)
        masked_secret_key = config_env_settings["secret_key"][:3] + "*" * (len(config_env_settings["secret_key"]) - 4)
        logging.debug("Environment variable found: PC_SAAS_API_ENDPOINT: %s", config_env_settings["api_endpoint"])
        logging.debug("Environment variable found: PC_COMPUTE_API_ENDPOINT: %s", config_env_settings["pcc_api_endpoint"])
        logging.debug("Environment variable found: PC_ACCESS_KEY: %s", masked_access_key)
        logging.debug("Environment variable found: PC_SECRET_KEY: %s", masked_secret_key)
    except Exception as exc:  # pylint:disable=broad-except
        logging.debug("Error reading from environment: %s", exc)
    logging.debug("Configuration read from environment")
    return config_env_settings


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
            logging.error("There was an error executing the request. Check if this API (cspm) is available in your environment.")  # noqa: E501
            logging.error("Please check your config and try again. Error: %s", exc)  # noqa: E501
            exit(1)
    if api == "cwpp":
        if not endpoint.startswith("api"):
            endpoint = "api/v1/%s" % endpoint
            try:
                result = pc_api.execute_compute(request_type, endpoint, query_params)
            except Exception as exc:  # pylint:disable=broad-except
                logging.error("There was an error executing the request: %s", exc)
                exit(1)
    if api == "code":
        try:
            result = pc_api.execute_code_security(request_type, endpoint, query_params)
        except Exception as exc:  # pylint:disable=broad-except
            logging.error("There was an error executing the request. Check if this API (code) is available in your environment.")  # noqa: E501
            logging.error("Please check your config and try again. Error: %s", exc)  # noqa: E501
            exit(1)
    return result


""" Instance of the Prisma Cloud API """

pc_api.configure(map_cli_config_to_api_config())
# Add the get_endpoint method to this instance.
pc_api.get_endpoint = types.MethodType(get_endpoint, pc_api)
