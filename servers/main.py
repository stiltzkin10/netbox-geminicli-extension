#!/usr/bin/env python3

import logging
import os

import pynetbox
from mcp.server.fastmcp import FastMCP
from toon_format import encode

logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("netbox-geminicli-extension")


NETBOX_URL = os.getenv("NETBOX_URL")
NETBOX_API_KEY = os.getenv("NETBOX_API_KEY")

if not NETBOX_URL or not NETBOX_API_KEY:
    raise ValueError("NETBOX_URL and NETBOX_API_KEY must be set")

nb = pynetbox.api(NETBOX_URL, token=NETBOX_API_KEY)


@mcp.tool()
async def get_all_sites() -> dict:
    """Return a list of all sites."""
    sites = nb.dcim.sites.all()
    return encode(sites)


@mcp.tool()
async def get_device_by_site(site: str) -> str:
    """Return a TOON formatted list of device in a specific site."""

    try:
        devices = nb.dcim.devices.filter(site=site)

        device_list = []
        for device in devices:
            device_list.append(dict(device))
        return encode(device_list)
    except pynetbox.RequestError as e:
        raise Exception(e)


@mcp.tool()
async def get_interfaces_by_device(device_name: str) -> str:
    """Return a TOON formatted list of interfaces for a specific device."""

    try:
        interfaces = nb.dcim.interfaces.filter(device=device_name)

        interface_list = []
        for interface in interfaces:
            interface_list.append(dict(interface))
        return encode(interface_list)
    except pynetbox.RequestError as e:
        raise Exception(e)


@mcp.tool()
async def bulk_create_interfaces(
    device_name: str,
    interfaces: list[dict],
) -> dict:
    """Bulk create new interfaces in Netbox.

    Args:
        device_name: The name of the device to add the interfaces to
        interfaces: A list of interfaces to create

    Returns:
        A message indicating that all interfaces were created successfully.

    Interface list example:

    ```
    [
        {
            "device_name": "router1",
            "name": "Ethernet1",
            "type": "10gbase-x-sfpp",
            "description": "Customer port 1",
            "enabled": true,
        },
        {
            "device_name": "router1",
            "name": "Ethernet2",
            "type": "10gbase-x-sfpp",
            "description": "Customer port 2",
            "enabled": true,
        },
    ]
    ```

    Returns:
        A TOON formatted representation of the created interfaces.
    """

    try:
        for interface in interfaces:
            await create_interface(
                device_name,
                interface["name"],
                interface["type"],
                interface.get("description", ""),
                interface["enabled"],
            )
    except pynetbox.RequestError as e:
        raise Exception(f"Failed to create interface: {e}")

    return "All interfaces created successfully"


@mcp.tool()
async def create_interface(
    device_name: str,
    name: str,
    type: str,
    description: str = None,
    enabled: bool = True,
) -> dict:
    """Create a new interface in Netbox for a specific device.

    Args:
        device_name: The name of the device to add the interface to
        name: The name of the interface (e.g., "eth0", "GigabitEthernet0/1")
        type: The type of interface (e.g., "virtual", "1000base-t", "10gbase-x-sfpp", "bridge")
        description: Optional description for the interface
        enabled: Whether the interface is enabled (default: True)

    Returns:
        A TOON formatted representation of the created interface.
    """
    try:
        device = nb.dcim.devices.get(name=device_name)
        if not device:
            raise Exception(f"Device '{device_name}' not found.")

        interface_data = {
            "device": device.id,
            "name": name,
            "type": type,
            "enabled": enabled,
        }

        if description:
            interface_data["description"] = description

        interface = nb.dcim.interfaces.create(**interface_data)

        # Return the interface data with the Netbox ID
        interface_data["netbox_id"] = interface.id
        interface_data["device"] = device_name
        return encode(interface_data)

    except pynetbox.RequestError as e:
        raise Exception(f"Failed to create interface: {e}")


@mcp.tool()
async def create_device(
    name: str,
    device_type: str,
    site: str,
    device_role: str,
    status: str = "active",
    serial: str = None,
    asset_tag: str = None,
    description: str = None,
) -> dict:
    """Create a new device in Netbox.

    Args:
        name: The name of the device
        device_type: The device type (model/slug, e.g., "cisco-asr-1001-x")
        site: The site name or slug where the device is located
        device_role: The device role (slug or name, e.g., "router", "switch", "firewall")
        status: The device status (default: "active"). Options: "offline", "active", "planned", "staged", "failed", "inventory", "decommissioning"
        serial: Optional serial number of the device
        asset_tag: Optional asset tag for the device
        description: Optional description for the device

    Returns:
        A TOON formatted representation of the created device.
    """
    try:
        # Look up site by name or slug
        site_obj = nb.dcim.sites.get(name=site)
        if not site_obj:
            site_obj = nb.dcim.sites.get(slug=site)
        if not site_obj:
            raise Exception(f"Site '{site}' not found.")

        # Look up device type by model or slug
        device_type_obj = nb.dcim.device_types.get(model=device_type.lower())
        if not device_type_obj:
            device_type_obj = nb.dcim.device_types.get(slug=device_type.lower())
        if not device_type_obj:
            raise Exception(f"Device type '{device_type.lower()}' not found.")

        # Look up device role by name or slug
        role_obj = nb.dcim.device_roles.get(name=device_role)
        if not role_obj:
            role_obj = nb.dcim.device_roles.get(slug=device_role)
        if not role_obj:
            raise Exception(f"Device role '{device_role}' not found.")

        device_data = {
            "name": name,
            "device_type": device_type_obj.id,
            "site": site_obj.id,
            "role": role_obj.id,
            "status": status,
        }

        if serial:
            device_data["serial"] = serial
        if asset_tag:
            device_data["asset_tag"] = asset_tag
        if description:
            device_data["description"] = description

        device = nb.dcim.devices.create(**device_data)

        # Return the device data with the Netbox ID
        device_data["netbox_id"] = device.id
        return encode(device_data)

    except pynetbox.RequestError as e:
        raise Exception(f"Failed to create device: {e}")


if __name__ == "__main__":
    logger.info("Starting the NETBOX GeminiCLI Extension…")
    mcp.run()
