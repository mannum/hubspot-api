from pathlib import Path
import os

from dotenv import load_dotenv

config = load_dotenv(override=True)

PROJECT_ROOT = Path(__file__).parent.parent

CONTRACTS_ROOT = PROJECT_ROOT / "contracts"

TEMP_ROOT = PROJECT_ROOT / ".temp"
# Make the temp directory if it doesn't exist
TEMP_ROOT.mkdir(parents=True, exist_ok=True)

# Tests
TEST_ROOT = PROJECT_ROOT.parent / "test"
TEST_FILES_ROOT = TEST_ROOT / "test_files"

# Hubspot API/ Default pipeline
HUBSPOT_API_KEY = os.environ.get("HUBSPOT_API_KEY")
HUBSPOT_PIPELINE_ID = os.environ.get("HUBS_PIPELINE_ID")

# Hubspot Test API/Pipeline
HUBSPOT_TEST_API_KEY = os.environ.get("HUBSPOT_TEST_API_KEY")
HUBSPOT_TEST_PIPELINE_ID = os.environ.get("HUBS_TEST_PIPELINE_ID")
