"""
Azure Authentication Module with Token Caching

Provides multiple authentication methods similar to Azure CLI:
1. Azure CLI authentication (az login)
2. Managed Identity authentication
3. Service Principal authentication
4. Interactive browser authentication (with token caching)
5. Device code authentication

Includes advanced token caching for project-based authentication
"""

import os
import requests
from typing import Optional, Union
from datetime import datetime, timedelta
from rich.console import Console
from rich.prompt import Prompt, Confirm
from azure.identity import (
    DefaultAzureCredential,
    AzureCliCredential,
    ManagedIdentityCredential,
    ClientSecretCredential,
    InteractiveBrowserCredential,
    DeviceCodeCredential,
    ChainedTokenCredential
)
from azure.core.credentials import TokenCredential, AccessToken
from azure.core.exceptions import ClientAuthenticationError

console = Console()

# Export public interface
__all__ = [
    'get_azure_credential',
    'get_current_user_object_id',
    'get_current_tenant_id',
    'TokenCachingWrapper',
    'CachedInteractiveCredential', 
    'CachedCredentialFactory'
]


class AuthenticationMethod:
    """Authentication method enumeration"""
    AZURE_CLI = "azure_cli"
    MANAGED_IDENTITY = "managed_identity"
    SERVICE_PRINCIPAL = "service_principal"
    INTERACTIVE = "interactive"
    DEVICE_CODE = "device_code"
    DEFAULT = "default"


