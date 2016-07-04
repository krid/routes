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

class RoutesError(Exception):
    """The optional code & val attributes are used by the test suite."""

    def __init__(self, message, code=None, val=''):
        self.message = message
        self.code = "{}{}{}".format(code, '-' if val != '' else '', val)
