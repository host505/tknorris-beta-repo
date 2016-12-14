#!/usr/bin/python
"""
    download_po.py
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
import re
import json
import urllib2
import urlparse
import base64
import sys
import os

BASE_URL = 'https://www.transifex.com/api/2/'

class Transifex(object):
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.auth_info = base64.urlsafe_b64encode('%s:%s' % (username, password))
        
    def get_resource(self, project, resource):
        return self._call_transifex('project/%s/resource/%s/?details' % (project, resource))
    
    def get_translation(self, project, resource, lang_code):
        return self._call_transifex('project/%s/resource/%s/translation/%s/' % (project, resource, lang_code))
    
    def _call_transifex(self, path):
        url = urlparse.urljoin(BASE_URL, path)
        req = urllib2.Request(url)
        req.add_header('Authorization', 'Basic %s' % (self.auth_info))
        response = urllib2.urlopen(req)
        return json.load(response)
    
def filter_po(content):
    lines = content.split('\n')
    trans_exists = False
    file_buf = ''
    in_trans = False
    msgid = False
    msgstr = False
    all_trans = []
    for line in lines:
        if line.startswith('msgctxt'):
            in_trans = True
            msgid = False
            msgstr = False
            trans = {'msgctxt': line}

        if in_trans:
            if line.startswith('msgid'):
                trans['msgid'] = [line]
                msgid = True
                msgstr = False
            elif line.startswith('msgstr'):
                trans['msgstr'] = [line]
                msgid = False
                msgstr = True
            else:
                if not line:
                    msgid = msgstr = False
                    all_trans.append(trans)
                elif msgid:
                    trans['msgid'].append(line)
                elif msgstr:
                    trans['msgstr'].append(line)
        
        if not in_trans:
            # strip email addresses jic
            line = re.sub('\s*<[^>]+@[^>]+>', '', line)
            file_buf += line + '\n'
        
    trans_count = 0
    for trans in all_trans:
        if len(trans['msgstr']) > 1 or trans['msgstr'][0] != 'msgstr ""':
            trans_exists = True
            file_buf += trans['msgctxt'] + '\n'
            file_buf += '\n'.join(trans['msgid']) + '\n'
            file_buf += '\n'.join(trans['msgstr']) + '\n'
            file_buf += '\n'
            trans_count += 1

    if trans_exists:
        print '%s Strings Exist...' % (trans_count),
        return file_buf
    else:
        return ''

def lang_name(name):
    return name.replace('United States', 'US')
    
def main(argv=None):
    if sys.argv: argv = sys.argv
    
    if len(argv) < 5:
        print 'download_po <username> <pasword> <project> <resource>'
        return

    user = argv[1]
    password = argv[2]
    proj_slug = argv[3]
    res_slug = argv[4]

    transifex = Transifex(user, password)
    resource = transifex.get_resource(proj_slug, res_slug)
    for lang in resource['available_languages']:
        if lang['code'] == resource['source_language_code']:
            continue
        
        print 'Extracting Language: %s...' % (lang['name']),
        translation = transifex.get_translation(proj_slug, res_slug, lang['code'])
        content = filter_po(translation['content'])
        if content:
            print 'Exists'
            name = lang_name(lang['name'])
            if not os.path.exists(name):
                os.mkdir(name)
            file_name = os.path.join(name, 'strings.po')
            with open(file_name, 'w') as f:
                f.write(content.encode('utf-8'))
        else:
            print
    
if __name__ == '__main__':
    sys.exit(main())
