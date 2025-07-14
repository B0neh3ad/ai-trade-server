#!/usr/bin/env python3
"""
Test script for KOSPI database functionality
"""
import asyncio
import pandas as pd
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.database import KOSPIDatabase, DatabaseConfig
from app.utils.parser.websocket.domestic_index_future import DomesticIndexFutureExecutionResponse

async def test_database():
    """Test database functionality"""
    print("🔄 Testing KOSPI Database...")
    
    # Create database instance
    config = DatabaseConfig(
        base_path="/tmp/test_kospi_data",
        batch_size=5,  # Small batch size for testing
        max_memory_items=100
    )
    
    db = KOSPIDatabase(config)
    
    # Create some test data
    test_data = []
    for i in range(10):
        data = DomesticIndexFutureExecutionResponse(
            shrn_iscd="101W09",
            bsop_hour="090000",
            futs_prdy_vrss=str(1000 + i * 100),
            prdy_vrss_sign="2",
            futs_prdy_ctrt="0.50",
            futs_prpr=str(402000 + i * 100),
            futs_oprc="401000",
            futs_hgpr="403000",
            futs_lwpr="399000",
            last_cnqn=str(10 + i),
            acml_vol=str(1000 + i),
            acml_tr_pbmn=str(400000000 + i * 1000000),
            hts_thpr="402500",
            mrkt_basis="500",
            dprt="0.12",
            nmsc_fctn_stpl_prc="402000",
            fmsc_fctn_stpl_prc="403000",
            spead_prc="1000",
            hts_otst_stpl_qty="50000",
            otst_stpl_qty_icdc="100",
            oprc_hour="090000",
            oprc_vrss_prpr_sign="2",
            oprc_vrss_nmix_prpr="1000",
            hgpr_hour="110000",
            hgpr_vrss_prpr_sign="5",
            hgpr_vrss_nmix_prpr="-1000",
            lwpr_hour="140000",
            lwpr_vrss_prpr_sign="2",
            lwpr_vrss_nmix_prpr="3000",
            shnu_rate="52.5",
            cttr="120.5",
            esdg="0.15",
            otst_stpl_rgbf_qty_icdc="50",
            thpr_basis="450",
            futs_askp1="402100",
            futs_bidp1="401900",
            askp_rsqn1="100",
            bidp_rsqn1="150",
            seln_cntg_csnu="5",
            shnu_cntg_csnu="8",
            ntby_cntg_csnu="3",
            seln_cntg_smtn="500",
            shnu_cntg_smtn="800",
            total_askp_rsqn="1000",
            total_bidp_rsqn="1200",
            prdy_vol_vrss_acml_vol_rate="15.5",
            dscs_bltr_acml_qty="0",
            dynm_mxpr="410000",
            dynm_llam="390000",
            dynm_prc_limt_yn="N"
        )
        test_data.append(data)
    
    # Test 1: Add data
    print("\n1. Adding test data...")
    for i, data in enumerate(test_data):
        await db.add_data("H0IFCNT0", "101W09", data)
        print(f"   Added record {i+1}/10")
    
    # Test 2: Flush buffers
    print("\n2. Flushing buffers...")
    await db.flush_all_buffers()
    print("   ✅ Buffers flushed")
    
    # Test 3: Get available tables
    print("\n3. Getting available tables...")
    tables = db.get_available_tables()
    print(f"   Available tables: {tables}")
    
    # Test 4: Get table info
    if tables:
        table_name = tables[0]
        print(f"\n4. Getting info for table: {table_name}")
        info = db.get_table_info(table_name)
        print(f"   Table info: {info}")
    
    # Test 5: Query data
    print("\n5. Querying data...")
    df = db.get_data("101W09", "H0IFCNT0")
    print(f"   Retrieved {len(df)} records")
    if not df.empty:
        print("   Sample data:")
        print(df[['timestamp', 'shrn_iscd', 'futs_prpr', 'last_cnqn']].head())
    
    # Test 6: Export to CSV
    print("\n6. Testing CSV export...")
    if not df.empty:
        csv_data = df.to_csv(index=False)
        print(f"   CSV export successful, {len(csv_data)} characters")
        print("   Sample CSV (first 200 chars):")
        print(csv_data[:200] + "...")
    
    print("\n✅ All tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_database())