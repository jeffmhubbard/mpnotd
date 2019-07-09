# -*- coding: utf-8 -*-

"""MPD Client"""

from mpd import MPDClient


def get_client(parent):
    """Setup MPD connection
    """

    host = parent.config["host"]
    port = parent.config["port"]

    client = MPDClient()
    client.connect(host, port)
    parent.log.debug("MPD connection established!")
    return client


def quit_client(parent):
    """End MPD connection
    """

    parent.client.close()
    parent.client.disconnect()
    parent.log.debug("MPD connection closed!")


def auth_client(parent, password):
    """Authenticate to MPD server

    Args:
        password (str): Plain text password

    """

    try:
        parent.client.password(password)
        parent.log.debug("MPD Auth accepted!")
    except Exception as e:
        parent.log.exception("MPD Auth error: {}".format(e))
