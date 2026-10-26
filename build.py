#!/usr/bin/env python3
"""Generate the service and town pages, the sitemap and robots.txt.

The home page (index.html) is hand-maintained; everything else is generated
from the content below so the nav, footer and markup never drift apart. The
nav and footer are lifted out of index.html at build time for the same reason
-- change them there and they change everywhere.

Run from the project root:  python build.py
"""
import hashlib
import html
import os
import re

SITE = 'https://ospreypowerwash.com'
BIZ = 'Osprey Power Wash'
LEGAL = 'Tidal Wash LLC'
PHONE_PRETTY = '(609) 732-2007'
PHONE_E164 = '+16097322007'

# Osprey's own Meta dataset ("Osprey CRM Conversions" in Events Manager). The CRM
# sends Osprey's conversions to it too, so site visits and paid jobs land in one
# place. Never put Tidal Wash's pixel (614831401421194) on this site.
META_PIXEL_ID = '1765569311150702'
META_PIXEL = '\n'.join([
    '<!-- Meta Pixel Code -->',
    '<script>',
    '!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?'
    'n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;'
    'n.push=n;n.loaded=!0;n.version=\'2.0\';n.queue=[];t=b.createElement(e);t.async=!0;'
    't.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}'
    '(window,document,\'script\',\'https://connect.facebook.net/en_US/fbevents.js\');',
    "fbq('init','%s');" % META_PIXEL_ID,
    "fbq('track','PageView');",
    '</script>',
    '<noscript><img height="1" width="1" style="display:none" alt="" '
    'src="https://www.facebook.com/tr?id=%s&amp;ev=PageView&amp;noscript=1"></noscript>' % META_PIXEL_ID,
    '<!-- End Meta Pixel Code -->',
])
EMAIL = 'contact@ospreypowerwash.com'
INSTAGRAM = 'https://www.instagram.com/ospreypowerwash/'
BRAND_KEY = 'osprey'   # which workbook the shared booking endpoint writes to

# ---------------------------------------------------------------------------
# CHRISTMAS LIGHTING
#
# The seasonal line. It does not price off square footage like the washing
# does, so it does not go through the estimator: the sale is a free design
# visit, a mockup drawn on a photo of the customer's own house, and three
# tiers priced off that. The booking form on the page books that visit
# through the same endpoint as everything else, so a lighting lead lands in
# the CRM with the alert and the follow-up like any other.
#
# Set a price below and the page shows "from $X". Leave it None and it shows
# "Priced per property" -- so the page is always safe to publish and can
# never show a number nobody has approved.
# ---------------------------------------------------------------------------
XMAS_PACKAGES = [
    dict(
        name='Classic',
        tag='The roofline',
        price='649',
        blurb='The front roofline picked out in C9 bulbs, in whatever color you want. One '
              'clean line along the top of the house, which is the part anyone actually sees '
              'from the road, and the package most people start with.',
        items=[
            'Front roofline in C9 LED, any color &mdash; warm white, cool white, red, green, '
            'blue, multicolor, or a repeating pattern of your own',
            'Cut and fitted to your roof, clipped to the shingle line or the gutter edge',
            'Outdoor timer set to your hours, so nobody has to remember to switch it on',
        ],
    ),
    dict(
        name='Classic Plus',
        tag='Roofline, wreath and beds',
        price='899',
        popular=True,
        badge='Most popular',
        blurb='The roofline, plus the two things that make a house look finished rather '
              'than outlined: a lit wreath on the front of the house, and the shrubs along '
              'the front beds wrapped to match.',
        items=[
            'Everything in Classic',
            'Lit wreath with a bow on the door, gable or garage',
            'Front bed shrubs wrapped in micro LED, matching the roof or deliberately not',
        ],
    ),
    dict(
        name='Destination',
        tag='The whole property',
        price='1,499',
        blurb='The one people slow down for. Roofline, wreaths, beds, the walkway lined, '
              'and the specimen trees in the front yard wrapped trunk and branch.',
        items=[
            'Everything in Classic Plus',
            'Walkway or drive edge lined',
            'Specimen trees wrapped &mdash; trunk, and out along the main branches',
            'Columns, porch rail and pergola wrapped where you have them',
        ],
    ),
]

XMAS_INCLUDED = [
    ('A design drawn on your own house',
     'Nothing here is off a shelf. We take a picture of the front of your house and draw '
     'your display straight onto it &mdash; your colors, your roof line, the trees you '
     'actually have &mdash; so before you spend anything you are looking at a visual of your '
     'own home lit up, not a photo of somebody else&rsquo;s.'),
    ('We use our own lights',
     'So you never have to buy them, maintain them, untangle them or find somewhere to keep '
     'them. Commercial-grade LED, cut to fit your roof, and ours to look after &mdash; no '
     'boxes in your garage for eleven months, and no strand that half-works when it comes '
     'back out.'),
    ('Maintained the whole time it is up',
     'We install it and then look after it. A bulb gone, a run gone dark, a strand pulled '
     'loose by the wind &mdash; one call and we come and fix it, at no charge, for as long as '
     'the display is up.'),
    ('Taken down when you are ready',
     'Takedowns start in January, and you are welcome to keep them lit through to '
     'mid-February if you are in no hurry. Whenever you say, the lights come down and go into '
     'our storage rather than your attic. Next season you call and it goes straight back up.'),
]

# The wording that makes the shared booking form a Christmas form. Everything
# else about it -- the endpoint, the contact-method picker, the photo upload,
# the consent boxes -- is identical on both seasonal pages.
XMAS_FORM_CFG = dict(
    label='Free consultation',
    head='Ask for a consultation',
    lead='Tell us when suits and how you would rather be reached. Most designs are drawn '
         'without us setting foot on the property &mdash; from Street View, or from a couple '
         'of photos you send us here. We come out in person when the house is awkward to see, '
         'or when you would simply rather we did.',
    emailnote='"We will email you, and send the design to the same address."',
    noteph='Steep roof, dogs, gate code, HOA rules&hellip;',
    extraval='Commercial',
    extraopt='Commercial property',
    photoleg='Photos of the front of the house',
    photonote='Up to six. They are resized in your browser before they are sent, so a poor '
              'signal is not a problem. If we cannot see the house well enough from these or '
              'from Street View, we will arrange to come out.',
    subject='holiday lighting consultation and quote',
    btnicon='&#127876;',
    btn='Request my consultation',
    addrerr='Please give us the property address - the design is drawn on a picture of it.',
)

XMAS_PKG_FOOT = ('Every package includes the design, installation, maintenance through the '
                 'season, takedown from January and off-season storage. A 25&#37; materials '
                 'deposit holds your install date and covers the bulbs and cord cut for your '
                 'roof; the balance is due once the lights are on.')

# ---------------------------------------------------------------------------
# FALL PORCH DECOR
#
# The other seasonal line, and deliberately the same shape as the lighting: it
# cannot price off square footage either, so it does not go through the
# estimator. The sale is a free design and three tiers priced off it, booked
# through the same endpoint.
#
# It exists partly on its own merits and partly because it lands the customer
# in front of us in SEPTEMBER, which is when the Christmas calendar needs
# filling. Anyone who books both gets the fall display cleared on the same
# visit the lights go up -- one trip for us, no bare porch for them.
#
# Same price rule as the lighting: a number here becomes "from $X", and
# price=None becomes "Priced per property", so the page is always safe to
# publish.
# ---------------------------------------------------------------------------
# How many porches we will take. It is a real cap, not a marketing one: fall
# installs and the first Christmas light installs share October and the same
# crew. Change this one number and the page changes everywhere.
FALL_SLOTS = 30
FALL_WINDOW = 'September 29 &ndash; October 31'

# Three tiers, and the pumpkin count is the headline on each of them because
# that is how this market is shopped -- competitors sell "22+ / 32+ / 44+" and
# a customer comparing two quotes is counting. The counts below are what the
# prices were built around, so moving one should move the other.
FALL_PACKAGES = [
    dict(
        name='The Doorstep',
        tag='22 pumpkins &middot; either side of the door',
        price='349',
        blurb='The pair of piles that flank the front door, built up out of real pumpkins with '
              'mums and a bale behind them. It is the part of the house people photograph and '
              'the part they walk past, and on most porches it is all you actually need.',
        items=[
            '<strong>22 pumpkins</strong> &mdash; 2 oversize to anchor each side of the door, '
            '8 large and medium, and 12 minis and gourds',
            '2 large mums in a color you pick &mdash; rust, burgundy, gold, cream or purple',
            'A straw bale and a cornstalk bundle to build the height against',
            'Designed for your own steps, delivered and arranged on the day',
            'Taken away whenever you are ready to change the porch over',
        ],
    ),
    dict(
        name='The Full Porch',
        tag='42 pumpkins &middot; door, steps and railings',
        price='699',
        popular=True,
        badge='Most popular',
        blurb='The display spills down the steps instead of stopping at the door. Twice the '
              'pumpkins, white and heirloom varieties mixed in with the orange, and cornstalks '
              'tied to the posts so the whole porch reads as one thing from the road.',
        items=[
            '<strong>42 pumpkins</strong> &mdash; 4 oversize, 12 large and medium, 6 specialty '
            '(white ghost, blue, warty heirloom) and 20 minis and gourds',
            '4 large mums, placed where the display meets the walkway',
            '2 straw bales, 2 cornstalk bundles and ornamental corn for the posts',
            'A mid-season visit to keep the whole display looking its best',
            'Add lighting for $185 and the porch works after dark too',
        ],
    ),
    dict(
        name='The Whole Front',
        tag='70 pumpkins &middot; lighting included',
        price='1,199',
        blurb='For a wide front, a double door, a long walk up, or a house that is going to be '
              'photographed. The porch is the centerpiece and the display carries out to the '
              'walkway and the beds &mdash; and this one is lit, so it still works at night.',
        items=[
            '<strong>70 pumpkins</strong> &mdash; 6 oversize including one true giant, 22 large '
            'and medium, 12 specialty heirloom in blue, pink, green and white, and 30 minis '
            'and gourds',
            '6 large mums, in the beds as well as on the porch',
            '3 straw bales, 3 cornstalk bundles and ornamental corn',
            '<strong>Lighting included</strong> &mdash; mini lights through the display and '
            'spotlights on it, both on a timer',
            'Two mid-season visits, and a second area dressed if you would like one',
        ],
    ),
]

