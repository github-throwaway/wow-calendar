#!/usr/bin/env python3
"""Baut aus dem Eventkalender von ludwigshafen-wow.de eine einzige .ics-Datei.

Nutzt die Einzeltermin-Exporte der Website (/feed/calendar/?id=...) und
sammelt die Event-IDs über die "Mehr laden"-Schnittstelle des Kalenders.
Aufruf: python3 wow_kalender.py [ausgabe.ics]
"""
import json, re, sys, time, urllib.request
from datetime import datetime, timezone

BASE = "https://ludwigshafen-wow.de"
GRID_ID = 45  # Veranstaltungskalender auf der Startseite
UA = {"User-Agent": "wow-kalender-abo/1.0 (privater Kalender-Export)"}


def http(url, data=None):
    req = urllib.request.Request(url, data=data, headers={**UA, **({"Content-Type": "application/json"} if data else {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def event_ids():
    ids, offset, total = [], 0, None
    body = json.dumps({"id": GRID_ID, "facets": [1], "is_main_query": False, "permalink": BASE + "/"}).encode()
    while total is None or offset < total:
        url = f"{BASE}/wp-json/wpgb/v2/filter/?action=refresh" + (f"&_mehr_laden={offset}" if offset else "")
        d = json.loads(http(url, body))
        total = d.get("total", 0)
        found = re.findall(r"wpgb-post-(\d+)", d.get("posts", ""))
        if not found:
            break
        ids += [i for i in found if i not in ids]
        offset += len(found)
    return ids


def fold(line):
    out, b = [], line.encode()
    while len(b) > 75:
        cut = 75 if not out else 74
        while (b[cut] & 0xC0) == 0x80:  # UTF-8-Zeichen nicht zerschneiden
            cut -= 1
        out.append(b[:cut].decode()); b = b[cut:]
    out.append(b.decode())
    return "\r\n ".join(out)


PROP = re.compile(
    r"^(?:BEGIN|END|DTSTART|DTEND|DTSTAMP|UID|SUMMARY|DESCRIPTION|LOCATION|URL|CATEGORIES|STATUS|"
    r"CREATED|LAST-MODIFIED|SEQUENCE|ORGANIZER|GEO|CLASS|TRANSP|ATTACH|RRULE|PRIORITY|X-[A-Z0-9-]+)[;:]"
)


def logical_lines(text):
    """Entfaltet Zeilen und repariert rohe Zeilenumbrüche in Textfeldern.

    Die Einzelexporte der Website enthalten teils echte Zeilenumbrüche mitten in
    DESCRIPTION. Solche Zeilen beginnen ohne Eigenschaftsnamen und machen die
    Datei ungültig (iPhone lehnt das Abo dann ab). Sie werden als "\\n" an den
    vorherigen Wert angehängt.
    """
    out = []
    for l in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if not l.strip():
            continue
        if l[0] in " \t" and out:
            out[-1] += l[1:]
        elif PROP.match(l) or not out:
            out.append(l)
        else:
            out[-1] += "\\n" + l
    return out


def vevent(ics):
    m = re.search(r"BEGIN:VEVENT(.*?)END:VEVENT", ics, re.S)
    if not m:
        return None
    body = re.sub(r"BEGIN:VALARM.*?END:VALARM", "", m.group(1), flags=re.S)  # keine 100 Erinnerungen
    lines = [l for l in logical_lines(body) if not l.startswith("TZID:")]
    # Manche Termine haben auf der Website keine saubere Uhrzeit (Startzeit = Exportzeitpunkt,
    # Ende 1970). Die werden zu ganztägigen Terminen am richtigen Tag.
    start = next((l for l in lines if l.startswith("DTSTART")), "")
    end = next((l for l in lines if l.startswith("DTEND")), "")
    ms, me = re.search(r":(\d{8})T(\d{6})", start), re.search(r":(\d{8})T", end)
    if ms and (not ms.group(2).endswith("00") or (me and me.group(1) < ms.group(1))):
        lines = [l for l in lines if not l.startswith(("DTSTART", "DTEND"))]
        lines.insert(0, f"DTSTART;VALUE=DATE:{ms.group(1)}")
    return ["BEGIN:VEVENT"] + [fold(l) for l in lines] + ["END:VEVENT"]


VTIMEZONE = """BEGIN:VTIMEZONE
TZID:Europe/Berlin
BEGIN:STANDARD
TZOFFSETFROM:+0200
TZOFFSETTO:+0100
TZNAME:CET
DTSTART:19701025T030000
RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU
END:STANDARD
BEGIN:DAYLIGHT
TZOFFSETFROM:+0100
TZOFFSETTO:+0200
TZNAME:CEST
DTSTART:19700329T020000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU
END:DAYLIGHT
END:VTIMEZONE""".split("\n")


def main(out="ludwigshafen-wow.ics"):
    ids = event_ids()
    print(f"{len(ids)} Veranstaltungen gefunden", file=sys.stderr)
    events = []
    for i in ids:
        try:
            ev = vevent(http(f"{BASE}/feed/calendar/?id={i}"))
            if ev:
                events.append(ev)
        except Exception as e:
            print(f"  ID {i} übersprungen: {e}", file=sys.stderr)
        time.sleep(0.3)  # Server schonen
    cal = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//wow-kalender-abo//DE", "CALSCALE:GREGORIAN",
           "METHOD:PUBLISH", "X-WR-CALNAME:Ludwigshafen WOW", "X-WR-TIMEZONE:Europe/Berlin",
           "REFRESH-INTERVAL;VALUE=DURATION:PT12H", "X-PUBLISHED-TTL:PT12H"] + VTIMEZONE
    for ev in events:
        cal += ev
    cal.append("END:VCALENDAR")
    with open(out, "w", encoding="utf-8", newline="") as f:
        f.write("\r\n".join(cal) + "\r\n")
    print(f"{len(events)} Termine in {out} geschrieben", file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:2])
