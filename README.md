# storm-otx
This is an example [Synapse Storm Service](https://synapse.docs.vertex.link/en/latest/synapse/glossary.html#gloss-service) for use with the Alienvault OTX
DNS API.

A blog piece on using this can be found [here.](https://musings.konundrum.org/2021/03/21/synapse-storm-services.html)

# Requirements
* https://github.com/vertexproject/synapse
* https://github.com/AlienVault-OTX/OTX-Python-SDK
* Alientvault OTX API Key.

# Setup
After cloning this repository do the following:

1. Change the password in `cell.yaml`
2. Generate a new guid `python -c 'import synapse.common; print(synapse.common.guid())'` and change the value in `storm.py`
3. Create a data directory for the service to use
4. Copy `cell.yaml` to the root of this new directory
5. Start the service

# Start the service
```
$ cd storm-otx/synmods/otx
$ python -m synapse.servers.cell service.Otx /path/to/store/data
```
