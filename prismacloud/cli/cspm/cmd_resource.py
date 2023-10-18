import click
import json
import yaml

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.group("resource", short_help="[CSPM] Returns detailed information for the resource with the given rrn.")
@pass_environment
def cli(ctx):
    pass


@click.option(
    "-a",
    "--account",
    help="Cloud Account",
    multiple=True,
)
@click.option(
    "-r",
    "--region",
    help="Cloud Region",
    multiple=True,
)
@click.option(
    "-s",
    "--service",
    help="Cloud Service",
    multiple=True,
)
@click.option(
    "-rt",
    "--resource_type",
    help="Resource Type",
    multiple=True,
)
@click.option(
    "-t",
    "--type",
    help="Cloud Type",
    multiple=True,
)
@click.option(
    "-st",
    "--status",
    help="Scan Status",
    multiple=True,
)
@click.option(
    "-tg",
    "--tag",
    help="Resource Tag (in the format 'key:value')",
    multiple=True,
)
@click.option(
    "-f",
    "--tf_file",
    help="Path to the Terraform output file",
    default="import.tf",
)
@click.command("list", short_help="[CSPM] Returns detailed information for the resource with the given rrn.")
def list_resource(region, service, type, status, account, resource_type, tag, tf_file):

    base_filters = [
        {"name": "includeEventForeignEntities", "operator": "=", "value": "false"},
        {"name": "decorateWithDerivedRRN", "operator": "=", "value": False},
    ]

    region_filters = [{"name": "cloud.region", "operator": "=", "value": r} for r in region]
    service_filters = [{"name": "cloud.service", "operator": "=", "value": s} for s in service]
    type_filters = [{"name": "cloud.type", "operator": "=", "value": t} for t in type]
    status_filters = [{"name": "scan.status", "operator": "=", "value": st} for st in status]
    account_filters = [{"name": "cloud.account", "operator": "=", "value": a} for a in account]
    resource_type_filters = [{"name": "resource.type", "operator": "=", "value": rt} for rt in resource_type]
    tag_filters = []
    for tg in tag:
        key, value = tg.split(":")
        tag_filters.append({"name": "resource.tagv2", "operator": "=", "value": json.dumps({"key": key, "value": value})})

    payload = {
        "filters": base_filters
        + region_filters
        + service_filters
        + type_filters
        + status_filters
        + account_filters
        + resource_type_filters
        + tag_filters,  # noqa: E501
        "limit": 100,
        "timeRange": {"type": "to_now", "value": "epoch"},
    }
    result = pc_api.resource_scan_info_read(body_params=payload)

    if tf_file:
        generate_tf_file(result, tf_file, "mapping.yaml")

    cli_output(result)


def get_terraform_mapping(yaml_file_path, prismacloud_type):
    with open(yaml_file_path, "r") as yaml_file:
        mappings = yaml.safe_load(yaml_file)

    for mapping in mappings:
        if mapping["prismacloud"] == prismacloud_type:
            return mapping["terraform"]
    return None


def generate_tf_file(json_data, tf_file_path, yaml_file_path):
    written_ids = set()  # A set to store the IDs that have been written to the file

    with open(tf_file_path, "w") as tf_file:
        for entry in json_data:
            entry_id = entry.get("id")

            # If the ID has already been written to the file, skip this entry
            if entry_id in written_ids:
                continue

            terraform_type = get_terraform_mapping(yaml_file_path, entry.get("assetType"))

            if terraform_type is not None:
                name_slug = entry.get("name").lower().replace(" ", "_").replace("-", "_")
                tf_file.write(
                    f"""
import {{
  to = {terraform_type}.{name_slug}
  id = "{entry_id}"
}}
                """
                )
                # Add the ID to the set of written IDs
                written_ids.add(entry_id)


cli.add_command(list_resource)
