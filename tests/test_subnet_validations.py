"""
Test Enhanced Subnet Validations

Tests for:
1. IP availability validation (Azure reserved IPs + usage)
2. Subnet delegation validation (SQL MI, App Service, etc.)
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from azmig_tool.models import MigrationConfig
from azmig_tool.mock.servers_validator import MockServersValidator


def test_successful_subnet_validation():
    """Test subnet with sufficient IPs and no delegation"""
    print("\n" + "=" * 80)
    print("TEST 1: Successful Subnet Validation")
    print("=" * 80)
    
    validator = MockServersValidator(success_rate=1.0)
    
    config = MigrationConfig(
        target_machine_name="test-vm-01",
        target_region="East US",
        target_subscription="sub-123",
        target_rg="rg-migration",
        target_vnet="vnet-prod",
        target_subnet="subnet-servers",  # Normal subnet
        target_machine_sku="Standard_D4s_v3",
        target_disk_type="Premium_LRS"
    )
    
    result = validator.validate_vnet_and_subnet(config)
    
    print(f"✓ Passed: {result.passed}")
    print(f"✓ Message: {result.message}")
    print(f"✓ Details:")
    for key, value in result.details.items():
        print(f"  - {key}: {value}")
    
    assert result.passed, "Expected subnet validation to pass"
    assert "Available IPs" in result.message
    assert result.details.get("is_delegated") == False
    assert result.details.get("available_ips") > 0
    
    print("\n✓ TEST 1 PASSED\n")


def test_delegated_subnet_failure():
    """Test subnet delegated to SQL Managed Instance"""
    print("\n" + "=" * 80)
    print("TEST 2: Delegated Subnet (SQL Managed Instance)")
    print("=" * 80)
    
    validator = MockServersValidator(success_rate=1.0)
    
    config = MigrationConfig(
        target_machine_name="test-vm-02",
        target_region="East US",
        target_subscription="sub-123",
        target_rg="rg-migration",
        target_vnet="vnet-prod",
        target_subnet="subnet-delegated-sqlmi",  # Delegated subnet
        target_machine_sku="Standard_D4s_v3",
        target_disk_type="Premium_LRS"
    )
    
    result = validator.validate_vnet_and_subnet(config)
    
    print(f"✗ Passed: {result.passed}")
    print(f"✗ Message: {result.message}")
    print(f"✗ Details:")
    for key, value in result.details.items():
        print(f"  - {key}: {value}")
    
    assert not result.passed, "Expected delegated subnet validation to fail"
    assert "delegated" in result.message.lower()
    assert result.details.get("is_delegated") == True
    assert result.details.get("delegation_service") == "Microsoft.Sql/managedInstances"
    
    print("\n✓ TEST 2 PASSED\n")


def test_full_subnet_failure():
    """Test subnet with no available IPs"""
    print("\n" + "=" * 80)
    print("TEST 3: Full Subnet (No Available IPs)")
    print("=" * 80)
    
    validator = MockServersValidator(success_rate=1.0)
    
    config = MigrationConfig(
        target_machine_name="test-vm-03",
        target_region="East US",
        target_subscription="sub-123",
        target_rg="rg-migration",
        target_vnet="vnet-prod",
        target_subnet="subnet-full",  # Full subnet
        target_machine_sku="Standard_D4s_v3",
        target_disk_type="Premium_LRS"
    )
    
    result = validator.validate_vnet_and_subnet(config)
    
    print(f"✗ Passed: {result.passed}")
    print(f"✗ Message: {result.message}")
    print(f"✗ Details:")
    for key, value in result.details.items():
        print(f"  - {key}: {value}")
    
    assert not result.passed, "Expected full subnet validation to fail"
    assert "insufficient" in result.message.lower() or "available: 0" in result.message.lower()
    assert result.details.get("available_ips") == 0
    assert result.details.get("azure_reserved_ips") == 5
    
    print("\n✓ TEST 3 PASSED\n")


def test_ip_calculation():
    """Test IP calculation logic"""
    print("\n" + "=" * 80)
    print("TEST 4: IP Calculation Verification")
    print("=" * 80)
    
    validator = MockServersValidator(success_rate=1.0)
    
    config = MigrationConfig(
        target_machine_name="test-vm-04",
        target_region="East US",
        target_subscription="sub-123",
        target_rg="rg-migration",
        target_vnet="vnet-prod",
        target_subnet="subnet-servers",
        target_machine_sku="Standard_D4s_v3",
        target_disk_type="Premium_LRS"
    )
    
    result = validator.validate_vnet_and_subnet(config)
    
    # Verify IP calculation
    total = result.details.get("total_ips", 0)
    reserved = result.details.get("azure_reserved_ips", 0)
    used = result.details.get("used_ips", 0)
    available = result.details.get("available_ips", 0)
    
    print(f"IP Calculation:")
    print(f"  Total IPs:     {total}")
    print(f"  Azure Reserved: {reserved}")
    print(f"  Used IPs:      {used}")
    print(f"  Available:     {available}")
    print(f"  Formula:       {total} - {reserved} - {used} = {available}")
    
    # Verify calculation
    expected_available = total - reserved - used
    assert available == expected_available, f"IP calculation incorrect: expected {expected_available}, got {available}"
    assert reserved == 5, "Azure should reserve 5 IPs"
    
    print("\n✓ TEST 4 PASSED\n")


def test_invalid_subnet():
    """Test non-existent subnet"""
    print("\n" + "=" * 80)
    print("TEST 5: Invalid Subnet")
    print("=" * 80)
    
    validator = MockServersValidator(success_rate=1.0)
    
    config = MigrationConfig(
        target_machine_name="test-vm-05",
        target_region="East US",
        target_subscription="sub-123",
        target_rg="rg-migration",
        target_vnet="vnet-prod",
        target_subnet="subnet-invalid",  # Invalid subnet
        target_machine_sku="Standard_D4s_v3",
        target_disk_type="Premium_LRS"
    )
    
    result = validator.validate_vnet_and_subnet(config)
    
    print(f"✗ Passed: {result.passed}")
    print(f"✗ Message: {result.message}")
    
    assert not result.passed, "Expected invalid subnet validation to fail"
    assert "not found" in result.message.lower()
    
    print("\n✓ TEST 5 PASSED\n")


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("ENHANCED SUBNET VALIDATION TESTS")
    print("=" * 80)
    
    tests = [
        ("Successful Subnet Validation", test_successful_subnet_validation),
        ("Delegated Subnet Failure", test_delegated_subnet_failure),
        ("Full Subnet Failure", test_full_subnet_failure),
        ("IP Calculation Verification", test_ip_calculation),
        ("Invalid Subnet", test_invalid_subnet)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n✗ TEST FAILED: {name}")
            print(f"  Error: {e}")
            failed += 1
        except Exception as e:
            print(f"\n✗ TEST ERROR: {name}")
            print(f"  Exception: {e}")
            failed += 1
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {len(tests)}")
    print(f"✓ Passed: {passed}")
    print(f"✗ Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        return 0
    else:
        print(f"\n⚠️  {failed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    exit(main())