class AzureAuthenticator:
    """
    Handles Azure authentication with multiple methods

    Supports:
    - Azure CLI (az login)
    - Managed Identity (VM, App Service, etc.)
    - Service Principal (client ID + secret)
    - Interactive Browser Login
    - Device Code Flow
    - Default Credential Chain
    """

    def __init__(self, auth_method: Optional[str] = None):
        """
        Initialize authenticator

        Args:
            auth_method: Authentication method to use (if None, will prompt user)
        """
        self.auth_method = auth_method
        self.credential: Optional[TokenCredential] = None

    def authenticate(self) -> TokenCredential:
        """
        Perform authentication based on selected or prompted method

        Returns:
            TokenCredential: Azure credential object

        Raises:
            ClientAuthenticationError: If authentication fails
        """
        # If method not specified, prompt user
        if not self.auth_method:
            self.auth_method = self._prompt_auth_method()

        # Authenticate using selected method
        try:
            if self.auth_method == AuthenticationMethod.AZURE_CLI:
                self.credential = self._authenticate_azure_cli()
            elif self.auth_method == AuthenticationMethod.MANAGED_IDENTITY:
                self.credential = self._authenticate_managed_identity()
            elif self.auth_method == AuthenticationMethod.SERVICE_PRINCIPAL:
                self.credential = self._authenticate_service_principal()
            elif self.auth_method == AuthenticationMethod.INTERACTIVE:
                self.credential = self._authenticate_interactive()
            elif self.auth_method == AuthenticationMethod.DEVICE_CODE:
                self.credential = self._authenticate_device_code()
            else:  # DEFAULT
                self.credential = self._authenticate_default()

            # Validate credential works
            self._validate_credential()

            console.print("[green]✓[/green] Authentication successful!\n")
            return self.credential

        except ClientAuthenticationError as e:
            console.print(f"[red]✗[/red] Authentication failed: {e}")
            raise
        except Exception as e:
            console.print(f"[red]✗[/red] Unexpected error: {e}")
            raise

    def _prompt_auth_method(self) -> str:
        """
        Prompt user to select authentication method

        Returns:
            str: Selected authentication method
        """
        console.print("[bold cyan]Select Authentication Method:[/bold cyan]\n")

        options = {
            "1": ("Azure CLI (az login)", AuthenticationMethod.AZURE_CLI),
            "2": ("Managed Identity", AuthenticationMethod.MANAGED_IDENTITY),
            "3": ("Service Principal", AuthenticationMethod.SERVICE_PRINCIPAL),
            "4": ("Interactive Browser", AuthenticationMethod.INTERACTIVE),
            "5": ("Device Code Flow", AuthenticationMethod.DEVICE_CODE),
            "6": ("Default Credential Chain", AuthenticationMethod.DEFAULT)
        }

        for key, (description, _) in options.items():
            console.print(f"  {key}. {description}")

        console.print()

        choice = Prompt.ask(
            "Choose method",
            choices=list(options.keys()),
            default="1"
        )

        _, method = options[choice]
        console.print(f"[cyan]Selected:[/cyan] {options[choice][0]}\n")
        return method

    def _authenticate_azure_cli(self) -> AzureCliCredential:
        """
        Authenticate using Azure CLI credentials

        Requires: az login to be executed beforehand

        Returns:
            AzureCliCredential: Azure CLI credential
        """
        console.print("[cyan]Using Azure CLI authentication...[/cyan]")
        console.print("[dim]Note: Ensure you've run 'az login' first[/dim]\n")

        try:
            credential = AzureCliCredential()
            return credential
        except Exception as e:
            console.print("[red]Azure CLI authentication failed![/red]")
            console.print(
                "[yellow]Run 'az login' first and try again[/yellow]")
            raise ClientAuthenticationError(f"Azure CLI auth failed: {e}")

    def _authenticate_managed_identity(self) -> ManagedIdentityCredential:
        """
        Authenticate using Managed Identity

        Works on: Azure VM, App Service, Container Instances, etc.

        Returns:
            ManagedIdentityCredential: Managed identity credential
        """
        console.print("[cyan]Using Managed Identity authentication...[/cyan]")

        # Check if client_id is provided via environment variable
        client_id = os.getenv("AZURE_CLIENT_ID")

        if client_id:
            console.print(
                f"[dim]Using user-assigned identity: {client_id}[/dim]\n")
            credential = ManagedIdentityCredential(client_id=client_id)
        else:
            console.print("[dim]Using system-assigned identity[/dim]\n")
            credential = ManagedIdentityCredential()

        return credential

    def _authenticate_service_principal(self) -> ClientSecretCredential:
        """
        Authenticate using Service Principal (App Registration)

        Requires:
        - Tenant ID
        - Client ID (Application ID)
        - Client Secret

        Can be provided via:
        - Environment variables (AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET)
        - Interactive prompts

        Returns:
            ClientSecretCredential: Service principal credential
        """
        console.print(
            "[cyan]Using Service Principal authentication...[/cyan]\n")

        # Try environment variables first
        tenant_id = os.getenv("AZURE_TENANT_ID")
        client_id = os.getenv("AZURE_CLIENT_ID")
        client_secret = os.getenv("AZURE_CLIENT_SECRET")

        # Prompt for missing values
        if not tenant_id:
            tenant_id = Prompt.ask("[yellow]Tenant ID[/yellow]")

        if not client_id:
            client_id = Prompt.ask(
                "[yellow]Client ID (Application ID)[/yellow]")

        if not client_secret:
            client_secret = Prompt.ask(
                "[yellow]Client Secret[/yellow]",
                password=True
            )

        console.print()

        try:
            credential = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )
            return credential
        except Exception as e:
            console.print(
                "[red]Service Principal authentication failed![/red]")
            raise ClientAuthenticationError(
                f"Service principal auth failed: {e}")

    def _authenticate_interactive(self) -> InteractiveBrowserCredential:
        """
        Authenticate using interactive browser login

        Opens browser for user to sign in

        Returns:
            InteractiveBrowserCredential: Interactive browser credential
        """
        console.print(
            "[cyan]Using Interactive Browser authentication...[/cyan]")
        console.print(
            "[dim]A browser window will open for you to sign in[/dim]\n")

        tenant_id = os.getenv("AZURE_TENANT_ID")

        if not tenant_id:
            use_specific_tenant = Confirm.ask(
                "Do you want to specify a tenant ID?",
                default=False
            )
            if use_specific_tenant:
                tenant_id = Prompt.ask("Tenant ID")

        console.print()

        try:
            if tenant_id:
                credential = InteractiveBrowserCredential(tenant_id=tenant_id)
            else:
                credential = InteractiveBrowserCredential()
            return credential
        except Exception as e:
            console.print("[red]Interactive authentication failed![/red]")
            raise ClientAuthenticationError(f"Interactive auth failed: {e}")

    def _authenticate_device_code(self) -> DeviceCodeCredential:
        """
        Authenticate using device code flow

        Useful for:
        - Headless environments
        - SSH sessions
        - Remote terminals

        Returns:
            DeviceCodeCredential: Device code credential
        """
        console.print("[cyan]Using Device Code authentication...[/cyan]")
        console.print(
            "[dim]You'll receive a code to enter at https://microsoft.com/devicelogin[/dim]\n")

        tenant_id = os.getenv("AZURE_TENANT_ID")

        if not tenant_id:
            use_specific_tenant = Confirm.ask(
                "Do you want to specify a tenant ID?",
                default=False
            )
            if use_specific_tenant:
                tenant_id = Prompt.ask("Tenant ID")

        console.print()

        def device_code_callback(verification_uri, user_code, expires_in):
            console.print(
                f"[bold yellow]Device Code Authentication[/bold yellow]")
            console.print(f"1. Go to: [link]{verification_uri}[/link]")
            console.print(f"2. Enter code: [bold]{user_code}[/bold]")
            console.print(f"3. Code expires in {expires_in} seconds\n")

        try:
            if tenant_id:
                credential = DeviceCodeCredential(
                    tenant_id=tenant_id,
                    prompt_callback=device_code_callback
                )
            else:
                credential = DeviceCodeCredential(
                    prompt_callback=device_code_callback
                )
            return credential
        except Exception as e:
            console.print("[red]Device code authentication failed![/red]")
            raise ClientAuthenticationError(f"Device code auth failed: {e}")

    def _authenticate_default(self) -> DefaultAzureCredential:
        """
        Authenticate using DefaultAzureCredential chain

        Tries in order:
        1. Environment variables (service principal)
        2. Managed Identity
        3. Azure CLI
        4. Azure PowerShell
        5. Interactive browser

        Returns:
            DefaultAzureCredential: Default credential chain
        """
        console.print("[cyan]Using Default Credential Chain...[/cyan]")
        console.print(
            "[dim]Trying: Environment → Managed Identity → Azure CLI → Interactive[/dim]\n")

        try:
            credential = DefaultAzureCredential()
            return credential
        except Exception as e:
            console.print("[red]Default credential chain failed![/red]")
            console.print(
                "[yellow]Try using a specific authentication method[/yellow]")
            raise ClientAuthenticationError(f"Default auth failed: {e}")

    def _validate_credential(self):
        """
        Validate that credential works by attempting to get a token

        Raises:
            ClientAuthenticationError: If credential validation fails
        """
        if not self.credential:
            raise ClientAuthenticationError(
                "No credential available for validation")

        try:
            # Try to get a token for Azure Resource Manager
            token = self.credential.get_token(
                "https://management.azure.com/.default")
            if not token or not token.token:
                raise ClientAuthenticationError(
                    "Failed to obtain access token")
        except Exception as e:
            raise ClientAuthenticationError(
                f"Credential validation failed: {e}")


