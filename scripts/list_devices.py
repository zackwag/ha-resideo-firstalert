#!/usr/bin/env python3
"""List all devices on a Resideo account with their IDs.

Usage:
    python scripts/list_devices.py <refresh_token>
"""

import asyncio
import sys

import aiohttp

OAUTH_CLIENT_ID = "SRmiA7CaYi1JgivDZdzzoZu4X5VBogGt"
OAUTH_TOKEN_URL = "https://login.resideo.com/oauth/token"
API_BASE_URL = "https://api.resideo.com"
API_ACCOUNTS_ENDPOINT = "/ris-public-api/api/v1/accounts"


async def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/list_devices.py <refresh_token>")
        sys.exit(1)

    refresh_token = sys.argv[1]

    async with aiohttp.ClientSession() as session:
        print("Authenticating...")
        async with session.post(
            OAUTH_TOKEN_URL,
            json={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": OAUTH_CLIENT_ID,
            },
        ) as resp:
            if resp.status != 200:
                text = await resp.text()
                print(f"FATAL: Token refresh failed ({resp.status}): {text}")
                sys.exit(1)
            data = await resp.json()
            token = data["access_token"]
            new_rt = data.get("refresh_token")
            if new_rt and new_rt != refresh_token:
                print(f"NOTE: Refresh token rotated. New token:\n{new_rt}\n")

        print("Fetching devices...\n")
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        async with session.get(
            f"{API_BASE_URL}{API_ACCOUNTS_ENDPOINT}", headers=headers
        ) as resp:
            if resp.status != 200:
                text = await resp.text()
                print(f"FATAL: Accounts request failed ({resp.status}): {text}")
                sys.exit(1)
            account_data = await resp.json()

        print(f"{'#':<4} {'Name':<30} {'Hardware ID':<20} {'Consumer Device ID'}")
        print("-" * 100)

        idx = 0
        for consumer_user in account_data.get("data", {}).get("consumerUsers", []):
            for location in consumer_user.get("consumerAccount", {}).get("locations", []):
                location_name = location.get("name", "Unknown")
                for consumer_device in location.get("consumerDevices", []):
                    device = consumer_device.get("device", {})
                    idx += 1
                    name = consumer_device.get("name", "Unnamed")
                    hw_id = device.get("deviceId", "?")
                    consumer_id = consumer_device.get("id", "?")
                    device_type = device.get("globalDeviceType", "?")
                    print(f"{idx:<4} {name:<30} {hw_id:<20} {consumer_id}")
                    print(f"     Location: {location_name}  |  Type: {device_type}")
                    print()

        if idx == 0:
            print("No devices found.")


if __name__ == "__main__":
    asyncio.run(main())
