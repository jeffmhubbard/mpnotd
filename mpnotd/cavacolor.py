# -*- coding: utf-8 -*-

""" CAVA Color
"""

import fileinput
import subprocess
import sys
from os import path

from colorthief import ColorThief

from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000
from colormath.color_objects import LabColor, sRGBColor

CAVA_CFG = path.expanduser("~/.config/cava/config")


def cava_color(icon):

    """ Set CAVA color with dominant color from artwork
    """

    artwork = path.expanduser(icon)
    print(artwork)

    if path.exists(artwork):

        # get dominant color
        art_color = get_artwork_color(artwork)

        # get hex
        hex_color = '#{:02x}{:02x}{:02x}'.format(
            art_color[0],
            art_color[1],
            art_color[2])

        # write to config
        update_config(CAVA_CFG, hex_color)

        # read config
        restart_cava()


def cava_color_term(image, term_colors):

    """ Set CAVA color with nearest color in term_colors
    """

    artwork = path.expanduser(image)
    palette = term_colors.split(",")

    if path.exists(artwork):

        # get dominant color
        dom_color = get_artwork_color(artwork)

        # return closest palette match
        color_match = get_palette_match(dom_color, palette)

        # write to config
        update_config(CAVA_CFG, color_match)

        # read config
        restart_cava()


def get_artwork_color(image):

    """ Return dominant color from image
    """

    image = ColorThief(image)

    return image.get_color(quality=1)


def get_palette_match(color, palette):

    """ Return palette color closest to given color
    """

    color1_rgb = sRGBColor(*color)
    color1_lab = convert_color(color1_rgb, LabColor)

    results = []

    for hcolor in palette:

        color2 = tuple(
            int(hcolor.strip("#")[i:i + 2], 16) for i in (0, 2, 4))
        color2_rgb = sRGBColor(*color2)
        color2_lab = convert_color(color2_rgb, LabColor)

        delta_e = delta_e_cie2000(color1_lab, color2_lab)
        results.append((int(delta_e), hcolor))

    results.sort()

    return results[0][1]


def update_config(config, color):

    """ Find and replace `foreground` in CAVA_CFG
    """

    if path.exists(config):
        for line in fileinput.input([config], inplace=True):
            if line.strip().startswith("foreground ="):
                line = "foreground = '%s'\n" % color
            sys.stdout.write(line)


def restart_cava():

    """ Force CAVA to read config and redraw
    """

    subprocess.run(["pkill", "-USR2", "cava"])
