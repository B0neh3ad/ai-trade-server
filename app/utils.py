# Signal handler for graceful shutdown
import sys
from global_vars import global_broker_ws

def signal_handler(sig, frame):
    # TODO: 구독 중이던 정보 전부 구독 취소하기
    print("\n🛑 Keyboard interrupt received. Shutting down gracefully...")
    try:
        if global_broker_ws.is_alive():
            print(f"Terminating broker process {global_broker_ws.pid}")
            global_broker_ws.terminate()
            global_broker_ws.join(timeout=2)  # Wait up to 2 seconds for the process to terminate
            if global_broker_ws.is_alive():
                print(f"Force killing broker process {global_broker_ws.pid}")
                global_broker_ws.kill()
        print("✅ All broker processes terminated. Exiting.")
    finally:
        sys.exit(0)
