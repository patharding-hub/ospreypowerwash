#!/usr/bin/env python3
"""Generate the service and town pages, the sitemap and robots.txt.

The home page (index.html) is hand-maintained; everything else is generated
from the content below so the nav, footer and markup never drift apart. The
nav and footer are lifted out of index.html at build time for the same reason
-- change them there and they change everywhere.

Run from the project root:  python build.py
"""
import html
import os
import re

SITE = 'https://ospreypowerwash.com'
BIZ = 'Osprey Power Wash'
LEGAL = 'Tidal Wash LLC'
PHONE_PRETTY = '(609) 780-2766'
PHONE_E164 = '+16097802766'
EMAIL = 'contact@ospreypowerwash.com'
INSTAGRAM = 'https://www.instagram.com/ospreypowerwash/'

# --------------------------------------------------------------------------
# SERVICES
# --------------------------------------------------------------------------
SERVICES = [
    dict(
        slug='house-washing',
        nav='House Washing',
        h1=('HOUSE WASHING', 'AND SOFT WASHING'),
        title='House Washing & Soft Washing in South Jersey',
        desc='Soft wash house cleaning across South Jersey. Removes algae, '
             'mildew and that grey-green film from vinyl, cedar shake, stucco '
             'and brick. Instant online quote.',
        image='house-washing.jpg',
        lead='The grey-green film down the side of your house is not dirt, and hosing it '
             'will not shift it. It is algae, it is alive, and it is feeding on moisture '
             'from humidity and rain. South Jersey supplies plenty of both.',
        body=[
            ('What soft washing actually means', [
                'Soft washing runs at garden-hose pressure. The work is done by a cleaning '
                'solution that kills the growth rather than by force, and that is the whole '
                'point: blasting knocks the green off the surface, but the roots stay and it '
                'comes back within the season. Kill it and the house stays clean far longer.',
                'It also means the wall itself is left alone. High pressure on siding can '
                'damage vinyl and aluminum over time, beating up the vinyl and sometimes '
                'cracking it, and removing the paint from an aluminum surface. Soft washing '
                'treats the algae and the dirt without harming the surface underneath.',
            ]),
            ('Surfaces we clean this way', [
                'Vinyl and insulated vinyl, cedar shake and clapboard, stucco and dryvit, '
                'brick, fiber cement and older aluminum siding. Each takes a different mix '
                'and a different dwell time, which is most of what twenty years teaches you.',
                'Shaded elevations are always the worst. On most houses the north wall and '
                'anything under a tree line will be a shade darker than the rest, and those '
                'are the walls that make the difference when the job is done.',
            ]),
            ('What it costs', [
                'House washing is priced on the footprint of the building and the number of '
                'stories, with the siding material adjusting the rate. You can measure your '
                'own house off the satellite view in the estimator and see the price on '
                'screen, no visit or sales call necessary.',
            ]),
        ],
    ),
    dict(
        slug='roof-washing',
        nav='Roof Washing',
        h1=('ROOF WASHING', 'WITHOUT THE DAMAGE'),
        title='Roof Washing & Black Streak Removal in South Jersey',
        desc='Low-pressure roof soft washing across South Jersey. Removes black '
             'streaks, moss and lichen from shingle, metal and cedar shake roofs '
             'without stripping granules.',
        image='roof-washing.jpg',
        lead='Those black streaks running down your shingles are a bacteria called '
             'Gloeocapsa magma. It lives on the limestone filler in asphalt shingles, and '
             'damp coastal air is close to ideal for it.',
        body=[
            ('Why a roof is never pressure washed', [
                'Asphalt shingles are protected by a layer of mineral granules. Pressure '
                'strips them, and once they are gone the shingle is exposed and its life is '
                'shortened. A roof cleaned with pressure can look excellent for a season and '
                'cost you years.',
                'Roof work is therefore soft wash only: low pressure, the right solution, and '
                'patience. The streaks lift and rinse away, and the roof is not aged in the '
                'process. Shingle manufacturers say the same thing in their own warranty '
                'documents.',
            ]),
            ('Moss and lichen are a different problem', [
                'Moss holds water against the shingle and lifts its edges. Lichen roots into '
                'the surface and leaves a mark even after it dies. Both need treating rather '
                'than scraping, and both are worth catching early, because neither one is '
                'purely cosmetic once it has taken hold.',
            ]),
            ('Roofs we work on', [
                'Asphalt and architectural shingle, standing seam and corrugated metal, cedar '
                'shake, and terracotta or concrete tile. Pricing is by roof area and pitch, '
                'since a steep roof is slower and more careful work than a shallow one.',
            ]),
        ],
    ),
    dict(
        slug='driveway-patio-cleaning',
        nav='Driveways & Patios',
        h1=('DRIVEWAYS, WALKS', 'AND PATIOS'),
        title='Driveway, Walkway & Patio Cleaning in South Jersey',
        desc='Pressure washing for concrete, paver and brick driveways, walkways '
             'and patios across South Jersey. Salt scale, oil, moss and ground-in '
             'grime removed.',
        image='paver-walkway.jpg',
        lead='Concrete is the one place high pressure genuinely belongs, and the one place '
             'a careless job shows for years afterwards.',
        body=[
            ('No zebra stripes', [
                'Cleaning a drive with a wand alone leaves overlap marks, and on concrete '
                'those stripes are permanent until the whole slab is redone. The work is done '
                'with a surface cleaner, which keeps the pressure even across the full width '
                'and gives you one consistent finish rather than the pattern of how somebody '
                'walked.',
            ]),
            ('What comes off', [
                'Salt scale from winter, rust marks, tire rubber, the moss that creeps in at '
                'the joints and edges, and the general grey that arrives so slowly nobody '
                'notices until it is gone. What comes back is concrete that looks new again, '
                'and the difference shows from the street.',
            ]),
            ('Pavers take less pressure', [
                'Pavers are cleaned with minimal pressure, to preserve the polymeric sand in '
                'the joints that holds them in place. Concrete can take the full force of a '
                'surface cleaner; pavers are washed at a setting that lifts the moss and the '
                'grey without stripping the joints out.',
                'Pricing is by the square foot, with a different rate for pavers than for '
                'poured concrete. Measure yours in the estimator for a price on screen.',
            ]),
        ],
    ),
    dict(
        slug='deck-porch-cleaning',
        nav='Decks & Porches',
        h1=('DECKS AND PORCHES', 'WITHOUT THE SPLINTERS'),
        title='Deck & Porch Cleaning in South Jersey',
        desc='Deck and porch cleaning across South Jersey for composite and wood. '
             'Removes the grey, algae and black staining without splintering the '
             'boards.',
        image='deck-patio.jpg',
        lead='A deck goes grey for two reasons at once: the surface of the timber weathers, '
             'and algae settles into it. Cleaning deals with the second and reveals how much '
             'of the first there really was.',
        body=[
            ('Composite and wood are not the same job', [
                'Composite boards take a gentler approach than people expect. They scar, and '
                'the scars do not weather away. Wood can take a little more, but only along '
                'the grain and only up to the point where the surface fibers start to lift.',
                'Get it wrong on wood and you get a furry deck that splinters underfoot for a '
                'season. That is the single most common piece of damage on a badly washed '
                'deck, and it is entirely avoidable.',
            ]),
            ('The parts people forget', [
                'Porch ceilings, stair treads, the underside of rails and outdoor shower floors '
                'all collect more than the open boards do, because they stay damp longest. They '
                'are also the parts most often missed, and a deck shows it where somebody '
                'stopped short.',
            ]),
            ('If you are staining afterwards', [
                'Stain and sealer need a clean, dry surface or they will not key properly. If '
                'the plan is to seal the deck, have it washed first and give it a few dry days '
                'before the sealer goes on.',
            ]),
        ],
    ),
    dict(
        slug='fence-washing',
        nav='Fence Washing',
        h1=('FENCE', 'WASHING'),
        title='Fence Cleaning & Washing in South Jersey',
        desc='Vinyl, wood and wrought iron fence cleaning across South Jersey. '
             'Green algae and weathering removed. Priced per linear foot, one '
             'side or both.',
        image='fence-washing.jpg',
        lead='A fence is the thing you look at most and think about least. It is also, on a lot '
             'of properties, the greenest surface there is.',
        body=[
            ('Vinyl, wood and iron', [
                'Vinyl is the most common fence down here, and it is the one that cleans up '
                'closest to new. It takes low pressure and a solution that kills the green '
                'rather than scours it off.',
                'Wood needs the same care as a deck: along the grain, and no further than the '
                'point where the surface starts to lift. Wrought iron and aluminum rail is '
                'mostly about the salt film and the rust spots where the coating has gone.',
            ]),
            ('Shaded sides green up fastest', [
                'Anything under trees, or backing onto water or wetland, holds damp for longer '
                'and grows a film far quicker than a fence on an open street. On those runs a '
                'yearly wash keeps on top of it, where leaving it three years turns a wash into '
                'a much harder job.',
            ]),
            ('What it costs', [
                'Pricing is per linear foot and per side, so you can have one side or both. '
                'Put your fence line into the estimator and the difference shows in the quote '
                'before you book.',
            ]),
        ],
    ),
    dict(
        slug='gutter-cleaning',
        nav='Gutter Cleaning',
        h1=('GUTTER', 'CLEANING'),
        title='Gutter Cleaning & Brightening in South Jersey',
        desc='Gutter clearing and exterior gutter brightening across South '
             'Jersey. Removes blockages and the black tiger striping on gutter '
             'faces. Added to any job.',
        image='gutter-cleaning.jpg',
        lead='Two different jobs get called gutter cleaning, and it is worth knowing which '
             'one you are asking for.',
        body=[
            ('Clearing versus brightening', [
                'Clearing is the inside: getting the leaves, shingle grit and nesting material '
                'out so water runs to the downspout instead of over the front edge. That is '
                'the one that protects the fascia and the foundation.',
                'Brightening is the outside: those vertical black stripes down the face of the '
                'gutter, which are an oxidised film rather than dirt and do not come off with '
                'a rinse. It needs treating, and it makes more visual difference to the front '
                'of a house than most people expect.',
            ]),
            ('Worth doing with a wash', [
                'Gutters are the obvious thing to do while the house is being washed, because '
                'the access is already set up. Priced per linear foot either way, and doing '
                'both at once means one visit rather than two.',
            ]),
        ],
    ),
    dict(
        slug='window-cleaning',
        nav='Window Cleaning',
        h1=('WINDOW', 'CLEANING'),
        title='Window Cleaning in South Jersey',
        desc='Window cleaning across South Jersey - glass, frames and screens, '
             'inside and out. Salt film and hard water spotting removed.',
        image='window-cleaning.jpg',
        # Windows are not in the online estimator yet, so this page must not
        # promise a price on screen the way the others can.
        cta_head='Tell us how many windows',
        cta='Windows are quoted by the number of panes rather than by area, so call, or add '
            'them in the notes when you book anything else and we will price them with the '
            'job. Everything else on the site prices itself on screen.',
        lead='Clean glass is the cheapest change you can make to how a house looks, and the '
             'one people notice without being able to say why.',
        body=[
            ('Glass, frames and screens', [
                'A window is not just the pane. Sills and frames hold a surprising amount of '
                'dirt, and the screens hold more than either - which is why glass cleaned '
                'without doing the screens looks poor again after the first rain.',
                'Screens come out, get washed and go back. It is the step most often skipped '
                'and the one that decides how long the job lasts, which is why it is worth '
                'adding.',
            ]),
            ('Salt film and hard water', [
                'Coastal glass carries a fine salt film that water and a squeegee will simply '
                'move around, leaving it streaked. It needs a solution that lifts it.',
                'Hard water spotting is the other one, usually from a sprinkler hitting the '
                'glass day after day. Caught early it comes off. Left for years the minerals '
                'etch into the surface and no amount of cleaning brings it all back, so it is '
                'worth dealing with before it sets.',
            ]),
            ('What it costs', [
                'Windows are quoted by the number of panes rather than by area, so tell us how '
                'many, and whether you want screen cleaning and frame cleaning added. Add it to '
                'a house wash and the frames and screens are cleaned for free.',
            ]),
        ],
    ),
    dict(
        slug='add-on-services',
        nav='Add-On Services',
        h1=('ADD-ON', 'SERVICES'),
        title='Outdoor Furniture & Awning Cleaning in South Jersey',
        desc='Outdoor furniture, awning and trash can cleaning across South Jersey, '
             'added to any job. Priced per piece and per square foot.',
        image='add-on-services.jpg',
        gallery=[
            ('patio-furniture.jpg', 'Cleaned patio furniture on a paver patio',
             'Furniture and the patio underneath it, done in the same visit.'),
            ('awning-cleaning.jpg', 'A black fabric door awning after cleaning',
             'Fabric awnings take a gentle wash - pressure costs you the stitching.'),
        ],
        lead='Small things that are quick while the equipment is already set up, and awkward '
             'to justify a visit for on their own.',
        body=[
            ('Outdoor furniture', [
                'Patio sets, loungers and cushions collect the same film as the deck they stand '
                'on. Cleaning the furniture and the cushions can bring them back to new '
                'condition, and buy you a few more seasons before they need replacing. Priced '
                'per piece, and quick work alongside a deck or patio clean.',
            ]),
            ('Awnings and canopies', [
                'Fabric awnings grow mildew in exactly the way a north wall does, and the worst '
                'of it is usually on the top side, where the damp sits longest. They take a '
                'gentle wash - fabric will not survive pressure and the stitching goes first.',
                'Priced by the square foot.',
            ]),
            ('Trash and recycling cans', [
                'Cans are worth adding while the equipment is already out. They get washed '
                'inside and out, which clears the gunk that builds up in the bottom of them '
                'over a summer.',
            ]),
        ],
    ),
]

