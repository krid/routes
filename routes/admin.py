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

from django.contrib import admin

from .models import Ride, Route, RouteDate, Segment, RouteSegment


class RouteSegmentInline(admin.TabularInline):
    model = RouteSegment
    extra = 1


class RouteDateInline(admin.TabularInline):
    model = RouteDate
    extra = 1


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    inlines = (RouteSegmentInline, RouteDateInline)


for model in (Ride, RouteDate, Segment, RouteSegment):
    admin.site.register(model)
