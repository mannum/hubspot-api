import pytest
from tenacity import retry, stop_after_attempt, wait_fixed

from hs_api.api.hubspot_api import BATCH_LIMITS, EMAIL_BATCH_LIMIT, HubSpotClient
from hs_api.settings.settings import (
    HUBSPOT_TEST_ACCESS_TOKEN,
    HUBSPOT_TEST_PIPELINE_ID,
    HUBSPOT_TEST_TICKET_PIPELINE_ID,
)


def test_pipeline_id_none_raises_value_error():
    with pytest.raises(ValueError):
        client = HubSpotClient(access_token=HUBSPOT_TEST_ACCESS_TOKEN, pipeline_id=None)
        client.pipeline_stages


def test_create_and_find_contact(
    hubspot_client, first_name, last_name, email, phone, company_name
):
    # Assert the contact doesn't already exist
    contact = hubspot_client.find_contact("email", email)
    assert not contact

    # Create the contact
    contact_result = hubspot_client.create_contact(
        email=email,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        company=company_name,
    )

    assert contact_result
    assert contact_result.id

    @retry(stop=stop_after_attempt(7), wait=wait_fixed(2))
    def _get_contact():
        _contact = hubspot_client.find_contact("hs_object_id", contact_result.id)
        assert _contact

    # Assert the contact now exists based on previous creation
    _get_contact()


def test_create_and_find_company(hubspot_client, company_name, domain):
    # Assert the company doesn't already exist
    company = hubspot_client.find_company("name", company_name)
    assert not company

    # Create the company
    company_result = hubspot_client.create_company(name=company_name, domain=domain)

    assert company_result
    assert company_result.id

    @retry(stop=stop_after_attempt(7), wait=wait_fixed(2))
    def _test():
        _company = hubspot_client.find_company("hs_object_id", company_result.id)
        assert _company

    # Assert the company now exists based on previous creation
    _test()


def test_create_and_find_company_iter(hubspot_client, domain, unique_id):
    company_name = f"{unique_id} test_create_and_find_company_iter"

    # Assert the company doesn't already exist
    with pytest.raises(StopIteration):
        next(hubspot_client.find_company_iter("name", company_name))

    # Create the company
    company_result = hubspot_client.create_company(name=company_name, domain=domain)

    assert company_result
    assert company_result.id

    @retry(stop=stop_after_attempt(7), wait=wait_fixed(2))
    def _test():
        _company = next(
            hubspot_client.find_company_iter("hs_object_id", company_result.id)
        )
        assert _company

    # Assert the company now exists based on previous creation
    _test()


def test_create_and_find_ticket(hubspot_client: HubSpotClient, unique_id):
    ticket_name = f"{unique_id}0 ticket name"
    ticket = hubspot_client.find_all_tickets(
        filter_name="subject", filter_value=ticket_name
    )
    assert ticket


def test_create_and_find_email(hubspot_client: HubSpotClient):
    email_resp = hubspot_client.find_all_email_events()
    assert next(email_resp)


def test_create_contact_and_associated_company_with_auto_created_company(
    hubspot_client,
    first_name,
    last_name,
    email_custom_domain,
    phone,
    unique_id,
):
    company_name = f"{unique_id} test_create_contact_and_associated_company_with_auto_created_company"
    # Assert the company and contact don't already exist
    company = hubspot_client.find_company("name", company_name)
    assert not company

    email_custom_domain = (
        f"{unique_id}@testcreatecontactandassociatedcompanywithautocreatedcompany.com"
    )
    contact = hubspot_client.find_contact("email", email_custom_domain)
    assert not contact

    # Create the contact and company
    result = hubspot_client.create_contact_and_company(
        email=email_custom_domain,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        company=company_name,
    )

    assert result
    assert result["contact"].id
    assert result["company"].id

    @retry(stop=stop_after_attempt(7), wait=wait_fixed(2))
    def _test():
        _company = hubspot_client.find_company("hs_object_id", result["company"].id)
        assert _company
        assert _company[0].properties["name"] == company_name

        _contact = hubspot_client.find_contact("email", email_custom_domain)
        assert _contact

    # Assert the company and contact now exists based on previous creation
    # and are linked
    _test()


def test_create_contact_and_associated_company_without_auto_created_company(
    hubspot_client, first_name, last_name, phone, unique_id
):
    # Assert the company and contact don't already exist
    company_name = f"{unique_id} test_create_contact_and_associated_company_without_auto_created_company"
    company = hubspot_client.find_company("name", company_name)
    assert not company

    email = f"{unique_id}@testcreatecontactandassociatedcompanywithoutautocreatedcompany.com"
    contact = hubspot_client.find_contact("email", email)
    assert not contact

    # Create the contact and company
    result = hubspot_client.create_contact_and_company(
        email=email,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        company=company_name,
    )

    assert result
    assert result["contact"].id
    assert result["company"].id

    @retry(stop=stop_after_attempt(7), wait=wait_fixed(2))
    def _test():
        _company = hubspot_client.find_company("hs_object_id", result["company"].id)
        assert _company
        assert _company[0].properties["name"] == company_name

        _contact = hubspot_client.find_contact("email", email)
        assert _contact

        _association = hubspot_client.contact_associations(
            result["contact"].id, "company"
        )
        assert _association
        assert _association[0].to_object_id == int(result["company"].id)

    # Assert the company and contact now exists based on previous creation
    # and are linked
    _test()


def test_create_and_find_deal(hubspot_client, unique_id):
    test_amount = 99.99

    # Assert the deal doesn't already exist
    deal_name = f"{unique_id} test_create_and_find_deal"
    deal = hubspot_client.find_deal("dealname", deal_name)
    assert not deal

    # Create the deal
    deal_result = hubspot_client.create_deal(
        name=deal_name,
        amount=test_amount,
    )

    assert deal_result
    assert deal_result.id

    @retry(stop=stop_after_attempt(7), wait=wait_fixed(2))
    def _test():
        _deal = hubspot_client.find_deal("dealname", deal_name)
        assert _deal

    # Assert the deal now exists based on previous creation
    _test()


