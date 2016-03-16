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


BASE_URL = 'http://mysticland1.org'

class MysticLand_Scraper(scraper.Scraper):
    base_url = BASE_URL

    def __init__(self, timeout=scraper.DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.base_url = kodi.get_setting('%s-base_url' % (self.get_name()))

    @classmethod
    def provides(cls):
        return frozenset([VIDEO_TYPES.TVSHOW, VIDEO_TYPES.EPISODE])

    @classmethod
    def get_name(cls):
        return 'MysticLand'

    def resolve_link(self, link):
        return link

    def format_source_label(self, item):
        if 'format' in item:
            label = '[%s] (%s) %s' % (item['quality'], item['format'], item['host'])
        else:
            label = '[%s] %s' % (item['quality'], item['host'])
        return label

    def get_sources(self, video):
        source_url = self.get_url(video)
        hosters = []
        if source_url and source_url != FORCE_NO_MATCH:
            for episode in self.__find_episode(source_url, video):
                _show_title, _season, _episode, height, extra = scraper_utils.parse_episode_link(episode)
                if 'dubbed' in extra.lower(): continue
                stream_url = episode + '|User-Agent=%s' % (scraper_utils.get_ua())
                hoster = {'multi-part': False, 'host': self._get_direct_hostname(stream_url), 'class': self, 'quality': scraper_utils.height_get_quality(height), 'views': None, 'rating': None, 'url': stream_url, 'direct': True}
                if 'x265' in extra: hoster['format'] = 'x265'
                hosters.append(hoster)
            
        return hosters

    def get_url(self, video):
        return super(MysticLand_Scraper, self)._default_get_url(video)

    def _get_episode_url(self, show_url, video):
        force_title = scraper_utils.force_title(video)
        if not force_title:
            if self.__find_episode(show_url, video):
                return scraper_utils.pathify_url(show_url)

    def __find_episode(self, show_url, video):
        matches = {}
        show_url = urlparse.urljoin(self.base_url, show_url)
        html = self._http_get(show_url, cache_limit=2)
        fragment = dom_parser.parse_dom(html, 'div', {'id': 'season0*%s' % (video.season)})
        if fragment:
            titles = dom_parser.parse_dom(fragment[0], 'a', ret='title')
            links = dom_parser.parse_dom(fragment[0], 'a', ret='href')
            for title, link in zip(titles, links):
                match = re.search('[._ -]S%02d[._ -]?E%02d[._ -]' % (int(video.season), int(video.episode)), title, re.I)
                if match:
                    matches[link] = title
        return matches
        
    def search(self, video_type, title, year, season=''):
        results = []
        search_url = urlparse.urljoin(self.base_url, '/?s=%s' % (urllib.quote_plus(title)))
        html = self._http_get(search_url, cache_limit=24)
        links = dom_parser.parse_dom(html, 'a', {'class': 'SearchReadMore'}, ret='href')
        titles = dom_parser.parse_dom(html, 'a', {'class': 'SearchReadMore'}, ret='title')
        for match_url, match_title in zip(links, titles):
            match_title = re.sub('[^\x00-\x7F]', '', match_title)
            result = {'url': scraper_utils.pathify_url(match_url), 'title': scraper_utils.cleanse_title(match_title), 'year': ''}
            results.append(result)
        return results

    def __get_files(self, url, cache_limit=.5):
        sources = []
        for row in self.__parse_directory(self._http_get(url, cache_limit=cache_limit)):
            source_url = urlparse.urljoin(url, row['link'])
            if row['directory']:
                sources += self.__get_files(source_url)
            else:
                row['url'] = source_url
                sources.append(row)
        return sources
    
    def __parse_directory(self, html):
        rows = []
        for match in re.finditer('\s*<a\s+href="([^"]+)">([^<]+)</a>\s+(\d+-[a-zA-Z]+-\d+ \d+:\d+)\s+(-|\d+)', html):
            link, title, date, size = match.groups()
            if title.endswith('/'): title = title[:-1]
            row = {'link': link, 'title': title, 'date': date}
            if link.endswith('/'):
                row['directory'] = True
            else:
                row['directory'] = False

            if size == '-':
                row['size'] = None
            else:
                row['size'] = size
            rows.append(row)
        return rows