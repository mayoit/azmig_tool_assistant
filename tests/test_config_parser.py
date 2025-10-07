"""
Test unified configuration parser
Tests both Layer 1 (CSV/JSON) and Layer 2 (Excel) parsing with backward compatibility
"""
from azmig_tool.config.parsers import ConfigParser, ExcelParser
from azmig_tool.config import LandingZoneConfigParser as Layer1ConfigParser


def test_unified_parser_layer1():
    """Test unified parser with Layer 1 CSV"""
    print("\n" + "="*80)
    print("TEST 1: Unified ConfigParser with Layer 1 CSV")
    print("="*80)

    parser = ConfigParser("tests/data/sample_migrate_projects.csv")
    success, configs, message = parser.parse()

    print(f"✓ File type detected: {parser.file_type}")
    print(f"✓ Parse result: {message}")
    print(f"✓ Projects loaded: {len(configs)}")

    if configs:
        print(f"\nFirst project:")
        print(f"  - Name: {configs[0].migrate_project_name}")
        print(f"  - Region: {configs[0].region}")
        print(f"  - Appliance: {configs[0].appliance_type_enum.value}")

    assert success, "Layer 1 CSV parsing should succeed"
    assert len(configs) == 3, "Should parse 3 projects"
    print("✅ PASSED\n")


def test_unified_parser_layer1_json():
    """Test unified parser with Layer 1 JSON"""
    print("="*80)
    print("TEST 2: Unified ConfigParser with Layer 1 JSON")
    print("="*80)

    parser = ConfigParser("tests/data/sample_migrate_projects.json")
    success, configs, message = parser.parse()

    print(f"✓ File type detected: {parser.file_type}")
    print(f"✓ Parse result: {message}")
    print(f"✓ Projects loaded: {len(configs)}")

    if configs:
        print(f"\nFirst project:")
        print(f"  - Name: {configs[0].migrate_project_name}")
        print(f"  - Region: {configs[0].region}")

    assert success, "Layer 1 JSON parsing should succeed"
    assert len(configs) == 3, "Should parse 3 projects"
    print("✅ PASSED\n")


def test_unified_parser_layer2():
    """Test unified parser with Layer 2 Excel"""
    print("="*80)
    print("TEST 3: Unified ConfigParser with Layer 2 Excel")
    print("="*80)

    parser = ConfigParser("tests/data/sample_migration.xlsx")
    success, configs, validation_results = parser.parse()

    print(f"✓ File type detected: {parser.file_type}")
    print(f"✓ Validation results: {len(validation_results)}")
    print(f"✓ Machines loaded: {len(configs)}")

    if configs:
        print(f"\nFirst machine:")
        print(f"  - Name: {configs[0].target_machine_name}")
        print(f"  - Region: {configs[0].target_region}")
        print(f"  - SKU: {configs[0].target_machine_sku}")

    assert success, "Layer 2 Excel parsing should succeed"
    assert len(configs) > 0, "Should parse at least one machine"
    print("✅ PASSED\n")


def test_backward_compatibility_layer1():
    """Test backward compatibility with Layer1ConfigParser"""
    print("="*80)
    print("TEST 4: Backward Compatibility - Layer1ConfigParser")
    print("="*80)

    parser = Layer1ConfigParser("tests/data/sample_migrate_projects.csv")
    success, configs, message = parser.parse()

    print(f"✓ Using Layer1ConfigParser (backward compatible)")
    print(f"✓ Parse result: {message}")
    print(f"✓ Projects loaded: {len(configs)}")

    assert success, "Layer1ConfigParser should work"
    assert len(configs) == 3, "Should parse 3 projects"
    print("✅ PASSED\n")


def test_backward_compatibility_excel():
    """Test backward compatibility with ExcelParser"""
    print("="*80)
    print("TEST 5: Backward Compatibility - ExcelParser")
    print("="*80)

    parser = ExcelParser("tests/data/sample_migration.xlsx")
    success, configs, validation_results = parser.validate_and_parse()

    print(f"✓ Using ExcelParser (backward compatible)")
    print(f"✓ Validation results: {len(validation_results)}")
    print(f"✓ Machines loaded: {len(configs)}")

    assert success, "ExcelParser should work"
    assert len(configs) > 0, "Should parse machines"
    print("✅ PASSED\n")


if __name__ == "__main__":
    print("\n" + "╔" + "═"*78 + "╗")
    print("║" + " "*20 + "Unified Configuration Parser Tests" + " "*24 + "║")
    print("╚" + "═"*78 + "╝")

    try:
        test_unified_parser_layer1()
        test_unified_parser_layer1_json()
        test_unified_parser_layer2()
        test_backward_compatibility_layer1()
        test_backward_compatibility_excel()

        print("╔" + "═"*78 + "╗")
        print("║" + " "*25 + "ALL TESTS PASSED! ✅" + " "*33 + "║")
        print("╚" + "═"*78 + "╝\n")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        raise
