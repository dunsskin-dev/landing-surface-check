"""Build the compact landing-facility dataset (facilities.json) from FAA NASR APT CSV files.

Usage: python -I build_data.py <csv_dir> <out_json>
"""
import csv, json, sys, collections, os

TYPES = {'A': 0, 'H': 1, 'C': 2, 'G': 3, 'U': 4, 'B': 5}


def _rows(src, name):
    with open(os.path.join(src, name), newline='', encoding='latin-1') as fh:
        yield from csv.DictReader(fh)


def _num(v, nd=None):
    v = (v or '').strip()
    if not v:
        return None
    try:
        x = float(v)
    except ValueError:
        return None
    if nd is None:
        return int(round(x))
    return round(x, nd)


def build(src, out):
    """Read APT_BASE/APT_RWY/APT_RWY_END CSVs from src, write compact JSON to out. Returns stats."""
    stats = collections.Counter()
    eff = None
    fac = {}
    for r in _rows(src, 'APT_BASE.csv'):
        eff = eff or r['EFF_DATE']
        status = r['ARPT_STATUS'].strip()
        stats['status_' + status] += 1
        stats['type_' + r['SITE_TYPE_CODE']] += 1
        if status == 'CP':  # permanently closed: not a landing surface
            continue
        lat, lon = _num(r['LAT_DECIMAL'], 5), _num(r['LONG_DECIMAL'], 5)
        if lat is None or lon is None:
            stats['no_coords'] += 1
            continue
        fac[r['SITE_NO']] = {
            'id': r['ARPT_ID'].strip(),
            'name': r['ARPT_NAME'].strip(),
            't': r['SITE_TYPE_CODE'].strip(),
            'city': r['CITY'].strip(),
            'st': r['STATE_CODE'].strip() or r['COUNTRY_CODE'].strip(),
            'use': r['FACILITY_USE_CODE'].strip(),
            'own': r['OWNERSHIP_TYPE_CODE'].strip(),
            'status': status,
            'lat': lat, 'lon': lon,
            'elev': _num(r['ELEV']),
            'icao': r['ICAO_ID'].strip(),
            'rw': collections.OrderedDict(),
        }

    for r in _rows(src, 'APT_RWY.csv'):
        f = fac.get(r['SITE_NO'])
        if not f:
            continue
        f['rw'][r['RWY_ID'].strip()] = {
            'len': _num(r['RWY_LEN']), 'wid': _num(r['RWY_WIDTH']),
            'surf': r['SURFACE_TYPE_CODE'].strip(), 'ends': []}

    for r in _rows(src, 'APT_RWY_END.csv'):
        f = fac.get(r['SITE_NO'])
        if not f:
            continue
        rw = f['rw'].get(r['RWY_ID'].strip())
        if rw is None:
            continue
        lat, lon = _num(r['LAT_DECIMAL'], 5), _num(r['LONG_DECIMAL'], 5)
        if lat is not None and lon is not None and -90 <= lat <= 90:
            rw['ends'].append((lat, lon))

    out_rows = []
    for f in fac.values():
        rws = []
        for rid, rw in f['rw'].items():
            geo = [c for pt in rw['ends'][:2] for c in pt]  # [] | [lat,lon] | [lat1,lon1,lat2,lon2]
            stats['rwy_geo_%d' % (len(geo) // 2)] += 1
            rws.append([rid, rw['len'], rw['wid'], rw['surf']] + geo)
        stats['facilities_out'] += 1
        out_rows.append([
            f['id'], f['name'], TYPES.get(f['t'], 0), f['city'], f['st'],
            f['use'], f['own'], 1 if f['status'] == 'CI' else 0,
            f['lat'], f['lon'], f['elev'], f['icao'], rws])

    out_rows.sort(key=lambda x: x[8])  # sorted by latitude: the page binary-searches on it
    y, m, d = eff.split('/')
    stats['eff'] = f'{y}-{m}-{d}'
    with open(out, 'w', encoding='utf-8') as fh:
        json.dump({'eff': stats['eff'], 'f': out_rows}, fh, separators=(',', ':'), ensure_ascii=False)
    stats['bytes'] = os.path.getsize(out)
    return stats


if __name__ == '__main__':
    for k, v in sorted(build(sys.argv[1], sys.argv[2]).items()):
        print(k, v)
