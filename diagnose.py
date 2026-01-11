#!/usr/bin/env python3
"""
Diagnostic script to verify the LLM AirSim Swarm installation
and help troubleshoot common issues.
"""

import sys
import os
import json
from pathlib import Path

# Ensure src package is importable when running from repo root
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(current_dir))
if src_dir.exists():
    sys.path.insert(0, str(src_dir))


def print_header(text):
    print(f"\n{'='*70}")
    print(f"{text.center(70)}")
    print(f"{'='*70}")


def print_section(text):
    print(f"\n{text}")
    print("-" * len(text))


def check_python_version():
    """Check Python version"""
    print_section("1. Python Version")
    version = sys.version_info
    print(f"   Version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 8:
        print(f"   ✓ Python 3.8+ OK")
        return True
    else:
        print(f"   ✗ Python 3.8+ required")
        return False


def check_package(package_name, import_name=None):
    """Check if a package is installed"""
    if import_name is None:
        import_name = package_name
    
    try:
        module = __import__(import_name)
        version = getattr(module, '__version__', 'unknown')
        print(f"   ✓ {package_name:20s} {version}")
        return True
    except ImportError:
        print(f"   ✗ {package_name:20s} NOT INSTALLED")
        return False


def check_dependencies():
    """Check all required packages"""
    print_section("2. Python Dependencies")
    
    packages = [
        ("numpy", "numpy"),
        ("scipy", "scipy"),
        ("scikit-learn", "sklearn"),
        ("OpenAI", "openai"),
        ("AirSim", "airsim"),
        ("sdf", "sdf"),
    ]
    
    results = []
    for name, import_name in packages:
        results.append(check_package(name, import_name))
    
    if all(results):
        print(f"\n   ✓ All dependencies installed")
        return True
    else:
        print(f"\n   ✗ Missing dependencies. Run: pip install -r requirements.txt")
        return False


def check_environment_variables():
    """Check LLM API environment variables"""
    print_section("3. Environment Variables")
    
    vars_to_check = [
        ("OPENAI_API_KEY", "LLM API Key"),
        ("OPENAI_BASE_URL", "LLM API Base URL"),
        ("LLM_MODEL", "LLM Model Name"),
    ]
    
    all_set = True
    for var_name, description in vars_to_check:
        value = os.getenv(var_name, "")
        if value:
            # Mask the value for security
            if len(value) > 10:
                masked = value[:4] + "..." + value[-4:]
            else:
                masked = "*" * len(value)
            print(f"   ✓ {var_name:25s} = {masked}")
        else:
            print(f"   ⚠ {var_name:25s} not set")
            all_set = False
    
    if not all_set:
        print("\n   ⚠ Some LLM variables not set. Set them with:")
        print("     export OPENAI_API_KEY='your-key'")
        print("     export OPENAI_BASE_URL='https://api.openai.com/v1'")
        print("     export LLM_MODEL='gpt-3.5-turbo'")
    
    return all_set


def check_airsim_settings():
    """Check AirSim settings file"""
    print_section("4. AirSim Configuration")
    
    # Common AirSim settings locations
    possible_paths = [
        os.path.expanduser("~/Documents/AirSim/settings.json"),
        os.path.expanduser("~/.config/AirSim/settings.json"),
        "./settings.json",
        "./airsim_swarm_llm/settings.json",
    ]
    
    settings_found = None
    for path in possible_paths:
        if os.path.exists(path):
            settings_found = path
            break
    
    if settings_found:
        print(f"   ✓ Found settings at: {settings_found}")
        try:
            with open(settings_found, 'r') as f:
                settings = json.load(f)
            
            # Check key settings
            sim_mode = settings.get("SimMode", "Unknown")
            vehicles = settings.get("Vehicles", {})
            
            print(f"   ✓ SimMode: {sim_mode}")
            print(f"   ✓ Number of vehicles: {len(vehicles)}")
            
            for drone_name in list(vehicles.keys())[:4]:  # Show first 4
                print(f"     - {drone_name}")
            
            if len(vehicles) > 4:
                print(f"     ... and {len(vehicles) - 4} more")
            
            return True
            
        except Exception as e:
            print(f"   ✗ Error reading settings: {e}")
            return False
    else:
        print(f"   ⚠ AirSim settings.json not found")
        print(f"   Expected locations:")
        for path in possible_paths:
            print(f"     - {path}")
        return False


def test_llm_api():
    """Test LLM API connection"""
    print_section("5. LLM API Connection Test")
    
    try:
        from src.llm_client import LLMClient
        
        print("   Attempting to connect to LLM API...")
        client = LLMClient()
        
        print("   Sending test message...")
        response = client.chat_completion([
            {"role": "user", "content": "Say 'OK' in one word"}
        ])
        
        if response:
            print(f"   ✓ API responded: '{response}'")
            return True
        else:
            print(f"   ✗ No response from API")
            return False
            
    except ImportError:
        print(f"   ✗ Could not import llm_client")
        print(f"   Make sure you're in the correct directory")
        return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        print(f"   Check:")
        print(f"     - API key is valid")
        print(f"     - Network connection is working")
        print(f"     - API base URL is correct")
        return False


def test_airsim_connection():
    """Test AirSim connection"""
    print_section("6. AirSim Connection Test")
    
    try:
        import airsim
        
        print("   Attempting to connect to AirSim at 127.0.0.1...")
        client = airsim.MultirotorClient(ip="127.0.0.1")
        
        print("   Confirming connection...")
        client.confirmConnection()
        
        print(f"   ✓ Connected to AirSim")
        return True
        
    except ImportError:
        print(f"   ✗ Could not import airsim")
        return False
    except Exception as e:
        print(f"   ⚠ Could not connect to AirSim: {e}")
        print(f"   Make sure:")
        print(f"     - AirSim is running")
        print(f"     - Configured for multi-drone mode")
        print(f"     - IP 127.0.0.1 is correct")
        return False


def check_project_structure():
    """Check if project files are in place"""
    print_section("7. Project Files")
    
    required_files = [
        ("src/llm_client.py", "LLM Client"),
        ("src/airsim_controller.py", "AirSim Controller"),
        ("src/swarm_controller.py", "Swarm Controller"),
        ("src/sdf_executor.py", "SDF Executor"),
        ("src/integrated_controller.py", "Integrated Controller"),
        ("src/config.py", "Configuration"),
        ("examples.py", "Examples Script"),
        ("docs/README.md", "Documentation"),
        ("requirements.txt", "Dependencies"),
    ]
    
    all_found = True
    for filename, description in required_files:
        if os.path.exists(filename):
            print(f"   ✓ {description:30s} ({filename})")
        else:
            print(f"   ✗ {description:30s} ({filename}) - NOT FOUND")
            all_found = False
    
    return all_found


def generate_summary(results):
    """Generate a summary report"""
    print_header("DIAGNOSTIC SUMMARY")
    
    categories = {
        "Critical": ["Python Version", "Dependencies", "Project Files"],
        "Important": ["Environment Variables", "AirSim Settings"],
        "Optional": ["LLM API Connection", "AirSim Connection"],
    }
    
    # Create result mapping
    result_map = {
        "Python Version": results.get("python_version", False),
        "Dependencies": results.get("dependencies", False),
        "Environment Variables": results.get("env_vars", False),
        "AirSim Settings": results.get("airsim_settings", False),
        "LLM API Connection": results.get("llm_connection", False),
        "AirSim Connection": results.get("airsim_connection", False),
        "Project Files": results.get("project_files", False),
    }
    
    for category, checks in categories.items():
        print(f"\n{category}:")
        for check in checks:
            status = "✓" if result_map.get(check, False) else "✗"
            print(f"  {status} {check}")
    
    # Recommendations
    print(f"\n{'Recommendations':30s}")
    print("-" * 30)
    
    if not result_map.get("Dependencies", False):
        print("• Install missing dependencies:")
        print("  pip install -r requirements.txt")
    
    if not result_map.get("Environment Variables", False):
        print("• Set LLM API credentials:")
        print("  export OPENAI_API_KEY='your-key'")
        print("  export OPENAI_BASE_URL='https://api.openai.com/v1'")
        print("  export LLM_MODEL='gpt-3.5-turbo'")
    
    if not result_map.get("AirSim Settings", False):
        print("• Copy settings.json to AirSim configuration directory")
        print("  See INSTALL.md for details")
    
    if not result_map.get("AirSim Connection", False):
        print("• Start AirSim and ensure it's in multi-drone mode")
        print("  Check LocalHostIp in settings.json")
    
    if result_map.get("Dependencies", False) and result_map.get("Environment Variables", False):
        print("• Run quickstart.py for interactive testing:")
        print("  python quickstart.py --interactive")
    
    # Overall status
    critical_ok = all(result_map.get(c, False) for c in categories["Critical"])
    
    print("\n" + "="*70)
    if critical_ok:
        print("✓ System appears to be correctly configured!".center(70))
        print("Ready to use. See README.md for usage examples.".center(70))
    else:
        print("✗ Some critical issues found. Please fix above issues.".center(70))
    print("="*70 + "\n")


def main():
    """Run all diagnostics"""
    print_header("LLM AirSim Swarm Controller - Diagnostic Tool")
    
    results = {}
    
    # Run all checks
    results["python_version"] = check_python_version()
    results["dependencies"] = check_dependencies()
    results["env_vars"] = check_environment_variables()
    results["airsim_settings"] = check_airsim_settings()
    results["project_files"] = check_project_structure()
    
    # Optional tests (don't fail overall if these fail)
    try:
        results["llm_connection"] = test_llm_api()
    except Exception as e:
        print(f"LLM API test skipped: {e}")
        results["llm_connection"] = False
    
    try:
        results["airsim_connection"] = test_airsim_connection()
    except Exception as e:
        print(f"AirSim test skipped: {e}")
        results["airsim_connection"] = False
    
    # Generate summary
    generate_summary(results)


if __name__ == "__main__":
    main()
