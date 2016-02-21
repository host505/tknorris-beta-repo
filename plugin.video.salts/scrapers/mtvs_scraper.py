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
import re
import urlparse
import urllib
import base64
from salts_lib import dom_parser
from salts_lib import kodi
from salts_lib import log_utils
from salts_lib import scraper_utils
from salts_lib.constants import FORCE_NO_MATCH
from salts_lib.constants import VIDEO_TYPES
from salts_lib.constants import QUALITIES
import scraper


BASE_URL = 'http://www.mtvs.me'

class MTVS_Scraper(scraper.Scraper):
    base_url = BASE_URL

    def __init__(self, timeout=scraper.DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.base_url = kodi.get_setting('%s-base_url' % (self.get_name()))

    @classmethod
    def provides(cls):
        return frozenset([VIDEO_TYPES.TVSHOW, VIDEO_TYPES.EPISODE])

    @classmethod
    def get_name(cls):
        return 'MTVS'

    def resolve_link(self, link):
        return link

    def format_source_label(self, item):
        if 'label' in item:
            return '[%s] %s (%s)' % (item['quality'], item['host'], item['label'])
        else:
            return '[%s] %s' % (item['quality'], item['host'])

    def get_sources(self, video):
        source_url = self.get_url(video)
        hosters = []
        if source_url and source_url != FORCE_NO_MATCH:
            page_url = urlparse.urljoin(self.base_url, source_url)
            html = self._http_get(page_url, cache_limit=.25)
            for td in dom_parser.parse_dom(html, 'td', {'class': 'name hover'}, ret='data-bind'):
                match = re.search("(https?://[^']+)", td)
                if match:
                    stream_url = match.group(1)
                    host = urlparse.urlparse(stream_url).hostname
                    quality = scraper_utils.get_quality(video, host, QUALITIES.HIGH)
                    hoster = {'multi-part': False, 'host': host, 'class': self, 'quality': quality, 'views': None, 'rating': None, 'url': stream_url, 'direct': False}
                    hosters.append(hoster)
        return hosters

    def get_url(self, video):
        return self._default_get_url(video)

    def _get_episode_url(self, show_url, video):
        url = urlparse.urljoin(self.base_url, show_url)
        html = self._http_get(url, cache_limit=24)
        match = re.search('href="([^"]+/seasons/%s)"' % video.season, html)
        if match:
            season_url = match.group(1)
            episode_pattern = 'href="([^"]*/seasons/%s/episodes/%s(?!\d)[^"]*)' % (video.season, video.episode)
            title_pattern = 'href="(?P<url>[^"]+)[^>]+>\s*Episode\s+\d+\s*-\s*(?P<title>[^<]+)'
            airdate_pattern = 'href="([^"]+)[^>]+>[^<]+</a>\s*</h4>\s*<strong>Release Date:\s*{year}-{p_month}-{p_day}'
            return self._default_get_episode_url(season_url, video, episode_pattern, title_pattern, airdate_pattern)

    def search(self, video_type, title, year, season=''):
        results = []
        search_url = urlparse.urljoin(self.base_url, '/search?q=')
        search_url += urllib.quote_plus(title)
        html = self._http_get(search_url, cache_limit=1)
        fragment = dom_parser.parse_dom(html, 'div', {'id': 'series'})
        match_year = ''
        if fragment:
            for figure in dom_parser.parse_dom(fragment[0], 'figcaption'):
                match = re.search('href="([^"]+)[^>]+>([^<]+)', figure)
                if match:
                    match_url, match_title = match.groups()
                    if not year or not match_year or year == match_year:
                        result = {'url': scraper_utils.pathify_url(match_url), 'title': scraper_utils.cleanse_title(match_title), 'year': match_year}
                        results.append(result)

        return results
