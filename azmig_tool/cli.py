#!/usr/bin/env python3
import argparse
from rich.console import Console

from .modes.mock_mode import run_mock_mode
from .modes.live_mode import run_live_mode

console = Console()


def main():
    parser = argparse.ArgumentParser(
        prog="azmig",
        description="Azure Bulk Migration CLI - Migrate servers from DC to Azure (interactive wizard by default)"
    )

    # Mode selection
    parser.add_argument(
        "--live",
        action="store_true",
        help="Run in live Azure mode with interactive prompts (requires Azure authentication)"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run in mock mode with interactive prompts for offline testing"
    )

    # Authentication options (optional - will prompt if not provided in live mode)
    parser.add_argument(
        "--auth-method",
        type=str,
        choices=["azure_cli", "managed_identity", "service_principal",
                 "interactive", "device_code", "default"],
        help="Authentication method for live mode (optional - will prompt if not specified)"
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
        "--validation-config",
        type=str,
        help="Path to validation configuration YAML file (optional - will prompt)"
    )
    parser.add_argument(
        "--validation-profile",
        type=str,
        choices=["default", "full", "quick", "rbac_only", "resource_only"],
        help="Use a predefined validation profile (optional - will prompt)"
    )

    # Utility options
    parser.add_argument(
        "--create-default-config",
        action="store_true",
        help="Create a default validation_config.yaml file and exit"
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Disable interactive prompts (all parameters must be provided via CLI)"
    )

    args = parser.parse_args()

    # Handle config file creation
    if args.create_default_config:
        from .config.validation_config import ValidationConfigLoader
        try:
            config_path = ValidationConfigLoader.create_default_config()
            console.print(
                f"[green]SUCCESS[/green] Created default validation config: {config_path}")
        except FileExistsError as e:
            console.print(f"[yellow]WARNING[/yellow] {e}")
        return

    # Determine mode (default to interactive if neither --live nor --mock specified)
    if not args.live and not args.mock:
        # Show welcome and let user choose mode
        console.print("\n[bold cyan]🛠️  Azure Bulk Migration Tool[/bold cyan]")
        console.print("[dim]Interactive Wizard Mode[/dim]\n")

        from rich.prompt import Prompt
        mode_choice = Prompt.ask(
            "[cyan]Select mode[/cyan]",
            choices=["live", "mock"],
            default="live"
        )
        mode = mode_choice
    else:
        mode = "live" if args.live and not args.mock else "mock"

    console.print(f"\n[bold]Mode:[/bold] {mode.upper()}\n")

    # Gather parameters from CLI args
    provided_params = {
        'operation': args.operation,
        'excel': args.excel,
        'lz_file': args.lz_file,
        'export_json': args.export_json,
        'validation_config': args.validation_config,
        'validation_profile': args.validation_profile,
        'auth_method': args.auth_method,
        'tenant_id': args.tenant_id,
        'client_id': args.client_id,
        'client_secret': args.client_secret
    }

    # Use interactive prompts if not in non-interactive mode
    if not args.non_interactive:
        from .interactive_prompts import get_interactive_inputs
        params = get_interactive_inputs(mode, provided_params)
    else:
        # Non-interactive mode - require all necessary parameters
        params = provided_params

        # Validate required parameters for non-interactive mode
        if mode == "live" and not params['auth_method']:
            console.print(
                "[red]✗[/red] --auth-method required in non-interactive mode")
            return

        if not params['operation']:
            console.print(
                "[red]✗[/red] --operation required in non-interactive mode")
            return

    # Handle configure_validations operation
    if params.get('operation') == 'configure_validations':
        console.print("\n[green]✓[/green] Validation configuration complete!")
        return

    # Run appropriate mode
    if mode == "mock":
        run_mock_mode(
            excel_path=params.get('excel'),
            export_json=params.get('export_json'),
            validation_config_path=params.get('validation_config'),
            validation_profile=params.get('validation_profile'),
            operation=params.get('operation'),
            lz_file=params.get('lz_file')
        )
    else:
        run_live_mode(
            excel_path=params.get('excel'),
            export_json=params.get('export_json'),
            validation_config_path=params.get('validation_config'),
            validation_profile=params.get('validation_profile'),
            auth_method=params.get('auth_method'),
            tenant_id=params.get('tenant_id'),
            client_id=params.get('client_id'),
            client_secret=params.get('client_secret'),
            operation=params.get('operation'),
            lz_file=params.get('lz_file')
        )


if __name__ == '__main__':
    main()
