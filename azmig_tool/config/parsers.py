"""  
Unified Configuration Parser - Parse CSV/JSON/Excel files for Azure migration configurations
Supports:
- Landing Zone: CSV/JSON files with Azure Migrate project configurations
- Servers: Excel files with individual machine migration configurations
"""
import csv
import json
import pandas as pd
from pathlib import Path
from typing import List, Tuple, Union
from rich.console import Console

from ..models import (
    MigrationConfig,
    MigrateProjectConfig,
    ConsolidatedMigrationConfig,
    ValidationResult,
    ValidationStage
)
from ..constants import (
    LANDING_ZONE_CSV_COLUMNS,
    LANDING_ZONE_OPTIONAL_COLUMNS,
    SERVERS_REQUIRED_COLUMNS,
    SERVERS_OPTIONAL_COLUMNS,
    SERVERS_COLUMN_MAPPING,
    CONSOLIDATED_REQUIRED_COLUMNS,
    CONSOLIDATED_OPTIONAL_COLUMNS,
    CONSOLIDATED_COLUMN_MAPPING,
    # Backward compatibility
    LAYER1_CSV_COLUMNS,
    LAYER1_OPTIONAL_COLUMNS,
    LAYER2_REQUIRED_COLUMNS,
    LAYER2_OPTIONAL_COLUMNS,
    LAYER2_COLUMN_MAPPING
)

console = Console()