# The after-dark add-on. Deliberately just two things, both of which use kit we
# already own and put up every Christmas -- the fine-wire mini LED we wrap
# shrubs with, and ground spots. No roof lines here: a roof line is a full
# lighting install and belongs on the lighting page, not bolted onto pumpkins.
FALL_LIGHTING = [
    ('&#10024;',
     'Mini lights through the display',
     'from $125',
     'Warm white mini lights on fine wire, woven down through the pumpkins, the bale and the '
     'cornstalks and run to an outdoor timer. It is the same wire we wrap shrubs with at '
     'Christmas &mdash; it all but disappears in daylight, so what you see after dark is a lit '
     'pile of pumpkins and not a string of lights lying on top of them.'),
    ('&#128161;',
     'Spotlights on the porch',
     'from $95',
     'One or two warm spotlights at ground level, throwing the display and the front of the '
     'porch into relief so the whole thing still reads from the road at six in the evening. '
     'Worth more than people expect on a house set back from the street, and it is what makes '
     'the big pumpkins look big after dark.'),
]

FALL_LIGHT_HEAD = 'The porch after dark'

FALL_LIGHT_LEAD = (
    'By the end of October it is dark before most people get home, and a lit porch is the one '
    'people slow down for. It is also the one you see from the car every evening on the way in, '
    'which is really the point of the whole thing. Lighting is what we do all winter, so it is '
    'the easiest thing in the world for us to add while we are there.')

FALL_LIGHT_FOOT = (
    'Add either to any package, or <strong>both together for $185</strong>. Both come included '
    'in The Whole Front. The lights and the timer are ours, and they come away with the display '
    'at the end of the season &mdash; so there is nothing to buy, nothing to store and nothing '
    'to put out again next year. The timer takes care of switching on, which means the porch is '
    'simply lit every evening without anybody thinking about it.')

FALL_INCLUDED = [  # (icon, heading, body)
    ('&#127875;',
     'Designed for your porch, in your colors',
     'Before we buy a thing we look at your steps &mdash; Street View, or a photo from your '
     'phone. Your porch gets a display built to its own shape and scale, in the colors you '
     'like: classic orange, soft cream and white, deep burgundy and rust, or something we put '
     'together for you. You tell us what you love and we do the rest.'),
    ('&#128666;',
     'We bring every last thing',
     'The pumpkins, the mums, the bales, the cornstalks, the gourds, the ornamental corn. All '
     'of it sourced from growers, loaded, driven and carried up your steps by us. There is no '
     'trip to the farm stand, no car full of pumpkins, and nothing for you to lift.'),
    ('&#10024;',
     'Built in an hour, while you get on with your day',
     'Most displays are up inside an hour, and you do not need to be home for any of it. We '
     'text you when we are on the way, and you come back to a porch that looks like somebody '
     'spent the afternoon on it &mdash; because somebody did.'),
    ('&#127810;',
     'Looked after, then taken away when you say',
     'We come back through the season to keep the display looking its best, and the takedown '
     'is already in the price. You pick the day &mdash; right after Halloween, or keep it '
     'through November while it still looks like fall &mdash; and the week after Thanksgiving '
     'at the latest we collect every piece of it. Pumpkins go to compost, and the mums are '
     'yours to keep and plant if you would like them.'),
]

FALL_FORM_CFG = dict(
    label='Free porch design',
    head='Ask for a porch design',
    lead='Tell us when suits and how you would rather be reached. We design most porches '
         'without setting foot on the property &mdash; from Street View, or from a couple of '
         'photos of your own steps sent here &mdash; and come back to you with the display '
         'laid out and priced. Say which colors you like and which you cannot stand.',
    emailnote='"We will email you, and send the design to the same address."',
    noteph='Steps, railings, dogs, gate code, HOA rules&hellip;',
    extraval='Fall Porch: Commercial',
    extraopt='Storefront or business',
    photoleg='Photos of your porch and front steps',
    photonote='Up to six. They are resized in your browser before they are sent, so they go '
              'through quickly straight from your phone. One straight on and one from the '
              'curb is plenty &mdash; we mainly need to see how wide the steps are and '
              'what there is to build the display against.',
    subject='fall porch design and quote',
    btnicon='&#127875;',
    btn='Request my porch design',
    addrerr='Please give us the property address - the display is designed around your own steps.',
)

