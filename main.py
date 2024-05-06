#
# The BunnyCDN DRM Video Downloader is a powerful tool designed
# to facilitate the downloading of DRM-protected videos hosted on BunnyCDN.
# With this tool, users can easily download their favorite videos from BunnyCDN's
# content delivery network, even if they are protected with
# Digital Rights Management (DRM) technology.
#
# Disclaimer
# This program is a modification of https://github.com/MaZED-UP/bunny-cdn-drm-video-dl.
#
#
# Josh Holly (WafleHacker AK TrainReq Cunsto Fork)
# This custom fork allows for downloading multipl videos
# This custom fork bypases DRM protection that wasn't bypassed by the original

import re
import sys
import requests
import yt_dlp
from hashlib import md5
from html import unescape
from random import random
from urllib.parse import urlparse, urlunparse, parse_qs

class colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'

# Define path to main directory
path = './videos/'

# Generating Sessions using custom user-agent
user_agent = {
    'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
}

session = requests.session()
session.headers.update(user_agent)

def process_url(url):
    # Remove parameters from URL
    url_components = urlparse(url)
    url = urlunparse((url_components.scheme, url_components.netloc, url_components.path, '', '', ''))

    # Copy the URL to both referer and embed_url
    referer = url
    embed_url = url

    # Extract guid from URL using urlparse
    guid = urlparse(embed_url).path.split('/')[-1]

    # Define headers for HTTP requests
    headers = {
        'embed': {
            'authority': 'iframe.mediadelivery.net',
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'referer': referer,
            'sec-fetch-dest': 'iframe',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'cross-site',
            'upgrade-insecure-requests': '1',
        },
        'ping|activate': {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'no-cache',
            'origin': 'https://iframe.mediadelivery.net',
            'pragma': 'no-cache',
            'referer': 'https://iframe.mediadelivery.net/',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
        },
        'playlist': {
            'authority': 'iframe.mediadelivery.net',
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'referer': embed_url,
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
        }
    }

    # Retrieve embed page content
    embed_response = session.get(embed_url, headers=headers['embed'])
    embed_page = embed_response.text

    # Extract server ID using regular expression
    try:
        server_id = re.search(r'https://video-(.*?)\.mediadelivery\.net', embed_page).group(1)
    except AttributeError:
        sys.exit(1)

    # Update headers with server ID
    headers['ping|activate'].update({'authority': f'video-{server_id}.mediadelivery.net'})
    search = re.search(r'contextId=(.*?)&secret=(.*?)["&]', embed_page)

    # Check if search result is not None before accessing groups
    if search is not None:
        # Define context_id and secret
        context_id, secret = search.group(1), search.group(2)
    else:
        # If search result is None, print a message and return
        print(colors.RED + f"Could not extract contextId and secret from URL: {url}" + colors.RESET)
        print(print(colors.MAGENTA + f"Re-trying via TrainReq's Bypass Method for {url}" + colors.RESET))
        file_name_unescaped = re.search(r'og:title" content="(.*?)"', embed_page).group(1)
        file_name_escaped = unescape(file_name_unescaped)
        file_name = re.sub(r'\.[^.]*$.*', '.mp4', file_name_escaped)
        original_url_match = re.search(r"var originalUrl = '(.*?)';", embed_page)
        trainreq_bypass(original_url_match.group(1),file_name)


        return

    # Extract file name from embed page
    file_name_unescaped = re.search(r'og:title" content="(.*?)"', embed_page).group(1)
    file_name_escaped = unescape(file_name_unescaped)
    file_name = re.sub(r'\.[^.]*$.*', '.mp4', file_name_escaped)

    def prepare_dl():
        # Prepare the download process
        def ping(time: int, paused: str, res: str):
            # Send ping request
            md5_hash = md5(f'{secret}_{context_id}_{time}_{paused}_{res}'.encode('utf8')).hexdigest()
            params = {
                'hash': md5_hash,
                'time': time,
                'paused': paused,
                'chosen_res': res
            }
            session.get(f'https://video-{server_id}.mediadelivery.net/.drm/{context_id}/ping', params=params, headers=headers['ping|activate'])

        def activate():
            # Getting sessions from Activate
            session.get(f'https://video-{server_id}.mediadelivery.net/.drm/{context_id}/activate', headers=headers['ping|activate'])

        def main_playlist():
            # Retrieve main playlist
            params = {'contextId': context_id, 'secret': secret}
            response = session.get(f'https://iframe.mediadelivery.net/{guid}/playlist.drm', params=params, headers=headers['playlist'])
            resolutions = re.findall(r'RESOLUTION=(.*)', response.text)[::-1]
            if not resolutions:
                sys.exit(2)
            else:
                return resolutions[0]

        def video_playlist():
            # Retrieve video playlist
            params = {'contextId': context_id}
            session.get(f'https://iframe.mediadelivery.net/{guid}/{resolution}/video.drm', params=params, headers=headers['playlist'])

        ping(time=0, paused='true', res='0')
        activate()
        resolution = main_playlist()
        video_playlist()
        for i in range(0, 29, 4):
            ping(time=i + round(random(), 6), paused='false', res=resolution.split('x')[-1])
        session.close()
        return resolution

    def download():
        # Download the video
        resolution = prepare_dl()
        url = [f'https://iframe.mediadelivery.net/{guid}/{resolution}/video.drm?contextId={context_id}']
        ydl_opts = {
            'http_headers': {
                'Referer': embed_url,
                'User-Agent': user_agent['user-agent']
            },
            'concurrent_fragment_downloads': 10,
            'nocheckcertificate': True,
            'outtmpl': file_name,
            'restrictfilenames': True,
            'windowsfilenames': True,
            'nopart': True,
            'paths': {
                'home': path,
                'temp': f'.{file_name}/',
            },
            'retries': float('inf'),
            'extractor_retries': float('inf'),
            'fragment_retries': float('inf'),
            'skip_unavailable_fragments': False,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download(url)

    download()

def trainreq_bypass(original_url, file_name):
    referer = url
    print(f"Downloading {file_name} from {original_url } u")
    response = session.get(original_url, headers={'User-Agent': user_agent['user-agent'], 'Referer': referer})
    if response.status_code == 200:
        with open(path+file_name, 'wb') as file:
            file.write(response.content)
            print(colors.GREEN + f"{file_name} downloaded successfully via TrainReq bypass" + colors.RESET)
    else:
        print(f"Failed to download {file_name}")


if __name__ == '__main__':
    # Read URLs from files.txt and process them one by one
    with open('files.txt', 'r') as file:
        urls = file.read().splitlines()
        for url in urls:
            process_url(url)