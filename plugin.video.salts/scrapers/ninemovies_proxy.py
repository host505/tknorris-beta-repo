"""
    SALTS XBMC Addon
    Copyright (C) 2014 tknorris

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import base64
from salts_lib import log_utils
from salts_lib import scraper_utils
import proxy

scraper_key = base64.b64decode('cGFzc180X25pbmU=')
scraper_url = base64.b64decode('aHR0cDovL3Rrbm9ycmlzLm9mZnNob3JlcGFzdGViaW4uY29tL25pbmVtb3ZpZXNfc2NyYXBlci50eHQ=')
file_name = 'ninemovies_scraper.py'

class NineMovies_Proxy(proxy.Proxy):
    try:
        scraper_utils.update_scraper(file_name, scraper_url, scraper_key)
        from ninemovies_scraper import NineMovies_Scraper as real_scraper
    except Exception as e:
        real_scraper = None
        log_utils.log('import failed: %s' % (e), log_utils.LOGDEBUG)
