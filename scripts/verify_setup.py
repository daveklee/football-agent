"""Verification script to test setup and dependencies."""
import sys
import importlib

def check_import(module_name, package_name=None):
    """Check if a module can be imported."""
    try:
        importlib.import_module(module_name)
        print(f"✅ {package_name or module_name}")
        return True
    except ImportError as e:
        print(f"❌ {package_name or module_name}: {e}")
        return False

def check_environment():
    """Check environment variables."""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    required_vars = [
        'GEMINI_API_KEY',
        'YAHOO_CONSUMER_KEY',
        'YAHOO_CONSUMER_SECRET',
        'YAHOO_LEAGUE_ID',
    ]
    
    optional_vars = [
        'YAHOO_EMAIL',
        'YAHOO_PASSWORD',
    ]
    
    print("\n📋 Environment Variables:")
    print("=" * 60)
    
    all_set = True
    for var in required_vars:
        value = os.getenv(var)
        if value and value not in ['your_gemini_api_key_here', 'your_yahoo_consumer_key', 'your_league_id']:
            print(f"✅ {var}: {'*' * min(len(value), 20)}")
        else:
            print(f"❌ {var}: Not set or using placeholder")
            all_set = False
    
    for var in optional_vars:
        value = os.getenv(var)
        if value and value not in ['your_yahoo_email@example.com']:
            print(f"⚠️  {var}: {'*' * min(len(value), 20)} (optional)")
        else:
            print(f"⚠️  {var}: Not set (optional, needed for browser automation)")
    
    return all_set

def check_python_version():
    """Check Python version."""
    version = sys.version_info
    print(f"\n🐍 Python Version: {version.major}.{version.minor}.{version.micro}")
    if version.major >= 3 and version.minor >= 9:
        print("✅ Python version is compatible")
        return True
    else:
        print("❌ Python 3.9+ required")
        return False

def check_dependencies():
    """Check if required dependencies are installed."""
    print("\n📦 Dependencies:")
    print("=" * 60)
    
    dependencies = [
        ('google.generativeai', 'google-generativeai'),
        ('yahoofantasy', 'yahoofantasy'),
        ('selenium', 'selenium'),
        ('dotenv', 'python-dotenv'),
        ('pydantic', 'pydantic'),
        ('aiohttp', 'aiohttp'),
    ]
    
    results = []
    for module, package in dependencies:
        results.append(check_import(module, package))
    
    # Check ADK (may not be available)
    print("\n🔧 Google ADK:")
    adk_available = False
    try:
        import google.adk
        print("✅ google-adk (new style)")
        adk_available = True
    except ImportError:
        try:
            import google.adk.agents
            print("✅ google-adk (alternative style)")
            adk_available = True
        except ImportError:
            print("⚠️  google-adk: Not found (may need special installation)")
            print("   See SETUP_NOTES.md for installation instructions")
    
    # Check MCP
    print("\n🔌 MCP Server:")
    try:
        import mcp
        print("✅ mcp")
    except ImportError:
        print("⚠️  mcp: Not found (may need installation)")
    
    return all(results), adk_available

def test_gemini_api():
    """Test Gemini API connection."""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key or api_key == 'your_gemini_api_key_here':
        print("\n⚠️  Gemini API: API key not configured")
        return False
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        # Using gemini-2.5-pro for function calling support
        model = genai.GenerativeModel('gemini-2.5-pro')
        response = model.generate_content("Say 'test' if you can read this.")
        print(f"\n✅ Gemini API: Connected successfully")
        print(f"   Response: {response.text[:50]}...")
        return True
    except Exception as e:
        print(f"\n❌ Gemini API: Connection failed - {e}")
        return False

def test_browser_mcp():
    """Test Browser MCP availability."""
    try:
        # Check if Browser MCP extension is mentioned in docs
        # Actual testing would require the extension to be installed
        print(f"\n⚠️  Browser MCP: Manual check required")
        print("   Make sure Browser MCP Chrome extension is installed: https://browsermcp.io/")
        print("   Browser MCP uses stdio transport (no port needed)")
        return True  # Don't fail setup if extension not installed
    except Exception as e:
        print(f"\n⚠️  Browser MCP: {e}")
        return True  # Non-critical

def main():
    """Run all verification checks."""
    print("=" * 60)
    print("Fantasy Football Agent - Setup Verification")
    print("=" * 60)
    
    checks = []
    
    # Python version
    checks.append(check_python_version())
    
    # Dependencies
    deps_ok, adk_ok = check_dependencies()
    checks.append(deps_ok)
    
    # Environment variables
    env_ok = check_environment()
    checks.append(env_ok)
    
    # Gemini API
    if env_ok:
        checks.append(test_gemini_api())
    
    # Browser MCP (optional but recommended)
    browser_mcp_ok = test_browser_mcp()
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    
    if all(checks):
        print("✅ All critical checks passed!")
        print("\nNext steps:")
        print("1. Complete Yahoo OAuth setup (see README.md)")
        print("2. Test the agent: python example_usage.py")
        print("3. Start ADK web interface: make run-web or ./scripts/start_adk_web.sh")
    else:
        print("⚠️  Some checks failed. Please review the errors above.")
        print("\nCommon fixes:")
        print("- Install missing dependencies: pip install -r requirements.txt")
        print("- Set up .env file with your credentials")
        print("- Install ChromeDriver for browser automation")
        print("- See SETUP_NOTES.md for detailed instructions")
    
    if not browser_mcp_ok:
        print("\n⚠️  Browser MCP: Install Chrome extension from https://browsermcp.io/")
    
    if not adk_ok:
        print("\n⚠️  Google ADK not found. See SETUP_NOTES.md for installation.")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()

