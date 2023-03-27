import datetime
import time

import pytest

from hs_api.api.hubspot_api import BATCH_LIMITS, EMAIL_BATCH_LIMIT, HubSpotClient
from hs_api.settings.settings import (
    HUBSPOT_TEST_ACCESS_TOKEN,
    HUBSPOT_TEST_PIPELINE_ID,
    HUBSPOT_TEST_TICKET_PIPELINE_ID,
)

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


def test_pipeline_id_none_raises_value_error():
    with pytest.raises(ValueError):
        client = HubSpotClient(access_token=HUBSPOT_TEST_ACCESS_TOKEN, pipeline_id=None)
        client.pipeline_stages


def test_create_and_find_contact(hubspot_client):

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

    # Added a retry loop because this test is failing
    for i in range(0, 100):
        time.sleep(10)
        contact = hubspot_client.find_contact("hs_object_id", contact_result.id)
        if len(contact) > 0:
            break
    assert contact


def test_create_and_find_company(hubspot_client):

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

    for i in range(0, 100):
        time.sleep(7)
        company = hubspot_client.find_company("hs_object_id", company_result.id)
        if len(company) > 0:
            break
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


def test_create_and_find_deal(hubspot_client):

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


def test_find_owner_by_email(hubspot_client):
    # This test relies on owner_id "49185288" existing in the testing environment.
    owner = hubspot_client.find_owner("email", "lovely-whole.abcaebiz@mailosaur.io")
    assert owner
    assert owner.id == "49185288"


def test_find_owner_not_found_returns_none(hubspot_client):
    owner = hubspot_client.find_owner("email", "email@doesnotexist.com")
    assert owner is None


def test_find_owner_by_id(hubspot_client):
    # This test relies on owner_id "49185288" existing in the testing environment.
    owner = hubspot_client.find_owner("id", "49185288")
    assert owner
    assert owner.email == "lovely-whole.abcaebiz@mailosaur.io"


def test_find_owner_without_id_or_email(hubspot_client):
    with pytest.raises(NameError):
        hubspot_client.find_owner("some_id", "some_value")


def test_find_all_tickets_returns_batches(hubspot_client):
    tickets = hubspot_client.find_all_tickets()

    # Assert that the first batch contains the limit of records
    # for a batch
    initial_batch = next(tickets)
    assert len(initial_batch) == BATCH_LIMITS

    following_batch = next(tickets)

    # Assert that the next batch follows on from the previous
    assert following_batch[0].updated_at > initial_batch[-1].updated_at


def test_find_all_tickets_returns_default_properties(hubspot_client):
    tickets = hubspot_client.find_all_tickets()
    actual = next(tickets)[0].properties
    expected = {
        "content": None,
        "createdate": None,
        "hs_lastmodifieddate": None,
        "hs_object_id": None,
        "hs_pipeline": None,
        "hs_pipeline_stage": None,
        "hs_ticket_category": None,
        "hs_ticket_priority": None,
        "subject": None,
    }

    # We don't care about the actual values just the keys
    assert actual.keys() == expected.keys()


def test_find_all_tickets_returns_given_properties(hubspot_client):
    tickets = hubspot_client.find_all_tickets(
        properties=["hs_lastmodifieddate", "hs_object_id"]
    )
    actual = next(tickets)[0].properties
    expected = {
        "hs_lastmodifieddate": None,
        "hs_object_id": None,
        # createdate is always returned
        "createdate": None,
    }

    # We don't care about the actual values just the keys
    assert actual.keys() == expected.keys()


def test_find_all_tickets_returns_after_given_hs_lastmodifieddate(hubspot_client):
    all_tickets = hubspot_client.find_all_tickets()
    filter_value = next(all_tickets)[0].updated_at
    filtered_tickets = hubspot_client.find_all_tickets(
        filter_name="hs_lastmodifieddate",
        filter_value=filter_value,
    )

    # Assert that the first record of the returned filtered list starts
    # after the original returned list
    assert next(filtered_tickets)[0].updated_at > filter_value


def test_find_all_tickets_returns_after_given_hs_object_id(hubspot_client):
    all_tickets = hubspot_client.find_all_tickets()
    filter_value = next(all_tickets)[0].id
    filtered_tickets = hubspot_client.find_all_tickets(
        filter_name="hs_object_id",
        filter_value=filter_value,
    )

    # Assert that the first record of the returned filtered list starts
    # after the original returned list
    assert next(filtered_tickets)[0].id > filter_value


