import datetime
import time

import pytest

from hs_api.api.hubspot_api import HubSpotClient
from hs_api.settings.settings import HUBSPOT_TEST_ACCESS_TOKEN, HUBSPOT_TEST_PIPELINE_ID

# Test Pipeline

current_timestamp = datetime.datetime.now()
UNIQUE_ID = f"{current_timestamp:%Y%m%d%H%M%S%f}"

TEST_COMPANY_NAME = f"{UNIQUE_ID} company"
TEST_EMAIL = f"{UNIQUE_ID}@email.com"
TEST_EMAIL_CUSTOM_DOMAIN = f"{UNIQUE_ID}@domain{UNIQUE_ID}.ai"
TEST_DEAL_NAME = f"{UNIQUE_ID} deal name"


def clear_down_test_objects(client):
    companies = client.find_company("name", TEST_COMPANY_NAME)
    for company in companies:
        client.delete_company(company.id)

    deals = client.find_deal("dealname", TEST_DEAL_NAME)
    for deal in deals:
        client.delete_deal(deal.id)

    client.delete_contact(value=TEST_EMAIL, property_name="email")
    client.delete_contact(value=TEST_EMAIL_CUSTOM_DOMAIN, property_name="email")


@pytest.fixture()
def hubspot_client():
    client = HubSpotClient(
        access_token=HUBSPOT_TEST_ACCESS_TOKEN, pipeline_id=HUBSPOT_TEST_PIPELINE_ID
    )
    try:
        yield client
    finally:
        clear_down_test_objects(client)


def test_create_and_search_contact(hubspot_client):

    test_first_name = f"{UNIQUE_ID} first name"
    test_last_name = f"{UNIQUE_ID} last name"
    test_phone = f"{UNIQUE_ID}"

    # Assert the contact doesn't already exist
    contact = hubspot_client.find_contact("email", TEST_EMAIL)
    assert not contact

    # Create the contact
    contact_result = hubspot_client.create_contact(
        email=TEST_EMAIL,
        first_name=test_first_name,
        last_name=test_last_name,
        phone=test_phone,
        company=TEST_COMPANY_NAME,
    )

    assert contact_result
    assert contact_result.id

    # Assert the contact now exists based on previous creation
    time.sleep(10)
    contact = hubspot_client.find_contact("hs_object_id", contact_result.id)
    assert contact


def test_create_and_search_company(hubspot_client):

    test_domain = f"{UNIQUE_ID}.test"

    # Assert the company doesn't already exist
    company = hubspot_client.find_company("name", TEST_COMPANY_NAME)
    assert not company

    # Create the company
    company_result = hubspot_client.create_company(
        name=TEST_COMPANY_NAME, domain=test_domain
    )

    assert company_result
    assert company_result.id

    # Assert the company now exists based on previous creation
    time.sleep(7)
    company = hubspot_client.find_company("hs_object_id", company_result.id)
    assert company


def test_create_contact_and_associated_company_with_auto_created_company(
    hubspot_client,
):

    test_first_name = f"{UNIQUE_ID} first name"
    test_last_name = f"{UNIQUE_ID} last name"
    test_phone = f"{UNIQUE_ID}"

    # Assert the company and contact don't already exist
    company = hubspot_client.find_company("name", TEST_COMPANY_NAME)
    assert not company

    contact = hubspot_client.find_contact("email", TEST_EMAIL_CUSTOM_DOMAIN)
    assert not contact

    # Create the contact and company
    result = hubspot_client.create_contact_and_company(
        email=TEST_EMAIL_CUSTOM_DOMAIN,
        first_name=test_first_name,
        last_name=test_last_name,
        phone=test_phone,
        company=TEST_COMPANY_NAME,
    )

    assert result
    assert result["contact"].id
    assert result["company"].id

    # Assert the company and contact now exists based on previous creation
    # and are linked
    time.sleep(7)
    company = hubspot_client.find_company("hs_object_id", result["company"].id)
    assert company
    assert company[0].properties["name"] == TEST_COMPANY_NAME

    contact = hubspot_client.find_contact("email", TEST_EMAIL_CUSTOM_DOMAIN)
    assert contact


