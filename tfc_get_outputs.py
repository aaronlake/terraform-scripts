#!/usr/bin/env python3

"""This script interacts with Terraform Cloud (TFC) to get all or specific
outputs from a terraform workspace.

Usage:
python3 script.py --org <your_organization> [--url <your_custom_url>] \
    --ws <your_workspace> [--output <your_output>]
Replace <your_organization> with the name of your TFC organization and
<your_custom_url>.
"""

import os
import json
import argparse
import logging
from terrasnek.api import TFC

logging.basicConfig(level=logging.INFO)

TFC_TOKEN = os.getenv("TFC_TOKEN")
TFC_URL = os.getenv("TFC_URL", "https://app.terraform.io")


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
    args = argparse.ArgumentParser(description="Get Terraform Cloud Outputs")
    args.add_argument(
        "--org", help="Terraform Cloud Organization", required=True
    )
    args.add_argument(
        "--url", "-u", help="Terraform Cloud URL", default=TFC_URL
    )
    args.add_argument(
        "--ws", "-w", help="Terraform Cloud Workspace", required=True
    )
    args.add_argument(
        "--output", "-o", help="Terraform Cloud Output", required=False
    )

    return args.parse_args()


def get_outputs(args, ws_id: str, output: str) -> dict:
    """
    Get all or specific outputs from a workspace.

    :param args: CLI arguments
    :type args: argparse.Namespace
    :param ws_id: Workspace ID
    :param output: Output name
    :returns: Workspace outputs
    """
    try:
        tfc = TFC(TFC_TOKEN, url=args.url)
        tfc.set_org(args.org)

        workspace = tfc.workspaces.show(workspace_name=args.ws)
        if workspace is None:
            raise TerraformCloudError(
                f"Workspace {args.ws} not found in organization {args.org}"
            )

        return tfc.state_version_outputs.show_current_for_workspace(
            workspace_id=workspace["data"]["id"]
        )
    except Exception as err:
        raise TerraformCloudError(err) from err


def main():
    """Main function."""
    args = cli()

    if not TFC_TOKEN:
        print("Please set the TFC_TOKEN environment variable.")
        exit(1)

    try:
        outputs = get_outputs(args, args.ws, args.output)
    except TerraformCloudError as err:
        print(err)
        exit(1)

    output_dict = {
        output["attributes"]["name"]: output["attributes"]["value"]
        for output in outputs["data"]
    }

    if args.output:
        print(output_dict[args.output])
    else:
        print(json.dumps(output_dict, indent=4))


if __name__ == "__main__":
    main()