# What each service looks like on the home page grid. Kept beside SERVICES and
# checked against it at build time, so a new service page cannot quietly ship
# without a card, or the other way round.
CARDS = {
    'house-washing': ('\U0001F3E0', 'House Washing', 'Soft Wash',
        'Soft wash lifts the green off vinyl, cedar shake, stucco and brick — including '
        'the shaded north wall that always goes first. Low pressure throughout: the cleaning '
        'solution does the work, not force.'),
    'roof-washing': ('\U0001F3DA️', 'Roof Washing', 'Soft Wash Only',
        'Low-pressure soft wash clears black streaks, moss and lichen from shingle, metal and '
        'cedar shake roofs. Damp shore air feeds the algae behind those streaks, and pressure '
        'would cost you shingles.'),
    'driveway-patio-cleaning': ('\U0001F6E3️', 'Driveway &amp; Pavers', 'Pressure Wash',
        'Cement, brick and paver drives, walks and patios. Salt scale, moss and years of '
        'ground-in grime come up. Pavers are cleaned with minimal pressure, to preserve '
        'the polymeric sand that holds them in place.'),
    'deck-porch-cleaning': ('\U0001FAB5', 'Deck &amp; Patio', 'Soft + Pressure',
        'Decks, porches and outdoor shower floors, composite or wood. Sand and salt grind grey '
        'into the boards — we bring the color back without splintering them.'),
    'fence-washing': ('\U0001F512', 'Fencing', 'All Materials',
        'Vinyl, wood and wrought iron, one side or both. Fences under trees and on shaded runs '
        'green up fastest, so they are worth doing yearly.'),
    'gutter-cleaning': ('\U0001F342', 'Gutter Cleaning', 'Clear &amp; Brighten',
        'Clearing the inside so water reaches the downspout, and brightening the outside where '
        'black tiger striping has set into the face. Two different jobs, and both worth doing.'),
    'window-cleaning': ('\U0001FA9F', 'Window Cleaning', 'Inside &amp; Out',
        'Glass, frames and screens. Salt film and hard-water spotting need more than water and '
        'a squeegee, and clean glass changes how a house looks more than people expect.'),
    'add-on-services': ('✨', 'Add-On Services', 'Bundle &amp; Save',
        'Outdoor furniture, awnings and trash cans, added to any job. Bundling means one visit '
        'instead of two, and the bigger the job the better the rate.'),
}

