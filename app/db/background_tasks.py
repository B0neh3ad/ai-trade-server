import asyncio
from datetime import datetime, time
from app.db.database import get_kospi_database

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

# Global background tasks instance
_background_tasks = None

def get_background_tasks() -> BackgroundTasks:
    """Get global background tasks instance"""
    global _background_tasks
    if _background_tasks is None:
        _background_tasks = BackgroundTasks()
    return _background_tasks