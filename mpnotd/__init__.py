#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# mpnotd - MPD Notification Daemon

import json
import logging
import sys
import time
from glob import glob
from os import listdir, path, remove
from re import sub
from shutil import copyfile
from urllib.parse import quote
from urllib.request import Request, urlopen, urlretrieve

import notify2
from bs4 import BeautifulSoup
from mpd import MPDClient
from PIL import Image

from utils import (
        read_args,
        load_config,
        write_config,
        _makedirs,
        clean_cache)

APP_NAME = "mpnotd"
APP_DESC = "MPD Notification Daemon"

APP_DIRS = {
    "cache": path.join(path.expanduser("~/.cache"), APP_NAME),
    "config": path.join(path.expanduser("~/.config"), APP_NAME),
    "plugins": path.join(path.expanduser("~/.config"), APP_NAME, "plugins"),
}

DEBUG = False

# Default configuration
DEFAULTS = {
    # Host name of MPD server
    "host": "localhost",
    # Port number of MPD server
    "port": 6600,
    # Password (leave blank for no password)
    "auth": "",
    # Notification timeout in seconds
    "time": 10,
    # Path to music folder
    "music": "~/Music/",
}


class MpNotd:

    # Load defaults
    name = APP_NAME
    desc = APP_DESC
    paths = APP_DIRS
    config = DEFAULTS
    updating = False

    def __init__(self, auth=None, debug=False):
        """MPD Notification Daemon

        Args:
            debug (bool): Log debug messages

        """

        # Parse command line arguments
        self.args = read_args(
                self.name,
                self.desc)

        # Write config and quit

        if self.args.writeini:
            write_config(
                self.name,
                self.paths,
                self.config)

            sys.exit(0)

        # Enable debugging messages

        if self.args.DEBUG or debug:
            global DEBUG
            DEBUG = True

        # Load user config
        self.config = load_config(
                self.name,
                self.paths,
                self.config)

        # Start logging
        self.log_start()
        self.log.debug(u"\u2500" * 79)

        # Open MPD connection
        self.mpd_start()

        # If auth passed as arg, overwrite config

        if auth is not None:
            self.config["auth"] = auth

        # Send password if set (untested)

        if not self.config["auth"] == "":
            self.mpd_auth(self.config["auth"])

        try:
            self.idle_loop()
        except Exception as e:
            self.log.debug(e, exc_info=True)

        # Close MPD connection
        self.mpd_end()

