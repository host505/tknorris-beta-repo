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
import scraper
import urllib
import urlparse
import re
import xbmcaddon
import base64
from salts_lib.constants import VIDEO_TYPES
from salts_lib.constants import QUALITIES

BASE_URL = 'http://viooz.ac'

class VioozAc_Scraper(scraper.Scraper):
    base_url = BASE_URL

    def __init__(self, timeout=scraper.DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.base_url = xbmcaddon.Addon().getSetting('%s-base_url' % (self.get_name()))

    @classmethod
    def provides(cls):
        return frozenset([VIDEO_TYPES.MOVIE])

    @classmethod
    def get_name(cls):
        return 'viooz.ac'

    def resolve_link(self, link):
        return link

    def format_source_label(self, item):
        return '[%s] %s' % (item['quality'], item['host'])

    def get_sources(self, video):
        source_url = self.get_url(video)
        hosters = []
        if source_url:
            url = urlparse.urljoin(self.base_url, source_url)
            html = self._http_get(url, cache_limit=.5)

            if re.search('<span[^>]+>\s*Low Quality\s*</span>', html):
                quality = QUALITIES.LOW
            else:
                quality = QUALITIES.HIGH

            pattern = '<div id="cont(.*?)</div>'
            for match in re.finditer(pattern, html, re.DOTALL):
                link_fragment = match.group(1)
                match = re.search('<iframe.*?src="([^"]+)', link_fragment)
                if match:
                    stream_url = match.group(1)
                    direct = False
                else:
                    match = re.search('proxy\.link=([^"&]+)', link_fragment)
                    if match:
                        proxy_link = match.group(1)
                        proxy_link = proxy_link.split('*', 1)[-1]
                        stream_url = self._gk_decrypt(base64.urlsafe_b64decode('YVhWN09hU0M4MDRWYXlUQ0lPYmE='), proxy_link)
                        direct = True
                    else:
                        continue

                # skip these for now till I work out how to extract them
                if 'hqq.tv' in stream_url:
                    continue

                try:
                    host = urlparse.urlsplit(stream_url).hostname.lower()
                except AttributeError:
                    pass
                else:
                    hoster = {'multi-part': False, 'url': stream_url, 'class': self, 'quality': self._get_quality(video, host, quality), 'host': host, 'rating': None, 'views': None, 'direct': direct}
                    hosters.append(hoster)
        return hosters

    def get_url(self, video):
        return super(VioozAc_Scraper, self)._default_get_url(video)

    def search(self, video_type, title, year):
        search_url = urlparse.urljoin(self.base_url, '/search?q=')
        search_url += urllib.quote_plus(title)
        search_url += '&s=t'
        html = self._http_get(search_url, cache_limit=.25)
        pattern = 'class="title_list">\s*<a\s+href="([^"]+)"\s+title="([^"]+)\((\d{4})\)'
        results = []
        for match in re.finditer(pattern, html):
            url, title, match_year = match.groups('')
            if not year or not match_year or year == match_year:
                result = {'url': url.replace(self.base_url, ''), 'title': title, 'year': match_year}
                results.append(result)
        return results

    def _http_get(self, url, cache_limit=8):
        return super(VioozAc_Scraper, self)._cached_http_get(url, self.base_url, self.timeout, cache_limit=cache_limit)
