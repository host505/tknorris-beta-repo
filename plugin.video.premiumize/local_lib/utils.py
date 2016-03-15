"""
    Premiumize Kodi Addon
    Copyright (C) 2016 tknorris

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

def format_size(num, suffix='B'):
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Y', suffix)

def make_info(name):
    info = {}
    sxe_patterns = [
        '(.*?)[._ -]s([0-9]+)[._ -]*e([0-9]+)',
        '(.*?)[._ -]([0-9]+)x([0-9]+)',
        # '(.*?)[._ -]([0-9]+)([0-9][0-9])', removed due to looking like Movie.Title.YYYY
        '(.*?)[._ -]?season[._ -]*([0-9]+)[._ -]*-?[._ -]*episode[._ -]*([0-9]+)',
        '(.*?)[._ -]\[s([0-9]+)\][._ -]*\[e([0-9]+)\]',
        '(.*?)[._ -]s([0-9]+)[._ -]*ep([0-9]+)']
    
    show_title = ''
    season = ''
    episode = ''
    airdate = ''
    for pattern in sxe_patterns:
        match = re.search(pattern, name, re.I)
        if match:
            show_title, season, episode = match.groups()
            break
    else:
        airdate_pattern = '(.*?)[. _](\d{4})[. _](\d{2})[. _](\d{2})[. _]'
        match = re.search(airdate_pattern, name)
        if match:
            show_title, year, month, day = match.groups()
            airdate = '%s-%s-%s' % (year, month, day)
    
    if show_title:
        show_title = re.sub('[._ -]', ' ', show_title)
        show_title = re.sub('\s\s+', ' ', show_title)
        info['title'] = name
        info['tvshowtitle'] = show_title
        info['season'] = str(int(season))
        info['episode'] = str(int(episode))
        if airdate: info['aired'] = info['premiered'] = airdate
    else:
        pattern = '(.*?)[._ -](\d{4})[._ -](.*?)'
        match = re.search(pattern, name)
        if match:
            title, year, _extra = match.groups()
            title = re.sub('[._ -]', ' ', title)
            title = re.sub('\s\s+', ' ', title)
            info['title'] = title
            info['year'] = year
        
    return info

def format_time(seconds):
    minutes, seconds = divmod(seconds, 60)
    if minutes > 60:
        hours, minutes = divmod(minutes, 60)
        return "%02dh:%02dm:%02ds" % (hours, minutes, seconds)
    else:
        return "%02dm:%02ds" % (minutes, seconds)

