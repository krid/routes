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

from django.shortcuts import render
from django.views.decorators.http import require_safe
from django import forms
from django.utils.text import slugify

from .models import Ride, Route, Segment, RouteSegment, RouteDate


class SearchForm(forms.Form):
    """    
    
    FIXME Add min/max and exclude/include validators
    date (or just "not recent"?)
    Use tags?
    """

    ride = forms.ModelChoiceField(Ride.objects.all(), initial='egan')
    min_distance = forms.ChoiceField(
        ((0, 0), (10, 10), (15, 15), (20, 20), (25, 25), (30, 30), (40, 40),
         (50, 50), (60, 60), (70, 70), (80, 80), (90, 90), (100, 100)),
        initial=0)
    max_distance = forms.ChoiceField(
        ((0, 0), (10, 10), (15, 15), (20, 20), (25, 25), (30, 30), (40, 40),
         (50, 50), (60, 60), (70, 70), (80, 80), (90, 90), (100, 100),
         ("", "Unlimited")),
        initial="", required=False)
    min_climbing = forms.ChoiceField(
        ((0, 0), (1000, 1000), (1500, 1500), (2000, 2000), (2500, 2500),
         (3000, 3000), (4000, 4000), (5000, 5000), (6000, 6000), (7000, 7000),
         (8000, 8000), (9000, 9000), (10000, 10000)),
        initial=0)
    max_climbing = forms.ChoiceField(
        ((0, 0), (1000, 1000), (1500, 1500), (2000, 2000), (2500, 2500),
         (3000, 3000), (4000, 4000), (5000, 5000), (6000, 6000), (7000, 7000),
         (8000, 8000), (9000, 9000), (10000, 10000), ("", "Unlimited")),
        initial="", required=False)
    include_segment = forms.ModelChoiceField(Segment.objects.all(), required=False)
    exclude_segment = forms.ModelChoiceField(Segment.objects.all(), required=False)
#     min_grade = forms.ChoiceField((
#         (5, '5%'),
#         (8, '8%'),
#         (10, '10%'),
#         (13, '13%'),
#         (15, '15%'),
#         (18, '18%'),
#         (20, '20%'),
#     ))
#     max_grade = forms.ChoiceField((
#         (5, '5%'),
#         (8, '8%'),
#         (10, '10%'),
#         (13, '13%'),
#         (15, '15%'),
#         (18, '18%'),
#         (20, '20%'),
#     ))
#     start_date = forms.DateField(required=False,
#         widget=forms.TextInput(attrs={'class': 'datepicker'}))
#     search_type = forms.ChoiceField((('routes', 'Routes'),
#                                      ('segments', 'Segments')),
#                                      widget=forms.RadioSelect,
#                                      initial='routes')


@require_safe
def show_routes(request):
    logging.info("show_routes")
    params = None
    if len(request.GET) > 0:
        form = SearchForm(request.GET)
        if form.is_valid():
            params = form.cleaned_data
    else:
        form = SearchForm()
    if params is None:
        routes = Route.objects.all()
    else:
        # Filter Routes by search criteria
        routes = Route.objects.filter(ride=params['ride'],
                                      distance__gte=params['min_distance'],
                                      climbing__gte=params['min_climbing'])
        if params['max_distance']:
            routes = routes.filter(distance__lte=params['max_distance'])
        if params['max_climbing']:
            routes = routes.filter(climbing__lte=params['max_climbing'])
        if params['include_segment']:
            routes = routes.filter(segments=params['include_segment'])
        if params['exclude_segment']:
            routes = routes.exclude(segments=params['exclude_segment'])

    # Can't find a way to sort by least recently used via the DB
    routes = list(routes)
    routes.sort(key=lambda x: (x.routedate_set.latest().date, x.distance),
                reverse=True)
    return render(request, "routes.html",
                  dict(routes=routes, form=form))


@require_safe
def show_segments(request):
    logging.info("show_segments")
    return render(request, "segments.html",
                  dict(segments=Segment.objects.all()))


@require_safe
def show_route(request, route_pk):
    logging.info("show_route %d", route_pk)
    route = Route.objects.get(pk=route_pk)
    return render(request, "route.html", dict(route=route))


@require_safe
def show_segment(request, slug):
    logging.info("show_segment %s", slug)
    segment = Segment.objects.get(slug=slug)
    return render(request, "segment.html", dict(segment=segment))


class RouteForm(forms.Form):
    """Form for adding and editing Routes.
    """
    ride = forms.ModelChoiceField(Ride.objects.all(), initial='egan')
    date = forms.DateField(required=False)
    distance = forms.IntegerField(required=True)
    climbing = forms.IntegerField(required=True)
    name = forms.CharField(max_length=100, required=False)
    cue_sheet = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 8, 'cols': 80}),
        required=True)
    intervals = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 8, 'cols': 80}),
        required=True)
    url = forms.URLField(
        widget=forms.URLInput(attrs={'size': '60'}),
        required=False)
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'cols': 60}),
        required=False)
    action = forms.ChoiceField(choices=(('validate', 'validate'),
                                        ('create', 'create')))


def add_route(request):
    logging.info("add_route")
    params = None
    if len(request.POST) > 0:
        form = RouteForm(request.POST)
        if form.is_valid():
            params = form.cleaned_data
    else:
        form = RouteForm()
    if params is None:
        # Send blank form
        return render(request, "add-route.html", dict(form=form))
    else:
        seg_names = re.split(',\s*', params['intervals'].replace('\n', ' '))
        slugged = {slugify(x): x for x in seg_names}
        existing_segments = Segment.objects.filter(slug__in=slugged.keys())
        existing_slugs = {s.slug for s in existing_segments}
        new_segments = [name for slug, name in slugged.items()
                    if slug not in existing_slugs]
        route = Route(ride=params['ride'],
                      distance=params['distance'],
                      climbing=params['climbing'],
                      cue_sheet=params['cue_sheet'],
                      url=params['url'],
                      notes=params['notes'])
        if params['action'] == "validate":
            # Show the user the route and the segments
            return render(request, "add-route.html",
                          dict(form=form,
                               validated=True,
                               route=route,
                               routedate=params['date'],
                               new_segments=new_segments,
                               existing_segments=existing_segments))
        else:
            # Validated, create the new route and any new segments
            seg_by_slug = {s.slug: s for s in existing_segments}
            for ns in new_segments:
                seg, _ = Segment.objects.get_or_create(name=ns, slug=slugify(ns))
                seg_by_slug[seg.slug] = seg
            route.save()
            for i, sn in enumerate(seg_names):
                RouteSegment.objects.create(route=route,
                                            segment=seg_by_slug[slugify(sn)],
                                            order=i)
            if params['date']:
                RouteDate.objects.create(route=route,
                                         date=params['date'],
                                         ride=params['ride'])
            return render(request, "route.html",
                          dict(route=route,
                               message="Route Created"))

