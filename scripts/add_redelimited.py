#!/usr/bin/env python3
"""Add the newest re-delimitations that post-date the 2008 delimitation:
  - Jammu & Kashmir 2022  : assembly (90) + Lok Sabha (5)
  - Ladakh 2022           : Lok Sabha (1)
  - Assam 2023            : Lok Sabha (14)

Source GeoJSONs (in redelimited/source/) are from shijithpk/2024_maps_supplement.
Assam's 2023 *assembly* (126, redrawn) is NOT openly available and is not included.

Output matches the repo's standard schema (WGS84 shapefiles, per unit).
"""
import os, json, shapefile

OUT = os.path.join(os.path.dirname(__file__), "..", "redelimited")
SRC = os.path.join(OUT, "source")
WGS84_PRJ = ('GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",'
             '6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],'
             'UNIT["Degree",0.0174532925199433]]')
AC_FIELDS = [("ST_CODE","C",3,0),("ST_NAME","C",40,0),("AC_NO","N",4,0),
             ("AC_NAME","C",60,0),("AC_TYPE","C",3,0),("PC_NO","N",4,0),("PC_NAME","C",60,0)]
PC_FIELDS = [("ST_CODE","C",3,0),("ST_NAME","C",40,0),("PC_NO","N",4,0),
             ("PC_NAME","C",60,0),("PC_TYPE","C",3,0)]
NAME = {"U08":"Jammu & Kashmir","U09":"Ladakh","S03":"Assam"}

def rings(geom):
    """MultiPolygon/Polygon coords -> flat list of rings (each list of [x,y])."""
    out = []
    if geom["type"] == "Polygon":
        polys = [geom["coordinates"]]
    else:
        polys = geom["coordinates"]
    for poly in polys:
        for ring in poly:
            if len(ring) >= 3:
                out.append([[float(x), float(y)] for x, y, *_ in ring])
    return out

def write(path, fields, feats):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    w = shapefile.Writer(path, shapeType=shapefile.POLYGON)
    for f in fields: w.field(*f)
    for rec, rgs in feats:
        w.poly(rgs); w.record(*rec)
    w.close()
    open(path + ".prj", "w").write(WGS84_PRJ)

def load(name):
    return json.load(open(os.path.join(SRC, name)))["features"]

def build_jk_assembly():
    feats = []
    for ft in load("j_and_k_assembly_new_borders.geojson"):
        p = ft["properties"]; sid = p["seat_id"]
        if sid is None or sid > 90:   # drop the PoK placeholder (9999)
            continue
        feats.append(([ "U08", NAME["U08"], sid, (p["seat_name_en"] or "").strip(),
                        (p.get("sc_st_gen") or "").strip().upper(), None, "" ], rings(ft["geometry"])))
    write(os.path.join(OUT, "assembly", "U08_AC"), AC_FIELDS, feats)
    return len(feats)

def build_ls(name, code):
    feats = []
    for ft in load(name):
        p = ft["properties"]
        c = p["ls_seat_code"]
        if str(c) == "999":           # drop 'Rest of J&K' / 'Rest of Ladakh' PoK placeholders
            continue
        feats.append(([ code, NAME[code], int(c), (p["ls_seat_name"] or "").strip(), "" ], rings(ft["geometry"])))
    write(os.path.join(OUT, "parliamentary", f"{code}_PC"), PC_FIELDS, feats)
    return len(feats)

if __name__ == "__main__":
    print("J&K 2022 assembly :", build_jk_assembly())
    print("J&K 2022 LS       :", build_ls("j_and_k_ls_new_borders.geojson", "U08"))
    print("Ladakh 2022 LS    :", build_ls("ladakh_ls_new_borders.geojson", "U09"))
    print("Assam 2023 LS     :", build_ls("assam_ls_new_borders.geojson", "S03"))
