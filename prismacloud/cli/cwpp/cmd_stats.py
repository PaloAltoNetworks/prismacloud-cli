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
    "--cvss",
    default="9.0",
    help="CVSSThreshold is the minimum CVSS score indicating that all retrieved CVEs CVSS scores are greater than or equal to the threshold. Default: 9.0",
)
def vulnerabilities(cve, collection, cvss):
    if not cve and not cvss:
        result = pc_api.stats_vulnerabilities_read({"collections": collection})
        result = result[0]
        cli_output(result)
        return
    elif not cve:                
        logging.debug("CVSS to search for: {cvss}")
        results = pc_api.stats_vulnerabilities_read({"cvssThreshold": cvss})
        image_data = []
        for result in results:
            # Check if 'images', 'hosts', 'containers', 'functions' keys exist
            for key in ['images', 'hosts', 'containers', 'functions']:
                if key in result:
                    # Check if 'vulnerabilities' key exists in the specific category                    
                    if 'vulnerabilities' in result[key]:
                        for vulnerability in result[key]['vulnerabilities']:
                            logging.info(f"Found this CVE: {vulnerability['cve']} in {key}")      
                            resources = pc_api.stats_vulnerabilities_impacted_resoures_read({"cve": vulnerability['cve'], "resourceType": vulnerability["impactedResourceType"]})

                            # Check and loop through images if they exist
                            if 'images' in resources:
                                logging.debug("Some interesting images here")
                                for image in resources['images']:
                                    packages_info = []

                                    # Check if 'packages' key exists and is a list
                                    if 'packages' in image and isinstance(image['packages'], list):
                                        for package in image['packages']:
                                            package_info = {
                                                'package': package.get('package', 'Unknown'),
                                                'severity': package.get('severity', 'Unknown'),
                                                'cvss': package.get('cvss', 'Unknown')
                                            }
                                            packages_info.append(package_info)

                                    # Iterate through each container in the image
                                    for container in image['containers']:
                                        image_info = {
                                            'type': "image",
                                            'cve': vulnerability['cve'],
                                            'resourceID': image['resourceID'],                                                
                                            'image': container['image'],
                                            'imageID': container['imageID'],
                                            'container': container['container'],
                                            'host': container['host'],
                                            'namespace': container['namespace'],
                                            'factors': container['factors'],
                                            'packages': image['packages'],
                                            'risk_score': vulnerability['riskScore'],
                                            'impacted_packages': vulnerability['impactedPkgs'],
                                            'cve_description': vulnerability['description']
                                        }
                                        logging.debug(f"Image info: {image_info}")
                                        image_data.append(image_info)


                            # Assuming resources is the API response dictionary
                            if 'hosts' in resources:
                                logging.info("Some interesting hosts here")
                                for host in resources['hosts']:
                                    packages_info = []

                                    # Check if 'packages' key exists and is a list
                                    if 'packages' in host and isinstance(host['packages'], list):
                                        for package in image['packages']:
                                            package_info = {
                                                'package': package.get('package', 'Unknown'),
                                                'severity': package.get('severity', 'Unknown'),
                                                'cvss': package.get('cvss', 'Unknown')
                                            }
                                            packages_info.append(package_info)

                                    # Process each host
                                    # Example: Extracting host information
                                    host_info = {
                                        'type': "host",
                                        'cve': vulnerability['cve'],
                                        'resourceID': host['resourceID'],
                                        'packages': image['packages'],
                                        'risk_score': vulnerability['riskScore'],
                                        'impacted_packages': vulnerability['impactedPkgs'],
                                        'cve_description': vulnerability['description']
                                    }
                                    logging.info(f"Host info: {host_info}")
                                    image_data.append(host_info)

        return cli_output(image_data)
        # return cli_output(result)
    
    cves = cve.split(",")
    logging.debug("CVEs to search for: {cves}")

    # Get impacted resources for each cve in cves
    result_tree = {}
    for cve_to_check in cves:
        result = pc_api.stats_vulnerabilities_impacted_resoures_read({"cve": cve_to_check})
        result_tree[cve_to_check] = result

    cli_output(result_tree)


cli.add_command(daily)
cli.add_command(dashboard)
cli.add_command(events)
cli.add_command(license_stats)
cli.add_command(vulnerabilities)
