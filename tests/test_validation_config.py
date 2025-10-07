"""
Test validation configuration system

This test verifies that validation checks can be enabled/disabled via configuration
"""

from rich.console import Console
from rich.table import Table
from azmig_tool.config.validation_config import (
    ValidationConfigLoader,
    ValidationConfig,
    get_validation_config,
    reset_validation_config
)
import yaml
import os
import tempfile

console = Console()


def test_default_config():
    """Test that default configuration enables all validations"""
    console.print("\n[bold cyan]TEST 1: Default Configuration[/bold cyan]")

    reset_validation_config()
    config = get_validation_config()

    table = Table(title="Default Config - Landing Zone Validations")
    table.add_column("Validation", style="cyan")
    table.add_column("Enabled", style="green")

    table.add_row("Access Validation",
                  "✓" if config.is_access_validation_enabled() else "✗")
    table.add_row("Appliance Health",
                  "✓" if config.is_appliance_health_enabled() else "✗")
    table.add_row("Storage Cache",
                  "✓" if config.is_storage_cache_enabled() else "✗")
    table.add_row("Quota Validation",
                  "✓" if config.is_quota_validation_enabled() else "✗")

    console.print(table)

    table2 = Table(title="Default Config - Servers Validations")
    table2.add_column("Validation", style="cyan")
    table2.add_column("Enabled", style="green")

    table2.add_row(
        "Region", "✓" if config.is_region_validation_enabled() else "✗")
    table2.add_row(
        "Resource Group", "✓" if config.is_resource_group_validation_enabled() else "✗")
    table2.add_row(
        "VNet/Subnet", "✓" if config.is_vnet_subnet_validation_enabled() else "✗")
    table2.add_row(
        "VM SKU", "✓" if config.is_vm_sku_validation_enabled() else "✗")
    table2.add_row(
        "Disk Type", "✓" if config.is_disk_type_validation_enabled() else "✗")
    table2.add_row(
        "Discovery", "✓" if config.is_discovery_validation_enabled() else "✗")
    table2.add_row(
        "RBAC", "✓" if config.is_servers_rbac_validation_enabled() else "✗")

    console.print(table2)

    # Verify all are enabled by default
    assert config.is_access_validation_enabled() == True
    assert config.is_appliance_health_enabled() == True
    assert config.is_region_validation_enabled() == True
    assert config.is_servers_rbac_validation_enabled() == True

    console.print(
        "[green]✓ PASSED[/green]: All validations enabled by default\n")


def test_custom_config_disabled():
    """Test custom configuration with some validations disabled"""
    console.print(
        "[bold cyan]TEST 2: Custom Config - Disabled Validations[/bold cyan]")

    # Create custom config with some validations disabled
    custom_config = {
        "landing_zone": {
            "access_validation": {"enabled": True},
            "appliance_health": {"enabled": False},  # Disabled
            "storage_cache": {"enabled": True},
            "quota_validation": {"enabled": False}  # Disabled
        },
        "servers": {
            "region_validation": {"enabled": True},
            "resource_group_validation": {"enabled": True},
            "vnet_subnet_validation": {"enabled": False},  # Disabled
            "vm_sku_validation": {"enabled": True},
            "disk_type_validation": {"enabled": True},
            "discovery_validation": {"enabled": False},  # Disabled
            "rbac_validation": {"enabled": True}
        },
        "active_profile": "default"
    }

    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(custom_config, f)
        temp_path = f.name

    try:
        # Load custom config
        reset_validation_config()
        config = get_validation_config(temp_path)

        table = Table(title="Custom Config Status")
        table.add_column("Validation", style="cyan")
        table.add_column("Status", style="yellow")

        table.add_row("Access Validation",
                      "✓ Enabled" if config.is_access_validation_enabled() else "✗ Disabled")
        table.add_row("Appliance Health",
                      "✓ Enabled" if config.is_appliance_health_enabled() else "✗ Disabled")
        table.add_row("Quota Validation",
                      "✓ Enabled" if config.is_quota_validation_enabled() else "✗ Disabled")
        table.add_row(
            "VNet/Subnet", "✓ Enabled" if config.is_vnet_subnet_validation_enabled() else "✗ Disabled")
        table.add_row(
            "Discovery", "✓ Enabled" if config.is_discovery_validation_enabled() else "✗ Disabled")

        console.print(table)

        # Verify disabled validations
        assert config.is_appliance_health_enabled() == False
        assert config.is_quota_validation_enabled() == False
        assert config.is_vnet_subnet_validation_enabled() == False
        assert config.is_discovery_validation_enabled() == False

        # Verify enabled validations
        assert config.is_access_validation_enabled() == True
        assert config.is_region_validation_enabled() == True

        console.print(
            "[green]✓ PASSED[/green]: Custom config correctly disables validations\n")

    finally:
        # Cleanup
        os.unlink(temp_path)


