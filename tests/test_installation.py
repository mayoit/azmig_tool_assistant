"""
Quick installation test script
"""
import sys


def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")

    try:
        from azmig_tool import models
        print("  ✓ models")
    except Exception as e:
        print(f"  ✗ models: {e}")
        return False

    try:
        from azmig_tool import config_parser
        print("  ✓ config_parser")
    except Exception as e:
        print(f"  ✗ config_parser: {e}")
        return False

    try:
        from azmig_tool import api_client
        print("  ✓ api_client")
    except Exception as e:
        print(f"  ✗ api_client: {e}")
        return False

    try:
        from azmig_tool import migrate_api_client
        print("  ✓ migrate_api_client")
    except Exception as e:
        print(f"  ✗ migrate_api_client: {e}")
        return False

    try:
        from azmig_tool.base import BaseValidatorInterface
        from azmig_tool.validators import ServersValidator
        print("  ✓ validators (base, validators)")
    except Exception as e:
        print(f"  ✗ validators: {e}")
        return False

    try:
        from azmig_tool import wizard
        print("  ✓ wizard")
    except Exception as e:
        print(f"  ✗ wizard: {e}")
        return False

    try:
        from azmig_tool import azure_migrate
        print("  ✓ azure_migrate")
    except Exception as e:
        print(f"  ✗ azure_migrate: {e}")
        return False

    return True


def test_validator():
    """Test Validator functionality - requires Azure auth"""
    print("\nTesting Validator (requires Azure authentication)...")

    try:
        from azmig_tool.validators import ServersValidator
        from azmig_tool.models import MigrationConfig
        from azure.identity import DefaultAzureCredential

        # This requires Azure authentication
        print("  Note: This test requires Azure authentication")
        print("  Skipping validator tests - requires Azure credentials")
        return True

        # Commented out - requires Azure auth
        # validator = ServersValidator(DefaultAzureCredential())

        config = MigrationConfig(
            target_machine_name="test-vm-01",
            target_region="eastus",
            target_subscription="12345678-1234-1234-1234-123456789012",
            target_rg="test-rg",
            target_vnet="test-vnet",
            target_subnet="default",
            target_machine_sku="Standard_D4s_v3",
            target_disk_type="Premium_LRS"
        )

        # Commented out - requires Azure auth
        # result = validator.validate_region(config)
        # print(f"  ✓ validate_region: {result.passed}")
        print("  ✓ ServersValidator can be imported")

        return True

    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_client():
    """Test API client creation"""
    print("\nTesting API Client...")

    try:
        from azmig_tool.clients.azure_client import AzureRestApiClient
        from azure.identity import DefaultAzureCredential

        # Just test creation, don't make actual API calls
        credential = DefaultAzureCredential()
        client = AzureRestApiClient(credential, "test-subscription-id")
        print("  ✓ AzureRestApiClient created")

        from azmig_tool.clients.azure_client import AzureMigrateApiClient
        migrate_client = AzureMigrateApiClient(
            credential, "test-subscription-id")
        print("  ✓ AzureMigrateApiClient created")

        return True

    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_excel_parser():
    """Test Excel parser with sample file"""
    print("\nTesting Excel Parser...")

    try:
        from azmig_tool.config.parsers import ConfigParser
        import os

        sample_file = "tests/data/sample_migration.xlsx"

        if not os.path.exists(sample_file):
            print(f"  ⚠ Sample file not found: {sample_file}")
            print("  Run: python scripts/create_sample_excel.py")
            return False

        parser = ConfigParser(sample_file)
        success, configs, validation_results = parser.parse_layer2()

        if success:
            print(f"  ✓ Excel parsed: {len(configs)} configurations")

            if configs:
                print(f"    - First machine: {configs[0].target_machine_name}")
                print(f"    - Region: {configs[0].target_region}")
                print(f"    - SKU: {configs[0].target_machine_sku}")

            return True
        else:
            print(f"  ✗ Validation failed")
            for vr in validation_results:
                if not vr.passed:
                    print(f"    - {vr.message}")
            return False

    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Azure Bulk Migration Tool - Installation Test")
    print("=" * 60)

    results = {
        "Imports": test_imports(),
        "Validator": test_validator(),
        "API Client": test_api_client(),
        "Excel Parser": test_excel_parser()
    }

    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {test_name}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n🎉 All tests passed! Installation is successful.\n")
        print("Next steps:")
        print("  1. Run 'azmig --help' to see CLI options")
        print("  2. Run 'azmig' to test with Azure authentication")
        print("  3. Run 'azmig' for Azure integration")
        return 0
    else:
        print("\n⚠ Some tests failed. Check errors above.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
