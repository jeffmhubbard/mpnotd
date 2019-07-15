# -*- coding: utf-8 -*-

""" MPD Client
"""

from mpd import MPDClient, MPDError, ConnectionError


def get_client(config, log):
    """ Setup MPD connection, return `client`
    """

    host = config["host"]
    port = config["port"]

    client = MPDClient()

    try:
        client.connect(host, port)
        log.debug("MPD connection established!")
    except ConnectionError as conn_err:
        log.exception("MPD Conn error: {}".format(conn_err))
        raise

    return client


def get_currentsong(client):
    """ Return current song dict
    """

    return client.currentsong()


def get_nextsong(client, status):
    """ Return next song dict
    """

    next_id = status["nextsongid"]
    song = client.playlistid(next_id)[0]
    url = song["file"]

    if "name" in song:
        artist, title, album = song["name"].split(" - ")
    else:
        artist = song["artist"]
        album = song["album"]

    nextsong = {
        "file": url,
        "artist": artist,
        "album": album,
    }

    return nextsong


def auth_client(client, password, log):
    """ Authenticate to MPD server
    """

    try:
        client.password(password)
        log.debug("MPD Auth accepted!")
    except MPDError as mpd_err:
        log.exception("MPD Auth error: {}".format(mpd_err))


def quit_client(client, log):
    """ End MPD connection
    """

    client.close()
    client.disconnect()
    log.debug("MPD connection closed!")
