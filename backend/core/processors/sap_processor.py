import pandas as pd
from decimal import Decimal
from ..models import RawRecord, NormalizedEmissionRecord
from ..utils.normalization import normalize_unit, normalize_date, detect_suspicious_values
from ..utils.emission_factors import calculate_emissions, classify_scope


def process_sap_data(data_source, file_path):
    """
    Process SAP CSV export containing fuel and procurement data.
    
    Expected columns:
    - Plant_Code / Werk
    - Material_Number / Materialnummer
    - Material_Description / Materialbeschreibung
    - Quantity / Menge
    - Unit / Einheit
    - Posting_Date / Buchungsdatum
    - Vendor / Lieferant
    - Document_Number / Belegnummer
    """
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding='latin-1')
    
    column_mapping = {
        'Werk': 'Plant_Code',
        'Materialnummer': 'Material_Number',
        'Materialbeschreibung': 'Material_Description',
        'Menge': 'Quantity',
        'Einheit': 'Unit',
        'Buchungsdatum': 'Posting_Date',
        'Lieferant': 'Vendor',
        'Belegnummer': 'Document_Number',
    }
    
    df.rename(columns=column_mapping, inplace=True)
    
    required_columns = ['Quantity', 'Unit', 'Posting_Date']
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
            
            material_desc = str(row.get('Material_Description', '')).lower()
            
            if 'diesel' in material_desc:
                activity_type = 'diesel'
                category = 'Fuel'
            elif 'petrol' in material_desc or 'gasoline' in material_desc:
                activity_type = 'petrol'
                category = 'Fuel'
            elif 'gas' in material_desc:
                activity_type = 'natural_gas'
                category = 'Fuel'
            else:
                activity_type = 'procurement'
                category = 'Procurement'
            
            quantity = float(row['Quantity'])
            unit = str(row['Unit'])
            
            if unit.lower() in ['l', 'ltr', 'liters', 'litres']:
                normalized_qty, normalized_unit = normalize_unit(quantity, 'liters', 'volume')
            elif unit.lower() in ['kg', 'kilogram']:
                normalized_qty, normalized_unit = normalize_unit(quantity, 'kg', 'mass')
            else:
                normalized_qty = Decimal(str(quantity))
                normalized_unit = unit
            
            activity_date = normalize_date(row['Posting_Date'])
            
            emission_value, emission_factor, emission_unit = calculate_emissions(
                normalized_qty, activity_type
            )
            
            scope = classify_scope(activity_type, 'sap')
            
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
                scope=scope,
                category=category,
                activity_type=activity_type,
                activity_date=activity_date,
                quantity=normalized_qty,
                normalized_unit=normalized_unit,
                original_unit=unit,
                emission_factor=emission_factor,
                emission_value=emission_value,
                emission_unit=emission_unit,
                location=str(row.get('Plant_Code', '')),
                vendor=str(row.get('Vendor', '')),
                suspicious_flag=is_suspicious,
                suspicious_reason='; '.join(suspicious_reasons) if is_suspicious else '',
                status='flagged' if is_suspicious else 'pending',
                metadata={
                    'material_number': str(row.get('Material_Number', '')),
                    'document_number': str(row.get('Document_Number', '')),
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
