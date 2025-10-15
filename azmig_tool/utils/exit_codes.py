"""
Exit code constants and management for Azure Migration Tool
Provides standardized exit codes for different failure scenarios
"""
import sys
from enum import IntEnum
from rich.console import Console

console = Console()


class ExitCode(IntEnum):
    """Standard exit codes for the Azure Migration Tool"""
    
    # Success
    SUCCESS = 0
    
    # Configuration & Input Errors (1-10)
    GENERAL_ERROR = 1
    CONFIG_FILE_ERROR = 2
    INVALID_ARGUMENTS = 3
    FILE_NOT_FOUND = 4
    UNSUPPORTED_FILE_FORMAT = 5
    EXCEL_STRUCTURE_ERROR = 6
    
    # Authentication Errors (11-20)
    AUTH_FAILED = 11
    SUBSCRIPTION_NOT_FOUND = 12
    PERMISSION_DENIED = 13
    TOKEN_EXPIRED = 14
    
    # Validation Errors (21-30)
    VALIDATION_FAILED = 21
    LANDING_ZONE_FAILED = 22
    SERVER_VALIDATION_FAILED = 23
    CRITICAL_VALIDATION_FAILED = 24
    ALL_VALIDATIONS_FAILED = 25
    
    # Azure API Errors (31-40)
    AZURE_API_ERROR = 31
    RESOURCE_NOT_FOUND = 32
    QUOTA_EXCEEDED = 33
    API_THROTTLED = 34
    NETWORK_ERROR = 35
    
    # System Errors (41-50)
    TIMEOUT_ERROR = 41
    MEMORY_ERROR = 42
    DISK_SPACE_ERROR = 43
    PERMISSION_ERROR = 44
    
    # User Interruption (128+)
    USER_CANCELLED = 130  # Standard for Ctrl+C


class ExitManager:
    """Manages application exit with proper codes and messaging"""
    
    @staticmethod
    def exit_with_code(exit_code: ExitCode, message: str = "", details: str = ""):
        """Exit application with proper code and user message"""
        
        if exit_code != ExitCode.SUCCESS:
            console.print(f"\n[red]❌ Operation Failed (Exit Code: {exit_code.value})[/red]")
            if message:
                console.print(f"[yellow]Reason:[/yellow] {message}")
            if details:
                console.print(f"[dim]Details:[/dim] {details}")
            
            # Provide troubleshooting hints based on exit code
            troubleshooting = ExitManager._get_troubleshooting_hint(exit_code)
            if troubleshooting:
                console.print(f"\n[cyan]💡 Troubleshooting Hint:[/cyan]\n{troubleshooting}")
        
        sys.exit(exit_code.value)
    
    @staticmethod
    def _get_troubleshooting_hint(exit_code: ExitCode) -> str:
        """Get troubleshooting hint for specific exit code"""
        
        hints = {
            ExitCode.CONFIG_FILE_ERROR: "• Check file path and permissions\n• Validate file format (CSV/JSON/Excel)\n• Ensure required columns are present",
            
            ExitCode.AUTH_FAILED: "• Run 'az login' for Azure CLI authentication\n• Check service principal credentials\n• Verify tenant ID and subscription access",
            
            ExitCode.SUBSCRIPTION_NOT_FOUND: "• Verify subscription ID is correct\n• Check if you have access to the subscription\n• Ensure subscription is not disabled",
            
            ExitCode.PERMISSION_DENIED: "• Request Contributor role on target resources\n• Ensure Reader access on subscription\n• Check Azure Migrate project permissions",
            
            ExitCode.VALIDATION_FAILED: "• Review validation details above\n• Check Azure resource configurations\n• Use --debug for detailed error information",
            
            ExitCode.AZURE_API_ERROR: "• Check network connectivity to Azure\n• Verify service availability status\n• Try again after a short wait (rate limiting)",
            
            ExitCode.TIMEOUT_ERROR: "• Increase timeout with --timeout parameter\n• Check network connectivity\n• Try validating fewer resources at once"
        }
        
        return hints.get(exit_code, "• Check logs for detailed error information\n• Run with --debug for verbose output")
    
    @staticmethod
    def handle_keyboard_interrupt():
        """Handle Ctrl+C gracefully"""
        console.print("\n[yellow]⚠ Operation cancelled by user[/yellow]")
        sys.exit(ExitCode.USER_CANCELLED.value)
    
    @staticmethod
    def handle_critical_error(error: Exception, context: str = ""):
        """Handle unexpected critical errors"""
        console.print(f"\n[red]💥 Critical Error[/red]")
        console.print(f"[red]Error:[/red] {str(error)}")
        if context:
            console.print(f"[dim]Context:[/dim] {context}")
        
        console.print(f"\n[yellow]Please report this error with the following information:[/yellow]")
        console.print(f"[dim]Error Type:[/dim] {type(error).__name__}")
        console.print(f"[dim]Error Details:[/dim] {str(error)}")
        if context:
            console.print(f"[dim]Context:[/dim] {context}")
        
        sys.exit(ExitCode.GENERAL_ERROR.value)


def validate_exit_on_failure(validation_results: list, operation_type: str = "validation"):
    """Check validation results and exit with appropriate code if failures found"""
    
    if not validation_results:
        ExitManager.exit_with_code(
            ExitCode.VALIDATION_FAILED,
            "No validation results found",
            "The validation process did not return any results"
        )
    
    failed_results = [r for r in validation_results if hasattr(r, 'passed') and not r.passed]
    critical_failures = [r for r in failed_results if hasattr(r, 'stage') and 
                        r.stage in ['EXCEL_STRUCTURE', 'AZURE_REGION', 'SUBSCRIPTION_ACCESS']]
    
    if critical_failures:
        ExitManager.exit_with_code(
            ExitCode.CRITICAL_VALIDATION_FAILED,
            f"Critical {operation_type} failures detected",
            f"{len(critical_failures)} critical validation(s) failed"
        )
    
    if failed_results:
        # Determine appropriate exit code based on failure type
        if len(failed_results) == len(validation_results):
            exit_code = ExitCode.ALL_VALIDATIONS_FAILED
        elif operation_type == "landing_zone":
            exit_code = ExitCode.LANDING_ZONE_FAILED  
        elif operation_type == "server":
            exit_code = ExitCode.SERVER_VALIDATION_FAILED
        else:
            exit_code = ExitCode.VALIDATION_FAILED
            
        ExitManager.exit_with_code(
            exit_code,
            f"{operation_type.title()} validation failed",
            f"{len(failed_results)} of {len(validation_results)} validations failed"
        )