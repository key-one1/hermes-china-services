---
name: amap
description: "Use when searching for nearby POIs, geocoding addresses, planning routes, or querying weather via 高德地图 (Amap) Web API. Requires free API key from 高德开放平台. Covers place search, reverse geocode, directions (driving/walking/transit), and weather."
version: 1.0.0
author: key-one1
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [china-services, location, maps, amap, 高德, geocode, routing, weather, nearby, POI]
    related_skills: [find-nearby, web-search]
prerequisites:
  env_vars: [AMAP_KEY]
---

# 高德地图 (Amap) — Chinese Location Services via Hermes

## Overview

Search nearby places, geocode addresses, plan routes, and query weather using 高德地图 Web API. Covers the Chinese geographic domain with far richer POI data than OpenStreetMap in mainland China. Free tier: 5000 calls/day per API.

## Setup

```bash
# 1. Get a free API key at https://console.amap.com/dev/key/app
#    → "Web服务" type, no binding needed for personal use
#    → Free tier: 5000 calls/day for most APIs

# 2. Set the key
export AMAP_KEY="your_key_here"
# Or add to ~/.hermes/.env (preferred):
echo 'AMAP_KEY=your_key_here' >> ~/.hermes/.env
```

## When to Use

- "附近有什么好吃的" / "find restaurants near me"
- "查一下这个地址的坐标" / geocode an address
- "从天安门到三里屯怎么走" / route planning (driving/walking/transit)
- "北京今天天气" / weather query
- "搜索附近的加油站/停车场/医院" / POI search by type
- Any location question in mainland China (Amap has far denser POI data than OSM)

## API Reference

All endpoints use `https://restapi.amap.com/v3/` and require `?key=$AMAP_KEY`.

### Place Search — `place/around`

Search POIs near a coordinate point.

```bash
curl -s "https://restapi.amap.com/v3/place/around?key=$AMAP_KEY&location=116.397428,39.90923&radius=1000&keywords=咖啡&offset=10&output=json"
```

| Param | Required | Description |
|-------|----------|-------------|
| `location` | yes | `lng,lat` (Amap uses GCJ-02, same as GPS for practical purposes) |
| `radius` | no | Meters, default 3000, max 50000 |
| `keywords` | no | Search keywords, supports `\|` for OR (e.g. `咖啡\|奶茶`) |
| `types` | no | POI category code (see references/poi-types.md) |
| `offset` | no | Page size, default 10, max 25 |
| `page` | no | Page number, starts at 1 |
| `extensions` | no | `base` (basic) or `all` (with photos/rating/phone) |

Response: `{"status":"1","pois":[{"name":"星巴克","location":"116.398,39.910","address":"...","distance":"250",...}]}`

### Text Search — `place/text`

Search POIs by keyword, optionally scoped to a city.

```bash
curl -s "https://restapi.amap.com/v3/place/text?key=$AMAP_KEY&keywords=北京大学&city=北京&citylimit=true&offset=5&output=json"
```

### Geocode — `geocode/geo`

Convert address → coordinates.

```bash
curl -s "https://restapi.amap.com/v3/geocode/geo?key=$AMAP_KEY&address=北京市朝阳区阜通东大街6号&output=json"
```

### Reverse Geocode — `geocode/regeo`

Convert coordinates → address.

```bash
curl -s "https://restapi.amap.com/v3/geocode/regeo?key=$AMAP_KEY&location=116.481488,39.990464&radius=1000&extensions=base&output=json"
```

### Driving Directions — `direction/driving`

```bash
curl -s "https://restapi.amap.com/v3/direction/driving?key=$AMAP_KEY&origin=116.459298,40.003874&destination=116.387271,39.922501&extensions=all&output=json"
```

For `origin`/`destination`, use `lng,lat` coordinates. Use `geocode/geo` first if starting from addresses.

### Walking Directions — `direction/walking`

```bash
curl -s "https://restapi.amap.com/v3/direction/walking?key=$AMAP_KEY&origin=116.434307,39.90909&destination=116.434446,39.90816&output=json"
```

### Public Transit — `direction/transit/integrated`

```bash
curl -s "https://restapi.amap.com/v3/direction/transit/integrated?key=$AMAP_KEY&origin=116.434307,39.90909&destination=116.397428,39.90923&city=北京&output=json"
```

