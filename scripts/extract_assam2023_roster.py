#!/usr/bin/env python3
"""Extract the authoritative Assam 2023 assembly-constituency roster (126 ACs:
number, name, reservation, parent Lok Sabha, district) from the ECI final
delimitation order, and write redelimited/assam2023_assembly_list.csv.

Vector polygons for these 126 ACs are NOT publicly available (the ECI provides
only village-level composition text and raster map plates), so this roster + the
AC->PC mapping is the machine-readable part that can be recovered.

Source PDF (~47 MB):
  https://www.eci.gov.in/Documents/Delimitation/DELIMITATIONASSAM_UPDATED.pdf
The roster is parsed from "PAPER-7" (Parliamentary constituencies and their extent
in terms of the new assembly constituencies).

Requires: poppler's `pdftotext` on PATH.
"""
import os, re, csv, subprocess, urllib.request, collections

HERE = os.path.dirname(__file__)
PDF_URL = "https://www.eci.gov.in/Documents/Delimitation/DELIMITATIONASSAM_UPDATED.pdf"
PDF = os.path.join(HERE, "assam_delim.pdf")
TXT = os.path.join(HERE, "assam_delim.txt")
OUT = os.path.join(HERE, "..", "redelimited", "assam2023_assembly_list.csv")

def ensure_text():
    if os.path.exists(TXT):
        return
    if not os.path.exists(PDF):
        print("downloading ECI order ...")
        req = urllib.request.Request(PDF_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as r, open(PDF, "wb") as f:
            f.write(r.read())
    subprocess.run(["pdftotext", "-layout", PDF, TXT], check=True)

def parse():
    lines = open(TXT).read().splitlines()
    # locate PAPER-7 (parliamentary constituencies x new assembly constituencies)
    start = next(i for i, l in enumerate(lines) if "PAPER - 7" in l or "PAPER -7" in l)
    sec = lines[start:start + 520]
    row = re.compile(r'(\d{1,3})-\s*([A-Za-z][A-Za-z().,&\'\-/ ]*?)(\((SC|ST)\))?\s{2,}')
    acs = {}; cur_pc = None
    for ln in sec:
        if any(s in ln for s in ("Grand Total", "%age", "DELIMITATION OF", "Page ")):
            continue
        toks = [(int(a), b.strip(), res or "") for a, b, c, res in row.findall(ln)]
        if not toks:
            continue
        nums = re.findall(r'\b\d{4,}\b', ln)
        parts = [p for p in ln.split("  ") if p.strip()]
        dist = parts[-1].strip() if parts and not re.search(r'\d', parts[-1]) else ""
        if len(toks) >= 2 and nums:
            cur_pc = toks[0]; ac = toks[1]
        elif len(toks) == 1 and not nums:
            cur_pc = toks[0]; continue
        else:
            ac = toks[0]
        if cur_pc and 1 <= ac[0] <= 126:
            acs[ac[0]] = (ac[1], ac[2], cur_pc[0], cur_pc[1], cur_pc[2], dist)
    return acs

if __name__ == "__main__":
    ensure_text()
    acs = parse()
    assert len(acs) == 126, f"expected 126 ACs, got {len(acs)}"
    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ac_no", "ac_name", "ac_type", "pc_no", "pc_name", "pc_type", "district"])
        for n in sorted(acs):
            nm, res, pn, pnm, pres, dist = acs[n]
            w.writerow([n, nm.title(), res, pn, pnm.title(), pres, dist.title()])
    res = collections.Counter(v[1] for v in acs.values())
    print(f"wrote {len(acs)} ACs -> {OUT}  (ST={res['ST']}, SC={res['SC']})")
