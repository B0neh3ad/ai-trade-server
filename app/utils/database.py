import sqlite3
import pandas as pd
import asyncio
from datetime import datetime
from typing import Dict, List
from dataclasses import dataclass, asdict
from pathlib import Path
import os
import threading
from concurrent.futures import ThreadPoolExecutor
import logging

from app.utils.parser.websocket.map import TR_ID_MAP, InstrumentType, MessageType

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Database configuration"""
    base_path: str = "/home/js1044k/ai-trade-server/data"
    batch_size: int = 100
    max_memory_items: int = 10000
    
class KOSPIDatabase:
    """
    SQLite database manager for KOSPI200 futures/options real-time data
    
    Database Structure:
    - One database per day (YYYYMMDD.db)
    - Separate tables for each instrument type and TR_ID
    - Tables: {instrument_code}_{tr_id} (e.g., 101W09_H0IFCNT0, 201W0725_H0IOCNT0)
    """
    
    def __init__(self, config: DatabaseConfig = None):
        self.config = config or DatabaseConfig()
        self.memory_buffer: Dict[str, List[Dict]] = {}
        self.lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Create data directory if it doesn't exist
        Path(self.config.base_path).mkdir(parents=True, exist_ok=True)
    
    def get_db_path(self, date_str: str = None) -> str:
        """Get database file path for given date"""
        if date_str is None:
            date_str = datetime.now().strftime("%Y%m%d")
        return os.path.join(self.config.base_path, f"{date_str}.db")
    
    def get_table_name(self, instrument_code: str, tr_id: str) -> str:
        """Generate table name from instrument code and TR_ID"""
        return f"{instrument_code}_{tr_id}"
    
    def _create_table_if_not_exists(self, conn: sqlite3.Connection, table_name: str, tr_id: str):
        """Create table if it doesn't exist based on TR_ID"""
        tr_meta = TR_ID_MAP[tr_id]
        dataclass = tr_meta.model
        fields = dataclass.__dataclass_fields__
        if tr_meta.message_type == MessageType.ORDERBOOK:
            fields = ['bsop_hour', 'futs_askp1', 'futs_bidp1', 'askp_csnu1', 'bidp_csnu1', 'askp_rsqn1', 'bidp_rsqn1']

        field_names_str = ', '.join([f'{name} TEXT' for name in fields])
        sql = f"""
        CREATE TABLE IF NOT EXISTS '{table_name}' (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            {field_names_str}
        )
        """
        
        conn.execute(sql)
        # Create indexes for performance
        conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_timestamp ON '{table_name}'(timestamp)")
    
    async def add_data(self, tr_id: str, tr_key: str, data):
        """Add data to memory buffer for batch processing"""
        table_name = self.get_table_name(tr_key, tr_id)
        data_dict = asdict(data)

        # 호가 데이터는 매도/매수호가1 관련 데이터만 저장
        tr_meta = TR_ID_MAP[tr_id]
        if tr_meta.message_type == MessageType.ORDERBOOK:
            # TODO: message type 판별 if문은 선물/옵션 일반화 되어 있으나, column명은 선물만 적용됨
            # 추후 옵션 등의 호가 데이터 추가 시 column명 일반화 필요
            data_dict = {k: v for k, v in data_dict.items() if k in
                         ['bsop_hour', 'futs_askp1', 'futs_bidp1', 'askp_csnu1', 'bidp_csnu1', 'askp_rsqn1', 'bidp_rsqn1']}
        
        # Add timestamp when data is received
        data_dict['timestamp'] = datetime.now().isoformat()
        
        logger.debug(f"Adding data to buffer: table='{table_name}', tr_id='{tr_id}', tr_key='{tr_key}'")
        
        with self.lock:
            if table_name not in self.memory_buffer:
                self.memory_buffer[table_name] = []
                logger.info(f"Created new buffer for table '{table_name}'")
            
            self.memory_buffer[table_name].append({
                'tr_id': tr_id,
                'data': data_dict
            })
            
            buffer_size = len(self.memory_buffer[table_name])
            logger.debug(f"Buffer size for '{table_name}': {buffer_size}/{self.config.batch_size}")
            
            # Check if we need to flush this table
            if buffer_size >= self.config.batch_size:
                logger.info(f"Buffer full for '{table_name}', triggering flush")
                await self._flush_table_buffer(table_name)
    
    async def _flush_table_buffer(self, table_name: str):
        """Flush specific table buffer to database"""
        if table_name not in self.memory_buffer or not self.memory_buffer[table_name]:
            logger.warning(f"No data to flush for table '{table_name}'")
            return
            
        # Move data to avoid blocking
        buffer_data = self.memory_buffer[table_name].copy()
        self.memory_buffer[table_name] = []
        
        logger.info(f"Flushing {len(buffer_data)} records from buffer to database for table '{table_name}'")
        
        # Run database operation in thread pool
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, self._write_to_database, table_name, buffer_data)
    
    def _write_to_database(self, table_name: str, buffer_data: List[Dict]):
        """Write buffer data to database (runs in thread pool)"""
        if not buffer_data:
            return
            
        db_path = self.get_db_path()
        tr_id = buffer_data[0]['tr_id']
        
        # Log database connection
        db_exists = os.path.exists(db_path)
        logger.info(f"Database path: {db_path} (exists: {db_exists})")
        
        with sqlite3.connect(db_path) as conn:
            # Log database file creation
            if not db_exists:
                logger.info(f"✅ Created new database file: {db_path}")
            
            self._create_table_if_not_exists(conn, table_name, tr_id)
            logger.info(f"Table '{table_name}' ready for data insertion")

            # # [DEBUG] log column names of table `table_name`
            # cursor = conn.execute(f"PRAGMA table_info('{table_name}')")
            # column_names = [row[1] for row in cursor.fetchall()]
            # print(f"Column names: {column_names}")
            
            # Prepare data for insertion
            rows = []
            for item in buffer_data:
                row = item['data'].copy()
                # Use the timestamp from the buffer data
                row['timestamp'] = item['data']['timestamp']
                rows.append(row)
            
            # Convert to DataFrame for easier insertion
            df = pd.DataFrame(rows)
            df.to_sql(table_name, conn, if_exists='append', index=False)
            
            logger.info(f"✅ Inserted {len(rows)} rows into table '{table_name}' in database '{db_path}'")
            print(f"✅ Inserted {len(rows)} rows into {table_name}")
    
    async def flush_all_buffers(self):
        """Flush all memory buffers to database"""
        tasks = []
        for table_name in list(self.memory_buffer.keys()):
            if self.memory_buffer[table_name]:
                tasks.append(self._flush_table_buffer(table_name))
        
        if tasks:
            await asyncio.gather(*tasks)
    
    def get_data(self, instrument_code: str, tr_id: str, date_str: str = None, 
                 start_time: str = None, end_time: str = None) -> pd.DataFrame:
        """
        Query data from database
        
        Args:
            instrument_code: Instrument code (e.g., '101W09')
            tr_id: Transaction ID (e.g., 'H0IFCNT0')
            date_str: Date string (YYYYMMDD), defaults to today
            start_time: Start time filter (HH:MM:SS)
            end_time: End time filter (HH:MM:SS)
        
        Returns:
            pandas.DataFrame: Query results
        """
        db_path = self.get_db_path(date_str)
        table_name = self.get_table_name(instrument_code, tr_id)
        
        if not os.path.exists(db_path):
            return pd.DataFrame()
        
        query = f"SELECT * FROM '{table_name}'"
        conditions = []
        
        if start_time:
            conditions.append(f"time(timestamp) >= '{start_time}'")
        if end_time:
            conditions.append(f"time(timestamp) <= '{end_time}'")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY timestamp"
        
        try:
            with sqlite3.connect(db_path) as conn:
                return pd.read_sql_query(query, conn)
        except Exception as e:
            print(f"Error querying data: {e}")
            return pd.DataFrame()
    
    def get_available_tables(self, date_str: str = None) -> List[str]:
        """Get list of available tables in database"""
        db_path = self.get_db_path(date_str)
        
        if not os.path.exists(db_path):
            return []
        
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting tables: {e}")
            return []
    
    def get_table_info(self, table_name: str, date_str: str = None) -> Dict:
        """Get table information (row count, date range, etc.)"""
        db_path = self.get_db_path(date_str)
        
        if not os.path.exists(db_path):
            return {}
        
        try:
            with sqlite3.connect(db_path) as conn:
                # Get row count
                cursor = conn.execute(f"SELECT COUNT(*) FROM '{table_name}'")
                row_count = cursor.fetchone()[0]
                
                # Get date range
                cursor = conn.execute(f"SELECT MIN(timestamp), MAX(timestamp) FROM '{table_name}'")
                date_range = cursor.fetchone()
                
                return {
                    'table_name': table_name,
                    'row_count': row_count,
                    'min_timestamp': date_range[0],
                    'max_timestamp': date_range[1]
                }
        except Exception as e:
            print(f"Error getting table info: {e}")
            return {}
    
    async def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old database files"""
        current_date = datetime.now().date()
        
        for filename in os.listdir(self.config.base_path):
            if filename.endswith('.db'):
                try:
                    file_date = datetime.strptime(filename[:8], '%Y%m%d').date()
                    if (current_date - file_date).days > days_to_keep:
                        os.remove(os.path.join(self.config.base_path, filename))
                        print(f"Deleted old database: {filename}")
                except:
                    continue
    
    def __del__(self):
        """Cleanup on destruction"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)

# Global database instance
_kospi_db = None

def get_kospi_database() -> KOSPIDatabase:
    """Get global KOSPI database instance"""
    global _kospi_db
    if _kospi_db is None:
        _kospi_db = KOSPIDatabase()
    return _kospi_db