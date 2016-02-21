"""
    SALTS Context Menu XBMC Addon
    Copyright (C) 2015 tknorris

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
import sys
import re
import xbmc
import xbmcaddon
import xbmcvfs
import xbmcgui
from lib import log_utils
from lib import kodi

addon = xbmcaddon.Addon('plugin.video.salts')

def __enum(**enums):
    return type('Enum', (), enums)

MODES = __enum(GET_SOURCES='get_sources', SET_URL_MANUAL='set_url_manual', SET_URL_SEARCH='set_url_search', SELECT_SOURCE='select_source', DOWNLOAD_SOURCE='download_source',
               ADD_TO_LIST='add_to_list', SCRAPERS='scrapers', SEARCH='search', AUTOPLAY='autoplay')
VIDEO_TYPES = __enum(TVSHOW='TV Show', MOVIE='Movie', EPISODE='Episode', SEASON='Season')
SECTIONS = __enum(TV='TV', MOVIES='Movies')

def toggle_auto_play():
    if __autoplay_enabled():
        addon.setSetting('auto-play', 'false')
        kodi.notify(msg='SALTS Auto-Play Turned Off')
    else:
        addon.setSetting('auto-play', 'true')
        kodi.notify(msg='SALTS Auto-Play Turned On')

def source_action(mode, li_path):
    try:
        lines = xbmcvfs.File(li_path).read()
        lines = lines.replace('mode=%s' % (MODES.GET_SOURCES), 'mode=%s' % (mode))
        if mode in [MODES.SELECT_SOURCE, MODES.AUTOPLAY]:
            builtin = 'PlayMedia'
        else:
            builtin = 'RunPlugin'
        runstring = '%s(%s)' % (builtin, lines)
        xbmc.executebuiltin(runstring)
    except Exception as e:
        log_utils.log('Failed to read item %s: %s' % (li_path, str(e)), xbmc.LOGERROR)

def set_related_url(mode):
    video_type = __get_media_type()
    if video_type == VIDEO_TYPES.SEASON:
        title = xbmc.getInfoLabel('ListItem.TVShowtitle')
    else:
        title = xbmc.getInfoLabel('ListItem.Title')
    title = re.sub(' \(\d{4}\)$', '', title)
    year = xbmc.getInfoLabel('ListItem.Year')
    queries = {'mode': mode, 'video_type': video_type, 'title': title, 'year': year, 'trakt_id': 0}  # trakt_id set to 0, not used and don't have it
    if video_type == VIDEO_TYPES.SEASON:
        queries['season'] = xbmc.getInfoLabel('ListItem.Season')
    runstring = 'RunPlugin(plugin://plugin.video.salts%s)' % (kodi.get_plugin_url(queries))
    xbmc.executebuiltin(runstring)
    
def add_to_list():
    show_id = {'show_id': xbmc.getInfoLabel('ListItem.IMDBNumber')}
    if __get_media_type() == VIDEO_TYPES.TVSHOW:
        show_id['id_type'] = 'tvdb'
        section = SECTIONS.TV
    elif __get_media_type() == VIDEO_TYPES.MOVIE:
        show_id['id_type'] = 'tmdb'
        section = SECTIONS.MOVIES

    # override id_type is it looks like an imdb #
    if show_id['show_id'].startswith('tt'):
        show_id['id_type'] = 'imdb'
    
    if 'id_type' in show_id:
        queries = {'mode': MODES.ADD_TO_LIST, 'section': section}
        queries.update(show_id)
        runstring = 'RunPlugin(plugin://plugin.video.salts%s)' % (kodi.get_plugin_url(queries))
        xbmc.executebuiltin(runstring)

def scraper_sort_order():
    queries = {'mode': MODES.SCRAPERS}
    runstring = 'RunAddon(plugin.video.salts,%s)' % (kodi.get_plugin_url(queries))
    xbmc.executebuiltin(runstring)
    
def addon_settings():
    xbmc.executebuiltin('Addon.OpenSettings(plugin.video.salts)')

def search(section):
    queries = {'mode': MODES.SEARCH, 'section': section}
    runstring = 'RunPlugin(plugin://plugin.video.salts%s)' % (kodi.get_plugin_url(queries))
    xbmc.executebuiltin(runstring)
    
def __autoplay_enabled():
    auto_play = addon.getSetting('auto-play')
    return auto_play == 'true'
    
def __get_media_type():
    if xbmc.getCondVisibility('Container.Content(tvshows)'):
        return VIDEO_TYPES.TVSHOW
    elif xbmc.getCondVisibility('Container.Content(seasons)'):
        return VIDEO_TYPES.SEASON
    elif xbmc.getCondVisibility('Container.Content(episodes)'):
        return VIDEO_TYPES.EPISODE
    elif xbmc.getCondVisibility('Container.Content(movies)'):
        return VIDEO_TYPES.MOVIE
    else:
        return None
    
def __is_salts_listitem(li_path):
    addon = xbmcaddon.Addon('plugin.video.salts')
    tvshow_folder = xbmc.translatePath(addon.getSetting('tvshow-folder'))
    movie_folder = xbmc.translatePath(addon.getSetting('movie-folder'))
    real_path = xbmc.translatePath(li_path)
    if not real_path.startswith(movie_folder) and not real_path.startswith(tvshow_folder):
        log_utils.log('Path Mismatch: |%s|%s|%s|' % (real_path, movie_folder, tvshow_folder))
        return False
    
    try:
        lines = xbmcvfs.File(li_path).read()
        if lines and not lines.startswith('plugin://plugin.video.salts'):
            log_utils.log('STRM Mistmatch: %s' % (lines))
            return False
    except Exception as e:
        log_utils.log('Failed to read item %s: %s' % (li_path, str(e)), xbmc.LOGERROR)
    
    return True

def __get_tools(path):
    if __autoplay_enabled():
        action = MODES.SELECT_SOURCE
        label = 'Select Source'
    else:
        action = MODES.AUTOPLAY
        label = 'Auto-Play'
        
    tools = [
        ((VIDEO_TYPES.MOVIE, VIDEO_TYPES.TVSHOW, VIDEO_TYPES.SEASON, VIDEO_TYPES.EPISODE), 'Toggle Auto-Play', toggle_auto_play, []),
        ((VIDEO_TYPES.MOVIE, VIDEO_TYPES.EPISODE), label, source_action, [action, path]),
        ((VIDEO_TYPES.MOVIE, VIDEO_TYPES.EPISODE), 'Download Source', source_action, [MODES.DOWNLOAD_SOURCE, path]),
        ((VIDEO_TYPES.MOVIE, VIDEO_TYPES.TVSHOW), 'Add to List', add_to_list, []),
        ((VIDEO_TYPES.MOVIE), 'Movie Search', search, [SECTIONS.MOVIES]),
        ((VIDEO_TYPES.TVSHOW), 'TV Show Search', search, [SECTIONS.TV]),
        ((VIDEO_TYPES.MOVIE, VIDEO_TYPES.TVSHOW, VIDEO_TYPES.SEASON, VIDEO_TYPES.EPISODE), 'Scraper Sort Order', scraper_sort_order, []),
        ((VIDEO_TYPES.MOVIE, VIDEO_TYPES.TVSHOW, VIDEO_TYPES.SEASON, VIDEO_TYPES.EPISODE), 'Addon Settings', addon_settings, []),
        ((VIDEO_TYPES.MOVIE, VIDEO_TYPES.TVSHOW, VIDEO_TYPES.SEASON), 'Set Related Url (Search)', set_related_url, [MODES.SET_URL_SEARCH]),
        ((VIDEO_TYPES.MOVIE, VIDEO_TYPES.TVSHOW, VIDEO_TYPES.SEASON), 'Set Related Url (Manual)', set_related_url, [MODES.SET_URL_MANUAL])
    ]
    
    media_type = __get_media_type()
    new_tools = [(tool[1], tool[2], tool[3]) for tool in tools if media_type in tool[0]]
    return new_tools

def main(argv=None):
    if sys.argv: argv = sys.argv
    log_utils.log('Version: |%s|' % (kodi.get_version()))
    log_utils.log('Args: |%s|' % (argv))
    path = xbmc.getInfoLabel('ListItem.FileNameAndPath')
    if not path:
        path = xbmc.getInfoLabel('ListItem.Path')
        
    if __is_salts_listitem(path):
        dialog = xbmcgui.Dialog()
        tools = __get_tools(path)
        ret = dialog.select('SALTS Tools', [i[0] for i in tools])
        if ret > -1:
            tools[ret][1](*tools[ret][2])
    else:
        kodi.notify(msg='Not a SALTS Library Item')

if __name__ == '__main__':
    sys.exit(main())
