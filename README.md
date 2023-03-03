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
    pipeline_id=pipeline_id,
)
```

You can also set the environment variables `HUBSPOT_ACCESS_TOKEN` and
`HUBS_PIPELINE_ID` which will be used as defaults if no access_token or
pipeline_id are passed to the `HubSpotClient`. This can be done by copying
the .env.template file from `hs_api\.env.template` into the root of the 
project and renaming it to .env. 


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

## Releasing

In order to release your changes, you will create a PR for your branch as
normal, which will kick off the github actions to run the linting and tests.

Be aware that a couple of the tests can be flakey due to the delay in the
asynchronous way hubspot returns results and actually applies them to the
underlying data. There are delays in place to account for this but there can
be cases where a test fails because a record appears to have not been created.
This probably needs reworking, but feel free to re-run the tests.

When releasing a change, you will have to update the `setup.py` file with the
new version number so that the relevant library imports can get the right version.

Once the PR is approved and tests pass, you can merge back into master.

From here - in Github - you can create a new release, which you can find on the
right hand side of the repo page under the _About_ section.

Click on _Draft a new release_ and create a new tag for the version number you used
in the `setup.py` of the merged branch and give it a title and description
of the change. This doesn't have to be too formal as this is only internal
use at the moment.
Now you can click _Publish release_ and this will make it available as a
library.

Be sure to update the relevant dependant projects to pull this new version, i.e.

```
pip install git+https://github.com/mannum/hubspot-api.git@9.9.0
```
