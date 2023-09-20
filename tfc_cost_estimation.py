#!/usr/bin/env python3

"""This script interacts with Terraform Cloud (TFC) to enumerate all the
workspaces within a specified organization, count the resources in each
workspace, and estimate their cost.

Usage:
python3 script.py --org <your_organization> [--url <your_custom_url>].
Replace <your_organization> with the name of your TFC organization and
<your_custom_url>.
"""

import os
import argparse
import logging
from terrasnek.api import TFC

logging.basicConfig(level=logging.INFO)

TFC_TOKEN = os.getenv("TFC_TOKEN")
TFC_URL = os.getenv("TFC_URL", "https://app.terraform.io")
TFC_COST = float(0.00014 * 24)  # As of 2023-07-12, 0.00014 USD per hour


class TerraformCloudError(Exception):
    """Custom exception for Terraform Cloud errors.

    :param Exception: Base exception class
    :type Exception: Exception
    """


def cli():
    """Parse CLI arguments.

    :returns: CLI arguments
    :rtype: argparse.Namespace
    """
    args = argparse.ArgumentParser(
        description="Count Terraform Cloud Resources"
    )
    args.add_argument(
        "--org", "-o", help="Terraform Cloud Organization", required=True
    )
    args.add_argument(
        "--url", "-u", help="Terraform Cloud URL", default=TFC_URL
    )

    return args.parse_args()


def count_resources(api, ws_id: str) -> int:
    """
    Count the number of resources in a workspace.

    :param api: TFC API object
    :type api: terrasnek.api.TFC
    :param ws_id: Workspace ID
    :returns: Number of resources in a workspace
    """
    total_resources = 0
    next_url = None

    try:
        while True:
            if next_url:
                response = api._get(next_url)
            else:
                response = api.workspaces.list_resources(ws_id)

            resources = response["data"]
            total_resources += len(resources)

            next_url = response.get("links", {}).get("next")
            if not next_url:
                break
    except Exception as err:
        raise TerraformCloudError(
            f"Error counting resources: {str(err)}"
        ) from err

    return total_resources


def calculate_cost(ws_name: str, ws_id: str, resources: int) -> float:
    """Calculate the monthly cost of a workspace.

    :param ws_name: Workspace name
    :param ws_id: Workspace ID
    :param resources: Number of resources in a workspace
    :returns: Monthly cost of a workspace
    """

    total_cost = round(resources * TFC_COST, 4)
    logging.info(
        "Workspace: %s (%s - %s resources) - Monthly Cost: $%s",
        ws_name,
        ws_id,
        resources,
        total_cost,
    )
    return total_cost


def main():
    """Main function."""
    args = cli()

    if not TFC_TOKEN:
        print("TFC_TOKEN environment variable not set")
        exit(1)

    try:
        api = TFC(TFC_TOKEN, url=args.url)
        api.set_org(args.org)
    except Exception as err:
        print(f"Failed to initialize TFC API: {str(err)}")
        exit(1)

    try:
        all_workspaces = api.workspaces.list_all()["data"]
    except Exception as err:
        print(f"Failed to list workspaces: {str(err)}")
        exit(1)

    workspace_data = []

    for workspace in all_workspaces:
        workspace_name = workspace["attributes"]["name"]
        workspace_id = workspace["id"]

        try:
            resources = count_resources(api, workspace_id)
            workspace_data.append((workspace_name, workspace_id, resources))
        except TerraformCloudError as err:
            print(f"Error with workspace {workspace_name}: {str(err)}")

    workspace_data.sort(key=lambda x: x[2])

    total_resources = 0
    total_monthly_cost = 0

    for ws_name, workspace_id, resources in workspace_data:
        total_resources += resources
        total_monthly_cost += calculate_cost(ws_name, workspace_id, resources)

    total_yearly_cost = round(total_monthly_cost * 12, 4)

    logging.info("Total Resources: %s", total_resources)
    logging.info("Total Monthly Cost: $%s", round(total_monthly_cost, 4))
    logging.info("Total Yearly Cost: $%s", total_yearly_cost)


if __name__ == "__main__":
    main()
