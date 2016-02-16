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
import urllib
import urlparse

from salts_lib import kodi
from salts_lib import log_utils
from salts_lib import scraper_utils
from salts_lib import dom_parser
from salts_lib.constants import FORCE_NO_MATCH
from salts_lib.constants import VIDEO_TYPES
from salts_lib.constants import QUALITIES
from salts_lib.kodi import i18n
import scraper


BASE_URL = 'http://www.theextopia.com'
IMAGES = {'1080p': QUALITIES.HD1080, '720p': QUALITIES.HD720}

class TheExtopia_Scraper(scraper.Scraper):
    base_url = BASE_URL

    def __init__(self, timeout=scraper.DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.base_url = kodi.get_setting('%s-base_url' % (self.get_name()))

    @classmethod
    def provides(cls):
        return frozenset([VIDEO_TYPES.EPISODE])

    @classmethod
    def get_name(cls):
        return 'TheExtopia'

    def resolve_link(self, link):
        return link

    def format_source_label(self, item):
        label = '[%s] %s' % (item['quality'], item['host'])
        if 'views' in item and item['views']:
            label += ' (%s Views)' % (item['views'])
        return label

    def get_sources(self, video):
        source_url = self.get_url(video)
        hosters = []
        if source_url and source_url != FORCE_NO_MATCH:
            url = urlparse.urljoin(self.base_url, source_url)
            html = self._http_get(url, cache_limit=.5)

            views = dom_parser.parse_dom(html, 'span', {'class': 'contador'})
            if views:
                views = re.sub('[^\d]', '', views[0])
            else:
                views = None

            return self.__get_episode_links(video, views, html)
        return hosters

    def __get_episode_links(self, video, views, html):
        hosters = []
        fragment = dom_parser.parse_dom(html, 'div', {'class': 'entry'})
        if fragment:
            headers = dom_parser.parse_dom(fragment[0], 'img', {'class': '[^"]*aligncenter[^"]*'}, ret='src')
            link_frags = dom_parser.parse_dom(fragment[0], 'code')
            
            for header, fragment in zip(headers, link_frags):
                base_quality = self.__get_quality(header)
                for url in dom_parser.parse_dom(fragment, 'a', ret='href'):
                    hoster = {'multi-part': False, 'class': self, 'views': views, 'url': url, 'rating': None, 'quality': None, 'direct': False}
                    hoster['host'] = urlparse.urlsplit(url).hostname
                    hoster['quality'] = scraper_utils.get_quality(video, hoster['host'], base_quality)
                    hosters.append(hoster)
        return hosters
    
    def __get_quality(self, header):
        quality = QUALITIES.HIGH
        for key in IMAGES:
            if key in header:
                quality = IMAGES[key]
                break
        return quality
        
    def get_url(self, video):
        return self._blog_get_url(video)

    @classmethod
    def get_settings(cls):
        settings = super(cls, cls).get_settings()
        settings = scraper_utils.disable_sub_check(settings)
        name = cls.get_name()
        settings.append('         <setting id="%s-select" type="enum" label="     %s" lvalues="30636|30637" default="0" visible="eq(-4,true)"/>' % (name, i18n('auto_select')))
        return settings

    def search(self, video_type, title, year, season=''):
        search_url = urlparse.urljoin(self.base_url, '/?s=')
        search_url += urllib.quote_plus(title)
        html = self._http_get(search_url, cache_limit=1)
        pattern = '<h\d+>.*?<a\s+href="(?P<url>[^"]+)"\s+rel="bookmark"\s+title="(?:Permanent Link to )?(?P<post_title>[^"]+)'
        date_format = ''
        return self._blog_proc_results(html, pattern, date_format, video_type, title, year)
