from hs_api import HubSpotClient

client = HubSpotClient()
df = client.find_all_contact_lists()
print(df)