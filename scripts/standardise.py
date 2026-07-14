#!/usr/bin/env python3
"""Standardise pre-2008 (pre-delimitation) India constituency shapefiles.

- Parliamentary (PC) set is already WGS84 lon/lat -> passthrough geometry.
- Assembly (AC) set is in an unknown projected CRS with no .prj; each state is
  aligned to WGS84 by an axis-aligned affine that maps the state's native bbox
  onto the same state's PC (WGS84) bbox. This also corrects the misregistered
  S28 (Uttarakhand) file for free.

Output: per-state standardised shapefiles (+ .prj) and a national merge per layer.
"""
import os, glob, shapefile

REF = "/Users/Karthik/Documents/work/elections/geo/reference"
OUT = "/Users/Karthik/Documents/work/india-pre2008-constituency-maps"

WGS84_PRJ = ('GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",'
             '6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],'
             'UNIT["Degree",0.0174532925199433]]')

def titlecase(s):
    s = (s or "").strip()
    return s.title() if s.isupper() else s

def state_names():
    """ST_CODE -> Title Case state name, from the PC set (has ST_NAME)."""
    m = {}
    for shp in glob.glob(REF + "/PC_Data/States/*/*_PC.shp"):
        code = os.path.basename(shp)[:3]
        r = shapefile.Reader(shp, encoding="latin1", encodingErrors="replace")
        names = [f[0] for f in r.fields[1:]]
        rec = r.records()[0]
        m[code] = titlecase(rec[names.index("ST_NAME")])
    return m

STATES = state_names()

def num(v):
    try: return int(round(float(v)))
    except (TypeError, ValueError): return None

def affine_for(ac_bbox, pc_bbox):
    axmin, aymin, axmax, aymax = ac_bbox
    pxmin, pymin, pxmax, pymax = pc_bbox
    sx = (pxmax - pxmin) / (axmax - axmin)
    sy = (pymax - pymin) / (aymax - aymin)
    ox = pxmin - axmin * sx
    oy = pymin - aymin * sy
    return lambda x, y: (x * sx + ox, y * sy + oy)

def transform_shape(shape, fn):
    """Return (points, parts) with fn applied; keeps part structure."""
    pts = [fn(x, y) for (x, y) in shape.points]
    return pts, list(shape.parts)

def get(names, rec, key, default=None):
    return rec[names.index(key)] if key in names else default

def build_assembly():
    dst_dir = os.path.join(OUT, "assembly")
    os.makedirs(dst_dir, exist_ok=True)
    pc_bbox = {os.path.basename(p)[:3]: shapefile.Reader(p).bbox
               for p in glob.glob(REF + "/PC_Data/States/*/*_PC.shp")}
    national = shapefile.Writer(os.path.join(dst_dir, "india_assembly"), shapeType=shapefile.POLYGON)
    for f in [("ST_CODE","C",3,0),("ST_NAME","C",40,0),("AC_NO","N",4,0),
              ("AC_NAME","C",60,0),("AC_TYPE","C",3,0),("PC_NO","N",4,0)]:
        national.field(*f)
    manifest = []
    for shp in sorted(glob.glob(REF + "/AC_Data/States/*/*_AC.shp")):
        code = os.path.basename(shp)[:3]
        r = shapefile.Reader(shp, encoding="latin1", encodingErrors="replace")
        names = [fd[0] for fd in r.fields[1:]]
        fn = affine_for(r.bbox, pc_bbox[code])
        w = shapefile.Writer(os.path.join(dst_dir, f"{code}_AC"), shapeType=shapefile.POLYGON)
        for f in [("ST_CODE","C",3,0),("ST_NAME","C",40,0),("AC_NO","N",4,0),
                  ("AC_NAME","C",60,0),("AC_TYPE","C",3,0),("PC_NO","N",4,0)]:
            w.field(*f)
        n = 0
        for sr in r.iterShapeRecords():
            rec = sr.record
            row = [code, STATES.get(code, ""), num(get(names, rec, "AC_NO")),
                   titlecase(get(names, rec, "AC_NAME", "")),
                   (get(names, rec, "AC_TYPE", "") or "").strip().upper(),
                   num(get(names, rec, "PC_NO"))]
            pts, parts = transform_shape(sr.shape, fn)
            w.poly([pts[a:b] for a, b in zip(parts, parts[1:] + [len(pts)])])
            w.record(*row)
            national.poly([pts[a:b] for a, b in zip(parts, parts[1:] + [len(pts)])])
            national.record(*row)
            n += 1
        w.close()
        open(os.path.join(dst_dir, f"{code}_AC.prj"), "w").write(WGS84_PRJ)
        manifest.append((code, STATES.get(code, ""), n))
    national.close()
    open(os.path.join(dst_dir, "india_assembly.prj"), "w").write(WGS84_PRJ)
    return manifest

def build_parliamentary():
    dst_dir = os.path.join(OUT, "parliamentary")
    os.makedirs(dst_dir, exist_ok=True)
    national = shapefile.Writer(os.path.join(dst_dir, "india_parliamentary"), shapeType=shapefile.POLYGON)
    for f in [("ST_CODE","C",3,0),("ST_NAME","C",40,0),("PC_NO","N",4,0),
              ("PC_NAME","C",60,0),("PC_TYPE","C",3,0)]:
        national.field(*f)
    manifest = []
    for shp in sorted(glob.glob(REF + "/PC_Data/States/*/*_PC.shp")):
        code = os.path.basename(shp)[:3]
        r = shapefile.Reader(shp, encoding="latin1", encodingErrors="replace")
        names = [fd[0] for fd in r.fields[1:]]
        w = shapefile.Writer(os.path.join(dst_dir, f"{code}_PC"), shapeType=shapefile.POLYGON)
        for f in [("ST_CODE","C",3,0),("ST_NAME","C",40,0),("PC_NO","N",4,0),
                  ("PC_NAME","C",60,0),("PC_TYPE","C",3,0)]:
            w.field(*f)
        n = 0
        for sr in r.iterShapeRecords():
            rec = sr.record
            row = [code, STATES.get(code, ""), num(get(names, rec, "PC_NO") or get(names, rec, "PC_CODE")),
                   titlecase(get(names, rec, "PC_NAME", "")),
                   (get(names, rec, "PC_TYPE", "") or "").strip().upper()]
            parts = list(sr.shape.parts); pts = sr.shape.points
            rings = [pts[a:b] for a, b in zip(parts, parts[1:] + [len(pts)])]
            w.poly(rings); w.record(*row)
            national.poly(rings); national.record(*row)
            n += 1
        w.close()
        open(os.path.join(dst_dir, f"{code}_PC.prj"), "w").write(WGS84_PRJ)
        manifest.append((code, STATES.get(code, ""), n))
    national.close()
    open(os.path.join(dst_dir, "india_parliamentary.prj"), "w").write(WGS84_PRJ)
    return manifest

if __name__ == "__main__":
    ac = build_assembly()
    pc = build_parliamentary()
    print("ASSEMBLY: %d states, %d ACs" % (len(ac), sum(x[2] for x in ac)))
    print("PARLIAMENTARY: %d states, %d PCs" % (len(pc), sum(x[2] for x in pc)))
    import csv
    with open(os.path.join(OUT, "manifest.csv"), "w", newline="") as f:
        wr = csv.writer(f); wr.writerow(["st_code","st_name","layer","n_features"])
        for c, s, n in ac: wr.writerow([c, s, "assembly", n])
        for c, s, n in pc: wr.writerow([c, s, "parliamentary", n])
