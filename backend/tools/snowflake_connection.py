"""
Snowflake connection management
"""
import os
from pathlib import Path
import snowflake.connector
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import logging

logger = logging.getLogger(__name__)

class SnowflakeConnection:
    """Manages Snowflake database connections"""
    
    def __init__(self):
        self.user = os.getenv("SNOWFLAKE_USER")
        self.account = os.getenv("SNOWFLAKE_ACCOUNT")
        self.private_key_path = os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH")
        self.warehouse = os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")
        self.database = os.getenv("SNOWFLAKE_DATABASE", "HEALTH_INTELLIGENCE")
        self.schema = os.getenv("SNOWFLAKE_SCHEMA", "HEALTH_RECORDS")
        self.role = os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN")
        
    def _get_private_key(self):
        """Load private key from file"""
        if not self.private_key_path:
            raise ValueError("SNOWFLAKE_PRIVATE_KEY_PATH environment variable not set")
        
        key_path = Path(self.private_key_path).expanduser()
        if not key_path.exists():
            raise FileNotFoundError(f"Private key file not found: {key_path}")
        
        with open(key_path, 'rb') as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None,
                backend=default_backend()
            )
        return private_key
    
    def get_connection(self):
        """Create Snowflake connection using key-pair authentication"""
        try:
            private_key = self._get_private_key()
            
            return snowflake.connector.connect(
                user=self.user,
                account=self.account,
                private_key=private_key,
                warehouse=self.warehouse,
                database=self.database,
                schema=self.schema,
                role=self.role
            )
        except Exception as e:
            logger.error(f"Failed to connect to Snowflake: {str(e)}")
            raise