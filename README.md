# Prisma Cloud CLI

[![Code Quality Check](https://github.com/PaloAltoNetworks/prismacloud-cli/actions/workflows/build.yml/badge.svg)](https://github.com/PaloAltoNetworks/prismacloud-cli/actions/workflows/build.yml)

The Prisma Cloud CLI is a command line interface for [Prisma Cloud](https://www.paloaltonetworks.com/prisma/cloud) by [Palo Alto Networks](https://www.paloaltonetworks.com/).

# Community Supported
This template/solution is released under an as-is, best effort, support policy. These scripts should be seen as community supported and Palo Alto Networks will contribute our expertise as and when possible. We do not provide technical support or help in using or troubleshooting the components of the project through our normal support options such as Palo Alto Networks support teams, or ASC (Authorized Support Centers) partners and backline support options. The underlying product used (Prisma Cloud) by the scripts or templates are still supported, but the support is only for the product functionality and not for help in deploying or using the template or script itself.

Unless explicitly tagged, all projects or work posted in our GitHub repository (at https://github.com/PaloAltoNetworks) or sites other than our official Downloads page on https://support.paloaltonetworks.com are provided under the best effort policy.

# Release Notes

## v0.6.10

 * Added output count which just returns the number of results found.
 * Added option to rql command --file, to define a yaml file with rql queries to run

### Use Case

The new --field parameter of the rql command can be used to parse a file with 
RQL queries. This file needs to be in yaml format as the example below:

```
- name: Find all permissions granted to Users
  query: config from iam where grantedby.cloud.entity.type = 'user'

- name: Find all permissions granted to Roles
  query: config from iam where grantedby.cloud.entity.type = 'role'

- name: IAM identities that can delete DynamoDB tables
  query: config from iam where action.name = 'dynamodb:DeleteTable'
```

Examples to use this:

`pc -o count rql --file ~/.prismacloud/my-important-queries.yaml`
`pc rql --file ~/.prismacloud/my-important-queries.yaml`

### Sample output

Command

`pc -o markdown rql --file ~/.prismacloud/my-important-queries.yaml `

RQL Query name: Find all permissions granted to Roles
RQL Query: config from iam where grantedby.cloud.entity.type = 'role'
| id                             | sourcePublic   | sourceCloudType   | sourceCloudAccount   | sourceCloudRegion   |
|:-------------------------------|:---------------|:------------------|:---------------------|:--------------------|
| 7984fc7e5041b7439272897da5c948 | False          | AWS               | Pedro AWS Account    | AWS Oregon          |
| 538adb5f6ccea83434be64b9e3b882 |                |                   |                      |                     |
| 2c47                           |                |                   |                      |                     |
| 3206a93cd56dc0d983f67a994a648a | False          | AWS               | Pedro AWS Account    | AWS Oregon          |
| 9a7e2f47f8a1d8851f37433312c1bc |                |                   |                      |                     |
| a3d5                           |                |                   |                      |                     |

RQL Query name: Find all permissions granted to Groups
RQL Query: config from iam where grantedby.cloud.entity.type = 'group'
| id                             | sourcePublic   | sourceCloudType   | sourceCloudAccount   | sourceCloudRegion   |
|:-------------------------------|:---------------|:------------------|:---------------------|:--------------------|
| 177bef83192f13a4e11f439fa8f7bb | False          | AWS               | pete-aws             | AWS Global          |
| dc50ce83185092er44re4431d3cad0 |                |                   |                      |                     |
| 19ce                           |                |                   |                      |                     |
| 177bef83192f13aer11f4erfa8f7bb | False          | AWS               | pete-aws             | AWS Global          |
| dc50ce831850928ddfeb9461d3cad0 |                |                   |                      |                     |
| 19ce                           |                |                   |                      |                     |

RQL Query name: Show all INACTIVE identities and their allowed actions over the last specified number of days
RQL Query: config from iam where action.lastaccess.days > 90


## v0.6.0
Output options have been added: markdown and clipboard. Clipboard can be used to output data directly into your clipboard and paste e.g. into MS Excel or Google Docs.

# Getting started

### Requirements
 * Python >= 3.8
 * Pip3

### Installation

```sh
pip3 install prismacloud-cli
```

Installation on Alpine:
```sh
sudo pip3 install --upgrade pip && pip3 install --upgrade setuptools
sudo pip3 install prismacloud-cli
```

Installation on Ubuntu:
```sh
sudo apt update
sudo apt install -y python3-venv python3-pip jq
mkdir python_virtual_environments/
cd python_virtual_enviornments/
python3 -m venv prisma_cli_env
source prisma_cli_env/bin/activate
pip3 install prismacloud-cli
```

### Run the script

Run the pc cli script. If you don't have a config file yet, it will help you to create one.

```
pc version
```

This process looks like the screenshot below. the prismacloud-cli asks you for some details, stores it in the credentials file and uses that file when it is already available.

![First run](https://raw.githubusercontent.com/PaloAltoNetworks/prismacloud-cli/main/screenshot.png)

### Create your own configuration

Create an access key from Settings then Access key
Get the path to console from Compute tab, System, Utilities

Create a file into home directory .prismacloud/credentials.json with the following structure.

```json
{
  "url":      "__REDACTED__",
  "identity": "__REDACTED__",
  "secret":   "__REDACTED__"
}
```

You can add additional configurations which you can call by using --config. For example, create a file
called ~/.prismacloud/demo.json with the contents above.

Add ```--config demo``` to your cli commands.

For example:

```
pc --config demo -o csv policy
```

### Use environment variables for configuration

By setting the environment variables:

```
PC_URL
PC_IDENTITY
PC_SECRET
```

And then run pc referring to a configuration called environment:

`pc --config environment <command>`

## Examples
```
pc -o csv policy
pc -o json policy | jq
pc tags
pc stats dashboard
pc -o json stats dashboard
pc cloud name
pc --columns defendersSummary.host stats dashboard
```

## Global options
The following global options are available

```
Options:
  -v, --verbose                   Enables verbose mode.
  -vv, --very_verbose             Enables very verbose mode.
  -o, --output [text|csv|json|html|clipboard|markdown|columns]
  -c, --config TEXT               Select configuration
                                  ~/.prismacloud/[CONFIGURATION].json
  --columns TEXT                  Select columns for output
  --help                          Show this message and exit.
```

Use -o columns to get a list of columns available for --columns, e.g.:

```
pc -o columns images
pc --columns hostname,repoTag.repo,osDistro -o csv images -l 1
```

## Environment variables

To overwrite the default output settings, use environment variables MAX_WIDTH (console output), MAX_ROWS, MAX_COLUMNS and MAX_LINES. 

- MAX_LINES is used to defined the maximum number of lines within a cell when wrapping the contents.

## Commands
The cli has several commands to work with, see the screenshot below for an example, but use ```pc --help``` to see the latest list for your version.

![Help](https://raw.githubusercontent.com/PaloAltoNetworks/prismacloud-cli/main/help.png)

## Use cases

### Log4J Impacted Resources
```
pc -o json stats vulnerabilities --cve CVE-2021-44228 | jq
pc stats vulnerabilities --cve CVE-2021-44228
```

Use something similar for getting the *Spring Shell* impacted resources.

### Search scan reports for images scanned by the Jenkins plugin or twistcli.
```
pc scans --help
```

Select only specific columns for the output:

```
pc --columns entityInfo.repoTag.registry,entityInfo.repoTag.repo,entityInfo.repoTag.tag,entityInfo.vulnerabilitiesCount scans -l 20 -s nginx
```

You might also want to add some additional columns and save the output as html:

```
pc --config local -o html --columns entityInfo.repoTag.registry,entityInfo.repoTag.repo,entityInfo.repoTag.tag,entityInfo.vulnerabilitiesCount,entityInfo.vulnerabilityDistribution.critical,entityInfo.vulnerabilityDistribution.high,entityInfo.vulnerabilityDistribution.medium scans -l 20 -s nginx  > /tmp/results.html
```

Then, open /tmp/results.html:

![Results](https://raw.githubusercontent.com/PaloAltoNetworks/prismacloud-cli/main/results.png)


### Enable CSPM policies with Prisma Cloud CLI

```
pc policy set --help
pc -vv policy set --status enable --compliance_standard 'CIS v1.4.0 (AWS)'
```

### Disable CSPM policies with Prisma Cloud CLI

```
pc -vv policy set --status disable --compliance_standard 'CIS v1.4.0 (AWS)'
```

### Code Security

The below examples are using Github as integration but it works as well with other integration: 
- Bitbucket
- Gitlab
- AzureRepos
- Github Enterprise
- Gitlab Enterprise
- Bitbucket Enterprise

Count the number of unique git authors across all Github repositories:  
```
pc -ojson repositories count-git-authors -i Github | jq .
```

Get the details of all CVE across all Github repositories:  
```
 pc -ojson repositories search -i Github -c Vulnerabilities -t packageCve --details | jq .
```

Get all secrets across all Github repositories:  
```
pc -ojson repositories search -i Github -c Secrets -t violation  | jq .
```

Get all drift across all Github repositories: 
```
pc repositories search --integration_type Github --categories Drift
```