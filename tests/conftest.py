import datetime

import pytest

from hs_api.api.hubspot_api import BATCH_LIMITS, EMAIL_BATCH_LIMIT, HubSpotClient
from hs_api.settings.settings import (
    HUBSPOT_TEST_ACCESS_TOKEN,
    HUBSPOT_TEST_PIPELINE_ID,
    HUBSPOT_TEST_TICKET_PIPELINE_ID,
)


@pytest.fixture(scope="session")
def hubspot_client(deal_name, company_name, email, email_custom_domain, unique_id):
    client = HubSpotClient(
        access_token=HUBSPOT_TEST_ACCESS_TOKEN, pipeline_id=HUBSPOT_TEST_PIPELINE_ID
    )
    test_deal = None
    test_tickets = None
    test_emails = []

    try:
        # create Hubspot elements
        test_deal = client.create_deal(deal_name)
        test_tickets = create_tickets(client, unique_id, BATCH_LIMITS + 1)
        test_emails = create_emails(client, EMAIL_BATCH_LIMIT + 1)

        yield client

    finally:
        # clean up all created elements
        if test_deal:
            client.delete_deal(test_deal.id)

        if test_tickets:
            for tid in test_tickets:
                hubspot_client.delete_ticket(tid)

        for tid in test_emails:
            client.delete_email(tid)

        clear_down_test_objects(
            client, company_name, deal_name, email, email_custom_domain
        )


def create_emails(client, quantity):
    test_emails = []
    for _ in range(quantity):
        test_emails.append(client.create_email().id)
    return test_emails


def create_tickets(client, unique_id, quantity):
    ticket_ids = []
    for i in range(quantity):
        test_ticket_name = f"{unique_id}{i} ticket name"
        properties = dict(
            subject=test_ticket_name,
            hs_pipeline=HUBSPOT_TEST_TICKET_PIPELINE_ID,
            hs_pipeline_stage=1,
            hs_ticket_priority="HIGH",
        )

        ticket_result = client.create_ticket(**properties)
        assert ticket_result
        assert ticket_result.id
    return ticket_ids


def clear_down_test_objects(
    client, company_name, deal_name, email, email_custom_domain
):
    companies = client.find_company("name", company_name)
    for company in companies:
        client.delete_company(company.id)

    deals = client.find_deal("dealname", deal_name)
    for deal in deals:
        client.delete_deal(deal.id)

    client.delete_contact(value=email, property_name="email")
    client.delete_contact(value=email_custom_domain, property_name="email")


@pytest.fixture(scope="session")
def unique_id():
    current_timestamp = datetime.datetime.now()
    return f"{current_timestamp:%Y%m%d%H%M%S%f}"


@pytest.fixture(scope="session")
def company_name(unique_id):
    return f"{unique_id} company"


@pytest.fixture(scope="session")
def email(unique_id):
    return f"{unique_id}@email.com"


@pytest.fixture(scope="session")
def email_custom_domain(unique_id):
    return f"{unique_id}@domain{unique_id}.ai"


@pytest.fixture(scope="session")
def domain(unique_id):
    return f"{unique_id}.test"


@pytest.fixture(scope="session")
def deal_name(unique_id):
    return f"{unique_id} deal name"


@pytest.fixture(scope="session")
def first_name(unique_id):
    return f"{unique_id} first name"


@pytest.fixture(scope="session")
def last_name(unique_id):
    return f"{unique_id} last name"


@pytest.fixture(scope="session")
def phone(unique_id):
    return f"{unique_id}"
