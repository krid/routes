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

from django.db import models


class Ride(models.Model):

    slug = models.SlugField()
    name = models.CharField(max_length=20)
    tagline = models.CharField(max_length=60)
    email_subject = models.CharField(max_length=100, blank=True)
    email_boilerplate = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Segment(models.Model):

    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=40, blank=False)
    length = models.FloatField(null=True, blank=True)
    altitude = models.SmallIntegerField(null=True, blank=True)
    avg_grade = models.FloatField(null=True, blank=True)
    kom_time = models.TimeField(null=True, blank=True)
    strava_name = models.CharField(max_length=100, blank=True)
    strava_url = models.URLField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


class Route(models.Model):

    ride = models.ForeignKey(Ride)
    name = models.CharField(max_length=100, blank=True)
    distance = models.FloatField(null=True)
    climbing = models.SmallIntegerField(null=True)
    cue_sheet = models.TextField()
    segments = models.ManyToManyField(Segment,
                                      through='RouteSegment',
                                      related_name='routes')
    url = models.URLField(blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        if self.name or not self.pk:
            return "{}: {} - {:.0f} Mi".format(self.ride.name, self.name,
                                           self.distance)
        else:
            segs = self.routesegment_set.all()
            seg_str = ", ".join([s.segment.name for s in segs[:4]])
            seg_str += " ..." if len(segs) > 4 else ""
            return "{}: {:.0f} Mi - {}".format(self.ride.name,
                                               self.distance,
                                               seg_str)


class RouteDate(models.Model):

    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    date = models.DateField()
    ride = models.ForeignKey(Ride, null=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ('date',)
        get_latest_by = 'date'


class RouteSegment(models.Model):

    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    segment = models.ForeignKey(Segment, on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ('order',)
