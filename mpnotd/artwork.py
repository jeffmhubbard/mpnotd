# -*- coding: utf-8 -*-

"""Artwork methods"""

import json
from glob import glob
from os import path, remove
from shutil import copyfile
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen, urlretrieve

from bs4 import BeautifulSoup
from PIL import Image

from .utils import get_valid_str


def cache_artwork(cachedir, musicdir, log, url, artist, album):
    """Get album art thumbnail

    Attempt to find album art and thumbnail it
    First look for existing thumbnail
    Then find_image() searches filesystem
    Or else fetch_image() searches web

    Args:
        cachedir (str): Path to cached artwork
        musicdir (str): Path to music directory
        log (obj): The logger
        url (str): MPD database path or http url
        artist (str): Song artist
        album (str): Song ablum

    Returns:
       Return path to thumbnail or None

    """

    # Temp file
    tmpfile = path.join(cachedir, "artwork.tmp")
    if path.exists(tmpfile):
        remove(tmpfile)
        log.debug("Purge tmp: {}".format(tmpfile))

    # Get destination file path
    filename = "cover-{}-{}.png".format(artist, album)
    filename = get_valid_str(filename).lower()
    filepath = path.join(cachedir, filename)
    log.debug("Cache Dest: {}".format(filepath))

    # Check for cached image first
    if path.exists(filepath):
        log.debug("Found image: {}".format(filepath))

    # Try to find image in local path (even for streams... who knows)
    elif find_image(musicdir, tmpfile, log, url, artist, album):
        log.debug("Searching filesystem")
        _mkthumb(tmpfile, filepath)

    # If not, search google
    elif fetch_image(tmpfile, log, artist, album):
        log.debug("Searching web")
        _mkthumb(tmpfile, filepath)

    return filepath


def _mkthumb(in_file, out_file):

    """ Make thumbnail
    """

    image = Image.open(in_file)
    image.thumbnail((96, 96))
    image.save(out_file)


def find_image(musicdir, tmpfile, log, url, artist=None, album=None):
    """Search filesystem for artwork

    If `url` starts with HTTP, we assume we're streaming and
    make a guess on where to find artwork (music_dir/artist/album/)
    If `url` is a local path, just look in the same directory

    Args:
        musicdir (str): Path to music directory
        url (str): file path or web address
        artist (str): artist name
        album (str): album name

    Return:
        Return True if local image cached
    """

    # If streaming... Guess!
    if url.startswith("http"):
        base_dir = path.join(musicdir, artist, album)

    # If local, look there
    else:
        base_dir = path.dirname(path.join(musicdir, url))

    log.debug("Search path: {}".format(base_dir))

    if path.exists(base_dir):
        # Search for matching extensions
        for ext in ["png", "jpg", "jpeg"]:
            img_match = glob("{}/*.{}".format(base_dir, ext))

            # Return first match
            if img_match:
                copyfile(img_match[0], tmpfile)
                log.debug("Local image found: {}".format(img_match[0]))

                return True

    return False


def fetch_image(tmpfile, log, artist, album):
    """Search web for artwork

    This is slow but easy and free

    Args:
        artist (str): Song artist
        album (str): Song album

    Returns:
        True if image was downloaded, False otherwise

    """

    # Build search request
    search_string = "album art {} {}".format(album, artist)
    search_url = ("https://www.google.com/search?q=" +
                  quote(search_string.encode("utf-8")) +
                  "&source=lnms&tbm=isch")
    search_agent = {
        "User-Agent":
        """Mozilla/5.0 (X11; Linux x86_64)
        AppleWebKit/534.30 (KHTML, like Gecko) Ubuntu/11.04
        Chromium/12.0.742.112 Chrome/12.0.742.112 Safari/534.30"""
    }

    # Return search results
    try:
        results = BeautifulSoup(
            urlopen(
                Request(search_url, headers=search_agent)),
            "html.parser")

    except HTTPError as http_err:
        if http_err.code == 404:
            log.debug(http_err.code)
        elif http_err.code == 403:
            log.debug(http_err.code)
    except URLError as url_err:
        log.debug(url_err.reason)

    # Find image on page
    img_div = results.find("div", {"class": "rg_meta"})
    img_url = json.loads(img_div.text)["ou"]

    if urlretrieve(img_url, tmpfile):
        log.debug("Search image found: {}".format(tmpfile))

        return True

    return False
