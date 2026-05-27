from decimal import Decimal

EMISSION_FACTORS = {
    'diesel': {'factor': 2.68, 'unit': 'kg CO2e/liter', 'scope': 'scope_1'},
    'petrol': {'factor': 2.31, 'unit': 'kg CO2e/liter', 'scope': 'scope_1'},
    'gasoline': {'factor': 2.31, 'unit': 'kg CO2e/liter', 'scope': 'scope_1'},
    'natural_gas': {'factor': 2.03, 'unit': 'kg CO2e/m3', 'scope': 'scope_1'},
    'lpg': {'factor': 1.51, 'unit': 'kg CO2e/liter', 'scope': 'scope_1'},
    
    'electricity': {'factor': 0.385, 'unit': 'kg CO2e/kWh', 'scope': 'scope_2'},
    'grid_electricity': {'factor': 0.385, 'unit': 'kg CO2e/kWh', 'scope': 'scope_2'},
    
    'flight_short': {'factor': 0.158, 'unit': 'kg CO2e/km', 'scope': 'scope_3'},
    'flight_medium': {'factor': 0.109, 'unit': 'kg CO2e/km', 'scope': 'scope_3'},
    'flight_long': {'factor': 0.102, 'unit': 'kg CO2e/km', 'scope': 'scope_3'},
    'hotel_night': {'factor': 30.0, 'unit': 'kg CO2e/night', 'scope': 'scope_3'},
    'taxi': {'factor': 0.21, 'unit': 'kg CO2e/km', 'scope': 'scope_3'},
    'rental_car': {'factor': 0.17, 'unit': 'kg CO2e/km', 'scope': 'scope_3'},
}


def get_emission_factor(activity_type):
    """
    Get emission factor for a given activity type.
    Returns dict with factor, unit, and scope.
    """
    activity_lower = activity_type.lower().replace(' ', '_')
    return EMISSION_FACTORS.get(activity_lower)


def calculate_emissions(quantity, activity_type):
    """
    Calculate CO2e emissions based on quantity and activity type.
    Returns (emission_value, emission_factor, emission_unit)
    """
    factor_data = get_emission_factor(activity_type)
    
    if not factor_data:
        return None, None, 'kg CO2e'
    
    emission_factor = Decimal(str(factor_data['factor']))
    emission_value = Decimal(str(quantity)) * emission_factor
    
    return emission_value, emission_factor, 'kg CO2e'


def classify_scope(activity_type, source_type):
    """
    Classify emission scope based on activity type and source.
    """
    factor_data = get_emission_factor(activity_type)
    
    if factor_data:
        return factor_data['scope']
    
    if source_type == 'sap':
        return 'scope_1'
    elif source_type == 'utility':
        return 'scope_2'
    elif source_type == 'travel':
        return 'scope_3'
    
    return 'scope_3'
