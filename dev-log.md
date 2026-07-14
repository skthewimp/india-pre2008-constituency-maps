# Dev log

Build log for the pre-2008 constituency map standardisation. Prompts (paraphrased,
PII stripped) plus the technical decisions and problems hit along the way.

## Prompts

1. "Found boundaries.in with pre-2008 assembly maps. I think I have pre-2008 shapefiles
   on my computer too - search for them and tabulate what we have."
2. "Let's work on the pre-2008 thing. Standardise the nomenclature of the whole thing.
   Include Lok Sabha (pre-2008 also). Make formats consistent and keep it in a folder.
   Then we'll put it on GitHub."
3. Two clarifying decisions made during the build:
   - AC georeferencing: **affine-fit to WGS84** (over keeping the native CRS or sourcing
     a clean set elsewhere).
   - Output structure: **per-state standardised files + national merge**, both layers.

## What we found

- 238 `.shp` files scattered across `Documents` / `Downloads`. Most were unrelated
  (roads, landuse, census, current-delimitation maps).
- The pre-2008 set lived in `elections/geo/reference/AC_Data` and `PC_Data`, built
  ~2004-05 (file mtimes), with the tell-tale `INDIAASSEM` lineage fields.
- Assembly: 30 state/UT files, 4,109 ACs. Parliamentary: 35 state/UT files, 543 PCs
  (543 being the pre-delimitation Lok Sabha total - a good sanity check).

## Problems and decisions

**Vintage, not feature count, is the tell.** Delimitation kept per-state seat totals
fixed, so you can't distinguish pre/post-2008 by counting. The 2004-05 build date plus
the `INDIAASSEM` field lineage is what identifies these as pre-delimitation.

**The assembly set was not georeferenced.** No `.prj` on any file, and the coordinates
were in an unknown projected system - Karnataka and Maharashtra both had bounding boxes
around x=-12, y=1, i.e. overlapping, i.e. not a real map. The parliamentary set, by
contrast, was clean WGS84.

**Global affine was too coarse.** First attempt: fit one affine over the whole country
using per-state bbox corners as control points. Residuals were mean 0.2 deg (~22 km),
max 0.58 deg. The source projection isn't linear in lat-long, so a single affine smears.

**Per-state bbox alignment worked.** Final approach: for each state, map its assembly
bbox onto the same state's parliamentary (WGS84) bbox with an axis-aligned affine. Each
state lands on its true extent; residual is only the within-state projection curvature,
which is small. Bonus: the misregistered S28 (Uttaranchal) self-corrects, since its own
bbox maps onto its own correct extent.

**Encoding.** The `.dbf` files aren't UTF-8. Read with `latin1` + replace. The Hindi
name fields (`AC_HNAME` / `PC_HNAME`) are in a legacy non-Unicode font encoding
(Kruti-Dev / ISCII style) and render as garbage - dropped, not worth reverse-engineering.

**Dropped columns.** `AC_HNAME`/`PC_HNAME` (garbled), `PARTY` (ambiguous vintage - a
boundary reference file shouldn't ship possibly-mislabelled results), plus native
`AREA`/`PERIMETER` (in meaningless projection units after transform).

**Kept period names on purpose.** Orissa, Uttaranchal, Pondicherry - the 2004 names.
Modernising them would misrepresent the era the data is from.

## Tooling notes

- `ogrinfo` on this machine is broken (missing `libre2` dependency via the Arrow build),
  so GDAL was out. Used **pyshp** (pure Python) for all reading/writing and **numpy**
  only for the throwaway global-affine residual check. Install is `pip install pyshp` -
  no C toolchain needed, which is also why the rebuild is painless for anyone else.
- `pip` here is uv-managed; needed a `uv venv` + `uv pip install` to get pyshp/numpy.
- QA: rendered the transformed assembly fill under the parliamentary outlines with
  matplotlib and eyeballed it. Reads as India, layers align to within the stated
  tolerance. Saved as `docs/preview.png`.

## Output

- `assembly/` - 30 per-state `*_AC` shapefiles + `india_assembly` merge.
- `parliamentary/` - 35 per-state `*_PC` shapefiles + `india_parliamentary` merge.
- All WGS84 with `.prj`. Standard schemas (see README).
- `manifest.csv` - per-state feature counts.
- `scripts/standardise.py` - the full reproducible build.
