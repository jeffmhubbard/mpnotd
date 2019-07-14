#!/usr/bin/env python3

# -*- coding: utf-8 -*-

# MPDNotify - MPD Notification Daemon

import sys
from os import path

import notify2

from .artwork import cache_artwork
from .cavacolor import CavaColor
from .client import (auth_client, get_client, quit_client,
                     get_currentsong, get_nextsong)
from .utils import (clean_cache, get_logger, load_config, read_args,
                    write_config)

APP_NAME = "mpnotd"
APP_DESC = "MPD Notification Daemon"
APP_DIRS = {
    "cache": path.join(path.expanduser("~/.cache"), APP_NAME),
    "config": path.join(path.expanduser("~/.config"), APP_NAME),
    "plugins": path.join(path.expanduser("~/.config"), APP_NAME, "plugins"),
    "runpath": path.dirname(path.realpath(__file__)),
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
    "timeout": 10,
    # Path to music folder
    "music": "~/Music/",
    # CAVA color 0 no, 1 yes, 2 custom
    "cava": 0,
    # list of hex colors for cava 2, comma separated
    "cava_colors": "#ff0000,#00ff00,#0000ff",
}


class MPDNotify:

    # Load defaults
    config = DEFAULTS
    paths = APP_DIRS
    name = APP_NAME
    desc = APP_DESC
    icon = path.join(paths["runpath"], "images/mpnotd.svg")

    def __init__(self, auth=None, debug=False):
        """ MPD Notification Daemon

        Args:
            auth (str): Password string or None
            debug (bool): Log debug messages

        """

        # Parse command line arguments
        self.args = read_args(self.name, self.desc)

        # Enable debugging messages
        if self.args.DEBUG or debug:
            global DEBUG
            DEBUG = True

        self.inifile = path.join(self.paths["config"], "config")

        # Write config and quit
        if self.args.writeini:
            write_config(self.name, self.inifile, DEFAULTS)
            sys.exit(0)

        # Load user config
        self.config = load_config(self.name, self.inifile, self.config)

        # Start logging
        logfile = path.join(self.paths["cache"], "debug.log")
        self.log = get_logger(logfile, DEBUG)
        self.log.debug(u"\u2500" * 50)

        # Open MPD connection
        self.client = get_client(self.config, self.log)

        # If auth passed as arg, overwrite config
        if auth is not None:
            self.config["auth"] = auth

        # Send password if set (untested)
        if not self.config["auth"] == "":
            auth_client(self.client, self.config["auth"], self.log)

        try:
            self.mpd_events()
        except (KeyboardInterrupt, SystemExit):
            quit_client(self.client, self.log)
            sys.exit(1)

    def mpd_events(self):
        """ Display notifications for changes to MPD subsystems
        """

        cachedir = self.paths["cache"]
        musicdir = self.config["music"]
        hostname = self.config["host"]

        # Get initial status and outputs
        _status = self.client.status()
        _outputs = self.client.outputs()

        while True:

            # Clean cached artwork
            clean_cache(cachedir, self.log)

            data = {"summary": hostname}

            # Watch MPDClient.idle for changes
            subsystems = self.client.idle("player", "update", "output")

            for subsys in subsystems:
                self.log.debug("Subsys: {}".format(subsys))

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
                        data["icon"] = self.icon

                        Notification(**data)

                    # Player stopped
                    elif state == "stop":

                        data["message"] = "<i>Playback stopped...</i>"
                        data["icon"] = self.icon
                        self._status = None

                        Notification(**data)

                    # Show current song
                    elif state == "play" or _status["songid"] != status[
                            "songid"]:

                        current = get_currentsong(self.client)

                        # Only show after tag data is read
                        if all(key in current
                               for key in ("artist", "title", "album")):

                            # cache album art
                            artwork = cache_artwork(
                                cachedir,
                                musicdir,
                                self.log,
                                current['file'],
                                current['artist'],
                                current['album'])

                            # notifcation payload
                            data["summary"] = "Playing..."
                            data["message"] = "<b>{}</b>\nBy <b>{}</b>\nFrom <b>{}</b>".format(
                                    current['title'],
                                    current['artist'],
                                    current['album'])
                            data["icon"] = artwork

                            # Show Notification
                            Notification(**data)

                            # set CAVA color
                            if int(self.config["cava"]) > 0:
                                CavaColor(self.config, artwork)

                            # Cache album art for next song
                            nextsong = get_nextsong(self.client, status)
                            cache_artwork(
                                cachedir,
                                musicdir,
                                self.log,
                                nextsong['file'],
                                nextsong['artist'],
                                nextsong['album'])

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

                    Notification(**data)
                    self.log.debug(data["message"])

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

                            Notification(**data)
                            self.log.debug(data["message"])

                    _outputs = outputs


class Notification:

    def __init__(self,
                 summary=None,
                 message=None,
                 icon=None,
                 timeout=10,
                 **kwargs):

        notify2.init(summary)
        popup = notify2.Notification(summary, message, icon)
        popup.set_timeout(int(timeout) * 1000)
        popup.show()


if __name__ == "__main__":
    MPDNotify()

# vim: set ft=python
