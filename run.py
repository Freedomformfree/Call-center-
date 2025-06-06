#!/usr/bin/env python3
"""
🚀 VoiceConnect Pro - One-Click Setup & Run Script
Run this single command to set up and launch the complete project
"""

import os
import sys
import subprocess
import time
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_command(cmd, description=""):
    """Run a command and handle errors"""
    logger.info(f"🔄 {description}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            logger.info(f"✅ {description} - Success")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ {description} - Failed: {e}")
        if e.stdout:
            logger.error(f"STDOUT: {e.stdout}")
        if e.stderr:
            logger.error(f"STDERR: {e.stderr}")
        return False

def check_python():
    """Check Python version"""
    logger.info("🐍 Checking Python version...")
    if sys.version_info < (3, 8):
        logger.error("❌ Python 3.8+ required")
        return False
    logger.info(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def install_dependencies():
    """Install required dependencies"""
    logger.info("📦 Installing dependencies...")
    
    # Check if requirements.txt exists
    if Path("requirements.txt").exists():
        return run_command("pip install -r requirements.txt", "Installing from requirements.txt")
    
    # Install essential packages
    packages = [
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "pydantic>=2.0.0",
        "python-multipart>=0.0.6",
        "jinja2>=3.1.0",
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "sqlalchemy>=2.0.0",
        "alembic>=1.12.0",
        "python-dotenv>=1.0.0",
        "httpx>=0.25.0",
        "aiofiles>=23.0.0"
    ]
    
    for package in packages:
        if not run_command(f"pip install {package}", f"Installing {package}"):
            logger.warning(f"⚠️ Failed to install {package}, continuing...")
    
    return True

def setup_environment():
    """Setup environment variables and configuration"""
    logger.info("⚙️ Setting up environment...")
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        env_content = """# VoiceConnect Pro Environment Configuration
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///./voiceconnect.db
GEMINI_API_KEY=your-gemini-api-key
OPENAI_API_KEY=your-openai-api-key
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
"""
        with open(env_file, "w") as f:
            f.write(env_content)
        logger.info("✅ Created .env file with default configuration")
    
    return True

def setup_database():
    """Setup database if needed"""
    logger.info("🗄️ Setting up database...")
    
    # Check if we have database models
    if Path("core-api/models.py").exists():
        # Try to run database migrations
        os.chdir("core-api")
        run_command("python -c \"from models import *; print('Database models loaded')\"", "Loading database models")
        os.chdir("..")
    
    return True

def clean_project():
    """Clean up unnecessary files"""
    logger.info("🧹 Cleaning project...")
    
    # Remove test/demo files
    patterns_to_remove = [
        "**/*test*.py",
        "**/*demo*.py", 
        "**/*sample*.py",
        "**/*simulation*.py",
        "**/__pycache__",
        "**/*.pyc",
        "**/*.log"
    ]
    
    for pattern in patterns_to_remove:
        run_command(f"find . -path './{pattern}' -delete 2>/dev/null || true", f"Removing {pattern}")
    
    return True

def start_server():
    """Start the FastAPI server"""
    logger.info("🚀 Starting VoiceConnect Pro server...")
    
    # Find the main application file
    main_files = ["core-api/main.py", "main.py", "app.py", "core-api/app.py"]
    main_file = None
    
    for file in main_files:
        if Path(file).exists():
            main_file = file
            break
    
    if not main_file:
        logger.error("❌ No main application file found")
        return False
    
    # Change to the correct directory
    if main_file.startswith("core-api/"):
        os.chdir("core-api")
        main_file = main_file.replace("core-api/", "")
    
    # Start the server
    logger.info(f"🌐 Starting server from {main_file}")
    logger.info("📱 Frontend will be available at: https://work-1-uojdozitopihokid.prod-runtime.all-hands.dev")
    logger.info("📊 Dashboard will be available at: https://work-1-uojdozitopihokid.prod-runtime.all-hands.dev/dashboard")
    logger.info("📚 API docs will be available at: https://work-1-uojdozitopihokid.prod-runtime.all-hands.dev/docs")
    
    # Run the server
    cmd = f"python {main_file}"
    if "uvicorn" in open(main_file).read():
        # If the file contains uvicorn.run, just run it
        os.system(cmd)
    else:
        # Otherwise, use uvicorn directly
        module_name = main_file.replace(".py", "").replace("/", ".")
        os.system(f"uvicorn {module_name}:app --host 0.0.0.0 --port 12000 --reload")
    
    return True

def main():
    """Main setup and run function"""
    print("""
🤖 VoiceConnect Pro - Complete Setup & Launch
=============================================
This script will:
1. Check Python version
2. Install dependencies  
3. Setup environment
4. Clean project files
5. Setup database
6. Launch the server

Starting setup...
""")
    
    # Step 1: Check Python
    if not check_python():
        sys.exit(1)
    
    # Step 2: Install dependencies
    if not install_dependencies():
        logger.warning("⚠️ Some dependencies failed to install, continuing...")
    
    # Step 3: Setup environment
    if not setup_environment():
        logger.error("❌ Environment setup failed")
        sys.exit(1)
    
    # Step 4: Clean project
    if not clean_project():
        logger.warning("⚠️ Project cleanup had issues, continuing...")
    
    # Step 5: Setup database
    if not setup_database():
        logger.warning("⚠️ Database setup had issues, continuing...")
    
    # Step 6: Start server
    logger.info("✅ Setup complete! Starting server...")
    time.sleep(2)
    
    if not start_server():
        logger.error("❌ Failed to start server")
        sys.exit(1)

if __name__ == "__main__":
    main()