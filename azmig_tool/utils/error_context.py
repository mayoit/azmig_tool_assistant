"""
Enhanced error handling system for Azure Migration Tool
Provides contextual error messages with troubleshooting guidance
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()


class ErrorCategory(str, Enum):
    """Categories of errors for better organization"""
    CONFIGURATION = "configuration"
    AUTHENTICATION = "authentication" 
    AZURE_API = "azure_api"
    VALIDATION = "validation"
    NETWORK = "network"
    PERMISSION = "permission"
    RESOURCE = "resource"
    SYSTEM = "system"


@dataclass
class ErrorContext:
    """Enhanced error context with troubleshooting information"""
    error_code: str
    category: ErrorCategory
    title: str
    description: str
    user_action: str
    technical_details: Optional[Dict[str, Any]] = None
    related_errors: Optional[List[str]] = None
    documentation_links: Optional[List[str]] = None
    azure_trace_id: Optional[str] = None
    
    def display(self):
        """Display formatted error with troubleshooting guidance"""
        
        # Main error panel
        error_content = f"[bold red]{self.title}[/bold red]\n\n"
        error_content += f"{self.description}\n\n"
        error_content += f"[cyan]💡 What to do next:[/cyan]\n{self.user_action}"
        
        console.print(Panel(
            error_content,
            title=f"[red]❌ {self.category.value.title()} Error ({self.error_code})[/red]",
            border_style="red",
            expand=False
        ))
        
        # Technical details table
        if self.technical_details:
            details_table = Table(title="Technical Details", box=box.SIMPLE)
            details_table.add_column("Property", style="cyan")
            details_table.add_column("Value", style="dim")
            
            for key, value in self.technical_details.items():
                details_table.add_row(key, str(value))
            
            if self.azure_trace_id:
                details_table.add_row("Azure Trace ID", self.azure_trace_id)
            
            console.print(details_table)
        
        # Related errors
        if self.related_errors:
            console.print("\n[yellow]⚠ Related Issues:[/yellow]")
            for related in self.related_errors:
                console.print(f"  • {related}")
        
        # Documentation links
        if self.documentation_links:
            console.print("\n[cyan]📖 Helpful Resources:[/cyan]")
            for link in self.documentation_links:
                console.print(f"  • {link}")


class ErrorContextBuilder:
    """Builds contextual error information based on error patterns"""
    
    # Common error patterns and their contexts
    ERROR_PATTERNS = {
        # Authentication Errors
        "subscription_not_found": ErrorContext(
            error_code="AUTH001",
            category=ErrorCategory.AUTHENTICATION,
            title="Subscription Not Found",
            description="The specified Azure subscription could not be found or accessed.",
            user_action="1. Verify the subscription ID is correct\n2. Run 'az account list' to see available subscriptions\n3. Ensure you have access to the subscription\n4. Check if the subscription is active (not disabled)",
            documentation_links=["https://docs.microsoft.com/en-us/azure/azure-resource-manager/troubleshooting/error-not-found"]
        ),
        
        "invalid_credentials": ErrorContext(
            error_code="AUTH002", 
            category=ErrorCategory.AUTHENTICATION,
            title="Authentication Failed",
            description="The provided credentials are invalid or expired.",
            user_action="1. Run 'az login' to refresh Azure CLI credentials\n2. Check service principal credentials (tenant ID, client ID, secret)\n3. Verify the authentication method is supported\n4. Ensure your account is not locked or disabled",
            documentation_links=["https://docs.microsoft.com/en-us/cli/azure/authenticate-azure-cli"]
        ),
        
        "token_expired": ErrorContext(
            error_code="AUTH003",
            category=ErrorCategory.AUTHENTICATION,
            title="Access Token Expired",
            description="Your authentication token has expired and needs to be refreshed.",
            user_action="1. Run 'az login' to get a new token\n2. If using service principal, check credential expiration\n3. Restart the application after re-authentication",
            related_errors=["Authentication may fail intermittently", "API calls may return 401 errors"]
        ),
        
        # Permission Errors
        "insufficient_permissions": ErrorContext(
            error_code="PERM001",
            category=ErrorCategory.PERMISSION,
            title="Insufficient Permissions",
            description="You don't have the required permissions to perform this operation.",
            user_action="1. Request 'Contributor' role on target resource groups\n2. Ensure 'Reader' access on the subscription\n3. For Azure Migrate: Request 'Azure Migrate Project Contributor' role\n4. For Recovery Services: Request access to Recovery Services vault",
            documentation_links=[
                "https://docs.microsoft.com/en-us/azure/migrate/migrate-support-matrix#required-permissions",
                "https://docs.microsoft.com/en-us/azure/role-based-access-control/built-in-roles"
            ]
        ),
        
        "rbac_assignment_failed": ErrorContext(
            error_code="PERM002",
            category=ErrorCategory.PERMISSION,
            title="RBAC Role Assignment Failed",
            description="Could not verify or assign required RBAC roles.",
            user_action="1. Check if you have 'User Access Administrator' role\n2. Verify role assignments using Azure Portal\n3. Request an administrator to grant required permissions\n4. Use 'az role assignment list' to verify current roles",
            related_errors=["May affect resource group validation", "Recovery vault access may be limited"]
        ),
        
        # Azure API Errors
        "resource_not_found": ErrorContext(
            error_code="API001",
            category=ErrorCategory.AZURE_API,
            title="Azure Resource Not Found",
            description="The specified Azure resource could not be found.",
            user_action="1. Verify resource names and IDs are correct\n2. Check if the resource exists in the specified region\n3. Ensure the resource hasn't been deleted\n4. Verify subscription and resource group names",
            related_errors=["Resource may have been moved or renamed", "Wrong subscription or resource group specified"]
        ),
        
        "api_throttled": ErrorContext(
            error_code="API002", 
            category=ErrorCategory.AZURE_API,
            title="Azure API Throttling",
            description="Too many requests have been made to the Azure API. The service is temporarily limiting requests.",
            user_action="1. Wait a few minutes and try again\n2. Reduce the number of concurrent operations\n3. Use batch processing for large datasets\n4. Consider using exponential backoff retry logic",
            related_errors=["Multiple validation failures may occur", "Performance may be degraded"]
        ),
        
        "api_service_unavailable": ErrorContext(
            error_code="API003",
            category=ErrorCategory.AZURE_API,
            title="Azure Service Unavailable", 
            description="The Azure service is temporarily unavailable.",
            user_action="1. Check Azure Service Health: https://status.azure.com\n2. Wait and retry the operation\n3. Try a different Azure region if possible\n4. Report persistent issues to Azure Support",
            documentation_links=["https://status.azure.com", "https://docs.microsoft.com/en-us/azure/azure-monitor/platform/service-notifications"]
        ),
        
        # Configuration Errors
        "excel_structure_invalid": ErrorContext(
            error_code="CONF001",
            category=ErrorCategory.CONFIGURATION,
            title="Invalid Excel File Structure",
            description="The Excel file doesn't match the expected template structure.",
            user_action="1. Download the latest Excel template\n2. Check required column names (case-sensitive)\n3. Ensure all required columns are present\n4. Verify data types in each column\n5. Remove empty rows at the end of the file",
            related_errors=["Column mapping may fail", "Data parsing errors may occur"]
        ),
        
        "missing_required_fields": ErrorContext(
            error_code="CONF002",
            category=ErrorCategory.CONFIGURATION,
            title="Missing Required Fields",
            description="One or more required fields are missing or empty in the configuration.",
            user_action="1. Check for empty cells in required columns\n2. Verify all machine names are provided\n3. Ensure target regions and resource groups are specified\n4. Fill in missing subscription IDs",
            related_errors=["Validation will skip machines with missing data", "Some validations may fail"]
        ),
        
        "invalid_azure_names": ErrorContext(
            error_code="CONF003",
            category=ErrorCategory.CONFIGURATION,
            title="Invalid Azure Resource Names",
            description="One or more Azure resource names don't follow naming conventions.",
            user_action="1. Check Azure naming rules for each resource type\n2. Ensure names don't contain invalid characters\n3. Verify name lengths are within limits\n4. Check for reserved names",
            documentation_links=["https://docs.microsoft.com/en-us/azure/azure-resource-manager/management/resource-name-rules"]
        ),
        
        # Network Errors  
        "network_connectivity": ErrorContext(
            error_code="NET001",
            category=ErrorCategory.NETWORK,
            title="Network Connectivity Issue",
            description="Unable to connect to Azure services due to network issues.",
            user_action="1. Check internet connectivity\n2. Verify firewall settings allow HTTPS (443) to Azure\n3. Check proxy settings if applicable\n4. Ensure DNS resolution is working\n5. Try from a different network if possible",
            related_errors=["Authentication may fail", "All Azure API calls will fail"]
        ),
        
        # Validation Errors
        "region_not_supported": ErrorContext(
            error_code="VAL001",
            category=ErrorCategory.VALIDATION,
            title="Azure Region Not Supported",
            description="The specified Azure region is not supported for this operation.",
            user_action="1. Check the list of supported regions for Azure Migrate\n2. Use a different target region\n3. Verify region name spelling\n4. Check if the region supports the required services",
            documentation_links=["https://docs.microsoft.com/en-us/azure/migrate/migrate-support-matrix#supported-geographies"]
        ),
        
        "vm_sku_not_available": ErrorContext(
            error_code="VAL002",
            category=ErrorCategory.VALIDATION,
            title="VM SKU Not Available",
            description="The specified VM SKU is not available in the target region.",
            user_action="1. Check VM availability in the target region\n2. Use 'az vm list-skus' to see available SKUs\n3. Choose an alternative VM size\n4. Consider a different region with the required SKU",
            documentation_links=["https://docs.microsoft.com/en-us/azure/virtual-machines/sizes"]
        ),
        
        "quota_exceeded": ErrorContext(
            error_code="VAL003",
            category=ErrorCategory.VALIDATION,
            title="Azure Quota Exceeded",
            description="The operation would exceed your Azure subscription quota limits.",
            user_action="1. Check current quota usage in Azure Portal\n2. Request quota increase through Azure Portal\n3. Delete unused resources to free quota\n4. Consider using different VM sizes or regions",
            documentation_links=["https://docs.microsoft.com/en-us/azure/azure-portal/supportability/per-vm-quota-requests"]
        )
    }
    
    @classmethod
    def build_from_exception(cls, error: Exception, context: Optional[Dict[str, Any]] = None) -> ErrorContext:
        """Build error context from an exception"""
        
        error_str = str(error).lower()
        context = context or {}
        
        # Try to match error patterns
        for pattern_key, error_context in cls.ERROR_PATTERNS.items():
            if cls._matches_pattern(error_str, pattern_key, error):
                # Create a copy and add technical details
                enhanced_context = ErrorContext(
                    error_code=error_context.error_code,
                    category=error_context.category,
                    title=error_context.title,
                    description=error_context.description,
                    user_action=error_context.user_action,
                    technical_details=cls._extract_technical_details(error, context),
                    related_errors=error_context.related_errors,
                    documentation_links=error_context.documentation_links,
                    azure_trace_id=context.get('azure_trace_id')
                )
                return enhanced_context
        
        # Generic error if no pattern matches
        return ErrorContext(
            error_code="GEN001",
            category=ErrorCategory.SYSTEM,
            title="Unexpected Error",
            description=f"An unexpected error occurred: {str(error)}",
            user_action="1. Check the error details below\n2. Run with --debug for more information\n3. If the issue persists, report it with the technical details",
            technical_details=cls._extract_technical_details(error, context),
            azure_trace_id=context.get('azure_trace_id')
        )
    
    @classmethod
    def _matches_pattern(cls, error_str: str, pattern_key: str, error: Exception) -> bool:
        """Check if error matches a specific pattern"""
        
        pattern_checks = {
            "subscription_not_found": lambda: (
                "subscriptionnotfound" in error_str.replace(' ', '') or
                ("subscription" in error_str and "not found" in error_str) or
                ("subscription" in error_str and "could not be found" in error_str)
            ),
            "invalid_credentials": lambda: (
                "authentication" in error_str and "failed" in error_str or
                "invalid" in error_str and "credential" in error_str or
                "unauthorized" in error_str
            ),
            "token_expired": lambda: (
                "token" in error_str and ("expired" in error_str or "invalid" in error_str) or
                "401" in error_str
            ),
            "insufficient_permissions": lambda: (
                "permission" in error_str and "denied" in error_str or
                "authorization" in error_str and "failed" in error_str or
                "403" in error_str or "forbidden" in error_str
            ),
            "rbac_assignment_failed": lambda: (
                "rbac" in error_str or "role assignment" in error_str
            ),
            "resource_not_found": lambda: (
                "not found" in error_str and "resource" in error_str or
                "404" in error_str or "resourcenotfound" in error_str.replace(' ', '')
            ),
            "api_throttled": lambda: (
                "throttl" in error_str or "429" in error_str or "rate limit" in error_str
            ),
            "api_service_unavailable": lambda: (
                "service unavailable" in error_str or "503" in error_str or "502" in error_str
            ),
            "excel_structure_invalid": lambda: (
                "excel" in error_str and ("structure" in error_str or "column" in error_str) or
                "template" in error_str
            ),
            "missing_required_fields": lambda: (
                "required" in error_str and ("field" in error_str or "column" in error_str) or
                "null" in error_str and "value" in error_str
            ),
            "invalid_azure_names": lambda: (
                "name" in error_str and ("invalid" in error_str or "format" in error_str)
            ),
            "network_connectivity": lambda: (
                "network" in error_str or "connection" in error_str or 
                "timeout" in error_str or "dns" in error_str
            ),
            "region_not_supported": lambda: (
                "region" in error_str and ("not supported" in error_str or "invalid" in error_str)
            ),
            "vm_sku_not_available": lambda: (
                "sku" in error_str and ("not available" in error_str or "invalid" in error_str) or
                "vm size" in error_str
            ),
            "quota_exceeded": lambda: (
                "quota" in error_str and ("exceeded" in error_str or "limit" in error_str)
            )
        }
        
        check_func = pattern_checks.get(pattern_key)
        return check_func() if check_func else False
    
    @classmethod
    def _extract_technical_details(cls, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract technical details from error and context"""
        
        details = {
            "Error Type": type(error).__name__,
            "Error Message": str(error),
            "Timestamp": context.get('timestamp', 'Unknown')
        }
        
        # Add HTTP details if available
        if hasattr(error, 'status_code'):
            details["HTTP Status Code"] = error.status_code
            
        if hasattr(error, 'response') and error.response:
            details["Response Headers"] = dict(error.response.headers) if hasattr(error.response, 'headers') else 'N/A'
        
        # Add context details
        for key, value in context.items():
            if key not in ['timestamp', 'azure_trace_id']:
                details[key.replace('_', ' ').title()] = value
        
        return details


def handle_error_with_context(error: Exception, context: Optional[Dict[str, Any]] = None) -> ErrorContext:
    """Main entry point for handling errors with enhanced context"""
    
    error_context = ErrorContextBuilder.build_from_exception(error, context)
    error_context.display()
    return error_context