# --------------------------------------------------------------------------
# TOWNS
# --------------------------------------------------------------------------
TOWNS = [
    dict(
        slug='ocean-city', name='Ocean City', county='Cape May County',
        lead='Ocean City houses sit close together, close to the sand, and a great many of '
             'them are rented out by the week. All three change how we clean them.',
        body=[
            ('Salt spray and tight lots', [
                'On the properties closest to the beach the salt film never really goes away, '
                'and it holds dust '
                'the way nothing else does. Lots are narrow, so the shaded side wall of one '
                'house often stands three feet from the next. It stays damp all day and '
                'greens up first.',
                'That gap is the awkward part of the job. We keep the rinse tight, so we are '
                'not cleaning your house onto the neighbor\'s siding and plants.',
            ]),
            ('Rental turnover', [
                'If your place is a summer rental, the outside matters most on the day you '
                'take the photographs and on the Saturdays between tenants. You book online, '
                'so you pick the date that suits the calendar instead of negotiating it over '
                'the phone.',
                'Plenty of Ocean City owners live over in the Philadelphia suburbs and are '
                'not at the house midweek. You do not need to be there. Leave the outside tap '
                'on and the gate unlocked, and we send photographs when the job is done.',
            ]),
        ],
    ),
    dict(
        slug='sea-isle-city', name='Sea Isle City', county='Cape May County',
        lead='A large share of Sea Isle has been rebuilt in the last twenty-five years, which '
             'means a lot of newer vinyl, a lot of composite decking, and houses standing '
             'high on pilings.',
        body=[
            ('Newer construction, different work', [
                'Modern vinyl cleans up beautifully and takes low pressure. Composite decks '
                'want a gentler touch than the wood they replaced. Neither needs force, and '
                'both look markedly better when we treat them rather than blast them.',
                'Height is the other thing. Houses up on pilings put the second and third '
                'story a long way up, and we carry the equipment to reach them from the '
                'ground. Doing that safely is a large part of the trade.',
            ]),
            ('Bayside and beachside', [
                'The bay side and the beach side of the island weather differently. Bayside '
                'properties, especially those with slips or bulkheads, stay damper and grow '
                'more; beachside takes the salt and the wind-blown sand. Both are routine, '
                'but they are not the same wash.',
            ]),
        ],
    ),
    dict(
        slug='avalon', name='Avalon', county='Cape May County',
        lead='Avalon is cooler by a mile and shadier than most of the island chain, and it '
             'has a great deal of cedar. That combination grows more on a house than the '
             'brochure suggests.',
        body=[
            ('Cedar shake needs care', [
                'Cedar goes black and streaky where damp and shade get to it, and shaded '
                'elevations on this island get plenty of both. We soft wash the growth out, '
                'then follow with a wood brightener that lifts the color back and leaves the '
                'shakes looking new rather than only clean.',
                'Pressure is never part of it. On cedar it raises the grain, and raised cedar '
                'holds more dirt afterwards than it did to begin with, so a forceful job makes '
                'next year worse.',
            ]),
            ('Larger properties, dune side', [
                'The dune-side houses take weather from the front and hold shade at the back, '
                'so the two elevations rarely need the same approach. Bigger footprints also '
                'mean the size discount in the estimator usually applies, which is worth '
                'checking before you book.',
            ]),
        ],
    ),
    dict(
        slug='stone-harbor', name='Stone Harbor', county='Cape May County',
        lead='Stone Harbor is quieter than its neighbors, with older houses and more mature '
             'trees than anywhere else on Seven Mile Island. Shade is the thing that drives '
             'the work here.',
        body=[
            ('Tree cover means more growth', [
                'Anything under a canopy stays damp for hours longer after rain or fog, and '
                'that is all algae needs. Houses with trees close by go green faster and more '
                'unevenly than exposed ones, and the roof usually shows it before the siding '
                'does.',
                'It is also why the north and east elevations here are so often a shade darker '
                'than the front of the house. Those walls are where a wash earns its money.',
            ]),
            ('Older houses, painted trim', [
                'Older properties bring painted wood trim, porch ceilings and rail that need '
                'the gentle treatment. Low pressure and the right solution clean them without '
                'lifting sound paint, which a pressure wand cannot promise.',
            ]),
        ],
    ),
    dict(
        slug='cape-may', name='Cape May', county='Cape May County',
        lead='Cape May has the most delicate housing stock in South Jersey. Painted Victorian '
             'woodwork, gingerbread trim and a historic district that people rightly care '
             'about. None of it should ever meet a pressure washer.',
        body=[
            ('A Victorian is soft wash only', [
                'Painted wood, decorative trim and old glazing putty do not survive pressure. '
                'What they need is low pressure and chemistry: we kill the growth and rinse it '
                'off, the paint stays where it is, and the detail that makes the house worth '
                'looking at is still there afterwards.',
                'If anyone offers to pressure wash a painted Victorian, that is the moment to '
                'stop the conversation. The damage is not subtle and it is not cheap to put '
                'right.',
            ]),
            ('Damp, salt and shade together', [
                'Being nearly surrounded by water, Cape May holds damp longer than anywhere '
                'inland, and the older houses have the shaded porches and north walls to go '
                'with it. Green film on painted clapboard is the standard job here, and it '
                'comes off cleanly.',
            ]),
        ],
    ),
    dict(
        slug='somers-point', name='Somers Point', county='Atlantic County',
        lead='Somers Point is a year-round town, which changes the job: houses here are lived '
             'in through the winter, and the exterior work is about keeping on top of things '
             'rather than getting ready for a season.',
        body=[
            ('Bayfront weather', [
                'Fronting Great Egg Harbor Bay means salt without the full force of the ocean, '
                'and a lot of damp coming off the water. Bulkheads, docks and the fences and '
                'rail along the water take the worst of it and are usually the first thing '
                'worth cleaning.',
            ]),
            ('Older housing stock', [
                'A good number of ranches and colonials from the fifties through the eighties, '
                'which means original aluminum siding in places, painted trim, and concrete '
                'drives that have had decades to go grey. All of it cleans up; it simply wants '
                'the right method for its age.',
            ]),
        ],
    ),
    dict(
        slug='upper-township', name='Upper Township', county='Cape May County',
        lead='Upper Township covers a lot of ground, from Marmora and Seaville out to '
             'Tuckahoe, and it is the nearest work to home base in Corbin City. Wooded lots '
             'and well water make it a different job from the islands.',
        body=[
            ('Trees, damp and moss', [
                'Away from the beach the wind drops and the tree cover goes up, so surfaces '
                'stay wet longer. Roofs here collect moss rather than just streaking, and '
                'north-facing walls and fences go green quickly. Shaded concrete grows a film '
                'that gets slippery, which is worth staying ahead of.',
            ]),
            ('Close to home', [
                'Corbin City is inside the township, so this is the shortest run we make. '
                'Marmora, Seaville, Tuckahoe, Petersburg and Beesleys Point are all a few '
                'minutes away, which makes scheduling easy and makes small jobs worth doing.',
            ]),
        ],
    ),
    dict(
        slug='egg-harbor-township', name='Egg Harbor Township', county='Atlantic County',
        lead='Egg Harbor Township is a big year-round township of newer housing developments, '
             'and the work here runs to a pattern: a lot of vinyl siding and a lot of wide '
             'concrete driveway.',
        body=[
            ('Development vinyl', [
                'Houses from the nineties and two-thousands are mostly vinyl, which is the '
                'easiest siding there is to bring back — the green comes off completely and '
                'the color underneath is usually better than owners expect. Whole streets '
                'have the same problem on the same elevation, because they face the same way.',
            ]),
            ('Concrete and pavers', [
                'Driveways here are generous, and square footage is what drives the price on '
                'concrete. It is also where the size discount tends to kick in, so a drive '
                'and a house together often costs less than the two priced separately. Measure '
                'both in the estimator and it will show you.',
            ]),
        ],
    ),
    dict(
        slug='mays-landing', name='Mays Landing', county='Atlantic County',
        lead='Mays Landing spreads a long way inland, from the old village on the Great Egg '
             'Harbor River out through the developments and wooded lots around it. Shade and '
             'damp do the damage here, not salt.',
        body=[
            ('What the tree cover does', [
                'Tree cover keeps siding, roofs and concrete damp for hours longer after rain, '
                'and damp is all the algae needs. It also comes back sooner under a canopy '
                'than on an open lot, so a regular wash is worth more here than in most '
                'places.',
                'Black streaking on shingles is a common call out here, and it is soft wash '
                'work — pressure on a shingle roof buys a clean season at the cost of years '
                'of roof life.',
            ]),
            ('The village and the rest of it', [
                'The oldest housing sits around the village, and it brings painted wood, porch '
                'detail and trim that need the gentle approach. Most of Mays Landing is newer '
                'than that: vinyl-sided houses on big wooded lots, where the work is the shaded '
                'elevations and a wide concrete driveway.',
            ]),
        ],
    ),
    dict(
        slug='galloway', name='Galloway', county='Atlantic County',
        lead='Galloway covers a lot of ground between the Parkway and the bay, and most of it '
             'is wooded. Pine cover and sandy soil make for a different sort of dirt than the '
             'islands ever see.',
        body=[
            ('Pine shade, and what it does to a roof', [
                'Under pine the ground stays damp and the roof stays shaded, and that is '
                'exactly the combination algae wants. The north slope streaks black while the '
                'front of the house still looks respectable.',
                'Pine debris is the other half of it. Needles pack into gutters far more '
                'tightly than leaves do, and they hold water rather than letting it through, '
                'so gutters here fill up faster and stain the fascia while they are at it.',
            ]),
            ('The jobs that come up most', [
                'It is usually the same three jobs here: a soft wash on the roof for the '
                'streaking, a house wash for the shaded elevations, and the gutters cleared '
                'of needles. Booked together they are one visit and one price, which is how '
                'most Galloway houses are done. Smithville, Oceanville, Pomona, Absecon '
                'Highlands and the developments off Jimmie Leeds Road are all routine work.',
                'The eastern side towards Reeds Bay and the refuge is a different job again: '
                'marsh damp with no shade to speak of, which greens up fences and bulkhead '
                'rail quicker than anywhere else in the township.',
            ]),
        ],
    ),
    dict(
        slug='vineland', name='Vineland', county='Cumberland County',
        lead='Vineland is one of the largest cities in New Jersey by land area, and the work '
             'reflects it: long runs of fence, big driveways, and houses sitting on plenty of '
             'ground.',
        body=[
            ('Long runs price well', [
                'Fence is priced per linear foot and concrete per square foot, so the large '
                'properties around Vineland tend to hit the size discount brackets. A long '
                'fence line is usually cheaper per foot than people assume once you add it '
                'up.',
            ]),
            ('What most jobs here are', [
                'Away from the shore there is no salt film to deal with, so the work is the '
                'ordinary business of shade and damp: vinyl siding gone green on the north '
                'side, black streaking on the roof, and a driveway that has greyed off over a '
                'few winters.',
                'Most bookings are those three together, which is one visit instead of three '
                'and one price for the lot. Put them all into the estimator and it will show '
                'you the difference before you commit to anything.',
            ]),
        ],
    ),
]

