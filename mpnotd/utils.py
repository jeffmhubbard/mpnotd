from os import path, makedirs
import sys
import argparse
import configparser

def read_args(name, desc):
    """Read command line arguments
    """

    parser = argparse.ArgumentParser(
            prog=name,
            description=desc)

    group = parser.add_argument_group("useful arguments:")
    mxg = group.add_mutually_exclusive_group()

    # debug
    mxg.add_argument("--DEBUG",
                     action="store_true",
                     help="log debug messages")

    # write a config file
    mxg.add_argument("--writeini",
                     action="store_true",
                     help="write config file and quit")

    return parser.parse_args(sys.argv[1:])

def load_config(name, paths, defaults):
    """Load user config
    """

    config = {}

    # Override from user config
    fname = path.join(paths["config"], "config")

    if path.exists(fname):

        uconf = configparser.ConfigParser(defaults)
        uconf.read(fname)

        # All keys are required for valid config
        try:
            for cvar in defaults.keys():
                config[cvar] = uconf.get(name, cvar)
            return config
        except Exception:
            pass

def write_config(name, paths, defaults):
    """Write config file with defaults
    """

    filename = path.join(paths["config"], "config")

    # Config already exists, print location
    if path.exists(filename):
        print("File exists! {}".format(filename))
    else:
        # Check for directory and create
        _makedirs(filename)

        # Create parser and import defaults
        default_conf = configparser.ConfigParser()
        default_conf[name] = defaults

        # Write config
        with open(filename, "w") as new_conf:
            default_conf.write(new_conf)
            print("Config written to {}".format(filename))

def _makedirs(dest):
    """Create directories for target file

    Args:
        dest (str): Path of destination file

    """

    base_dir = path.dirname(path.expanduser(dest))

    if path.exists(base_dir):
        return
    else:
        try:
            makedirs(base_dir, exist_ok=True)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

def clean_cache(paths, log, limit=1):
    """Remove cached images

    Args:
        limit (int): Number of hours to keep cached image

    """

    limit *= 3600

    tmp_dir = paths["cache"]
    use_by = time.time() - limit
    log.debug("Cache Age: {}".format(use_by))

    for filename in listdir(tmp_dir):
        filepath = path.join(tmp_dir, filename)

        if filepath.endswith(".png") and path.getatime(filepath) < use_by:
            log.debug("Removing: {}".format(filepath))
            remove(path.join(filepath))

