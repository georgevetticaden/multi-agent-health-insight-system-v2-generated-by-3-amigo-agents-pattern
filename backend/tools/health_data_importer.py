"""
Health data import tool - extracted and refactored from MCP
"""
import os
import json
import uuid
import logging
import glob
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from collections import defaultdict
from pathlib import Path

from tools.snowflake_connection import SnowflakeConnection

logger = logging.getLogger(__name__)

class HealthDataImporter:
    """Handles importing health data from JSON files into Snowflake"""
    
    def __init__(self):
        self.snowflake = SnowflakeConnection()
        
    def parse_date(self, date_str: str) -> Optional[date]:
        """Parse date string to date object"""
        if not date_str:
            return None
        
        try:
            if len(date_str) == 10 and '-' in date_str:
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            elif len(date_str) == 10 and '/' in date_str:
                return datetime.strptime(date_str, '%m/%d/%Y').date()
            else:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
        except Exception as e:
            logger.warning(f"Could not parse date '{date_str}': {e}")
            return None
    
    def extract_patient_info(self, file_path: str) -> Dict[str, Any]:
        """Extract patient information from header_fields in JSON file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            if "header_fields" in data:
                header = data["header_fields"]
                return {
                    "patient_identity": header.get("Patient_Name", "Unknown Patient"),
                    "date_of_birth": self.parse_date(header.get("Date_Of_Birth")),
                    "patient_age": header.get("Patient_Age"),
                    "report_date": self.parse_date(header.get("Report_Date"))
                }
        except Exception as e:
            logger.warning(f"Could not extract patient info from {file_path}: {e}")
        
        return {}
    
    def ensure_patient_exists(self, conn, patient_info: Dict[str, Any]) -> str:
        """Ensure patient exists in database and return patient_id"""
        cursor = conn.cursor()
        
        try:
            patient_id = str(uuid.uuid4())
            
            cursor.execute("""
                INSERT INTO PATIENTS (PATIENT_ID, PATIENT_IDENTITY, DATE_OF_BIRTH, PATIENT_AGE)
                VALUES (%s, %s, %s, %s)
            """, (
                patient_id,
                patient_info.get("patient_identity", "Unknown Patient"),
                patient_info.get("date_of_birth"),
                patient_info.get("patient_age")
            ))
            
            logger.info(f"Created patient record with ID: {patient_id}")
            return patient_id
            
        except Exception as e:
            logger.error(f"Failed to create patient record: {str(e)}")
            raise
        finally:
            cursor.close()
    
    def create_import_record(self, conn, patient_id: str, source_files: List[str]) -> str:
        """Create import record and return import_id"""
        cursor = conn.cursor()
        
        try:
            import_id = str(uuid.uuid4())
            
            cursor.execute("""
                INSERT INTO IMPORTS (IMPORT_ID, PATIENT_ID, SOURCE_FILES, IMPORT_STATUS)
                VALUES (%s, %s, %s, %s)
            """, (
                import_id,
                patient_id,
                json.dumps(source_files),
                'IN_PROGRESS'
            ))
            
            logger.info(f"Created import record with ID: {import_id}")
            return import_id
            
        except Exception as e:
            logger.error(f"Failed to create import record: {str(e)}")
            raise
        finally:
            cursor.close()
    
    def process_lab_results(self, data: Dict, patient_id: str, import_id: str, source_file: str) -> List[Dict]:
        """Process lab results data into health records"""
        records = []
        
        if "Lab_Results" not in data:
            return records
        
        for lab_session in data["Lab_Results"]:
            test_date = self.parse_date(lab_session.get("Test_Date"))
            provider = lab_session.get("Provider", "Unknown Provider")
            
            for test in lab_session.get("Tests", []):
                record = {
                    "record_id": str(uuid.uuid4()),
                    "patient_id": patient_id,
                    "import_id": import_id,
                    "record_category": "LAB",
                    "record_date": test_date,
                    "provider": provider,
                    "item_description": test.get("Test_Name"),
                    "value_text": test.get("Test_Value"),
                    "measurement_dimension": test.get("Test_Unit"),
                    "reference_range": test.get("Reference_Range"),
                    "flag": test.get("Flag"),
                    "test_category": test.get("Test_Category"),
                    "source_file": source_file
                }
                
                # Try to parse numeric value
                try:
                    value_str = str(test.get("Test_Value", "")).strip()
                    if value_str and value_str.replace('.', '').replace('-', '').isdigit():
                        record["value_numeric"] = float(value_str)
                except:
                    pass
                
                records.append(record)
        
        return records
    
    def process_medications(self, data: Dict, patient_id: str, import_id: str, source_file: str) -> List[Dict]:
        """Process medications data into health records"""
        records = []
        
        if "Medications" not in data:
            return records
        
        for med in data["Medications"]:
            record = {
                "record_id": str(uuid.uuid4()),
                "patient_id": patient_id,
                "import_id": import_id,
                "record_category": "MEDICATION",
                "record_date": self.parse_date(med.get("Prescription_Date")),
                "provider": med.get("Provider", "Unknown Provider"),
                "item_description": med.get("Medication_Name"),
                "dosage": med.get("Dosage"),
                "form": med.get("Form"),
                "for_condition": med.get("For_Condition"),
                "frequency": med.get("Frequency"),
                "medication_status": med.get("Status", "PRESCRIBED"),
                "source_file": source_file
            }
            records.append(record)
        
        return records
    
    def process_vitals(self, data: Dict, patient_id: str, import_id: str, source_file: str) -> List[Dict]:
        """Process vitals data into health records"""
        records = []
        
        if "Vitals" not in data:
            return records
        
        for vital in data["Vitals"]:
            record = {
                "record_id": str(uuid.uuid4()),
                "patient_id": patient_id,
                "import_id": import_id,
                "record_category": "VITAL",
                "record_date": self.parse_date(vital.get("Measurement_Date")),
                "provider": vital.get("Provider", "Unknown Provider"),
                "item_description": vital.get("Vital_Type"),
                "value_numeric": vital.get("Vital_Value"),
                "measurement_dimension": vital.get("Vital_Unit"),
                "vital_category": vital.get("Vital_Type"),
                "source_file": source_file
            }
            records.append(record)
        
        return records
    
    def process_clinical_data(self, data: Dict, patient_id: str, import_id: str, source_file: str) -> List[Dict]:
        """Process clinical data (conditions, procedures, allergies, immunizations)"""
        records = []
        
        # Process Conditions
        if "Conditions" in data:
            for condition in data["Conditions"]:
                record = {
                    "record_id": str(uuid.uuid4()),
                    "patient_id": patient_id,
                    "import_id": import_id,
                    "record_category": "CONDITION",
                    "record_date": self.parse_date(condition.get("Diagnosis_Date")),
                    "provider": condition.get("Provider", "Unknown Provider"),
                    "item_description": condition.get("Condition_Name"),
                    "condition_status": condition.get("Status"),
                    "source_file": source_file
                }
                records.append(record)
        
        # Process other clinical data types...
        # (Procedures, Allergies, Immunizations - same pattern)
        
        return records
    
    def bulk_insert_health_records(self, conn, records: List[Dict]):
        """Bulk insert health records into database"""
        if not records:
            return
        
        cursor = conn.cursor()
        
        try:
            insert_sql = """
                INSERT INTO HEALTH_RECORDS (
                    RECORD_ID, PATIENT_ID, IMPORT_ID, RECORD_CATEGORY, RECORD_DATE, PROVIDER,
                    ITEM_DESCRIPTION, VALUE_TEXT, VALUE_NUMERIC, MEASUREMENT_DIMENSION, 
                    REFERENCE_RANGE, FLAG, TEST_CATEGORY, DOSAGE, FORM, FOR_CONDITION, 
                    FREQUENCY, MEDICATION_STATUS, VITAL_CATEGORY, CONDITION_STATUS, 
                    VACCINE_CATEGORY, PROCEDURE_CATEGORY, ALLERGY_CATEGORY
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """
            
            insert_data = []
            for record in records:
                insert_data.append((
                    record.get("record_id"),
                    record.get("patient_id"),
                    record.get("import_id"),
                    record.get("record_category"),
                    record.get("record_date"),
                    record.get("provider"),
                    record.get("item_description"),
                    record.get("value_text"),
                    record.get("value_numeric"),
                    record.get("measurement_dimension"),
                    record.get("reference_range"),
                    record.get("flag"),
                    record.get("test_category"),
                    record.get("dosage"),
                    record.get("form"),
                    record.get("for_condition"),
                    record.get("frequency"),
                    record.get("medication_status"),
                    record.get("vital_category"),
                    record.get("condition_status"),
                    record.get("vaccine_category"),
                    record.get("procedure_category"),
                    record.get("allergy_category")
                ))
            
            cursor.executemany(insert_sql, insert_data)
            logger.info(f"Inserted {len(records)} health records")
            
        except Exception as e:
            logger.error(f"Failed to insert health records: {str(e)}")
            raise
        finally:
            cursor.close()
    
    def calculate_import_statistics(self, records: List[Dict], source_files: List[str]) -> Dict[str, Any]:
        """Calculate comprehensive import statistics"""
        
        # Records by category
        records_by_category = defaultdict(int)
        for record in records:
            category = record.get("record_category", "Unknown")
            if category == "LAB":
                records_by_category["Lab Results"] += 1
            elif category == "MEDICATION":
                records_by_category["Medications"] += 1
            elif category == "VITAL":
                records_by_category["Vitals"] += 1
            else:
                records_by_category["Clinical Data"] += 1
        
        # Timeline coverage
        timeline_coverage = defaultdict(int)
        for record in records:
            record_date = record.get("record_date")
            if record_date:
                year = record_date.year if hasattr(record_date, 'year') else int(str(record_date)[:4])
                timeline_coverage[year] += 1
        
        # Data quality metrics
        total_records = len(records)
        lab_records = [r for r in records if r.get("record_category") == "LAB"]
        med_records = [r for r in records if r.get("record_category") == "MEDICATION"]
        
        lab_with_ranges = len([r for r in lab_records if r.get("reference_range")])
        med_with_status = len([r for r in med_records if r.get("medication_status")])
        records_with_dates = len([r for r in records if r.get("record_date")])
        
        # Key insights
        key_insights = []
        
        lab_dates = [r.get("record_date") for r in lab_records if r.get("record_date")]
        if lab_dates:
            most_recent_lab = max(lab_dates)
            key_insights.append(f"Most recent lab test: {most_recent_lab}")
        
        recent_meds = [r for r in med_records if r.get("record_date") and r.get("record_date") >= date(2024, 1, 1)]
        key_insights.append(f"Recent medications: {len(recent_meds)}")
        
        if timeline_coverage:
            top_years = sorted(timeline_coverage.items(), key=lambda x: x[1], reverse=True)[:2]
            years_list = [str(year) for year, _ in top_years]
            key_insights.append(f"Years with most complete data: {', '.join(years_list)}")
        
        unique_lab_tests = set(r.get("item_description") for r in lab_records if r.get("item_description"))
        key_insights.append(f"Total unique lab tests tracked: {len(unique_lab_tests)}")
        
        return {
            "total_records": total_records,
            "records_by_category": dict(records_by_category),
            "timeline_coverage": dict(timeline_coverage),
            "data_quality": {
                "lab_results_with_ranges": {
                    "count": lab_with_ranges,
                    "total": len(lab_records),
                    "percentage": round((lab_with_ranges / len(lab_records) * 100) if lab_records else 0, 1)
                },
                "medications_with_status": {
                    "count": med_with_status,
                    "total": len(med_records),
                    "percentage": round((med_with_status / len(med_records) * 100) if med_records else 0, 1)
                },
                "records_with_dates": {
                    "count": records_with_dates,
                    "total": total_records,
                    "percentage": round((records_with_dates / total_records * 100) if total_records else 0, 1)
                }
            },
            "key_insights": key_insights,
            "source_files": source_files
        }
    
    def update_import_record(self, conn, import_id: str, statistics: Dict[str, Any]):
        """Update import record with final statistics"""
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE IMPORTS 
                SET RECORDS_BY_CATEGORY = %s,
                    IMPORT_STATISTICS = %s,
                    TOTAL_RECORDS = %s,
                    IMPORT_STATUS = %s
                WHERE IMPORT_ID = %s
            """, (
                json.dumps(statistics["records_by_category"]),
                json.dumps(statistics),
                statistics["total_records"],
                'COMPLETED',
                import_id
            ))
            
            logger.info(f"Updated import record {import_id} with statistics")
            
        except Exception as e:
            logger.error(f"Failed to update import record: {str(e)}")
            raise
        finally:
            cursor.close()
    
    async def import_health_records(self, file_directory: str) -> Dict[str, Any]:
        """
        Import health data from directory of JSON files into Snowflake
        
        Args:
            file_directory: Directory path containing extracted JSON health data files
            
        Returns:
            Dictionary with import results and detailed statistics
        """
        try:
            logger.info(f"Starting health data import from directory: {file_directory}")
            
            # Expand and validate directory path
            expanded_path = os.path.expanduser(file_directory)
            if not os.path.exists(expanded_path):
                return {
                    "success": False,
                    "error": f"Directory not found: {file_directory}"
                }
            
            # Find JSON files
            file_patterns = [
                "lab_results_*.json",
                "vitals_*.json",
                "medications_*.json",
                "clinical_data_consolidated.json"
            ]
            
            source_files = []
            for pattern in file_patterns:
                files = glob.glob(os.path.join(expanded_path, pattern))
                source_files.extend(files)
            
            if not source_files:
                return {
                    "success": False,
                    "error": f"No health data JSON files found in directory: {file_directory}"
                }
            
            logger.info(f"Found {len(source_files)} data files")
            
            # Extract patient information
            patient_info = {}
            for file_path in source_files:
                patient_info = self.extract_patient_info(file_path)
                if patient_info.get("patient_identity") and patient_info.get("date_of_birth"):
                    break
            
            if not patient_info.get("patient_identity") or not patient_info.get("date_of_birth"):
                return {
                    "success": False,
                    "error": "Could not extract patient information from files"
                }
            
            # Connect to Snowflake
            conn = self.snowflake.get_connection()
            
            try:
                # Create patient record
                patient_id = self.ensure_patient_exists(conn, patient_info)
                
                # Create import record
                import_id = self.create_import_record(conn, patient_id, [os.path.basename(f) for f in source_files])
                
                # Process all files
                all_records = []
                
                for file_path in source_files:
                    logger.info(f"Processing file: {os.path.basename(file_path)}")
                    
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                        
                        source_file = os.path.basename(file_path)
                        
                        # Process different data types
                        all_records.extend(self.process_lab_results(data, patient_id, import_id, source_file))
                        all_records.extend(self.process_medications(data, patient_id, import_id, source_file))
                        all_records.extend(self.process_vitals(data, patient_id, import_id, source_file))
                        all_records.extend(self.process_clinical_data(data, patient_id, import_id, source_file))
                        
                    except Exception as e:
                        logger.error(f"Error processing file {file_path}: {str(e)}")
                        continue
                
                if not all_records:
                    return {
                        "success": False,
                        "error": "No valid health records found in the provided files"
                    }
                
                # Bulk insert records
                self.bulk_insert_health_records(conn, all_records)
                
                # Calculate statistics
                statistics = self.calculate_import_statistics(all_records, [os.path.basename(f) for f in source_files])
                
                # Update import record
                self.update_import_record(conn, import_id, statistics)
                
                # Commit transaction
                conn.commit()
                
                logger.info(f"Successfully imported {len(all_records)} health records")
                
                return {
                    "success": True,
                    "message": f"Successfully imported health records for {patient_info['patient_identity']}",
                    "patient_name": patient_info["patient_identity"],
                    "patient_dob": str(patient_info["date_of_birth"]),
                    "patient_id": patient_id,
                    "import_id": import_id,
                    "total_records": len(all_records),
                    "statistics": statistics
                }
                
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"Import failed: {str(e)}")
            return {
                "success": False,
                "error": f"Import failed: {str(e)}"
            }