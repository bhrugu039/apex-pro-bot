"""
APEX PRO - Start bot with built-in scheduler
"""

import os
import sys
import threading
import time
from datetime import datetime, timedelta

def run_bot():
    """Run the Telegram bot"""
    os.system("python bot.py")

def run_scanner():
    """Run the scanner"""
    print(f"🔍 Running scanner at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    os.system("python scanner.py")

def run_scanner_loop():
    """Run scanner daily at 6:00 PM IST"""
    
    # Run immediately on startup
    run_scanner()
    
    while True:
        # Calculate time until next 6:00 PM
        now = datetime.now()
        target = now.replace(hour=18, minute=0, second=0, microsecond=0)
        
        if now >= target:
            target += timedelta(days=1)
        
        wait_seconds = (target - now).total_seconds()
        print(f"⏰ Next scan at: {target.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏳ Waiting {wait_seconds/3600:.1f} hours...")
        
        time.sleep(wait_seconds)
        run_scanner()

def main():
    print("🚀 Starting APEX PRO Services...")
    
    # Start bot in background
    print("🤖 Starting Telegram Bot...")
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Start scanner loop (runs at 6 PM daily)
    print("📊 Starting Scanner (scheduled for 6:00 PM IST)...")
    scanner_thread = threading.Thread(target=run_scanner_loop, daemon=True)
    scanner_thread.start()
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("👋 Shutting down...")
        sys.exit(0)

if __name__ == "__main__":
    main()