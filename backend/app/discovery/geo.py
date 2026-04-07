"""Geographic utilities for search coverage strategy.

Implements grid subdivision by density level to ensure exhaustive coverage
when scraping Google Maps (max 60 results per query).
"""

import math
from dataclasses import dataclass


@dataclass
class BoundingBox:
    ne_lat: float
    ne_lng: float
    sw_lat: float
    sw_lng: float

    @property
    def center_lat(self) -> float:
        return (self.ne_lat + self.sw_lat) / 2

    @property
    def center_lng(self) -> float:
        return (self.ne_lng + self.sw_lng) / 2

    @property
    def width_km(self) -> float:
        return haversine(self.center_lat, self.sw_lng, self.center_lat, self.ne_lng)

    @property
    def height_km(self) -> float:
        return haversine(self.sw_lat, self.center_lng, self.ne_lat, self.center_lng)


@dataclass
class SearchCell:
    """A single search cell with center point and radius."""

    latitude: float
    longitude: float
    radius_km: float


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance in km between two points using Haversine formula."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def subdivide_bbox(bbox: BoundingBox, cell_size_km: float) -> list[SearchCell]:
    """Divide a bounding box into grid cells of approximately cell_size_km.

    Each cell gets a center point and radius that covers the cell area.
    The radius is set to cover the diagonal of the cell.

    Args:
        bbox: The area to subdivide
        cell_size_km: Target cell size in km (e.g. 3 for dense, 10 for rural)

    Returns:
        List of SearchCell with center coordinates and radius
    """
    width_km = bbox.width_km
    height_km = bbox.height_km

    cols = max(1, math.ceil(width_km / cell_size_km))
    rows = max(1, math.ceil(height_km / cell_size_km))

    lat_step = (bbox.ne_lat - bbox.sw_lat) / rows
    lng_step = (bbox.ne_lng - bbox.sw_lng) / cols

    # Radius covers the diagonal of each cell
    cell_radius = (cell_size_km * math.sqrt(2)) / 2

    cells = []
    for row in range(rows):
        for col in range(cols):
            center_lat = bbox.sw_lat + lat_step * (row + 0.5)
            center_lng = bbox.sw_lng + lng_step * (col + 0.5)
            cells.append(SearchCell(latitude=center_lat, longitude=center_lng, radius_km=cell_radius))

    return cells


# Density levels for Spain coverage strategy
DENSITY_DENSE = "dense"  # Madrid, Barcelona: 3km grid
DENSITY_MEDIUM = "medium"  # Valencia, Sevilla, etc: 8km grid
DENSITY_RURAL = "rural"  # Rest: single search with large radius


def get_cell_size_for_density(density: str) -> float:
    """Return grid cell size in km for a given density level."""
    return {
        DENSITY_DENSE: 3.0,
        DENSITY_MEDIUM: 8.0,
        DENSITY_RURAL: 30.0,
    }.get(density, 10.0)


def generate_search_cells(
    center_lat: float,
    center_lng: float,
    radius_km: float,
    density: str = DENSITY_RURAL,
) -> list[SearchCell]:
    """Generate search cells for a region based on its density level.

    For rural areas, returns a single cell with the full radius.
    For denser areas, creates a grid within the implied bounding box.

    Args:
        center_lat: Region center latitude
        center_lng: Region center longitude
        radius_km: Region coverage radius
        density: One of DENSITY_DENSE, DENSITY_MEDIUM, DENSITY_RURAL
    """
    if density == DENSITY_RURAL:
        return [SearchCell(latitude=center_lat, longitude=center_lng, radius_km=radius_km)]

    # Convert radius to bounding box
    lat_delta = radius_km / 111.32  # ~111.32 km per degree latitude
    lng_delta = radius_km / (111.32 * math.cos(math.radians(center_lat)))

    bbox = BoundingBox(
        ne_lat=center_lat + lat_delta,
        ne_lng=center_lng + lng_delta,
        sw_lat=center_lat - lat_delta,
        sw_lng=center_lng - lng_delta,
    )

    cell_size = get_cell_size_for_density(density)
    return subdivide_bbox(bbox, cell_size)


