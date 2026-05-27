from decimal import Decimal
from datetime import datetime
from dateutil import parser


UNIT_CONVERSIONS = {
    'energy': {
        'kwh': 1.0,
        'mwh': 1000.0,
        'gwh': 1000000.0,
        'kj': 0.000277778,
        'mj': 0.277778,
        'gj': 277.778,
    },
    'volume': {
        'liters': 1.0,
        'l': 1.0,
        'gallons': 3.78541,
        'gal': 3.78541,
        'kiloliters': 1000.0,
        'kl': 1000.0,
        'm3': 1000.0,
        'cubic_meters': 1000.0,
    },
    'mass': {
        'kg': 1.0,
        'kilograms': 1.0,
        'tonnes': 1000.0,
        't': 1000.0,
        'metric_tons': 1000.0,
        'pounds': 0.453592,
        'lbs': 0.453592,
    },
    'distance': {
        'km': 1.0,
        'kilometers': 1.0,
        'miles': 1.60934,
        'mi': 1.60934,
        'meters': 0.001,
        'm': 0.001,
    }
}


def normalize_unit(value, from_unit, category):
    """
    Convert value from source unit to normalized unit for category.
    Returns (normalized_value, normalized_unit)
    """
    from_unit_lower = from_unit.lower().strip()
    
    if category not in UNIT_CONVERSIONS:
        return Decimal(str(value)), from_unit
    
    conversions = UNIT_CONVERSIONS[category]
    
    if from_unit_lower not in conversions:
        return Decimal(str(value)), from_unit
    
    conversion_factor = Decimal(str(conversions[from_unit_lower]))
    normalized_value = Decimal(str(value)) * conversion_factor
    
    normalized_units = {
        'energy': 'kWh',
        'volume': 'liters',
        'mass': 'kg',
        'distance': 'km'
    }
    
    return normalized_value, normalized_units.get(category, from_unit)


def normalize_date(date_value):
    """
    Parse various date formats into standard datetime.date object.
    """
    if isinstance(date_value, datetime):
        return date_value.date()
    
    if isinstance(date_value, str):
        try:
            return parser.parse(date_value).date()
        except:
            return None
    
    return date_value


def detect_suspicious_values(record_data):
    """
    Detect suspicious or anomalous values in emission records.
    Returns (is_suspicious, reasons)
    """
    reasons = []
    
    quantity = record_data.get('quantity', 0)
    
    if quantity <= 0:
        reasons.append("Quantity is zero or negative")
    
    if quantity > 1000000:
        reasons.append("Unusually high quantity value")
    
    activity_date = record_data.get('activity_date')
    if activity_date:
        if isinstance(activity_date, str):
            activity_date = normalize_date(activity_date)
        
        if activity_date and activity_date > datetime.now().date():
            reasons.append("Activity date is in the future")
    
    if not record_data.get('normalized_unit'):
        reasons.append("Missing unit information")
    
    return len(reasons) > 0, reasons