ALTS = {
    'house-washing': 'Soft washing algae off vinyl house siding',
    'roof-washing': 'Soft wash roof cleaning removing black streaks',
    'driveway-patio-cleaning': 'Clean brick paver walkway curving through planted beds',
    'deck-porch-cleaning': 'Cleaned composite deck boards',
    'fence-washing': 'Cleaned vinyl fence panels',
    'gutter-cleaning': 'A gutter full of leaves beside the same gutter cleared out',
    'window-cleaning': 'Clean windows reflecting the sky on a two story house',
    'add-on-services': 'A cleaned wicker patio furniture set',
}


def card_photo(s):
    """The photo for the home page card. An explicit photo=None means we do not
    have one yet and the card falls back to a colored tile."""
    return s['photo'] if 'photo' in s else s['image']


def service_cards_html():
    """The Professional Services grid. The WHOLE card is the link - a title-only
    link left people unsure what was clickable, and most never found the
    service pages at all."""
    out = ['<div class="services-grid">']
    for s in SERVICES:
        icon, title, badge, desc = CARDS[s['slug']]
        photo = card_photo(s)
        if photo:
            media = ('<div class="svc-img"><img src="img/%s" alt="%s" loading="lazy"></div>'
                     % (photo, html.escape(ALTS[s['slug']], quote=True)))
        else:
            media = '<div class="svc-img ph"><span>%s</span></div>' % icon
        out.append(
            '    <a class="svc-card" href="%s.html">\n'
            '      %s\n'
            '      <div class="svc-body"><div class="svc-icon">%s</div>'
            '<div class="svc-title">%s</div>'
            '<div class="svc-desc">%s</div>'
            '<span class="svc-badge">%s</span>'
            '<div class="svc-more">See what is involved <span class="arw">&rarr;</span></div>'
            '</div>\n'
            '    </a>' % (s['slug'], media, icon, title, desc, badge))
    out.append('  </div>')
    return '\r\n'.join(out)