def test_validation_profile():
    """Test validation profiles"""
    console.print("[bold cyan]TEST 3: Validation Profiles[/bold cyan]")

    # Create config with profiles
    config_with_profiles = {
        "landing_zone": {
            "access_validation": {"enabled": True},
            "appliance_health": {"enabled": True},
            "storage_cache": {"enabled": True},
            "quota_validation": {"enabled": True}
        },
        "servers": {
            "region_validation": {"enabled": True},
            "resource_group_validation": {"enabled": True},
            "vnet_subnet_validation": {"enabled": True},
            "vm_sku_validation": {"enabled": True},
            "disk_type_validation": {"enabled": True},
            "discovery_validation": {"enabled": True},
            "rbac_validation": {"enabled": True}
        },
        "profiles": {
            "quick": {
                "description": "Quick validation",
                "overrides": {
                    "landing_zone.appliance_health.enabled": False,
                    "landing_zone.quota_validation.enabled": False,
                    "servers.discovery_validation.enabled": False
                }
            }
        },
        "active_profile": "quick"
    }

    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_with_profiles, f)
        temp_path = f.name

    try:
        # Load with quick profile
        reset_validation_config()
        config = get_validation_config(temp_path)

        table = Table(title="Quick Profile - Disabled Checks")
        table.add_column("Validation", style="cyan")
        table.add_column("Status", style="yellow")

        table.add_row("Appliance Health",
                      "✗ Disabled" if not config.is_appliance_health_enabled() else "✓ Enabled")
        table.add_row("Quota Validation",
                      "✗ Disabled" if not config.is_quota_validation_enabled() else "✓ Enabled")
        table.add_row(
            "Discovery", "✗ Disabled" if not config.is_discovery_validation_enabled() else "✓ Enabled")

        console.print(table)

        # Verify quick profile disables time-consuming checks
        assert config.is_appliance_health_enabled() == False
        assert config.is_quota_validation_enabled() == False
        assert config.is_discovery_validation_enabled() == False

        # Verify other checks still enabled
        assert config.is_access_validation_enabled() == True
        assert config.is_region_validation_enabled() == True

        console.print(
            "[green]✓ PASSED[/green]: Quick profile correctly applied\n")

    finally:
        # Cleanup
        os.unlink(temp_path)


def test_granular_rbac_controls():
    """Test granular RBAC validation controls"""
    console.print("[bold cyan]TEST 4: Granular RBAC Controls[/bold cyan]")

    # Create config with granular RBAC controls
    custom_config = {
        "landing_zone": {
            "access_validation": {
                "enabled": True,
                "checks": {
                    "migrate_project_rbac": {"enabled": True},
                    "recovery_vault_rbac": {"enabled": False},  # Disabled
                    "subscription_rbac": {"enabled": True}
                }
            }
        },
        "active_profile": "default"
    }

    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(custom_config, f)
        temp_path = f.name

    try:
        # Load custom config
        reset_validation_config()
        config = get_validation_config(temp_path)

        table = Table(title="Granular RBAC Controls")
        table.add_column("RBAC Check", style="cyan")
        table.add_column("Status", style="yellow")

        table.add_row("Migrate Project RBAC",
                      "✓ Enabled" if config.is_migrate_project_rbac_enabled() else "✗ Disabled")
        table.add_row("Recovery Vault RBAC",
                      "✓ Enabled" if config.is_recovery_vault_rbac_enabled() else "✗ Disabled")
        table.add_row("Subscription RBAC",
                      "✓ Enabled" if config.is_subscription_rbac_enabled() else "✗ Disabled")

        console.print(table)

        # Verify granular controls
        assert config.is_migrate_project_rbac_enabled() == True
        assert config.is_recovery_vault_rbac_enabled() == False
        assert config.is_subscription_rbac_enabled() == True

        console.print(
            "[green]✓ PASSED[/green]: Granular RBAC controls work correctly\n")

    finally:
        # Cleanup
        os.unlink(temp_path)


def run_all_tests():
    """Run all configuration tests"""
    console.rule(
        "[bold green]Validation Configuration System Tests[/bold green]")

    try:
        test_default_config()
        test_custom_config_disabled()
        test_validation_profile()
        test_granular_rbac_controls()

        console.rule("[bold green]ALL TESTS PASSED ✓[/bold green]")

    except AssertionError as e:
        console.print(f"[bold red]TEST FAILED ✗[/bold red]")
        console.print(f"[red]Error: {e}[/red]")
        raise
    except Exception as e:
        console.print(f"[bold red]TEST ERROR ✗[/bold red]")
        console.print(f"[red]Error: {e}[/red]")
        raise


if __name__ == "__main__":
    run_all_tests()
