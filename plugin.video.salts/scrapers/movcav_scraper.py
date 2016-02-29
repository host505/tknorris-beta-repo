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
from salts_lib import scraper_utils
import urlparse
import re
import urllib
import base64
from salts_lib import kodi
from salts_lib import dom_parser
from salts_lib import log_utils
from salts_lib.constants import VIDEO_TYPES
from salts_lib.constants import FORCE_NO_MATCH
from salts_lib.constants import QUALITIES

BASE_URL = 'http://movcav.com'
HEIGHT_MAP = {'MOBILE': 240}

class MovCav_Scraper(scraper.Scraper):
    base_url = BASE_URL

    def __init__(self, timeout=scraper.DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.base_url = kodi.get_setting('%s-base_url' % (self.get_name()))

    @classmethod
    def provides(cls):
        return frozenset([VIDEO_TYPES.MOVIE])

    @classmethod
    def get_name(cls):
        return 'MovCav'

    def resolve_link(self, link):
        return link

    def format_source_label(self, item):
        return '[%s] %s' % (item['quality'], item['host'])

    def get_sources(self, video):
        source_url = self.get_url(video)
        hosters = []
        if source_url and source_url != FORCE_NO_MATCH:
            url = urlparse.urljoin(self.base_url, source_url)
            html = self._http_get(url, cache_limit=.5)
            elements = [
                ['div', {'id': 'cap1'}], ['div', {'class': 'movieplay'}],
                ['li', {'class': 'elemento'}], ['div', {'id': 'player\d+'}]
            ]
            for element in elements:
                for item in dom_parser.parse_dom(html, element[0], element[1]):
                    src = dom_parser.parse_dom(item, 'iframe', ret='src')
                    if not src: src = dom_parser.parse_dom(item, 'a', ret='href')
                    if src:
                        if 'javascript' in src[0]:
                            match = re.search("attr\('src'\s*,\s*'([^']+)", item)
                            if match:
                                src = [match.group(1)]
                            else:
                                src = []
                        hosters += self.__get_embedded(src[0], url)

        new_hosters = []
        seen_urls = {}
        for hoster in hosters:
            if hoster['url'] not in seen_urls:
                seen_urls[hoster['url']] = True
                new_hosters.append(hoster)
        return new_hosters

    def __get_embedded(self, iframe_url, page_url):
        hosters = []
        if 'drive.google.com' in iframe_url:
            for source in self._parse_gdocs(iframe_url):
                quality = scraper_utils.gv_get_quality(source)
                stream_url = source + '|User-Agent=%s&Referer=%s' % (scraper_utils.get_ua(), urllib.quote(page_url))
                hoster = {'multi-part': False, 'host': self._get_direct_hostname(stream_url), 'class': self, 'quality': quality, 'views': None, 'rating': None, 'url': stream_url, 'direct': True}
                hosters.append(hoster)
        elif '/movcav/' in iframe_url:
            iframe_url = iframe_url.replace('&#038;', '&').replace('&amp;', '&')
            headers = {'Referer': page_url}
            html = self._http_get(iframe_url, headers=headers, cache_limit=.5)
            for match in re.finditer('<source\s+src\s*=\s*["\']([^\'"]+)[^>]+type=[\'"]video/mp4[\'"]', html):
                stream_url = match.group(1)
                if self._get_direct_hostname(stream_url) == 'gvideo':
                    quality = scraper_utils.gv_get_quality(stream_url)
                    stream_url += '|User-Agent=%s&Referer=%s' % (scraper_utils.get_ua(), urllib.quote(page_url))
                    hoster = {'multi-part': False, 'host': self._get_direct_hostname(stream_url), 'class': self, 'quality': quality, 'views': None, 'rating': None, 'url': stream_url, 'direct': True}
                    hosters.append(hoster)

            pattern = '"?file"?\s*:\s*"([^;]+)[^"]*"\s*,\s*"?label"?\s*:\s*"([^"]+)"\s*,\s*"?type\"?s*:\s*"([^"]+)'
            for match in re.finditer(pattern, html, re.DOTALL):
                stream_url, label, vid_type = match.groups()
                if vid_type.lower() not in ['mp4', 'avi']: continue
                if self._get_direct_hostname(stream_url) == 'gvideo':
                    quality = scraper_utils.gv_get_quality(stream_url)
                else:
                    quality = self.__get_quality_from_label(label)
    
                stream_url += '|User-Agent=%s&Referer=%s' % (scraper_utils.get_ua(), urllib.quote(page_url))
                hoster = {'multi-part': False, 'host': self._get_direct_hostname(stream_url), 'class': self, 'quality': quality, 'views': None, 'rating': None, 'url': stream_url, 'direct': True}
                hosters.append(hoster)
        else:
            host = urlparse.urlparse(iframe_url).hostname
            hoster = {'multi-part': False, 'host': host, 'class': self, 'quality': QUALITIES.HIGH, 'views': None, 'rating': None, 'url': iframe_url, 'direct': False}
            hosters.append(hoster)
        
        return hosters
    
    def __get_quality_from_label(self, label):
        label = label.upper()
        match = re.search('(\d{3,})', label)
        if match:
            label = match.group(1)

        height = HEIGHT_MAP.get(label.upper(), label)
        return scraper_utils.height_get_quality(height)
        
    def get_url(self, video):
        return self._default_get_url(video)

    def search(self, video_type, title, year, season=''):
        results = []
        search_url = urlparse.urljoin(self.base_url, '/?s=')
        search_url += urllib.quote_plus(title)
        html = self._http_get(search_url, cache_limit=1)
        for item in dom_parser.parse_dom(html, 'div', {'class': 'item'}):
            match = re.search('href="([^"]+)', item)
            if match:
                url = match.group(1)
                match_title_year = dom_parser.parse_dom(item, 'span', {'class': 'tt'})
                if match_title_year:
                    match = re.search('(.*?)\s+\(?(\d{4})\)?', match_title_year[0])
                    if match:
                        match_title, match_year = match.groups()
                    else:
                        match_title = match_title_year[0]
                        match_year = ''
                    
                    year_frag = dom_parser.parse_dom(item, 'span', {'class': 'year'})
                    if year_frag:
                        match_year = year_frag[0]
                        
                    if (not year or not match_year or year == match_year):
                        result = {'url': scraper_utils.pathify_url(url), 'title': scraper_utils.cleanse_title(match_title), 'year': match_year}
                        results.append(result)
        
        return results
