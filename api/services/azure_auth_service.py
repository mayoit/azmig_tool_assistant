"""
Azure Authentication Service for Project-Specific Credentials.

Handles Azure authentication for validation jobs using project-specific credentials.
Supports multiple authentication methods:
- User Login (Interactive/Device Code)
- Service Principal (Client Secret)
- Managed Identity
"""

import json
import base64
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
from cryptography.fernet import Fernet
import os

logger = logging.getLogger(__name__)

from azure.identity import (
    DefaultAzureCredential,
    ClientSecretCredential,
    ManagedIdentityCredential,
    DeviceCodeCredential,
    InteractiveBrowserCredential
)
from azure.core.credentials import AccessToken, TokenCredential
from sqlalchemy.orm import Session

from models import Project
from config import get_settings


class ManualTokenCredential(TokenCredential):
    """Custom credential class for manually provided tokens."""
    
    def __init__(self, access_token: str, expires_on: int):
        """
        Initialize with a manually provided token.
        
        Args:
            access_token: The Azure access token
            expires_on: Unix timestamp when token expires
        """
        self.access_token = access_token
        self.expires_on = expires_on
    
    def get_token(self, *scopes, **kwargs) -> AccessToken:
        """Return the stored access token."""
        return AccessToken(self.access_token, self.expires_on)


