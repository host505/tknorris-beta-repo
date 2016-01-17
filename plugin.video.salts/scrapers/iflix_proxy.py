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
from salts_lib.trans_utils import i18n
from salts_lib import log_utils
from salts_lib.constants import VIDEO_TYPES
try:
    from iflix_scraper import Iflix_Scraper as real_scraper
except Exception as e:
    log_utils.log('import failed: %s' % (e), log_utils.LOGDEBUG)

class IFlix_Proxy(scraper.Scraper):
    base_url = ''
    
    def __init__(self, timeout=scraper.DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.exists = False
        self._update_scraper_py('iflix_scraper.py')
        self.__scraper = None
        if self.exists:
            try:
                from iflix_scraper import Iflix_Scraper as real_scraper
                self.__scraper = real_scraper(timeout)
            except Exception as e:
                log_utils.log('Failure during %s scraper creation: %s' % (self.get_name(), e), log_utils.LOGWARNING)
   
    @classmethod
    def provides(cls):
        try:
            return real_scraper.provides()
        except:
            return frozenset([VIDEO_TYPES.TVSHOW, VIDEO_TYPES.EPISODE, VIDEO_TYPES.MOVIE])
    
    @classmethod
    def get_name(cls):
        return 'IFlix'
    
    def resolve_link(self, link):
        if self.__scraper is not None:
            return self.__scraper.resolve_link(link)
    
    def format_source_label(self, item):
        if self.__scraper is not None:
            return self.__scraper.format_source_label(item)
    
    def get_sources(self, video):
        if self.__scraper is not None:
            return self.__scraper.get_sources(video)
            
    def get_url(self, video):
        if self.__scraper is not None:
            return self.__scraper.get_url(video)
    
    def search(self, video_type, title, year):
        if self.__scraper is not None:
            return self.__scraper.search(video_type, title, year)
        else:
            return []
    
    def _get_episode_url(self, show_url, video):
        if self.__scraper is not None:
            return self.__scraper._get_episode_url(show_url, video)

    @classmethod
    def get_settings(cls):
        name = cls.get_name()
        try:
            settings = real_scraper.get_settings()
            offset = 5
        except:
            settings = super(cls, cls).get_settings()
            offset = 4
        settings.append('         <setting id="%s-scraper_url" type="text" label="    %s" default="" visible="eq(-%d,true)"/>' % (name, i18n('scraper_location'), offset))
        settings.append('         <setting id="%s-scraper_password" type="text" label="    %s" option="hidden" default="" visible="eq(-%d,true)"/>' % (name, i18n('scraper_key'), offset + 1))
        return settings
