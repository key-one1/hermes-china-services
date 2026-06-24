#!/usr/bin/env python3
"""
MCP Server for Amap (高德地图) — exposes all amap.py tools via Model Context Protocol.

Compatible with: Claude Code, Codex CLI, Cursor, Hermes Agent, and any MCP client.
Transport: stdio (standard MCP transport — no network config needed).

Setup:
    pip install -r requirements.txt
    export AMAP_KEY=your_key_here

Usage in Claude Code / Codex:
    Add to your MCP config:
    {
      "mcpServers": {
        "amap": {
          "command": "python3",
          "args": ["path/to/mcp-server/server.py"],
          "env": {"AMAP_KEY": "your_key_here"}
        }
      }
    }
"""

import json
import os
import subprocess
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# ── Config ──────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
AMAP_SCRIPT = SCRIPT_DIR.parent / "skills" / "amap" / "scripts" / "amap.py"

mcp = FastMCP(
    "amap",
    instructions="""
Amap (高德地图) MCP Server — Chinese location services.

Available tools:
- amap_nearby: Search POIs near a coordinate
- amap_text_search: Search POIs by keyword (optionally scoped to a city)
- amap_geocode: Convert address to coordinates
- amap_regeo: Convert coordinates to address
- amap_route: Plan driving/walking/transit routes
- amap_weather: Get current weather or 4-day forecast

Requires AMAP_KEY env var (free: https://console.amap.com/dev/key/app).
""",
)


def _get_key():
    key = os.environ.get("AMAP_KEY", "")
    if not key:
        raise RuntimeError("AMAP_KEY not set. Get a free key at https://console.amap.com/dev/key/app")
    return key


def _run_amap(subcommand: str, **kwargs) -> dict:
    """Run amap.py with --json and return parsed result."""
    key = _get_key()
    cmd = [
        sys.executable, str(AMAP_SCRIPT),
        "--key", key,
        "--json",
        subcommand,
    ]
    for k, v in kwargs.items():
        if v is None:
            continue
        flag = f"--{k.replace('_', '-')}"
        if isinstance(v, bool):
            if v:
                cmd.append(flag)
        else:
            cmd.extend([flag, str(v)])

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"error": "parse_error", "stdout": result.stdout[:500], "stderr": result.stderr[:500]}


# ── Tools ───────────────────────────────────────────────

@mcp.tool()
def amap_nearby(
    lng: float,
    lat: float,
    radius: int = 1500,
    keywords: str = "",
    types: str = "",
    extensions: str = "base",
    offset: int = 10,
) -> dict:
    """Search POIs (restaurants, shops, parking, hospitals, etc.) near a coordinate.

    Args:
        lng: Longitude (GCJ-02, same as GPS for practical purposes)
        lat: Latitude
        radius: Search radius in meters (500-50000, default: 1500)
        keywords: Search keywords, supports | for OR (e.g. "咖啡|奶茶")
        types: POI category code — use "050000" for restaurants, "090100" for hospitals,
               "150700" for parking, "150800" for gas stations, "060300" for supermarkets.
               See references/poi-types.md for full list.
        extensions: "base" for basic info, "all" for rating/phone/photos
        offset: Results per page (max 25, default 10)
    """
    return _run_amap("nearby", lng=lng, lat=lat, radius=radius,
                      keywords=keywords, types=types,
                      extensions=extensions, offset=offset)


@mcp.tool()
def amap_text_search(
    keywords: str,
    city: str = "",
    citylimit: bool = False,
    types: str = "",
    offset: int = 10,
) -> dict:
    """Search POIs by keyword across a city or nationwide.

    Use this instead of amap_nearby when you know what you're looking for
    (e.g. "北京大学") but don't have coordinates. Always scope with city
    when the intent is local.

    Args:
        keywords: Search keywords (required)
        city: City name or adcode to scope search (e.g. "北京", "杭州")
        citylimit: If true, only return results within the specified city
        types: POI category code (optional filter)
        offset: Results per page (default: 10)
    """
    return _run_amap("text", keywords=keywords, city=city,
                      citylimit=citylimit, types=types, offset=offset)


@mcp.tool()
def amap_geocode(address: str) -> dict:
    """Convert a Chinese address to coordinates (lng, lat).

    Args:
        address: Chinese address string (e.g. "北京市朝阳区望京SOHO", "杭州西湖")
    """
    return _run_amap("geocode", address=address)


@mcp.tool()
def amap_regeo(lng: float, lat: float, radius: int = 1000) -> dict:
    """Convert coordinates to a human-readable Chinese address.

    Useful for Telegram location pins, GPS coordinates, or any raw lng/lat.

    Args:
        lng: Longitude
        lat: Latitude
        radius: Radius in meters for nearby POI context (default: 1000)
    """
    return _run_amap("regeo", lng=lng, lat=lat, radius=radius)


@mcp.tool()
def amap_route(
    origin: str,
    destination: str,
    mode: str = "transit",
    city: str = "",
) -> dict:
    """Plan a route between two points (addresses or coordinates).

    Args:
        origin: Starting point — address (e.g. "天安门广场") or "lng,lat"
        destination: Ending point — address or "lng,lat"
        mode: "driving", "walking", "transit", or "bicycling" (default: "transit")
        city: City name for transit routing (required for transit mode)
    """
    return _run_amap("route", from_=origin, to=destination, mode=mode, city=city)


@mcp.tool()
def amap_weather(city: str, extensions: str = "all") -> dict:
    """Get weather for a Chinese city.

    Args:
        city: City name (e.g. "北京", "杭州", "深圳") or 6-digit adcode (e.g. "110000")
        extensions: "base" for current weather only, "all" for 4-day forecast (default)
    """
    return _run_amap("weather", city=city, extensions=extensions)


# ── Entry Point ─────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="stdio")