# Pre-defined Spanish provinces with density classification
SPAIN_PROVINCES = [
    # Dense (3km grid)
    {"name": "Madrid", "lat": 40.4168, "lng": -3.7038, "radius_km": 35, "density": DENSITY_DENSE},
    {"name": "Barcelona", "lat": 41.3874, "lng": 2.1686, "radius_km": 30, "density": DENSITY_DENSE},
    # Medium (8km grid)
    {"name": "Valencia", "lat": 39.4699, "lng": -0.3763, "radius_km": 25, "density": DENSITY_MEDIUM},
    {"name": "Sevilla", "lat": 37.3891, "lng": -5.9845, "radius_km": 25, "density": DENSITY_MEDIUM},
    {"name": "Málaga", "lat": 36.7213, "lng": -4.4217, "radius_km": 25, "density": DENSITY_MEDIUM},
    {"name": "Zaragoza", "lat": 41.6488, "lng": -0.8891, "radius_km": 20, "density": DENSITY_MEDIUM},
    {"name": "Bilbao", "lat": 43.2630, "lng": -2.9350, "radius_km": 20, "density": DENSITY_MEDIUM},
    {"name": "Alicante", "lat": 38.3452, "lng": -0.4810, "radius_km": 25, "density": DENSITY_MEDIUM},
    {"name": "Murcia", "lat": 37.9922, "lng": -1.1307, "radius_km": 20, "density": DENSITY_MEDIUM},
    {"name": "Palma de Mallorca", "lat": 39.5696, "lng": 2.6502, "radius_km": 20, "density": DENSITY_MEDIUM},
    # Rural (single search, large radius) - remaining 42 provinces
    {"name": "A Coruña", "lat": 43.3623, "lng": -8.4115, "radius_km": 40, "density": DENSITY_RURAL},
    {"name": "Álava", "lat": 42.8469, "lng": -2.6727, "radius_km": 30, "density": DENSITY_RURAL},
    {"name": "Albacete", "lat": 38.9942, "lng": -1.8585, "radius_km": 40, "density": DENSITY_RURAL},
    {"name": "Almería", "lat": 36.8340, "lng": -2.4637, "radius_km": 35, "density": DENSITY_RURAL},
    {"name": "Asturias", "lat": 43.3614, "lng": -5.8593, "radius_km": 40, "density": DENSITY_RURAL},
    {"name": "Ávila", "lat": 40.6565, "lng": -4.6819, "radius_km": 40, "density": DENSITY_RURAL},
    {"name": "Badajoz", "lat": 38.8794, "lng": -6.9707, "radius_km": 50, "density": DENSITY_RURAL},
    {"name": "Burgos", "lat": 42.3440, "lng": -3.6969, "radius_km": 45, "density": DENSITY_RURAL},
    {"name": "Cáceres", "lat": 39.4753, "lng": -6.3724, "radius_km": 50, "density": DENSITY_RURAL},
    {"name": "Cádiz", "lat": 36.5271, "lng": -6.2886, "radius_km": 35, "density": DENSITY_RURAL},
    {"name": "Cantabria", "lat": 43.1828, "lng": -3.9878, "radius_km": 35, "density": DENSITY_RURAL},
    {"name": "Castellón", "lat": 39.9864, "lng": -0.0513, "radius_km": 35, "density": DENSITY_RURAL},
    {"name": "Ciudad Real", "lat": 38.9848, "lng": -3.9274, "radius_km": 45, "density": DENSITY_RURAL},
    {"name": "Córdoba", "lat": 37.8882, "lng": -4.7794, "radius_km": 40, "density": DENSITY_RURAL},
    {"name": "Cuenca", "lat": 40.0704, "lng": -2.1374, "radius_km": 45, "density": DENSITY_RURAL},
    {"name": "Girona", "lat": 41.9794, "lng": 2.8214, "radius_km": 35, "density": DENSITY_RURAL},
    {"name": "Granada", "lat": 37.1773, "lng": -3.5986, "radius_km": 40, "density": DENSITY_RURAL},
    {"name": "Guadalajara", "lat": 40.6330, "lng": -3.1674, "radius_km": 40, "density": DENSITY_RURAL},
    {"name": "Guipúzcoa", "lat": 43.3128, "lng": -1.9781, "radius_km": 25, "density": DENSITY_RURAL},
    {"name": "Huelva", "lat": 37.2614, "lng": -6.9447, "radius_km": 40, "density": DENSITY_RURAL},
    {"name": "Huesca", "lat": 42.1401, "lng": -0.4089, "radius_km": 45, "density": DENSITY_RURAL},
    {"name": "Jaén", "lat": 37.7796, "lng": -3.7849, "radius_km": 40, "density": DENSITY_RURAL},
    {"name": "La Rioja", "lat": 42.2871, "lng": -2.5396, "radius_km": 30, "density": DENSITY_RURAL},
    {"name": "Las Palmas", "lat": 28.1235, "lng": -15.4363, "radius_km": 30, "density": DENSITY_RURAL},
    {"name": "León", "lat": 42.5987, "lng": -5.5671, "radius_km": 45, "density": DENSITY_RURAL},
    {"name": "Lleida", "lat": 41.6176, "lng": 0.6200, "radius_km": 45, "density": DENSITY_RURAL},
    {"name": "Lugo", "lat": 43.0097, "lng": -7.5568, "radius_km": 45, "density": DENSITY_RURAL},
    {"name": "Navarra", "lat": 42.6954, "lng": -1.6761, "radius_km": 35, "density": DENSITY_RURAL},
    {"name": "Ourense", "lat": 42.3400, "lng": -7.8648, "radius_km": 40, "density": DENSITY_RURAL},
    {"name": "Palencia", "lat": 42.0096, "lng": -4.5288, "radius_km": 40, "density": DENSITY_RURAL},
    {"name": "Pontevedra", "lat": 42.4310, "lng": -8.6445, "radius_km": 35, "density": DENSITY_RURAL},
    {"name": "Salamanca", "lat": 40.9701, "lng": -5.6635, "radius_km": 40, "density": DENSITY_RURAL},
    {"name": "Santa Cruz de Tenerife", "lat": 28.4636, "lng": -16.2518, "radius_km": 30, "density": DENSITY_RURAL},
    {"name": "Segovia", "lat": 40.9429, "lng": -4.1088, "radius_km": 35, "density": DENSITY_RURAL},
    {"name": "Soria", "lat": 41.7636, "lng": -2.4649, "radius_km": 40, "density": DENSITY_RURAL},
    {"name": "Tarragona", "lat": 41.1189, "lng": 1.2445, "radius_km": 35, "density": DENSITY_RURAL},
    {"name": "Teruel", "lat": 40.3456, "lng": -1.1065, "radius_km": 45, "density": DENSITY_RURAL},
    {"name": "Toledo", "lat": 39.8628, "lng": -4.0273, "radius_km": 45, "density": DENSITY_RURAL},
    {"name": "Valladolid", "lat": 41.6523, "lng": -4.7245, "radius_km": 35, "density": DENSITY_RURAL},
    {"name": "Vizcaya", "lat": 43.2630, "lng": -2.9350, "radius_km": 25, "density": DENSITY_RURAL},
    {"name": "Zamora", "lat": 41.5034, "lng": -5.7468, "radius_km": 40, "density": DENSITY_RURAL},
]