# --------------------------------------------------------------------------
# shared chrome, lifted out of index.html so it cannot drift
# --------------------------------------------------------------------------

def chrome():
    src = open('index.html', encoding='utf-8').read()
    nav = re.search(r'<nav>.*?</nav>', src, re.S).group(0)
    mob = re.search(r'<div id="mob-menu">.*?</div>', src, re.S).group(0)
    foot = re.search(r'<footer>.*?</footer>', src, re.S).group(0)
    # on a sub-page the home page anchors have to point back at the home page
    for frag in ['#services', '#results', '#about', '#area', '#estimate']:
        nav = nav.replace('href="%s"' % frag, 'href="index.html%s"' % frag)
        mob = mob.replace('href="%s"' % frag, 'href="index.html%s"' % frag)
    nav = nav.replace('<a href="#" class="nav-logo">', '<a href="index.html" class="nav-logo">')
    return nav, mob, foot


def ld_business():
    """The business itself. No street address: this is a service-area business
    working out of a home, and publishing the street is both a Google
    guidelines problem and nobody's business."""
    return {
        '@type': ['LocalBusiness', 'HomeAndConstructionBusiness'],
        '@id': SITE + '/#business',
        'name': BIZ,
        'legalName': LEGAL,
        'url': SITE + '/',
        'telephone': PHONE_E164,
        'email': EMAIL,
        'image': SITE + '/img/house-washing.jpg',
        'priceRange': '$$',
        'address': {'@type': 'PostalAddress', 'addressLocality': 'Corbin City',
                    'addressRegion': 'NJ', 'postalCode': '08270', 'addressCountry': 'US'},
        'areaServed': [{'@type': 'City', 'name': t['name']} for t in TOWNS],
        'sameAs': [INSTAGRAM],
        'openingHoursSpecification': [{
            '@type': 'OpeningHoursSpecification',
            'dayOfWeek': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
            'opens': '07:00', 'closes': '17:00',
        }],
    }


def json_ld(obj):
    import json
    return ('<script type="application/ld+json">'
            + json.dumps(obj, indent=None, separators=(',', ':'))
            + '</script>')


def head(title, desc, canonical, image, ld):
    return '\n'.join([
        '<!DOCTYPE html>',
        '<html lang="en">',
        '<head>',
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        '<title>%s | %s</title>' % (html.escape(title), BIZ),
        '<meta name="description" content="%s">' % html.escape(desc),
        '<link rel="canonical" href="%s">' % canonical,
        '<meta property="og:type" content="website">',
        '<meta property="og:site_name" content="%s">' % BIZ,
        '<meta property="og:title" content="%s | %s">' % (html.escape(title), BIZ),
        '<meta property="og:description" content="%s">' % html.escape(desc),
        '<meta property="og:url" content="%s">' % canonical,
        '<meta property="og:image" content="%s/img/%s">' % (SITE, image),
        '<meta name="twitter:card" content="summary_large_image">',
        '<link rel="preconnect" href="https://fonts.googleapis.com">',
        '<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;800;900&family=Lato:wght@300;400;700&display=swap" rel="stylesheet">',
        '<link rel="stylesheet" href="css/site.css">',
        '<link rel="stylesheet" href="css/page.css">',
        json_ld(ld),
        '</head>',
        '<body>',
    ])


TAIL = ('<script>function toggleMenu(){const m=document.getElementById("mob-menu");'
        'm.classList.toggle("open")}</script>\n</body>\n</html>')


def prose(sections):
    out = []
    for heading, paras in sections:
        out.append('    <h2>%s</h2>' % html.escape(heading))
        for p in paras:
            out.append('    <p>%s</p>' % p)
    return '\n'.join(out)


def endcta(line, heading='Get a price without picking up the phone'):
    return '\n'.join([
        '<section class="endcta">',
        '  <h2>%s</h2>' % heading,
        '  <p>%s</p>' % line,
        '  <div class="hero-btns" style="justify-content:center">',
        '    <a href="index.html#estimate" class="btn-primary">&#128203; Get Instant Quote</a>',
        '    <a href="tel:%s" class="btn-outline">&#128222; %s</a>' % (PHONE_E164, PHONE_PRETTY),
        '  </div>',
        '</section>',
    ])


