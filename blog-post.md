# The old constituencies nobody keeps around

A few days ago I stumbled onto boundaries.in, which has India's pre-2008 assembly
maps, and it reminded me that I've been sitting on a pile of old shapefiles for years.
Somewhere in the `elections/geo/reference` folder on my laptop - the kind of folder you
copy from machine to machine and never open - there was a full set of pre-delimitation
constituency maps. I went looking. They were there. And they were a mess.

For the uninitiated: in 2008 India redrew almost all its electoral boundaries. The
delimitation exercise kept the *number* of seats per state fixed, but moved the lines.
So a constituency called "Bangalore South" in 2004 and one called "Bangalore South" in
2009 are not the same shape on the ground. This matters more than people assume. If you
want to map the 2004 Lok Sabha result, or any state election before 2008, and you drape
it over today's constituencies, you get a map that is confidently wrong. The current
boundaries are everywhere - ECI, various GitHub repos, half a dozen data journalism
projects. The old ones have quietly disappeared.

What I had was two sets. The Lok Sabha set (543 constituencies, which is the giveaway -
543 is the old number) was clean. Proper WGS84, latitude and longitude where you'd
expect them, Uttar Pradesh sitting at 77-84 degrees east like it should.

The assembly set was another story. I ran the bounding boxes and Karnataka came out at
x between -12.6 and -12.2, y around 1. Maharashtra came out at almost exactly the same
coordinates. Two states can't occupy the same patch of the plane, so this wasn't a real
map - it was some projected coordinate system with no `.prj` file to tell me which one.
And Uttaranchal (as it was still called then) had wandered off to its own corner
entirely, clearly misregistered.

So the interesting problem was: how do you get 30 state files, each in some unknown
grid, into honest latitude-longitude?

The trick I used is almost embarrassingly simple. I had the Lok Sabha maps in correct
coordinates, and both sets cover the same states - a state's outline is a state's
outline whether you build it up from assembly seats or from parliamentary seats. So for
each state, I took its assembly bounding box and stretched it to sit exactly on top of
its parliamentary bounding box. An axis-aligned affine transform per state, fit on
nothing more than the corners. The nice side effect: Uttaranchal's misregistration
fixed itself, because its own bounding box got mapped onto its own correct extent along
with everyone else's.

I'll be honest about what this buys you and what it doesn't. It's approximate. It's
accurate to roughly state level, which is fine for choropleths and for overlaying old
results, and it is not survey-grade - if you zoom into the northwest you can see the
assembly fill and the Lok Sabha outline disagree by a few kilometres in places. I first
tried fitting one single affine for the whole country, and the average error was about
0.2 degrees, which is 20-odd kilometres. That's because the underlying projection isn't
actually a linear function of lat-long, so a global fit leaves you with a smeared map.
Doing it per-state cut the error down to the point where the QA render looks like India
and the two layers sit on each other properly. Good enough for the job, and I've said
so plainly in the README rather than pretending it's precise.

The rest was standardisation, which is the unglamorous 80% of any data project. The
files had thirteen different columns between them, including a Hindi-name field that
turned out to be in some legacy Kruti-Dev-style font encoding that renders as pure
garbage in Unicode, and a `PARTY` column of uncertain vintage that I didn't trust enough
to publish. I threw those out and kept the fields that actually identify a constituency -
state, number, name, type, and for assembly seats the parent Lok Sabha number. One
schema for assembly, one for parliamentary, title-cased names, WGS84 with a proper
`.prj` on every file, per-state files plus a national merge.

One small thing I decided to keep rather than "fix": the names. The source says Orissa,
not Odisha. Uttaranchal, not Uttarakhand. Pondicherry, not Puducherry. Every instinct
in a cleaning pipeline is to modernise these, but this is a pre-2008 dataset and those
were the names in 2004. Correcting them would be quietly lying about when the data is
from.

The whole thing is one Python script using pyshp - no GDAL, no geopandas, nothing that
needs a C toolchain to install - so anyone can rebuild it from the source in one command.
It's up on GitHub now. If you ever need to map an old Indian election properly, this is
the layer you were missing.
