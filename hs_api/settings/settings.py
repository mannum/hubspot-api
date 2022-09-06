import os
from pathlib import Path

from dotenv import load_dotenv

config = load_dotenv(override=False)

PROJECT_ROOT = Path(__file__).parent.parent

CONTRACTS_ROOT = PROJECT_ROOT / "contracts"

TEMP_ROOT = PROJECT_ROOT / ".temp"
# Make the temp directory if it doesn't exist
TEMP_ROOT.mkdir(parents=True, exist_ok=True)

# Tests
TEST_ROOT = PROJECT_ROOT.parent / "test"
TEST_FILES_ROOT = TEST_ROOT / "test_files"

# Hubspot API/ Default pipeline
HUBSPOT_ACCESS_TOKEN = os.environ.get("HUBSPOT_ACCESS_TOKEN")
HUBSPOT_PIPELINE_ID = os.environ.get("HUBS_PIPELINE_ID")

# Hubspot Test API/Pipeline
HUBSPOT_TEST_ACCESS_TOKEN = os.environ.get("HUBSPOT_TEST_ACCESS_TOKEN")
HUBSPOT_TEST_PIPELINE_ID = os.environ.get("HUBSPOT_TEST_PIPELINE_ID")
HUBSPOT_TEST_TICKET_PIPELINE_ID = os.environ.get("HUBSPOT_TEST_TICKET_PIPELINE_ID")
