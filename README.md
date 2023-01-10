# hubspot-api


This hubspot api is a handy wrapper on top of the existing [hubspot python api](https://github.com/HubSpot/hubspot-api-python).

More details around the inner workings of that and the wider Hubspot API can be found there.


## Installation

To install the package, run via pip:

```shell
pip install git+https://github.com/mannum/hubspot-api.git@1.2.0
```

Be sure to specify the correct version you want to install.



## Quickstart

### Initialise Hubspot Client

To create a hubspot client object that can then interact with the Hubspot
API, you will first have to create an `access_token` which can be done
via the creation of a [private app](https://developers.hubspot.com/docs/api/private-apps)
in Hubspot.
From there you can create a new client, passing the access token and the
id of the pipeline that you want to interact with as the default.

```python
from hs_api.api.hubspot_api import HubSpotClient

access_token = 'my_access_token'
pipeline_id = 'my_pipeline_id'

client = HubSpotClient(
    access_token=access_token,
    PIPELINE_ID=pipeline_id,
)
```

You can also set the environment variables `HUBSPOT_ACCESS_TOKEN` and
`HUBS_PIPELINE_ID` which will be used as defaults if no access_token or
pipeline_id are passed to the `HubSpotClient`.


More details on how to use the client can be found in the test cases that
demonstrate how the api should work.

## Developing

To develop on this hubspot package, you can simple clone the repo and make
the dev changes you require. From there you can run tests...

```
make test
```

... run linting...

```
make py-format-lint
```

... or everything

```
make all
```
