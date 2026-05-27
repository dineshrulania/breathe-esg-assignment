import csv
import io
from decimal import Decimal
from ..models import RawRecord, NormalizedEmissionRecord
from ..utils.normalization import normalize_unit, normalize_date, detect_suspicious_values
from ..utils.emission_factors import calculate_emissions, classify_scope


COLUMN_ALIASES = {
    'Werk': 'Plant_Code',
    'Materialnummer': 'Material_Number',
    'Materialbeschreibung': 'Material_Description',
    'Menge': 'Quantity',
    'Einheit': 'Unit',
    'Buchungsdatum': 'Posting_Date',
    'Lieferant': 'Vendor',
    'Belegnummer': 'Document_Number',
}


def read_csv_file(file_path):
    """Read CSV file trying utf-8 then latin-1 encoding."""
    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(file_path, encoding='latin-1') as f:
            content = f.read()
    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)
    return rows


def normalize_columns(rows):
    """Rename German column headers to English equivalents."""
    normalized = []
    for row in rows:
        new_row = {}
        for key, value in row.items():
            mapped = COLUMN_ALIASES.get(key.strip(), key.strip())
            new_row[mapped] = value.strip() if value else ''
        normalized.append(new_row)
    return normalized


def process_sap_data(data_source, file_path):
    """
    Process SAP CSV export containing fuel and procurement data.
    Uses stdlib csv — no pandas dependency.
    """
    rows = read_csv_file(file_path)
    rows = normalize_columns(rows)

    if not rows:
        raise ValueError("CSV file is empty")

    required = ['Quantity', 'Unit', 'Posting_Date']
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

            material_desc = row.get('Material_Description', '').lower()

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

            quantity = float(row.get('Quantity', 0) or 0)
            unit = row.get('Unit', '').strip()

            if unit.lower() in ['l', 'ltr', 'liters', 'litres']:
                normalized_qty, normalized_unit = normalize_unit(quantity, 'liters', 'volume')
            elif unit.lower() in ['kg', 'kilogram']:
                normalized_qty, normalized_unit = normalize_unit(quantity, 'kg', 'mass')
            elif unit.lower() in ['m3', 'cubic_meters']:
                normalized_qty, normalized_unit = normalize_unit(quantity, 'm3', 'volume')
            else:
                normalized_qty = Decimal(str(quantity))
                normalized_unit = unit

            activity_date = normalize_date(row.get('Posting_Date', ''))

            emission_value, emission_factor, emission_unit = calculate_emissions(
                normalized_qty, activity_type
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
                scope=classify_scope(activity_type, 'sap'),
                category=category,
                activity_type=activity_type,
                activity_date=activity_date,
                quantity=normalized_qty,
                normalized_unit=normalized_unit,
                original_unit=unit,
                emission_factor=emission_factor,
                emission_value=emission_value,
                emission_unit=emission_unit,
                location=row.get('Plant_Code', ''),
                vendor=row.get('Vendor', ''),
                suspicious_flag=is_suspicious,
                suspicious_reason='; '.join(suspicious_reasons) if is_suspicious else '',
                status='flagged' if is_suspicious else 'pending',
                metadata={
                    'material_number': row.get('Material_Number', ''),
                    'document_number': row.get('Document_Number', ''),
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
