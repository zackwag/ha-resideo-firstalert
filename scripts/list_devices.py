#!/usr/bin/env python3
"""List all devices on a Resideo account with their IDs.

Usage:
    python scripts/list_devices.py <refresh_token>

Requires: pip install pyresideo-firstalert
"""

import asyncio
import sys

import aiohttp
from resideo_firstalert_api import ResideoApiClient


async def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/list_devices.py <refresh_token>")
        sys.exit(1)

    refresh_token = sys.argv[1]

    async with aiohttp.ClientSession() as session:
        client = ResideoApiClient(session, refresh_token)

        print("Fetching devices...\n")
        devices = await client.get_devices()

        if client.refresh_token != refresh_token:
            print(f"NOTE: Refresh token rotated. New token:\n{client.refresh_token}\n")

        print(f"{'#':<4} {'Name':<30} {'Hardware ID':<20} {'Consumer Device ID'}")
        print("-" * 100)

        for idx, device in enumerate(devices, 1):
            name = device.get("name", "Unnamed")
            hw_id = device.get("device_id", "?")
            consumer_id = device.get("consumer_device_id", "?")
            location = device.get("location", "Unknown")
            device_type = device.get("device_type", "?")
            print(f"{idx:<4} {name:<30} {hw_id:<20} {consumer_id}")
            print(f"     Location: {location}  |  Type: {device_type}")
            print()

        if not devices:
            print("No devices found.")


if __name__ == "__main__":
    asyncio.run(main())
