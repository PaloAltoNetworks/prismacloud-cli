import logging
import click
import json

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


class ComplianceHelper():

    def get_compliance_finding(self, standard: str, compliance_requirement: str, compliance_section: str, scan_status: str, account_group: str, limit: int = 1000):
        # url = f"https://{self.stack}.prismacloud.io/resource/scan_info"
        payload = json.dumps({
        "filters": [  # Fine could be done based on https://prisma.pan.dev/api/cloud/cspm/asset-explorer/#operation/get-resource-scan-info
            {
            "name": "includeEventForeignEntities",
            "operator": "=",
            "value": "true"
            },
            {
            "name": "account.group",
            "operator": "=",
            "value": account_group
            },
            {
            "name": "policy.complianceSection",
            "operator": "=",
            "value": compliance_section
            },
            {
            "name": "policy.complianceRequirement",
            "operator": "=",
            "value": compliance_requirement
            },
            {
            "name": "policy.complianceStandard",
            "operator": "=",
            "value": standard
            },
            {
            "name": "scan.status",
            "operator": "=",
            "value": scan_status
            },
            {
            "name": "decorateWithDerivedRRN",
            "operator": "=",
            "value": True
            }
        ],
        "limit": limit,
        "timeRange": {
            "type": "to_now",  # Latest results
            "value": "epoch"
        }
        })

        # response = requests.request("POST", url, headers=self.headers, data=payload)
        return pc_api.resource_scan_info_read(body_params=payload)

    def get_compliance_requirements(self, standard_id: str):
        return pc_api.compliance_standard_requirement_list_read(compliance_standard_id=standard_id)

    def get_compliance_standard(self, standard_name: str):
        response = pc_api.compliance_standard_list_read()
        for standard in response:
            if standard.get('name', '') == standard_name:
                return standard

    def get_compliance_section(self, requirement_id: str):
        return pc_api.compliance_standard_requirement_section_list_read(compliance_requirement_id=requirement_id)


@click.group(
    "compliance", short_help="[CSPM] Returns a list of alerts based on compliance related findings in Prisma Cloud."
)
@pass_environment
def cli(ctx):
    pass


@click.command(name="export")
@click.option("--compliance-standard", help="Compliance standard, e.g.: 'CIS v1.4.0 (AWS)'")
@click.option("--account-group", help="Account Group ID, e.g.: 'MyAccountGroup'")
def compliance_exporter(compliance_standard, account_group):
    """Returns a list of alerts based on compliance related findings in Prisma Cloud."""
    data = []

    helper = ComplianceHelper()

    # Main logic
    # Get compliance standard information
    standard = helper.get_compliance_standard(standard_name=compliance_standard)

    logging.info("API - Starting compliance exporter ...")

    # Get all requirements from compliance standard
    # requirements = pc_api.compliance_standard_read(compliance_standard_id=standard['id'])
    requirements = helper.get_compliance_requirements(standard_id=standard['id'])
    for requirement in requirements:
        # Get all sections from compliance standard
        sections = helper.get_compliance_section(requirement_id=requirement['id'])
        for section in sections:
            def get_results(requirement, section, scan_status: str):
                """ Helper function to get compliance findings """
                findings = helper.get_compliance_finding(
                    standard["name"],
                    requirement['name'],
                    section['sectionId'],
                    scan_status,
                    account_group
                )
                for resource in findings.get('resources', []):                    
                    data = data + [
                        standard['name'] ,requirement['name'],requirement['requirementId'],
                        section['sectionId'],resource['accountName'],
                        resource['accountId'],resource['cloudType'],
                        resource.get('rrn', resource['id']), scan_status
                    ]

            # Get finding results for given section of compliance standard
            get_results(requirement, section, "failed")
            get_results(requirement, section, "passed")

    print("CSV generation finished")

    cli_output(data)


cli.add_command(compliance_exporter)

