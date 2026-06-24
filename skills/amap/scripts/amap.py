#!/usr/bin/env python3
"""Amap (高德地图) API convenience wrapper for Hermes Agent.

Usage:
    python3 amap.py nearby --lng 116.397 --lat 39.909 --radius 1000 --keywords 咖啡
    python3 amap.py geocode --address "北京市朝阳区望京SOHO"
    python3 amap.py regeo --lng 116.481 --lat 39.996
    python3 amap.py route --from "天安门广场" --to "三里屯太古里" --mode transit --city 北京
    python3 amap.py weather --city 北京
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error


BASE_URL = "https://restapi.amap.com/v3"


def get_key(args):
    return args.key or os.environ.get("AMAP_KEY", "")


def api_call(endpoint, params, api_key):
    params["key"] = api_key
    params["output"] = "json"
    url = f"{BASE_URL}/{endpoint}?{urllib.parse.urlencode(params)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Hermes-Amap-Skill/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return {"status": "0", "info": f"HTTP {e.code}: {body[:300]}"}
    except Exception as e:
        return {"status": "0", "info": str(e)}


def cmd_nearby(args):
    if not args.lng or not args.lat:
        die("--lng and --lat are required for nearby search")
    params = {"location": f"{args.lng},{args.lat}", "offset": args.offset}
    if args.radius:
        params["radius"] = args.radius
    if args.keywords:
        params["keywords"] = args.keywords
    if args.types:
        params["types"] = args.types
    if args.extensions:
        params["extensions"] = args.extensions

    data = api_call("place/around", params, get_key(args))
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    if data.get("status") != "1":
        die(f"API error: {data.get('info', 'unknown')}")

    pois = data.get("pois", [])
    if not pois:
        print("No results found.")
        return

    print(f"Found {data.get('count', len(pois))} results:\n")
    for p in pois:
        name = p.get("name", "?")
        dist = p.get("distance", "?")
        addr = p.get("address", "")[:40]
        rating = p.get("biz_ext", {}).get("rating", "") if p.get("biz_ext") else ""
        cost = p.get("biz_ext", {}).get("cost", "") if p.get("biz_ext") else ""
        tel = p.get("tel", "") or ""
        loc = p.get("location", "")

        line = f"  {name}"
        if rating:
            line += f"  ★{rating}"
        if cost:
            line += f"  ¥{cost}"
        line += f"\n    {dist}m │ {addr}"
        if tel:
            line += f" │ ☎ {tel}"
        if loc:
            lng, lat = loc.split(",")
            line += f"\n    https://uri.amap.com/marker?position={lng},{lat}&name={urllib.parse.quote(name)}"
        print(line)
        print()


def cmd_text_search(args):
    if not args.keywords:
        die("--keywords is required for text search")
    params = {"keywords": args.keywords, "offset": args.offset}
    if args.city:
        params["city"] = args.city
    if args.citylimit:
        params["citylimit"] = "true"
    if args.types:
        params["types"] = args.types

    data = api_call("place/text", params, get_key(args))
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    if data.get("status") != "1":
        die(f"API error: {data.get('info', 'unknown')}")

    pois = data.get("pois", [])
    if not pois:
        print("No results found.")
        return

    print(f"Found {data.get('count', len(pois))} results:\n")
    for p in pois:
        name = p.get("name", "?")
        addr = p.get("address", "")[:40]
        loc = p.get("location", "")
        print(f"  {name}")
        print(f"    {addr}")
        if loc:
            lng, lat = loc.split(",")
            print(f"    https://uri.amap.com/marker?position={lng},{lat}&name={urllib.parse.quote(name)}")
        print()


def cmd_geocode(args):
    if not args.address:
        die("--address is required for geocode")
    data = api_call("geocode/geo", {"address": args.address}, get_key(args))

    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    if data.get("status") != "1":
        die(f"API error: {data.get('info', 'unknown')}")

    geos = data.get("geocodes", [])
    if not geos:
        print(f"No coordinates found for: {args.address}")
        return

    for g in geos:
        loc = g.get("location", "")
        lng, lat = loc.split(",") if "," in loc else ("?", "?")
        print(f"  {g.get('formatted_address', args.address)}")
        print(f"    lng={lng}, lat={lat}")
        print(f"    adcode={g.get('adcode', '?')}  level={g.get('level', '?')}")
        print(f"    https://uri.amap.com/marker?position={lng},{lat}")
        print()


def cmd_regeo(args):
    if not args.lng or not args.lat:
        die("--lng and --lat are required for reverse geocode")
    params = {"location": f"{args.lng},{args.lat}"}
    if args.radius:
        params["radius"] = args.radius
    data = api_call("geocode/regeo", params, get_key(args))

    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    if data.get("status") != "1":
        die(f"API error: {data.get('info', 'unknown')}")

    regeo = data.get("regeocode", {})
    print(f"  {regeo.get('formatted_address', '?')}")
    addr = regeo.get("addressComponent", {})
    if addr:
        parts = []
        for k in ["province", "city", "district", "township", "streetNumber"]:
            v = addr.get(k)
            if v and isinstance(v, str):
                parts.append(v)
            elif v and isinstance(v, dict):
                parts.append(v.get("street", "") + (v.get("number", "")))
        print(f"  {' '.join(p for p in parts if p)}")


def cmd_route(args):
    if not args.from_ or not args.to:
        die("--from and --to are required for routing")

    key = get_key(args)

    # Geocode origin and destination if they look like addresses
    origin = args.from_
    dest = args.to
    city = args.city or ""

    # Try to parse as coordinates first
    for label, val in [("origin", origin), ("destination", dest)]:
        parts = val.split(",")
        if len(parts) != 2:
            try:
                [float(p) for p in parts]
            except ValueError:
                # Looks like an address, geocode it
                geo = api_call("geocode/geo", {"address": val, "city": city}, key)
                if geo.get("status") == "1" and geo.get("geocodes"):
                    loc = geo["geocodes"][0]["location"]
                    if not city and geo["geocodes"][0].get("city"):
                        city = geo["geocodes"][0]["city"]
                    if label == "origin":
                        origin = loc
                    else:
                        dest = loc

    mode = args.mode
    endpoint_map = {
        "driving": "direction/driving",
        "walking": "direction/walking",
        "transit": "direction/transit/integrated",
        "bicycling": "direction/bicycling",
    }
    endpoint = endpoint_map.get(mode, "direction/transit/integrated")

    params = {"origin": origin, "destination": dest, "extensions": "all"}
    if city:
        params["city"] = city

    data = api_call(endpoint, params, key)

    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    if data.get("status") != "1":
        die(f"API error: {data.get('info', 'unknown')}")

    route_info = data.get("route", {})
    if mode in ("driving", "walking", "bicycling"):
        paths = route_info.get("paths", [])
        if paths:
            p = paths[0]
            dist_km = int(p.get("distance", 0)) / 1000
            dur_min = int(p.get("duration", 0)) / 60
            print(f"  {mode.title()}: {dist_km:.1f}km, ~{dur_min:.0f}min")
            for step in p.get("steps", [])[:10]:
                instruction = step.get("instruction", "?")
                step_dist = int(step.get("distance", 0))
                print(f"    {instruction} ({step_dist}m)")
    else:  # transit
        transits = route_info.get("transits", [])
        if transits:
            t = transits[0]
            cost = t.get("cost", "?")
            dur_min = int(t.get("duration", 0)) / 60
            dist = int(t.get("distance", 0)) / 1000
            print(f"  Transit: {dist:.1f}km, ~{dur_min:.0f}min, ¥{cost}")
            for seg in t.get("segments", []):
                bus = seg.get("bus", {})
                walking = seg.get("walking", {})
                if bus and bus.get("buslines"):
                    bl = bus["buslines"][0]
                    dep = bl.get("departure_stop", {}).get("name", "?")
                    arr = bl.get("arrival_stop", {}).get("name", "?")
                    name = bl.get("name", "?")
                    print(f"    🚌 {name}: {dep} → {arr}")
                elif walking:
                    wd = walking.get("distance", "?")
                    print(f"    🚶 Walk {wd}m")


def cmd_weather(args):
    if not args.city:
        die("--city is required for weather")

    key = get_key(args)

    # Resolve city name to adcode if needed
    city_param = args.city
    if not city_param.isdigit() or len(city_param) != 6:
        district = api_call("config/district", {"keywords": args.city, "subdistrict": "0"}, key)
        if district.get("status") == "1" and district.get("districts"):
            adcode = district["districts"][0].get("adcode", "")
            if adcode:
                city_param = adcode

    params = {"city": city_param, "extensions": args.extensions}
    data = api_call("weather/weatherInfo", params, key)

    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    if data.get("status") != "1":
        die(f"API error: {data.get('info', 'unknown')}")

    # Check if result is inside "lives" (base) or "forecasts" (all)
    if data.get("lives"):
        for live in data["lives"]:
            print(f"  {live.get('province', '')} {live.get('city', '')}")
            print(f"  {live.get('weather', '?')}  {live.get('temperature', '?')}°C")
            print(f"  风向: {live.get('winddirection', '?')}  风力: {live.get('windpower', '?')}")
            print(f"  湿度: {live.get('humidity', '?')}%  报告时间: {live.get('reporttime', '?')}")

    elif data.get("forecasts"):
        for fc in data["forecasts"]:
            print(f"  {fc.get('province', '')} {fc.get('city', '')}")
            for cast in fc.get("casts", []):
                day = cast.get("date", "?")
                dw = cast.get("dayweather", "?")
                nw = cast.get("nightweather", "?")
                dt = cast.get("daytemp", "?")
                nt = cast.get("nighttemp", "?")
                print(f"  {day}  白天: {dw} {dt}°C  夜间: {nw} {nt}°C")


def die(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Amap API wrapper for Hermes Agent")
    parser.add_argument("--key", help="Amap API key (default: $AMAP_KEY)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")

    sub = parser.add_subparsers(dest="command")

    # nearby
    p = sub.add_parser("nearby", help="Search nearby POIs")
    p.add_argument("--lng", type=float, help="Longitude")
    p.add_argument("--lat", type=float, help="Latitude")
    p.add_argument("--radius", type=int, default=1500, help="Search radius in meters (default: 1500)")
    p.add_argument("--keywords", help="Search keywords")
    p.add_argument("--types", help="POI category code")
    p.add_argument("--offset", type=int, default=10, help="Results per page (default: 10, max: 25)")
    p.add_argument("--extensions", choices=["base", "all"], default="base", help="Result detail level")

    # text
    p = sub.add_parser("text", help="Text search for POIs")
    p.add_argument("--keywords", required=True, help="Search keywords")
    p.add_argument("--city", help="City name or adcode to scope search")
    p.add_argument("--citylimit", action="store_true", help="Limit results to specified city only")
    p.add_argument("--types", help="POI category code")
    p.add_argument("--offset", type=int, default=10, help="Results per page (default: 10)")

    # geocode
    p = sub.add_parser("geocode", help="Address → coordinates")
    p.add_argument("--address", required=True, help="Address to geocode")

    # regeo
    p = sub.add_parser("regeo", help="Coordinates → address")
    p.add_argument("--lng", type=float, help="Longitude")
    p.add_argument("--lat", type=float, help="Latitude")
    p.add_argument("--radius", type=int, default=1000, help="Radius for nearby POIs in result")

    # route
    p = sub.add_parser("route", help="Route planning")
    p.add_argument("--from", dest="from_", required=True, help="Origin (address or lng,lat)")
    p.add_argument("--to", required=True, help="Destination (address or lng,lat)")
    p.add_argument("--mode", choices=["driving", "walking", "transit", "bicycling"], default="transit")
    p.add_argument("--city", help="City name for transit routing")

    # weather
    p = sub.add_parser("weather", help="Weather query")
    p.add_argument("--city", required=True, help="City name or adcode")
    p.add_argument("--extensions", choices=["base", "all"], default="all", help="base=current, all=forecast")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "nearby": cmd_nearby,
        "text": cmd_text_search,
        "geocode": cmd_geocode,
        "regeo": cmd_regeo,
        "route": cmd_route,
        "weather": cmd_weather,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
