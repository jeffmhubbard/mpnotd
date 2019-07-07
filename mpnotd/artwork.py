# -*- coding: utf-8 -*-

"""Artwork methods"""

import json
from glob import glob
from os import path, remove
from re import sub
from shutil import copyfile
from urllib.parse import quote
from urllib.request import Request, urlopen, urlretrieve

from bs4 import BeautifulSoup
from PIL import Image


def get_albumart(parent, url, artist, album):
    """Get album art thumbnail

    Attempt to find album art and thumbnail it
    First look for existing thumbnail
    Then find_image() searches filesystem
    Or else fetch_image() searches web

    Args:
        url (str): MPD database path or http url
        artist (str): Song artist
        album (str): Song ablum

    Returns:
       Return path to thumbnail or None

    """

    # Temp file
    tmp_file = path.join(parent.paths["cache"], "artwork.tmp")
    if path.exists(tmp_file):
        remove(tmp_file)
        parent.log.debug("Purge tmp: {}".format(tmp_file))

    # Get destination file path
    filename = "cover-{}-{}.png".format(artist, album)
    filename = sub(r" ", "_", filename).lower()
    filepath = path.join(parent.paths["cache"], filename)
    parent.log.debug("Cache Dest: {}".format(filepath))

    # Save as thumbnail
    def _mkthumb(in_file, out_file):
        image = Image.open(in_file)
        image.thumbnail((96, 96))
        image.save(out_file)

    # Check for cached image first
    if path.exists(filepath):
        parent.log.debug("Found image: {}".format(filepath))

    # Try to find image in local path (even for streams... who knows)
    elif find_image(parent, tmp_file, url, artist, album):
        parent.log.debug("Searching filesystem")
        _mkthumb(tmp_file, filepath)

    # If not, search google
    elif fetch_image(parent, tmp_file, artist, album):
        parent.log.debug("Searching web")
        _mkthumb(tmp_file, filepath)

    return filepath


def find_image(parent, temp, url, artist=None, album=None):
    """Search filesystem for artwork

    If `url` starts with HTTP, we assume we're streaming and
    make a guess on where to find artwork (music_dir/artist/album/)
    If `url` is a local path, just look in the same directory

    Args:
        url (str): file path or web address
        artist (str): artist name
        album (str): album name

    Return:
        Return True if local image cached
    """

    # Build search path
    music_dir = path.expanduser(parent.config["music"])

    # If streaming... Guess!
    if url.startswith("http"):
        base_dir = path.join(music_dir, artist, album)

    # If local, use it
    else:
        base_dir = path.dirname(path.join(music_dir, url))

    parent.log.debug("Search path: {}".format(base_dir))

    if path.exists(base_dir):
        # Search for matching extensions
        for ext in ["png", "jpg", "jpeg"]:
            img_match = glob("{}/*.{}".format(base_dir, ext))

            # Return first match
            if img_match:
                copyfile(img_match[0], temp)
                parent.log.debug("Local image found: {}".format(img_match[0]))

                return True

    return False


def fetch_image(parent, temp, artist, album):
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
        """Mozilla/5.0 (Windows NT 6.1; WOW64)
              AppleWebKit/537.36 (KHTML,like Gecko)
              Chrome/43.0.2357.134 Safari/537.36"""
    }

    # Return search results
    results = BeautifulSoup(urlopen(Request(search_url, headers=search_agent)),
                            "html.parser")

    # Find image on page
    img_div = results.find("div", {"class": "rg_meta"})
    img_url = json.loads(img_div.text)["ou"]

    if urlretrieve(img_url, temp):
        parent.log.debug("Search image found: {}".format(temp))

        return True

    return False
