import pandas as pd
from decimal import Decimal
from ..models import RawRecord, NormalizedEmissionRecord
from ..utils.normalization import normalize_unit, normalize_date, detect_suspicious_values
from ..utils.emission_factors import calculate_emissions, classify_scope


AIRPORT_DISTANCES = {
    ('JFK', 'LAX'): 3983,
    ('LAX', 'JFK'): 3983,
    ('LHR', 'JFK'): 5541,
    ('JFK', 'LHR'): 5541,
    ('SFO', 'NRT'): 8280,
    ('NRT', 'SFO'): 8280,
}


def estimate_flight_distance(origin, destination):
    """Estimate flight distance between airports."""
    key = (origin.upper(), destination.upper())
    if key in AIRPORT_DISTANCES:
        return AIRPORT_DISTANCES[key]
    
    return 1000


def classify_flight_type(distance_km):
    """Classify flight as short/medium/long haul."""
    if distance_km < 1500:
        return 'flight_short'
    elif distance_km < 4000:
        return 'flight_medium'
    else:
        return 'flight_long'


def process_travel_data(data_source, file_path):
    """
    Process corporate travel data from platforms like Concur/Navan.
    
    Expected columns:
    - Traveler_Name
    - Travel_Date
    - Transport_Type (Flight/Hotel/Taxi/Rail/Car Rental)
    - Origin (for flights)
    - Destination (for flights)
    - Distance_km (optional)
    - Travel_Class (Economy/Business/First)
    - Hotel_Nights (for hotels)
    """
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding='latin-1')
    
    required_columns = ['Transport_Type', 'Travel_Date']
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    data_source.total_rows = len(df)
    data_source.save()
    
    processed_count = 0
    failed_count = 0
    
    for idx, row in df.iterrows():
        try:
            raw_payload = row.to_dict()
            
            raw_record = RawRecord.objects.create(
                source=data_source,
                raw_payload=raw_payload,
                validation_status='valid'
            )
            
            transport_type = str(row['Transport_Type']).lower()
            activity_date = normalize_date(row['Travel_Date'])
            
            if 'flight' in transport_type:
                if pd.notna(row.get('Distance_km')):
                    distance = float(row['Distance_km'])
                else:
                    origin = str(row.get('Origin', ''))
                    destination = str(row.get('Destination', ''))
                    distance = estimate_flight_distance(origin, destination)
                
                flight_type = classify_flight_type(distance)
                activity_type = flight_type
                category = 'Business Travel - Flight'
                quantity = Decimal(str(distance))
                normalized_unit = 'km'
                
            elif 'hotel' in transport_type:
                nights = float(row.get('Hotel_Nights', 1))
                activity_type = 'hotel_night'
                category = 'Business Travel - Accommodation'
                quantity = Decimal(str(nights))
                normalized_unit = 'nights'
                
            elif 'taxi' in transport_type or 'cab' in transport_type:
                distance = float(row.get('Distance_km', 10))
                activity_type = 'taxi'
                category = 'Business Travel - Ground Transport'
                quantity = Decimal(str(distance))
                normalized_unit = 'km'
                
            elif 'car' in transport_type or 'rental' in transport_type:
                distance = float(row.get('Distance_km', 50))
                activity_type = 'rental_car'
                category = 'Business Travel - Ground Transport'
                quantity = Decimal(str(distance))
                normalized_unit = 'km'
            
            else:
                activity_type = 'other_travel'
                category = 'Business Travel - Other'
                quantity = Decimal('1')
                normalized_unit = 'trip'
            
            emission_value, emission_factor, emission_unit = calculate_emissions(
                quantity, activity_type
            )
            
            record_data = {
                'quantity': quantity,
                'normalized_unit': normalized_unit,
                'activity_date': activity_date,
            }
            
            is_suspicious, suspicious_reasons = detect_suspicious_values(record_data)
            
            NormalizedEmissionRecord.objects.create(
                company=data_source.company,
                source=data_source,
                raw_record=raw_record,
                scope='scope_3',
                category=category,
                activity_type=activity_type,
                activity_date=activity_date,
                quantity=quantity,
                normalized_unit=normalized_unit,
                original_unit=normalized_unit,
                emission_factor=emission_factor,
                emission_value=emission_value,
                emission_unit=emission_unit,
                suspicious_flag=is_suspicious,
                suspicious_reason='; '.join(suspicious_reasons) if is_suspicious else '',
                status='flagged' if is_suspicious else 'pending',
                metadata={
                    'traveler_name': str(row.get('Traveler_Name', '')),
                    'origin': str(row.get('Origin', '')),
                    'destination': str(row.get('Destination', '')),
                    'travel_class': str(row.get('Travel_Class', '')),
                }
            )
            
            processed_count += 1
            
        except Exception as e:
            failed_count += 1
            raw_record.validation_status = 'invalid'
            raw_record.validation_errors = [str(e)]
            raw_record.save()
    
    data_source.processed_rows = processed_count
    data_source.failed_rows = failed_count
    data_source.processing_status = 'completed'
    data_source.save()
    
    return processed_count, failed_count
