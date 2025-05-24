import sys

# Signal handler for graceful shutdown
def signal_handler(sig, frame):
    # TODO: 구독 중이던 정보 전부 구독 취소하기
    print("\n🛑 Keyboard interrupt received.")
