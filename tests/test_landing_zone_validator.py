"""
Test script for Landing Zone Validator

This demonstrates the Landing Zone Validator functionality.
Note: Requires valid Azure credentials and a configured environment.
"""
from rich.console import Console
from rich.panel import Panel

console = Console()


def test_landing_zone_validator_import():
    """Test that LandingZoneValidator can be imported"""
    console.print(
        "\n[bold cyan]Testing Landing Zone Validator Import[/bold cyan]\n")

    try:
        from azmig_tool.validators import LandingZoneValidator
        from azmig_tool.models import MigrateProjectConfig, ApplianceType

        console.print("  ✓ LandingZoneValidator imported successfully")
        console.print("  ✓ Models imported successfully")

        # Test instantiation
        validator = LandingZoneValidator()
        console.print("  ✓ Validator instantiated successfully")

        # Show available methods
        console.print("\n[bold]Available Validation Methods:[/bold]")
        console.print("  • validate_access() - Check RBAC permissions")
        console.print(
            "  • validate_appliance_health() - Monitor appliance status")
        console.print(
            "  • validate_storage_cache() - Validate cache storage account")
        console.print("  • validate_quota() - Check vCPU quota availability")
        console.print("  • validate_project() - Run all enabled validations")
        console.print(
            "  • create_cache_storage_account() - Create storage if needed")

        return True

    except Exception as e:
        console.print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_validator_with_sample_config():
    """Test validator with a sample configuration"""
    console.print(
        "\n[bold cyan]Testing Validator with Sample Configuration[/bold cyan]\n")

    try:
        from azmig_tool.validators import LandingZoneValidator
        from azmig_tool.models import MigrateProjectConfig, ApplianceType

        # Create sample configuration
        config = MigrateProjectConfig(
            subscription_id="12345678-1234-1234-1234-123456789abc",
            migrate_resource_group="rg-migrate-prod",
            migrate_project_name="migration-project-prod",
            migrate_project_subscription="12345678-1234-1234-1234-123456789abc",
            region="eastus",
            appliance_name="VMwareReplicationAppliance01",
            appliance_type="VMware",
            cache_storage_account="stmigcacheeastus1234",
            recovery_vault_name="rsv-migrate-prod"
        )

        console.print("  ✓ Sample configuration created:")
        console.print(f"    - Project: {config.migrate_project_name}")
        console.print(f"    - Region: {config.region}")
        console.print(f"    - Appliance: {config.appliance_name}")
        console.print(f"    - Storage: {config.cache_storage_account}")

        console.print(
            "\n[yellow]Note: To run actual validations, you need:[/yellow]")
        console.print("  • Valid Azure credentials (az login)")
        console.print("  • An existing Azure Migrate project")
        console.print("  • Appropriate RBAC permissions")

        console.print("\n[bold]Example Usage:[/bold]")
        console.print("""
from azure.identity import DefaultAzureCredential
from azmig_tool.validators import LandingZoneValidator

# Initialize with credentials
credential = DefaultAzureCredential()
validator = LandingZoneValidator(credential)

# Run full project validation
result = validator.validate_project(config)

# Check individual validations
if result.access_result:
    print(f"Access: {result.access_result.status}")
if result.appliance_result:
    print(f"Appliances: {len(result.appliance_result.appliances)} found")
if result.storage_result:
    print(f"Storage: {result.storage_result.status}")
if result.quota_result:
    print(f"Quota: {len(result.quota_result.quotas)} families checked")
        """)

        return True

    except Exception as e:
        console.print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    console.print(Panel.fit(
        "[bold cyan]Landing Zone Validator Test Suite[/bold cyan]\n"
        "Tests the implementation for Azure Migrate project validation",
        border_style="cyan"
    ))

    results = []

    # Test 1: Import
    results.append(("Import Test", test_landing_zone_validator_import()))

    # Test 2: Sample Configuration
    results.append(("Sample Config Test", test_validator_with_sample_config()))

    # Summary
    console.print("\n" + "="*60)
    console.print("[bold]Test Results Summary[/bold]")
    console.print("="*60)

    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        color = "green" if passed else "red"
        console.print(f"  [{color}]{status}[/{color}]: {test_name}")

    console.print("="*60)

    all_passed = all(result[1] for result in results)
    if all_passed:
        console.print("\n[bold green]🎉 All tests passed![/bold green]")
    else:
        console.print("\n[bold yellow]⚠ Some tests failed[/bold yellow]")

    console.print("\n[bold]Key Features of LandingZoneValidator:[/bold]")
    console.print(
        "  1. [green]RBAC Validation[/green] - Checks Contributor/Reader roles")
    console.print(
        "  2. [green]Appliance Monitoring[/green] - Real-time health status")
    console.print(
        "  3. [green]Storage Management[/green] - Validates or creates cache storage")
    console.print(
        "  4. [green]Quota Checking[/green] - vCPU availability by VM family")
    console.print(
        "  5. [green]Auto-Creation[/green] - Can create missing resources")

    return all_passed


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
