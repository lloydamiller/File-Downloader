#!/usr/bin/env python

# Project Dependencies #
import bs4 as BeautifulSoup
import os
import requests
import ssl
import urllib3
from urllib.parse import urljoin
import shutil
import sys


# FILE TYPE LISTS #
documents_list     = ['doc', 'docx', 'odt', 'pdf', 'rtf', 'txt', 'tex', 'wks', 'wps', 'wpdf', 'pages']
spreadsheets_list  = ['csv', 'tsv', 'ods', 'xlr', 'xls', 'xlsx', 'numbers']
presentations_list = ['ppt', 'pptx', 'odp', 'pps', 'key']
compressed_list    = ['7z', 'arj', 'deb', 'pkg', 'rar', 'rpm', 'gz', 'sitx', 'tar', 'z', 'zip']
images_list        = ['ai', 'bmp', 'gif', 'ico', 'jpg', 'jpeg', 'png', 'psd', 'svg', 'tif', 'tiff']
audio_list         = ['aac', 'aif', 'cda', 'm4a', 'mid', 'midi', 'mp3', 'mpa', 'ogg', 'wav', 'wma', 'wpl']
videos_list        = ['3gp', '3g2', 'avi', 'flv', 'h264', 'm4v', 'mkv', 'mov', 'mp4', 'mpg', 'mpeg', 'rm', 'swf', 'vob', 'wmv']

filetype_dictionary = {
    'documents': {
        'list': documents_list,
        'string': '[D]ocuments: ' + ', '.join(documents_list)
    },
    'spreadsheets': {
        'list': spreadsheets_list,
        'string': '[S]preadsheets: ' + ', '.join(spreadsheets_list)
    },
    'presentations': {
        'list': presentations_list,
        'string': '[P]resentations: ' + ', '.join(presentations_list)
    },
    'compressed': {
        'list': compressed_list,
        'string': '[C]ompressed: ' + ', '.join(compressed_list)
    },
    'images': {
        'list': images_list,
        'string': '[I]mages: ' + ', '.join(images_list)
    },
    'audio': {
        'list': audio_list,
        'string': '[A]udio: ' + ', '.join(audio_list)
    },
    'videos': {
        'list': videos_list,
        'string': '[V]ideos: ' + ', '.join(videos_list)
    },
}


# Ignore SSL warnings
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings()


# create URLLIB3 PoolManager to handle requests
http = urllib3.PoolManager()


# Aquire HTML text from local or online file #
def get_page_text(url):
    # request web page or local HTML file location

    if 'http' not in url:
        with open(url, 'r') as f:
            r = f.read()
        return r

    else:
        try:
            r = requests.get(url, verify=False)
        except Exception as e:
            print('[!] ERROR: %s' % e)
            print('[!] Failed to connect to source url, ending session.')
            sys.exit(1)

    if r.status_code != 200:
        print('[!] ERROR: %s, %s' % (r.status_code, r.reason))
        print('[!] Restart to try again, ending session.')
        sys.exit(1)

    else:
        return r.text


# Parse HTML document and extract all links #
def parse_webpage_for_links(response):
    file_links = []
    links_in_html = BeautifulSoup.BeautifulSoup(response, "html.parser", parse_only=BeautifulSoup.SoupStrainer('a'))
    for link in links_in_html:
        if link.has_attr('href'):
            file_links.append(link['href'])

    return file_links


# takes a URL and downloads tries to download an associated file to the specified folder
def save_file(file_url, download_folder = 'files'):

    # get current directory and create /files/ folder if it does not already exist
    current_directory = os.getcwd()
    download_path = current_directory + '/' + download_folder
    if not os.path.exists(download_path):
        os.makedirs(download_path)

    # iterate through file urls and download each file to specificed downloads folder
    file_name = file_url.split('/')[-1]
    save_file_path = download_folder + '/' + file_name
    try:
        with http.request('GET', file_url, preload_content=False) as r, open(save_file_path, 'wb') as out_file:
            shutil.copyfileobj(r, out_file)
        print('[*] Saved file to %s' % save_file_path)
        return save_file_path

    except Exception as e:
        print('[!] Error: %s' % e)
        return
    pass

if __name__ == '__main__':
    start_prompt = """File Downloader v.1.0
Author: @lloydamiller
Provide a link and this script will download all linked files, or links of a specific file-type. Folder defaults to /files/ but can be changed in script."""
    print(start_prompt)
    page = input('[?] URL or file location to capture:')

    # Get list of filetype extensions to parse
    print('\nSelect document types to acquire, separated by commas')
    for type in filetype_dictionary:
        print('    %s' % filetype_dictionary[type]['string'])
    print('    Type [ALL] to grab all linked files.')
    print('    Type [CUSTOM] to designate custome extensions, separated by commas.')
    filetype_selection = input('[?] Filetype Selection: ').lower()


    # Parse filetype exensions
    valid_extension_list = []

    if filetype_selection == 'custom':
        filetype_selection = input('[?] Custom Filetype Selection: ').lower()
        filetype_selection = filetype_selection.replace(' ', '')
        valid_extension_list = filetype_selection.split(',')

    elif filetype_selection == 'all':
        valid_extension_list.append('*')

    else:
        filetype_selection = filetype_selection.replace(' ', '') # remove whitespace
        filetype_selection = filetype_selection.split(',')
        filetype_reference = {
            'd': 'documents',
            's': 'spreadsheets',
            'p': 'presentations',
            'c': 'compressed',
            'i': 'images',
            'a': 'audio',
            'v': 'videos'
        }
        for ext in filetype_selection:
            valid_extension_list += filetype_dictionary[filetype_reference[ext]]['list']

    if valid_extension_list == []:
        print('[!] No valid extensions inputted, try again.')
        sys.exit(1)

    print('[*] Capturing page text.')
    page_text = get_page_text(page)
    print('[*] Extracting links.')
    link_list = parse_webpage_for_links(page_text)

    download_link_list = [ ]

    if valid_extension_list[0] != '*':
        for link in link_list:
            for ext in valid_extension_list:
                if link.endswith(ext):
                    download_link_list.append(link)
    else:
        download_link_list = link_list

    print('[*] Preparing to download %i files.' % len(download_link_list))
    saved_files = []
    for link in download_link_list:

        # fixes relative URLs
        if not link.startswith('http'):
            link = urljoin(page, link)

        saved_files.append(save_file(link))

    print('[*] Saved %i files.' % len(saved_files))
