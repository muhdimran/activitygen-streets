import os
import sys
import noise

from typing import List, Tuple
import xml.etree.ElementTree as ET
from xml.etree import ElementTree
from utility import distance, smoothstep

import numpy as np

if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME' to use sumolib")

import sumolib


class NoiseSampler:
    """
    The NoiseSampler defines a noise configuration that can be sampled from
    """

    def __init__(
        self,
        centres: List[Tuple[float, float]],
        centre_weight: float,
        radius: float,
        offset: float,
        octaves: int = 3,
    ):
        self._centres = centres
        self._centre_weight = centre_weight
        self._radius = radius
        self._offset = offset
        self._octaves = octaves

    def sample(self, pos: Tuple[float, float]) -> float:
        """
        Samples the noise at the given position, considering multiple centers.
        :param pos: the position to sample at
        :return: a float in the range [0,1)
        """
        scale = 4 / self._radius
        noise01 = (
            noise.pnoise3(
                pos[0] * scale, pos[1] * scale, self._offset, octaves=self._octaves
            )
            + 1
        ) / 2

        # Calculate total influence from all centers
        total_gradient = 0
        for center in self._centres:
            distance_to_center = distance(pos, center)
            # Normalize distance for consistent influence across centers
            gradient = 1 - (distance_to_center / max(self._radius, distance_to_center))
            total_gradient += gradient * self._centre_weight

        # Combine noise and gradient with center weight
        return (smoothstep(noise01) + total_gradient * self._centre_weight) / (
            1 + self._centre_weight
        )


def get_edge_pair_centroid(coords: List[Tuple[float, float]]) -> Tuple[float, float]:
    """
    Centroid of rectangle (edge_pair) = (width/2, height/2)
    :param coords: [(x_1,y_1), (x_2,y_2), ... , (x_n,y_n)]
    :return: Centroid of given shape
    """
    x_avg = np.mean([pos[0] for pos in coords])
    y_avg = np.mean([pos[1] for pos in coords])
    return float(x_avg), float(y_avg)


def setup_streets(
    net: sumolib.net.Net,
    xml: ElementTree,
    pop_noise: NoiseSampler,
    work_noise: NoiseSampler,
):
    """
    Create a street for each edge in the network and calculate its population and workplaces based on
    modified Perlin noise from NoiseSamplers
    :param net: the SUMO network
    :param pop_noise: NoiseSampler to use for population
    :param work_noise: NoiseSample to use for workplaces
    """

    streets = xml.find("streets")
    if streets is None:
        streets = ET.SubElement(xml.getroot(), "streets")

    # Some edges might already have a street, so we want to ignore those
    known_streets = {
        street.attrib["edge"]: street for street in streets.findall("street")
    }

    for edge in net.getEdges():
        eid = edge.getID()
        if eid not in known_streets:
            # This edge is missing a street entry. Find population and industry for this edge
            pos = get_edge_pair_centroid(edge.getShape())
            population = pop_noise.sample(pos)
            industry = work_noise.sample(pos)

            ET.SubElement(
                streets,
                "street",
                {
                    "edge": eid,
                    "population": str(population),
                    "workPosition": str(industry),
                },
            )
