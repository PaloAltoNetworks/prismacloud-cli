import logging

import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.group("stats", short_help="[CWPP] Retrieve statistics for the resources protected by Prisma Cloud")
@pass_environment
def cli(ctx):
    pass


@click.command()
def daily():
    result = pc_api.stats_daily_read()
    cli_output(result)


@click.command()
def dashboard():
    result = pc_api.stats_trends_read()
    cli_output(result)


@click.command()
def events():
    result = pc_api.stats_events_read("")
    cli_output(result)


@click.command(name="license")
def license_stats():
    result = pc_api.stats_license_read()
    cli_output(result)


@click.command()
@click.option("-cve", "--cve")
@click.option("-collection", "--collection")
@click.option(
    "--severity",
    "-s",
    type=click.Choice(
        [
            "low",
            "medium",
            "high",
            "critical",
        ]
    ),
    help="Retrieves a list of vulnerabilities (CVEs) that matches the specified value of the severity threshold or higher.",
)
@click.option(
    "--cvss",
    help="CVSS Threshold is the minimum CVSS score.",
)
@click.option(
    "--resource-type",
    "-rt",
    type=click.Choice(
        [
            "images",
            "hosts",
            "registryImages",
            "containers",
            "functions",
            "all",
        ]
    ),
    multiple=True,
    default=["images"],
    help="Specify the resource types to search for vulnerabilities. Use 'all' to include all types.",
)
@click.option("-l", "--limit", default=10, help="Number of top vulnerabilities to search. Max is 100.")
def vulnerabilities(cve, collection, severity, cvss, resource_type, limit):
    if "all" in resource_type:
        resource_type = ["images", "hosts", "registryImages", "containers", "functions"]

    logging.debug(f"Searching for {resource_type} resoursce type")

    if not cve and not (cvss or severity):
        result = pc_api.stats_vulnerabilities_read({"limit": limit, "offset": 0, "collections": collection})
        result = result[0]
        return cli_output(result)

    elif not cve and (cvss and severity):
        logging.debug("CVSS to search for: {cvss} with Severity: {severity}")
        results = pc_api.stats_vulnerabilities_read(
            {"limit": limit, "offset": 0, "severityThreshold": severity, "cvssThreshold": cvss}
        )
        return cli_output(process_vulnerability_results(results, resource_type))

    elif not cve and cvss:
        logging.debug("CVSS to search for: {cvss}")
        results = pc_api.stats_vulnerabilities_read({"limit": limit, "offset": 0, "cvssThreshold": cvss})

        return cli_output(process_vulnerability_results(results, resource_type))

    elif not cve and severity:
        logging.debug("Severity to search for: {severity}")
        results = pc_api.stats_vulnerabilities_read({"limit": limit, "offset": 0, "severityThreshold": severity})
        return cli_output(process_vulnerability_results(results, resource_type))

    elif cve:
        logging.debug("CVE to search for: {cve}")
        results = pc_api.stats_vulnerabilities_read({"limit": limit, "offset": 0, "cve": cve})
        return cli_output(process_vulnerability_results(results, resource_type))


def process_vulnerability_results(results, resource_type):
    image_data = []
    tags = pc_api.tags_list_read()
    for result in results:
        for key in resource_type:
            if key in result and "vulnerabilities" in result[key]:
                vulnerabilities = result[key]["vulnerabilities"]
                with click.progressbar(vulnerabilities) as vulnerabilities_bar:
                    for vulnerability in vulnerabilities_bar:
                        logging.debug(f"Found CVE {vulnerability['cve']} from {vulnerability['impactedResourceType']}")
                        image_data = search_impacted_resource_per_cve(vulnerability, tags, image_data)
    return image_data


def search_impacted_resource_per_cve(vulnerability, tags, image_data):
    resources = pc_api.stats_vulnerabilities_impacted_resoures_read(
        {"cve": vulnerability["cve"], "resourceType": vulnerability["impactedResourceType"]}
    )

    # Function to create image_info with optional tag name
    def add_prisma_cloud_tags(base_info, tags):
        for tag in tags:
            if "vulns" in tag and tag["vulns"]:
                for tag_vuln in tag["vulns"]:
                    if vulnerability["cve"] == tag_vuln.get("id") and "resourceType" not in tag_vuln:
                        logging.debug(
                            f"=================> CVE {vulnerability['cve']} has a tag named {tag['name']} for all resourceType"
                        )
                        base_info["prima_cloud_tag"] = tag["name"]
                        base_info["prima_cloud_tag_comment"] = tag_vuln.get("comment")
                    elif vulnerability["cve"] == tag_vuln.get("id") and vulnerability["impactedResourceType"] == tag_vuln.get(
                        "resourceType"
                    ):
                        logging.debug(f"=================> CVE {vulnerability['cve']} has a tag named {tag['name']}")
                        base_info["prima_cloud_tag"] = tag["name"]
                        base_info["prima_cloud_tag_comment"] = tag_vuln.get("comment")

        return base_info

    if "registryImages" in resources:
        for image in resources["registryImages"]:
            image_info = add_prisma_cloud_tags(
                {
                    "type": "registry_image",
                    "cve": vulnerability["cve"],
                    "resourceID": image["resourceID"],
                    "packages": image["packages"],
                    "risk_score": vulnerability["riskScore"],
                    "impacted_packages": vulnerability["impactedPkgs"],
                    "cve_description": vulnerability["description"],
                },
                tags,
            )
            logging.debug(f"Image info: {image_info}")
            image_data.append(image_info)

    if "images" in resources:
        for image in resources["images"]:
            for container in image["containers"]:
                image_info = add_prisma_cloud_tags(
                    {
                        "type": "deployed_image",
                        "cve": vulnerability["cve"],
                        "resourceID": image["resourceID"],
                        "image": container.get("image", "na"),
                        "imageID": container.get("imageID", "na"),
                        "container": container.get("container", "na"),
                        "host": container.get("host", "na"),
                        "namespace": container.get("namespace", "na"),
                        "factors": container["factors"],
                        "packages": image["packages"],
                        "risk_score": vulnerability["riskScore"],
                        "impacted_packages": vulnerability["impactedPkgs"],
                        "cve_description": vulnerability["description"],
                    },
                    tags,
                )
                logging.debug(f"Image info: {image_info} -- Container: {container}")
                image_data.append(image_info)

    if "hosts" in resources:
        for host in resources["hosts"]:
            host_info = add_prisma_cloud_tags(
                {
                    "type": "host",
                    "cve": vulnerability["cve"],
                    "resourceID": host["resourceID"],
                    "packages": host["packages"],
                    "risk_score": vulnerability["riskScore"],
                    "impacted_packages": vulnerability["impactedPkgs"],
                    "cve_description": vulnerability["description"],
                },
                tags,
            )
            image_data.append(host_info)

    if "functions" in resources:
        for function in resources["functions"]:
            function_info = add_prisma_cloud_tags(
                {
                    "type": "function",
                    "cve": vulnerability["cve"],
                    "resourceID": function["resourceID"],
                    "function_details": function["functionDetails"],
                    "packages": function["packages"],
                    "risk_score": vulnerability["riskScore"],
                    "impacted_packages": vulnerability["impactedPkgs"],
                    "cve_description": vulnerability["description"],
                },
                tags,
            )
            image_data.append(function_info)

    return image_data


cli.add_command(daily)
cli.add_command(dashboard)
cli.add_command(events)
cli.add_command(license_stats)
cli.add_command(vulnerabilities)
