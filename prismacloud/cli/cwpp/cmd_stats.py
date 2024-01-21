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
def vulnerabilities(cve, collection, severity, cvss):
    if not cve and not (cvss or severity):
        result = pc_api.stats_vulnerabilities_read({"collections": collection})
        result = result[0]
        return cli_output(result)

    elif not cve and (cvss and severity):
        logging.debug("CVSS to search for: {cvss}")
        results = pc_api.stats_vulnerabilities_read({"severityThreshold": severity, "cvssThreshold": cvss})
        return cli_output(process_vulnerability_results(results))

    elif not cve and cvss:
        logging.debug("CVSS to search for: {cvss}")
        results = pc_api.stats_vulnerabilities_read({"cvssThreshold": cvss})
        return cli_output(process_vulnerability_results(results))

    elif not cve and severity:
        logging.debug("CVSS to search for: {cvss}")
        results = pc_api.stats_vulnerabilities_read({"severityThreshold": severity})
        return cli_output(process_vulnerability_results(results))

    elif cve:
        logging.debug("CVE to search for: {cve}")
        results = pc_api.stats_vulnerabilities_read({"cve": cve})
        return cli_output(process_vulnerability_results(results))


def process_vulnerability_results(results):
    image_data = []
    for result in results:
        for key in ["images", "hosts", "registryImages", "containers", "functions"]:
            if key in result and "vulnerabilities" in result[key]:
                for vulnerability in result[key]["vulnerabilities"]:
                    logging.info(f"Found this CVE: {vulnerability['cve']} in {key}")
                    image_data = search_impacted_resource_per_cve(vulnerability, image_data)
    return image_data


def search_impacted_resource_per_cve(vulnerability, image_data):
    resources = pc_api.stats_vulnerabilities_impacted_resoures_read(
        {"cve": vulnerability["cve"], "resourceType": vulnerability["impactedResourceType"]}
    )

    # Check and loop through images if they exist
    if "registryImages" in resources:
        logging.debug("Some interesting container images here")
        for image in resources["registryImages"]:

            image_info = {
                "type": "registry_image",
                "cve": vulnerability["cve"],
                "resourceID": image["resourceID"],
                "packages": image["packages"],
                "risk_score": vulnerability["riskScore"],
                "impacted_packages": vulnerability["impactedPkgs"],
                "cve_description": vulnerability["description"],
            }
            logging.debug(f"Image info: {image_info}")
            image_data.append(image_info)

    # Check and loop through registryImages if they exist
    if "images" in resources:
        logging.debug("Some interesting images here")
        for image in resources["images"]:
            # Iterate through each container in the image
            for container in image["containers"]:

                image_info = {
                    "type": "deployed_image",
                    "cve": vulnerability["cve"],
                    "resourceID": image["resourceID"],
                    "image": container["image"],
                    "imageID": container["imageID"],
                    "container": container.get("container", "na"),
                    "host": container.get("host", "na"),
                    "namespace": container.get("namespace", "na"),
                    "factors": container["factors"],
                    "packages": image["packages"],
                    "risk_score": vulnerability["riskScore"],
                    "impacted_packages": vulnerability["impactedPkgs"],
                    "cve_description": vulnerability["description"],
                }
                logging.debug(f"Image info: {image_info}")
                image_data.append(image_info)

    # Assuming resource is the API response dictionary
    if "hosts" in resources:
        logging.info("Some interesting hosts here")
        for host in resources["hosts"]:

            host_info = {
                "type": "host",
                "cve": vulnerability["cve"],
                "resourceID": host["resourceID"],
                "packages": host["packages"],
                "risk_score": vulnerability["riskScore"],
                "impacted_packages": vulnerability["impactedPkgs"],
                "cve_description": vulnerability["description"],
            }
            image_data.append(host_info)

    # Assuming resource is the API response dictionary
    if "functions" in resources:
        logging.info("Some interesting functions here")
        for function in resources["functions"]:

            function_info = {
                "type": "function",
                "cve": vulnerability["cve"],
                "resourceID": function["resourceID"],
                "function_details": function["functionDetails"],
                "packages": function["packages"],
                "risk_score": vulnerability["riskScore"],
                "impacted_packages": vulnerability["impactedPkgs"],
                "cve_description": vulnerability["description"],
            }
            image_data.append(function_info)

    return image_data


cli.add_command(daily)
cli.add_command(dashboard)
cli.add_command(events)
cli.add_command(license_stats)
cli.add_command(vulnerabilities)
