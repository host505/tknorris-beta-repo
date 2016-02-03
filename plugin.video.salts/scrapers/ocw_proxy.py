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
from salts_lib import log_utils
import scraper

try:
    from ocw_scraper import OCW_Scraper as real_scraper
except Exception as e:
    log_utils.log('import failed: %s' % (e), log_utils.LOGDEBUG)

class OCW_Proxy(scraper.Scraper):
    base_url = ''
    
    def __init__(self, timeout=scraper.DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.__scraper = None
        try:
            self.__scraper = real_scraper(timeout)
        except Exception as e:
            log_utils.log('Failure during %s scraper creation: %s' % (self.get_name(), e), log_utils.LOGDEBUG)
   
    @classmethod
    def provides(cls):
        try:
            return real_scraper.provides()
        except:
            return frozenset([])
    
    @classmethod
    def get_name(cls):
        try:
            return real_scraper.get_name()
        except:
            return 'OCW'
    
    @classmethod
    def get_settings(cls):
        try:
            settings = real_scraper.get_settings()
        except:
            settings = super(cls, cls).get_settings()
        return settings

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
