# Routes - Database for managing bike ride data
# Copyright (C) 2016, Dirk Bergstrom, dirk@otisbean.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re
import logging

from django.core.management.base import BaseCommand
from django.template.defaultfilters import slugify

from main import RoutesError
from routes.models import Ride, Route, Segment, RouteDate, RouteSegment


LOG = logging.getLogger('routes')


segment_cache = {}

def reconcile_segments(names):
    """Print a list of ambiguous segment names.
    
    Automatic de-duping isn't practical (need to look at a map for each
    route), so we find possible duplicates and print them out for
    manual examination.
    """
    segments = {}
    for s in Segment.objects.all():
        segments[s.slug] = dict(name=s.name, slug=s.slug, existing=True)
    for name in names:
        slug = slugify(name)
        if slug not in segments:
            segments[slug] = dict(name=name, slug=slug, existing=False)
    comps = dict(segments)
    for slug, segdata in segments.items():
        multiples = []
        for s, sd in comps.items():
            if slug in s or s in slug:
                multiples.append(sd)
        if len(multiples) > 1:
            print("Found multiples for", segdata['name'])
            for m in multiples:
                del(comps[m['slug']])
                print(m['name'], "[existing]" if m['existing'] else "")
            print("")


route_re = r"""
(?P<dates>\d\d\d\d-\d\d-\d\d[,\d\s-]*?)\n\n

(?:\[(?P<notes>.*?)\]\n+)?

Route:\s+(?P<cue_sheet>.*?)\n\n

Intervals:\s+(?P<segments>.*?)\.?\n\n

(?:Distance:\s+)?(?P<distance>[\d\.]+)\s+[mM]iles(?:\s*[/,]\s+(?P<climbing>\d+)\s+ft\.?)?\n
(?:(?P<urls>(?:^http.*?$\n?)+)\n)?
(?P<timing>\d+.*?$)?
"""

def do_import(fname, find_dupes, dry_run):
    with open(fname) as egan_txt:
        everything = egan_txt.read()
    _top, route_txt = everything.split("## CUT ##")
    raw_routes = route_txt.split("========")
    routes = []
    for i, r in enumerate(raw_routes):
        mat = re.search(route_re, r, re.DOTALL | re.VERBOSE | re.MULTILINE)
        if not mat:
            raise RoutesError("""Can't parse route {}: "{}..."\n""".
                  format(i, r))
        else:
            parts = mat.groupdict()
            dates = re.split(r',\s*', parts['dates'].replace('\n', ' '))
            cue_sheet = parts['cue_sheet'].replace('\n', ' ')
            segments = re.split(',\s*', parts['segments'].replace('\n', ' '))
            urls = parts['urls'] or ""
            urls = urls.split()
            climbing = float(parts['climbing']) if parts['climbing'] else None
            distance = float(parts['distance']) if parts['distance'] else None
            routes.append(dict(dates=dates,
                               notes=parts['notes'] or "",
                               cue_sheet=cue_sheet,
                               segments=segments,
                               distance=distance,
                               climbing=climbing,
                               urls=urls,
                               timing=parts['timing']))
            LOG.debug(routes[-1])
    if find_dupes:
        segs = set()
        for r in routes:
            segs.update(r['segments'])
        reconcile_segments(segs)
        return
    egan = Ride.objects.get(slug="egan")
    new_segments = 0
    for r in routes:
        segs = []
        for s in r['segments']:
            if dry_run:
                segs.append(s)
            else:
                seg, created = Segment.objects.get_or_create(name=s,
                                                             slug=slugify(s))
                new_segments += 1 if created else 0
                segs.append(seg)
        if r['timing']:
            r['notes'] += "\n" + r['timing']
        if len(r['urls']) > 1:
            r['notes'] += "\n" + r['urls'][1]
            url = r['urls'][0]
        else:
            url = ''.join(r['urls'])
        r['notes'] = r['notes'].strip()
        route = Route(ride=egan,
                      distance=r['distance'],
                      climbing=r['climbing'],
                      cue_sheet=r['cue_sheet'],
                      url=url,
                      notes=r['notes'])
        if dry_run:
            LOG.info("%.1f mi Route with %d ft. of climbing on %s with segments %s",
                     route.distance, route.climbing, r['dates'], [str(s) for s in segs])
        else:
            route.save()
            for i, seg in enumerate(segs):
                RouteSegment.objects.create(route=route,
                                            segment=seg,
                                            order=i)
            for d in r['dates']:
                RouteDate.objects.create(route=route,
                                         date=d,
                                         ride=egan)
            LOG.info("Route %s", route)
    LOG.info("Created %d Routes and %d new Segments",
             len(routes), new_segments)


class Command(BaseCommand):

    help = "Convert Egan Ride text file into Django Models."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help="Show without doing.")
        parser.add_argument('--find-dupes', action='store_true',
                            help="Find possible duplicate segments.")
        parser.add_argument('route-file', action='store',
                            help="File of routes in text format")

    def handle(self, *args, **options):
        if options['verbosity'] > 1:
            logging.getLogger('routes').setLevel(logging.DEBUG)
        else:
            logging.getLogger('routes').setLevel(logging.INFO)

        try:
            do_import(options['route-file'], options['find_dupes'],
                      options['dry_run'])
        except Exception:
            logging.exception("Horrible things happened!")
            if options.get('traceback'):
                import pdb;
                pdb.post_mortem()
            raise