def test_find_all_tickets_returns_for_given_pipeline_id(hubspot_client):
    all_tickets = hubspot_client.find_all_tickets(
        pipeline_id=HUBSPOT_TEST_TICKET_PIPELINE_ID
    )
    actual_pipeline = next(all_tickets)[0].properties["hs_pipeline"]

    assert actual_pipeline == HUBSPOT_TEST_TICKET_PIPELINE_ID


def test_pipeline_details_default(hubspot_client):
    pipelines = hubspot_client.pipeline_details()

    assert len(pipelines) == 1

    actual_pipeline = pipelines[0].id

    assert actual_pipeline == hubspot_client.pipeline_id


def test_pipeline_details_for_given_pipeline(hubspot_client):
    pipelines = hubspot_client.pipeline_details(
        pipeline_id=HUBSPOT_TEST_TICKET_PIPELINE_ID
    )

    assert len(pipelines) == 1

    actual_pipeline = pipelines[0].id

    assert actual_pipeline == HUBSPOT_TEST_TICKET_PIPELINE_ID

    assert pipelines[0].object_type == "TICKET"


def test_pipeline_details_for_all_pipelines(hubspot_client):
    pipelines = hubspot_client.pipeline_details(return_all_pipelines=True)
    assert len(pipelines) > 1


def test_find_all_deals_returns_default_properties(hubspot_client):
    deals = hubspot_client.find_all_deals()
    actual = next(deals)[0].properties
    expected = {
        "amount": None,
        "closedate": None,
        "createdate": None,
        "dealname": None,
        "dealstage": None,
        "hs_lastmodifieddate": None,
        "hs_object_id": None,
        "pipeline": None,
    }

    # We don't care about the actual values just the keys
    assert actual.keys() == expected.keys()


def test_find_all_deals_returns_given_properties(hubspot_client):
    deals = hubspot_client.find_all_deals(
        properties=["hs_lastmodifieddate", "hs_object_id"]
    )
    actual = next(deals)[0].properties
    expected = {
        "hs_lastmodifieddate": None,
        "hs_object_id": None,
        # createdate is always returned
        "createdate": None,
    }

    # We don't care about the actual values just the keys
    assert actual.keys() == expected.keys()


def test_find_all_deals_returns_after_given_hs_lastmodifieddate(hubspot_client):
    all_deals = hubspot_client.find_all_deals()
    filter_value = next(all_deals)[0].updated_at
    filtered_deals = hubspot_client.find_all_deals(
        filter_name="updated_at",
        filter_value=filter_value,
    )

    # Assert that the first record of the returned filtered list starts
    # after the original returned list
    assert next(filtered_deals)[0].updated_at > filter_value


def test_find_all_deals_returns_after_given_hs_object_id(hubspot_client):
    all_deals = hubspot_client.find_all_deals()
    filter_value = next(all_deals)[0].id
    filtered_deals = hubspot_client.find_all_deals(
        filter_name="id",
        filter_value=filter_value,
    )

    # Assert that the first record of the returned filtered list starts
    # after the original returned list
    assert next(filtered_deals)[0].id > filter_value


def test_find_all_deals_returns_for_given_pipeline_id(hubspot_client):
    all_deals = hubspot_client.find_all_deals(pipeline_id=HUBSPOT_TEST_PIPELINE_ID)
    actual_pipeline = next(all_deals)[0].properties["pipeline"]

    assert actual_pipeline == HUBSPOT_TEST_PIPELINE_ID


def test_find_all_deals_returns_properties_with_history(hubspot_client):
    expected_history = ["dealstage"]
    all_deals = hubspot_client.find_all_deals(properties_with_history=expected_history)
    actual_history = next(all_deals)[0].properties_with_history

    assert expected_history == [*actual_history]


def test_find_all_email_events_returns_batches(hubspot_client):
    email_events = hubspot_client.find_all_email_events()

    # Assert that the first batch contains the limit of records
    # for a batch
    initial_batch = next(email_events)
    assert len(initial_batch) == EMAIL_BATCH_LIMIT

    following_batch = next(email_events)

    # Assert that the next batch follows on from the previous and is not the same batch
    assert following_batch != initial_batch


def test_find_all_email_events_returns_after_given_starttimestamp_epoch(hubspot_client):
    all_events = hubspot_client.find_all_email_events()
    filter_value = next(all_events)[-1]["created"]
    filtered_events = hubspot_client.find_all_email_events(
        filter_name="startTimestamp",
        filter_value=filter_value + 1,
    )
    # Assert that the first record of the returned filtered list starts
    # after the original returned list
    assert next(filtered_events)[0]["created"] > filter_value
