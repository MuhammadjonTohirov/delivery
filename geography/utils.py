import math
import hashlib
from decimal import Decimal
from typing import Tuple, List, Dict, Optional


def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate the Haversine distance between two points on the earth.
    Returns distance in kilometers.
    
    Args:
        lat1, lng1: Latitude and longitude of first point
        lat2, lng2: Latitude and longitude of second point
    
    Returns:
        Distance in kilometers
    """
    # Convert decimal degrees to radians
    lat1, lng1, lat2, lng2 = map(math.radians, [float(lat1), float(lng1), float(lat2), float(lng2)])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Radius of earth in kilometers
    
    return c * r


def calculate_delivery_fee(distance_km: float, base_fee: Decimal = Decimal('2.50'), per_km_fee: Decimal = Decimal('0.50')) -> Decimal:
    """
    Calculate delivery fee based on distance.
    
    Args:
        distance_km: Distance in kilometers
        base_fee: Base delivery fee
        per_km_fee: Fee per kilometer
    
    Returns:
        Total delivery fee
    """
    return base_fee + (per_km_fee * Decimal(str(distance_km)))


def estimate_delivery_time(distance_km: float, base_time_minutes: int = 15, speed_km_per_minute: float = 0.5) -> int:
    """
    Estimate delivery time in minutes based on distance.
    
    Args:
        distance_km: Distance in kilometers
        base_time_minutes: Base preparation/handling time
        speed_km_per_minute: Average speed in km per minute
    
    Returns:
        Estimated delivery time in minutes
    """
    travel_time = distance_km / speed_km_per_minute
    return int(base_time_minutes + travel_time)


def normalize_address(address: str) -> str:
    """
    Normalize address string for consistent geocoding cache lookups.
    
    Args:
        address: Raw address string
    
    Returns:
        Normalized address string
    """
    # Convert to lowercase and remove extra whitespace
    normalized = ' '.join(address.lower().strip().split())
    
    # Basic normalization - could be enhanced with more sophisticated logic
    replacements = {
        'street': 'st',
        'avenue': 'ave',
        'boulevard': 'blvd',
        'drive': 'dr',
        'court': 'ct',
        'place': 'pl',
        'apartment': 'apt',
        'suite': 'ste',
    }
    
    for full, abbrev in replacements.items():
        normalized = normalized.replace(f' {full} ', f' {abbrev} ')
        normalized = normalized.replace(f' {full}', f' {abbrev}')
    
    return normalized


def hash_address(address: str) -> str:
    """
    Create a hash of an address for caching purposes.
    
    Args:
        address: Address string to hash
    
    Returns:
        SHA-256 hash of the normalized address
    """
    normalized = normalize_address(address)
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def find_optimal_route(waypoints: List[Dict[str, float]]) -> List[Dict[str, float]]:
    """
    Find optimal route through waypoints using nearest neighbor algorithm.
    This is a simplified implementation - production would use more sophisticated routing.
    
    Args:
        waypoints: List of {'lat': float, 'lng': float} dictionaries
    
    Returns:
        Optimized list of waypoints
    """
    if len(waypoints) <= 2:
        return waypoints
    
    # Start with the first waypoint
    route = [waypoints[0]]
    remaining = waypoints[1:]
    current = waypoints[0]
    
    while remaining:
        # Find nearest unvisited waypoint
        nearest_idx = 0
        nearest_distance = float('inf')
        
        for i, waypoint in enumerate(remaining):
            distance = calculate_distance(
                current['lat'], current['lng'],
                waypoint['lat'], waypoint['lng']
            )
            if distance < nearest_distance:
                nearest_distance = distance
                nearest_idx = i
        
        # Add nearest waypoint to route
        nearest = remaining.pop(nearest_idx)
        route.append(nearest)
        current = nearest
    
    return route


def calculate_route_distance(waypoints: List[Dict[str, float]]) -> float:
    """
    Calculate total distance for a route through waypoints.
    
    Args:
        waypoints: List of {'lat': float, 'lng': float} dictionaries
    
    Returns:
        Total distance in kilometers
    """
    if len(waypoints) < 2:
        return 0.0
    
    total_distance = 0.0
    for i in range(len(waypoints) - 1):
        distance = calculate_distance(
            waypoints[i]['lat'], waypoints[i]['lng'],
            waypoints[i + 1]['lat'], waypoints[i + 1]['lng']
        )
        total_distance += distance
    
    return total_distance


def is_point_in_radius(center_lat: float, center_lng: float, point_lat: float, point_lng: float, radius_km: float) -> bool:
    """
    Check if a point is within a given radius of a center point.
    
    Args:
        center_lat, center_lng: Center point coordinates
        point_lat, point_lng: Point to check coordinates
        radius_km: Radius in kilometers
    
    Returns:
        True if point is within radius, False otherwise
    """
    distance = calculate_distance(center_lat, center_lng, point_lat, point_lng)
    return distance <= radius_km


def get_bounding_box(center_lat: float, center_lng: float, radius_km: float) -> Dict[str, float]:
    """
    Calculate bounding box coordinates for a circular area.
    Useful for database queries to pre-filter locations.
    
    Args:
        center_lat, center_lng: Center point coordinates
        radius_km: Radius in kilometers
    
    Returns:
        Dictionary with min_lat, max_lat, min_lng, max_lng
    """
    # Approximate degrees per kilometer
    lat_deg_per_km = 1 / 111.0
    lng_deg_per_km = 1 / (111.0 * math.cos(math.radians(center_lat)))
    
    lat_offset = radius_km * lat_deg_per_km
    lng_offset = radius_km * lng_deg_per_km
    
    return {
        'min_lat': center_lat - lat_offset,
        'max_lat': center_lat + lat_offset,
        'min_lng': center_lng - lng_offset,
        'max_lng': center_lng + lng_offset,
    }


def format_address_components(address_data: Dict) -> Dict[str, str]:
    """
    Format address components from geocoding API response.
    
    Args:
        address_data: Raw address data from geocoding API
    
    Returns:
        Formatted address components
    """
    # This would be customized based on the geocoding provider
    # Example for Google Maps API format
    components = {
        'street_number': '',
        'route': '',
        'city': '',
        'state': '',
        'country': '',
        'postal_code': '',
    }
    
    # Extract components based on API response format
    # Implementation would depend on specific geocoding service
    
    return components


def validate_coordinates(latitude: float, longitude: float) -> bool:
    """
    Validate that coordinates are within valid ranges.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
    
    Returns:
        True if coordinates are valid, False otherwise
    """
    return -90 <= latitude <= 90 and -180 <= longitude <= 180


def calculate_midpoint(lat1: float, lng1: float, lat2: float, lng2: float) -> Tuple[float, float]:
    """
    Calculate the midpoint between two geographic coordinates.
    
    Args:
        lat1, lng1: First point coordinates
        lat2, lng2: Second point coordinates
    
    Returns:
        Tuple of (midpoint_lat, midpoint_lng)
    """
    # Convert to radians
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    
    # Calculate midpoint
    dlng = lng2 - lng1
    bx = math.cos(lat2) * math.cos(dlng)
    by = math.cos(lat2) * math.sin(dlng)
    
    mid_lat = math.atan2(
        math.sin(lat1) + math.sin(lat2),
        math.sqrt((math.cos(lat1) + bx) * (math.cos(lat1) + bx) + by * by)
    )
    mid_lng = lng1 + math.atan2(by, math.cos(lat1) + bx)
    
    # Convert back to degrees
    return math.degrees(mid_lat), math.degrees(mid_lng)


class RouteOptimizer:
    """
    Advanced route optimization utilities
    """
    
    @staticmethod
    def optimize_delivery_sequence(pickup_location: Dict[str, float], delivery_locations: List[Dict[str, float]]) -> List[Dict[str, float]]:
        """
        Optimize the sequence of deliveries starting from a pickup location.
        
        Args:
            pickup_location: {'lat': float, 'lng': float} of pickup point
            delivery_locations: List of delivery locations
        
        Returns:
            Optimized sequence starting from pickup location
        """
        if not delivery_locations:
            return [pickup_location]
        
        # Start from pickup location
        route = [pickup_location]
        remaining = delivery_locations.copy()
        current = pickup_location
        
        # Use nearest neighbor algorithm
        while remaining:
            nearest_idx = 0
            nearest_distance = float('inf')
            
            for i, location in enumerate(remaining):
                distance = calculate_distance(
                    current['lat'], current['lng'],
                    location['lat'], location['lng']
                )
                if distance < nearest_distance:
                    nearest_distance = distance
                    nearest_idx = i
            
            nearest = remaining.pop(nearest_idx)
            route.append(nearest)
            current = nearest
        
        return route
    
    @staticmethod
    def calculate_route_efficiency(route: List[Dict[str, float]]) -> Dict[str, float]:
        """
        Calculate efficiency metrics for a route.
        
        Args:
            route: List of waypoints in order
        
        Returns:
            Dictionary with efficiency metrics
        """
        if len(route) < 2:
            return {'total_distance': 0.0, 'efficiency_score': 1.0}
        
        total_distance = calculate_route_distance(route)
        
        # Calculate theoretical minimum distance (direct distances)
        direct_distances = []
        for i in range(len(route) - 1):
            distance = calculate_distance(
                route[i]['lat'], route[i]['lng'],
                route[i + 1]['lat'], route[i + 1]['lng']
            )
            direct_distances.append(distance)
        
        theoretical_minimum = sum(direct_distances)
        efficiency_score = theoretical_minimum / total_distance if total_distance > 0 else 1.0
        
        return {
            'total_distance': total_distance,
            'theoretical_minimum': theoretical_minimum,
            'efficiency_score': efficiency_score,
            'waypoint_count': len(route),
        }
