# -*- coding: utf-8 -*-

"""CAVA Color
"""

import fileinput
import subprocess
import sys
from os import path

from colorthief import ColorThief

from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000
from colormath.color_objects import LabColor, sRGBColor

CONFIG = path.expanduser("~/.config/cava/config")

TERM_COLORS = {
    "black": "#000000",
    "dark_red": "#c23621",
    "dark_green": "#25bc24",
    "dark_yellow": "#adad27",
    "dark_blue": "#492ee1",
    "dark_magenta": "#d338d3",
    "dark_cyan": "#33bbc8",
    "grey": "#cbcccd",
    "dark_grey": "#818383",
    "red": "#fc391f",
    "green": "#31e722",
    "yellow": "#eaec23",
    "blue": "#5833ff",
    "magenta": "#f935f8",
    "cyan": "#14f0f0",
    "white": "#e9ebeb",
}


def cava_color(icon):

    """Set CAVA color with dominant color from artwork
    """

    artwork = path.expanduser(icon)

    if path.exists(artwork):

        # get dominant color
        art_color = get_artwork_color(artwork)

        # get hex
        hex_color = '#{:02x}{:02x}{:02x}'.format(
            art_color[0],
            art_color[1],
            art_color[2])

        # write to config
        update_config(CONFIG, hex_color)

        # read config
        restart_cava()


def cava_xcolor(icon):

    """Set CAVA color with nearest color in TERM_COLORS
        This is pretty unpredictable and is mostly  for fun
        TERM_COLORS key names are unimportant, and can be
        antyhing
    """

    artwork = path.expanduser(icon)

    if path.exists(artwork):

        # get dominant color
        art_color = get_artwork_color(artwork)

        # return closest
        palette_color = get_palette_color(art_color)

        # write to config
        update_config(CONFIG, palette_color)

        # read config
        restart_cava()


def get_artwork_color(icon):

    """docstring
    """

    icon = ColorThief(icon)

    return icon.get_color(quality=1)


def get_palette_color(color):

    """docstring
    """

    color1_rgb = sRGBColor(*color)
    color1_lab = convert_color(color1_rgb, LabColor)

    results = []

    for name, hcolor in TERM_COLORS.items():

        color2 = tuple(
            int(hcolor.strip("#")[i:i + 2], 16) for i in (0, 2, 4))
        color2_rgb = sRGBColor(*color2)
        color2_lab = convert_color(color2_rgb, LabColor)

        delta_e = delta_e_cie2000(color1_lab, color2_lab)
        results.append((int(delta_e), hcolor))

    results.sort()

    return results[0][1]


def update_config(config, color):

    """docstring
    """

    if path.exists(config):
        for line in fileinput.input([config], inplace=True):
            if line.strip().startswith("foreground ="):
                line = "foreground = '%s'\n" % color
            sys.stdout.write(line)


def restart_cava():
    subprocess.run(["pkill", "-USR2", "cava"])