def test_create_contact_and_associated_company_without_auto_created_company(
    hubspot_client,
):

    test_first_name = f"{UNIQUE_ID} first name"
    test_last_name = f"{UNIQUE_ID} last name"
    test_phone = f"{UNIQUE_ID}"

    # Assert the company and contact don't already exist
    company = hubspot_client.find_company("name", TEST_COMPANY_NAME)
    assert not company

    contact = hubspot_client.find_contact("email", TEST_EMAIL)
    assert not contact

    # Create the contact and company
    result = hubspot_client.create_contact_and_company(
        email=TEST_EMAIL,
        first_name=test_first_name,
        last_name=test_last_name,
        phone=test_phone,
        company=TEST_COMPANY_NAME,
    )

    assert result
    assert result["contact"].id
    assert result["company"].id

    # Assert the company and contact now exists based on previous creation
    # and are linked
    time.sleep(7)
    company = hubspot_client.find_company("hs_object_id", result["company"].id)
    assert company
    assert company[0].properties["name"] == TEST_COMPANY_NAME

    contact = hubspot_client.find_contact("email", TEST_EMAIL)
    assert contact

    association = hubspot_client.contact_associations(result["contact"].id, "company")
    assert association
    assert association[0].id == result["company"].id


def test_create_and_search_deal(hubspot_client):

    test_amount = 99.99

    # Assert the deal doesn't already exist
    deal = hubspot_client.find_deal("dealname", TEST_DEAL_NAME)
    assert not deal

    # Create the deal
    deal_result = hubspot_client.create_deal(
        name=TEST_DEAL_NAME,
        amount=test_amount,
    )

    assert deal_result
    assert deal_result.id

    # Assert the deal now exists based on previous creation
    time.sleep(7)
    deal = hubspot_client.find_deal("dealname", TEST_DEAL_NAME)
    assert deal


def test_create_deal_for_company(hubspot_client):

    test_amount = 99.99

    # Assert the deal and company don't already exist
    deal = hubspot_client.find_deal("dealname", TEST_DEAL_NAME)
    assert not deal

    company = hubspot_client.find_company("name", TEST_COMPANY_NAME)
    assert not company

    # Create the company
    company_result = hubspot_client.create_company(name=TEST_COMPANY_NAME)

    # Create the deal
    deal_result = hubspot_client.create_deal(
        name=TEST_DEAL_NAME, amount=test_amount, company_id=company_result.id
    )

    assert deal_result
    assert deal_result.id

    # Assert the company and deal now exists based on previous creation
    # and are linked
    time.sleep(7)
    deal = hubspot_client.find_deal("dealname", TEST_DEAL_NAME)
    assert deal

    company = hubspot_client.find_company("hs_object_id", company_result.id)
    assert company

    association = hubspot_client.deal_associations(deal_result.id, "company")
    assert association
    assert association[0].id == company_result.id


def test_create_deal_for_contact(hubspot_client):

    test_first_name = f"{UNIQUE_ID} first name"
    test_last_name = f"{UNIQUE_ID} last name"
    test_phone = f"{UNIQUE_ID}"
    test_amount = 99.99

    # Assert the deal and company don't already exist
    deal = hubspot_client.find_deal("dealname", TEST_DEAL_NAME)
    assert not deal

    contact = hubspot_client.find_contact("email", TEST_EMAIL)
    assert not contact

    # Create the contact
    contact_result = hubspot_client.create_contact(
        email=TEST_EMAIL,
        first_name=test_first_name,
        last_name=test_last_name,
        phone=test_phone,
        company=TEST_COMPANY_NAME,
    )

    # Create the deal
    deal_result = hubspot_client.create_deal(
        name=TEST_DEAL_NAME, amount=test_amount, contact_id=contact_result.id
    )

    assert deal_result
    assert deal_result.id

    # Assert the company and deal now exists based on previous creation
    # and are linked
    time.sleep(7)
    deal = hubspot_client.find_deal("dealname", TEST_DEAL_NAME)
    assert deal

    company = hubspot_client.find_contact("hs_object_id", contact_result.id)
    assert company

    association = hubspot_client.deal_associations(deal_result.id, "contact")
    assert association
    assert association[0].id == contact_result.id
