#!/usr/bin/env python3
import argparse
import sys
from rich.console import Console

from ..core.core import run_migration_tool
from ..utils.exit_codes import ExitManager, ExitCode

console = Console()


def main():
    parser = argparse.ArgumentParser(
        prog="azmig",
        description="Azure Bulk Migration CLI - Migrate servers from DC to Azure (interactive wizard with Azure integration)"
    )

    # Authentication options (optional - interactive prompts available)
    parser.add_argument(
        "--auth-method",
        type=str,
        choices=["azure_cli", "managed_identity", "service_principal",
                 "interactive", "device_code", "default"],
        help="Authentication method (optional - will prompt if not specified)"
    )
    parser.add_argument(
        "--tenant-id",
        type=str,
        help="Azure tenant ID (optional for service principal)"
    )
    parser.add_argument(
        "--client-id",
        type=str,
        help="Azure client ID (optional for service principal/managed identity)"
    )
    parser.add_argument(
        "--client-secret",
        type=str,
        help="Azure client secret (optional for service principal)"
    )

    # Project management options
    parser.add_argument(
        "--project-name",
        type=str,
        help="Project name (for new projects or selecting existing)"
    )
    parser.add_argument(
        "--project-folder",
        type=str,
        help="Project folder path (optional - defaults to migration_projects/)"
    )

    # Operation options (optional - will prompt if not provided)
    parser.add_argument(
        "--operation",
        type=str,
        choices=["lz_validation", "server_validation",
                 "replication", "configure_validations", "full_wizard"],
        help="Operation type (optional - will prompt if not specified)"
    )
    parser.add_argument(
        "--excel",
        type=str,
        help="Path to Excel mapping file (optional - will prompt if needed)"
    )
    parser.add_argument(
        "--lz-file",
        type=str,
        help="Path to Landing Zone CSV/JSON file (optional - will prompt if needed)"
    )

    # Export and configuration options
    parser.add_argument(
        "--export-json",
        type=str,
        help="Export results to JSON file (optional)"
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Disable interactive prompts (all parameters must be provided via CLI)"
    )

    args = parser.parse_args()

    # Always run with Azure integration
    console.print("\n[bold cyan]🛠️  Azure Bulk Migration Tool[/bold cyan]")
    console.print("[dim]Azure Integration[/dim]\n")

    # Gather parameters from CLI args
    provided_params = {
        'auth_method': args.auth_method,
        'tenant_id': args.tenant_id,
        'client_id': args.client_id,
        'client_secret': args.client_secret,
        'operation': args.operation,
        'excel': args.excel,
        'lz_file': args.lz_file,
        'export_json': args.export_json,
        'project_name': args.project_name,
        'project_folder': args.project_folder
    }

    # Use interactive prompts if not in non-interactive mode
    if not args.non_interactive:
        # If no operation provided, go directly to wizard's project-first workflow
        if not args.operation:
            params = provided_params  # Skip operation prompt, let wizard handle project selection
        else:
            from .interactive_prompts import get_interactive_inputs
            params = get_interactive_inputs("azure", provided_params)
    else:
        # Non-interactive mode - require all necessary parameters
        params = provided_params

        # Validate required parameters for non-interactive mode
        if not params['auth_method']:
            ExitManager.exit_with_code(
                ExitCode.INVALID_ARGUMENTS,
                "--auth-method required in non-interactive mode",
                "Specify authentication method: azure_cli, managed_identity, service_principal, interactive, or default"
            )

        if not params['operation']:
            ExitManager.exit_with_code(
                ExitCode.INVALID_ARGUMENTS,
                "--operation required in non-interactive mode",
                "Specify operation: lz_validation, server_validation, replication, or full_wizard"
            )

    # Handle configure_validations operation
    if params.get('operation') == 'configure_validations':
        console.print("\n[green]✓[/green] Validation configuration complete!")
        return

    # Always run with Azure integration with proper error handling
    try:
        run_migration_tool(
            excel_path=params.get('excel'),
            export_json=params.get('export_json'),
            validation_config_path=params.get('validation_config'),
            validation_profile=params.get('validation_profile'),
            auth_method=params.get('auth_method'),
            tenant_id=params.get('tenant_id'),
            client_id=params.get('client_id'),
            client_secret=params.get('client_secret'),
            operation=params.get('operation'),
            lz_file=params.get('lz_file'),
            project_name=params.get('project_name'),
            project_folder=params.get('project_folder')
        )
        # If we get here, operation completed successfully
        sys.exit(ExitCode.SUCCESS.value)
        
    except KeyboardInterrupt:
        ExitManager.handle_keyboard_interrupt()
    except FileNotFoundError as e:
        ExitManager.exit_with_code(
            ExitCode.FILE_NOT_FOUND,
            f"Required file not found: {str(e)}",
            "Check file paths and ensure all required files exist"
        )
    except Exception as e:
        ExitManager.handle_critical_error(e, "CLI execution")


if __name__ == '__main__':
    main()
