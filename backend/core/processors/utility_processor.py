import pandas as pd
from decimal import Decimal
from ..models import RawRecord, NormalizedEmissionRecord
from ..utils.normalization import normalize_unit, normalize_date, detect_suspicious_values
from ..utils.emission_factors import calculate_emissions, classify_scope


def process_utility_data(data_source, file_path):
    """
    Process utility electricity data from CSV portal exports.
    
    Expected columns:
    - Meter_ID
    - Facility_Name
    - Billing_Period_Start
    - Billing_Period_End
    - Total_kWh
    - Peak_Usage_kWh (optional)
    - Off_Peak_Usage_kWh (optional)
    - Tariff_Type (optional)
    """
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding='latin-1')
    
    required_columns = ['Meter_ID', 'Total_kWh', 'Billing_Period_Start']
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
            
            quantity = float(row['Total_kWh'])
            normalized_qty, normalized_unit = normalize_unit(quantity, 'kWh', 'energy')
            
            activity_date = normalize_date(row['Billing_Period_Start'])
            
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
                facility=str(row.get('Facility_Name', '')),
                suspicious_flag=is_suspicious,
                suspicious_reason='; '.join(suspicious_reasons) if is_suspicious else '',
                status='flagged' if is_suspicious else 'pending',
                metadata={
                    'meter_id': str(row.get('Meter_ID', '')),
                    'billing_period_end': str(row.get('Billing_Period_End', '')),
                    'tariff_type': str(row.get('Tariff_Type', '')),
                    'peak_usage': str(row.get('Peak_Usage_kWh', '')),
                    'off_peak_usage': str(row.get('Off_Peak_Usage_kWh', '')),
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
