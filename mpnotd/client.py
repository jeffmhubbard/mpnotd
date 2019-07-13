# -*- coding: utf-8 -*-

"""MPD Client"""

from mpd import MPDClient


def get_client(config, log):
    """Setup MPD connection
    """

    host = config["host"]
    port = config["port"]

    client = MPDClient()
    client.connect(host, port)
    log.debug("MPD connection established!")
    return client


def quit_client(client, log):
    """End MPD connection
    """

    client.close()
    client.disconnect()
    log.debug("MPD connection closed!")


def auth_client(client, password, log):
    """Authenticate to MPD server

    Args:
        password (str): Plain text password

    """

    try:
        client.password(password)
        log.debug("MPD Auth accepted!")
    except Exception as auth_err:
        log.exception("MPD Auth error: {}".format(auth_err))