#    def read_args(self):
#        """Read command line arguments
#        """
#
#        parser = argparse.ArgumentParser(prog=self.name,
#                                         description="show current song info")
#
#        group = parser.add_argument_group("useful arguments:")
#        mxg = group.add_mutually_exclusive_group()
#
#        # debug
#        mxg.add_argument("--DEBUG",
#                         action="store_true",
#                         help="log debug messages")
#
#        # write a config file
#        mxg.add_argument("--writeini",
#                         action="store_true",
#                         help="write config file and quit")
#
#        return parser.parse_args(sys.argv[1:])

    def mpd_start(self):
        """Setup MPD connection
        """

        host = self.config["host"]
        port = self.config["port"]

        self.client = MPDClient()
        self.client.connect(host, port)
        self.log.debug("MPD connection established!")

    def mpd_end(self):
        """End MPD connection
        """

        self.client.close()
        self.client.disconnect()
        self.log.debug("MPD connection closed!")

    def mpd_auth(self, password):
        """Authenticate to MPD server

        Args:
            password (str): Plain text password

        """

        try:
            self.client.password(password)
            self.log.debug("MPD Auth accepted!")
        except Exception as e:
            self.log.exception("MPD Auth error: {}".format(e))
            pass

    def log_start(self):
        """Setup logging
        """

        log_to = path.join(self.paths["cache"], "debug.log")

        if not path.exists(log_to):
            _makedirs(log_to)

        logging.basicConfig(
            format="%(asctime)s %(message)s",
            datefmt="%m/%d/%Y %I:%M:%S %p",
            filename=log_to,
            filemode="w",
        )
        self.log = logging.getLogger()

        if DEBUG:
            self.log.setLevel(logging.DEBUG)

    def show_notification(self,
                          summary=None,
                          message=None,
                          icon=None,
                          **kwargs):
        """Display notification

        Build notification. Defaults are provided below so show_notification()
        can be called with any number of arguments or even none.

        Args:
            summary (str): Notification title
            message (str): Notification body
            icon (str): Album art or icon
        """

        # Defaults

        if not summary:
            summary = self.name

        if not message:
            message = ""

        if not icon:
            icon = "image-missing"

        notify2.init(summary)
        popup = notify2.Notification(summary, message, icon)

        # Set timeout
        timeout = self.config["time"]

        if timeout:
            popup.set_timeout(int(timeout) * 1000)

        # Display
        popup.show()

    def get_nowplaying(self, title, artist, album, **kwargs):
        """Get current song info

        Args:
            title (str): Song title
            artist (str): Song artist
            album (str): Song album

        Returns:
            Return `data` payload for show_notification()

        """

        data = {}

        # Format summary and message
        summary = "Playing..."
        message = "<b>{}</b>\nBy <b>{}</b>\nFrom <b>{}</b>".format(
            title, artist, album)
        icon = None

        # Get album art
        try:
            icon = self.get_albumart(kwargs["file"], artist, album)
        except Exception as e:
            self.log.debug(e)
            pass

        # Build notification payload
        data["summary"] = summary
        data["message"] = message
        data["icon"] = icon

        self.log.debug("Now Playing: {}".format(data))

        return data

    def get_nextsong(self, status):
        """Get next song info

        Get next song info so we can precache album art
        Returns list suitable for get_albumart(*args)

        Args:
            status (dict): current status

        Returns:
            Returns list (url, artist, album)

        """

        next_id = status["nextsongid"]
        song = self.client.playlistid(next_id)[0]
        url = song["file"]

        if "name" in song:
            artist, title, album = song["name"].split(" - ")
        else:
            artist = song["artist"]
            album = song["album"]

        return [url, artist, album]

    def get_albumart(self, url, artist, album, *args):
        """Get album art thumbnail

        Attempt to find album art and thumbnail it
        First look for existing thumbnail
        Then find_artwork() searches filesystem
        Or else fetch_artwork() searches web

        Args:
            url (str): MPD database path or http url
            artist (str): Song artist
            album (str): Song ablum

        Returns:
           Return path to thumbnail or None

        """

        # Get destination file path
        filename = "cover-{}-{}.png".format(artist, album)
        filename = sub("\s", "_", filename).lower()
        filepath = path.join(self.paths["cache"], filename)
        self.log.debug("Cache Dest: {}".format(filepath))

        # Check for cached image first

        if path.exists(filepath):
            self.log.debug("Found image: {}".format(filepath))

            return filepath

        # Temp file
        self.tmp_file = path.join(self.paths["cache"], "artwork.tmp")

        # Remove cached artwork
        if path.exists(self.tmp_file):
            remove(self.tmp_file)
            self.log.debug("Purge tmp: {}".format(self.tmp_file))

        # Save as thumbnail
        def _mkthumb(in_file, out_file):
            im = Image.open(in_file)
            im.thumbnail((96, 96))
            im.save(out_file)

        # Try to find image in local path (even for streams... who knows)
        self.log.debug("Searching filesystem")

        if self.find_artwork(url, artist, album):
            if _mkthumb(self.tmp_file, filepath):
                return filepath

        # If not, search google
        self.log.debug("Searching web")

        if self.fetch_artwork(artist, album):
            if _mkthumb(self.tmp_file, filepath):
                return filepath

    def find_artwork(self, url, artist=None, album=None):
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
        music_dir = path.expanduser(self.config["music"])
        # If streaming... Guess!

        if url.startswith("http"):
            base_dir = path.join(music_dir, artist, album)
        # If local, use it
        else:
            base_dir = path.dirname(path.join(music_dir, url))
        self.log.debug("Search path: {}".format(base_dir))

        if path.exists(base_dir):
            # Search for matching extensions

            for ext in ["png", "jpg", "jpeg"]:
                img_match = glob("{}/*.{}".format(base_dir, ext))

                # Return first match

                if len(img_match) > 0:
                    copyfile(img_match[0], self.tmp_file)
                    self.log.debug("Local image found: {}".format(
                        img_match[0]))

                    return True

    def fetch_artwork(self, artist, album):
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
        results = BeautifulSoup(
            urlopen(Request(search_url, headers=search_agent)), "html.parser")

        # Find image on page
        img_div = results.find("div", {"class": "rg_meta"})
        img_url = json.loads(img_div.text)["ou"]

        urlretrieve(img_url, self.tmp_file)
        self.log.debug("Search image found: {}".format(self.tmp_file))

        return True

    def idle_loop(self):
        """Display notifications for changes to MPD subsystems
        """

        # Get initial status and outputs
        _status = self.client.status()
        _outputs = self.client.outputs()

        while True:

            # Clean cached artwork
            clean_cache(self.path, self.log)

            data = {}

            # Watch MPDClient.idle for changes
            subsystems = self.client.idle("player", "update", "output")

            for subsys in subsystems:
                self.log.debug("Subsys: {}".format(subsys))
                data["summary"] = self.name
                data["icon"] = "rhythmbox-panel"

                # Player state changed

                if subsys == "player":

                    # Get current status
                    status = self.client.status()

                    # Get current state
                    state = status.get("state", "")

                    self.log.debug("Player: {}".format(state))

                    # Player paused

                    if state == "pause":
                        data["message"] = "<i>Playback paused...</i>"
                        data["icon"] = "rhythmbox-notplaying"
                        self.show_notification(**data)

                    # Player stopped
                    elif state == "stop":
                        data["message"] = "<i>Playback stopped...</i>"
                        data["icon"] = "rhythmbox-notplaying"
                        self._status = None
                        self.show_notification(**data)

                    # Show current song
                    elif state == "play" or _status["songid"] != status[
                            "songid"]:
                        song = self.client.currentsong()

                        # Only show after tag data is read

                        if all(key in song
                               for key in ("artist", "title", "album")):

                            # Show Notification
                            data = self.get_nowplaying(**song)
                            self.show_notification(**data)

                            # Cache album art for next song
                            try:
                                nextsong = self.get_nextsong(status)
                                self.get_albumart(*nextsong)
                            except Exception:
                                pass

                    # Save status
                    _status = status

                # Upadte state changed
                elif subsys == "update":

                    if self.updating:
                        data["message"] = "Database updated!"
                        data["icon"] = "checkbox-checked"
                        self.updating = False
                    else:
                        data["message"] = "Updating database..."
                        data["icon"] = "content-loading"
                        self.updating = True

                    self.log.debug(data["message"])
                    self.show_notification(**data)

                # Outputs changed
                elif subsys == "output":
                    outputs = self.client.outputs()

                    for _out, out in zip(_outputs, outputs):

                        if _out["outputenabled"] != out["outputenabled"]:

                            if out["outputenabled"] == "1":
                                data["message"] = "Output {} enabled".format(
                                    out["outputname"])
                                data["icon"] = "dialog-info"
                            else:
                                data["message"] = "Output {} disabled!".format(
                                    out["outputname"])
                                data["icon"] = "dialog-error"

                            self.log.debug(data["message"])
                            self.show_notification(**data)

                    _outputs = outputs


if __name__ == "__main__":
    MpNotd()

# vim: set ft=python
