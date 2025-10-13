"""
Cached Token Credential for Azure authentication
This module provides token caching functionality for interactive authentication
"""
from typing import Optional
from datetime import datetime, timedelta
from azure.core.credentials import TokenCredential, AccessToken
from azure.identity import InteractiveBrowserCredential
from rich.console import Console
from .project_manager import ProjectAuthConfig, ProjectManager

console = Console()


class TokenCachingWrapper(TokenCredential):
    """
    A wrapper credential that caches tokens after successful authentication
    Used for new project creation when no cached token exists yet
    """

    def __init__(self, base_credential: TokenCredential, project_auth: ProjectAuthConfig,
                 project_manager: ProjectManager, project_config):
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
        if hasattr(self.base_credential, 'close') and callable(getattr(self.base_credential, 'close')):
            self.base_credential.close()


class CachedInteractiveCredential(TokenCredential):
    """
    A credential that caches tokens from interactive authentication in project configuration
    """

    def __init__(self, project_auth: ProjectAuthConfig, project_manager: ProjectManager, project_config):
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
    def create_credential(
        project_auth: ProjectAuthConfig,
        project_manager: ProjectManager,
        project_config
    ) -> TokenCredential:
        """
        Create appropriate credential based on authentication method with caching support

        Args:
            project_auth: Project authentication configuration
            project_manager: Project manager for token persistence
            project_config: Project configuration to save

        Returns:
            TokenCredential: Configured credential with caching support
        """
        from .auth import get_azure_credential

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
