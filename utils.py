# Signal handler for graceful shutdown
def signal_handler(sig, frame):
    print("\n🛑 Keyboard interrupt received. Shutting down gracefully...")
    # Terminate all active broker processes
    for broker in active_brokers:
        if broker.is_alive():
            print(f"Terminating broker process {broker.pid}")
            broker.terminate()
            broker.join(timeout=2)  # Wait up to 2 seconds for the process to terminate
            if broker.is_alive():
                print(f"Force killing broker process {broker.pid}")
                broker.kill()
    
    print("✅ All broker processes terminated. Exiting.")
    sys.exit(0)
