# coding:utf-8
import time

import pytest

from lib.enquiry import EnquiryManager, Enquiry

pytest_plugins = ["errbot.backends.test"]
extra_plugin_dir = "."


def test_enquiry():
    """
    Enquiry class tests
    """
    user_id = "test_id"
enquiry_data = {
    "id": "60a7c8876d573fae8028be34",
    "route": "slack_query",
    "ttl": 1440,
    "users": [],
    "roles": [],
    "schema": {
        "type": "object",
        "properties": {
            "password": {
                "type": "string",
                "description": "Run this workflow (yes/no)",
                "required": True,
            },
        },
    },
}
    enquiry_id = enquiry_data["id"]

    enquiry = Enquiry(enquiry_data)

    # to be completed.


if __name__ == "__main__":
    print("Run with pytest")
    exit(1)
