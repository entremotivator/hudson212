#!/usr/bin/env python3
"""
Test script for the enhanced property search functionality.
This script tests the new database and export utilities.
"""

import sys
import json
from datetime import datetime

# Test data for validation
SAMPLE_PROPERTY_DATA = {
    "address": "123 Test Street, Test City, TS 12345",
    "results": [
        {
            "formattedAddress": "123 Test Street, Test City, TS 12345",
            "city": "Test City",
            "state": "TS",
            "zipCode": "12345",
            "propertyType": "Single Family",
            "bedrooms": 3,
            "bathrooms": 2,
            "squareFootage": 1500,
            "yearBuilt": 2000,
            "lastSalePrice": 350000,
            "lastSaleDate": "2023-01-15",
            "ownerOccupied": True
        }
    ],
    "search_params": {"address": "123 Test Street, Test City, TS 12345"},
    "search_timestamp": datetime.now().isoformat()
}

def test_imports():
    """Test that all new modules can be imported."""
    print("Testing imports...")
    
    try:
        from utils.search_database import (
            save_property_search,
            get_user_searches,
            save_named_search,
            get_search_statistics
        )
        print("✅ search_database imports successful")
    except ImportError as e:
        print(f"❌ search_database import failed: {e}")
        return False
    
    try:
        from utils.export_utils import (
            export_to_json,
            export_to_csv,
            export_to_excel,
            export_to_pdf_report,
            get_export_summary
        )
        print("✅ export_utils imports successful")
    except ImportError as e:
        print(f"❌ export_utils import failed: {e}")
        return False
    
    return True

def test_export_functions():
    """Test export utility functions."""
    print("\nTesting export functions...")
    
    try:
        from utils.export_utils import (
            export_to_json,
            export_to_csv,
            get_export_summary
        )
        
        # Test JSON export
        json_data, json_filename = export_to_json(SAMPLE_PROPERTY_DATA, "test")
        if json_data and json_filename:
            print("✅ JSON export function works")
        else:
            print("❌ JSON export function failed")
            return False
        
        # Test CSV export
        csv_data, csv_filename = export_to_csv(SAMPLE_PROPERTY_DATA["results"], "test")
        if csv_data and csv_filename:
            print("✅ CSV export function works")
        else:
            print("❌ CSV export function failed")
            return False
        
        # Test export summary
        summary = get_export_summary(SAMPLE_PROPERTY_DATA)
        if summary and "Export Date" in summary:
            print("✅ Export summary function works")
        else:
            print("❌ Export summary function failed")
            return False
        
    except Exception as e:
        print(f"❌ Export function test failed: {e}")
        return False
    
    return True

def test_file_structure():
    """Test that all required files exist."""
    print("\nTesting file structure...")
    
    import os
    
    required_files = [
        "utils/search_database.py",
        "utils/export_utils.py",
        "pages/4_📋_Saved_Searches.py",
        "pages/5_📥_Downloads.py",
        "requirements.txt",
        "ENHANCEMENTS.md"
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            return False
    
    return True

def test_requirements():
    """Test that requirements.txt includes new dependencies."""
    print("\nTesting requirements...")
    
    try:
        with open("requirements.txt", "r") as f:
            requirements = f.read()
        
        required_packages = ["reportlab", "openpyxl", "pandas", "streamlit"]
        
        for package in required_packages:
            if package in requirements:
                print(f"✅ {package} in requirements.txt")
            else:
                print(f"❌ {package} missing from requirements.txt")
                return False
        
    except Exception as e:
        print(f"❌ Requirements test failed: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("🧪 Testing Enhanced Property Search Application")
    print("=" * 50)
    
    tests = [
        test_file_structure,
        test_imports,
        test_export_functions,
        test_requirements
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The enhanced application is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

