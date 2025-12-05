# GeminiCLI extension for NetBox

A Gemini CLI extention to interact with NetBox.

## Setup

Install the extention using gemini:

```
gemini extensions install https://github.com/stiltzkin10/netbox-geminicli-extension
```

Export the Netbox URL and Netbox API key and start gemini:

```
export NETBOX_URL=http://localhost:8000
export NETBOX_API_KEY=API_TOKEN_HERE
gemini
```

Have fun!

## Example prompts

* List all the devices in site dc01
* Add all interfaces from spine01.dc01 to Netbox
* Gather facts from leaf01.dc01 and add a new Netbox device. Get role and site from the hostname.

