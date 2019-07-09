#!/usr/bin/env python3

# -*- coding: utf-8 -*-

# mpnotd - MPD Notification Daemon

import sys
from os import path

import notify2

from .artwork import get_albumart
from .client import get_client, auth_client, quit_client
from .utils import clean_cache, get_logger
from .utils import load_config, read_args, write_config

APP_NAME = "mpnotd"
APP_DESC = "MPD Notification Daemon"
APP_DIRS = {
    "cache": path.join(path.expanduser("~/.cache"), APP_NAME),
    "config": path.join(path.expanduser("~/.config"), APP_NAME),
    "plugins": path.join(path.expanduser("~/.config"), APP_NAME, "plugins"),
    "run": path.dirname(path.realpath(__file__)),
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


class MpNotd(object):

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
        self.args = read_args(self.name, self.desc)

        # Write config and quit
        if self.args.writeini:
            write_config(self.name, self.paths, self.config)
            sys.exit(0)

        # Enable debugging messages
        if self.args.DEBUG or debug:
            global DEBUG
            DEBUG = True

        # Load user config
        self.config = load_config(self.name, self.paths, self.config)

        # Start logging
        self.log = get_logger(self.paths, DEBUG)
        self.log.debug(u"\u2500" * 50)

        # Open MPD connection
        self.client = get_client(self)

        # If auth passed as arg, overwrite config
        if auth is not None:
            self.config["auth"] = auth

        # Send password if set (untested)
        if not self.config["auth"] == "":
            auth_client(self)

        try:
            self.mpd_events()
        except Exception as e:
            self.log.debug(e, exc_info=True)
        except (KeyboardInterrupt, SystemExit):
            sys.exit(1)

        # Close MPD connection
        quit_client()

#    def get_client(self):
#        """Setup MPD connection
#        """
#
#        host = self.config["host"]
#        port = self.config["port"]
#
#        self.client = MPDClient()
#        self.client.connect(host, port)
#        self.log.debug("MPD connection established!")
#
#    def quit_client(self):
#        """End MPD connection
#        """
#
#        self.client.close()
#        self.client.disconnect()
#        self.log.debug("MPD connection closed!")
#
#    def auth_client(self, password):
#        """Authenticate to MPD server
#
#        Args:
#            password (str): Plain text password
#
#        """
#
#        try:
#            self.client.password(password)
#            self.log.debug("MPD Auth accepted!")
#        except Exception as e:
#            self.log.exception("MPD Auth error: {}".format(e))
#            pass

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
            icon = path.join(self.paths["run"], "images/mpnotd.svg")

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
            icon = get_albumart(self, kwargs["file"], artist, album)
        except Exception as e:
            self.log.debug(e)
            raise

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

    def mpd_events(self):
        """Display notifications for changes to MPD subsystems
        """

        # Get initial status and outputs
        _status = self.client.status()
        _outputs = self.client.outputs()

        while True:

            # Clean cached artwork
            clean_cache(self.paths, self.log)

            data = {}

            # Watch MPDClient.idle for changes
            subsystems = self.client.idle("player", "update", "output")

            for subsys in subsystems:
                self.log.debug("Subsys: {}".format(subsys))
                data["summary"] = self.config["host"]
                data["icon"] = path.join(
                        self.paths["run"],
                        "images/mpnotd.svg")

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
                        data["icon"] = path.join(
                            self.paths["run"],
                            "images/mpnotd.svg")
                        self.show_notification(**data)

                    # Player stopped
                    elif state == "stop":
                        data["message"] = "<i>Playback stopped...</i>"
                        data["icon"] = path.join(
                            self.paths["run"],
                            "images/mpnotd.svg")
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
                                get_albumart(self, *nextsong)
                            except Exception:
                                pass

                    # Save status
                    _status = status

                # Upadte state changed
                elif subsys == "update":

                    if self.updating:
                        data["message"] = "Database updated!"
                        data["icon"] = path.join(
                            self.paths["run"],
                            "images/mpnotd.svg")
                        self.updating = False
                    else:
                        data["message"] = "Updating database..."
                        data["icon"] = path.join(
                            self.paths["run"],
                            "images/mpnotd.svg")
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
