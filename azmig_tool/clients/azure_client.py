"""
Azure REST API clients for Azure management and Azure Migrate operations
"""
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin, urlparse
import json
from azure.identity import DefaultAzureCredential
from azure.core.credentials import TokenCredential
from azure.core.exceptions import HttpResponseError
import requests


class AzureRestApiClient:
    """
    Base class for making Azure REST API calls

    Provides common functionality for authenticating and calling Azure APIs
    """

    BASE_URL = "https://management.azure.com"
    API_VERSION = "2023-01-01"  # Default API version

    def __init__(self, credential: TokenCredential, subscription_id: str):
        """
        Initialize the Azure REST API client

        Args:
            credential: Azure credential for authentication
            subscription_id: Azure subscription ID
        """
        self.credential = credential
        self.subscription_id = subscription_id
        self._token_cache: Optional[str] = None

    def _get_access_token(self) -> str:
        """
        Get Azure access token for management API

        Returns:
            Access token string
        """
        # Get token for Azure management scope
        token = self.credential.get_token(
            "https://management.azure.com/.default")
        return token.token

    def _build_url(self, path: str) -> str:
        """
        Build full URL from path

        Args:
            path: API path (can start with / or subscriptions/)

        Returns:
            Full URL
        """
        if not path.startswith('/'):
            path = '/' + path
        return urljoin(self.BASE_URL, path)

    def _get_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers with authentication

        Returns:
            Dictionary of headers
        """
        token = self._get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def get(
        self,
        path: str,
        api_version: Optional[str] = None,
        params: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make GET request to Azure REST API

        Args:
            path: API path
            api_version: API version (uses default if not provided)
            params: Additional query parameters

        Returns:
            Response JSON as dictionary

        Raises:
            HttpResponseError: If request fails
        """
        url = self._build_url(path)
        headers = self._get_headers()

        # Build query parameters
        query_params = {"api-version": api_version or self.API_VERSION}
        if params:
            query_params.update(params)

        try:
            response = requests.get(url, headers=headers, params=query_params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            raise HttpResponseError(
                message=f"HTTP {e.response.status_code}: {e.response.text}"
            )

    def post(
        self,
        path: str,
        data: Dict[str, Any],
        api_version: Optional[str] = None,
        params: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make POST request to Azure REST API

        Args:
            path: API path
            data: Request body
            api_version: API version (uses default if not provided)
            params: Additional query parameters

        Returns:
            Response JSON as dictionary

        Raises:
            HttpResponseError: If request fails
        """
        url = self._build_url(path)
        headers = self._get_headers()

        # Build query parameters
        query_params = {"api-version": api_version or self.API_VERSION}
        if params:
            query_params.update(params)

        try:
            response = requests.post(
                url,
                headers=headers,
                params=query_params,
                json=data
            )
            response.raise_for_status()
            return response.json() if response.text else {}
        except requests.exceptions.HTTPError as e:
            raise HttpResponseError(
                message=f"HTTP {e.response.status_code}: {e.response.text}"
            )

    def put(
        self,
        path: str,
        data: Dict[str, Any],
        api_version: Optional[str] = None,
        params: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make PUT request to Azure REST API

        Args:
            path: API path
            data: Request body
            api_version: API version (uses default if not provided)
            params: Additional query parameters

        Returns:
            Response JSON as dictionary

        Raises:
            HttpResponseError: If request fails
        """
        url = self._build_url(path)
        headers = self._get_headers()

        # Build query parameters
        query_params = {"api-version": api_version or self.API_VERSION}
        if params:
            query_params.update(params)

        try:
            response = requests.put(
                url,
                headers=headers,
                params=query_params,
                json=data
            )
            response.raise_for_status()
            return response.json() if response.text else {}
        except requests.exceptions.HTTPError as e:
            raise HttpResponseError(
                message=f"HTTP {e.response.status_code}: {e.response.text}"
            )

    def delete(
        self,
        path: str,
        api_version: Optional[str] = None,
        params: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Make DELETE request to Azure REST API

        Args:
            path: API path
            api_version: API version (uses default if not provided)
            params: Additional query parameters

        Returns:
            Response JSON as dictionary (if any)

        Raises:
            HttpResponseError: If request fails
        """
        url = self._build_url(path)
        headers = self._get_headers()

        # Build query parameters
        query_params = {"api-version": api_version or self.API_VERSION}
        if params:
            query_params.update(params)

        try:
            response = requests.delete(
                url, headers=headers, params=query_params)
            response.raise_for_status()
            return response.json() if response.text else None
        except requests.exceptions.HTTPError as e:
            raise HttpResponseError(
                message=f"HTTP {e.response.status_code}: {e.response.text}"
            )

    def list_all(
        self,
        path: str,
        api_version: Optional[str] = None,
        params: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Make GET request and handle pagination

        Args:
            path: API path
            api_version: API version (uses default if not provided)
            params: Additional query parameters

        Returns:
            List of all items from paginated response
        """
        all_items = []
        next_link = path

        while next_link:
            # If next_link is a full URL, extract just the path
            if next_link.startswith('http'):
                parsed = urlparse(next_link)
                next_link = parsed.path + \
                    ('?' + parsed.query if parsed.query else '')

            response = self.get(
                next_link, api_version=api_version, params=params)

            # Handle different pagination response formats
            if 'value' in response:
                all_items.extend(response['value'])
                next_link = response.get(
                    'nextLink') or response.get('@odata.nextLink')
            else:
                # Single item response
                all_items.append(response)
                next_link = None

        return all_items


class AzureMigrateApiClient(AzureRestApiClient):
    """
    Azure Migrate REST API client

    Uses Azure REST API instead of SDK to interact with Azure Migrate
    API Reference: https://learn.microsoft.com/en-us/rest/api/migrate/
    """

    # Azure Migrate API version
    API_VERSION = "2019-10-01"

    def __init__(self, credential, subscription_id: str):
        """
        Initialize Azure Migrate API client

        Args:
            credential: Azure credential
            subscription_id: Azure subscription ID
        """
        super().__init__(credential, subscription_id)

    def list_projects(self, resource_group: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List Azure Migrate projects in subscription or resource group

        Args:
            resource_group: Optional resource group name to filter

        Returns:
            List of project dictionaries
        """
        if resource_group:
            # List projects in specific resource group
            path = f"/subscriptions/{self.subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Migrate/migrateProjects"
        else:
            # List all projects in subscription
            path = f"/subscriptions/{self.subscription_id}/providers/Microsoft.Migrate/migrateProjects"

        try:
            return self.list_all(path, api_version=self.API_VERSION)
        except Exception as e:
            print(f"Error listing Azure Migrate projects: {e}")
            return []

    def get_project(self, resource_group: str, project_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific Azure Migrate project

        Args:
            resource_group: Resource group name
            project_name: Project name

        Returns:
            Project dictionary or None if not found
        """
        path = f"/subscriptions/{self.subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Migrate/migrateProjects/{project_name}"

        try:
            return self.get(path, api_version=self.API_VERSION)
        except Exception as e:
            print(f"Error getting Azure Migrate project: {e}")
            return None

    def list_solutions(self, resource_group: str, project_name: str) -> List[Dict[str, Any]]:
        """
        List solutions in an Azure Migrate project

        Args:
            resource_group: Resource group name
            project_name: Project name

        Returns:
            List of solution dictionaries
        """
        path = f"/subscriptions/{self.subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Migrate/migrateProjects/{project_name}/solutions"

        try:
            return self.list_all(path, api_version=self.API_VERSION)
        except Exception as e:
            print(f"Error listing solutions: {e}")
            return []

    def list_discovered_machines(
        self,
        resource_group: str,
        project_name: str
    ) -> List[Dict[str, Any]]:
        """
        List discovered machines in an Azure Migrate project

        Note: This uses the Assessment API to get discovered machines

        Args:
            resource_group: Resource group name
            project_name: Project name

        Returns:
            List of discovered machine dictionaries
        """
        # First, try to get the assessment project
        assessment_path = f"/subscriptions/{self.subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Migrate/assessmentProjects/{project_name}"

        try:
            # List machines using assessment API
            machines_path = f"{assessment_path}/machines"
            machines = self.list_all(machines_path, api_version="2019-10-01")
            return machines
        except Exception as e:
            print(f"Error listing discovered machines: {e}")
            # Try alternative path with groups
            try:
                groups_path = f"{assessment_path}/groups"
                groups = self.list_all(groups_path, api_version="2019-10-01")

                # Get machines from each group
                all_machines = []
                for group in groups:
                    group_name = group.get('name', '')
                    machines_in_group_path = f"{assessment_path}/groups/{group_name}/assessedMachines"
                    machines = self.list_all(
                        machines_in_group_path, api_version="2019-10-01")
                    all_machines.extend(machines)

                return all_machines
            except Exception as e2:
                print(f"Error with alternative path: {e2}")
                return []

    def get_machine_details(
        self,
        resource_group: str,
        project_name: str,
        machine_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get details of a specific discovered machine

        Args:
            resource_group: Resource group name
            project_name: Project name
            machine_name: Machine name

        Returns:
            Machine details dictionary or None
        """
        path = f"/subscriptions/{self.subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Migrate/assessmentProjects/{project_name}/machines/{machine_name}"

        try:
            return self.get(path, api_version="2019-10-01")
        except Exception as e:
            print(f"Error getting machine details: {e}")
            return None

    def list_assessments(
        self,
        resource_group: str,
        project_name: str,
        group_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List assessments in a project or group

        Args:
            resource_group: Resource group name
            project_name: Project name
            group_name: Optional group name

        Returns:
            List of assessment dictionaries
        """
        if group_name:
            path = f"/subscriptions/{self.subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Migrate/assessmentProjects/{project_name}/groups/{group_name}/assessments"
        else:
            path = f"/subscriptions/{self.subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Migrate/assessmentProjects/{project_name}/assessments"

        try:
            return self.list_all(path, api_version="2019-10-01")
        except Exception as e:
            print(f"Error listing assessments: {e}")
            return []

    def create_replication_item(
        self,
        resource_group: str,
        vault_name: str,
        fabric_name: str,
        protection_container_name: str,
        replication_item_name: str,
        properties: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Create a replication item (enable replication)

        This uses Azure Site Recovery API

        Args:
            resource_group: Resource group name
            vault_name: Recovery Services Vault name
            fabric_name: Fabric name
            protection_container_name: Protection container name
            replication_item_name: Replication item name
            properties: Replication properties

        Returns:
            Replication item response or None
        """
        path = f"/subscriptions/{self.subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.RecoveryServices/vaults/{vault_name}/replicationFabrics/{fabric_name}/replicationProtectionContainers/{protection_container_name}/replicationProtectedItems/{replication_item_name}"

        body = {
            "properties": properties
        }

        try:
            return self.put(path, body, api_version="2022-10-01")
        except Exception as e:
            print(f"Error creating replication item: {e}")
            return None

    def get_replication_status(
        self,
        resource_group: str,
        vault_name: str,
        fabric_name: str,
        protection_container_name: str,
        replication_item_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get replication status for a protected item

        Args:
            resource_group: Resource group name
            vault_name: Recovery Services Vault name
            fabric_name: Fabric name
            protection_container_name: Protection container name
            replication_item_name: Replication item name

        Returns:
            Replication status dictionary or None
        """
        path = f"/subscriptions/{self.subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.RecoveryServices/vaults/{vault_name}/replicationFabrics/{fabric_name}/replicationProtectionContainers/{protection_container_name}/replicationProtectedItems/{replication_item_name}"

        try:
            return self.get(path, api_version="2022-10-01")
        except Exception as e:
            print(f"Error getting replication status: {e}")
            return None
