import csv
import io
from decimal import Decimal
from ..models import RawRecord, NormalizedEmissionRecord
from ..utils.normalization import normalize_date, detect_suspicious_values
from ..utils.emission_factors import calculate_emissions


AIRPORT_DISTANCES = {
    ('JFK', 'LAX'): 3983, ('LAX', 'JFK'): 3983,
    ('LHR', 'JFK'): 5541, ('JFK', 'LHR'): 5541,
    ('SFO', 'NRT'): 8280, ('NRT', 'SFO'): 8280,
    ('LAX', 'SFO'): 543,  ('SFO', 'LAX'): 543,
}


def read_csv_file(file_path):
    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(file_path, encoding='latin-1') as f:
            content = f.read()
    reader = csv.DictReader(io.StringIO(content))
    return [dict(row) for row in reader]


def estimate_flight_distance(origin, destination):
    key = (origin.upper().strip(), destination.upper().strip())
    return AIRPORT_DISTANCES.get(key, 1000)


def classify_flight_type(distance_km):
    if distance_km < 1500:
        return 'flight_short'
    elif distance_km < 4000:
        return 'flight_medium'
    return 'flight_long'


def process_travel_data(data_source, file_path):
    """
    Process corporate travel CSV from Concur/Navan style exports.
    Uses stdlib csv — no pandas dependency.
    """
    rows = read_csv_file(file_path)

    if not rows:
        raise ValueError("CSV file is empty")

    required = ['Transport_Type', 'Travel_Date']
    for col in required:
        if col not in rows[0]:
            raise ValueError(f"Missing required column: {col}")

    data_source.total_rows = len(rows)
    data_source.save()

    processed_count = 0
    failed_count = 0

    for row in rows:
        raw_record = None
        try:
            raw_record = RawRecord.objects.create(
                source=data_source,
                raw_payload=row,
                validation_status='valid'
            )

            transport_type = row.get('Transport_Type', '').lower().strip()
            activity_date = normalize_date(row.get('Travel_Date', ''))

            dist_raw = row.get('Distance_km', '').strip()
            nights_raw = row.get('Hotel_Nights', '').strip()

            if 'flight' in transport_type:
                if dist_raw:
                    distance = float(dist_raw)
                else:
                    origin = row.get('Origin', '')
                    destination = row.get('Destination', '')
                    distance = estimate_flight_distance(origin, destination)
                activity_type = classify_flight_type(distance)
                category = 'Business Travel - Flight'
                quantity = Decimal(str(distance))
                normalized_unit = 'km'

            elif 'hotel' in transport_type:
                nights = float(nights_raw) if nights_raw else 1.0
                activity_type = 'hotel_night'
                category = 'Business Travel - Accommodation'
                quantity = Decimal(str(nights))
                normalized_unit = 'nights'

            elif 'taxi' in transport_type or 'cab' in transport_type:
                distance = float(dist_raw) if dist_raw else 10.0
                activity_type = 'taxi'
                category = 'Business Travel - Ground Transport'
                quantity = Decimal(str(distance))
                normalized_unit = 'km'

            elif 'car' in transport_type or 'rental' in transport_type:
                distance = float(dist_raw) if dist_raw else 50.0
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
                    'traveler_name': row.get('Traveler_Name', ''),
                    'origin': row.get('Origin', ''),
                    'destination': row.get('Destination', ''),
                    'travel_class': row.get('Travel_Class', ''),
                }
            )
            processed_count += 1

        except Exception as e:
            failed_count += 1
            if raw_record:
                raw_record.validation_status = 'invalid'
                raw_record.validation_errors = [str(e)]
                raw_record.save()

    data_source.processed_rows = processed_count
    data_source.failed_rows = failed_count
    data_source.processing_status = 'completed'
    data_source.save()

    return processed_count, failed_count
