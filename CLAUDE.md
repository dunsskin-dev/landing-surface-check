# Landing Surface Check: project notes

- **Live site:** https://dunsskin-dev.github.io/landing-surface-check/
- **Repository:** https://github.com/dunsskin-dev/landing-surface-check (public, GitHub account `dunsskin-dev`). Everything committed here is public.

## What it is

A single web page (`index.html`) that drone pilots for Air Operations Inc use on their phones:

1. Enter GPS coordinates and press **Check**. The result turns **red: "Does not fall under national waiver"** if any FAA-listed landing surface is within 2 NM, or **green: "Clear to fly under national waiver"** if none is. This implements special provision 2.h(3) of COA 2025-P107-ESA-26380 (no operating within 2 NM of a landing surface of an airport, heliport or seaplane base).
2. Fill in the **Flight notification** section and send it to Air Ops by text or email.

The coordinate box also takes a **street address**. Any line that isn't coordinates but contains words is looked up with OpenStreetMap's free Nominatim service (`nominatim.openstreetmap.org`, no key, limited to U.S. states and territories). The page then shows "Address found: ..." so the pilot can confirm the match.
- Lookups follow Nominatim's usage policy: at most one request a second, results cached per page load, and attribution in the footer.
- A match to a town or anything larger (`place_rank` ≤ 20) is refused.
- A ZIP code, park or neighborhood match (21 to 25) is checked from the area's center point, with a note saying so.
- A street-level match (26 to 29) also gets a note.

The US Census geocoder can't be used, because it doesn't send CORS headers.

The **Open this point in Maps** link drops a pin in the device's maps app: a `geo:` link on Android, Apple Maps on iPhone and iPad, and Google Maps on a computer.

## Decisions the user has made (keep these)

- Black background; red and green as the only accent colors. Single dark theme.
- Nautical miles only, with no statute-mile option. The radius defaults to 2 NM and stays editable.
- The coordinate box is blank every time the page opens. A **Clear** button empties it.
- The Flight notification section sits directly under the coordinate box and contains:
  - **Site ID:** placeholder text "Site ID".
  - **Lat/Long:** read-only, filled in from the checked coordinates.
  - **COA #:** read-only, preset to 2025-P107-ESA-26380, with a link to the PDF.
  - **Date and Start time:** both set to the current moment when Check is pressed.
  - **Est. time on site:** a dropdown. There is no end-time field.
  - **Pilot name, phone, email and Remote ID:** remembered per device in localStorage key `lsc-pilot`. Remote ID has a **?** that shows the DJI Fly steps.
  - **Text Air Ops, Email Air Ops and Copy** buttons.
- Air Ops contacts, from the memo in the PDF and published with the user's OK:
  - Text 913.219.1370.
  - Email airopsinc@outlook.com.
  - Responsible person: Michael den Hartog, (669) 247-6776 ext. 1.
  - COA effective 9/30/2025 to 9/29/2027.
- **Every type of landing surface counts** (owner's decision): airports, heliports, seaplane bases, gliderports, ultralight parks and balloonports, public and private. They always count; the facility-type checkboxes were removed so pilots can't switch any off.

## Files

| Path | Purpose |
| --- | --- |
| `index.html` | The whole app: inline CSS and JS, fonts from Google Fonts. |
| `facilities.json` | Generated FAA data. Don't hand-edit. |
| `tools/update_data.py` | Fetches the current FAA 28-day cycle and rebuilds `facilities.json` if newer. |
| `tools/build_data.py` | CSV to JSON converter used by `update_data.py`. |
| `coa/AOI-2025-P107-ESA-26380-Nationwide.pdf` | Air Ops memo (page 1) plus the COA (pages 2 to 4). |
| `.github/workflows/update-and-deploy.yml` | Weekly data check (Thursdays 14:17 UTC) and GitHub Pages deploy. Also deploys on every push to `main`. |

`facilities.json` rows are sorted by latitude:
`[id, name, type(0 airport, 1 heliport, 2 seaplane base, 3 gliderport, 4 ultralight, 5 balloonport), city, state, use(PU/PR), ownership, closedIndefinitely(0/1), lat, lon, elevFt, icao, runways]`.
Each runway is `[id, lenFt, widthFt, surface, lat1, lon1, lat2, lon2]`; the coordinates are present only when the FAA has them.

FAA source: `https://nfdc.faa.gov/webContent/28DaySub/extra/DD_Mon_YYYY_APT_CSV.zip` (NASR 28-day subscription). Cycles take effect on Thursdays. 2026-10-29 is a known cycle date.

## Making changes on this computer (Windows)

- Git and GitHub CLI are installed but not on the agent shell's PATH. Prefix commands with:
  `$env:PATH = 'C:\Program Files\Git\cmd;C:\Program Files\GitHub CLI;' + $env:PATH`
  `gh` is signed in as `dunsskin-dev`.
- **Test locally:** run `python -I -m http.server 8766 --bind 127.0.0.1 --directory "<this folder>"`, then open http://localhost:8766/.
- **Publish:** commit to `main` and push. The workflow deploys in about 30 seconds. Check the live URL with `?v=<n>` added to skip the cache.
- **localStorage keys:** `lsc-settings-v2` (radius and filters), `lsc-pilot` (pilot details). Don't rename them without a reason, or users lose their saved info.
- **Restore points:** git tags. `v1.0` (2026-11-08) is the version the user signed off on, with every feature above. To see it, run `git show v1.0:index.html`. To roll the live site back, restore the files from the tag, then commit and push.
- **New or renewed COA:** replace the PDF in `coa/` and update the `COA` constant (id, start, end), the COA # field value, the PDF link text, and the effective dates in the contact line in `index.html`.
