# Landing Surface Check

Enter GPS coordinates and see whether any FAA-listed landing surface (airport, heliport, seaplane base, gliderport, ultralight park or balloonport, public or private) is within 2 nautical miles (the radius and unit can be changed on the page):

- **Red: "Does not fall under national waiver"** means one or more landing surfaces are within the radius.
- **Green: "Clear to fly under national waiver"** means none are.

Covers all 50 states and U.S. territories. Distance is measured to the nearest runway or helipad where the FAA has its coordinates, otherwise to the facility's reference point. Not for navigation.

## Files

| File | What it is |
| --- | --- |
| `index.html` | The whole app: one web page. |
| `facilities.json` | FAA landing facility data the page loads (about 19,400 sites). |
| `tools/update_data.py` | Downloads the FAA's current 28-day NASR airport file and rebuilds `facilities.json` when it's newer. |
| `tools/build_data.py` | Converts the FAA CSV files into `facilities.json`. Used by `update_data.py`. |
| `.github/workflows/update-and-deploy.yml` | Weekly data check and publishing to GitHub Pages. |

## How the data stays current

Every Thursday, GitHub Actions runs `tools/update_data.py`. The FAA publishes new data every 28 days, so most weeks nothing changes. When a new cycle is out, the workflow commits the new `facilities.json` and republishes the site. The data date is shown at the top of the page.

To run the check right away: **Actions** tab → **Update FAA data and publish** → **Run workflow**.

If the FAA site is down during a run, the site keeps the previous data and the next week's run tries again.

## Data source

FAA National Airspace System Resources (NASR) 28-day subscription, airport CSV files: <https://www.faa.gov/air_traffic/flight_info/aeronav/aero_data/NASR_Subscription/>