def figures(items):
    """Optional photo strip inside a service page."""
    if not items:
        return ''
    figs = '\n'.join(
        '    <figure><img src="img/%s" alt="%s" loading="lazy"><figcaption>%s</figcaption></figure>'
        % (f, html.escape(alt, quote=True), html.escape(cap))
        for f, alt, cap in items)
    return '<section style="padding-top:0">\n  <div class="figs">\n%s\n  </div>\n</section>' % figs


def linkgrid(title, items):
    rows = '\n'.join('    <a href="%s">%s</a>' % (h, html.escape(n)) for h, n in items)
    return ('<section>\n  <div class="section-label">%s</div>\n  <div class="linkgrid">\n%s\n  </div>\n</section>'
            % (title, rows))


SERVICE_LINKS = [(s['slug'] + '.html', s['nav']) for s in SERVICES]
TOWN_LINKS = [(t['slug'] + '.html', t['name']) for t in TOWNS]


def build_service(s):
    canonical = '%s/%s.html' % (SITE, s['slug'])
    ld = {'@context': 'https://schema.org', '@graph': [
        ld_business(),
        {'@type': 'Service', 'name': s['nav'], 'serviceType': s['nav'],
         'provider': {'@id': SITE + '/#business'},
         'description': s['desc'],
         'areaServed': [{'@type': 'City', 'name': t['name']} for t in TOWNS]},
    ]}
    parts = [
        head(s['title'], s['desc'], canonical, s['image'], ld),
        NAV, MOB,
        '<section class="sub-hero">',
        '  <div class="crumb"><a href="index.html">Home</a> &rsaquo; %s</div>' % html.escape(s['nav']),
        '  <h1>%s<em>%s</em></h1>' % s['h1'],
        '  <p>%s</p>' % s['lead'],
        '  <div class="hero-btns">',
        '    <a href="index.html#estimate" class="btn-primary">&#128203; Get Instant Quote</a>',
        '    <a href="tel:%s" class="btn-outline">&#128222; %s</a>' % (PHONE_E164, PHONE_PRETTY),
        '  </div>',
        '</section>',
        '<section>',
        '  <div class="prose">',
        prose(s['body']),
        '  </div>',
        '</section>',
        figures(s.get('gallery')),
        linkgrid('Other services', [x for x in SERVICE_LINKS if x[0] != s['slug'] + '.html']),
        linkgrid('Towns we cover', TOWN_LINKS),
        endcta(s.get('cta', 'Prices are on screen in the estimator, and nothing is due until '
                            'the work is finished. Book the date yourself when you are ready.'),
               s.get('cta_head', 'Get a price without picking up the phone')),
        FOOT, TAIL,
    ]
    return '\n'.join(parts)


def build_town(t):
    canonical = '%s/%s.html' % (SITE, t['slug'])
    title = 'Pressure Washing in %s, NJ' % t['name']
    desc = ('Soft wash and pressure washing in %s, %s. House, roof, deck, driveway, '
            'fence and gutter cleaning. Quote online and book your own date.'
            % (t['name'], t['county']))
    ld = {'@context': 'https://schema.org', '@graph': [
        ld_business(),
        {'@type': 'Service', 'name': 'Pressure washing in %s' % t['name'],
         'serviceType': 'Pressure washing', 'provider': {'@id': SITE + '/#business'},
         'description': desc,
         'areaServed': {'@type': 'City', 'name': t['name'],
                        'containedInPlace': {'@type': 'AdministrativeArea',
                                             'name': t['county'] + ', New Jersey'}}},
    ]}
    parts = [
        head(title, desc, canonical, 'house-washing.jpg', ld),
        NAV, MOB,
        '<section class="sub-hero">',
        '  <div class="crumb"><a href="index.html">Home</a> &rsaquo; %s</div>' % html.escape(t['name']),
        '  <h1>PRESSURE WASHING<em>IN %s</em></h1>' % t['name'].upper(),
        '  <p>%s</p>' % t['lead'],
        '  <div class="hero-btns">',
        '    <a href="index.html#estimate" class="btn-primary">&#128203; Get Instant Quote</a>',
        '    <a href="tel:%s" class="btn-outline">&#128222; %s</a>' % (PHONE_E164, PHONE_PRETTY),
        '  </div>',
        '</section>',
        '<section>',
        '  <div class="prose">',
        prose(t['body']),
        '  </div>',
        '</section>',
        linkgrid('What we clean in %s' % html.escape(t['name']), SERVICE_LINKS),
        linkgrid('Other towns', [x for x in TOWN_LINKS if x[0] != t['slug'] + '.html']),
        endcta('Measure your own property off the satellite view, see the price on screen, '
               'and pick a date. No calls needed.'),
        FOOT, TAIL,
    ]
    return '\n'.join(parts)


PAGE_CSS = """/* Layout for the service and town pages. The palette, type and buttons all
   come from site.css - nothing is redefined here. */
.sub-hero{background:linear-gradient(160deg,var(--ink) 0%,#122b30 55%,#17505a 100%);padding:132px 5% 62px;color:#fff;position:relative;overflow:hidden}
.sub-hero .crumb{font-size:.78rem;color:rgba(255,255,255,.45);margin-bottom:14px;letter-spacing:.5px}
.sub-hero .crumb a{color:rgba(255,255,255,.72);text-decoration:none}
.sub-hero .crumb a:hover{color:var(--sky)}
.sub-hero h1{font-family:'Barlow Condensed',sans-serif;font-size:clamp(2.3rem,6.5vw,4.2rem);font-weight:900;line-height:.98;letter-spacing:1px;margin-bottom:18px}
.sub-hero h1 em{color:var(--sky);font-style:normal;display:block}
.sub-hero p{max-width:640px;color:rgba(255,255,255,.72);line-height:1.75;font-weight:300;font-size:1.05rem}
.sub-hero .hero-btns{display:flex;gap:14px;flex-wrap:wrap;margin-top:30px}
.prose{max-width:780px}
.prose h2{font-family:'Barlow Condensed',sans-serif;font-size:clamp(1.5rem,3.4vw,2rem);font-weight:800;color:var(--ink);margin:38px 0 12px;line-height:1.15}
.prose h2:first-child{margin-top:0}
.prose p{color:#556;line-height:1.85;margin-bottom:15px;font-weight:300}
.linkgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(196px,1fr));gap:10px;margin-top:18px}
.linkgrid a{display:block;padding:12px 15px;background:var(--white);border:1.5px solid #dfe8e6;border-radius:9px;color:var(--ocean);text-decoration:none;font-weight:700;font-size:.9rem;transition:all .18s}
.linkgrid a:hover{border-color:var(--sky);color:var(--ink);transform:translateY(-1px)}
.endcta{background:var(--ink);text-align:center}
.endcta h2{font-family:'Barlow Condensed',sans-serif;font-size:clamp(1.8rem,4.4vw,2.7rem);font-weight:800;color:#fff;margin-bottom:14px;line-height:1.1}
.endcta p{color:rgba(255,255,255,.65);max-width:540px;margin:0 auto 28px;line-height:1.75;font-weight:300}
.figs{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:18px}
.figs figure{margin:0}
.figs img{width:100%;height:240px;object-fit:cover;border-radius:12px;display:block}
.figs figcaption{margin-top:9px;font-size:.85rem;color:#667;line-height:1.5;font-weight:300}
@media(max-width:768px){.sub-hero{padding:108px 5% 48px}}
"""


