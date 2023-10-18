import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


@click.group("images", short_help="Deployed images scan reports")
@pass_environment
def cli(ctx):
    pass


@click.command(name="list")
@click.option("-l", "--limit")
def list_(limit=50):
    """Deployed images scan reports"""
    result = pc_api.images_list_read(query_params={"limit": limit})
    cli_output(result)


@click.command(name="packages")
@click.option("-p", "--package", default=None, help="Specify a package to filter on.")
@click.option("-i", "--image-name", default=None, help="Specify an image name to filter on.")
@click.option("-c", "--cluster", default=None, help="Specify a cluster to filter on.")
@click.option("-l", "--limit", default=50, help="Limit the number of images to process. Default limit is 50")
def packages_(package, image_name, cluster, limit):
    """Show deployed images package information."""
    query_params = {"limit": limit}
    if image_name:
        query_params["image_name"] = image_name
    if cluster:
        query_params["cluster"] = cluster

    images = pc_api.images_list_read(query_params=query_params)

    package_list = []

    # Go through images
    for image in images:
        # Go through packages
        for pkg_group in image["packages"]:
            # Go through list of packages
            for pkg in pkg_group["pkgs"]:
                # Check if a specific package is specified and filter on that
                if package is None or package.lower() in pkg["name"].lower():

                    image_tag = "Unknown"
                    if image["repoTag"] is not None:  # Check if repoTag is not None
                        image_tag = (
                            image["repoTag"]["registry"] + "/" + image["repoTag"]["repo"] + ":" + image["repoTag"]["tag"]
                        )

                    pkg_info = {
                        "image_name": image["instances"][0]["image"] if image["instances"] else "Unknown",
                        "image_id": image["id"],
                        "image_tag": image_tag,
                        "namespace": image.get("namespaces", "Unknown"),
                        "os_distro": image.get("installedProducts", {}).get("osDistro", "Unknown"),
                        "package_name": pkg["name"],
                        "package_version": pkg["version"],
                        "package_license": pkg["license"],
                        "package_cve_count": pkg["cveCount"],
                    }
                    package_list.append(pkg_info)

    cli_output(package_list)


cli.add_command(list_)
cli.add_command(packages_)
