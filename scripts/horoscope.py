#!/usr/bin/env python3
"""Personal daily horoscope based on natal chart transits.
Reads birth data from environment variables.
Outputs compact transit data for AI interpretation.
"""

import os, warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from kerykeion import AstrologicalSubject
from datetime import datetime, timezone, timedelta

# Birth data from environment
BIRTH_NAME = os.environ["BIRTH_NAME"]
BIRTH_YEAR = int(os.environ["BIRTH_YEAR"])
BIRTH_MONTH = int(os.environ["BIRTH_MONTH"])
BIRTH_DAY = int(os.environ["BIRTH_DAY"])
BIRTH_HOUR = int(os.environ["BIRTH_HOUR"])
BIRTH_MINUTE = int(os.environ["BIRTH_MINUTE"])
BIRTH_CITY = os.environ["BIRTH_CITY"]
BIRTH_NATION = os.environ.get("BIRTH_NATION", "BE")
BIRTH_TZ = os.environ.get("BIRTH_TZ", "Europe/Brussels")
LAT = float(os.environ["BIRTH_LAT"])
LON = float(os.environ["BIRTH_LON"])
PLANETS = ['sun','moon','mercury','venus','mars','jupiter','saturn','uranus','neptune','pluto']
SIGN_NL = {'Ari':'Ram','Tau':'Stier','Gem':'Tweelingen','Can':'Kreeft','Leo':'Leeuw','Vir':'Maagd',
           'Lib':'Weegschaal','Sco':'Schorpioen','Sag':'Boogschutter','Cap':'Steenbok','Aqu':'Waterman','Pis':'Vissen'}
SYM = {'Ari':'♈','Tau':'♉','Gem':'♊','Can':'♋','Leo':'♌','Vir':'♍','Lib':'♎','Sco':'♏','Sag':'♐','Cap':'♑','Aqu':'♒','Pis':'♓'}

def s(sign):
    return f"{SYM.get(sign,'')}{SIGN_NL.get(sign,sign)}"

natal = AstrologicalSubject(BIRTH_NAME, BIRTH_YEAR, BIRTH_MONTH, BIRTH_DAY, BIRTH_HOUR, BIRTH_MINUTE,
    lat=LAT, lng=LON, city=BIRTH_CITY, nation=BIRTH_NATION, tz_str=BIRTH_TZ)

now = datetime.now(timezone.utc)
transit = AstrologicalSubject("Now", now.year, now.month, now.day, now.hour, now.minute,
    lat=LAT, lng=LON, city=BIRTH_CITY, nation=BIRTH_NATION, tz_str=BIRTH_TZ)

def p(subj, name): return getattr(subj, name)

# Aspects
ASPECTS = {"conjunctie":(0,8), "oppositie":(180,8), "trigon":(120,6), "vierkant":(90,6), "sextiel":(60,5)}

aspects = []
for tn in PLANETS:
    tp = p(transit, tn)
    # vs natal planets
    for nn in PLANETS:
        np_ = p(natal, nn)
        diff = abs(tp.abs_pos - np_.abs_pos)
        if diff > 180: diff = 360 - diff
        for aname, (angle, orb) in ASPECTS.items():
            ex = abs(diff - angle)
            if ex <= orb:
                aspects.append((tp.name, aname, np_.name, ex, "natal"))
    # vs ascendant
    diff = abs(tp.abs_pos - natal.first_house.abs_pos)
    if diff > 180: diff = 360 - diff
    for aname, (angle, orb) in ASPECTS.items():
        ex = abs(diff - angle)
        if ex <= orb:
            aspects.append((tp.name, aname, "Ascendant", ex, "natal"))

aspects.sort(key=lambda x: x[3])

# Moon sign changes (check every 2h for next 24h)
moon_signs = []
for h in range(0, 25, 2):
    t = now + timedelta(hours=h)
    ms = AstrologicalSubject("M", t.year, t.month, t.day, t.hour, t.minute,
        lat=LAT, lng=LON, city=BIRTH_CITY, nation=BIRTH_NATION, tz_str=BIRTH_TZ)
    moon_signs.append((h, ms.moon.sign, ms.moon.position))

# Output
print(f"HOROSCOOP DATA — {now.strftime('%A %d %B %Y')}")
print(f"Natal: Zon {s(natal.sun.sign)} | Asc {s(natal.first_house.sign)} | Maan {s(natal.moon.sign)}")
print()

print("TRANSITS VANDAAG:")
for name in PLANETS:
    obj = p(transit, name)
    retro = " (retrograde)" if obj.retrograde else ""
    print(f"  {obj.name}: {obj.position:.1f}° {s(obj.sign)}{retro}")

print()
print("TRANSIT-NATAL ASPECTEN (gesorteerd op exactheid):")
seen = set()
for tname, asp, nname, ex, typ in aspects:
    key = (tname, asp, nname)
    if key in seen: continue
    seen.add(key)
    strength = "EXACT" if ex < 1 else ("sterk" if ex < 3 else "actief")
    print(f"  [{strength}] Transit {tname} {asp} natal {nname} (orb {ex:.1f}°)")

# Moon movement
print()
prev_sign = None
print("MAAN VERLOOP (komende 24u):")
for h, sign, pos in moon_signs:
    if sign != prev_sign:
        t_local = now + timedelta(hours=h)
        # Show in Brussels time (UTC+1 or +2)
        print(f"  +{h}u: Maan naar {s(sign)} ({pos:.1f}°)")
    prev_sign = sign