# --------------------------------------------------------------------------
# LEGAL PAGES
#
# These exist because the phone carriers require them. Before Twilio will let
# a business send texts, the A2P 10DLC review reads the website looking for
# three things: the consent box on the booking form, a privacy policy saying
# mobile numbers are never sold or shared for marketing, and a page setting
# out what the messages are and how to stop them. Missing any one of the three
# is the usual reason a campaign is rejected, so the required sentences below
# are kept intact -- do not "tidy" them away.
# --------------------------------------------------------------------------
LEGAL_UPDATED = 'August 26, 2026'
LEGAL_UPDATED_ISO = '2026-08-26'

LEGAL_PAGES = [
    dict(
        slug='privacy',
        nav='Privacy Policy',
        h1=('PRIVACY', 'POLICY'),
        title='Privacy Policy',
        desc='How Osprey Power Wash collects, uses and protects your personal '
             'information, including your mobile number and text message consent.',
        lead='Last updated ' + LEGAL_UPDATED + '. What we collect when you get a quote or '
             'book a job, what we do with it, and what we never do with it.',
        body=[
            ('Who we are', [
                'Osprey Power Wash is a registered trade name of Tidal Wash LLC, an exterior '
                'cleaning company working across South Jersey. You can reach us on '
                '<a href="tel:%(e164)s">%(phone)s</a> or '
                '<a href="mailto:%(email)s">%(email)s</a>. In this policy "we" and "us" mean '
                'Tidal Wash LLC trading as Osprey Power Wash.',
            ]),
            ('What we collect', [
                'When you use the estimator we collect the measurements and property details '
                'you enter and the address you type into the satellite measuring tool. None '
                'of that identifies you until you decide to book.',
                'When you book we collect your name, phone number, email address, service '
                'address and any notes you add, together with the date you picked and the '
                'estimate the calculator produced.',
                'When you call, text or email us we keep the message and our reply, so there '
                'is a record of what was agreed about the work.',
                'We do not ask for or store card or bank details on this website. Payment is '
                'taken after the work is finished.',
            ]),
            ('What we use it for', [
                'To give you a price, book the date, turn up and do the work, invoice you '
                'afterwards and answer questions about the job. That is the whole of it. We '
                'also keep the record for our own accounts and tax returns.',
            ]),
            ('Text messages and your mobile number', [
                'If you give us your mobile number we may text you about the job you booked: '
                'a confirmation, a reminder the day before, a message if the weather moves '
                'the date, and questions about access or timing. That is service contact '
                'about work you asked us for.',
                'Marketing texts - seasonal offers, or a reminder that it is about time the '
                'house was washed again - are separate. We send those only to people who '
                'ticked the box on the booking form agreeing to them or told us so in '
                'writing. Agreeing is optional and is never a condition of buying anything '
                'from us.',
                '<strong>No mobile information will be shared with third parties or '
                'affiliates for marketing or promotional purposes.</strong> Information '
                'sharing with subcontractors in support services, such as customer service '
                'and our text messaging provider, is permitted. All other use case '
                'categories exclude text messaging originator opt-in data and consent; this '
                'information will not be shared with any third parties.',
                'You can stop texts at any time by replying STOP to any message from us, or '
                'by telling us on the phone or by email. The detail is on our '
                '<a href="sms-terms.html">Text Message Terms</a> page.',
            ]),
            ('Who else sees your information', [
                'We are a small business and your details stay with us. The only outside '
                'companies involved are the ones running the tools we use to do the work: '
                'Google, which provides our email, calendar and the spreadsheet our customer '
                'records live in; Twilio, which delivers our text messages; and any '
                'subcontractor working on your job, who gets only what they need to find the '
                'property and do the work.',
                'We do not sell your information, we do not rent it, and we do not hand it '
                'to anybody for their own marketing.',
                'We will disclose information where the law requires it - a court order, a '
                'tax audit, or an insurance claim arising from work at your property.',
            ]),
            ('Cookies, advertising and the measuring tool', [
                'The satellite measuring tool is Google Maps running inside the page. The '
                'address you search for is sent to Google so it can show you the right roof, '
                'and Google sets its own cookies for that under its own privacy policy.',
                'We advertise on Facebook, Instagram and Google. While those campaigns are '
                'running this site carries the standard measurement tags from Meta and '
                'Google, which set cookies so we can tell that an advert led to a booking. '
                'They measure adverts; they are not how we contact you, and they are not '
                'given your text message consent. Your browser settings control whether '
                'those cookies are allowed.',
            ]),
            ('How long we keep it', [
                'Customer and job records are kept for at least seven years, because tax and '
                'insurance both require us to be able to show what work was done, when and '
                'for how much. Quote enquiries that never became jobs are kept for around '
                'two years, so we can pick up where we left off if you come back to us.',
            ]),
            ('Your choices', [
                'Reply STOP to any text to stop texts. Use the unsubscribe link in a '
                'marketing email to stop emails. Ask us and we will tell you what we hold '
                'about you, correct anything wrong, or delete whatever we are not legally '
                'required to keep. Email <a href="mailto:%(email)s">%(email)s</a> or call '
                '<a href="tel:%(e164)s">%(phone)s</a>.',
            ]),
            ('Children', [
                'This is a service for property owners. The site is not directed at children '
                'and we do not knowingly collect information from anyone under 18.',
            ]),
            ('Changes to this policy', [
                'If we change how we handle your information we will update this page and '
                'change the date at the top. A material change to how we use your mobile '
                'number will be told to you directly, not buried here.',
            ]),
        ],
    ),
    dict(
        slug='sms-terms',
        nav='Text Message Terms',
        h1=('TEXT MESSAGE', 'TERMS'),
        title='Text Message (SMS) Terms',
        desc='What text messages Osprey Power Wash sends, how often, how to get '
             'them and how to stop them. Reply STOP to opt out at any time.',
        lead='Last updated ' + LEGAL_UPDATED + '. Plain terms for the texts we send about '
             'your job and, if you have agreed to them, our occasional offers.',
        body=[
            ('The short version', [
                'Osprey Power Wash sends text messages about work you have booked with us, '
                'and separately - only if you have agreed to them - occasional offers. '
                'Message frequency varies. Message and data rates may apply. Reply STOP to '
                'cancel or HELP for help. Agreeing to marketing texts is not a condition of '
                'buying anything from us.',
            ]),
            ('What we send', [
                '<strong>About your job:</strong> confirmation that a booking is in the '
                'diary, a reminder the day before, a message if we are running late or the '
                'weather has moved the date, and questions about access, gates or where to '
                'park.',
                '<strong>Offers, only if you agreed:</strong> a seasonal reminder that it is '
                'about time the house was washed again, or a discount when we are already '
                'working in your street. These go only to people who ticked the consent box '
                'or told us in writing that they wanted them.',
                'A typical message reads: "Osprey Power Wash: reminder - we are scheduled at '
                'your property tomorrow between 9am and 11am. Reply STOP to opt out."',
            ]),
            ('How you sign up', [
                'By giving us your mobile number when you book online, ask for a quote, or '
                'ask us to text you, you agree that we may text you about that job.',
                'For offers, tick the box on the booking form that says so, or tell us in '
                'writing. The box is never ticked for you, and you can book without it.',
                'You can also start the conversation yourself by texting us on %(phone)s. '
                'Doing that means we may text you back.',
            ]),
            ('How often', [
                'Message frequency varies. Most jobs generate two or three messages around '
                'the appointment. If you have agreed to offers, expect no more than a couple '
                'a month and usually fewer.',
            ]),
            ('What it costs', [
                'We do not charge for text messages. Message and data rates may apply from '
                'your own mobile carrier, depending on your plan.',
            ]),
            ('How to stop', [
                'Reply <strong>STOP</strong> to any message from us. You will get one last '
                'message confirming you have been removed, and nothing after that. You can '
                'also simply tell us on the phone or by email and we will take the number '
                'off.',
                'Reply <strong>HELP</strong> to any message and we will text back our phone '
                'number and email address. Or call us on '
                '<a href="tel:%(e164)s">%(phone)s</a> at any time.',
                'Stopping texts does not cancel your appointment. If you stop texts we will '
                'confirm and remind you by email or phone instead.',
            ]),
            ('Delivery is not guaranteed', [
                'Text messages depend on your mobile carrier and on your phone having '
                'signal. We cannot guarantee that every message arrives, or arrives on time, '
                'and carriers are not liable for delayed or undelivered messages. Anything '
                'genuinely important about your job - a cancellation, a change of date - we '
                'will email or call about as well.',
            ]),
            ('Your privacy', [
                'Your mobile number and your consent are never sold, rented or shared with '
                'anyone else for their marketing. Our '
                '<a href="privacy.html">Privacy Policy</a> has the detail on what we hold '
                'and what we do with it.',
            ]),
            ('Questions', [
                'Call <a href="tel:%(e164)s">%(phone)s</a> or email '
                '<a href="mailto:%(email)s">%(email)s</a>. Osprey Power Wash is a registered '
                'trade name of Tidal Wash LLC.',
            ]),
        ],
    ),
]


