import os
from importlib import util

from setuptools import find_namespace_packages, setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


spec = util.spec_from_file_location("prismacloud.cli.version", os.path.join("prismacloud", "cli", "version.py"))

# noinspection PyUnresolvedReferences
mod = util.module_from_spec(spec)
spec.loader.exec_module(mod)  # type: ignore
version = mod.version  # type: ignore

setup(
    extras_require={},
    install_requires=[
        "api-client",
        "click",
        "click_completion",
        "click_help_colors",
        "coloredlogs",
        "ipython",
        "jsondiff",
        "pandas",
        "requests",
        "tabulate",
        "prismacloud-api",
    ],
    name="prismacloud-cli",
    version=version,
    python_requires=">=3.7",
    author="Steven de Boer, Simon Melotte, Tom Kishel",
    author_email="stdeboer@paloaltonetworks.com, smelotte@paloaltonetworks.com, tkishel@paloaltonetworks.com",
    description=("Prisma Cloud CLI"),
    license="BSD",
    keywords="prisma cloud cli",
    url="https://github.com/PaloAltoNetworks/prismacloud-cli",
    packages=find_namespace_packages(),
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Topic :: Utilities",
    ],
    entry_points="""
        [console_scripts]
        pc=prismacloud.cli:cli
    """,
)