### Weather — `weather/weatherInfo`

```bash
curl -s "https://restapi.amap.com/v3/weather/weatherInfo?key=$AMAP_KEY&city=110000&extensions=all&output=json"
```

Accepts city name, adcode, or district name. `extensions=base` for current weather only; `extensions=all` for 4-day forecast.

## Session Location Context

Amap APIs don't track the user's GPS. The agent must maintain a **session-level "current location"** so the user doesn't have to repeat their location in every query.

### How It Works

1. **First location mention** → geocode it, store as session location (variable in your head, not a file).
2. **Subsequent queries** ("附近", "天气", "导航到...") → use the stored location automatically.
3. **User moves** → update stored location on any new location signal.
4. **No location set** → ask once, then proceed.

### Location Signals (triggers to set/update)

| Signal | Action |
|--------|--------|
| "我在XX" / "现在在XX" | Geocode XX, store as new current location |
| "到XX了" / "刚到XX" | Same — treat as location update |
| Telegram location pin | Extract lat/lng directly, reverse-geocode for the human-readable name |
| "附近有什么" with no prior location | Ask: "你现在在哪？（地名/路牌/标志建筑都行）" |
| "北京今天天气" but user was last in Shanghai | Use the explicitly stated "北京", don't silently override stored location |

### Location Storage Format

Keep in your context as three fields:

```
session_location:
  name: "杭州西湖断桥"
  lng: 120.147
  lat: 30.260
  adcode: "330106"
  updated: "just now"
```

`adcode` matters for weather queries (required as 6-digit code). `name` is for echoing back to the user ("你目前在杭州西湖断桥附近...").

### IP Fallback (city-level only)

If the user asks a location-dependent question with no location set and no location signal in the message, use IP geolocation for a rough city-level guess:

```bash
curl -s "https://restapi.amap.com/v3/ip?key=$AMAP_KEY" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('city',''), d.get('adcode',''))"
```

- If it returns a city → store as session location, tell the user "你大概在{城市}，对吗？不对就告诉我具体位置。"
- IP precision is city-level. **Never use IP-derived coordinates for "附近" searches** — the precision isn't good enough. Only use IP to guess the city, then ask the user to narrow down.

### Travel Scenario

```
用户: "我到成都了"
Agent: → geocode 成都 → store as session location
      "知道了。成都宽窄巷子附近有什么需要查的？"

用户: "附近有什么火锅"
Agent: → nearby search around stored 成都 coordinates, keywords=火锅
      (no need to re-ask "你在哪")
```

### What NOT to Do

- **Don't persist location across sessions.** `memory` tool is for durable facts (user's home city, preferences). Session location is transient — the user might be traveling. Don't save it to memory.
- **Don't silently override on implicit cities.** "查一下北京的天气" doesn't mean the user moved to Beijing. Use the explicitly stated city for that query only.
- **Don't geocode names that are clearly not locations.** "我在想一个问题" ≠ location update. Only geocode when the sentence structure indicates physical presence.

## Canonical Patterns

### "附近有什么好吃的"

```bash
# Step 1: Get current location (from user, or geocode a landmark)
curl -s "https://restapi.amap.com/v3/geocode/geo?key=$AMAP_KEY&address=北京市朝阳区望京SOHO&output=json" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['geocodes'][0]['location'])"

# Step 2: Search nearby restaurants
curl -s "https://restapi.amap.com/v3/place/around?key=$AMAP_KEY&location=116.481,39.996&radius=1500&types=050000&offset=10&extensions=all&output=json" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
for p in d.get('pois', []):
    print(f'{p[\"name\"]:20s} │ {p.get(\"distance\",\"?\")}m │ ★{p.get(\"biz_ext\",{}).get(\"rating\",\"?\")} │ {p.get(\"address\",\"\")[:30]}')"
```

### Full workflow: Address → Coordinates → Route

