import time
from collections.abc import Generator
from datetime import datetime
from typing import Dict, Optional

from hubspot import HubSpot
from hubspot.auth.oauth import ApiException
from hubspot.crm.contacts import (
    Filter,
    FilterGroup,
    PublicGdprDeleteInput,
    PublicObjectSearchRequest,
    SimplePublicObjectInput,
)
from requests.exceptions import HTTPError

from hs_api.settings.settings import HUBSPOT_ACCESS_TOKEN, HUBSPOT_PIPELINE_ID

ASSOCIATION_TYPE_LOOKUP = {
    "contact-company": 1,
    "company-contact": 2,
    "deal-contact": 3,
    "contact-deal": 4,
    "deal-company": 5,
    "company-deal": 6,
}

BATCH_LIMITS = 50
EMAIL_BATCH_LIMIT = 10
RETRY_LIMIT = 3
RETRY_WAIT = 60


def get_association_id(from_object_type, to_object_type):
    lookup = f"{from_object_type}-{to_object_type}"
    return ASSOCIATION_TYPE_LOOKUP.get(lookup)


class HubSpotClient:
    def __init__(
        self, access_token=HUBSPOT_ACCESS_TOKEN, pipeline_id=HUBSPOT_PIPELINE_ID
    ):
        self._access_token = access_token
        self._pipeline_id = pipeline_id
        self._client = self.init_client()

    @property
    def pipeline_id(self):
        if self._pipeline_id is None:
            raise ValueError("pipeline_id cannot be None")
        return self._pipeline_id

    def init_client(self):
        return HubSpot(access_token=self._access_token)

    @property
    def pipeline_stages(self):
        results = self._client.crm.pipelines.pipeline_stages_api.get_all(
            "deals", self.pipeline_id
        ).results
        return sorted(results, key=lambda x: x.display_order)

    @property
    def create_lookup(self):
        return {
            "contact": self._client.crm.contacts.basic_api.create,
            "company": self._client.crm.companies.basic_api.create,
            "deal": self._client.crm.deals.basic_api.create,
            "ticket": self._client.crm.tickets.basic_api.create,
            "email": self._client.crm.objects.emails.basic_api.create,
        }

    @property
    def search_lookup(self):
        return {
            "contact": self._client.crm.contacts.search_api.do_search,
            "company": self._client.crm.companies.search_api.do_search,
            "email": self._client.crm.objects.emails.search_api.do_search,
        }

    @property
    def associations_lookup(self):
        return {
            "contact": self._client.crm.contacts.associations_api,
            "company": self._client.crm.companies.associations_api,
            "deal": self._client.crm.deals.associations_api,
        }

    @property
    def update_lookup(self):
        return {
            "contact": self._client.crm.contacts.basic_api.update,
            "company": self._client.crm.companies.basic_api.update,
            "deal": self._client.crm.deals.basic_api.update,
        }

    def pipeline_details(self, pipeline_id=None, return_all_pipelines=False):
        """
        Returns a list of details of pipelines. Where a pipeline_id is provided,
        that pipeline will be returned. Otherwise, it will default to using
        self.pipeline_id.
        Where return_all_pipelines=True, it will ignore the pipeline filter and
        instead return all pipelines.
        """
        pipeline_id = pipeline_id or self.pipeline_id

        pipelines = []
        for object_type in ["TICKET", "DEAL"]:
            response = self._client.crm.pipelines.pipelines_api.get_all(
                object_type=object_type
            ).results
            for pipeline in response:
                pipeline.object_type = object_type
            pipelines += response

        if not return_all_pipelines:
            pipelines = [x for x in pipelines if x.id == pipeline_id]
        return pipelines

    def _find(self, object_name, property_name, value, sort, limit=20, after=0):
        filter_groups = None
        if property_name and value:
            query = Filter(property_name=property_name, operator="EQ", value=value)
            filter_groups = [FilterGroup(filters=[query])]

        public_object_search_request = PublicObjectSearchRequest(
            limit=limit,
            filter_groups=filter_groups,
            sorts=sort,
            after=after,
        )

        response = self.search_lookup[object_name](
            public_object_search_request=public_object_search_request,
        )
        return response

    def _create(self, object_name, properties):
        try:
            simple_public_object_input = SimplePublicObjectInput(properties=properties)
            api_response = self.create_lookup[object_name](
                simple_public_object_input=simple_public_object_input
            )

            return api_response
        except ApiException as e:
            print(f"Exception when creating {object_name}: {e}\n")

    def _update(self, object_name, object_id, properties):
        try:
            simple_public_object_input = SimplePublicObjectInput(properties=properties)
            api_response = self.update_lookup[object_name](
                object_id, simple_public_object_input=simple_public_object_input
            )

            return api_response
        except ApiException as e:
            print(f"Exception when updating {object_name}: {e}\n")

    def find_contact(self, property_name, value):
        sort = [{"propertyName": "hs_object_id", "direction": "ASCENDING"}]

        response = self._find("contact", property_name, value, sort)
        return response.results

    def find_contact_iter(
        self, property_name: str, value: str, limit: int = 20
    ) -> Generator[Dict, None, None]:
        """
        Searches for a contact in Hubspot and returns results as a generator

        :param property_name: The field name from Hubspot
        :param value: The value to search in the field property_name
        :param limit: The number of results to return per iteration
        :return: Dictionary of results
        """
        sort = [{"propertyName": "hs_object_id", "direction": "ASCENDING"}]
        after = 0

        while True:
            response = self._find(
                "contact", property_name, value, sort, limit=limit, after=after
            )
            if not response.results:
                break

            yield response.results

            if not response.paging:
                break
            after = response.paging.next.after

    def find_company(self, property_name, value):
        sort = [{"propertyName": "hs_lastmodifieddate", "direction": "DESCENDING"}]

        response = self._find("company", property_name, value, sort)
        return response.results

    def find_company_iter(
        self, property_name: str, value: str, limit: int = 20
    ) -> Generator[Dict, None, None]:
        """
        Searches for a company in Hubspot and returns results as a generator

        :param property_name: The field name from Hubspot
        :param value: The value to search in the field property_name
        :param limit: The number of results to return per iteration
        :return: Dictionary of results
        """
        sort = [{"propertyName": "hs_lastmodifieddate", "direction": "DESCENDING"}]
        after = 0

        while True:
            response = self._find(
                "company", property_name, value, sort, limit=limit, after=after
            )
            if not response.results:
                break

            yield response.results

            if not response.paging:
                break
            after = response.paging.next.after

    def find_deal(self, property_name, value):
        pipeline_filter = Filter(
            property_name="pipeline", operator="EQ", value=self.pipeline_id
        )
        query = Filter(property_name=property_name, operator="EQ", value=value)
        filter_groups = [FilterGroup(filters=[pipeline_filter, query])]

        public_object_search_request = PublicObjectSearchRequest(
            limit=20,
            filter_groups=filter_groups,
            sorts=None,
        )

        response = self._client.crm.deals.search_api.do_search(
            public_object_search_request=public_object_search_request,
        )
        return response.results

    def _find_owner_by_email(self, email):
        response = self._client.crm.owners.owners_api.get_page_with_http_info(
            email=email
        )
        result = None
        # Returns the first result found if any as emails are unique
        if response[0].results:
            result = response[0].results[0]
        return result

    def _find_owner_by_id(self, owner_id):
        response = self._client.crm.owners.owners_api.get_by_id(owner_id=owner_id)
        return response

    def find_all_owners(self):
        after = None
        while True:
            response = self._client.crm.owners.owners_api.get_page(after=after)
            yield response

            if not response.paging:
                break
            after = response.paging.next.after

    def find_owner(self, property_name, value):
        if property_name not in ("id", "email"):
            raise NameError(
                f"'{property_name}' is not valid for property_name. "
                f"Must be one of 'id' or 'email'."
            )
        if property_name == "id":
            return self._find_owner_by_id(owner_id=value)
        if property_name == "email":
            return self._find_owner_by_email(email=value)

    def find_all_email_events(
        self, filter_name=None, filter_value=None, limit=EMAIL_BATCH_LIMIT, **parameters
    ):
        """
        Finds and returns all email events, using the filter name and value as the
        high watermark for the events to return. If None are provided, it
        returns everything, defaulting to using the 'created' date and
        0 epoch.
        This iterates over batches, using the previous batch as the new high
        watermark for the next batch to be returned until there are no more
        records or batches to return.
        """
        sort = [{"propertyName": "hs_lastmodifieddate", "direction": "DESCENDING"}]
        retry = 0
        after = None
        while True:
            try:
                if filter_name:
                    parameters[filter_name] = filter_value

                resp = self._find(
                    "email",
                    property_name=filter_name,
                    value=filter_value,
                    limit=limit,
                    after=after,
                    sort=sort,
                )
                if not resp.results:
                    break

                yield resp.results

                if not resp.paging:
                    break
                after = resp.paging.next.after

            except HTTPError as e:
                status_code = e.response.status_code
                if retry >= RETRY_LIMIT:
                    raise e
                if status_code in (504,):
                    retry += 1
                    time.sleep(RETRY_WAIT)
                else:
                    raise e

    def find_all_tickets(
        self, filter_name=None, filter_value=None, properties=None, pipeline_id=None
    ):
        """
        Finds and returns all tickets, using the filter name and value as the
        high watermark for the tickets to return. If None are provided, it
        returns everything, defaulting to using the 'hs_lastmodifieddate' and
        0 epoch.
        This iterates over batches, using the previous batch as the new high
        watermark for the next batch to be returned until there are no more
        records or batches to return.
        Also returns the default properties if none are given, otherwise it will
        return the given properties, where they exist as properties.
        If a pipeline_id is given, this will be used to filter tickets specific to
        that pipeline, otherwise it returns tickets from all pipelines.
        """
        if filter_name is None and filter_value is None:
            filter_name = "hs_lastmodifieddate"

        after = 0
        while after is not None:
            # If the filter is on the modified date, we want to convert the given
            # date to an epoch
            formatted_filter_value = filter_value
            if filter_name == "hs_lastmodifieddate":
                formatted_filter_value = convert_date_to_epoch(filter_value)

            query = Filter(
                property_name=filter_name, operator="GT", value=formatted_filter_value
            )

            filters = [query]

            if pipeline_id:
                pipeline_query = Filter(
                    property_name="hs_pipeline", operator="EQ", value=pipeline_id
                )
                filters.append(pipeline_query)

            filter_groups = [FilterGroup(filters=filters)]

            public_object_search_request = PublicObjectSearchRequest(
                limit=BATCH_LIMITS,
                filter_groups=filter_groups,
                sorts=[{"propertyName": filter_name, "direction": "ASCENDING"}],
                properties=properties,
                after=after,
            )
            response = self._client.crm.tickets.search_api.do_search(
                public_object_search_request=public_object_search_request
            )
            yield response.results

            # Update after to page onto next batch if there is next otherwise break as
            # there are no more batches to iterate over.
            if response.paging:
                after = response.paging.next.after
            else:
                after = None

    def find_ticket(self, ticket_id):
        return self._client.crm.tickets.basic_api.get_by_id(ticket_id)

    def find_all_deals(
        self,
        filter_name=None,
        filter_value=None,
        properties=None,
        pipeline_id=None,
        properties_with_history=None,
        archived_only=False,
    ):
        """
        Finds and returns all deals, using the filter name and value as the
        high watermark for the deals to return. If None are provided, it
        returns everything, defaulting to using the 'hs_lastmodifieddate' and
        0 epoch.
        This iterates over batches, using the previous batch as the new high
        watermark for the next batch to be returned until there are no more
        records or batches to return.
        Also returns the default properties if none are given, otherwise it will
        return the given properties, where they exist as properties.
        If a pipeline_id is given, this will be used to filter deals specific to
        that pipeline, otherwise it returns deals from all pipelines.
        """
        if filter_name is None and filter_value is None:
            filter_name = "id"
            filter_value = "0"

        after = 0
        while after is not None:
            if after == 0:
                after = None

            response = self._client.crm.deals.basic_api.get_page(
                limit=BATCH_LIMITS,
                properties=properties,
                properties_with_history=properties_with_history,
                associations=["contacts", "companies"],
                after=after,
                archived=archived_only,
            )

            results = response.results

            # Filter records on filter name/value and pipeline id if provided
            results = [
                x
                for x in results
                if getattr(x, filter_name) > filter_value
                and (x.properties.get("pipeline") == pipeline_id or pipeline_id is None)
            ]

            if results:
                yield results

            # Update after to page onto next batch if there is next otherwise break as
            # there are no more batches to iterate over.
            if not response.paging:
                break
            after = response.paging.next.after

    def create_contact(self, email, first_name, last_name, **properties):
        properties = dict(
            email=email, firstname=first_name, lastname=last_name, **properties
        )

        response = self._create("contact", properties)
        return response

    def create_company(self, name, domain=None, **properties):
        properties = dict(name=name, domain=domain, **properties)

        response = self._create("company", properties)
        return response

    def create_deal(
        self, name, stage=None, company_id=None, contact_id=None, **properties
    ):
        """
        Creates a new deal at the given stage or at the landing stage
        if not provided.
        If a company_id or contact_id are given, it will create the association
        between the deal and company/contact.
        """
        stage = stage or self.pipeline_stages[0].id
        properties = dict(dealname=name, dealstage=stage, **properties)

        response = self._create("deal", properties)

        # Create association to company if given
        if company_id or contact_id is not None:
            time.sleep(10)
        if company_id is not None:
            self.create_association(
                from_object_type="deal",
                from_object_id=response.id,
                to_object_type="company",
                to_object_id=company_id,
            )

        # Create association to contact if given
        if contact_id is not None:
            self.create_association(
                from_object_type="deal",
                from_object_id=response.id,
                to_object_type="contact",
                to_object_id=contact_id,
            )
        return response

    def create_ticket(self, subject, **properties):
        properties = dict(subject=subject, **properties)
        response = self._create("ticket", properties)
        return response

    def create_email(
        self,
        hs_timestamp: Optional[datetime] = None,
        hs_email_direction: Optional[str] = "EMAIL",
        **properties,
    ):
        """
        See documentation at https://developers.hubspot.com/docs/api/crm/email

        :param hs_timestamp: This field marks the email's time of creation and determines where the email sits on the
        record timeline. You can use either a Unix timestamp in milliseconds or UTC format. If not provided, then the
        current time is used.
        :param hs_email_direction: The direction the email was sent in. Possible values include:

        EMAIL: the email was sent from the CRM or sent and logged to the CRM with the BCC address.
        INCOMING_EMAIL: the email was a reply to a logged outgoing email.

        FORWARDED_EMAIL: the email was forwarded to the CRM.
        :param properties: Dictionary of properties as documented on hubspot
        :return:
        """
        if not hs_timestamp:
            hs_timestamp = int(datetime.now().timestamp())
        else:
            hs_timestamp = int(hs_timestamp.timestamp())

        properties = dict(
            hs_timestamp=hs_timestamp,
            hs_email_direction=hs_email_direction,
            **properties,
        )
        response = self._create("email", properties)
        return response

    def delete_contact(self, value, property_name=None):
        try:
            public_gdpr_delete_input = PublicGdprDeleteInput(
                object_id=value, id_property=property_name
            )
            api_response = self._client.crm.contacts.gdpr_api.purge(
                public_gdpr_delete_input=public_gdpr_delete_input
            )

            return api_response
        except ApiException as e:
            print(f"Exception when deleting contact: {e}\n")

    def delete_company(self, company_id):
        try:
            api_response = self._client.crm.companies.basic_api.archive(company_id)
            return api_response
        except ApiException as e:
            print(f"Exception when deleting company: {e}\n")

    def delete_deal(self, deal_id):
        try:
            api_response = self._client.crm.deals.basic_api.archive(deal_id)
            return api_response
        except ApiException as e:
            print(f"Exception when deleting deal: {e}\n")

    def delete_ticket(self, ticket_id):
        try:
            api_response = self._client.crm.tickets.basic_api.archive(ticket_id)
            return api_response
        except ApiException as e:
            print(f"Exception when deleting ticket: {e}\n")

    def delete_email(self, email_id):
        try:
            api_response = self._client.crm.objects.emails.basic_api.archive(email_id)
            return api_response
        except ApiException as e:
            print(f"Exception when deleting email: {e}\n")

    def update_company(self, object_id, **properties):
        response = self._update("company", object_id, properties)
        return response

    def update_contact(self, object_id, **properties):
        response = self._update("contact", object_id, properties)
        return response

    def company_associations(self, company_id, associated_with_type):
        result = self.associations_lookup["company"].get_all(
            company_id=company_id, to_object_type=associated_with_type
        )
        return result.results

    def contact_associations(self, contact_id, associated_with_type):
        result = self.associations_lookup["contact"].get_all(
            contact_id=contact_id, to_object_type=associated_with_type
        )
        return result.results

    def deal_associations(self, deal_id, associated_with_type):
        result = self.associations_lookup["deal"].get_all(
            deal_id=deal_id, to_object_type=associated_with_type
        )
        return result.results

    def create_association(
        self, from_object_type, from_object_id, to_object_type, to_object_id
    ):
        result = self.associations_lookup[from_object_type].create(
            from_object_id,
            to_object_type,
            to_object_id,
            [],
        )
        return result

    def create_contact_and_company(
        self, email, first_name, last_name, company, **properties
    ):
        """
        Creates the contact and associated company. If the company is auto generated from
        the domain, it will update that company name if its empty. Otherwise, it will create
        a new company to associate to the contact.
        """
        output = dict()
        output["contact"] = self.create_contact(
            email, first_name, last_name, company=company, **properties
        )
        new_contact_id = output["contact"].id

        # Check if company has been created and assigned to contact already
        time.sleep(10)
        result = self.contact_associations(new_contact_id, "company")
        if result:
            company_id = result[0].id
            # Update company name if null
            company_result = self.find_company("hs_object_id", company_id)[0]
            if company_result.properties["name"] is None:
                output["company"] = self.update_company(company_id, name=company)

        else:
            output["company"] = self.create_company(name=company)
            self.create_association(
                from_object_type="contact",
                from_object_id=output["contact"].id,
                to_object_type="company",
                to_object_id=output["company"].id,
            )
        return output


def convert_date_to_epoch(date):
    if date:
        start_millisecond_value = (int(date.timestamp()) * 1000) + int(
            date.microsecond / 1000
        )
    else:
        start_millisecond_value = 0

    return start_millisecond_value
