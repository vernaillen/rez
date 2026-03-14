#!/usr/bin/env python3
"""
Immoweb Monitor CLI for Clawdbot
Searches, monitors, and analyzes immoweb.be property listings.
Includes full analysis workflow for Wouter's property search.
"""

import argparse
import json
import os
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import unicodedata

try:
    import httpx
except ImportError:
    print(json.dumps({"status": "error", "message": "httpx not installed"}))
    sys.exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    print(json.dumps({"status": "error", "message": "beautifulsoup4 not installed"}))
    sys.exit(1)


# Paths
CLAWDBOT_DIR = Path.home() / ".clawdbot"
CONFIG_FILE = CLAWDBOT_DIR / "immoweb-config.json"
SEEN_FILE = CLAWDBOT_DIR / "immoweb-seen.json"
IMMO_DIR = Path.home() / "Documents" / "immo"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "nl-BE,nl;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "no-cache",
    "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"macOS"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "Referer": "https://www.immoweb.be/",
}

# Default config (override via immoweb-config.json in same directory)
DEFAULT_CONFIG = {
    "postal_code": "9000",
    "postal_codes": [],
    "radius_km": 35,
    "max_price": 500000,
    "max_price_private": 350000,
    "min_bedrooms": 2,
    "min_living_area": 100,
    "must_have_garden": True,
    "must_have_parking": True,
    "must_be_quiet": False,
    "allow_renovation": False,
    "property_type": "house",
    "min_soundhealing_room": 14,
    "preferred_dance_hall": 60,
    "top_candidate": {}
}

# Load config override from immoweb-config.json if it exists
import json as _json
_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "immoweb-config.json")
if os.path.exists(_config_path):
    with open(_config_path) as _f:
        DEFAULT_CONFIG.update(_json.load(_f))


def slugify(text: str) -> str:
    """Convert text to URL/folder-friendly slug."""
    # Normalize unicode
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    # Replace spaces and special chars
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text).strip('-')
    return text[:50]  # Limit length


