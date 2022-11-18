import logging

import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.group("host_auto_deploy", short_help="[CSPM] Create host deploy rules")
@pass_environment
def cli(ctx):
    pass


@click.command("list", short_help="[CSPM] List host auto deploy policies.")
def host_auto_deploy_read():
    result = pc_api.settings_host_auto_deploy_read()
    cli_output(result)


@click.command("update", short_help="Update host auto defend rules based on the cloud accounts onboarded")
@click.option(
    "--provider",
    default="aws",
    type=click.Choice(["aws", "azure", "gcp"]),
    help="Cloud Service Provider",
)
@click.option(
    "--aws_region_type",
    default="regular",
    type=click.Choice(["regular", "government", "china"]),
    help="Scanning scope",
)
@click.option(
    "--bucket_region",
    default="US-EAST1",
    help="[GCP ONLY] - Bucket Region",
)
@click.option(
    "--console_hostname",
    default="",
    help="Console Hostname",
)
@click.option(
    "--collection_name",
    default="All",
    help="Collection to use for the scope of the rule",
)
def host_auto_deploy_update(provider, aws_region_type, bucket_region, console_hostname, collection_name):
    """Update repository"""
    logging.info("API - Updating host auto-defend rule")

    cloud_accounts = []

    credentials = pc_api.get_endpoint("credentials?cloud=true")
    for credential in credentials:
        if credential["type"] == provider and credential["useAWSRole"] is False:
            logging.info("API - Found Credential: %s", credential["_id"])
            cloud_accounts.append(credential["_id"])

    body_params = []
    if cloud_accounts:
        logging.info("API - All cloud accounts: %s", cloud_accounts)

        cloud_collection = ""
        collections = pc_api.get_endpoint("collections")
        for collection in collections:
            if collection["name"] == collection_name:
                del collection["system"]
                del collection["prisma"]
                del collection["modified"]
                cloud_collection = collection
                logging.info("API - Found collection: %s", cloud_collection)

        for cloud_account in cloud_accounts:
            autodefend = {}
            autodefend["provider"] = provider
            autodefend["name"] = cloud_account
            autodefend["credentialID"] = cloud_account
            autodefend["awsRegionType"] = aws_region_type
            autodefend["bucketRegion"] = bucket_region
            autodefend["consoleHostname"] = console_hostname
            autodefend["collections"] = [cloud_collection]
            body_params.append(autodefend)
    else:
        logging.error("API - ERROR No cloud account were found. ")

    if body_params:
        logging.info("API - List of rules to be updated %s", body_params)
        result = pc_api.settings_host_auto_deploy_write(body=body_params)
        logging.info("API - Host auto-defend rule have been updated: %s", result)
    else:
        logging.error("API - Something went wrong with building the object for the policies")


@click.command("create", short_help="Create only one rule and erase all the other host auto-defend rules")
@click.option(
    "--provider",
    default="aws",
    type=click.Choice(["aws", "azure", "gcp"]),
    help="Cloud Service Provider",
)
@click.option(
    "--name",
    help="Rule name",
)
@click.option(
    "--credential_id",
    help="Cloud credentials",
)
@click.option(
    "--aws_region_type",
    default="regular",
    type=click.Choice(["regular", "government", "china"]),
    help="Scanning scope",
)
@click.option(
    "--bucket_region",
    default="US-EAST1",
    help="[GCP ONLY] - Bucket Region",
)
@click.option(
    "--console_hostname",
    default="europe-west3.cloud.twistlock.com",
    help="Console Hostname",
)
@click.option(
    "--collection_name",
    default="All",
    help="Collection to use for the scope of the rule",
)
def host_auto_deploy_create(provider, name, credential_id, aws_region_type, bucket_region, console_hostname, collection_name):
    """Update repository"""
    logging.info("API - Updating host auto-defend rule")

    body_params = []
    cloud_collection = ""
    collections = pc_api.get_endpoint("collections")
    for collection in collections:
        if collection["name"] == collection_name:
            del collection["system"]
            del collection["prisma"]
            del collection["modified"]
            cloud_collection = collection
            logging.info("API - Found collection: %s", cloud_collection)

    autodefend = {}
    autodefend["provider"] = provider
    autodefend["name"] = name
    autodefend["credentialID"] = credential_id
    autodefend["awsRegionType"] = aws_region_type
    autodefend["bucketRegion"] = bucket_region
    autodefend["consoleHostname"] = console_hostname
    autodefend["collections"] = [cloud_collection]
    body_params.append(autodefend)

    if body_params:
        logging.info("API - List of rules to be updated %s", body_params)
        result = pc_api.settings_host_auto_deploy_write(body=body_params)
        logging.info("API - Host auto-defend rule have been updated: %s", result)
    else:
        logging.error("API - Something went wrong with building the object for the policies")


cli.add_command(host_auto_deploy_update)
cli.add_command(host_auto_deploy_create)
