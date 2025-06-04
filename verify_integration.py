#!/usr/bin/env python3
"""
Verification script for Gemini integration
Checks that all required files are in place and properly configured.
"""

import os
import sys
import json

def check_file_exists(filepath, description):
    """Check if a file exists and print status."""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} (MISSING)")
        return False

def check_file_content(filepath, search_text, description):
    """Check if a file contains specific content."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            if search_text in content:
                print(f"✅ {description}")
                return True
            else:
                print(f"❌ {description} (NOT FOUND)")
                return False
    except Exception as e:
        print(f"❌ {description} (ERROR: {e})")
        return False

def main():
    """Run verification checks."""
    print("🔍 GEMINI INTEGRATION VERIFICATION")
    print("=" * 50)
    
    all_good = True
    
    # Check backend files
    print("\n📁 Backend Files:")
    backend_files = [
        ("core-api/gemini_chat_service.py", "Gemini Chat Service"),
        ("core-api/gemini_response_parser.py", "Gemini Response Parser"),
        ("core-api/gemini_chat_api.py", "Gemini Chat API"),
        ("core-api/requirements.txt", "Requirements File"),
        ("core-api/main.py", "Main Application"),
        ("config/api_keys.py", "API Keys Configuration"),
    ]
    
    for filepath, description in backend_files:
        if not check_file_exists(filepath, description):
            all_good = False
    
    # Check frontend files
    print("\n🎨 Frontend Files:")
    frontend_files = [
        ("frontend/gemini-chat.css", "Gemini Chat Styles"),
        ("frontend/gemini-chat.js", "Gemini Chat JavaScript"),
        ("frontend/dashboard.html", "Updated Dashboard"),
    ]
    
    for filepath, description in frontend_files:
        if not check_file_exists(filepath, description):
            all_good = False
    
    # Check content updates
    print("\n🔧 Content Verification:")
    content_checks = [
        ("core-api/main.py", "from gemini_chat_api import router as gemini_chat_router", "Gemini router import in main.py"),
        ("core-api/main.py", "app.include_router(gemini_chat_router)", "Gemini router included in main.py"),
        ("frontend/dashboard.html", "gemini-chat", "Gemini chat section in dashboard"),
        ("frontend/dashboard.html", "gemini-chat.css", "Gemini CSS included in dashboard"),
        ("frontend/dashboard.html", "gemini-chat.js", "Gemini JS included in dashboard"),
        ("config/api_keys.py", "gemini_api_key", "Gemini API key configuration"),
        ("core-api/requirements.txt", "google-generativeai", "Google Generative AI dependency"),
    ]
    
    for filepath, search_text, description in content_checks:
        if not check_file_content(filepath, search_text, description):
            all_good = False
    
    # Check if demo_main.py was deleted
    print("\n🗑️  File Cleanup:")
    if not os.path.exists("demo_main.py"):
        print("✅ demo_main.py deleted successfully")
    else:
        print("❌ demo_main.py still exists (should be deleted)")
        all_good = False
    
    # Check API key configuration
    print("\n🔑 API Configuration:")
    try:
        sys.path.append('config')
        from api_keys import api_keys
        
        # Check if the function exists and can be called
        try:
            # This will return None if GEMINI_API_KEY is not set, which is expected
            api_keys.get_api_key('gemini')
            print("✅ API key function accessible")
        except Exception as e:
            print(f"❌ API key function error: {e}")
            all_good = False
            
    except ImportError as e:
        print(f"❌ Cannot import API keys module: {e}")
        all_good = False
    
    # Environment check
    print("\n🌍 Environment:")
    gemini_key = os.getenv('GEMINI_API_KEY')
    if gemini_key:
        print(f"✅ GEMINI_API_KEY is set (length: {len(gemini_key)})")
    else:
        print("⚠️  GEMINI_API_KEY not set (required for API calls)")
    
    # Check dependencies
    print("\n📦 Dependencies:")
    try:
        import google.generativeai
        print("✅ google-generativeai package available")
    except ImportError:
        print("❌ google-generativeai package not installed")
        all_good = False
    
    try:
        import structlog
        print("✅ structlog package available")
    except ImportError:
        print("❌ structlog package not installed")
        all_good = False
    
    try:
        import fastapi
        print("✅ fastapi package available")
    except ImportError:
        print("❌ fastapi package not installed")
        all_good = False
    
    # Summary
    print("\n" + "=" * 50)
    if all_good:
        print("🎉 VERIFICATION PASSED!")
        print("\n✅ All components are properly installed and configured.")
        print("\n🚀 Next steps:")
        print("   1. Set GEMINI_API_KEY environment variable")
        print("   2. Start the server: cd core-api && uvicorn main:app --reload --host 0.0.0.0 --port 12000")
        print("   3. Open dashboard and test Gemini Chat tab")
    else:
        print("❌ VERIFICATION FAILED!")
        print("\n⚠️  Some components are missing or misconfigured.")
        print("   Please review the errors above and fix them.")
    
    print("\n📚 Documentation:")
    print("   - See GEMINI_INTEGRATION_README.md for detailed setup instructions")
    print("   - Run simple_gemini_test.py to test parsing functionality")
    
    return all_good

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)