class AzureAuthService:
    """Service to manage Azure authentication for projects."""
    
    # Encryption key for storing credentials (should be in environment variable)
    _encryption_key = os.getenv('ENCRYPTION_KEY', Fernet.generate_key())
    _cipher = Fernet(_encryption_key)
    
    # Token scope for Azure Resource Manager
    ARM_SCOPE = "https://management.azure.com/.default"
    
    def __init__(self, db_session: Session):
        """Initialize Azure auth service."""
        self.db = db_session
        self.settings = get_settings()
    
    def _encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data."""
        return self._cipher.encrypt(data.encode()).decode()
    
    def _decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        return self._cipher.decrypt(encrypted_data.encode()).decode()
    
    def configure_project_auth(
        self,
        project_id: int,
        tenant_id: str,
        auth_method: str,
        credentials: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Configure Azure authentication for a project.
        
        Args:
            project_id: Project ID
            tenant_id: Azure AD Tenant ID
            auth_method: One of: user_login, user_interactive, service_principal, managed_identity
            credentials: Auth-specific credentials dict
                - For service_principal: {client_id, client_secret}
                - For managed_identity: {client_id} (optional)
                - For user_login: {} (device code flow)
                - For user_interactive: {} (browser-based flow)
                - For user_token: {access_token, expires_on} (manual token)
        
        Returns:
            Dict with status and message
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {"success": False, "error": "Project not found"}
        
        # Validate auth method
        valid_methods = ['user_login', 'user_interactive', 'service_principal', 'managed_identity', 'user_token']
        if auth_method not in valid_methods:
            return {"success": False, "error": f"Invalid auth method. Must be one of: {valid_methods}"}
        
        # Store configuration
        project.azure_tenant_id = tenant_id
        project.auth_method = auth_method
        
        # Encrypt and store credentials if provided
        if credentials:
            encrypted_creds = self._encrypt_data(json.dumps(credentials))
            project.auth_credentials = {"data": encrypted_creds}
        
        self.db.commit()
        
        return {
            "success": True,
            "message": f"Authentication configured successfully using {auth_method}",
            "tenant_id": tenant_id,
            "auth_method": auth_method
        }
    
    def get_credential(self, project_id: int) -> Tuple[Any, Dict[str, Any]]:
        """
        Get Azure credential for a project.
        
        Returns:
            Tuple of (credential_object, auth_info_dict)
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError("Project not found")
        
        if not project.auth_method or not project.azure_tenant_id:
            # Fallback to default credential
            return DefaultAzureCredential(), {
                "method": "default",
                "message": "No authentication configured, using default Azure credential"
            }
        
        auth_info = {
            "method": project.auth_method,
            "tenant_id": project.azure_tenant_id
        }
        
        try:
            if project.auth_method == 'service_principal':
                # Service Principal with Client Secret
                if not project.auth_credentials:
                    raise ValueError("Service principal credentials not configured")
                
                creds_data = self._decrypt_data(project.auth_credentials.get('data', ''))
                creds = json.loads(creds_data)
                
                credential = ClientSecretCredential(
                    tenant_id=project.azure_tenant_id,
                    client_id=creds.get('client_id'),
                    client_secret=creds.get('client_secret')
                )
                auth_info["client_id"] = creds.get('client_id')
                
            elif project.auth_method == 'managed_identity':
                # Managed Identity
                client_id = None
                if project.auth_credentials:
                    creds_data = self._decrypt_data(project.auth_credentials.get('data', ''))
                    creds = json.loads(creds_data)
                    client_id = creds.get('client_id')
                
                credential = ManagedIdentityCredential(client_id=client_id)
                auth_info["client_id"] = client_id
                
            elif project.auth_method == 'user_login':
                # Device Code Flow - use stored token instead of re-authenticating
                logger.info(f"[AUTH] Processing user_login (device code) for project {project_id}")
                
                # Check if we have a stored token
                if project.auth_token:
                    try:
                        logger.info(f"[AUTH] Using stored token from device code authentication")
                        # Decrypt and use the stored token
                        decrypted_token = self._decrypt_data(project.auth_token)
                        expires_on = int(project.auth_token_expires_at.timestamp()) if project.auth_token_expires_at else 0
                        
                        logger.info(f"[AUTH] Token expires at: {project.auth_token_expires_at}")
                        credential = ManualTokenCredential(decrypted_token, expires_on)
                        auth_info["message"] = "Using stored token from device code authentication"
                        auth_info["token_expires_on"] = expires_on
                    except Exception as e:
                        logger.error(f"[AUTH] Error using stored token: {str(e)}")
                        # Fall back to creating DeviceCodeCredential (will prompt for re-auth)
                        credential = DeviceCodeCredential(
                            tenant_id=project.azure_tenant_id,
                            client_id="04b07795-8ddb-461a-bbee-02f9e1bf7b46"
                        )
                        auth_info["message"] = "Stored token invalid, re-authentication required"
                else:
                    logger.warning(f"[AUTH] No stored token found for project {project_id}")
                    # No stored token, create DeviceCodeCredential (will prompt for auth)
                    credential = DeviceCodeCredential(
                        tenant_id=project.azure_tenant_id,
                        client_id="04b07795-8ddb-461a-bbee-02f9e1bf7b46"
                    )
                    auth_info["message"] = "No stored token, device code authentication required"
            
            elif project.auth_method == 'user_interactive':
                # Interactive Browser Flow - only works locally, not in Docker
                # Check if we're in Docker environment
                is_docker = os.path.exists('/.dockerenv')
                if is_docker:
                    raise ValueError(
                        "Browser-based authentication is not supported in Docker containers. "
                        "Please use 'User Login (Device Code)' instead, which works in all environments."
                    )
                
                credential = InteractiveBrowserCredential(
                    tenant_id=project.azure_tenant_id,
                    client_id="04b07795-8ddb-461a-bbee-02f9e1bf7b46"  # Azure CLI client ID (public)
                )
                auth_info["message"] = "Using interactive browser authentication"
            
            elif project.auth_method == 'user_token':
                # Manual Token - user provides their own access token
                logger.info(f"[AUTH] Processing user_token for project {project_id}")
                if not project.auth_credentials:
                    logger.error(f"[AUTH] No auth_credentials found for project {project_id}")
                    raise ValueError("Access token not configured")
                
                try:
                    logger.info(f"[AUTH] Decrypting credentials for project {project_id}")
                    creds_data = self._decrypt_data(project.auth_credentials.get('data', ''))
                    logger.info(f"[AUTH] Decryption successful, parsing JSON")
                    creds = json.loads(creds_data)
                    
                    access_token = creds.get('access_token')
                    expires_on = creds.get('expires_on', 0)
                    
                    # Strip quotes if token is wrapped in quotes
                    if access_token and isinstance(access_token, str):
                        access_token = access_token.strip('"')
                    
                    logger.info(f"[AUTH] Token extracted: {access_token[:20]}... expires_on: {expires_on}")
                    
                    if not access_token:
                        logger.error(f"[AUTH] No access_token in decrypted credentials")
                        raise ValueError("Access token is required")
                    
                    logger.info(f"[AUTH] Creating ManualTokenCredential")
                    credential = ManualTokenCredential(access_token, expires_on)
                    logger.info(f"[AUTH] ManualTokenCredential created successfully")
                    auth_info["message"] = "Using manually provided access token"
                    auth_info["token_expires_on"] = expires_on
                except json.JSONDecodeError as e:
                    logger.error(f"[AUTH] JSON decode error: {str(e)}")
                    raise ValueError(f"Failed to parse credentials: {str(e)}")
                except Exception as e:
                    logger.error(f"[AUTH] Error processing user_token: {str(e)}", exc_info=True)
                    raise
            
            else:
                raise ValueError(f"Unsupported auth method: {project.auth_method}")
            
            return credential, auth_info
            
        except Exception as e:
            raise ValueError(f"Failed to create credential: {str(e)}")
    
    def test_authentication(self, project_id: int) -> Dict[str, Any]:
        """
        Test Azure authentication for a project.
        
        Returns:
            Dict with test results
        """
        try:
            credential, auth_info = self.get_credential(project_id)
            
            # Try to get a token for Azure Resource Manager
            token = credential.get_token(self.ARM_SCOPE)
            
            project = self.db.query(Project).filter(Project.id == project_id).first()
            
            # Cache the token
            self._cache_token(project, token)
            
            return {
                "success": True,
                "message": "Authentication successful",
                "auth_method": auth_info.get("method"),
                "tenant_id": auth_info.get("tenant_id"),
                "token_expires_at": datetime.fromtimestamp(token.expires_on).isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Authentication failed"
            }
    
    def _cache_token(self, project: Project, token: AccessToken):
        """Cache access token in database."""
        # Encrypt token
        encrypted_token = self._encrypt_data(token.token)
        
        # Store encrypted token and expiration (timezone-aware)
        project.auth_token = encrypted_token
        project.auth_token_expires_at = datetime.fromtimestamp(token.expires_on, tz=timezone.utc)
        
        self.db.commit()
    
    def get_cached_token(self, project_id: int) -> Optional[str]:
        """
        Get cached token if still valid.
        
        Returns:
            Token string or None if expired/not found
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project or not project.auth_token or not project.auth_token_expires_at:
            return None
        
        # Check if token is still valid (with 5 minute buffer)
        now = datetime.now(timezone.utc)
        expires_at = project.auth_token_expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        if now >= expires_at - timedelta(minutes=5):
            return None
        
        # Decrypt and return token
        return self._decrypt_data(project.auth_token)
    
    def refresh_token(self, project_id: int) -> Dict[str, Any]:
        """
        Refresh the access token for a project.
        
        Returns:
            Dict with new token info
        """
        try:
            credential, _ = self.get_credential(project_id)
            token = credential.get_token(self.ARM_SCOPE)
            
            project = self.db.query(Project).filter(Project.id == project_id).first()
            self._cache_token(project, token)
            
            return {
                "success": True,
                "message": "Token refreshed successfully",
                "expires_at": datetime.fromtimestamp(token.expires_on).isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_auth_status(self, project_id: int) -> Dict[str, Any]:
        """
        Get authentication status for a project.
        
        Returns:
            Dict with auth configuration and status
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {"configured": False, "error": "Project not found"}
        
        if not project.auth_method or not project.azure_tenant_id:
            return {
                "configured": False,
                "message": "Azure authentication not configured for this project"
            }
        
        token_valid = False
        if project.auth_token_expires_at:
            # Use timezone-aware datetime for comparison
            now = datetime.now(timezone.utc)
            # Remove timezone info from expires_at if it's timezone-aware, or make it aware
            expires_at = project.auth_token_expires_at
            if expires_at.tzinfo is None:
                # If stored time is naive, assume UTC
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            token_valid = now < expires_at - timedelta(minutes=5)
        
        return {
            "configured": True,
            "tenant_id": project.azure_tenant_id,
            "auth_method": project.auth_method,
            "token_cached": project.auth_token is not None,
            "token_valid": token_valid,
            "token_expires_at": project.auth_token_expires_at.isoformat() if project.auth_token_expires_at else None
        }
    
    def initiate_device_code_flow(self, project_id: int) -> Dict[str, Any]:
        """
        Initiate device code authentication flow.
        
        Returns:
            Dict with device code, user code, verification URL, and instructions
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {"success": False, "error": "Project not found"}
        
        if project.auth_method != 'user_login':
            return {"success": False, "error": "Device code flow is only for user_login method"}
        
        if not project.azure_tenant_id:
            return {"success": False, "error": "Tenant ID not configured"}
        
        try:
            from azure.identity import DeviceCodeCredential
            from azure.core.credentials import AccessToken
            import queue
            import threading
            
            device_code_info = {}
            token_queue = queue.Queue()
            
            def device_code_callback(verification_uri, user_code, expires_in):
                """Callback to capture device code information."""
                logger.info(f"Device code generated - URI: {verification_uri}, Code: {user_code}")
                device_code_info.update({
                    "verification_uri": verification_uri,
                    "user_code": user_code,
                    "expires_in": expires_in,
                    "message": f"To sign in, use a web browser to open the page {verification_uri} and enter the code {user_code} to authenticate."
                })
            
            # Create credential with callback
            credential = DeviceCodeCredential(
                tenant_id=project.azure_tenant_id,
                client_id="04b07795-8ddb-461a-bbee-02f9e1bf7b46",  # Azure CLI public client ID
                prompt_callback=device_code_callback,
                timeout=300  # 5 minutes
            )
            
            # Trigger the device code flow by requesting a token in background
            def acquire_token():
                try:
                    logger.info(f"Starting token acquisition for project {project_id}")
                    token = credential.get_token(self.ARM_SCOPE)
                    logger.info(f"Token acquired successfully for project {project_id}")
                    token_queue.put(('success', token))
                    
                    # Cache the token in a new database session
                    # We need a new session because we're in a different thread
                    from database import SessionLocal
                    db_session = SessionLocal()
                    try:
                        proj = db_session.query(Project).filter(Project.id == project_id).first()
                        if proj:
                            # Encrypt token
                            encrypted_token = self._encrypt_data(token.token)
                            
                            # Store encrypted token and expiration
                            proj.auth_token = encrypted_token
                            proj.auth_token_expires_at = datetime.fromtimestamp(token.expires_on, tz=timezone.utc)
                            
                            db_session.commit()
                            logger.info(f"Token cached successfully for project {project_id}")
                    except Exception as e:
                        logger.error(f"Failed to cache token: {e}", exc_info=True)
                        db_session.rollback()
                    finally:
                        db_session.close()
                        
                except Exception as e:
                    logger.error(f"Device code flow failed for project {project_id}: {e}", exc_info=True)
                    token_queue.put(('error', str(e)))
            
            # Start token acquisition in background thread
            thread = threading.Thread(target=acquire_token, daemon=True)
            thread.start()
            
            # Wait up to 5 seconds for device code to be generated
            import time
            max_wait = 5
            waited = 0
            while not device_code_info and waited < max_wait:
                time.sleep(0.5)
                waited += 0.5
            
            if device_code_info:
                logger.info(f"Device code flow initiated successfully for project {project_id}")
                return {
                    "success": True,
                    **device_code_info
                }
            else:
                logger.error(f"Failed to generate device code for project {project_id}")
                return {
                    "success": False,
                    "error": "Failed to generate device code - timeout waiting for Azure response"
                }
                
        except Exception as e:
            logger.error(f"Exception in initiate_device_code_flow: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to initiate device code flow: {str(e)}"
            }
