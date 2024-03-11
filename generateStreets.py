"""
Usage:
    generateStreets.py --net-file=FILE --output-file=FILE [--centre.pop-weight=F] [--centre.work-weight=F]

Input Options:
    -n, --net-file FILE     Input road network to create streets from


Output Options:    
    -o, --output-file=FILE  Output file to write streets to

Other Options:
    --centre.pop-weight=F       The increase in population near the city center. [default: 0.5]
    --centre.work-weight=F      The increase in work places near the city center. [default: 0.1]
"""

import os
import sys
import random

import xml.etree.ElementTree as ET

from docopt import docopt
from perlin import NoiseSampler, setup_streets

from utility import find_city_centre, radius_of_network

if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME' to use sumolib")

import sumolib


def main():
    args = docopt(__doc__)

    pop_offset = 65_536 * random.random()
    work_offset = 65_536 * random.random()
    while pop_offset == work_offset:
        work_offset = 65_536 * random.random()

    # Read SUMO network
    net = sumolib.net.readNet(args["--net-file"])

    centre = find_city_centre(net)
    radius = radius_of_network(net, centre)

    pop_noise = NoiseSampler(
        centre, float(args["--centre.pop-weight"]), radius, pop_offset
    )
    work_noise = NoiseSampler(
        centre, float(args["--centre.work-weight"]), radius, work_offset
    )

    root = ET.Element("city")
    tree = ET.ElementTree(root)

    tree.write(args["--output-file"], encoding="utf-8", xml_declaration=True)
    stats = ET.parse(args["--output-file"])

    setup_streets(net, stats, pop_noise, work_noise)
    stats.write(args["--output-file"])


if __name__ == "__main__":
    main()
