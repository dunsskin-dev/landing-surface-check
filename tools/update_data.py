"""Refresh facilities.json from the FAA's latest 28-day NASR airport data.

Run from anywhere:  python -I tools/update_data.py [--force] [--out PATH]

Prints exactly one status line last:
  UP_TO_DATE <eff>             facilities.json already holds the current FAA cycle
  UPDATED <old> -> <new> <n>   facilities.json was rebuilt with n facilities
  NOT_AVAILABLE <eff> <why>    the FAA file for the current cycle couldn't be fetched (exit 2)
  FAILED <why>                 the download or build looked wrong; facilities.json untouched (exit 1)
"""
import datetime as dt, importlib.util, json, os, shutil, sys, tempfile, time, urllib.request, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = ROOT / 'facilities.json'
ANCHOR = dt.date(2026, 10, 29)          # a known FAA 28-day cycle effective date
MIN_FACILITIES = 18000                  # sanity floor: the national file has ~19,400
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) LandingSurfaceCheck/1.0'
NEEDED = ('APT_BASE.csv', 'APT_RWY.csv', 'APT_RWY_END.csv')


def current_cycle(today):
    """Latest 28-day cycle effective on or before today."""
    return ANCHOR + dt.timedelta(days=28 * ((today - ANCHOR).days // 28))


def cycle_url(d):
    return 'https://nfdc.faa.gov/webContent/28DaySub/extra/%02d_%s_%d_APT_CSV.zip' % (d.day, d.strftime('%b'), d.year)


def load_builder():
    spec = importlib.util.spec_from_file_location('build_data', HERE / 'build_data.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fetch(url, dest):
    last = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=120) as r, open(dest, 'wb') as fh:
                shutil.copyfileobj(r, fh)
            return
        except Exception as e:  # network hiccup or FAA 5xx: retry a couple of times
            last = e
            time.sleep(10 * (attempt + 1))
    raise last


def main():
    args = sys.argv[1:]
    force = '--force' in args
    out = Path(args[args.index('--out') + 1]) if '--out' in args else DATA

    old = None
    try:
        old = json.load(open(DATA, encoding='utf-8')).get('eff')
    except Exception:
        pass
    cyc = current_cycle(dt.date.today())
    if old == cyc.isoformat() and not force:
        print('UP_TO_DATE', old)
        return 0

    work = Path(tempfile.mkdtemp(prefix='faa_apt_'))  # downloads stay in their own fresh folder
    try:
        zpath, xdir = work / 'apt.zip', work / 'csv'
        try:
            fetch(cycle_url(cyc), zpath)
        except Exception as e:
            print('NOT_AVAILABLE', cyc.isoformat(), repr(e)[:200])
            return 2
        with zipfile.ZipFile(zpath) as z:
            names = {Path(n).name: n for n in z.namelist()}
            missing = [n for n in NEEDED if n not in names]
            if missing:
                print('FAILED zip is missing', ','.join(missing))
                return 1
            xdir.mkdir()
            for n in NEEDED:
                with z.open(names[n]) as src, open(xdir / n, 'wb') as dst:
                    shutil.copyfileobj(src, dst)
        tmp_out = work / 'facilities.json'
        stats = load_builder().build(str(xdir), str(tmp_out))
        n = stats['facilities_out']
        if n < MIN_FACILITIES:
            print('FAILED only', n, 'facilities in the new file; keeping the old data')
            return 1
        if stats['eff'] != cyc.isoformat():
            print('FAILED file is for', stats['eff'], 'but expected', cyc.isoformat())
            return 1
        shutil.copyfile(tmp_out, str(out) + '.tmp')
        os.replace(str(out) + '.tmp', out)
        print('UPDATED', old, '->', stats['eff'], n)
        return 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == '__main__':
    sys.exit(main())
