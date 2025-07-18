import asyncio
from datetime import datetime, time, timedelta
from app.db.database import get_kospi_database
from app.services.rest import fetch_domestic_futureoption_time_fuopchartprice, fetch_domestic_futureoption_daily_fuopchartprice

class BackgroundTasks:
    """Background tasks for database maintenance"""
    
    def __init__(self):
        self.running = False
        self.tasks = []
    
    async def start(self):
        """Start background tasks"""
        if self.running:
            return
        
        self.running = True
        
        # Start periodic buffer flush
        self.tasks.append(asyncio.create_task(self._periodic_flush_buffers()))
        
        # Start daily cleanup task
        self.tasks.append(asyncio.create_task(self._daily_cleanup()))
        
        # Start daily KOSPI200 futures data fetching task
        self.tasks.append(asyncio.create_task(self._daily_kospi200_futures_data_fetch()))
        
        print("✅ Background tasks started")
    
    async def stop(self):
        """Stop background tasks"""
        self.running = False
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Final buffer flush
        kospi_db = get_kospi_database()
        await kospi_db.flush_all_buffers()
        
        print("✅ Background tasks stopped")
    
    async def _periodic_flush_buffers(self):
        """Flush database buffers every 30 seconds"""
        while self.running:
            try:
                await asyncio.sleep(30)  # 30 seconds
                if self.running:
                    kospi_db = get_kospi_database()
                    await kospi_db.flush_all_buffers()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"⚠️ Error in periodic buffer flush: {e}")
    
    async def _daily_cleanup(self):
        """Clean up old data(30 days) daily at 2 AM"""
        while self.running:
            try:
                now = datetime.now()
                target_time = now.replace(hour=2, minute=0, second=0, microsecond=0)
                
                # If it's already past 2 AM today, schedule for tomorrow
                if now.time() > time(2, 0):
                    target_time = target_time.replace(day=target_time.day + 1)
                
                # Calculate sleep time
                sleep_seconds = (target_time - now).total_seconds()
                await asyncio.sleep(sleep_seconds)
                
                if self.running:
                    kospi_db = get_kospi_database()
                    await kospi_db.cleanup_old_data(days_to_keep=30)
                    print("✅ Daily cleanup completed")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"⚠️ Error in daily cleanup: {e}")
                # Wait 1 hour before retrying
                await asyncio.sleep(3600)
    
    async def _daily_kospi200_futures_data_fetch(self):
        """Fetch KOSPI200 futures data daily at 4 PM"""
        while self.running:
            try:
                now = datetime.now()
                target_time = now.replace(hour=16, minute=0, second=0, microsecond=0)
                
                # If it's already past 4 PM today, schedule for tomorrow
                if now.time() > time(16, 0):
                    target_time = target_time.replace(day=target_time.day + 1)
                
                # Calculate sleep time
                sleep_seconds = (target_time - now).total_seconds()
                await asyncio.sleep(sleep_seconds)
                
                if self.running:
                    # Fetch 1분봉 data
                    await self._fetch_kospi200_futures_1min_data()
                    
                    # Fetch 일봉 data
                    await self._fetch_kospi200_futures_daily_data()
                    
                    print("✅ Daily KOSPI200 futures data fetch completed")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"⚠️ Error in daily KOSPI200 futures data fetch: {e}")
                # Wait 1 hour before retrying
                await asyncio.sleep(3600)
    
    async def _fetch_kospi200_futures_1min_data(self):
        """KOSPI200 최근월 선물 1분봉 데이터 수집 및 저장"""
        market_div_code = "J"  # 선물
        symbol = "101W09"  # KOSPI200 최근월 (202509)
        date = datetime.now().strftime("%Y%m%d")
        hour = "16"  # 4 PM
        hour_class_code = "1"  # 1분봉
        include_pw_data = True
        
        try:
            data = fetch_domestic_futureoption_time_fuopchartprice(
                market_div_code, symbol, date, hour, hour_class_code, include_pw_data, print_log=True
            )
            
            # Save to database
            if data and 'output2' in data:
                kospi_db = get_kospi_database()
                await kospi_db.save_chart_data_to_db(symbol, data['output2'], "1min")
                print(f"✅ KOSPI200 futures 1분봉 data fetched and saved at {datetime.now()}")
            else:
                print(f"⚠️ No data received for KOSPI200 futures 1분봉")
            
            return data
        except Exception as e:
            print(f"⚠️ Error fetching KOSPI200 futures 1분봉 data: {e}")
            return None

    async def _fetch_kospi200_futures_daily_data(self):
        """KOSPI200 최근월 선물 일봉 데이터 수집 및 저장"""
        market_div_code = "J"  # 선물
        symbol = "101W09"  # KOSPI200 최근월 (202509)
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")  # 30일치
        period_div_code = "D"  # 일봉
        
        try:
            data = fetch_domestic_futureoption_daily_fuopchartprice(
                market_div_code, symbol, start_date, end_date, period_div_code, print_log=True
            )
            
            # Save to database
            if data and 'output2' in data:
                kospi_db = get_kospi_database()
                await kospi_db.save_chart_data_to_db(symbol, data['output2'], "daily")
                print(f"✅ KOSPI200 futures 일봉 data fetched and saved at {datetime.now()}")
            else:
                print(f"⚠️ No data received for KOSPI200 futures 일봉")
            
            return data
        except Exception as e:
            print(f"⚠️ Error fetching KOSPI200 futures 일봉 data: {e}")
            return None

# Global background tasks instance
_background_tasks = None

def get_background_tasks() -> BackgroundTasks:
    """Get global background tasks instance"""
    global _background_tasks
    if _background_tasks is None:
        _background_tasks = BackgroundTasks()
    return _background_tasks