class ImmowebCLI:
    def __init__(self):
        CLAWDBOT_DIR.mkdir(parents=True, exist_ok=True)
        self.config = self._load_config()
        self.seen = self._load_seen()
        # SOCKS proxy support: set IMMOWEB_PROXY=socks5://localhost:1080
        self.proxy = os.environ.get("IMMOWEB_PROXY") or os.environ.get("SOCKS_PROXY")
    
    def _get_client(self) -> httpx.Client:
        """Return configured httpx client with optional proxy."""
        kwargs = {
            "follow_redirects": True,
            "timeout": 15.0,
        }
        if self.proxy:
            kwargs["proxy"] = self.proxy
        return httpx.Client(**kwargs)
    
    def _load_config(self) -> dict:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE) as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
        return DEFAULT_CONFIG.copy()
    
    def _save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def _load_seen(self) -> dict:
        if SEEN_FILE.exists():
            with open(SEEN_FILE) as f:
                return json.load(f)
        return {"seen": {}, "dismissed": {}}
    
    def _save_seen(self):
        with open(SEEN_FILE, 'w') as f:
            json.dump(self.seen, f, indent=2)
    
    def _mark_seen(self, prop_id: str, data: dict):
        self.seen["seen"][prop_id] = {
            "first_seen": datetime.now().isoformat(),
            "title": data.get("title", ""),
            "price": data.get("price", 0)
        }
        self._save_seen()
    
    def _is_new(self, prop_id: str) -> bool:
        return prop_id not in self.seen["seen"] and prop_id not in self.seen.get("dismissed", {})
    
    def _build_search_url(self, page: int = 1) -> str:
        """Build immoweb search URL."""
        prop_type = self.config["property_type"]
        postal_codes = self.config.get("postal_codes", [self.config["postal_code"]])
        max_price = self.config["max_price"]
        min_bed = self.config["min_bedrooms"]
        
        type_map = {"house": "huis", "apartment": "appartement", "building": "gebouw"}
        prop_nl = type_map.get(prop_type, "huis")
        
        postal_param = ",".join(f"BE-{p}" for p in postal_codes)
        
        url = f"https://www.immoweb.be/nl/zoeken/{prop_nl}/te-koop"
        url += f"?countries=BE"
        url += f"&postalCodes={postal_param}"
        url += f"&maxPrice={max_price}"
        url += f"&minBedroomCount={min_bed}"
        url += f"&orderBy=newest"
        url += f"&page={page}"
        
        return url
    
    def _extract_listing_ids(self, html: str) -> List[str]:
        """Extract property IDs from search results page."""
        ids = re.findall(r'/(\d{8,})"', html)
        return list(set(ids))
    
    def _fetch_property_details(self, prop_id: str) -> Optional[dict]:
        """Fetch and parse a single property listing."""
        url = f"https://www.immoweb.be/nl/zoekertje/huis/te-koop/x/x/{prop_id}"
        
        try:
            with self._get_client() as client:
                resp = client.get(url, headers=HEADERS)
                resp.raise_for_status()
                return self._parse_property(resp.text, prop_id, resp.url)
        except Exception as e:
            print(f"Error fetching {prop_id}: {e}", file=sys.stderr)
            return None
    
    def _parse_property(self, html: str, prop_id: str, final_url: str) -> dict:
        """Parse property details from HTML."""
        idx = html.find('window.classified')
        if idx != -1:
            try:
                brace_start = html.index('{', idx)
                decoder = json.JSONDecoder()
                data, _ = decoder.raw_decode(html, brace_start)
                return self._parse_classified_json(data, prop_id, str(final_url), html)
            except:
                pass
        
        return self._parse_html(html, prop_id, str(final_url))
    
    def _parse_classified_json(self, data: dict, prop_id: str, url: str, html: str = "") -> dict:
        """Parse the window.classified JSON object."""
        prop = data.get('property', {})
        price_data = data.get('price', {})
        location = prop.get('location', {})
        building = prop.get('building', {})
        land = prop.get('land', {})
        
        # Address
        street = location.get('street', '')
        number = location.get('number', '')
        city = location.get('locality', '')
        postal = location.get('postalCode', '')
        address = f"{street} {number}, {postal} {city}".strip(", ")
        
        # Garden
        garden_surface = prop.get('gardenSurface')
        has_garden = prop.get('hasGarden')
        plot_size = land.get('surface')
        if has_garden is None:
            has_garden = (garden_surface and garden_surface > 0) or (plot_size and plot_size > 200)
        
        # Condition
        condition_raw = building.get('condition', '')
        condition_map = {
            'GOOD': 'instapklaar', 'AS_NEW': 'instapklaar', 'JUST_RENOVATED': 'instapklaar',
            'TO_RESTORE': 'te renoveren', 'TO_RENOVATE': 'te renoveren', 'TO_BE_DONE_UP': 'op te frissen'
        }
        condition = condition_map.get(condition_raw, condition_raw)
        
        # Extract rooms info for practice potential
        rooms = []
        room_count = prop.get('roomCount', 0)
        
        # Check for annexe/bijgebouw
        has_annexe = False
        annexe_keywords = ['bijgebouw', 'loods', 'atelier', 'garage', 'praktijk', 'bureau']
        description = data.get('description', '')
        title = prop.get('title', '')
        text_to_check = (description + ' ' + title + ' ' + html).lower()
        
        for kw in annexe_keywords:
            if kw in text_to_check:
                has_annexe = True
                break
        
        # Check for quiet location indicators
        quiet_indicators = ['rustig', 'landelijk', 'residentieel', 'villawijk', 'doodlopend']
        noisy_indicators = ['steenweg', 'gewestweg', 'n8', 'n42', 'n60', 'doorgangsweg', 'druk', 'hoofdweg']
        
        is_quiet = None
        for indicator in quiet_indicators:
            if indicator in text_to_check:
                is_quiet = True
                break
        for indicator in noisy_indicators:
            if indicator in text_to_check:
                is_quiet = False
                break
        
        # Parking
        parking_count = prop.get('parkingCountIndoor', 0) or 0
        parking_count += prop.get('parkingCountOutdoor', 0) or 0
        has_garage = prop.get('hasGarage', False)
        has_parking = parking_count > 0 or has_garage or 'parking' in text_to_check or 'garage' in text_to_check
        
        return {
            "id": prop_id,
            "url": url,
            "title": prop.get('title', f"Property {prop_id}"),
            "description": description[:500] if description else "",
            "price": price_data.get('mainValue', 0),
            "address": address if address else "Unknown",
            "street": street,
            "postal_code": postal,
            "city": city,
            "bedrooms": prop.get('bedroomCount'),
            "bathrooms": prop.get('bathroomCount'),
            "living_area": prop.get('netHabitableSurface'),
            "plot_size": plot_size,
            "condition": condition,
            "has_garden": bool(has_garden),
            "garden_size": garden_surface or plot_size,
            "year_built": building.get('constructionYear'),
            "epc": data.get('transaction', {}).get('certificates', {}).get('epcScore'),
            "epc_value": data.get('transaction', {}).get('certificates', {}).get('primaryEnergyConsumptionPerSqm'),
            # Enhanced fields
            "has_annexe": has_annexe,
            "has_parking": has_parking,
            "parking_count": parking_count,
            "has_garage": has_garage,
            "is_quiet": is_quiet,
            "room_count": room_count,
            "property_type": prop.get('type', ''),
            "subtype": prop.get('subtype', ''),
        }
    
    def _parse_html(self, html: str, prop_id: str, url: str) -> dict:
        """Fallback HTML parsing."""
        soup = BeautifulSoup(html, 'html.parser')
        
        title_elem = soup.find('h1')
        title = title_elem.text.strip() if title_elem else f"Property {prop_id}"
        
        price = 0
        price_text = soup.find(string=re.compile(r'€\s*[\d\.,]+'))
        if price_text:
            match = re.search(r'([\d\.]+)', price_text.replace(',', '').replace('.', ''))
            if match:
                price = int(match.group(1))
        
        return {
            "id": prop_id,
            "url": url,
            "title": title,
            "price": price,
            "address": "Unknown",
            "bedrooms": None,
            "living_area": None,
            "condition": None,
            "has_garden": "tuin" in html.lower() or "garden" in html.lower(),
            "has_annexe": "bijgebouw" in html.lower() or "loods" in html.lower(),
            "has_parking": "parking" in html.lower() or "garage" in html.lower(),
            "is_quiet": None
        }
    
    def _score_property(self, prop: dict) -> dict:
        """Score a property against criteria."""
        matches = []
        mismatches = []
        flags = []
        
        # Price
        if prop["price"] and prop["price"] <= self.config["max_price"]:
            matches.append(f"✅ Price €{prop['price']:,}")
        elif prop["price"]:
            mismatches.append(f"❌ Price €{prop['price']:,} exceeds €{self.config['max_price']:,}")
        
        # Bedrooms
        if prop.get("bedrooms"):
            if prop["bedrooms"] >= self.config["min_bedrooms"]:
                matches.append(f"✅ {prop['bedrooms']} bedrooms")
            else:
                mismatches.append(f"❌ Only {prop['bedrooms']} bedrooms")
        else:
            flags.append("⚠️ Bedrooms unknown")
        
        # Garden
        if self.config["must_have_garden"]:
            if prop.get("has_garden"):
                if prop.get("garden_size"):
                    matches.append(f"✅ Garden ({prop['garden_size']}m²)")
                else:
                    matches.append("✅ Has garden")
            else:
                mismatches.append("❌ No garden")
        
        # Parking
        if self.config.get("must_have_parking"):
            if prop.get("has_parking"):
                matches.append("✅ Parking available")
            else:
                mismatches.append("❌ No parking mentioned")
        
        # Quiet location (nice-to-have, shown as info)
        if prop.get("is_quiet") is True:
            matches.append("✅ Quiet location")
        elif prop.get("is_quiet") is False:
            flags.append("⚠️ Possibly busier location - verify")
        
        # Annexe / practice potential
        if prop.get("has_annexe"):
            matches.append("✅ Has annexe/bijgebouw (practice potential)")
        
        # Condition
        condition = (prop.get("condition") or "").lower()
        if "renoveren" in condition or "restore" in condition:
            if not self.config["allow_renovation"]:
                mismatches.append("❌ Needs renovation")
            else:
                flags.append("⚠️ Needs renovation")
        elif condition:
            matches.append(f"✅ {prop['condition']}")
        
        # Living area
        if prop.get("living_area"):
            if prop["living_area"] >= self.config.get("min_living_area", 100):
                matches.append(f"✅ {prop['living_area']}m² living")
            else:
                flags.append(f"⚠️ Only {prop['living_area']}m²")
        
        # Calculate score
        if len(mismatches) >= 2:
            score = 1
            rec = "🔴 SKIP"
        elif len(mismatches) == 1:
            score = 2
            rec = "🟡 MAYBE"
        elif len(flags) >= 3:
            score = 3
            rec = "🟡 CHECK"
        elif len(flags) >= 1:
            score = 4
            rec = "🟢 GOOD"
        else:
            score = 5
            rec = "🟢 VISIT"
        
        return {
            **prop,
            "score": score,
            "recommendation": rec,
            "matches": matches,
            "mismatches": mismatches,
            "flags": flags
        }
    
    def _phase1_check(self, prop: dict) -> dict:
        """Phase 1: Quick must-have checklist."""
        checks = {}
        passed = True
        
        # Budget
        if prop.get("price") and prop["price"] <= self.config["max_price"]:
            checks["budget"] = {"status": "✅", "note": f"€{prop['price']:,} < €{self.config['max_price']:,}"}
        elif prop.get("price"):
            checks["budget"] = {"status": "❌", "note": f"€{prop['price']:,} exceeds max"}
            passed = False
        else:
            checks["budget"] = {"status": "⚠️", "note": "Price unknown"}
        
        # Location (assume within radius since it came from search)
        checks["location"] = {"status": "✅", "note": f"{prop.get('city', 'Unknown')} - within search radius"}
        
        # Quiet street - only fail on confirmed noisy, unknown is just a warning
        if prop.get("is_quiet") is True:
            checks["quiet"] = {"status": "✅", "note": "Rustig/landelijk indicated"}
        elif prop.get("is_quiet") is False:
            checks["quiet"] = {"status": "⚠️", "note": "Possible main road - verify on map"}
            # Don't auto-fail, just warn - let user verify
        else:
            checks["quiet"] = {"status": "⚠️", "note": "Unknown - verify on map"}
        
        # Garden
        if prop.get("has_garden"):
            size_note = f" ({prop.get('garden_size')}m²)" if prop.get('garden_size') else ""
            checks["garden"] = {"status": "✅", "note": f"Has garden{size_note}"}
        else:
            checks["garden"] = {"status": "❌", "note": "No garden"}
            passed = False
        
        # Parking
        if prop.get("has_parking"):
            checks["parking"] = {"status": "✅", "note": "Parking available"}
        else:
            checks["parking"] = {"status": "❌", "note": "No parking mentioned"}
            passed = False
        
        # Bedrooms
        if prop.get("bedrooms") and prop["bedrooms"] >= self.config["min_bedrooms"]:
            checks["bedrooms"] = {"status": "✅", "note": f"{prop['bedrooms']} bedrooms"}
        elif prop.get("bedrooms"):
            checks["bedrooms"] = {"status": "❌", "note": f"Only {prop['bedrooms']} bedrooms"}
            passed = False
        else:
            checks["bedrooms"] = {"status": "⚠️", "note": "Bedroom count unknown"}
        
        # Soundhealing room potential (14m²)
        living = prop.get("living_area", 0) or 0
        if living >= 100 or prop.get("has_annexe"):
            checks["soundhealing"] = {"status": "✅", "note": "Likely has 14m²+ room available"}
        elif living >= 80:
            checks["soundhealing"] = {"status": "⚠️", "note": "May have suitable room - verify"}
        else:
            checks["soundhealing"] = {"status": "⚠️", "note": "Living area unknown - verify rooms"}
        
        # Condition
        condition = (prop.get("condition") or "").lower()
        if "renoveren" in condition:
            checks["condition"] = {"status": "❌", "note": "Needs full renovation"}
            if not self.config["allow_renovation"]:
                passed = False
        elif "frissen" in condition:
            checks["condition"] = {"status": "⚠️", "note": "Needs refreshing"}
        elif condition:
            checks["condition"] = {"status": "✅", "note": prop.get("condition", "OK")}
        else:
            checks["condition"] = {"status": "⚠️", "note": "Condition unknown"}
        
        return {
            "passed": passed,
            "checks": checks,
            "fail_reasons": [k for k, v in checks.items() if v["status"] == "❌"]
        }
    
    def _estimate_split(self, prop: dict) -> dict:
        """Estimate zaak/privé split."""
        price = prop.get("price", 0)
        living = prop.get("living_area", 0) or 0
        
        # Base estimate: 30% business if annexe, 20% otherwise
        if prop.get("has_annexe"):
            business_pct = 35
        elif living >= 200:
            business_pct = 25
        else:
            business_pct = 20
        
        business_value = int(price * business_pct / 100)
        private_value = price - business_value
        
        return {
            "total_price": price,
            "business_pct": business_pct,
            "business_value": business_value,
            "private_value": private_value,
            "private_under_limit": private_value <= self.config.get("max_price_private", 350000),
            "note": "Estimate based on property features - actual split depends on room allocation"
        }
    
    def _generate_analyse_md(self, prop: dict, phase1: dict, split: dict) -> str:
        """Generate ANALYSE.md content."""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Determine final recommendation
        if not phase1["passed"]:
            final_score = "⭐⭐" if len(phase1["fail_reasons"]) == 1 else "⭐"
            verdict = "🔴 **NIET AANBEVOLEN**"
            verdict_reason = f"Failed Phase 1: {', '.join(phase1['fail_reasons'])}"
        elif prop.get("has_annexe") and prop.get("is_quiet") is not False:
            final_score = "⭐⭐⭐⭐⭐" if split["private_under_limit"] else "⭐⭐⭐⭐"
            verdict = "🟢 **ZEKER BEZOEKEN**"
            verdict_reason = "Has annexe/bijgebouw for practice, meets core criteria"
        elif split["private_under_limit"]:
            final_score = "⭐⭐⭐⭐"
            verdict = "🟢 **ZEKER BEZOEKEN**"
            verdict_reason = "Private portion within budget, meets criteria"
        else:
            final_score = "⭐⭐⭐"
            verdict = "🟡 **MISSCHIEN**"
            verdict_reason = "Some concerns - review details"
        
        # Build phase 1 table
        p1_rows = []
        for key, val in phase1["checks"].items():
            p1_rows.append(f"| {key.title()} | {val['status']} | {val['note']} |")
        p1_table = "\n".join(p1_rows)
        
        # Comparison to top candidate
        top = self.config.get("top_candidate", {})
        
        md = f"""# Property Analysis

**Generated:** {today}
**Tool:** Immoweb Skill (Clawdbot)

---

## 📍 Property Summary

| Field | Value |
|-------|-------|
| **Adres** | {prop.get('address', 'Unknown')} |
| **Link** | {prop.get('url', '')} |
| **Datum analyse** | {today} |
| **Totale prijs** | €{prop.get('price', 0):,} |
| **Geschatte privé-waarde** | €{split['private_value']:,} |
| **Geschatte zakelijke waarde** | €{split['business_value']:,} ({split['business_pct']}%) |
| **Type pand** | {prop.get('subtype', prop.get('property_type', 'Woning'))} |
| **Bouwjaar** | {prop.get('year_built', 'Unknown')} |
| **Totale oppervlakte** | {prop.get('living_area', '?')} m² |
| **Perceel** | {prop.get('plot_size', '?')} m² |
| **Aantal slaapkamers** | {prop.get('bedrooms', '?')} |
| **EPC** | {prop.get('epc', '?')} |

---

## ✅ PHASE 1: Quick Checklist Results

| Must-Have | Resultaat | Notes |
|-----------|-----------|-------|
{p1_table}

**Phase 1 Result:** {'✅ PROCEED to Phase 2' if phase1['passed'] else f"❌ STOPPED (reason: {', '.join(phase1['fail_reasons'])})"}

---

## 🔍 PHASE 2: Detailed Analysis

### A. Key Features

| Feature | Status |
|---------|--------|
| **Bijgebouw/Annexe** | {'✅ Yes' if prop.get('has_annexe') else '❌ No'} |
| **Garage** | {'✅ Yes' if prop.get('has_garage') else '❌ No'} |
| **Parking** | {'✅ Yes' if prop.get('has_parking') else '❌ No'} |
| **Tuin** | {'✅ Yes' if prop.get('has_garden') else '❌ No'} ({prop.get('garden_size', '?')}m²) |
| **Rustige ligging** | {'✅ Yes' if prop.get('is_quiet') else '⚠️ Unknown/No' if prop.get('is_quiet') is False else '⚠️ Verify'} |
| **Staat** | {prop.get('condition', 'Unknown')} |

---

### B. Space Allocation (Zaak/Privé Split)

**Estimated Configuration:**
- **Total price:** €{split['total_price']:,}
- **Business portion:** €{split['business_value']:,} ({split['business_pct']}%)
- **Private portion:** €{split['private_value']:,}
- **Private under €350k limit:** {'✅ Yes' if split['private_under_limit'] else '❌ No'}

{split['note']}

**Business spaces (typical):**
- Soundhealing room (14m²+ required)
- Practice space / waiting area
- Client entrance (if separate)
- Client parking
- Bijgebouw/annexe if present

**Private spaces:**
- Bedrooms ({prop.get('bedrooms', '?')})
- Living room, kitchen, bathroom(s)
- Private garden area

---

### C. Practice Potential

| Aspect | Assessment |
|--------|------------|
| **Soundhealing room (14m²)** | {'✅ Likely available' if (prop.get('living_area') or 0) >= 100 or prop.get('has_annexe') else '⚠️ Verify room sizes'} |
| **Dance hall (60m²)** | {'⚠️ Possible in bijgebouw' if prop.get('has_annexe') else '❌ No obvious space'} |
| **Separate client entrance** | {'⚠️ Possible' if prop.get('has_annexe') else '⚠️ May need to create'} |
| **Client parking** | {'✅ Yes' if prop.get('has_parking') else '❌ No'} |

---

### D. Comparison to Top Candidate ({top.get('name', 'Baseline')})

| Factor | This Property | {top.get('name', 'Baseline')} (⭐⭐⭐⭐⭐) | Advantage |
|--------|---------------|----------------------|-----------|
| **Total price** | €{prop.get('price', 0):,} | €{top.get('price', 385000):,} | {'This' if prop.get('price', 999999) < top.get('price', 385000) else top.get('name', 'Baseline') if prop.get('price', 0) > top.get('price', 385000) else 'Equal'} |
| **Bijgebouw** | {'Yes' if prop.get('has_annexe') else 'No'} | Yes | {'Equal' if prop.get('has_annexe') else top.get('name', 'Baseline')} |
| **Rustige ligging** | {'Yes' if prop.get('is_quiet') else 'Unknown'} | Excellent | {'Equal' if prop.get('is_quiet') else top.get('name', 'Baseline')} |
| **Tuin** | {'Yes' if prop.get('has_garden') else 'No'} | Large + views | {'Similar' if prop.get('has_garden') else top.get('name', 'Baseline')} |

---

### E. Strengths

"""
        # Add strengths
        strengths = []
        if prop.get("has_annexe"):
            strengths.append("- ✅ Has bijgebouw/annexe — excellent for practice space")
        if prop.get("is_quiet"):
            strengths.append("- ✅ Quiet location — good for soundhealing")
        if split["private_under_limit"]:
            strengths.append("- ✅ Private portion within €350k budget")
        if prop.get("has_garden"):
            strengths.append(f"- ✅ Has garden ({prop.get('garden_size', '?')}m²)")
        if prop.get("condition") and "instapklaar" in prop.get("condition", "").lower():
            strengths.append("- ✅ Move-in ready condition")
        if prop.get("epc") and prop.get("epc") in ["A", "B"]:
            strengths.append(f"- ✅ Good energy rating (EPC {prop.get('epc')})")
        
        if not strengths:
            strengths.append("- (Review listing for specific strengths)")
        
        md += "\n".join(strengths)
        
        md += """

---

### F. Concerns / Weaknesses

"""
        # Add concerns
        concerns = []
        if not prop.get("has_annexe"):
            concerns.append("- ⚠️ No bijgebouw — practice space in main building only")
        if prop.get("is_quiet") is False:
            concerns.append("- ❌ Possibly on busy road — not ideal for soundhealing")
        if not split["private_under_limit"]:
            concerns.append(f"- ⚠️ Private portion €{split['private_value']:,} exceeds €350k preference")
        if prop.get("condition") and "renoveren" in prop.get("condition", "").lower():
            concerns.append("- ❌ Needs renovation — significant investment required")
        if prop.get("epc") and prop.get("epc") in ["E", "F", "G"]:
            concerns.append(f"- ⚠️ Poor energy rating (EPC {prop.get('epc')}) — insulation costs")
        
        for reason in phase1["fail_reasons"]:
            if reason not in ["quiet", "condition"]:  # Avoid duplicates
                concerns.append(f"- ❌ Phase 1 fail: {reason}")
        
        if not concerns:
            concerns.append("- (No major concerns identified)")
        
        md += "\n".join(concerns)
        
        md += f"""

---

## 📊 Final Recommendation

**Overall Score:** {final_score}

**Verdict:** {verdict}

**Why:** {verdict_reason}

---

### Open Questions / Research Needed

- [ ] Verify quietness of street (check Google Maps / Street View)
- [ ] Bestemmingsplan allows soundhealing practice?
- [ ] Exact room dimensions (is there a 14m²+ room?)
- [ ] Parking arrangements for clients
- [ ] Noise restrictions in area?
- [ ] Agent contact for viewing

---

### Viewing Notes (fill in after visit)

- **Date visited:** ___
- **First impressions:** ___
- **Soundhealing room suitability:** ___
- **Neighborhood feel:** ___
- **Deal-breakers discovered:** ___
- **Would revisit:** ✅ / ❌
- **Action items:** ___
"""
        
        return md
    
    def search(self, limit: int = 20) -> dict:
        """Search immoweb for listings."""
        url = self._build_search_url()
        
        try:
            with self._get_client() as client:
                resp = client.get(url, headers=HEADERS)
                resp.raise_for_status()
        except Exception as e:
            return {"status": "error", "message": str(e)}
        
        ids = self._extract_listing_ids(resp.text)[:limit]
        
        if not ids:
            return {"status": "success", "count": 0, "properties": [], "message": "No listings found"}
        
        properties = []
        for prop_id in ids:
            details = self._fetch_property_details(prop_id)
            if details:
                scored = self._score_property(details)
                properties.append(scored)
                self._mark_seen(prop_id, details)
        
        properties.sort(key=lambda x: (-x["score"], x.get("price", 0)))
        
        return {
            "status": "success",
            "count": len(properties),
            "search_url": url,
            "properties": properties
        }
    
    def check_new(self, limit: int = 20) -> dict:
        """Check for new listings only."""
        url = self._build_search_url()
        
        try:
            with self._get_client() as client:
                resp = client.get(url, headers=HEADERS)
                resp.raise_for_status()
        except Exception as e:
            return {"status": "error", "message": str(e)}
        
        ids = self._extract_listing_ids(resp.text)[:limit]
        new_ids = [i for i in ids if self._is_new(i)]
        
        if not new_ids:
            return {
                "status": "success",
                "new_count": 0,
                "message": "No new listings since last check",
                "total_seen": len(self.seen.get("seen", {}))
            }
        
        properties = []
        for prop_id in new_ids:
            details = self._fetch_property_details(prop_id)
            if details:
                scored = self._score_property(details)
                properties.append(scored)
                self._mark_seen(prop_id, details)
        
        properties.sort(key=lambda x: (-x["score"], x.get("price", 0)))
        
        return {
            "status": "success",
            "new_count": len(properties),
            "properties": properties
        }
    
    def analyze(self, url: str) -> dict:
        """Analyze a single property URL (basic)."""
        match = re.search(r'/(\d{8,})(?:\?|$|")', url)
        if not match:
            return {"status": "error", "message": "Could not extract property ID from URL"}
        
        prop_id = match.group(1)
        details = self._fetch_property_details(prop_id)
        
        if not details:
            return {"status": "error", "message": "Failed to fetch property"}
        
        return {"status": "success", "property": self._score_property(details)}
    
    def analyze_full(self, url: str, output_dir: str = None) -> dict:
        """Full analysis with folder creation and ANALYSE.md generation."""
        match = re.search(r'/(\d{8,})(?:\?|$|")', url)
        if not match:
            return {"status": "error", "message": "Could not extract property ID from URL"}
        
        prop_id = match.group(1)
        details = self._fetch_property_details(prop_id)
        
        if not details:
            return {"status": "error", "message": "Failed to fetch property - listing may be removed"}
        
        # Score and analyze
        scored = self._score_property(details)
        phase1 = self._phase1_check(scored)
        split = self._estimate_split(scored)
        
        # Generate folder name
        today = datetime.now().strftime("%Y-%m-%d")
        city = scored.get("city", "Unknown").split()[0]  # First word of city
        
        # Create short description from title
        title = scored.get("title", "Property")
        short_desc = slugify(title[:40])
        
        folder_name = f"{today}_{city}_{short_desc}"
        
        # Determine output directory
        if output_dir:
            base_dir = Path(output_dir)
        else:
            base_dir = IMMO_DIR
        
        folder_path = base_dir / folder_name
        folder_path.mkdir(parents=True, exist_ok=True)
        
        # Generate and save ANALYSE.md
        analyse_content = self._generate_analyse_md(scored, phase1, split)
        analyse_path = folder_path / "ANALYSE.md"
        
        with open(analyse_path, 'w') as f:
            f.write(analyse_content)
        
        # Mark as seen
        self._mark_seen(prop_id, scored)
        
        return {
            "status": "success",
            "property": scored,
            "phase1": phase1,
            "split": split,
            "folder": str(folder_path),
            "analyse_file": str(analyse_path),
            "recommendation": scored.get("recommendation"),
            "score": scored.get("score")
        }
    
    def dismiss(self, prop_id: str) -> dict:
        """Mark a property as dismissed."""
        self.seen.setdefault("dismissed", {})[prop_id] = {
            "dismissed_at": datetime.now().isoformat()
        }
        self._save_seen()
        return {"status": "success", "message": f"Dismissed {prop_id}"}
    
    def list_seen(self) -> dict:
        """List seen and dismissed properties."""
        return {
            "status": "success",
            "seen_count": len(self.seen.get("seen", {})),
            "dismissed_count": len(self.seen.get("dismissed", {})),
            "seen": self.seen.get("seen", {}),
            "dismissed": self.seen.get("dismissed", {})
        }


