"""
Health query executor - extracted and refactored from MCP
"""
import os
import logging
import traceback
import hashlib
import base64
import jwt
import requests
from datetime import datetime, date, timezone, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from tools.snowflake_connection import SnowflakeConnection

logger = logging.getLogger(__name__)

class HealthQueryExecutor:
    """Handles health data queries using Cortex Analyst"""
    
    def __init__(self):
        self.snowflake = SnowflakeConnection()
        self.semantic_model_file = os.getenv("SNOWFLAKE_SEMANTIC_MODEL_FILE", "health_intelligence_semantic_model.yaml")
        
    def call_cortex_analyst(self, query: str) -> Dict[str, Any]:
        """Call Snowflake Cortex Analyst REST API using JWT authentication"""
        try:
            logger.debug(f"Calling Cortex Analyst with query: {query}")
            
            # Get authentication details
            user = self.snowflake.user
            account = self.snowflake.account
            
            # Load private key
            expanded_path = os.path.expanduser(self.snowflake.private_key_path)
            with open(expanded_path, 'rb') as key_file:
                private_key_data = key_file.read()
            
            p_key = serialization.load_pem_private_key(
                private_key_data,
                password=None,
                backend=default_backend()
            )
            
            # Generate JWT token
            def clean_account_identifier(acct):
                if not '.global' in acct:
                    idx = acct.find('.')
                    if idx > 0:
                        acct = acct[0:idx]
                acct = acct.replace('.', '-')
                return acct.upper()
            
            clean_account = clean_account_identifier(account)
            upper_user = user.upper()
            
            # Calculate public key fingerprint
            public_key_raw = p_key.public_key().public_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            sha256hash = hashlib.sha256()
            sha256hash.update(public_key_raw)
            public_key_fp = 'SHA256:' + base64.b64encode(sha256hash.digest()).decode('utf-8')
            
            # Create JWT
            now = datetime.now(timezone.utc)
            lifetime = timedelta(minutes=59)
            
            payload = {
                "iss": f"{clean_account}.{upper_user}.{public_key_fp}",
                "sub": f"{clean_account}.{upper_user}",
                "iat": int(now.timestamp()),
                "exp": int((now + lifetime).timestamp())
            }
            
            token = jwt.encode(payload, p_key, algorithm="RS256")
            if isinstance(token, bytes):
                token = token.decode('utf-8')
            
            # Call Cortex Analyst API
            base_url = f"https://{account.lower()}.snowflakecomputing.com/api/v2/cortex/analyst/message"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "X-Snowflake-Authorization-Token-Type": "KEYPAIR_JWT",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            # Construct full stage path
            semantic_model_file = f"@{self.snowflake.database}.{self.snowflake.schema}.RAW_DATA/{self.semantic_model_file}"
            
            request_body = {
                "timeout": 60000,
                "messages": [
                    {"role": "user", "content": [{"type": "text", "text": query}]}
                ],
                "semantic_model_file": semantic_model_file
            }
            
            logger.debug(f"Calling Cortex Analyst API: {base_url} with semantic model: {semantic_model_file}")
            
            response = requests.post(base_url, headers=headers, json=request_body)
            
            logger.debug(f"Response status: {response.status_code}")
            if response.status_code != 200:
                logger.error(f"Response body: {response.text}")
            
            response.raise_for_status()
            return response.json()
                
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response body: {e.response.text}")
            raise Exception(f"Cortex Analyst call failed: {str(e)}")
        except Exception as e:
            logger.error(f"Cortex Analyst error: {str(e)}")
            raise Exception(f"Cortex Analyst call failed: {str(e)}")
    
    def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        """Execute SQL query and return results as list of dictionaries"""
        try:
            conn = self.snowflake.get_connection()
            cursor = conn.cursor()
            
            logger.debug(f"Executing SQL: {sql}")
            cursor.execute(sql)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                # Handle all non-JSON-serializable types
                converted_row = []
                for value in row:
                    if isinstance(value, (datetime, date)):
                        converted_row.append(value.isoformat())
                    elif isinstance(value, Decimal):
                        converted_row.append(float(value))
                    elif value is None:
                        converted_row.append(None)
                    else:
                        converted_row.append(value)
                results.append(dict(zip(columns, converted_row)))
            
            logger.debug(f"Query returned {len(results)} rows")
            return results
            
        except Exception as e:
            logger.error(f"SQL execution failed: {str(e)}")
            raise Exception(f"SQL execution failed: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    
    def calculate_health_metrics(self, query: str, results: List[Dict]) -> Dict[str, Any]:
        """Calculate basic health-specific metrics"""
        if not results:
            return {"message": "No data to analyze"}
        
        metrics = {
            "row_count": len(results),
            "columns": list(results[0].keys()) if results else [],
            "has_date_data": any("date" in str(k).lower() for k in results[0].keys()) if results else False,
            "has_numeric_data": any(isinstance(v, (int, float)) for v in results[0].values()) if results else False
        }
        
        # Add query-specific insights
        query_lower = query.lower()
        if "cholesterol" in query_lower:
            metrics["data_category"] = "lab_results"
            metrics["health_focus"] = "cardiovascular"
        elif "medication" in query_lower:
            metrics["data_category"] = "medications"
            metrics["health_focus"] = "treatment"
        elif "blood pressure" in query_lower:
            metrics["data_category"] = "vitals"
            metrics["health_focus"] = "cardiovascular"
        elif "hba1c" in query_lower or "glucose" in query_lower:
            metrics["data_category"] = "lab_results"
            metrics["health_focus"] = "diabetes"
        else:
            metrics["data_category"] = "general"
            metrics["health_focus"] = "general"
        
        return metrics
    
    async def execute_health_query(self, query: str) -> Dict[str, Any]:
        """
        Execute natural language health queries using Cortex Analyst
        
        Args:
            query: Natural language query about health data
            
        Returns:
            Query results with metadata including SQL generated, results, and health-specific metrics
        """
        try:
            logger.debug(f"Processing health query: {query}")
            
            # Call Cortex Analyst to translate query
            cortex_response = self.call_cortex_analyst(query)
            
            # Extract SQL from response
            sql = None
            interpretation = ""
            
            if "message" in cortex_response and "content" in cortex_response["message"]:
                for content_item in cortex_response["message"]["content"]:
                    if content_item.get("type") == "sql":
                        sql = content_item.get("statement")
                    if content_item.get("type") == "text":
                        interpretation += content_item.get("text", "") + "\n\n"
            
            if not sql:
                # Fallback extraction methods
                if "sql" in cortex_response:
                    sql = cortex_response["sql"]
                elif "code" in cortex_response:
                    sql = cortex_response["code"]
            
            if not sql:
                return {
                    "error": "Could not extract SQL from Cortex Analyst response",
                    "query": query,
                    "query_successful": False,
                    "cortex_response": cortex_response
                }
            
            logger.debug(f"Executing SQL: {sql}")
            
            # Execute the generated SQL
            results = self.execute_query(sql)
            
            # Calculate metrics
            metrics = self.calculate_health_metrics(query, results)
            
            # Return results in expected format
            return {
                "query": query,
                "interpretation": interpretation.strip(),
                "sql": sql,
                "results": results,
                "result_count": len(results),
                "data_metrics": metrics,
                "query_successful": True,
                "execution_time": "Not provided",
                "warnings": []
            }
            
        except Exception as e:
            logger.error(f"Query error: {str(e)}")
            return {
                "error": str(e),
                "error_details": traceback.format_exc(),
                "query": query,
                "query_successful": False
            }