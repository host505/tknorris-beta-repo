# -*- coding: utf-8 -*-
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
from salts_lib import dom_parser
from salts_lib import kodi
from salts_lib import log_utils
from salts_lib import scraper_utils
from salts_lib.constants import FORCE_NO_MATCH
from salts_lib.constants import VIDEO_TYPES
import scraper

BASE_URL = 'http://tv.dl-pars.in'

class DLPars_Scraper(scraper.Scraper):
    base_url = BASE_URL

    def __init__(self, timeout=scraper.DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.base_url = kodi.get_setting('%s-base_url' % (self.get_name()))

    @classmethod
    def provides(cls):
        return frozenset([VIDEO_TYPES.TVSHOW, VIDEO_TYPES.EPISODE])

    @classmethod
    def get_name(cls):
        return 'DL-Pars'

    def resolve_link(self, link):
        return link

    def format_source_label(self, item):
        if 'format' in item:
            label = '[%s] (%s) %s' % (item['quality'], item['format'], item['host'])
        else:
            label = '[%s] %s' % (item['quality'], item['host'])
        if 'size' in item:
            label += ' (%s)' % (item['size'])
        return label

    def get_sources(self, video):
        hosters = []
        source_url = self.get_url(video)
        if source_url and source_url != FORCE_NO_MATCH:
            _show_title, _season, _episode, height, _extra = scraper_utils.parse_episode_link(source_url)
            stream_url = urlparse.urljoin(self.base_url, source_url) + '|User-Agent=%s' % (scraper_utils.get_ua())
            hoster = {'multi-part': False, 'host': self._get_direct_hostname(stream_url), 'class': self, 'quality': scraper_utils.height_get_quality(height), 'views': None, 'rating': None, 'url': stream_url, 'direct': True}
            hosters.append(hoster)
            
        return hosters

    def get_url(self, video):
        return self._default_get_url(video)

    def _get_episode_url(self, show_url, video):
        force_title = scraper_utils.force_title(video)
        if not force_title:
            show_url = urlparse.urljoin(self.base_url, show_url)
            html = self._http_get(show_url, cache_limit=24)
            match = re.search('href="(S0*%s/)"' % (int(video.season)), html, re.I)
            if match:
                season_url = urlparse.urljoin(show_url, match.group(1))
                for item in self._get_files(season_url, cache_limit=1):
                    if '720p' in item['link']: continue
                    match = re.search('[._ -]S%02d[._ -]?E%02d[^\d]' % (int(video.season), int(video.episode)), item['title'], re.I)
                    if match:
                        return scraper_utils.pathify_url(item['url'])

    def search(self, video_type, title, year, season=''):
        results = []
        norm_title = scraper_utils.normalize_title(title)
        html = self._http_get(self.base_url, cache_limit=48)
        for item in self._parse_directory(html):
            if norm_title in scraper_utils.normalize_title(item['title']):
                result = {'url': scraper_utils.pathify_url(item['link']), 'title': scraper_utils.cleanse_title(item['title']), 'year': ''}
                results.append(result)
        return results
