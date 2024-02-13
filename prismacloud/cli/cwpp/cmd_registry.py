import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.group("registry", short_help="[CWPP] Scan reports for images in your registry.")
@pass_environment
def cli(ctx):
    pass


@click.command("images", short_help="Retrieves registry image scan reports.")
@click.option("--field", default="")
def images(field=""):
    result = pc_api.registry_list_read("registry")

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


@click.command("list", short_help="Retrieves the list of registries Prisma Cloud is configured to scan. ")
@click.option(
    "--include",
    "-i",
    multiple=True,
    help="Include a registry, a repository, or both for the scan. \
        Format: registry_name/repo_name, registry_name, or repo_name",
    default=[],
)
@click.option(
    "--exclude",
    "-e",
    multiple=True,
    help="Exclude a registry, a repository, or both from the scan. \
        Format: registry_name/repo_name, registry_name, or repo_name",
    default=[],
)
def list(include, exclude):
    registries_to_scan = []
    registries = pc_api.settings_registry_read()
    for registry_item in registries["specifications"]:
        registries_to_scan.append(
            {"registry": registry_item["registry"], "repo": registry_item["repository"], "tag": registry_item["tag"]}
        )
    if exclude:
        # Later in your main function, when processing registries to scan:
        excluded_registries = [normalize_registry_name(e) for e in exclude]  # Prepare the list of normalized exclusions
        registries_to_scan = [r for r in registries_to_scan if not is_excluded(r, excluded_registries)]

    # Filter registries based on inclusion criteria if any are specified
    if include:
        registries_to_scan = [r for r in registries_to_scan if is_included(r, include)]

    cli_output(registries_to_scan)


@click.command("scan", short_help="Trigger the scan of registries.")
@click.option(
    "--include",
    "-i",
    multiple=True,
    help="Include a registry, a repository, or both for the scan. \
        Format: registry_name/repo_name, registry_name, or repo_name",
    default=[],
)
@click.option(
    "--exclude",
    "-e",
    multiple=True,
    help="Exclude a registry, a repository, or both from the scan. \
    Format: registry_name/repo_name, registry_name, or repo_name",
    default=[],
)
def scan(include, exclude):
    registries_to_scan = []
    registries = pc_api.settings_registry_read()
    for registry_item in registries["specifications"]:
        registries_to_scan.append(
            {"registry": registry_item["registry"], "repo": registry_item["repository"], "tag": registry_item["tag"]}
        )
    if exclude:
        # Later in your main function, when processing registries to scan:
        excluded_registries = [normalize_registry_name(e) for e in exclude]  # Prepare the list of normalized exclusions
        registries_to_scan = [r for r in registries_to_scan if not is_excluded(r, excluded_registries)]

    # Filter registries based on inclusion criteria if any are specified
    if include:
        registries_to_scan = [r for r in registries_to_scan if is_included(r, include)]

    # Transform each registry to the new format
    payload = [{"tag": {"registry": r["registry"], "repo": r["repo"], "tag": r["tag"]}} for r in registries_to_scan]

    pc_api.registry_scan_select(body_params=payload)
    cli_output(registries_to_scan)


def normalize_registry_name(registry_name):
    """Strip 'https://' prefix and trailing slash from registry names for consistent comparison."""
    normalized_name = registry_name
    if normalized_name.startswith("https://"):
        normalized_name = normalized_name[len("https://"):]
    if normalized_name.endswith("/"):
        normalized_name = normalized_name[:-1]
    return normalized_name.lower()  # Consider lowercasing to make comparison case-insensitive


def is_excluded(registry, exclusions):
    """Check if a given registry should be excluded based on the exclusions list."""
    for exclusion in exclusions:
        exclusion_normalized = normalize_registry_name(exclusion)
        registry_normalized = normalize_registry_name(registry["registry"])
        repo_normalized = registry["repo"].lower()
        # Check if the exclusion matches the registry or repository name
        if exclusion_normalized in registry_normalized or exclusion_normalized in repo_normalized:
            return True
    return False


def is_included(registry, inclusions):
    """Check if a given registry should be included based on the inclusions list."""
    # If no inclusions are specified, assume everything is included by default
    if not inclusions:
        return True

    for inclusion in inclusions:
        inclusion_normalized = normalize_registry_name(inclusion)
        registry_normalized = normalize_registry_name(registry["registry"])
        repo_normalized = registry["repo"].lower()

        # Split inclusion criteria in case it specifies both registry and repo
        if "/" in inclusion_normalized:
            inclusion_parts = inclusion_normalized.split("/", 1)
            inclusion_registry = inclusion_parts[0]
            inclusion_repo = inclusion_parts[1]

            # Check if both registry and repo match the inclusion criteria
            if inclusion_registry in registry_normalized and inclusion_repo in repo_normalized:
                return True
        else:
            # If the inclusion criteria is only one part, check both registry and repo for a match
            if inclusion_normalized in registry_normalized or inclusion_normalized in repo_normalized:
                return True

    # If none of the inclusions match, return False
    return False


cli.add_command(images)
cli.add_command(list)
cli.add_command(scan)
