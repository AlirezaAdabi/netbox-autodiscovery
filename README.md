# NetBox AutoDiscovery Plugin
===========================

A NetBox plugin to automatically **discover network assets** such as hosts, IPs, VLANs, and Cisco switch details via range scanning or SNMP.

## Supports:

-   **Range scans** (CIDR-based host discovery with ICMP + reverse DNS).

-   **Cisco scans** (via SNMP to discover devices, interfaces, VLANs, and assignments).

-   **Fake mode** for testing without hardware.

-   Tracking of **scan runs**, logs, and findings.

-   Bulk delete for scanners and runs.

* * * * *

## 🔧 Requirements
---------------

-   **NetBox**: v4.4+ (tested with NetBox Docker)

-   **Python**: 3.10+

-   **PostgreSQL**: 14+

-   **Dependencies**: Installed automatically via `plugin_requirements.txt` (includes `pysnmp` and `pyasn1`)

* * * * *

## 📦 Installation
---------------

### 1\. Clone plugin

Inside your NetBox Docker setup:

`git clone https://github.com/AlirezaAdabi/netbox-autodiscovery.git ./plugins/netbox-autodiscovery`

### 2\. Enable plugin in NetBox config

Edit `configuration/plugins.py` and add:

`PLUGINS = [
    "netbox_autodiscovery",
]`

### 3\. Add Dockerfile-Plugin

`FROM netboxcommunity/netbox:latest

# Install plugin requirements
COPY ./plugins/netbox-autodiscovery/plugin_requirements.txt /opt/netbox/netbox_autodiscovery/
RUN /usr/local/bin/uv pip install -r /opt/netbox/netbox_autodiscovery/plugin_requirements.txt

# Install your local plugin source (editable-style inside container)
COPY ./plugins/netbox-autodiscovery /opt/netbox/netbox_autodiscovery
RUN /usr/local/bin/uv pip install -e /opt/netbox/netbox_autodiscovery


# If your plugin ships static files, collect them:
# RUN DEBUG="true" SECRET_KEY="dummydummydummydummydummydummydummydummydummy" \
#     /opt/netbox/venv/bin/python /opt/netbox/netbox/manage.py collectstatic --no-input
`

### 4\. Add Dockerfile-Plugins to Dockerfile
   ` build:
      context: .
      dockerfile: Dockerfile-Plugins`


### 5\. Rebuild NetBox Docker

`docker compose build
docker compose up -d`

### 6\. Run migrations

`
docker compose exec --user root netbox python manage.py makemigrations netbox_autodiscovery
docker compose exec netbox python manage.py migrate netbox_autodiscovery
`

* * * * *

## 🚀 Usage
--------

### Create a Scanner

1.  Go to **Plugins → Auto Discovery → Scanners**.

2.  Click **Add Scanner**.

3.  Choose type:

    -   **Range** → enter CIDR (e.g. `192.168.1.0/24`).

    -   **Cisco** → enter hostname/IP and SNMP community string.

    -   Optionally enable **Fake Mode** for testing.

### Run a Scanner

-   From a scanner's detail page, click **Run Scanner**.

-   A new **Scan Run** will be created and processed in the background (via RQ).

### View Scan Results

-   Go to **Plugins → Auto Discovery → Runs**.

-   Select a run to view:

    -   **Status** (pending, running, success, failed)

    -   **Stats** (counts of interfaces, VLANs, IPs)

    -   **Log** (progress messages)

    -   **Findings** (IPs discovered, devices updated, VLANs created, etc.)

### Bulk Delete

-   Both **Scanners** and **Runs** support multi-select → **Delete selected**.

* * * * *

## 🧪 Fake Mode Examples
---------------------

-   **Range scan**: Will randomly mark 5 hosts alive and add them to NetBox IPAM with fake hostnames.

-   **Cisco scan**: Creates a fake Cisco switch with interfaces, VLANs, and IPs in NetBox DCIM/IPAM.

* * * * *

## 📚 Roadmap
----------

-   Scheduling support (e.g. nightly scans).

-   Better findings presentation (charts, diffs).

-   Additional vendor-specific discovery (Juniper, Arista).

* * * * *

## 🤝 Contributing
---------------

Pull requests and feature requests welcome!

* * * * *
