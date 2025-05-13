import math
from decimal import Decimal


def calculate_distance(lat1, lng1, lat2, lng2):
    """
    Calculate the Haversine distance between two points on the earth.
    Returns distance in kilometers.
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


def calculate_delivery_fee(distance_km, base_fee=Decimal('2.50'), per_km_fee=Decimal('0.50')):
    """
    Calculate delivery fee based on distance.
    """
    return base_fee + (per_km_fee * Decimal(distance_km))


def estimated_delivery_time(distance_km, base_time_minutes=15, speed_km_per_minute=0.5):
    """
    Estimate delivery time in minutes based on distance.
    """
    travel_time = distance_km / speed_km_per_minute
    return base_time_minutes + travel_time