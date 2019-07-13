# -*- coding: utf-8 -*-

"""Utility methods"""

import argparse
import configparser
import errno
import logging
import re
import string
import sys
import time
from os import listdir, makedirs, path, remove


def read_args(name, desc):
    """Read command line arguments
    """

    parser = argparse.ArgumentParser(prog=name, description=desc)

    group = parser.add_argument_group("useful arguments:")
    mxg = group.add_mutually_exclusive_group()

    # debug
    mxg.add_argument("--DEBUG", action="store_true", help="log debug messages")

    # write a config file
    mxg.add_argument("--writeini",
                     action="store_true",
                     help="write config file and quit")

    return parser.parse_args(sys.argv[1:])


def load_config(name, inifile, defaults):
    """Load user config
    """

    config = {}

    # Override from user config
    if path.exists(inifile):
        uconf = configparser.ConfigParser(defaults)
        uconf.read(inifile)

        # All keys are required for valid config
        for cvar in defaults.keys():
            config[cvar] = uconf.get(name, cvar)

    return config


def write_config(name, inifile, defaults):
    """Write config file with defaults
    """

    # Config already exists, print location
    if path.exists(inifile):
        print("File exists! {}".format(inifile))
    else:
        # Check for directory and create
        _makedirs(inifile)

        # Create parser and import defaults
        default_conf = configparser.ConfigParser()
        default_conf[name] = defaults

        # Write config
        with open(inifile, "w") as new_conf:
            default_conf.write(new_conf)
            print("Config written to {}".format(inifile))


def get_logger(logfile, debug):
    """Setup logging
    """
    if not path.exists(logfile):
        _makedirs(logfile)

    logging.basicConfig(
        format="%(asctime)s %(message)s",
        datefmt="%m/%d/%Y %I:%M:%S %p",
        filename=logfile,
        filemode="w",
    )
    log = logging.getLogger()

    if debug:
        log.setLevel(logging.DEBUG)

    return log


def get_valid_str(text):
    """Get valid strings for filenames

    Args:
        text (str): String to make valid

    Returns:
        Return string containing valid file path characters
    """

    vchar = "-_.()[] %s%s" % (string.ascii_letters, string.digits)
    text = re.sub(' ', '_', text)
    return ''.join(c for c in text if c in vchar)


def _makedirs(dest):
    """Create directories for target file

    Args:
        dest (str): Path of destination file

    """

    base_dir = path.dirname(path.expanduser(dest))

    if not path.exists(base_dir):
        try:
            makedirs(base_dir, exist_ok=True)
        except OSError as md_error:
            if md_error.errno != errno.EEXIST:
                raise


def clean_cache(cachedir, log, limit=100):
    """Remove cached images

    Args:
        cachedir (str): Path to image cache
        log (obj): Logger for debug
        limit (int): Number of hours to keep cached image

    """

    limit *= 3600

    use_by = time.time() - limit
    log.debug("Cache Age: {}".format(use_by))

    for filename in listdir(cachedir):
        filepath = path.join(cachedir, filename)

        if filepath.endswith(".png") and path.getatime(filepath) < use_by:
            log.debug("Removing: {}".format(filepath))
            remove(path.join(filepath))
