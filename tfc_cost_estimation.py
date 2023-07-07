#!/usr/bin/env python3

import os
import argparse
from terrasnek.api import TFC

TFC_TOKEN = os.getenv("TFC_TOKEN")
TFC_URL = os.getenv("TFC_URL", "https://app.terraform.io")
TFC_COST = float(0.00014 * 24)


def cli():
    """Parse CLI arguments."""
    args = argparse.ArgumentParser(description="Count Terraform Cloud Resources")
    args.add_argument("--org", "-o", help="Terraform Cloud Organization", required=True)
    args.add_argument("--url", "-u", help="Terraform Cloud URL", default=TFC_URL)

    return args.parse_args()


def count_resources(api, ws_id):
    """Count the number of resources in a workspace."""
    resources = api.workspaces.list_resources(ws_id)["data"]

    return len(resources)


def main():
    """Main function."""
    args = cli()

    if not TFC_TOKEN:
        print("TFC_TOKEN environment variable not set")
        exit(1)

    api = TFC(TFC_TOKEN, url=args.url)
    api.set_org(args.org)

    all_workspaces = api.workspaces.list_all()["data"]

    workspace_data = []

    for workspace in all_workspaces:
        workspace_name = workspace["attributes"]["name"]
        workspace_id = workspace["id"]
        resources = count_resources(api, workspace_id)
        workspace_data.append((workspace_name, workspace_id, resources))

    workspace_data.sort(key=lambda x: x[2])

    total_resources = 0

    for ws_name, workspace_id, resources in workspace_data:
        total_resources += resources
        rounded_cost = round(resources * TFC_COST, 4)
        print(
            f"Workspace: {ws_name} ({workspace_id} - {resources} resources) "
            + f"- Monthly Cost: ${rounded_cost}"
        )

    rounded_total_cost = round(total_resources * TFC_COST, 4)
    rounded_yearly_cost = round(rounded_total_cost * 12, 4)

    print(f"Total: {total_resources} resources")
    print(f"Total Monthly Cost: ${rounded_total_cost}")
    print(f"Total Yearly Cost: ${rounded_yearly_cost}")


if __name__ == "__main__":
    main()