```bash
AMAP_KEY="your_key"
ORIGIN="天安门广场"
DEST="三里屯太古里"

# Geocode both
O_COORDS=$(curl -s "https://restapi.amap.com/v3/geocode/geo?key=$AMAP_KEY&address=$ORIGIN&output=json" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['geocodes'][0]['location'])")
D_COORDS=$(curl -s "https://restapi.amap.com/v3/geocode/geo?key=$AMAP_KEY&address=$DEST&output=json" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['geocodes'][0]['location'])")

# Route
curl -s "https://restapi.amap.com/v3/direction/transit/integrated?key=$AMAP_KEY&origin=$O_COORDS&destination=$D_COORDS&city=北京&output=json" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
route = d.get('route', {})
print(f'Distance: {route.get(\"distance\",\"?\")}m, Duration: {int(route.get(\"transits\",[{}])[0].get(\"duration\",0))/60:.0f}min')
for step in route.get('transits', []):
    for seg in step.get('segments', []):
        bus = seg.get('bus', {})
        walking = seg.get('walking', {})
        if bus:
            print(f'  🚌 {bus.get(\"buslines\",[{}])[0].get(\"name\",\"?\")}: {bus.get(\"buslines\",[{}])[0].get(\"departure_stop\",{}).get(\"name\",\"?\")} → {bus.get(\"buslines\",[{}])[0].get(\"arrival_stop\",{}).get(\"name\",\"?\")}')
        elif walking:
            print(f'  🚶 Walk {walking.get(\"distance\",\"?\")}m to next stop')
"
```

## Convenience Script

A Python helper is available at `scripts/amap.py` that wraps all 7 endpoints with proper error handling and formatted output:

```bash
# Search nearby POIs (auto-formatted output)
python3 SKILL_DIR/scripts/amap.py nearby --lng 116.397 --lat 39.909 --radius 1000 --keywords 咖啡

# Geocode an address
python3 SKILL_DIR/scripts/amap.py geocode --address "北京市朝阳区望京SOHO"

# Reverse geocode
python3 SKILL_DIR/scripts/amap.py regeo --lng 116.481 --lat 39.996

# Route between two points
python3 SKILL_DIR/scripts/amap.py route --from "天安门广场" --to "三里屯太古里" --mode transit --city 北京

# Weather
python3 SKILL_DIR/scripts/amap.py weather --city 北京
```

All commands support `--json` for machine-readable output and `--key` to override `$AMAP_KEY`.

## Common Pitfalls

1. **Missing API key**: First call returns `{"status":"0","infocode":"10001","info":"INVALID_USER_KEY"}`. Run `export AMAP_KEY=...` or add to `~/.hermes/.env`. Register at https://console.amap.com/dev/key/app (free).

2. **Coordinate format**: Amap uses GCJ-02 coordinate system. For most practical purposes in mainland China, GPS coordinates (±50m accuracy) work fine. Outside China, use OSM-based tools instead.

3. **Adcode required for weather**: The weather API requires a 6-digit adcode (e.g. `110000` for Beijing), not city name directly. The script auto-resolves city names via the district API.

4. **City scoping**: `place/text` without `city` parameter searches nationwide — results may be far from the user's actual location. Always scope with `city` (name or adcode) when intent is local.

5. **Rate limits**: Free tier = 5000 calls/day per API. The script reports remaining quota from response headers. Bulk queries should add a 200ms delay between calls.

6. **Proxy not needed**: Amap API is accessible from mainland China without proxy unlike Google APIs. If curl fails with connection errors, check DNS resolution, not proxy settings.

## What NOT to Do

- **Don't use Amap outside China.** POI coverage is poor outside mainland China. Fall back to `find-nearby` skill (OSM-based) for international locations.
- **Don't hardcode coordinates.** Always resolve addresses via geocode first, then use coordinates for subsequent calls. Addresses are ambiguous; coordinates are exact.
- **Don't chain more than 3 API calls without asking.** Geocode → Nearby = 2 calls, fine. Geocode → Route with 3 waypoints = still fine. Searching 20 cities for a chain store = use batch processing with delays.
- **Don't expose the API key in output.** Always redact the key parameter from any echoed curl commands.

## Verification Checklist

- [ ] `AMAP_KEY` env var set and valid (run `curl -s "https://restapi.amap.com/v3/ip?key=$AMAP_KEY"`)
- [ ] Can search nearby POIs with coordinates
- [ ] Can geocode a Chinese address and get valid lng,lat
- [ ] Can plan a transit route between two known points
- [ ] Weather query returns current conditions for a major city
- [ ] Script `scripts/amap.py` runs without ImportError
