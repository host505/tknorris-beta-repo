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
import sys
import os.path
from local_lib.url_dispatcher import URL_Dispatcher
from local_lib.premiumize_api import Premiumize_API,PremiumizeError
from local_lib import log_utils
from local_lib import kodi
from local_lib import utils
from local_lib.kodi import i18n
import xbmcgui
import xbmcplugin
import xbmc
import xbmcvfs

def __enum(**enums):
    return type('Enum', (), enums)

VIDEO_EXTS = ['MP4', 'MKV', 'AVI']
STATUS_COLORS = {'FINISHED': 'green', 'WAITING': 'blue', 'SEEDING': 'green', 'TIMEOUT': 'red', 'ERROR': 'red'}
DEFAULT_COLOR = 'white'
MODES = __enum(
    MAIN='main', TRANSFER_LIST='transfer_list', FILE_LIST='file_list', BROWSE_TORRENT='browse_torrent',
    PLAY_VIDEO='play_video', CLEAR_FINISHED='clear_finished', DELETE_TRANSFER='delete_transfer',
    DELETE_ITEM='delete_item', CREATE_FOLDER='create_folder', DELETE_FOLDER='delete_folder',
    RENAME_FOLDER='rename_folder', ADD_TORRENT='add_torrent'
)

customer_id = kodi.get_setting('customer_id')
pin = kodi.get_setting('pin')
use_https = kodi.get_setting('use_https') == 'true'
premiumize_api = Premiumize_API(customer_id, pin, use_https)
url_dispatcher = URL_Dispatcher()

@url_dispatcher.register(MODES.MAIN)
def main_menu():
    kodi.create_item({'mode': MODES.TRANSFER_LIST}, i18n('transfer_list'))
    queries = {'mode': MODES.CREATE_FOLDER, 'parent_id': None}
    menu_items = [(i18n('create_folder'), 'RunPlugin(%s)' % (kodi.get_plugin_url(queries)))]
    kodi.create_item({'mode': MODES.FILE_LIST}, i18n('file_list'), menu_items=menu_items)
    kodi.create_item({'mode': MODES.ADD_TORRENT}, i18n('add_torrent'))
    kodi.end_of_directory()

@url_dispatcher.register(MODES.ADD_TORRENT)
def add_torrent():
    dialog = xbmcgui.Dialog()
    path = dialog.browse(1, i18n('select_torrent'), 'files', '.torrent|.magnet|.link')
    if path:
        f = xbmcvfs.File(path, 'rb')
        torrent = f.read()
        f.close()
        if torrent.endswith('\n'):
            torrent = torrent[:-1]
            
        if torrent:
            try:
                premiumize_api.add_torrent(torrent)
                msg = '%s: %s' % (i18n('torrent_added'), os.path.basename(path))
            except PremiumizeError as e:
                msg = str(e)
            kodi.notify(msg=msg, duration=5000)

@url_dispatcher.register(MODES.TRANSFER_LIST)
def show_transfers():
    results = premiumize_api.get_transfers()
    kodi.create_item({'mode': MODES.CLEAR_FINISHED}, i18n('clear_all_finished'), is_folder=False, is_playable=False)
    if 'transfers' in results:
        for item in results['transfers']:
            status = item['status'].upper()
            color = STATUS_COLORS.get(status, DEFAULT_COLOR)
            label = '[[COLOR %s]%s[/COLOR]] %s' % (color, status, item['name'])
            if 'size' in item: label += ' (%s)' % (utils.format_size(int(item['size']), 'B'))
            if item['status'] != 'finished':
                try: progress = item['progress'] * 100
                except: progress = 0
                if 'progress' in item: label += ' (%d%% %s)' % (progress, i18n('complete'))
                if 'eta' in item and item['eta']: label += ' - ETA: %s' % (utils.format_time(item['eta']))
                next_mode = MODES.TRANSFER_LIST
                del_label = i18n('abort_transfer')
            else:
                next_mode = MODES.BROWSE_TORRENT
                del_label = i18n('del_transfer')
            queries = {'mode': MODES.DELETE_TRANSFER, 'torrent_id': item['id']}
            menu_items = [(del_label, 'RunPlugin(%s)' % (kodi.get_plugin_url(queries)))]
            kodi.create_item({'mode': next_mode, 'hash_id': item['hash'], 'torrent_id': item['id']}, label, menu_items=menu_items)
            
    kodi.end_of_directory()

@url_dispatcher.register(MODES.DELETE_ITEM, ['torrent_id'])
def delete_item(torrent_id):
    premiumize_api.delete_item(torrent_id)
    kodi.refresh_container()

@url_dispatcher.register(MODES.DELETE_TRANSFER, ['torrent_id'])
def delete_transfer(torrent_id):
    premiumize_api.delete_transfer(torrent_id)
    kodi.refresh_container()

@url_dispatcher.register(MODES.DELETE_FOLDER, ['folder_id'])
def delete_folder(folder_id):
    premiumize_api.delete_folder(folder_id)
    kodi.refresh_container()