def test_create_deal_for_company(hubspot_client, unique_id):
    test_amount = 99.99

    # Assert the deal and company don't already exist
    deal_name = f"{unique_id} test_create_deal_for_company"
    deal = hubspot_client.find_deal("dealname", deal_name)
    assert not deal

    company_name = f"{unique_id} test_create_deal_for_company"
    company = hubspot_client.find_company("name", company_name)
    assert not company

    # Create the company
    company_result = hubspot_client.create_company(name=company_name)

    # Create the deal
    deal_result = hubspot_client.create_deal(
        name=deal_name, amount=test_amount, company_id=company_result.id
    )

    assert deal_result
    assert deal_result.id

    @retry(stop=stop_after_attempt(7), wait=wait_fixed(2))
    def _test():
        _deal = hubspot_client.find_deal("dealname", deal_name)
        assert _deal

        _company = hubspot_client.find_company("hs_object_id", company_result.id)
        assert _company

        _association = hubspot_client.deal_associations(deal_result.id, "company")
        assert _association
        assert _association[0].to_object_id == int(company_result.id)

    # Assert the company and deal now exists based on previous creation
    # and are linked
    _test()


def test_create_deal_for_contact(
    hubspot_client, first_name, last_name, phone, company_name, unique_id
):
    test_amount = 99.99

    # Assert the deal and company don't already exist
    deal_name = f"{unique_id} test_create_deal_for_contact"
    deal = hubspot_client.find_deal("dealname", deal_name)
    assert not deal

    email = f"{unique_id}@testcreatedealforcontact.com"
    contact = hubspot_client.find_contact("email", email)
    assert not contact

    # Create the contact
    contact_result = hubspot_client.create_contact(
        email=email,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        company=company_name,
    )

    # Create the deal
    deal_result = hubspot_client.create_deal(
        name=deal_name, amount=test_amount, contact_id=contact_result.id
    )

    assert deal_result
    assert deal_result.id

    @retry(stop=stop_after_attempt(7), wait=wait_fixed(2))
    def _test():
        _deal = hubspot_client.find_deal("dealname", deal_name)
        assert _deal

        _company = hubspot_client.find_contact("hs_object_id", contact_result.id)
        assert _company

        _association = hubspot_client.deal_associations(deal_result.id, "contact")
        assert _association
        assert _association[0].to_object_id == int(contact_result.id)

    # Assert the company and deal now exists based on previous creation
    # and are linked
    _test()


def test_find_owner_by_email(hubspot_client):
    owners = next(hubspot_client.find_all_owners())
    oid = owners.results[0].id
    oemail = owners.results[0].email

    owner = hubspot_client.find_owner("email", oemail)
    assert owner
    assert owner.id == oid


def test_find_owner_not_found_returns_none(hubspot_client):
    owner = hubspot_client.find_owner("email", "email@doesnotexist.com")
    assert owner is None


def test_find_owner_by_id(hubspot_client):
    owners = next(hubspot_client.find_all_owners())
    oid = owners.results[0].id
    oemail = owners.results[0].email

    owner = hubspot_client.find_owner("id", oid)
    assert owner
    assert owner.email == oemail


def test_find_owner_without_id_or_email(hubspot_client):
    with pytest.raises(NameError):
        hubspot_client.find_owner("some_id", "some_value")


def test_find_all_tickets_returns_batches(hubspot_client: HubSpotClient):
    @retry(stop=stop_after_attempt(7), wait=wait_fixed(2))
    def _test():
        tickets = hubspot_client.find_all_tickets()

        # Assert that the first batch contains the limit of records
        # for a batch
        initial_batch = next(tickets)
        assert len(initial_batch) == BATCH_LIMITS

        following_batch = next(tickets)

        # Assert that the next batch follows on from the previous
        assert following_batch[0].updated_at > initial_batch[-1].updated_at

    _test()


def test_find_all_tickets_returns_default_properties(hubspot_client: HubSpotClient):
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


def test_find_all_tickets_returns_given_properties(hubspot_client: HubSpotClient):
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


def test_find_all_tickets_returns_after_given_hs_lastmodifieddate(
    hubspot_client: HubSpotClient,
):
    all_tickets = hubspot_client.find_all_tickets()
    filter_value = next(all_tickets)[0].updated_at
    filtered_tickets = hubspot_client.find_all_tickets(
        filter_name="hs_lastmodifieddate",
        filter_value=filter_value,
    )

    # Assert that the first record of the returned filtered list starts
    # after the original returned list
    assert next(filtered_tickets)[0].updated_at > filter_value


def test_find_all_tickets_returns_after_given_hs_object_id(
    hubspot_client: HubSpotClient,
):
    all_tickets = hubspot_client.find_all_tickets()
    filter_value = next(all_tickets)[0].id
    filtered_tickets = hubspot_client.find_all_tickets(
        filter_name="hs_object_id",
        filter_value=filter_value,
    )

    # Assert that the first record of the returned filtered list starts
    # after the original returned list
    assert next(filtered_tickets)[0].id > filter_value


def test_find_all_tickets_returns_for_given_pipeline_id(hubspot_client: HubSpotClient):
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
    filter_value = next(all_events)[-1].created_at
    parameters = dict(created_after=filter_value.timestamp() + 1)
    filtered_events = hubspot_client.find_all_email_events(**parameters)
    # Assert that the first record of the returned filtered list starts
    # after the original returned list
    assert next(filtered_events)[0].created_at > filter_value