def get_azure_credential(
    auth_method: Optional[str] = None,
    tenant_id: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None
) -> TokenCredential:
    """
    Convenience function to get Azure credential

    Args:
        auth_method: Authentication method (azure_cli, managed_identity, service_principal, etc.)
        tenant_id: Azure tenant ID (for service principal)
        client_id: Azure client ID (for service principal or managed identity)
        client_secret: Azure client secret (for service principal)

    Returns:
        TokenCredential: Authenticated Azure credential

    Example:
        # Azure CLI
        credential = get_azure_credential(auth_method="azure_cli")

        # Managed Identity
        credential = get_azure_credential(auth_method="managed_identity")

        # Service Principal
        credential = get_azure_credential(
            auth_method="service_principal",
            tenant_id="xxx",
            client_id="yyy",
            client_secret="zzz"
        )
    """
    # Set environment variables if provided
    if tenant_id:
        os.environ["AZURE_TENANT_ID"] = tenant_id
    if client_id:
        os.environ["AZURE_CLIENT_ID"] = client_id
    if client_secret:
        os.environ["AZURE_CLIENT_SECRET"] = client_secret

    authenticator = AzureAuthenticator(auth_method=auth_method)
    return authenticator.authenticate()


def get_current_user_object_id(credential: TokenCredential) -> Optional[str]:
    """
    Get the current user's Azure AD Object ID from the authenticated credential

    Args:
        credential: Azure token credential

    Returns:
        str: Azure AD Object ID of the current user, or None if not available
    """
    try:
        # Get access token for Microsoft Graph API
        token = credential.get_token("https://graph.microsoft.com/.default")

        # Call Microsoft Graph API to get current user info
        headers = {
            'Authorization': f'Bearer {token.token}',
            'Content-Type': 'application/json'
        }

        response = requests.get(
            'https://graph.microsoft.com/v1.0/me',
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            user_info = response.json()
            object_id = user_info.get('id')

            if object_id:
                console.print(
                    f"[green]✓[/green] Detected current user: {user_info.get('userPrincipalName', 'Unknown')} (Object ID: {object_id})")
                return object_id
            else:
                console.print(
                    "[yellow]⚠[/yellow] Could not extract Object ID from user info")
                return None
        else:
            console.print(
                f"[yellow]⚠[/yellow] Could not retrieve user info from Microsoft Graph (HTTP {response.status_code})")
            return None

    except Exception as e:
        console.print(
            f"[yellow]⚠[/yellow] Could not auto-detect user Object ID: {str(e)}")
        return None


def get_current_tenant_id(credential: TokenCredential) -> Optional[str]:
    """
    Get the current tenant ID from the authenticated credential

    Args:
        credential: Azure token credential

    Returns:
        str: Tenant ID, or None if unable to retrieve

    Raises:
        Exception: If unable to get tenant information
    """
    try:
        # Get access token for Microsoft Graph
        token = credential.get_token('https://graph.microsoft.com/.default')

        headers = {
            'Authorization': f'Bearer {token.token}',
            'Content-Type': 'application/json'
        }

        # Get organization information to extract tenant ID
        response = requests.get(
            'https://graph.microsoft.com/v1.0/organization',
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            org_info = response.json()
            if org_info.get('value') and len(org_info['value']) > 0:
                tenant_id = org_info['value'][0].get('id')
                if tenant_id:
                    console.print(
                        f"[green]✓[/green] Detected tenant ID: {tenant_id}")
                    return tenant_id

            console.print(
                "[yellow]⚠[/yellow] Could not extract tenant ID from organization info")
            return None
        else:
            console.print(
                f"[yellow]⚠[/yellow] Could not retrieve organization info from Microsoft Graph (HTTP {response.status_code})")
            return None

    except Exception as e:
        console.print(
            f"[yellow]⚠[/yellow] Could not auto-detect tenant ID: {str(e)}")
        return None


# =============================================================================
# TOKEN CACHING CLASSES (Merged from cached_credential.py)
# =============================================================================

class TokenCachingWrapper(TokenCredential):
    """
    A wrapper credential that caches tokens after successful authentication
    Used for new project creation when no cached token exists yet
    """

    def __init__(self, base_credential: TokenCredential, project_auth, 
                 project_manager, project_config):
        """
        Initialize token caching wrapper

        Args:
            base_credential: The underlying credential to wrap
            project_auth: Project authentication configuration
            project_manager: Project manager for saving tokens
            project_config: Project configuration to save
        """
        self.base_credential = base_credential
        self.project_auth = project_auth
        self.project_manager = project_manager
        self.project_config = project_config
        self._first_token_obtained = False

    def get_token(self, *scopes: str, **kwargs) -> AccessToken:
        """Get token and cache it if it's the first time"""
        token = self.base_credential.get_token(*scopes, **kwargs)

        # Cache the token if this is interactive authentication and first time
        if (not self._first_token_obtained and
            self.project_auth.auth_method.value == "interactive" and
                isinstance(self.base_credential, InteractiveBrowserCredential)):

            try:
                expires_at = datetime.fromtimestamp(token.expires_on)
                self.project_auth.cache_token(
                    access_token=token.token,
                    expires_at=expires_at
                )

                # Save the project with cached token
                self.project_manager.save_project(self.project_config)
                console.print(
                    "[green]✅ Authentication token saved to project![/green]")
                self._first_token_obtained = True

            except Exception as e:
                console.print(
                    f"[yellow]⚠️ Warning: Could not save token: {e}[/yellow]")

        return token

    def close(self):
        """Close the underlying credential"""
        try:
            if hasattr(self.base_credential, 'close') and callable(getattr(self.base_credential, 'close')):
                # Type ignore for dynamic attribute access
                getattr(self.base_credential, 'close')()  # type: ignore
        except Exception:
            # Some credentials may not support close() - ignore silently
            pass


class CachedInteractiveCredential(TokenCredential):
    """
    A credential that caches tokens from interactive authentication in project configuration
    """

    def __init__(self, project_auth, project_manager, project_config):
        """
        Initialize the cached credential

        Args:
            project_auth: Project authentication configuration with token cache
            project_manager: Project manager for saving token updates
            project_config: Project configuration to save
        """
        self.project_auth = project_auth
        self.project_manager = project_manager
        self.project_config = project_config
        self._interactive_credential = None

    def get_token(self, *scopes: str, **kwargs) -> AccessToken:
        """
        Get access token, using cached token if available and valid

        Args:
            *scopes: The scopes for which the token is requested
            **kwargs: Additional keyword arguments

        Returns:
            AccessToken: Valid access token
        """
        # First, check if we have a valid cached token
        if self.project_auth.is_token_valid() and self.project_auth.cached_token and self.project_auth.token_expires_at:
            console.print("[dim]ℹ️ Using cached authentication token...[/dim]")

            # Create AccessToken from cached data
            expires_at = datetime.fromisoformat(
                self.project_auth.token_expires_at)
            return AccessToken(token=self.project_auth.cached_token, expires_on=int(expires_at.timestamp()))

        # No valid cached token, need to authenticate interactively
        console.print(
            "[cyan]🔐 Cached token expired or not found. Opening browser for authentication...[/cyan]")

        if not self._interactive_credential:
            self._interactive_credential = InteractiveBrowserCredential(
                tenant_id=self.project_auth.tenant_id
            )

        # Get new token via interactive authentication
        token = self._interactive_credential.get_token(*scopes, **kwargs)

        # Cache the new token
        expires_at = datetime.fromtimestamp(token.expires_on)
        self.project_auth.cache_token(
            access_token=token.token,
            expires_at=expires_at,
            refresh_token=None  # InteractiveBrowserCredential doesn't expose refresh tokens
        )

        # Save the updated project configuration
        try:
            self.project_manager.save_project(self.project_config)
            console.print(
                "[green]✅ Authentication token cached successfully![/green]")
        except Exception as e:
            console.print(
                f"[yellow]⚠️ Warning: Could not save token cache: {e}[/yellow]")

        return token

    def close(self):
        """Close the credential and clean up resources"""
        if self._interactive_credential and hasattr(self._interactive_credential, 'close'):
            self._interactive_credential.close()


class CachedCredentialFactory:
    """
    Factory for creating cached credentials based on project configuration
    """

    @staticmethod
    def create_credential(project_auth, project_manager, project_config) -> TokenCredential:
        """
        Create appropriate credential based on authentication method with caching support

        Args:
            project_auth: Project authentication configuration
            project_manager: Project manager for token persistence
            project_config: Project configuration to save

        Returns:
            TokenCredential: Configured credential with caching support
        """
        # For interactive authentication, use cached credential if token exists
        if project_auth.auth_method.value == "interactive":
            if project_auth.is_token_valid():
                return CachedInteractiveCredential(project_auth, project_manager, project_config)
            else:
                # No valid cached token, create new one with caching wrapper
                base_credential = get_azure_credential(
                    auth_method=project_auth.auth_method.value,
                    tenant_id=project_auth.tenant_id,
                    client_id=project_auth.client_id
                )
                return TokenCachingWrapper(base_credential, project_auth, project_manager, project_config)

        # For other authentication methods, use standard credentials
        # (They handle their own caching mechanisms)
        return get_azure_credential(
            auth_method=project_auth.auth_method.value,
            tenant_id=project_auth.tenant_id,
            client_id=project_auth.client_id
        )
