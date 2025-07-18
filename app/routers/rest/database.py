from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict
from datetime import datetime
import pandas as pd

from app.db.database import get_kospi_database

router = APIRouter()

@router.get("/tables")
async def get_available_tables(date: Optional[str] = Query(None, description="Date in YYYYMMDD format")):
    """Get list of available tables in database"""
    try:
        kospi_db = get_kospi_database()
        tables = kospi_db.get_available_tables(date)
        return {"tables": tables}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tables/{table_name}/info")
async def get_table_info(table_name: str, date: Optional[str] = Query(None, description="Date in YYYYMMDD format")):
    """Get table information (row count, date range, etc.)"""
    try:
        kospi_db = get_kospi_database()
        info = kospi_db.get_table_info(table_name, date)
        
        if not info:
            raise HTTPException(status_code=404, detail="Table not found")
        
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/{instrument_code}/{tr_id}")
async def get_data(
    instrument_code: str, 
    tr_id: str,
    date: Optional[str] = Query(None, description="Date in YYYYMMDD format"),
    start_time: Optional[str] = Query(None, description="Start time in HH:MM:SS format"),
    end_time: Optional[str] = Query(None, description="End time in HH:MM:SS format"),
    limit: Optional[int] = Query(1000, description="Maximum number of rows to return")
):
    """
    Query data from database
    
    Examples:
    - /data/101W09/H0IFCNT0 - Get futures execution data
    - /data/101W09/H0IFASP0 - Get futures orderbook data
    - /data/201W072500/H0IOCNT0 - Get options execution data
    """
    try:
        kospi_db = get_kospi_database()
        df = kospi_db.get_data(instrument_code, tr_id, date, start_time, end_time)
        
        if df.empty:
            return {"data": [], "count": 0}
        
        # Apply limit
        if limit:
            df = df.tail(limit)
        
        # Convert DataFrame to dict
        data = df.to_dict(orient='records')
        
        return {
            "data": data,
            "count": len(data),
            "columns": df.columns.tolist()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/flush")
async def flush_buffers():
    """Flush all memory buffers to database"""
    try:
        kospi_db = get_kospi_database()
        await kospi_db.flush_all_buffers()
        return {"message": "All buffers flushed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_database_stats(date: Optional[str] = Query(None, description="Date in YYYYMMDD format")):
    """Get database statistics"""
    try:
        kospi_db = get_kospi_database()
        tables = kospi_db.get_available_tables(date)
        
        stats = {
            "date": date or datetime.now().strftime("%Y%m%d"),
            "total_tables": len(tables),
            "tables": {}
        }
        
        for table in tables:
            info = kospi_db.get_table_info(table, date)
            stats["tables"][table] = info
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cleanup")
async def cleanup_old_data(days_to_keep: int = Query(30, description="Number of days to keep")):
    """Clean up old database files"""
    try:
        kospi_db = get_kospi_database()
        await kospi_db.cleanup_old_data(days_to_keep)
        return {"message": f"Cleaned up data older than {days_to_keep} days"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/{instrument_code}/{tr_id}")
async def export_data_to_csv(
    instrument_code: str,
    tr_id: str,
    date: Optional[str] = Query(None, description="Date in YYYYMMDD format"),
    start_time: Optional[str] = Query(None, description="Start time in HH:MM:SS format"),
    end_time: Optional[str] = Query(None, description="End time in HH:MM:SS format")
):
    """Export data to CSV format"""
    try:
        kospi_db = get_kospi_database()
        df = kospi_db.get_data(instrument_code, tr_id, date, start_time, end_time)
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No data found")
        
        # Convert to CSV
        csv_data = df.to_csv(index=False)
        
        return {
            "csv_data": csv_data,
            "filename": f"{instrument_code}_{tr_id}_{date or datetime.now().strftime('%Y%m%d')}.csv",
            "row_count": len(df)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))