def build_legal(p):
    """A legal page: same chrome, no sales pitch, no cross-link grids. Whoever
    is reading it is either a customer checking what happens to their number or
    a carrier reviewing the texting campaign, and neither wants an upsell."""
    canonical = '%s/%s.html' % (SITE, p['slug'])
    ld = {'@context': 'https://schema.org', '@graph': [
        ld_business(),
        {'@type': 'WebPage', '@id': canonical, 'url': canonical,
         'name': p['title'], 'description': p['desc'],
         'publisher': {'@id': SITE + '/#business'},
         'dateModified': LEGAL_UPDATED_ISO},
    ]}
    sub = {'phone': PHONE_PRETTY, 'e164': PHONE_E164, 'email': EMAIL}
    body = [(h, [para % sub for para in paras]) for h, paras in p['body']]
    parts = [
        head(p['title'], p['desc'], canonical, 'house-washing.jpg', ld),
        NAV, MOB,
        '<section class="sub-hero">',
        '  <div class="crumb"><a href="index.html">Home</a> &rsaquo; %s</div>' % html.escape(p['nav']),
        '  <h1>%s<em>%s</em></h1>' % p['h1'],
        '  <p>%s</p>' % p['lead'],
        '</section>',
        '<section>',
        '  <div class="prose">',
        prose(body),
        '  </div>',
        '</section>',
        FOOT, TAIL,
    ]
    return '\n'.join(parts)


def main():
    global NAV, MOB, FOOT

    slugs = {s['slug'] for s in SERVICES}
    if slugs != set(CARDS) or slugs != set(ALTS):
        print('!! SERVICES, CARDS and ALTS disagree:')
        print('   no card:  ', sorted(slugs - set(CARDS)))
        print('   no service:', sorted(set(CARDS) - slugs))
        print('   no alt:   ', sorted(slugs - set(ALTS)))
        raise SystemExit(1)

    NAV, MOB, FOOT = chrome()

    os.makedirs('css', exist_ok=True)
    open('css/page.css', 'w', encoding='utf-8', newline='\r\n').write(PAGE_CSS)

    written = []
    for s in SERVICES:
        fn = s['slug'] + '.html'
        open(fn, 'w', encoding='utf-8', newline='\r\n').write(build_service(s))
        written.append(fn)
    for t in TOWNS:
        fn = t['slug'] + '.html'
        open(fn, 'w', encoding='utf-8', newline='\r\n').write(build_town(t))
        written.append(fn)

    legal = []
    for p in LEGAL_PAGES:
        fn = p['slug'] + '.html'
        open(fn, 'w', encoding='utf-8', newline='\r\n').write(build_legal(p))
        legal.append(fn)
    written += legal

    # ---- sitemap + robots ----
    urls = ['/'] + ['/' + f for f in written]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    lowpri = {'/' + f for f in legal}
    for u in urls:
        pri = '1.0' if u == '/' else '0.3' if u in lowpri else '0.8'
        sm.append('  <url><loc>%s%s</loc><priority>%s</priority></url>' % (SITE, u, pri))
    sm.append('</urlset>')
    open('sitemap.xml', 'w', encoding='utf-8', newline='\r\n').write('\n'.join(sm))

    open('robots.txt', 'w', encoding='utf-8', newline='\r\n').write(
        'User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n' % SITE)

    print('generated %d pages:' % len(written))
    for f in written:
        print('   %-34s %6.1f KB' % (f, os.path.getsize(f) / 1024))
    print('   css/page.css')
    print('   sitemap.xml  (%d urls)' % len(urls))
    print('   robots.txt')


if __name__ == '__main__':
    main()