def main():
    parser = argparse.ArgumentParser(description="Immoweb Monitor CLI")
    subparsers = parser.add_subparsers(dest="command")
    
    # Search
    search_p = subparsers.add_parser("search", help="Search for listings")
    search_p.add_argument("--limit", type=int, default=20)
    search_p.add_argument("--postal", help="Postal code")
    search_p.add_argument("--radius", type=int, help="Radius in km")
    search_p.add_argument("--max-price", type=int, help="Max price")
    search_p.add_argument("--type", choices=["house", "apartment", "building"])
    
    # Check new
    check_p = subparsers.add_parser("check-new", help="Check for new listings only")
    check_p.add_argument("--limit", type=int, default=20)
    
    # Analyze (basic)
    analyze_p = subparsers.add_parser("analyze", help="Analyze a property URL (basic)")
    analyze_p.add_argument("url", help="Property URL")
    
    # Analyze-full (creates folder + ANALYSE.md)
    analyze_full_p = subparsers.add_parser("analyze-full", help="Full analysis with folder + ANALYSE.md")
    analyze_full_p.add_argument("url", help="Property URL")
    analyze_full_p.add_argument("--output-dir", help="Output directory (default: ~/Documents/immo)")
    
    # Dismiss
    dismiss_p = subparsers.add_parser("dismiss", help="Dismiss a property")
    dismiss_p.add_argument("id", help="Property ID")
    
    # List seen
    subparsers.add_parser("list-seen", help="List seen properties")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    cli = ImmowebCLI()
    
    # Apply overrides
    if hasattr(args, 'postal') and args.postal:
        cli.config["postal_code"] = args.postal
    if hasattr(args, 'radius') and args.radius:
        cli.config["radius_km"] = args.radius
    if hasattr(args, 'max_price') and args.max_price:
        cli.config["max_price"] = args.max_price
    if hasattr(args, 'type') and args.type:
        cli.config["property_type"] = args.type
    
    if args.command == "search":
        result = cli.search(limit=args.limit)
    elif args.command == "check-new":
        result = cli.check_new(limit=args.limit)
    elif args.command == "analyze":
        result = cli.analyze(args.url)
    elif args.command == "analyze-full":
        result = cli.analyze_full(args.url, args.output_dir)
    elif args.command == "dismiss":
        result = cli.dismiss(args.id)
    elif args.command == "list-seen":
        result = cli.list_seen()
    else:
        parser.print_help()
        sys.exit(1)
    
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