FALL_PKG_FOOT = ('Every package is designed for your porch, delivered, arranged on the day and '
                 'taken away again when you are ready &mdash; the week after Thanksgiving at '
                 'the latest. The price shown is where that size of display starts; what moves '
                 'it is the width of the porch, the number of steps and how much of the front '
                 'you want covered. A 25&#37; deposit books your install week and buys the '
                 'pumpkins for it; the balance is due on the day it goes up.')

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
             'mildew and that gray-green film from vinyl, cedar shake, stucco '
             'and brick. Instant online quote.',
        image='house-washing.jpg',
        lead='The gray-green film down the side of your house is not dirt, and hosing it '
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
                'the joints and edges, and the general gray that arrives so slowly nobody '
                'notices until it is gone. What comes back is concrete that looks new again, '
                'and the difference shows from the street.',
            ]),
            ('Pavers take less pressure', [
                'Pavers are cleaned with minimal pressure, to preserve the polymeric sand in '
                'the joints that holds them in place. Concrete can take the full force of a '
                'surface cleaner; pavers are washed at a setting that lifts the moss and the '
                'gray without stripping the joints out.',
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
             'Removes the gray, algae and black staining without splintering the '
             'boards.',
        image='deck-patio.jpg',
        lead='A deck goes gray for two reasons at once: the surface of the timber weathers, '
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
    dict(
        slug='fall-porch',
        nav='Fall Porch Decor',
        h1=('FALL PORCH', 'DECORATING'),
        title='Fall Porch Decorating &amp; Pumpkin Delivery in South Jersey',
        desc='Fall porch decorating across South Jersey, from $349. A beautiful display of '
             'pumpkins, mums, bales and cornstalks designed for your porch, delivered, built '
             'and taken away again when you say. Free design, and nothing for you to do.',
        image='fall-porch.jpg',
        # Behind the hero text, under a scrim. Same treatment as the lighting
        # page: show the thing before saying a word about it.
        hero_image='fall-hero.jpg',
        seasonal=True,
        accent='fall',
        theme='s-fall',
        hero_btn=('#book', '&#127875; Ask for a free design'),
        lead='A porch dressed for fall, and nothing for you to do. No trips to the farm '
             'stand, no carrying pumpkins up the steps, and nothing to clear away when '
             'the season is over. We design the display for your own home, bring every '
             'piece, build it, look after it right through fall, and take it all away '
             'again on the day you choose. You pull into the driveway and enjoy it.',
        body=[
            ('A porch worth pulling up to', [
                'There is a real difference between a few pumpkins by the door and a porch that '
                'looks designed, and it comes down to abundance and variety. A pair of '
                'genuinely oversize pumpkins low down to anchor each side. A dozen more stacked '
                'in behind them at different heights so the whole thing has depth. White, blue '
                'and heirloom varieties broken into the orange so the color moves. Minis and '
                'gourds spilling down the treads to carry your eye to the door.',
                'That is what we build, and we build it to your house &mdash; the width of your '
                'steps, the color of your front door, the way the light falls on it in the '
                'afternoon. The result is the porch on the street that people slow down for, '
                'and the one your family walks past every day for two months.',
                'It is also the backdrop for every photograph anybody takes at your house '
                'between now and Thanksgiving, which is worth more than people expect.',
            ]),
            ('Nothing for you to do, start to finish', [
                'Booking takes a few minutes and a couple of photos. After that the whole thing '
                'is ours: choosing the pumpkins, sourcing the mums in the shade you picked, '
                'loading the truck, driving it, carrying it up your steps and arranging it.',
                'You do not need to be home and you do not need to move your car. We text you '
                'when we are on the way, the display goes up in about an hour, and it is there '
                'when you get back. Nothing gets delivered to your driveway for you to deal '
                'with later, and you are never left with a job half done.',
                'Then at the end of the season we come and take all of it away, on a day you '
                'choose. That part is already in the price, so there is nothing to arrange, '
                'nothing to haul out to the curb and nothing to find room for in the garage.',
            ]),
            ('Real pumpkins, mums, bales and cornstalks', [
                'Everything comes from growers, and the mix is what makes a display look '
                'considered. Oversize field pumpkins give it weight at the bottom. Large and '
                'medium jack varieties build the height. White ghost pumpkins, blue Jarrahdale, '
                'green and warty heirlooms give the color somewhere to go, and minis and '
                'ornamental gourds fill in and run down the steps.',
                'Mums are the color you see from the road, so they go where the display meets '
                'the walkway. We buy large, hardy garden mums in full bud, which is what keeps '
                'them coming into flower right through the season. Rust, burgundy, gold, cream '
                'and purple all look wonderful &mdash; pick a favorite, or leave it to us.',
                'Straw bales give the display depth, lifting the back of each pile so it has '
                'shape rather than sitting flat against the house. And cornstalks give it '
                'height: tied to a column, a porch post or a lamp post, they are what makes a '
                'display scale up to a tall front and finish the whole thing off.',
            ]),
            ('Up any week in October, and it runs to Thanksgiving', [
                'Displays go up from the last week of September right through to the end of '
                'October, so you can have it whenever suits you &mdash; in time for the first '
                'pumpkin patch weekend, in time for the school photographs, or in time for '
                'trick-or-treat. Book early and you get the pick of the dates; we only take %d '
                'porches, so the calendar closes when it closes.' % FALL_SLOTS,
                'Thanksgiving falls on November 26 this year, which is as late as it ever gets. '
                'That makes for a long, generous season: even a display that goes up on the '
                'last day of October has a full four weeks to stand, and one that goes up at '
                'the start of the month is there for the best part of two.',
                'Pick the week that suits you when you book, and we will confirm the day. If '
                'you have people coming for a particular weekend, tell us and we will have it '
                'up in good time.',
                'Takedown works the same way: you say when, and we confirm the day rather than '
                'just turning up. Some people like the porch clear the morning after Halloween. '
                'Plenty keep it right through November, because a porch full of pumpkins and '
                'cornstalks still looks like fall long after the costumes are put away. The '
                'The week after Thanksgiving is the latest we collect &mdash; the start of '
                'December this year &mdash; which is usually exactly when you want the porch '
                'ready for Christmas.',
            ]),
            ('Storefronts, offices and business entrances', [
                'The same job at a different scale, and it reads as effort in a way a printed '
                'sign never does. Shop fronts, restaurant entrances, real estate offices and '
                'dealership doors are all worth doing, and a commercial display usually wants '
                'building bigger and bolder because it is being seen from a road rather than '
                'from a front walk.',
                'Tell us on the form if there is a property manager or an approval chain and we '
                'will put the proposal in whatever format they need.',
            ]),
        ],
        scarcity=('Only %d porches this season' % FALL_SLOTS,
                  'Installs run ' + FALL_WINDOW),
        packages=FALL_PACKAGES,
        lighting=(FALL_LIGHTING, FALL_LIGHT_HEAD, FALL_LIGHT_LEAD, FALL_LIGHT_FOOT),
        pkg_label='Three sizes of porch',
        pkg_points=['Designed for your home',
                    'Setup and removal included',
                    'Stress-free &mdash; we handle design, setup, and takedown'],
        pkg_foot=FALL_PKG_FOOT,
        pkg_prefix='Fall Porch: ',
        included=FALL_INCLUDED,
        form=FALL_FORM_CFG,
        crosspromo=dict(
            href='christmas-lights.html', icon='&#127876;',
            kicker='Book both and save',
            head='One porch, two seasons',
            body='Christmas installs start in October, while your fall display is still up, and '
                 'the latest we take the pumpkins away is the week after Thanksgiving &mdash; '
                 'which is exactly when most people want their lights on. Book both and we '
                 'clear the fall display on the same visit, so the porch goes straight from one '
                 'season to the next with nothing in between. One trip instead of two, and '
                 '<strong>$100 off the lighting</strong>.',
            link='See the lighting packages'),
        cta_head='Have the best porch on the street this fall',
        cta='Ask for a design and tell us how you would rather talk &mdash; text, email, phone '
            'or in person. We lay the display out for your own steps, price it, and hold your '
            'install week. Nothing is due until you pick a package, and everything after that '
            'is ours to worry about: we bring it, we build it, we look after it, and we take '
            'it all away again on the day you choose.',
    ),
    dict(
        slug='christmas-lights',
        nav='Christmas Lights',
        h1=('CHRISTMAS LIGHT', 'INSTALLATION'),
        title='Christmas Light Installation in South Jersey',
        desc='Professional Christmas light installation across South Jersey, from $649. We '
             'design it on a photo of your own house, install commercial-grade LED in any '
             'color, maintain it all season, take down from January and store it. Free '
             'custom design, no visit needed.',
        image='christmas-lights.jpg',
        # Behind the hero text, under a scrim. The page should show the work
        # before it says a word about it.
        hero_image='christmas-hero.jpg',
        seasonal=True,
        hero_btn=('#book', '&#127876; Ask for a free design'),
        lead='Nobody enjoys the ladder in December. We design the display on a picture of your '
             'own house - usually without setting foot on the property - then install it, keep '
             'it lit as long as you want it, take it down and store it until next year.',
        body=[
            ('Free design quotes, visualized on your own home', [
                'The package prices are on this page and we are happy to talk numbers on the '
                'phone &mdash; call us, describe the house, and you will get a figure. What '
                'moves it up or down is the length of the roof line, how many peaks there '
                'are, whether it is one story or three, and how much of the yard you want '
                'lit.',
                'What we would rather do as well is show you. We take a picture of the front '
                'of your house and draw the display onto it, so before you commit to anything '
                'you are looking at your own home lit up rather than a number and a '
                'description.',
                'Most of the time we never need to come out to get that picture. Street View '
                'shows us the roof line, the peaks and the beds, and if it is out of date or '
                'the house is set back behind trees you can send us a couple of photos from '
                'your phone when you ask for the consultation. We only arrange to visit when '
                'the house genuinely cannot be seen &mdash; or when you would rather we did.',
                'Either way the design is free and there is nothing to sign at the end of it.',
            ]),
            ('C9 roof lines, mini LED wraps, wreaths and garland', [
                'The lights are not the boxed sets from the hardware store. They are '
                'commercial C9 LED on cord we cut to the length of your roof line, so there '
                'is no doubled-back slack at the corner and no extension lead running across '
                'the front of the house. Bulbs are individually replaceable, which is why one '
                'failure does not take out the run.',
                'Because every bulb goes in separately, the color is genuinely yours to '
                'choose. Warm white is what most people picture when they picture a house '
                'done properly, and cool white reads crisper against brick. But red and warm '
                'white, red and green, blue, multicolor, or a repeating pattern down the run '
                'are all the same job to us &mdash; and there is nothing stopping the roof '
                'being one color and the trees another.',
                'C9 is only the roof line, though. Bed shrubs and hedges are wrapped in mini '
                'LED on a fine wire that all but disappears in daylight, so what you see is '
                'the light rather than the cord. Trees are wrapped the same way &mdash; up '
                'the trunk first, then out along the main branches on the big ones &mdash; '
                'and porch columns, posts and rails are wrapped or spiralled to match.',
                'Then there is everything that hangs: lit wreaths for the door, the gable or '
                'the garage, and garland along window ledges, over doorways and around lamp '
                'posts, finished with a bow in whatever color you have chosen. Walkways and '
                'drive edges get lined. If there is something you have in mind that is not on '
                'that list, ask &mdash; it is all the same commercial-grade kit and the same '
                'maintenance either way. And if you cannot settle on a color, say so on the '
                'form and we will send the same house back to you in two or three, so you are '
                'choosing from pictures rather than from memory.',
            ]),
            ('You never have to own, maintain or store them', [
                'The lights, cord, clips and timers are ours, and they stay ours. You are '
                'paying for a lit house, not for six boxes that sit in a garage for eleven '
                'months, come out the following November with a dead section and a missing '
                'clip, and have to be fought with every year.',
                'Commercial-grade LED is made to sit outside for a full season, so most '
                'displays run from install to takedown without needing a thing. If a problem '
                'does come up, maintenance and replacements are fully included. And when the '
                'season is over the lot goes back into our storage, not your attic.',
            ]),
            ('Installed from October, lit whenever you want', [
                'Installs start in October. The season is a short one &mdash; there are only '
                'so many install days between October and the end of November &mdash; and the '
                'calendar fills as it gets closer, so booking early is how you end up with the '
                'date you actually wanted.',
                'Having them up does not mean having them on. The timer is set to whatever '
                'you say, so the house stays dark until you are ready &mdash; most people '
                'switch on for November, some wait for the day after Thanksgiving. It is '
                'your call and you can change your mind.',
                'Takedowns begin in January, and you can keep them up into mid-February if '
                'you want. Plenty of people like the house lit through the dark end of '
                'winter, so just tell us when you have had enough. You do not need to be home '
                'for either visit, and you do not need to find anywhere to put six boxes of '
                'lights afterwards.',
            ]),
            ('Storefronts, dealerships and HOA entrances', [
                'The commercial side is the same job at a different scale, and it is worth '
                'booking earliest of all &mdash; a car lot or a restaurant wants the lights '
                'on the day after Thanksgiving, which puts the survey in September and the '
                'install well before the retail season starts.',
                'If you have a property manager or a corporate approval chain, say so on '
                'the form and we will put the proposal in the format they need.',
            ]),
        ],
        packages=XMAS_PACKAGES,
        pkg_foot=XMAS_PKG_FOOT,
        included=XMAS_INCLUDED,
        form=XMAS_FORM_CFG,
        crosspromo=dict(
            href='fall-porch.html', icon='&#127875;',
            kicker='Before the lights go up',
            head='Your front porch does not have to wait until December',
            body='We dress porches for fall as well &mdash; real pumpkins, mums, straw bales '
                 'and cornstalks, arranged on your steps in early October and lit if you want '
                 'them. The latest we clear it away is the week after Thanksgiving, so book '
                 'both and the pumpkins go on the same visit your lights go up: the porch '
                 'changes season in one trip, and you get <strong>$100 off the lighting</strong>.',
            link='See the fall porch packages'),
        gallery=[
            ('christmas-roofline.jpg',
             'Warm white C9 bulbs outlining every peak and gable of a two-story house at dusk',
             'Warm white along every gable and peak, with the beds at the front picked out '
             'underneath.'),
            ('christmas-trees.jpg',
             'A lit evergreen beside a house with the walkway lined in warm white at night',
             'The walk lined the whole way to the door, and the big evergreen out front '
             'wrapped top to bottom.'),
            ('christmas-garland.jpg',
             'A stone house with an alternating red and warm white roofline and lit garland '
             'across the window ledges',
             'Alternating red and warm white along the roof, lit garland on the window ledges '
             'and the columns wrapped to match.'),
            ('christmas-color.jpg',
             'A stone house with shrubs and an evergreen wrapped in multicolored lights at dusk',
             'Any color you like: full multicolor on the shrubs and the tree, wreaths in every '
             'window, and uplighting on the stone.'),
        ],
        cta_head='See your own house lit up first',
        cta='Ask for a consultation and tell us how you would rather talk - text, email, '
            'phone or in person. We mock the lights up on a picture of your house and send '
            'the three options priced. Nothing is due until you pick one, and a 25% '
            'materials deposit holds your install date.',
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
        'Decks, porches and outdoor shower floors, composite or wood. Sand and salt grind gray '
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
    'fall-porch': ('\U0001F383', 'Fall Porch Decor', 'Seasonal',
        'A beautiful display of pumpkins, mums, straw bales and cornstalks, designed for your '
        'own steps and built on them any week in October, lit if you would like it. We bring '
        'it, we '
        'build it, we look after it and we take it all away again on the day you choose.'),
    'christmas-lights': ('\U0001F384', 'Christmas Lights', 'Seasonal',
        'Designed on a photo of your own house, installed in commercial-grade LED, '
        'maintained all season, taken down when you are ready and stored until next year. The '
        'design is free, and we rarely need to visit.'),
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
                'drives that have had decades to go gray. All of it cleans up; it simply wants '
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
                'side, black streaking on the roof, and a driveway that has grayed off over a '
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
    'fall-porch': 'A front porch stacked with pumpkins, mums, straw bales and cornstalks in fall',
    'christmas-lights': 'A house roof line and front trees lit with warm white Christmas bulbs at night',
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


def asset_v():
    """A short stamp appended to the stylesheet links, so a browser that is
    holding the old CSS picks up the new one the moment the site is deployed
    rather than whenever it feels like revalidating. Both stylesheets are
    generated -- page.css from PAGE_CSS here, site.css from CSS_ADD in
    seo_home.py -- so hashing those two sources changes the stamp exactly when
    the CSS actually changes, and not on every build."""
    h = hashlib.sha1(PAGE_CSS.encode('utf-8'))
    try:
        h.update(open('seo_home.py', 'rb').read())
    except OSError:
        pass          # still produces a usable stamp from PAGE_CSS alone
    return h.hexdigest()[:8]


def head(title, desc, canonical, image, ld, body_class=''):
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
        META_PIXEL,
        '<link rel="preconnect" href="https://fonts.googleapis.com">',
        '<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;800;900&family=Lato:wght@300;400;700&display=swap" rel="stylesheet">',
        '<link rel="stylesheet" href="css/site.css?v=%s">' % asset_v(),
        '<link rel="stylesheet" href="css/page.css?v=%s">' % asset_v(),
        json_ld(ld),
        '</head>',
        '<body%s>' % (' class="%s"' % body_class if body_class else ''),
    ])


TAIL = ('<script>function toggleMenu(){const m=document.getElementById("mob-menu");'
        'm.classList.toggle("open")}</script>\n</body>\n</html>')


def prose(sections, blocks=False):
    out = []
    for heading, paras in sections:
        if blocks:
            out.append('    <div class="pblock">')
        out.append('    <h2>%s</h2>' % html.escape(heading))
        for p in paras:
            out.append('    <p>%s</p>' % p)
        if blocks:
            out.append('    </div>')
    return '\n'.join(out)


def endcta(line, heading='Get a price without picking up the phone', btn=None):
    # btn lets a page that does not sell through the estimator - the seasonal
    # lighting page - send people somewhere that fits what it is selling.
    href, label = btn or ('index.html#estimate', '&#128203; Get Instant Quote')
    return '\n'.join([
        '<section class="endcta">',
        '  <h2>%s</h2>' % heading,
        '  <p>%s</p>' % line,
        '  <div class="hero-btns" style="justify-content:center">',
        '    <a href="%s" class="btn-primary">%s</a>' % (href, label),
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


# --------------------------------------------------------------------------
# Christmas lighting: packages, the "what's included" strip, and the form that
# books the free design visit.
# --------------------------------------------------------------------------

def price_label(pkg):
    """A package with no agreed price says so rather than inventing one. Put a
    number on price= in XMAS_PACKAGES and it becomes "from $X"."""
    return 'from $%s' % pkg['price'] if pkg.get('price') else 'Priced per property'


def packages_html(pkgs, label='Three ways to do it', foot=None, accent='', points=None):
    if not pkgs:
        return ''
    out = ['<section class="pkg-wrap%s">' % (' ' + accent if accent else ''),
           '  <div class="section-label">%s</div>' % html.escape(label)]
    if points:
        out.append('  <ul class="pkg-points">')
        out += ['    <li>%s</li>' % x for x in points]
        out.append('  </ul>')
    out.append('  <div class="pkgs">')
    for p in pkgs:
        out.append('    <div class="%s">' % ('pkg pop' if p.get('popular') else 'pkg'))
        if p.get('badge'):
            out.append('      <span class="pkg-badge">%s</span>' % html.escape(p['badge']))
        out.append('      <div class="pkg-tag">%s</div>' % p['tag'])
        out.append('      <h3>%s</h3>' % html.escape(p['name']))
        out.append('      <div class="pkg-price">%s</div>' % price_label(p))
        out.append('      <p>%s</p>' % p['blurb'])
        out.append('      <ul>')
        for it in p['items']:
            out.append('        <li>%s</li>' % it)
        out.append('      </ul>')
        out.append('      <a href="#book" class="pkg-cta">Get this priced &rarr;</a>')
        out.append('    </div>')
    out += ['  </div>']
    if foot:
        out.append('  <p class="pkg-foot">%s</p>' % foot)
    out.append('</section>')
    return '\n'.join(out)


def scarcity_html(s):
    if not s.get('scarcity'):
        return ''
    a, b = s['scarcity']
    return ('<section class="scarce-wrap">\n'
            '  <div class="scarce"><span class="scarce-dot"></span>'
            '<span>%s</span><span class="scarce-sep">&middot;</span>'
            '<span>%s</span></div>\n'
            '</section>' % (a, b))


def lighting_html(items, head, lead, foot):
    """The fall page's after-dark block. It is its own section rather than a
    fourth package because it is an add-on to any of them -- and because the
    bulb-swap line underneath it is the whole reason this is worth selling."""
    rows = '\n'.join(
        '    <div class="lit-row"><div class="lit-ico">%s</div><div>'
        '<h3>%s <span class="lit-price">%s</span></h3><p>%s</p></div></div>'
        % (ico, html.escape(name), price, body)
        for ico, name, price, body in items)
    return ('<section class="lit-wrap">\n'
            '  <div class="section-label">After dark</div>\n'
            '  <h2 class="lit-head">%s</h2>\n'
            '  <p class="lit-lead">%s</p>\n'
            '  <div class="lits">\n' + rows + '\n  </div>\n'
            '  <p class="lit-foot">%s</p>\n'
            '</section>') % (html.escape(head), lead, foot)


def included_html(items):
    if not items:
        return ''
    rows = []
    for it in items:
        ico, h, b = it if len(it) == 3 else ('', it[0], it[1])
        rows.append('    <div class="inc">%s<h3>%s</h3><p>%s</p></div>'
                    % ('<div class="inc-ico">%s</div>' % ico if ico else '',
                       html.escape(h), b))
    rows = '\n'.join(rows)
    return ('<section style="background:var(--foam)">\n'
            '  <div class="section-label">What every package includes</div>\n'
            '  <div class="incs">\n' + rows + '\n  </div>\n</section>')


def booking_url():
    """Lifted out of index.html rather than repeated, so the site has one
    endpoint and it cannot drift when the deployment id changes."""
    src = open('index.html', encoding='utf-8').read()
    m = re.search(r'const ASURL\s*=\s*"([^"]+)"', src)
    if not m:
        raise SystemExit('!! could not find ASURL in index.html')
    return m.group(1)


SEASON_FORM = r"""<section class="xbook" id="book">
  <div class="xbook-in">
    <div class="xlabel xb-lab">__F_LABEL__</div>
    <h2>__F_HEAD__</h2>
    <p class="xb-lead">__F_LEAD__</p>

    <div class="xb-grid">
      <label>Your name<input id="x-name" type="text" autocomplete="name"></label>
      <label>Property address<input id="x-addr" type="text" autocomplete="street-address"></label>
      <label>Email<input id="x-email" type="email" autocomplete="email"></label>
      <label>Phone<input id="x-phone" type="tel" autocomplete="tel"></label>
    </div>

    <div class="xb-block">
      <div class="xb-legend">How should we reach you?</div>
      <div class="xb-meths" id="x-meths">
        <button type="button" class="xb-meth on" data-m="Text">&#128172; Text</button>
        <button type="button" class="xb-meth" data-m="Email">&#9993; Email</button>
        <button type="button" class="xb-meth" data-m="Phone call">&#128222; Phone call</button>
        <button type="button" class="xb-meth" data-m="In person">&#127968; In person</button>
      </div>
      <p class="xb-note" id="x-mnote">We will text you to talk it through.</p>
    </div>

    <div class="xb-when off" id="x-when">
      <label>Preferred day<input id="x-date" type="date"></label>
      <label>Preferred time<select id="x-time"></select></label>
    </div>

    <div class="xb-grid" style="margin-top:14px">
      <label>Roughly what you have in mind<select id="x-pkg">
        <option value="">Not sure yet &mdash; show me the options</option>
__OPTS__
        <option value="__F_EXTRAVAL__">__F_EXTRAOPT__</option>
      </select></label>
      <label>Anything we should know<input id="x-note" type="text" placeholder="__F_NOTEPH__"></label>
    </div>

    <div class="xb-block">
      <div class="xb-legend">__F_PHOTOLEG__ <span>optional, and it speeds everything up</span></div>
      <p class="xb-note">__F_PHOTONOTE__</p>
      <label class="xb-drop" id="x-drop">
        <input id="x-files" type="file" accept="image/*" multiple>
        <span>&#128247; Choose photos</span>
      </label>
      <div class="xb-thumbs" id="x-thumbs"></div>
    </div>

    <label class="__CONSENT__"><input type="checkbox" id="x-sms"><span>Text me about my __F_SUBJECT__ with __LEGAL__. These are service messages about my own job.</span></label>
    <label class="__CONSENT__"><input type="checkbox" id="x-smsm"><span>Separately, text me occasional service offers and seasonal specials from __LEGAL__. These are marketing messages.</span></label>
    <p class="__FINE__">Both boxes are optional and independent &mdash; you can ask for a consultation without ticking either, and we will call or email you instead. Message frequency varies. Message and data rates may apply. Reply STOP to opt out or HELP for help. <a href="__PRIVACY__" target="_blank">Privacy Policy</a> <span>&middot;</span> <a href="__SMSTERMS__" target="_blank">Text Message Terms</a></p>

    <div class="xb-err" id="x-err"></div>
    <button class="xb-go" id="x-go">__F_BTNICON__ __F_BTN__</button>
    <div class="xb-prog" id="x-prog"></div>

    <div class="xb-ok" id="x-ok">
      <div class="si">&#9989;</div>
      <h3>Request sent.</h3>
      <p id="x-okmsg"></p>
    </div>

    <p class="xb-alt">Would rather just talk now? <a href="tel:__E164__">__PHONE__</a></p>
  </div>
</section>
<script>
(function(){
  var URL_="__URL__", BRAND="__BRAND__", MAXP=6, method="Text", shots=[];
  function g(i){return document.getElementById(i)}
  function tidy(s){return String(s||"").trim()}
  function post(body){return fetch(URL_,{method:"POST",body:JSON.stringify(body)}).then(function(r){return r.json()})}

  // ---- preferred time: half hours, 8am to 8pm. Evening is on the list because
  // a phone or text consultation does not need daylight and most people are
  // only free after work.
  (function(){
    var sel=g("x-time"), o=document.createElement("option");
    o.value=""; o.textContent="No preference"; sel.appendChild(o);
    for(var m=8*60;m<=20*60;m+=30){
      var h=Math.floor(m/60), mm=m%60, ampm=h<12?"AM":"PM", h12=h%12||12;
      var op=document.createElement("option");
      op.value=(h<10?"0":"")+h+":"+(mm?"30":"00");
      op.textContent=h12+":"+(mm?"30":"00")+" "+ampm;
      sel.appendChild(op);
    }
  })();
  g("x-date").min=new Date().toISOString().split("T")[0];

  // ---- how they want to be reached
  var NOTES={
    "Text":"We will text you to talk it through.",
    "Email":__F_EMAILNOTE__,
    "Phone call":"We will call you at the time you picked.",
    "In person":"We will come out and look at the house with you."
  };
  // Day and time are only asked for when the customer has to be there: a text
  // or an email needs no appointment, and asking for one is a question they
  // have to answer for nothing.
  function needsWhen(m){return m==="Phone call"||m==="In person"}
  function syncWhen(){g("x-when").classList.toggle("off",!needsWhen(method))}
  syncWhen();

  g("x-meths").addEventListener("click",function(e){
    var b=e.target.closest(".xb-meth"); if(!b)return;
    method=b.dataset.m;
    [].forEach.call(this.children,function(c){c.classList.remove("on")});
    b.classList.add("on");
    g("x-mnote").textContent=NOTES[method];
    syncWhen();
  });

  // ---- photos: shrunk in the browser first. A modern phone photo is 3-4MB and
  // six of those is a request no phone signal will finish; 1600px at 0.82 is
  // plenty to draw a design on and lands around 300KB.
  function shrink(file){
    return new Promise(function(res,rej){
      var url=URL.createObjectURL(file), img=new Image();
      img.onload=function(){
        var max=1600,w=img.width,h=img.height;
        if(w>h&&w>max){h=Math.round(h*max/w);w=max}
        else if(h>=w&&h>max){w=Math.round(w*max/h);h=max}
        var c=document.createElement("canvas");c.width=w;c.height=h;
        c.getContext("2d").drawImage(img,0,0,w,h);
        URL.revokeObjectURL(url);
        try{res(c.toDataURL("image/jpeg",0.82))}catch(err){rej(err)}
      };
      img.onerror=function(){URL.revokeObjectURL(url);rej(new Error(file.name))};
      img.src=url;
    });
  }
  function drawThumbs(){
    var box=g("x-thumbs"); box.innerHTML="";
    shots.forEach(function(s,i){
      var d=document.createElement("div"); d.className="xb-thumb";
      var im=document.createElement("img"); im.src=s;
      var x=document.createElement("button"); x.type="button"; x.className="xb-x";
      x.innerHTML="&times;"; x.title="Remove";
      x.onclick=function(){shots.splice(i,1);drawThumbs()};
      d.appendChild(im); d.appendChild(x); box.appendChild(d);
    });
    if(shots.length){
      var n=document.createElement("p"); n.className="xb-note";
      n.textContent=shots.length+" photo"+(shots.length>1?"s":"")+" ready to send.";
      box.appendChild(n);
    }
  }
  g("x-files").addEventListener("change",async function(){
    var files=[].slice.call(this.files), err=g("x-err"); err.textContent="";
    var skipped=0;
    for(var i=0;i<files.length;i++){
      if(shots.length>=MAXP){skipped++;continue}
      try{shots.push(await shrink(files[i]))}catch(e){skipped++}
    }
    this.value="";
    if(skipped){err.textContent="We could not use "+skipped+" of those. Six is the limit, and "+
      "some phone formats will not open in a browser - email them over instead if they matter."}
    drawThumbs();
  });

  // ---- send
  g("x-go").addEventListener("click",async function(){
    var err=g("x-err"), prog=g("x-prog");
    var n=tidy(g("x-name").value), e=tidy(g("x-email").value);
    var p=tidy(g("x-phone").value), a=tidy(g("x-addr").value);
    err.textContent=""; prog.textContent="";
    if(!n){err.textContent="Please give us your name.";return}
    if(!a){err.textContent="__F_ADDRERR__";return}
    if(!e&&!p){err.textContent="Please leave an email address or a phone number.";return}
    if((method==="Text"||method==="Phone call")&&!p){err.textContent="You asked to be reached by "+method.toLowerCase()+", so we need a phone number.";return}
    if(method==="Email"&&!e){err.textContent="You asked to be reached by email, so we need an email address.";return}

    this.disabled=true; this.textContent="Sending…";
    try{
      var d=await post({action:"holidayLead",brand:BRAND,
        customerName:n,customerEmail:e,customerPhone:p,address:a,
        contactMethod:method,
        preferredDate:needsWhen(method)?g("x-date").value:"",
        preferredTime:needsWhen(method)?g("x-time").value:"",
        packageInterest:g("x-pkg").value,notes:tidy(g("x-note").value),
        photoCount:shots.length,
        smsConsent:g("x-sms").checked?"Yes":"No",
        smsMarketingConsent:g("x-smsm").checked?"Yes":"No"});
      // d.user marks a message written for the customer. Anything else is a
      // fault at our end and they should not be reading it.
      if(!d.success){throw new Error(d.user?d.error:"We could not send that just now")}

      // The lead is saved at this point. Photos are a bonus: if one fails we
      // say so and carry on, rather than losing an inquiry over a picture.
      var sent=0, failed=0;
      if(shots.length&&d.photoUpload){
        for(var i=0;i<shots.length;i++){
          prog.textContent="Sending photo "+(i+1)+" of "+shots.length+"…";
          try{
            var r=await post({action:"holidayPhoto",ref:d.ref,index:i,
              mimeType:"image/jpeg",dataBase64:shots[i].split(",")[1]});
            r.success?sent++:failed++;
          }catch(ex){failed++}
        }
      }
      prog.textContent="";
      var msg="We have your request and will confirm the time with you shortly.";
      if(sent)msg+=" "+sent+" photo"+(sent>1?"s":"")+" came through.";
      if(failed)msg+=" "+failed+" would not send - email "+"__EMAIL__"+" and we will add them.";
      g("x-okmsg").textContent=msg;
      g("x-ok").style.display="block";
      this.style.display="none";
      g("x-ok").scrollIntoView({behavior:"smooth",block:"center"});
    }catch(ex){
      err.textContent=ex.message+" - call us on __PHONE__ and we will take it down by hand.";
      this.disabled=false; this.innerHTML="__F_BTNICON__ __F_BTN__";
    }
  });
})();
</script>"""


def season_form_html(pkgs, f, prefix=''):
    """Asks for a consultation through the same endpoint as every other
    booking, so a seasonal lead lands in the CRM with the alert and the
    follow-up exactly like a wash booking does. It is a REQUEST, not a
    booking: nothing goes on the calendar, and photos the customer sends go
    to a Drive folder linked from the lead row. See the HOLIDAY section of
    the booking project for what happens at the other end.

    Both seasonal pages post the same `holidayLead` action, so the fall
    packages are prefixed in the dropdown value -- that is what tells a fall
    porch lead from a lighting lead in the CRM's holiday view, with no change
    needed at the booking end."""
    opts = '\n'.join(
        '        <option value="%s">%s &mdash; %s</option>'
        % (html.escape(prefix + p['name'], quote=True),
           html.escape(p['name']), html.escape(p['tag']))
        for p in pkgs)
    out = (SEASON_FORM
           .replace('__OPTS__', opts)
           .replace('__LEGAL__', BIZ)
           .replace('__EMAIL__', EMAIL)
           .replace('__E164__', PHONE_E164)
           .replace('__PHONE__', PHONE_PRETTY)
           .replace('__BRAND__', BRAND_KEY)
           .replace('__CONSENT__', 'sms-opt')
           .replace('__FINE__', 'sms-fine')
           .replace('__PRIVACY__', 'privacy.html')
           .replace('__SMSTERMS__', 'sms-terms.html')
           .replace('__URL__', booking_url()))
    for k, v in f.items():
        out = out.replace('__F_%s__' % k.upper(), v)
    if '__F_' in out:
        raise SystemExit('!! season form left a token unfilled: %s'
                         % out[out.index('__F_'):out.index('__F_') + 40])
    return out


def crosspromo(c):
    """The band that sends the fall page at the Christmas page and back again.
    The two seasons share one customer, one front door and -- for anyone who
    books both -- one visit, since the fall display comes away on the same
    trip the lights go up."""
    if not c:
        return ''
    return ('<section class="xsell-wrap">\n'
            '  <a class="xsell" href="%s">\n'
            '    <div class="xsell-ico">%s</div>\n'
            '    <div class="xsell-txt">\n'
            '      <div class="xsell-kick">%s</div>\n'
            '      <h3>%s</h3>\n'
            '      <p>%s</p>\n'
            '      <span class="xsell-go">%s &rarr;</span>\n'
            '    </div>\n'
            '  </a>\n'
            '</section>' % (c['href'], c['icon'], html.escape(c['kicker']),
                            html.escape(c['head']), c['body'], html.escape(c['link'])))


def linkgrid(title, items):
    rows = '\n'.join('    <a href="%s">%s</a>' % (h, html.escape(n)) for h, n in items)
    return ('<section>\n  <div class="section-label">%s</div>\n  <div class="linkgrid">\n%s\n  </div>\n</section>'
            % (title, rows))


SERVICE_LINKS = [(s['slug'] + '.html', s['nav']) for s in SERVICES]
TOWN_LINKS = [(t['slug'] + '.html', t['name']) for t in TOWNS]


def build_service(s):
    canonical = '%s/%s.html' % (SITE, s['slug'])
    hero_btn = s.get('hero_btn', ('index.html#estimate', '&#128203; Get Instant Quote'))
    hero_open = '<section class="sub-hero">'
    if s.get('hero_image'):
        hero_open = ('<section class="sub-hero has-photo" style="background-image:url(img/%s)">'
                     % s['hero_image'])
    ld = {'@context': 'https://schema.org', '@graph': [
        ld_business(),
        {'@type': 'Service', 'name': s['nav'], 'serviceType': s['nav'],
         'provider': {'@id': SITE + '/#business'},
         'description': s['desc'],
         'areaServed': [{'@type': 'City', 'name': t['name']} for t in TOWNS]},
    ]}
    parts = [
        head(s['title'], s['desc'], canonical, s['image'], ld, s.get('theme', '')),
        NAV, MOB,
        hero_open,
        '  <div class="crumb"><a href="index.html">Home</a> &rsaquo; %s</div>' % html.escape(s['nav']),
        '  <h1>%s<em>%s</em></h1>' % s['h1'],
        '  <p>%s</p>' % s['lead'],
        '  <div class="hero-btns">',
        '    <a href="%s" class="btn-primary">%s</a>' % hero_btn,
        '    <a href="tel:%s" class="btn-outline">&#128222; %s</a>' % (PHONE_E164, PHONE_PRETTY),
        '  </div>',
        '</section>',
        scarcity_html(s),
        packages_html(s.get('packages'), s.get('pkg_label', 'Three ways to do it'),
                      s.get('pkg_foot'), s.get('accent', ''), s.get('pkg_points')),
        lighting_html(*s['lighting']) if s.get('lighting') else '',
        '<section>',
        '  <div class="%s">' % ('prose cols' if s.get('packages') else 'prose'),
        prose(s['body'], blocks=bool(s.get('packages'))),
        '  </div>',
        '</section>',
        included_html(s.get('included')),
        crosspromo(s.get('crosspromo')),
        season_form_html(s['packages'], s['form'], s.get('pkg_prefix', ''))
        if s.get('form') else '',
        figures(s.get('gallery')),
        linkgrid('Other services', [x for x in SERVICE_LINKS if x[0] != s['slug'] + '.html']),
        linkgrid('Towns we cover', TOWN_LINKS),
        endcta(s.get('cta', 'Prices are on screen in the estimator, and nothing is due until '
                            'the work is finished. Book the date yourself when you are ready.'),
               s.get('cta_head', 'Get a price without picking up the phone'),
               s.get('hero_btn')),
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
/* A photo behind the hero needs a scrim or the white text is unreadable over
   the bright parts of it. Weighted to the left, where the text sits; flattened
   on a phone, where the text crosses the whole frame. */
.sub-hero.has-photo{background-size:cover;background-position:center 62%;background-repeat:no-repeat}
.sub-hero.has-photo:before{content:"";position:absolute;inset:0;background:linear-gradient(95deg,rgba(9,18,22,.9) 0%,rgba(9,18,22,.8) 34%,rgba(9,18,22,.5) 68%,rgba(9,18,22,.28) 100%)}
.sub-hero.has-photo>*{position:relative;z-index:1}
/* A scrim alone still leaves the paragraph crossing a lit roof line. The
   shadow is what makes it legible over the bright spots, and it means the
   photo can stay brighter than it otherwise could. */
.sub-hero.has-photo h1,.sub-hero.has-photo p,.sub-hero.has-photo .crumb{text-shadow:0 1px 16px rgba(0,0,0,.72),0 1px 3px rgba(0,0,0,.5)}
.sub-hero.has-photo p{color:rgba(255,255,255,.88)}
@media(max-width:720px){.sub-hero.has-photo:before{background:linear-gradient(180deg,rgba(9,18,22,.9),rgba(9,18,22,.88))}}
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
/* Two-column explanation, used only on the pages that lead with prices. Real
   CSS columns rather than a grid, so the text flows down one column and into
   the next instead of leaving a ragged row whenever two topics differ in
   length; break-inside keeps a heading with its own paragraphs. */
.prose.cols{max-width:none;column-count:2;column-gap:50px}
.prose.cols .pblock{break-inside:avoid;-webkit-column-break-inside:avoid;margin-bottom:26px}
.prose.cols .pblock h2{margin-top:0;font-size:clamp(1.22rem,2.3vw,1.48rem);margin-bottom:9px}
.prose.cols p{font-size:.915rem;line-height:1.78;margin-bottom:12px}
.prose.cols .pblock:last-child{margin-bottom:0}
@media(max-width:880px){.prose.cols{column-count:1}}
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

/* ---- Christmas lighting ------------------------------------------------
   The seasonal page carries one extra accent - a warm bulb gold - because a
   page about lights that is entirely sea-green reads as a washing page. It is
   scoped to these blocks and never leaks into the rest of the site. */
.pkg-wrap{--gold:#e0a83c}
/* The fall page runs the same blocks on a pumpkin accent rather than a bulb gold. */
.pkg-wrap.fall{--gold:#c2611f}

/* ---- Fall porch page palette -------------------------------------------
   The whole site is drawn from five custom properties, so a seasonal page
   gets its own look by re-pointing those five rather than restating a
   single rule. body.s-fall turns the page autumn; the nav, the mobile menu
   and the footer are pinned straight back to the brand colors, because the
   furniture should not change color from one page to the next. The two
   hand-written gradients (the hero and the after-dark block) name their
   colors directly, so those are the only two that need spelling out. */
body.s-fall{--ink:#1d1206;--ocean:#a8551b;--sky:#edab45;--foam:#fdf2e3;--sand:#faf3e8}
body.s-fall nav,body.s-fall #mob-menu,body.s-fall footer{--ink:#0f1a1f;--ocean:#1b6b72;--sky:#4fd1a5;--foam:#e6f4f1;--sand:#f5f3ee}
body.s-fall .sub-hero{background:linear-gradient(160deg,#1d1206 0%,#4a2410 54%,#8d4616 100%)}
/* The hero photo is bright daylight rather than the lighting page's night
   shots, so the scrim is both warmer and heavier on the left where the text
   sits. The photo is already cropped tight, so it is centered rather than
   pulled down to 62%. */
body.s-fall .sub-hero.has-photo{background-position:center center}
body.s-fall .sub-hero.has-photo:before{background:linear-gradient(95deg,rgba(26,15,6,.94) 0%,rgba(26,15,6,.91) 44%,rgba(30,17,7,.74) 74%,rgba(40,22,9,.4) 100%)}
@media(max-width:720px){body.s-fall .sub-hero.has-photo:before{background:linear-gradient(180deg,rgba(26,15,6,.9),rgba(30,17,7,.9))}}
body.s-fall .btn-primary:hover{box-shadow:0 8px 24px rgba(237,171,69,.42)}
body.s-fall .lit-wrap{background:linear-gradient(160deg,#241607,#17100a 58%,#32190a)}

/* Festive touches, all from one drawing, held in a custom property so the
   pumpkin is defined once and inherited by everything that wants it. */
body.s-fall{--pumpkin:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 20 20'%3E%3Cpath d='M10 6.2c-.6-.6-1.4-1-2.3-1C5.5 5.2 3.7 7.4 3.7 10.1s1.8 4.9 4 4.9c.9 0 1.7-.4 2.3-1 .6.6 1.4 1 2.3 1 2.2 0 4-2.2 4-4.9s-1.8-4.9-4-4.9c-.9 0-1.7.4-2.3 1z' fill='%23c2611f'/%3E%3Cpath d='M10 6.2V4.4c0-.8.7-1.5 1.5-1.5' fill='none' stroke='%234e7c33' stroke-width='1.5' stroke-linecap='round'/%3E%3C/svg%3E")}
.pkg-wrap.fall .pkg li:before{background:var(--pumpkin) center/contain no-repeat;border-radius:0;width:15px;height:15px;left:0;top:.28em}
.pkg-wrap.fall .pkg li{padding-left:24px}
body.s-fall .scarce-dot{width:17px;height:17px;border-radius:0;background:var(--pumpkin) center/contain no-repeat}

/* The three things worth knowing before anyone reads a package, sat directly
   under the section label so they are read on the way to the prices. */
.pkg-points{list-style:none;padding:0;margin:13px 0 6px;display:flex;flex-wrap:wrap;gap:11px 36px}
.pkg-points li{position:relative;padding-left:27px;font-size:1.02rem;font-weight:700;color:var(--ink);letter-spacing:.2px;line-height:1.4}
.pkg-points li:before{content:"";position:absolute;left:0;top:.14em;width:18px;height:18px;background:var(--pumpkin) center/contain no-repeat}
@media(max-width:700px){.pkg-points{flex-direction:column;gap:10px;margin-bottom:2px}.pkg-points li{font-size:.97rem}}
.inc-ico{font-size:1.7rem;line-height:1;margin-bottom:11px}
.pkgs{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px;margin-top:20px;align-items:start}
.pkg{position:relative;background:var(--white);border:1.5px solid #dfe8e6;border-radius:14px;padding:26px 24px 24px;display:flex;flex-direction:column}
.pkg.pop{border-color:var(--gold);box-shadow:0 10px 34px rgba(224,168,60,.16)}
.pkg-badge{position:absolute;top:-11px;left:24px;background:var(--gold);color:#2a1d05;font-size:.66rem;font-weight:800;letter-spacing:1.4px;text-transform:uppercase;padding:4px 11px;border-radius:99px}
.pkg-tag{font-size:.72rem;font-weight:700;letter-spacing:1.6px;text-transform:uppercase;color:var(--ocean)}
.pkg h3{font-family:'Barlow Condensed',sans-serif;font-size:2rem;font-weight:900;color:var(--ink);line-height:1;margin:6px 0 2px;letter-spacing:.5px}
.pkg-price{font-size:1rem;font-weight:700;color:var(--gold);margin-bottom:12px}
.pkg p{color:#556;line-height:1.75;font-weight:300;font-size:.95rem;margin-bottom:14px}
.pkg ul{list-style:none;padding:0;margin:0 0 18px;flex:1}
.pkg li{position:relative;padding:0 0 0 22px;margin-bottom:9px;color:#445;font-size:.9rem;line-height:1.6;font-weight:300}
.pkg li:before{content:"";position:absolute;left:2px;top:.55em;width:7px;height:7px;border-radius:50%;background:var(--gold)}
.pkg-cta{margin-top:auto;display:inline-block;font-weight:700;font-size:.9rem;color:var(--ocean);text-decoration:none}
.pkg-cta:hover{color:var(--ink)}


/* The season cap. It is a real constraint - fall installs and the first
   Christmas installs share October - so it gets stated plainly
   rather than dressed up as a countdown. */
.scarce-wrap{padding-bottom:0}
.scarce{display:flex;flex-wrap:wrap;align-items:center;justify-content:center;gap:10px;background:#fdf3e6;border:1.5px solid #ecd4b0;border-radius:99px;padding:11px 24px;margin:0 auto;width:fit-content;max-width:100%;font-size:.88rem;font-weight:700;color:#8c4a12;letter-spacing:.3px;text-align:center}
.scarce-dot{width:8px;height:8px;border-radius:50%;background:#c2611f;flex:0 0 auto}
.scarce-sep{color:#d6b184}
@media(max-width:520px){.scarce{flex-direction:column;gap:3px;border-radius:14px;padding:11px 18px;font-size:.84rem;line-height:1.4}.scarce-sep{display:none}.scarce-dot{display:none}}

/* After-dark block on the fall page. Dark, because it is about what the porch
   looks like at night and a cream panel makes that point badly. */
.lit-wrap{background:linear-gradient(160deg,#13323a,#0e2830 60%,#1a2b22);color:#fff}
.lit-wrap .section-label{color:#e8a84a}
.lit-head{font-family:'Barlow Condensed',sans-serif;font-size:clamp(1.9rem,4.2vw,2.6rem);font-weight:900;color:#fff;line-height:1.08;margin:6px 0 12px;letter-spacing:.5px}
.lit-lead{color:rgba(255,255,255,.72);line-height:1.8;font-weight:300;max-width:66ch;margin-bottom:28px}
.lits{display:grid;gap:16px;margin-bottom:26px}
.lit-row{display:flex;gap:16px;align-items:flex-start;background:rgba(255,255,255,.055);border:1px solid rgba(255,255,255,.1);border-radius:13px;padding:19px 21px}
.lit-ico{font-size:1.5rem;line-height:1;flex:0 0 auto;margin-top:2px}
.lit-row h3{font-family:'Barlow Condensed',sans-serif;font-size:1.4rem;font-weight:800;color:#fff;letter-spacing:.4px;margin-bottom:6px;line-height:1.15}
.lit-price{display:inline-block;background:rgba(224,168,60,.16);border:1px solid rgba(224,168,60,.35);color:#f0c274;border-radius:99px;padding:2px 11px;font-family:'Inter',system-ui,sans-serif;font-size:.72rem;font-weight:700;letter-spacing:.3px;margin-left:8px;vertical-align:middle;white-space:nowrap}
.lit-row p{color:rgba(255,255,255,.7);line-height:1.72;font-weight:300;font-size:.93rem;margin:0}
.lit-row p strong{color:#f0c274;font-weight:700}
.lit-foot{color:rgba(255,255,255,.78);line-height:1.8;font-weight:300;font-size:.97rem;max-width:72ch;border-top:1px solid rgba(255,255,255,.13);padding-top:22px}
.lit-foot strong{color:#fff;font-weight:700}
@media(max-width:560px){.lit-row{flex-direction:column;gap:9px;padding:17px 18px}.lit-price{margin-left:0;display:block;width:fit-content;margin-top:6px}}
.xsell-wrap{padding-top:0}
.xsell{display:flex;gap:20px;align-items:flex-start;text-decoration:none;background:linear-gradient(105deg,#fff8ec,#fdf1e2 60%,#f7ece2);border:1.5px solid #ecd9bd;border-radius:16px;padding:26px 28px;transition:border-color .18s,box-shadow .18s,transform .18s}
.xsell:hover{border-color:#d9b47a;box-shadow:0 12px 32px rgba(150,100,30,.13);transform:translateY(-2px)}
.xsell-ico{font-size:2.3rem;line-height:1;flex:0 0 auto;margin-top:2px}
.xsell-kick{font-size:.7rem;font-weight:800;letter-spacing:1.6px;text-transform:uppercase;color:#a8681d}
.xsell h3{font-family:'Barlow Condensed',sans-serif;font-size:1.75rem;font-weight:900;color:var(--ink);line-height:1.1;margin:5px 0 9px;letter-spacing:.4px}
.xsell p{color:#5a5147;line-height:1.75;font-weight:300;font-size:.95rem;margin:0 0 13px;max-width:62ch}
.xsell p strong{font-weight:700;color:#8c4a12}
.xsell-go{font-weight:700;font-size:.9rem;color:var(--ocean)}
.xsell:hover .xsell-go{color:var(--ink)}
@media(max-width:560px){.xsell{flex-direction:column;gap:12px;padding:22px 20px}.xsell-ico{font-size:2rem}}
.pkg-foot{max-width:720px;margin-top:22px;color:#667;font-size:.88rem;line-height:1.75;font-weight:300}
.incs{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:22px;margin-top:18px}
.inc h3{font-family:'Barlow Condensed',sans-serif;font-size:1.25rem;font-weight:800;color:var(--ink);margin-bottom:7px;line-height:1.15}
.inc p{color:#556;line-height:1.72;font-weight:300;font-size:.92rem}

.xbook{background:linear-gradient(165deg,var(--ink) 0%,#122b30 60%,#1a3b33 100%);color:#fff}
.xbook-in{max-width:860px;margin:0 auto}
.xbook .xb-lab{color:#e0a83c}
.xbook h2{font-family:'Barlow Condensed',sans-serif;font-size:clamp(1.9rem,4.6vw,2.9rem);font-weight:900;line-height:1.05;margin-bottom:14px;letter-spacing:.5px}
.xb-lead{color:rgba(255,255,255,.7);line-height:1.8;font-weight:300;max-width:620px;margin-bottom:26px}
.xb-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.xb-grid label,.xb-when label{display:flex;flex-direction:column;gap:6px;font-size:.78rem;font-weight:700;letter-spacing:.6px;text-transform:uppercase;color:rgba(255,255,255,.62)}
.xb-grid input,.xb-grid select,.xb-when input,.xb-when select{background:rgba(255,255,255,.07);border:1.5px solid rgba(255,255,255,.16);border-radius:9px;padding:12px 13px;color:#fff;font-family:inherit;font-size:.98rem;font-weight:300;text-transform:none;letter-spacing:0}
.xb-grid input:focus,.xb-grid select:focus,.xb-when input:focus,.xb-when select:focus{outline:none;border-color:#e0a83c;background:rgba(255,255,255,.1)}
.xb-grid select option,.xb-when select option{color:#0f1a1f}
.xb-grid input::placeholder{color:rgba(255,255,255,.3)}
.xb-when{margin-top:22px;display:grid;grid-template-columns:1fr 1fr;gap:14px;align-items:start}
.xb-when.off{display:none}
.xbook .sms-opt{margin-top:12px}
.xbook .sms-opt span{color:rgba(255,255,255,.72)}
.xbook .sms-fine{color:rgba(255,255,255,.4);border-top-color:rgba(255,255,255,.12);margin-top:10px}
.xbook .sms-fine a{color:#e0a83c}
.xbook .sms-fine span{color:rgba(255,255,255,.2)}
.xb-err{color:#ffb4a8;font-size:.9rem;font-weight:700;line-height:1.6;margin-top:14px;min-height:1px}
.xb-go{margin-top:18px;background:#e0a83c;color:#2a1d05;border:none;border-radius:10px;padding:16px 30px;font-family:'Barlow Condensed',sans-serif;font-size:1.15rem;font-weight:800;letter-spacing:1px;text-transform:uppercase;cursor:pointer;transition:transform .15s,box-shadow .15s}
.xb-go:hover{transform:translateY(-2px);box-shadow:0 12px 30px rgba(224,168,60,.3)}
.xb-go:disabled{opacity:.6;cursor:default;transform:none;box-shadow:none}
.xb-ok{display:none;margin-top:20px;background:rgba(255,255,255,.07);border:1.5px solid rgba(224,168,60,.4);border-radius:12px;padding:24px}
.xb-ok .si{font-size:2rem;margin-bottom:6px}
.xb-ok h3{font-family:'Barlow Condensed',sans-serif;font-size:1.6rem;font-weight:800;margin-bottom:6px}
.xb-ok p{color:rgba(255,255,255,.7);line-height:1.7;font-weight:300}
.xb-alt{margin-top:18px;color:rgba(255,255,255,.5);font-size:.9rem;font-weight:300}
.xb-alt a{color:#e0a83c;font-weight:700;text-decoration:none}
.xb-block{margin-top:22px}
.xb-legend{font-size:.78rem;font-weight:700;letter-spacing:.6px;text-transform:uppercase;color:rgba(255,255,255,.62);margin-bottom:9px}
.xb-legend span{text-transform:none;letter-spacing:0;font-weight:400;color:rgba(255,255,255,.38)}
.xb-meths{display:flex;flex-wrap:wrap;gap:9px}
.xb-meth{background:rgba(255,255,255,.07);border:1.5px solid rgba(255,255,255,.16);border-radius:9px;color:#fff;padding:12px 17px;font-family:inherit;font-size:.92rem;font-weight:700;cursor:pointer;transition:all .15s}
.xb-meth:hover{border-color:#e0a83c}
.xb-meth.on{background:#e0a83c;border-color:#e0a83c;color:#2a1d05}
.xb-note{margin-top:9px;color:rgba(255,255,255,.45);font-size:.85rem;font-weight:300;line-height:1.6}
.xb-drop{display:inline-flex;align-items:center;gap:9px;background:rgba(255,255,255,.07);border:1.5px dashed rgba(255,255,255,.26);border-radius:10px;padding:16px 22px;cursor:pointer;color:rgba(255,255,255,.8);font-weight:700;font-size:.92rem;transition:all .15s;margin-top:4px}
.xb-drop:hover{border-color:#e0a83c;color:#fff}
.xb-drop input{position:absolute;width:1px;height:1px;opacity:0;pointer-events:none}
.xb-thumbs{display:flex;flex-wrap:wrap;gap:10px;margin-top:12px}
.xb-thumb{position:relative;width:92px;height:92px;border-radius:9px;overflow:hidden;border:1.5px solid rgba(255,255,255,.16)}
.xb-thumb img{width:100%;height:100%;object-fit:cover;display:block}
.xb-x{position:absolute;top:3px;right:3px;width:22px;height:22px;border:none;border-radius:50%;background:rgba(0,0,0,.65);color:#fff;font-size:15px;line-height:1;cursor:pointer;padding:0}
.xb-x:hover{background:#c0392b}
.xb-thumbs .xb-note{flex-basis:100%;margin-top:0}
.xb-prog{margin-top:10px;color:#e0a83c;font-size:.88rem;font-weight:700;min-height:1px}
@media(max-width:720px){.xb-grid{grid-template-columns:1fr}.xb-when{grid-template-columns:1fr}.xb-meth{flex:1 1 44%}}
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
                'for how much. Quote inquiries that never became jobs are kept for around '
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

    missing = sorted({s['image'] for s in SERVICES
                      if not os.path.exists(os.path.join('img', s['image']))})
    for m in missing:
        print('!! img/%s does not exist - that page has a broken og:image' % m)

    print('generated %d pages:' % len(written))
    for f in written:
        print('   %-34s %6.1f KB' % (f, os.path.getsize(f) / 1024))
    print('   css/page.css')
    print('   sitemap.xml  (%d urls)' % len(urls))
    print('   robots.txt')


if __name__ == '__main__':
    main()