class ConfigParser:
    """
    Unified configuration parser for Azure migration tool

    Supports:
    - CSV/JSON for Landing Zone project configurations
    - Excel for Servers migration configurations
    """

    def __init__(self, config_path: str):
        """
        Initialize parser

        Args:
            config_path: Path to configuration file (CSV/JSON/Excel)
        """
        self.config_path = Path(config_path)
        self.file_type = self._detect_file_type()
        self.df = None  # For Excel parsing

    def _detect_file_type(self) -> str:
        """
        Detect configuration file type

        Returns:
            'csv', 'json', 'excel', or 'unknown'
        """
        suffix = self.config_path.suffix.lower()
        if suffix == '.csv':
            return 'csv'
        elif suffix == '.json':
            return 'json'
        elif suffix in ['.xlsx', '.xls']:
            return 'excel'
        else:
            return 'unknown'

    def validate_file_exists(self) -> ValidationResult:
        """Validate configuration file exists"""
        if not self.config_path.exists():
            return ValidationResult(
                stage=ValidationStage.EXCEL_STRUCTURE,
                passed=False,
                message=f"Configuration file not found: {self.config_path}"
            )

        if self.file_type == 'unknown':
            return ValidationResult(
                stage=ValidationStage.EXCEL_STRUCTURE,
                passed=False,
                message=f"Unsupported file format: {self.config_path.suffix}. Use .csv, .json, or .xlsx"
            )

        return ValidationResult(
            stage=ValidationStage.EXCEL_STRUCTURE,
            passed=True,
            message=f"Configuration file found: {self.config_path.name}"
        )

    # ========================================
    # Layer 1: Landing Zone Configuration (CSV/JSON)
    # ========================================

    def parse_layer1_csv(self) -> Tuple[bool, List[MigrateProjectConfig], str]:
        """
        Parse CSV configuration file for Layer 1 (Landing Zone)

        Returns:
            Tuple of (success, configs, error_message)
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                # Validate headers
                if not reader.fieldnames:
                    return False, [], "CSV file has no headers"

                # Strip whitespace from headers
                headers = [h.strip() for h in reader.fieldnames]

                missing_cols = [
                    col for col in LANDING_ZONE_CSV_COLUMNS if col not in headers]
                if missing_cols:
                    return False, [], f"Missing required columns: {', '.join(missing_cols)}"

                # Parse rows
                configs = []
                for idx, row in enumerate(reader, start=2):
                    try:
                        # Strip whitespace from values
                        row = {k.strip(): v.strip() if v else "" for k,
                               v in row.items()}

                        config = MigrateProjectConfig(
                            subscription_id=row.get("Subscription ID", ""),
                            migrate_project_name=row.get(
                                "Migrate Project Name", ""),
                            appliance_type=row.get("Appliance Type", "Other"),
                            appliance_name=row.get("Appliance Name", ""),
                            region=row.get("Region", ""),
                            cache_storage_account=row.get(
                                "Cache Storage Account", ""),
                            cache_storage_resource_group=row.get(
                                "Cache Storage Resource Group", ""),
                            migrate_project_subscription=row.get(
                                "Migrate Project Subscription", ""),
                            migrate_resource_group=row.get(
                                "Migrate Resource Group", ""),
                            recovery_vault_name=row.get(
                                "Recovery Vault Name", None) or None
                        )

                        # Validate required fields
                        if not config.subscription_id:
                            console.print(
                                f"[yellow]⚠ Row {idx}: Missing Subscription ID, skipping[/yellow]")
                            continue

                        if not config.migrate_project_name:
                            console.print(
                                f"[yellow]⚠ Row {idx}: Missing Migrate Project Name, skipping[/yellow]")
                            continue

                        configs.append(config)

                    except Exception as e:
                        console.print(
                            f"[red]✗ Row {idx}: Error parsing - {str(e)}[/red]")
                        continue

                if not configs:
                    return False, [], "No valid configuration rows found"

                return True, configs, f"Parsed {len(configs)} project configurations"

        except Exception as e:
            return False, [], f"Error reading CSV file: {str(e)}"

    def parse_layer1_json(self) -> Tuple[bool, List[MigrateProjectConfig], str]:
        """
        Parse JSON configuration file for Layer 1 (Landing Zone)

        Returns:
            Tuple of (success, configs, error_message)
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Support both array and object with "projects" key
            if isinstance(data, dict) and "projects" in data:
                projects = data["projects"]
            elif isinstance(data, list):
                projects = data
            else:
                return False, [], "JSON must be an array or object with 'projects' key"

            configs = []
            for idx, proj in enumerate(projects, start=1):
                try:
                    config = MigrateProjectConfig(
                        subscription_id=proj.get("subscription_id", ""),
                        migrate_project_name=proj.get(
                            "migrate_project_name", ""),
                        appliance_type=proj.get("appliance_type", "Other"),
                        appliance_name=proj.get("appliance_name", ""),
                        region=proj.get("region", ""),
                        cache_storage_account=proj.get(
                            "cache_storage_account", ""),
                        cache_storage_resource_group=proj.get(
                            "cache_storage_resource_group", ""),
                        migrate_project_subscription=proj.get(
                            "migrate_project_subscription", ""),
                        migrate_resource_group=proj.get(
                            "migrate_resource_group", ""),
                        recovery_vault_name=proj.get(
                            "recovery_vault_name", None)
                    )

                    # Validate required fields
                    if not config.subscription_id:
                        console.print(
                            f"[yellow]⚠ Project {idx}: Missing subscription_id, skipping[/yellow]")
                        continue

                    if not config.migrate_project_name:
                        console.print(
                            f"[yellow]⚠ Project {idx}: Missing migrate_project_name, skipping[/yellow]")
                        continue

                    configs.append(config)

                except Exception as e:
                    console.print(
                        f"[red]✗ Project {idx}: Error parsing - {str(e)}[/red]")
                    continue

            if not configs:
                return False, [], "No valid project configurations found"

            return True, configs, f"Parsed {len(configs)} project configurations"

        except json.JSONDecodeError as e:
            return False, [], f"Invalid JSON format: {str(e)}"
        except Exception as e:
            return False, [], f"Error reading JSON file: {str(e)}"

    def parse_landing_zone(self) -> Tuple[bool, List[MigrateProjectConfig], str]:
        """
        Parse Landing Zone configuration file (auto-detect CSV/JSON)

        Returns:
            Tuple of (success, configs, message)
        """
        # Check file exists
        validation = self.validate_file_exists()
        if not validation.passed:
            return False, [], validation.message

        # Parse based on extension
        if self.file_type == 'csv':
            return self.parse_layer1_csv()
        elif self.file_type == 'json':
            return self.parse_layer1_json()
        else:
            return False, [], f"Unsupported Landing Zone file format: {self.config_path.suffix}. Use .csv or .json"

    # Backward compatibility alias
    def parse_layer1(self) -> Tuple[bool, List[MigrateProjectConfig], str]:
        """
        Alternative name for parse_landing_zone() - Parse Layer 1 (Landing Zone) configuration

        Returns:
            Tuple of (success, list of configs, error message)
        """
        return self.parse_landing_zone()

    def save_layer1_csv(self, configs: List[MigrateProjectConfig], output_path: str) -> bool:
        """
        Save Layer 1 configurations to CSV file

        Args:
            configs: List of project configurations
            output_path: Output CSV file path

        Returns:
            True if successful
        """
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(
                    f, fieldnames=LANDING_ZONE_CSV_COLUMNS + LANDING_ZONE_OPTIONAL_COLUMNS)
                writer.writeheader()

                for config in configs:
                    writer.writerow({
                        "Subscription ID": config.subscription_id,
                        "Migrate Project Name": config.migrate_project_name,
                        "Appliance Type": config.appliance_type,
                        "Appliance Name": config.appliance_name,
                        "Region": config.region,
                        "Cache Storage Account": config.cache_storage_account,
                        "Cache Storage Resource Group": config.cache_storage_resource_group,
                        "Migrate Project Subscription": config.migrate_project_subscription,
                        "Migrate Resource Group": config.migrate_resource_group,
                        "Recovery Vault Name": config.recovery_vault_name or ""
                    })

            console.print(
                f"[green]✓ Saved {len(configs)} configurations to {output_path}[/green]")
            return True

        except Exception as e:
            console.print(f"[red]✗ Error saving CSV: {str(e)}[/red]")
            return False

    def save_layer1_json(self, configs: List[MigrateProjectConfig], output_path: str) -> bool:
        """
        Save Layer 1 configurations to JSON file

        Args:
            configs: List of project configurations
            output_path: Output JSON file path

        Returns:
            True if successful
        """
        try:
            data = {
                "projects": [
                    {
                        "subscription_id": c.subscription_id,
                        "migrate_project_name": c.migrate_project_name,
                        "appliance_type": c.appliance_type,
                        "appliance_name": c.appliance_name,
                        "region": c.region,
                        "cache_storage_account": c.cache_storage_account,
                        "cache_storage_resource_group": c.cache_storage_resource_group,
                        "migrate_project_subscription": c.migrate_project_subscription,
                        "migrate_resource_group": c.migrate_resource_group,
                        "recovery_vault_name": c.recovery_vault_name
                    }
                    for c in configs
                ]
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            console.print(
                f"[green]✓ Saved {len(configs)} configurations to {output_path}[/green]")
            return True

        except Exception as e:
            console.print(f"[red]✗ Error saving JSON: {str(e)}[/red]")
            return False

    # ========================================
    # Layer 2: Machine Configuration (Excel)
    # ========================================

    def validate_layer2_structure(self) -> Tuple[ValidationResult, pd.DataFrame]:
        """Validate Excel structure for Layer 2 (Machine) and return DataFrame"""
        try:
            # Read Excel file
            self.df = pd.read_excel(self.config_path)

            # Check for empty file
            if self.df.empty:
                return ValidationResult(
                    stage=ValidationStage.EXCEL_STRUCTURE,
                    passed=False,
                    message="Excel file is empty"
                ), None

            # Strip spaces from column names
            self.df.columns = self.df.columns.str.strip()

            # Check required columns
            missing_cols = [col for col in SERVERS_REQUIRED_COLUMNS
                            if col not in self.df.columns]

            if missing_cols:
                return ValidationResult(
                    stage=ValidationStage.EXCEL_STRUCTURE,
                    passed=False,
                    message=f"Missing required columns: {', '.join(missing_cols)}",
                    details={"missing_columns": missing_cols}
                ), None

            # Rename columns to internal format using mapping
            self.df = self.df.rename(columns=SERVERS_COLUMN_MAPPING)

            # Check for duplicate machine names
            duplicates = self.df[self.df.duplicated(
                subset=['machine_name'], keep=False)]
            if not duplicates.empty:
                dup_names = duplicates['machine_name'].tolist()
                return ValidationResult(
                    stage=ValidationStage.EXCEL_STRUCTURE,
                    passed=False,
                    message=f"Duplicate Target Machine found: {', '.join(map(str, dup_names))}",
                    details={"duplicate_names": dup_names}
                ), None

            # Get list of internal required column names
            required_internal = [SERVERS_COLUMN_MAPPING[col]
                                 for col in SERVERS_REQUIRED_COLUMNS]

            # Check for null values in required columns
            null_check = self.df[required_internal].isnull().sum()
            cols_with_nulls = null_check[null_check > 0]

            if not cols_with_nulls.empty:
                return ValidationResult(
                    stage=ValidationStage.EXCEL_STRUCTURE,
                    passed=False,
                    message=f"Null values found in required columns: {dict(cols_with_nulls)}",
                    details={"null_columns": dict(cols_with_nulls)}
                ), None

            return ValidationResult(
                stage=ValidationStage.EXCEL_STRUCTURE,
                passed=True,
                message=f"Excel structure validated successfully ({len(self.df)} records)",
                details={"record_count": len(self.df)}
            ), self.df

        except Exception as e:
            return ValidationResult(
                stage=ValidationStage.EXCEL_STRUCTURE,
                passed=False,
                message=f"Error reading Excel file: {str(e)}"
            ), None

    def parse_layer2_configs(self) -> List[MigrationConfig]:
        """Parse DataFrame to list of MigrationConfig objects for Layer 2"""
        if self.df is None:
            raise ValueError(
                "Excel file not loaded. Call validate_layer2_structure() first.")

        configs = []
        errors = []

        for idx, row in self.df.iterrows():
            try:
                config = MigrationConfig(
                    machine_name=str(
                        row['machine_name']).strip(),
                    target_region=str(row['target_region']).strip(),
                    target_subscription=str(
                        row['target_subscription']).strip(),
                    target_rg=str(row['target_rg']).strip(),
                    target_vnet=str(row['target_vnet']).strip(),
                    target_subnet=str(row['target_subnet']).strip(),
                    target_machine_sku=str(row['target_machine_sku']).strip(),
                    target_disk_type=str(row['target_disk_type']).strip(),
                    migrate_project_name=str(
                        row['migrate_project_name']).strip()
                )
                configs.append(config)
            except ValueError as e:
                errors.append(f"Row {idx + 2}: {str(e)}")
                console.print(f"[yellow]⚠ Row {idx + 2}: {str(e)}[/yellow]")

        if errors:
            console.print(
                f"\n[red]Found {len(errors)} configuration errors.[/red]")
            for error in errors[:5]:  # Show first 5 errors
                console.print(f"  [red]• {error}[/red]")
            if len(errors) > 5:
                console.print(f"  [red]... and {len(errors) - 5} more[/red]")

        return configs

    def parse_servers(self) -> Tuple[bool, List[MigrationConfig], List[ValidationResult]]:
        """
        Complete validation and parsing workflow for Servers (Machine).

        Returns:
            Tuple of (success, configs, validation_results)
        """
        validation_results = []

        # Step 1: Check file exists
        file_result = self.validate_file_exists()
        validation_results.append(file_result)
        if not file_result.passed:
            return False, [], validation_results

        # Step 2: Validate structure
        structure_result, df = self.validate_layer2_structure()
        validation_results.append(structure_result)
        if not structure_result.passed:
            return False, [], validation_results

        # Step 3: Parse to configs
        try:
            configs = self.parse_layer2_configs()
            if not configs:
                validation_results.append(
                    ValidationResult(
                        stage=ValidationStage.EXCEL_STRUCTURE,
                        passed=False,
                        message="No valid configurations parsed from Excel"
                    )
                )
                return False, [], validation_results

            return True, configs, validation_results

        except Exception as e:
            validation_results.append(
                ValidationResult(
                    stage=ValidationStage.EXCEL_STRUCTURE,
                    passed=False,
                    message=f"Error parsing configurations: {str(e)}"
                )
            )
            return False, [], validation_results

    def validate_consolidated_structure(self) -> Tuple[ValidationResult, pd.DataFrame]:
        """Validate Excel structure for consolidated template (LZ + Servers) and return DataFrame"""
        try:
            # Read Excel file
            self.df = pd.read_excel(self.config_path)

            # Check for empty file
            if self.df.empty:
                return ValidationResult(
                    stage=ValidationStage.EXCEL_STRUCTURE,
                    passed=False,
                    message="Excel file is empty"
                ), None

            # Strip spaces from column names
            self.df.columns = self.df.columns.str.strip()

            # Check required columns
            missing_cols = [col for col in CONSOLIDATED_REQUIRED_COLUMNS
                            if col not in self.df.columns]

            if missing_cols:
                return ValidationResult(
                    stage=ValidationStage.EXCEL_STRUCTURE,
                    passed=False,
                    message=f"Missing required columns: {', '.join(missing_cols)}",
                    details={"missing_columns": missing_cols}
                ), None

            # Rename columns to internal format using mapping
            self.df = self.df.rename(columns=CONSOLIDATED_COLUMN_MAPPING)

            # Check for duplicate machine names
            duplicates = self.df[self.df.duplicated(
                subset=['machine_name'], keep=False)]
            if not duplicates.empty:
                dup_names = duplicates['machine_name'].tolist()
                return ValidationResult(
                    stage=ValidationStage.EXCEL_STRUCTURE,
                    passed=False,
                    message=f"Duplicate Target Machine found: {', '.join(map(str, dup_names))}",
                    details={"duplicate_names": dup_names}
                ), None

            # Get list of internal required column names
            required_internal = [CONSOLIDATED_COLUMN_MAPPING[col]
                                 for col in CONSOLIDATED_REQUIRED_COLUMNS]

            # Check for null values in required columns
            null_check = self.df[required_internal].isnull().sum()
            cols_with_nulls = null_check[null_check > 0]

            if not cols_with_nulls.empty:
                return ValidationResult(
                    stage=ValidationStage.EXCEL_STRUCTURE,
                    passed=False,
                    message=f"Null values found in required columns: {dict(cols_with_nulls)}",
                    details={"null_columns": dict(cols_with_nulls)}
                ), None

            return ValidationResult(
                stage=ValidationStage.EXCEL_STRUCTURE,
                passed=True,
                message=f"Consolidated Excel structure validated successfully ({len(self.df)} records)",
                details={"record_count": len(self.df)}
            ), self.df

        except Exception as e:
            return ValidationResult(
                stage=ValidationStage.EXCEL_STRUCTURE,
                passed=False,
                message=f"Error reading Excel file: {str(e)}"
            ), None

    def parse_consolidated_configs(self) -> List[ConsolidatedMigrationConfig]:
        """Parse DataFrame to list of ConsolidatedMigrationConfig objects"""
        if self.df is None:
            raise ValueError(
                "Excel file not loaded. Call validate_consolidated_structure() first.")

        configs = []
        errors = []

        for idx, row in self.df.iterrows():
            try:
                config = ConsolidatedMigrationConfig(
                    # Landing Zone fields
                    migrate_project_subscription=str(
                        row['migrate_project_subscription']).strip(),
                    migrate_project_name=str(
                        row['migrate_project_name']).strip(),
                    appliance_type=str(row['appliance_type']).strip(),
                    appliance_name=str(row['appliance_name']).strip(),
                    cache_storage_account=str(
                        row['cache_storage_account']).strip(),
                    cache_storage_resource_group=str(
                        row['cache_storage_resource_group']).strip(),
                    migrate_resource_group=str(
                        row['migrate_resource_group']).strip(),

                    # Server fields
                    machine_name=str(
                        row['machine_name']).strip(),
                    target_region=str(row['target_region']).strip(),
                    target_subscription=str(
                        row['target_subscription']).strip(),
                    target_rg=str(row['target_rg']).strip(),
                    target_vnet=str(row['target_vnet']).strip(),
                    target_subnet=str(row['target_subnet']).strip(),
                    target_machine_sku=str(row['target_machine_sku']).strip(),
                    target_disk_type=str(row['target_disk_type']).strip()
                )
                configs.append(config)
            except ValueError as e:
                row_number = int(idx) + 2 if isinstance(idx, int) else idx
                errors.append(f"Row {row_number}: {str(e)}")
                console.print(f"[yellow]⚠ Row {row_number}: {str(e)}[/yellow]")

        if errors:
            console.print(
                f"\n[red]Found {len(errors)} configuration errors.[/red]")
            for error in errors[:5]:  # Show first 5 errors
                console.print(f"  [red]• {error}[/red]")
            if len(errors) > 5:
                console.print(f"  [red]... and {len(errors) - 5} more[/red]")

        return configs

    def parse_consolidated(self) -> Tuple[bool, List[ConsolidatedMigrationConfig], List[ValidationResult]]:
        """
        Complete validation and parsing workflow for consolidated template (LZ + Servers).

        Returns:
            Tuple of (success, configs, validation_results)
        """
        validation_results = []

        # Step 1: Check file exists
        file_result = self.validate_file_exists()
        validation_results.append(file_result)
        if not file_result.passed:
            return False, [], validation_results

        # Step 2: Validate structure
        structure_result, df = self.validate_consolidated_structure()
        validation_results.append(structure_result)
        if not structure_result.passed:
            return False, [], validation_results

        # Step 3: Parse to configs
        try:
            configs = self.parse_consolidated_configs()
            if not configs:
                validation_results.append(
                    ValidationResult(
                        stage=ValidationStage.EXCEL_STRUCTURE,
                        passed=False,
                        message="No valid configurations parsed from Excel"
                    )
                )
                return False, [], validation_results

            return True, configs, validation_results

        except Exception as e:
            validation_results.append(
                ValidationResult(
                    stage=ValidationStage.EXCEL_STRUCTURE,
                    passed=False,
                    message=f"Error parsing configurations: {str(e)}"
                )
            )
            return False, [], validation_results

    # Backward compatibility alias
    def parse_layer2(self) -> Tuple[bool, List[MigrationConfig], List[ValidationResult]]:
        """
        Alternative name for parse_servers() - Parse Layer 2 (Machine) configuration

        Returns:
            Tuple of (success, list of configs, validation results)
        """
        return self.parse_servers()

    # ========================================
    # Auto-detect and Parse
    # ========================================

    def detect_excel_format(self) -> str:
        """
        Auto-detect Excel format (consolidated vs. servers-only)

        Returns:
            'consolidated' if it has both LZ and server columns
            'servers' if it has only server columns
            'unknown' if it doesn't match either format
        """
        if self.file_type != 'excel':
            return 'unknown'

        try:
            # Read Excel file to check columns
            df = pd.read_excel(self.config_path)
            if df.empty:
                return 'unknown'

            # Strip spaces from column names
            columns = [col.strip() for col in df.columns]

            # Check for consolidated format (has both LZ and server columns)
            # First 7 are LZ columns
            lz_cols_present = sum(
                1 for col in CONSOLIDATED_REQUIRED_COLUMNS[:7] if col in columns)
            # Rest are server columns
            server_cols_present = sum(
                1 for col in CONSOLIDATED_REQUIRED_COLUMNS[7:] if col in columns)

            # If it has most LZ columns (5+ out of 7) and server columns, it's consolidated
            if lz_cols_present >= 5 and server_cols_present >= 6:
                return 'consolidated'

            # Check for traditional server format (has server columns but few/no LZ columns)
            server_traditional = sum(
                1 for col in SERVERS_REQUIRED_COLUMNS if col in columns)
            if server_traditional >= 6 and lz_cols_present <= 2:
                return 'servers'

            return 'unknown'

        except Exception:
            return 'unknown'

    def parse(self) -> Tuple[bool, Union[List[MigrateProjectConfig], List[MigrationConfig], List[ConsolidatedMigrationConfig]], Union[str, List[ValidationResult]]]:
        """
        Auto-detect file type and parse accordingly

        Returns:
            For Landing Zone (CSV/JSON): Tuple of (success, List[MigrateProjectConfig], message)
            For Servers (Excel): Tuple of (success, List[MigrationConfig], validation_results) 
            For Consolidated (Excel): Tuple of (success, List[ConsolidatedMigrationConfig], validation_results)
        """
        if self.file_type in ['csv', 'json']:
            return self.parse_landing_zone()
        elif self.file_type == 'excel':
            excel_format = self.detect_excel_format()

            if excel_format == 'consolidated':
                console.print(
                    "[cyan]Detected consolidated Excel template (Landing Zone + Servers)[/cyan]")
                return self.parse_consolidated()
            elif excel_format == 'servers':
                console.print(
                    "[cyan]Detected traditional server Excel template[/cyan]")
                return self.parse_servers()
            else:
                return False, [], [ValidationResult(
                    stage=ValidationStage.EXCEL_STRUCTURE,
                    passed=False,
                    message="Excel file format not recognized. Please use consolidated template with both Landing Zone and Server columns, or traditional server template."
                )]
        else:
            return False, [], f"Unsupported file format: {self.config_path.suffix}"


# ========================================
# Backward Compatibility Aliases
# ========================================

class Layer1ConfigParser(ConfigParser):
    """
    Alias for ConfigParser - Landing Zone configuration parser

    This class provides backward compatibility. Use ConfigParser or
    LandingZoneConfigParser for new code.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def parse(self) -> Tuple[bool, List[MigrateProjectConfig], str]:
        """Parse Landing Zone configuration"""
        return self.parse_landing_zone()

    def save_csv(self, configs: List[MigrateProjectConfig], output_path: str) -> bool:
        """Save to CSV"""
        return self.save_layer1_csv(configs, output_path)

    def save_json(self, configs: List[MigrateProjectConfig], output_path: str) -> bool:
        """Save to JSON"""
        return self.save_layer1_json(configs, output_path)


class ExcelParser(ConfigParser):
    """
    Alias for ConfigParser - Servers Excel parser

    This class provides backward compatibility. Use ConfigParser for new code.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def validate_structure(self) -> Tuple[ValidationResult, pd.DataFrame]:
        """Validate Excel structure"""
        return self.validate_layer2_structure()

    def parse_to_configs(self) -> List[MigrationConfig]:
        """Parse to configs"""
        return self.parse_layer2_configs()

    def validate_and_parse(self) -> Tuple[bool, List[MigrationConfig], List[ValidationResult]]:
        """Validate and parse"""
        return self.parse_servers()
