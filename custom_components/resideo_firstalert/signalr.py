"""SignalR client for real-time notifications from Resideo."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Callable
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

SIGNALR_HUB_URL = "https://ds-notification-service.prod.titans.cloud/Hub/"
SIGNALR_NEGOTIATE_URL = f"{SIGNALR_HUB_URL}negotiate?negotiateVersion=1"
RECORD_SEPARATOR = "\x1e"


class SignalRClient:
    """ASP.NET Core SignalR client over WebSocket."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        get_access_token: Callable[[], str | None],
        on_event: Callable[[dict[str, Any]], None],
    ) -> None:
        """Initialize the SignalR client."""
        self._session = session
        self._get_access_token = get_access_token
        self._on_event = on_event
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._task: asyncio.Task | None = None
        self._stopping = False
        self._device_ids: list[str] = []

    async def start(self, device_ids: list[str]) -> None:
        """Start the SignalR connection and subscribe to device events."""
        self._device_ids = device_ids
        self._stopping = False
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        """Stop the SignalR connection."""
        self._stopping = True
        if self._ws and not self._ws.closed:
            await self._ws.close()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _run(self) -> None:
        """Main loop: connect, subscribe, listen, reconnect on failure."""
        while not self._stopping:
            try:
                await self._connect_and_listen()
            except asyncio.CancelledError:
                break
            except Exception:
                if self._stopping:
                    break
                _LOGGER.debug(
                    "SignalR connection lost, reconnecting in 30s", exc_info=True
                )
                await asyncio.sleep(30)

    async def _negotiate(self) -> str:
        """Negotiate a SignalR connection and return the WebSocket URL."""
        token = self._get_access_token()
        headers: dict[str, str] = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        async with self._session.post(
            SIGNALR_NEGOTIATE_URL, headers=headers
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()

        connection_id = data.get("connectionId")
        if not connection_id:
            raise RuntimeError("No connectionId from SignalR negotiate")

        ws_url = SIGNALR_HUB_URL.replace("https://", "wss://").replace(
            "http://", "ws://"
        )
        return f"{ws_url}?id={connection_id}"

    async def _connect_and_listen(self) -> None:
        """Establish WebSocket, handshake, subscribe, and listen."""
        ws_url = await self._negotiate()
        token = self._get_access_token()
        headers: dict[str, str] = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        self._ws = await self._session.ws_connect(ws_url, headers=headers)
        _LOGGER.debug("SignalR WebSocket connected")

        try:
            # Send handshake (JSON protocol, version 1)
            await self._send({"protocol": "json", "version": 1})

            # Wait for handshake response
            handshake_msg = await self._receive_one()
            if handshake_msg is None:
                raise RuntimeError("No handshake response from SignalR")
            if handshake_msg.get("error"):
                raise RuntimeError(
                    f"SignalR handshake error: {handshake_msg['error']}"
                )
            _LOGGER.debug("SignalR handshake complete")

            # Subscribe to device events
            if self._device_ids:
                await self._invoke(
                    "SubscribeSignalRV2", [self._device_ids]
                )
                _LOGGER.debug(
                    "Subscribed to SignalR events for %d devices",
                    len(self._device_ids),
                )

            # Listen for messages
            await self._listen()
        finally:
            if self._ws and not self._ws.closed:
                await self._ws.close()
            self._ws = None

    async def _listen(self) -> None:
        """Listen for incoming messages."""
        async for msg in self._ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                for frame in msg.data.split(RECORD_SEPARATOR):
                    if not frame.strip():
                        continue
                    try:
                        message = json.loads(frame)
                    except json.JSONDecodeError:
                        continue
                    await self._handle_message(message)
            elif msg.type == aiohttp.WSMsgType.PING:
                await self._ws.pong(msg.data)
            elif msg.type in (
                aiohttp.WSMsgType.CLOSE,
                aiohttp.WSMsgType.CLOSING,
                aiohttp.WSMsgType.CLOSED,
                aiohttp.WSMsgType.ERROR,
            ):
                break

    async def _handle_message(self, message: dict[str, Any]) -> None:
        """Handle an incoming SignalR message."""
        msg_type = message.get("type")

        if msg_type == 6:
            # Ping — respond with pong
            await self._send({"type": 6})
        elif msg_type == 1:
            # Invocation (server calling a client method)
            self._on_event(message)
        elif msg_type == 7:
            # Close
            _LOGGER.debug("SignalR server sent close: %s", message)

    async def _send(self, data: dict[str, Any]) -> None:
        """Send a message with the record separator."""
        if self._ws and not self._ws.closed:
            await self._ws.send_str(json.dumps(data) + RECORD_SEPARATOR)

    async def _invoke(self, method: str, args: list[Any]) -> None:
        """Invoke a hub method."""
        await self._send(
            {"type": 1, "target": method, "arguments": args}
        )

    async def _receive_one(self) -> dict[str, Any] | None:
        """Receive a single message (used during handshake)."""
        async for msg in self._ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                for frame in msg.data.split(RECORD_SEPARATOR):
                    if not frame.strip():
                        continue
                    return json.loads(frame)
            elif msg.type in (
                aiohttp.WSMsgType.CLOSE,
                aiohttp.WSMsgType.ERROR,
            ):
                return None
        return None