@url_dispatcher.register(MODES.CREATE_FOLDER, ['mode'], ['folder_id'])
@url_dispatcher.register(MODES.RENAME_FOLDER, ['mode', 'folder_id', 'folder_name'])
def folder_action(mode, folder_id=None, folder_name=None):
    keyboard = xbmc.Keyboard()
    keyboard.setHeading(i18n('enter_folder_name'))
    if mode == MODES.RENAME_FOLDER and folder_name is not None:
        keyboard.setDefault(folder_name)
    keyboard.doModal()
    if keyboard.isConfirmed():
        folder_name = keyboard.getText()
        if folder_name:
            if mode == MODES.CREATE_FOLDER:
                premiumize_api.create_folder(folder_name, folder_id)
            elif mode == MODES.RENAME_FOLDER:
                premiumize_api.rename_folder(folder_name, folder_id)
                kodi.refresh_container()

@url_dispatcher.register(MODES.CLEAR_FINISHED)
def clear_finished():
    premiumize_api.clear_finished()
    kodi.refresh_container()

@url_dispatcher.register(MODES.FILE_LIST, [], ['folder_id'])
def show_files(folder_id=None):
    results = premiumize_api.get_files(folder_id)
    if 'content' in results:
        for result in results['content']:
            if result['type'] == 'folder':
                menu_items = []
                queries = {'mode': MODES.CREATE_FOLDER, 'folder_id': result['id']}
                menu_items.append((i18n('create_folder'), 'RunPlugin(%s)' % (kodi.get_plugin_url(queries))))
                queries = {'mode': MODES.DELETE_FOLDER, 'folder_id': result['id']}
                menu_items.append((i18n('delete_folder'), 'RunPlugin(%s)' % (kodi.get_plugin_url(queries))))
                queries = {'mode': MODES.RENAME_FOLDER, 'folder_id': result['id'], 'folder_name': result['name']}
                menu_items.append((i18n('rename_folder'), 'RunPlugin(%s)' % (kodi.get_plugin_url(queries))))
                
                kodi.create_item({'mode': MODES.FILE_LIST, 'folder_id': result['id']}, result['name'], menu_items=menu_items)
            elif result['type'] == 'torrent':
                label = result['name']
                if 'size' in result:
                    label += ' (%s)' % (utils.format_size(int(result['size']), 'B'))
                queries = {'mode': MODES.DELETE_ITEM, 'torrent_id': result['id']}
                menu_items = [(i18n('delete_item'), 'RunPlugin(%s)' % (kodi.get_plugin_url(queries)))]
                
                kodi.create_item({'mode': MODES.BROWSE_TORRENT, 'hash_id': result['hash'], 'torrent_id': result['id']}, label, menu_items=menu_items)
    kodi.end_of_directory()

@url_dispatcher.register(MODES.BROWSE_TORRENT, ['hash_id'])
def browse_torrent(hash_id):
    results = premiumize_api.browse_torrent(hash_id)
    if 'content' in results:
        videos = get_videos(results['content'])
        for video in sorted(videos, key=lambda x: x['label']):
            kodi.create_item({'mode': MODES.PLAY_VIDEO, 'name': video['name'], 'url': video['url']}, video['label'], is_folder=False, is_playable=True)
            
    kodi.end_of_directory()

@url_dispatcher.register(MODES.PLAY_VIDEO, ['url'], ['name'])
def play_video(url, name=None):
    listitem = xbmcgui.ListItem(label=name, path=url)
    listitem.setPath(url)
    if name is not None:
        info = utils.make_info(name)
        listitem.setInfo('video', info)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem)

def get_videos(content):
    videos = []
    for key in content:
        item = content[key]
        if item['type'] == 'dir':
            videos += get_videos(item['children'])
        else:
            if 'ext' in item and item['ext'].upper() in VIDEO_EXTS:
                label = item['name']
                if 'size' in item: label += ' (%s)' % (utils.format_size(int(item['size']), 'B'))
                video = {'label': label, 'name': item['name'], 'url': item['url']}
                videos.append(video)
                if 'transcoded' in item:
                    transcode = item['transcoded']
                    label = '%s (%s) (%s)' % (item['name'], i18n('transcode'), utils.format_size(int(transcode['size']), 'B'))
                    video = {'label': label, 'name': item['name'], 'url': transcode['url']}
                    videos.append(video)
    return videos

def main(argv=None):
    if sys.argv: argv = sys.argv
    queries = kodi.parse_query(sys.argv[2])
    log_utils.log('Version: |%s| Queries: |%s|' % (kodi.get_version(), queries))
    log_utils.log('Args: |%s|' % (argv))

    # don't process params that don't match our url exactly. (e.g. plugin://plugin.video.1channel/extrafanart)
    plugin_url = 'plugin://%s/' % (kodi.get_id())
    if argv[0] != plugin_url:
        return

    mode = queries.get('mode', None)
    url_dispatcher.dispatch(mode, queries)

if __name__ == '__main__':
    sys.exit(main())
