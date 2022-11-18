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
@click.option("-l", "--limit")
def packages_(limit=50):
    """Show deployed images package information"""
    result = pc_api.images_list_read(query_params={"limit": limit})

    # Build a list of packages, the images they're in and their licenses
    package_list = []

    # Go through images
    for i in result:
        # Go through packages
        for package in i["packages"]:
            # Go through list of packages
            for p_in_image in package["pkgs"]:
                p_in_image["image_id"] = i["id"]
                p_in_image["image_tag"] = i["repoTag"]["registry"] + "/" + i["repoTag"]["repo"] + ":" + i["repoTag"]["tag"]
                package_list.append(p_in_image)

    cli_output(package_list)


cli.add_command(list_)
cli.add_command(packages_)
