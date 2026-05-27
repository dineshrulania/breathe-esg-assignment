import csv
import io
from decimal import Decimal
from ..models import RawRecord, NormalizedEmissionRecord
from ..utils.normalization import normalize_unit, normalize_date, detect_suspicious_values
from ..utils.emission_factors import calculate_emissions


def read_csv_file(file_path):
    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(file_path, encoding='latin-1') as f:
            content = f.read()
    reader = csv.DictReader(io.StringIO(content))
    return [dict(row) for row in reader]


def process_utility_data(data_source, file_path):
    """
    Process utility electricity CSV portal exports.
    Uses stdlib csv — no pandas dependency.
    """
    rows = read_csv_file(file_path)

    if not rows:
        raise ValueError("CSV file is empty")

    required = ['Meter_ID', 'Total_kWh', 'Billing_Period_Start']
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

            quantity = float(row.get('Total_kWh', 0) or 0)
            normalized_qty, normalized_unit = normalize_unit(quantity, 'kWh', 'energy')
            activity_date = normalize_date(row.get('Billing_Period_Start', ''))

            emission_value, emission_factor, emission_unit = calculate_emissions(
                normalized_qty, 'electricity'
            )

            record_data = {
                'quantity': normalized_qty,
                'normalized_unit': normalized_unit,
                'activity_date': activity_date,
            }
            is_suspicious, suspicious_reasons = detect_suspicious_values(record_data)

            NormalizedEmissionRecord.objects.create(
                company=data_source.company,
                source=data_source,
                raw_record=raw_record,
                scope='scope_2',
                category='Electricity',
                activity_type='electricity',
                activity_date=activity_date,
                quantity=normalized_qty,
                normalized_unit=normalized_unit,
                original_unit='kWh',
                emission_factor=emission_factor,
                emission_value=emission_value,
                emission_unit=emission_unit,
                facility=row.get('Facility_Name', ''),
                suspicious_flag=is_suspicious,
                suspicious_reason='; '.join(suspicious_reasons) if is_suspicious else '',
                status='flagged' if is_suspicious else 'pending',
                metadata={
                    'meter_id': row.get('Meter_ID', ''),
                    'billing_period_end': row.get('Billing_Period_End', ''),
                    'tariff_type': row.get('Tariff_Type', ''),
                    'peak_usage': row.get('Peak_Usage_kWh', ''),
                    'off_peak_usage': row.get('Off_Peak_Usage_kWh', ''),
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
