import logging
import click

from prismacloud.cli import cli_output, pass_environment
from prismacloud.cli.api import pc_api


class ComplianceHelper:
    def get_compliance_finding(
        self,
        standard: str,
        compliance_requirement: str,
        compliance_section: str,
        scan_status: str,
        account_group: str,
        limit: int = 1000,
    ):
        parameters = {}
        parameters["filters"] = [
            {"name": "includeEventForeignEntities", "operator": "=", "value": "true"},
            {"name": "account.group", "operator": "=", "value": account_group},
            {"name": "policy.complianceSection", "operator": "=", "value": compliance_section},
            {"name": "policy.complianceRequirement", "operator": "=", "value": compliance_requirement},
            {"name": "policy.complianceStandard", "operator": "=", "value": standard},
            {"name": "scan.status", "operator": "=", "value": scan_status},
            {"name": "decorateWithDerivedRRN", "operator": "=", "value": True},
        ]
        parameters["limit"] = 10
        parameters["timeRange"] = {"type": "to_now", "value": "epoch"}  # Latest results

        # response = requests.request("POST", url, headers=self.headers, data=payload)
        return pc_api.resource_scan_info_read(body_params=parameters)

    def get_compliance_standard(self, standard_name: str):
        response = pc_api.compliance_standard_list_read()
        logging.info("API - GET STANDARD %s", response)
        for standard in response:
            if standard.get("name", "") == standard_name:
                return standard


@click.group("compliance", short_help="[CSPM] Returns a list of alerts based on compliance related findings in Prisma Cloud.")
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

    logging.info("API - Starting compliance exporter ...")

    # Main logic
    # Get compliance standard information
    standard = helper.get_compliance_standard(standard_name=compliance_standard)

    # Get all requirements from compliance standard
    requirements = pc_api.compliance_standard_requirement_list_read(compliance_standard_id=standard["id"])
    logging.info("API - Requirements collected: %s", requirements)
    for requirement in requirements:
        # Get all sections from compliance standard
        sections = pc_api.compliance_standard_requirement_section_list_read(compliance_requirement_id=requirement["id"])
        logging.info("API - Sections collected: %s", sections)
        for section in sections:

            def get_results(requirement, section, scan_status: str):
                """Helper function to get compliance findings"""
                func_data = []
                findings = helper.get_compliance_finding(
                    standard["name"], requirement["name"], section["sectionId"], scan_status, account_group
                )
                for resource in findings:
                    func_data = func_data + [
                        {
                            "standard_name": standard["name"],
                            "requirement_name": requirement["name"],
                            "requirement_id": requirement["requirementId"],
                            "section_id": section["sectionId"],
                            "account_name": resource["accountName"],
                            "account_id": resource["accountId"],
                            "cloud_type": resource["cloudType"],
                            "rrn": resource.get("rrn", resource["id"]),
                            "status": scan_status,
                        }
                    ]
                return func_data

            # Get finding results for given section of compliance standard
            data = data + get_results(requirement, section, "failed")
            data = data + get_results(requirement, section, "passed")

    cli_output(data)


cli.add_command(compliance_exporter)
