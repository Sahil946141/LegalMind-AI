#!/usr/bin/env python3
"""
Setup script to help configure Redis and Celery for the Legal Analyzer
"""
import subprocess
import sys
import os
import platform

def check_redis():
    """Check if Redis is running"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis is running and accessible")
        return True
    except Exception as e:
        print(f"❌ Redis is not accessible: {e}")
        return False

def check_redis_installed():
    """Check if Redis is installed"""
    try:
        result = subprocess.run(['redis-server', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"✅ Redis is installed: {result.stdout.strip()}")
            return True
    except Exception:
        pass
    
    print("❌ Redis is not installed")
    return False

def install_redis_instructions():
    """Provide Redis installation instructions"""
    system = platform.system().lower()
    
    print("\n📋 Redis Installation Instructions:")
    print("=" * 50)
    
    if system == "windows":
        print("For Windows:")
        print("1. Download Redis from: https://github.com/microsoftarchive/redis/releases")
        print("2. Or use WSL2 with Ubuntu and run: sudo apt install redis-server")
        print("3. Or use Docker: docker run -d -p 6379:6379 redis:alpine")
        
    elif system == "darwin":  # macOS
        print("For macOS:")
        print("1. Using Homebrew: brew install redis")
        print("2. Start Redis: brew services start redis")
        print("3. Or use Docker: docker run -d -p 6379:6379 redis:alpine")
        
    else:  # Linux
        print("For Linux (Ubuntu/Debian):")
        print("1. Update packages: sudo apt update")
        print("2. Install Redis: sudo apt install redis-server")
        print("3. Start Redis: sudo systemctl start redis-server")
        print("4. Enable auto-start: sudo systemctl enable redis-server")
        print("5. Or use Docker: docker run -d -p 6379:6379 redis:alpine")

def start_redis_instructions():
    """Provide instructions to start Redis"""
    system = platform.system().lower()
    
    print("\n🚀 Starting Redis:")
    print("=" * 30)
    
    if system == "windows":
        print("Windows:")
        print("1. If installed natively: redis-server")
        print("2. If using WSL2: sudo service redis-server start")
        print("3. If using Docker: docker run -d -p 6379:6379 redis:alpine")
        
    elif system == "darwin":  # macOS
        print("macOS:")
        print("1. Using Homebrew: brew services start redis")
        print("2. Or manually: redis-server")
        print("3. If using Docker: docker run -d -p 6379:6379 redis:alpine")
        
    else:  # Linux
        print("Linux:")
        print("1. Using systemctl: sudo systemctl start redis-server")
        print("2. Or manually: redis-server")
        print("3. If using Docker: docker run -d -p 6379:6379 redis:alpine")

def start_celery_worker():
    """Instructions to start Celery worker"""
    print("\n🔧 Starting Celery Worker:")
    print("=" * 35)
    print("Run this command in a separate terminal:")
    
    system = platform.system().lower()
    if system == "windows":
        print("celery -A app.worker.celery_app worker --loglevel=info --pool=solo")
    else:
        print("celery -A app.worker.celery_app worker --loglevel=info")
    
    print("\nNote: Keep this terminal open while using the application")

def main():
    print("🔍 Legal Analyzer - Redis & Celery Setup Check")
    print("=" * 55)
    
    # Check if Redis is installed
    redis_installed = check_redis_installed()
    
    # Check if Redis is running
    redis_running = check_redis()
    
    if not redis_installed:
        install_redis_instructions()
        return
    
    if not redis_running:
        start_redis_instructions()
        print("\n⏳ After starting Redis, run this script again to verify")
        return
    
    # If Redis is running, provide Celery instructions
    start_celery_worker()
    
    print("\n✅ Setup Complete!")
    print("Now you can:")
    print("1. Start the FastAPI server: python run_server.py")
    print("2. Upload documents and they will be processed by Celery")

if __name__ == "__main__":
    main()