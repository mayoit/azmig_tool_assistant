"""
Azure REST API clients for Azure management and Azure Migrate operations
"""
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin, urlparse
import json
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

        # Check if path already has query parameters
        from urllib.parse import urlparse, parse_qs
        parsed_url = urlparse(url)
        existing_params = parse_qs(parsed_url.query)

        # Build query parameters only if api-version is not already present
        query_params = {}
        if 'api-version' not in existing_params:
            query_params["api-version"] = api_version or self.API_VERSION
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

    # Azure Migrate API version - Updated to supported version
    API_VERSION = "2020-05-01"

    def __init__(self, credential, subscription_id: str):
        """
        Initialize Azure Migrate API client

        Args:
            credential: Azure credential
            subscription_id: Azure subscription ID
        """
        super().__init__(credential, subscription_id)
        # Cache for discovered machines to avoid repeated API calls
        self._machines_cache = {}  # Format: {project_key: machines_list}

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
        project_name: str,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List discovered machines using migrateProjects API (authoritative source)

        Args:
            resource_group: Resource group name
            project_name: Project name
            use_cache: Whether to use cached results (default: True)

        Returns:
            List of discovered machine dictionaries from migrateProjects API
        """
        # Create cache key for this project
        cache_key = f"{self.subscription_id}:{resource_group}:{project_name}"

        # Return cached results if available and requested
        if use_cache and cache_key in self._machines_cache:
            cached_machines = self._machines_cache[cache_key]
            print(
                f"🚀 Using cached machines data ({len(cached_machines)} machines)")
            return cached_machines

        # Use migrateProjects API as the authoritative source for machine list
        migrate_path = f"/subscriptions/{self.subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Migrate/migrateProjects/{project_name}"

        try:
            # List machines using migrateProjects API with correct version
            machines_path = f"{migrate_path}/machines"
            machines = self.list_all(
                machines_path, api_version="2018-09-01-preview")
            print(f"Found {len(machines)} machines via migrateProjects API")

            # Cache the results for future use
            self._machines_cache[cache_key] = machines
            print(
                f"💾 Cached {len(machines)} machines for project {project_name}")

            return machines
        except Exception as e:
            print(f"migrateProjects API failed: {e}")
            return []

    def _add_discovery_status(self, machine: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add discovery status information to a machine record
        
        Args:
            machine: Machine dictionary from Azure API
            
        Returns:
            Machine dictionary with _discovery_status added
        """
        properties = machine.get("properties", {})
        migration_data = properties.get("migrationData", [])
        discovery_data = properties.get("discoveryData", [])
        assessment_data = properties.get("assessmentData", [])
        
        machine["_discovery_status"] = {
            "migration_ready": len(migration_data) > 0,
            "discovered": len(discovery_data) > 0 or len(migration_data) > 0,
            "migration_records": len(migration_data),
            "discovery_records": len(discovery_data),
            "assessment_records": len(assessment_data)
        }
        
        return machine

    def search_machines_by_name(
        self,
        resource_group: str,
        project_name: str,
        machine_name: str
    ) -> List[Dict[str, Any]]:
        """
        Search for a specific machine by name using the individual machine API endpoint

        Uses the API: GET /subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.Migrate/migrateProjects/{migrateProjectName}/machines/{machineName}?api-version=2018-09-01-preview

        Args:
            resource_group: Resource group name
            project_name: Project name
            machine_name: Machine name to search for

        Returns:
            List of matching machine dictionaries (single machine if found)
        """
        # Try direct API call to the specific machine endpoint
        machine_path = f"/subscriptions/{self.subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Migrate/migrateProjects/{project_name}/machines/{machine_name}"

        try:
            # Make direct API call to get specific machine
            machine_data = self.get(machine_path, api_version="2018-09-01-preview")
            
            if machine_data:
                properties = machine_data.get("properties", {})
                
                # Check if machine has migrationData (indicates it's discoverable by migration appliance)
                migration_data = properties.get("migrationData", [])
                discovery_data = properties.get("discoveryData", [])
                assessment_data = properties.get("assessmentData", [])
                
                # Log the discovery status
                if migration_data:
                    print(f"✅ Machine '{machine_name}' found with migration data ({len(migration_data)} records) - migration-ready")
                elif discovery_data:
                    print(f"📋 Machine '{machine_name}' found with discovery data ({len(discovery_data)} records) - discovered only")
                else:
                    print(f"⚠️ Machine '{machine_name}' found but no migration or discovery data")
                
                # Add discovery status to machine data for validation logic
                machine_data = self._add_discovery_status(machine_data)
                
                return [machine_data]  # Return as list for consistency with other search methods
                
        except HttpResponseError as e:
            if "404" in str(e) or "NotFound" in str(e):
                print(f"❌ Machine '{machine_name}' not found in project '{project_name}'")
                return []
            else:
                print(f"❌ API error searching for machine '{machine_name}': {e}")
                # Fall back to list-based search on other errors
                
        except Exception as e:
            print(f"❌ Error searching for machine '{machine_name}': {e}")
            # Fall back to list-based search

        # Fallback: search through all machines if direct API call fails
        print(f"🔄 Falling back to list-based search for machine '{machine_name}'")
        all_machines = self.list_discovered_machines(resource_group, project_name)
        matching_machines = []

        for machine in all_machines:
            properties = machine.get("properties", {})
            machine_id = machine.get("name", "")
            
            # Check if machine name matches (case-insensitive)
            if machine_name.upper() == machine_id.upper():
                # First priority: Check migrationData (migration-ready machines)
                migration_data = properties.get("migrationData", [])
                discovery_data = properties.get("discoveryData", [])
                assessment_data = properties.get("assessmentData", [])
                
                # Add discovery status
                machine = self._add_discovery_status(machine)
                
                if migration_data:
                    print(f"✅ Found '{machine_name}' with migration data - migration-ready")
                elif discovery_data:
                    print(f"📋 Found '{machine_name}' with discovery data - discovered only")
                
                matching_machines.append(machine)
                break

        return matching_machines

    def search_machines_by_name_cached(
        self,
        resource_group: str,
        project_name: str,
        machine_name: str
    ) -> List[Dict[str, Any]]:
        """
        Search for machines by name using cached data (performance optimized)

        This method first ensures all machines are cached, then searches locally
        to minimize API calls during bulk validation.

        Args:
            resource_group: Resource group name
            project_name: Project name
            machine_name: Machine name to search for

        Returns:
            List of matching machine dictionaries
        """
        # Ensure machines are cached (makes only one API call if not already cached)
        all_machines = self.list_discovered_machines(
            resource_group, project_name, use_cache=True)

        matching_machines = []
        machine_name_upper = machine_name.upper()

        for machine in all_machines:
            properties = machine.get("properties", {})
            machine_id = machine.get("name", "")
            found_match = False

            # Check if machine name/ID matches (case-insensitive)
            if machine_name_upper == machine_id.upper():
                found_match = True
            else:
                # Also search within migrationData and discoveryData for machine name
                migration_data = properties.get("migrationData", [])
                for data in migration_data:
                    if machine_name_upper in data.get("machineName", "").upper():
                        found_match = True
                        break
                
                if not found_match:
                    discovery_data = properties.get("discoveryData", [])
                    for data in discovery_data:
                        if machine_name_upper in data.get("machineName", "").upper():
                            found_match = True
                            break

            if found_match:
                # Add discovery status information consistent with direct API method
                machine = self._add_discovery_status(machine)
                matching_machines.append(machine)

        return matching_machines

    def get_machine_details(
        self,
        resource_group: str,
        project_name: str,
        machine_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get details of a specific discovered machine

        Uses migrateProjects API for basic info and assessmentProjects API for detailed info

        Args:
            resource_group: Resource group name
            project_name: Project name
            machine_name: Machine name (can be display name or machine ID)

        Returns:
            Combined machine details dictionary or None
        """
        # First, try to find the machine by name using cached search for performance
        matching_machines = self.search_machines_by_name_cached(
            resource_group, project_name, machine_name)

        if matching_machines:
            # Found machine via search - return the first match with migrate API data
            machine = matching_machines[0]
            machine_id = machine.get("name")
            print(f"Found machine via search: {machine_id}")

            # Enrich with detailed assessment data if available
            try:
                # Try to get detailed info from assessment API
                assessment_project = "p-az1-azmig025610project"  # Known assessment project
                assessment_path = f"/subscriptions/{self.subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Migrate/assessmentProjects/{assessment_project}/machines"

                # Search for matching machine in assessment project
                assessment_machines = self.list_all(
                    assessment_path, api_version="2023-03-15")
                for assess_machine in assessment_machines:
                    assess_props = assess_machine.get("properties", {})
                    if assess_props.get("displayName", "").upper() == machine_name.upper():
                        # Combine migrate API data with assessment details
                        machine["assessmentDetails"] = assess_machine.get(
                            "properties", {})
                        print(
                            f"Enriched with assessment details for {machine_name}")
                        break
            except Exception as assess_e:
                print(f"Could not enrich with assessment details: {assess_e}")

            return machine

        # If search fails, try direct access by machine ID
        migrate_path = f"/subscriptions/{self.subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Migrate/migrateProjects/{project_name}/machines/{machine_name}"

        try:
            result = self.get(migrate_path, api_version="2018-09-01-preview")
            if result:
                print(
                    f"Found machine {machine_name} via direct migrateProjects API")
                return result
        except Exception as e:
            print(
                f"Direct migrateProjects API failed for machine {machine_name}: {e}")

        print(f"Machine {machine_name} not found")
        return None

    def find_machine_by_display_name(
        self,
        resource_group: str,
        project_name: str,
        display_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Find a machine by its display name using the new search approach

        Args:
            resource_group: Resource group name
            project_name: Project name  
            display_name: Display name to search for (e.g., "p-dc1-qview03")

        Returns:
            Machine details dictionary or None
        """
        print(f"🔍 Searching for machine with display name: '{display_name}'")

        # Use the new search method that leverages both APIs
        return self.get_machine_details(resource_group, project_name, display_name)

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
            return self.list_all(path, api_version=self.API_VERSION)
        except Exception as e:
            print(f"Error listing assessments: {e}")
            return []

    def get_appliances(self, resource_group: str, project_name: str) -> List[Dict[str, Any]]:
        """
        Get appliances in an Azure Migrate project

        Args:
            resource_group: Resource group name
            project_name: Project name

        Returns:
            List of appliance dictionaries
        """
        try:
            # Try different API approaches in order of reliability
            api_attempts = [
                {
                    'name': 'Resource Graph - Resources table',
                    'method': self._try_resource_graph_resources,
                    'args': (resource_group, project_name)
                },
                {
                    'name': 'Direct ServerSites - 2023-06-06',
                    'method': self._try_server_sites_api,
                    'args': (resource_group, project_name, '2023-06-06')
                },
                {
                    'name': 'Direct ServerSites - 2022-10-27',
                    'method': self._try_server_sites_api,
                    'args': (resource_group, project_name, '2022-10-27')
                },
                {
                    'name': 'Migrate Project solutions - 2020-05-01',
                    'method': self._try_migrate_solutions,
                    'args': (resource_group, project_name, '2020-05-01')
                },
                {
                    'name': 'Migrate Project solutions - 2019-06-01',
                    'method': self._try_migrate_solutions,
                    'args': (resource_group, project_name, '2019-06-01')
                }
            ]

            for attempt in api_attempts:
                try:
                    print(f"Trying {attempt['name']}...")
                    result = attempt['method'](*attempt['args'])
                    if result:
                        print(
                            f"✅ Successfully retrieved {len(result)} appliance(s) via {attempt['name']}")
                        return result
                except Exception as e:
                    print(f"❌ {attempt['name']} failed: {e}")
                    continue

            print(f"❌ All API attempts failed for project {project_name}")
            return []

        except Exception as e:
            print(f"Error getting appliances: {e}")
            return []

    def _try_resource_graph_resources(self, resource_group: str, project_name: str) -> List[Dict[str, Any]]:
        """Try Resource Graph with Resources table"""
        query = f"""
        Resources
        | where type == "microsoft.offazure/serversites"
        | where resourceGroup == "{resource_group}"
        | where properties.discoverySolutionId contains "{project_name}"
        | project id, name, type, properties, resourceGroup, subscriptionId
        """

        result = self._query_resource_graph(query)
        if result:
            return self._parse_resource_graph_appliances(result)
        return []

    def _try_server_sites_api(self, resource_group: str, project_name: str, api_version: str) -> List[Dict[str, Any]]:
        """Try direct ServerSites API with specific version"""
        path = f"/subscriptions/{self.subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.OffAzure/ServerSites"

        result = self.list_all(path, api_version=api_version)
        if result:
            # Filter ServerSites related to this project
            filtered_appliances = []
            for site in result:
                discovery_solution = site.get(
                    'properties', {}).get('discoverySolutionId', '')
                if project_name in discovery_solution:
                    filtered_appliances.append(
                        self._format_server_site_as_appliance(site))
            return filtered_appliances
        return []

    def _try_migrate_solutions(self, resource_group: str, project_name: str, api_version: str) -> List[Dict[str, Any]]:
        """Try Migrate Project solutions API"""
        path = f"/subscriptions/{self.subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Migrate/migrateProjects/{project_name}/solutions"

        result = self.list_all(path, api_version=api_version)
        if result:
            # Look for appliance-related solutions
            appliance_solutions = []
            for solution in result:
                solution_type = solution.get('properties', {}).get('tool', '')
                if 'appliance' in solution_type.lower() or 'discovery' in solution_type.lower() or 'server' in solution_type.lower():
                    # Convert solution to appliance format
                    appliance_solutions.append(
                        self._format_solution_as_appliance(solution, project_name))
            return appliance_solutions
        return []

    def _format_solution_as_appliance(self, solution: Dict[str, Any], project_name: str) -> Dict[str, Any]:
        """Format a solution response as an appliance"""
        properties = solution.get('properties', {})

        return {
            'id': solution.get('id', ''),
            'name': solution.get('name', ''),
            'type': 'solution-based-appliance',
            'appliance_name': f"{project_name}-appliance",
            'provisioning_state': properties.get('status', 'Unknown'),
            'service_endpoint': '',
            'last_heartbeat': '',
            'agent_version': '',
            'discovery_scenario': 'Migrate',
            'health_status': 'Unknown' if properties.get('status') != 'Active' else 'Healthy',
            'properties': properties,
            'tool': properties.get('tool', ''),
            'details': properties.get('details', {})
        }

    def _query_resource_graph(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Query Azure Resource Graph

        Args:
            query: KQL query string

        Returns:
            Resource Graph query result or None
        """
        try:
            # Resource Graph batch API endpoint
            batch_path = "/providers/Microsoft.ResourceGraph/resources"

            query_body = {
                "subscriptions": [self.subscription_id],
                "query": query,
                "options": {
                    "resultFormat": "table"
                }
            }

            return self.post(batch_path, query_body, api_version="2021-03-01")

        except Exception as e:
            print(f"Resource Graph query failed: {e}")
            return None

    def _parse_resource_graph_appliances(self, graph_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse Resource Graph response into appliance format

        Args:
            graph_result: Resource Graph API response

        Returns:
            List of formatted appliance dictionaries
        """
        appliances = []

        try:
            data = graph_result.get('data', {})
            columns = data.get('columns', [])
            rows = data.get('rows', [])

            # Create column name to index mapping
            col_map = {col['name']: i for i, col in enumerate(columns)}

            for row in rows:
                appliance = {
                    'id': row[col_map.get('id', 0)] if 'id' in col_map else '',
                    'name': row[col_map.get('name', 2)] if 'name' in col_map else '',
                    'type': row[col_map.get('type', 1)] if 'type' in col_map else '',
                    'resource_group': row[col_map.get('resourceGroup', 0)] if 'resourceGroup' in col_map else '',
                    'properties': row[col_map.get('properties', 3)] if 'properties' in col_map else {}
                }

                # Extract appliance-specific properties
                properties = appliance['properties']
                if isinstance(properties, dict):
                    appliance.update({
                        'appliance_name': properties.get('applianceName', appliance['name']),
                        'provisioning_state': properties.get('provisioningState', 'Unknown'),
                        'service_endpoint': properties.get('serviceEndpoint', ''),
                        'last_heartbeat': properties.get('agentDetails', {}).get('lastHeartBeatUtc', ''),
                        'agent_version': properties.get('agentDetails', {}).get('version', ''),
                        'discovery_scenario': properties.get('discoveryScenario', ''),
                        'health_status': self._determine_appliance_health(properties)
                    })

                appliances.append(appliance)

        except Exception as e:
            print(f"Error parsing Resource Graph appliances: {e}")

        return appliances

    def _format_server_site_as_appliance(self, server_site: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format ServerSite as appliance dictionary

        Args:
            server_site: ServerSite resource

        Returns:
            Formatted appliance dictionary
        """
        properties = server_site.get('properties', {})

        return {
            'id': server_site.get('id', ''),
            'name': server_site.get('name', ''),
            'type': server_site.get('type', ''),
            'appliance_name': properties.get('applianceName', server_site.get('name', '')),
            'provisioning_state': properties.get('provisioningState', 'Unknown'),
            'service_endpoint': properties.get('serviceEndpoint', ''),
            'last_heartbeat': properties.get('agentDetails', {}).get('lastHeartBeatUtc', ''),
            'agent_version': properties.get('agentDetails', {}).get('version', ''),
            'discovery_scenario': properties.get('discoveryScenario', ''),
            'health_status': self._determine_appliance_health(properties),
            'properties': properties
        }

    def _determine_appliance_health(self, properties: Dict[str, Any]) -> str:
        """
        Determine appliance health status from properties

        Args:
            properties: Appliance properties

        Returns:
            Health status string
        """
        try:
            # Check provisioning state
            provisioning_state = properties.get(
                'provisioningState', '').lower()
            if provisioning_state != 'succeeded':
                return 'Unhealthy'

            # Check agent heartbeat (consider healthy if heartbeat within last 24 hours)
            last_heartbeat = properties.get(
                'agentDetails', {}).get('lastHeartBeatUtc', '')
            if last_heartbeat:
                from datetime import datetime, timezone, timedelta
                try:
                    heartbeat_time = datetime.fromisoformat(
                        last_heartbeat.replace('Z', '+00:00'))
                    current_time = datetime.now(timezone.utc)
                    if current_time - heartbeat_time > timedelta(hours=24):
                        return 'Unhealthy'
                except Exception:
                    pass

            # Check for service endpoint
            service_endpoint = properties.get('serviceEndpoint', '')
            if not service_endpoint:
                return 'Unhealthy'

            return 'Healthy'

        except Exception as e:
            print(f"Error determining appliance health: {e}")
            return 'Unknown'

    def get_protection_container_mappings(
        self,
        resource_group: str,
        vault_name: str
    ) -> List[Dict[str, Any]]:
        """
        Get replication protection container mappings for a Recovery Services Vault

        Args:
            resource_group: Resource group name
            vault_name: Recovery Services Vault name

        Returns:
            List of protection container mapping dictionaries
        """
        path = f"/subscriptions/{self.subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.RecoveryServices/vaults/{vault_name}/replicationProtectionContainerMappings"

        try:
            return self.list_all(path, api_version="2023-06-01")
        except Exception as e:
            print(f"Error getting protection container mappings: {e}")
            return []

    def get_replication_fabrics(
        self,
        resource_group: str,
        vault_name: str
    ) -> List[Dict[str, Any]]:
        """
        Get replication fabrics for a Recovery Services Vault

        Args:
            resource_group: Resource group name
            vault_name: Recovery Services Vault name

        Returns:
            List of replication fabric dictionaries
        """
        path = f"/subscriptions/{self.subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.RecoveryServices/vaults/{vault_name}/replicationFabrics"

        try:
            return self.list_all(path, api_version="2023-06-01")
        except Exception as e:
            print(f"Error getting replication fabrics: {e}")
            return []

    def get_protection_containers(
        self,
        resource_group: str,
        vault_name: str,
        fabric_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get protection containers for a Recovery Services Vault

        Args:
            resource_group: Resource group name
            vault_name: Recovery Services Vault name
            fabric_name: Optional fabric name to filter containers

        Returns:
            List of protection container dictionaries
        """
        if fabric_name:
            path = f"/subscriptions/{self.subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.RecoveryServices/vaults/{vault_name}/replicationFabrics/{fabric_name}/replicationProtectionContainers"
        else:
            # Get all protection containers across all fabrics
            fabrics = self.get_replication_fabrics(resource_group, vault_name)
            all_containers = []
            for fabric in fabrics:
                fabric_name = fabric.get('name', '')
                if fabric_name:
                    containers_path = f"/subscriptions/{self.subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.RecoveryServices/vaults/{vault_name}/replicationFabrics/{fabric_name}/replicationProtectionContainers"
                    try:
                        containers = self.list_all(
                            containers_path, api_version="2023-06-01")
                        all_containers.extend(containers)
                    except Exception as e:
                        print(
                            f"Error getting containers for fabric {fabric_name}: {e}")
            return all_containers

        try:
            return self.list_all(path, api_version="2023-06-01")
        except Exception as e:
            print(f"Error getting protection containers: {e}")
            return []

    def validate_replication_readiness(
        self,
        resource_group: str,
        vault_name: str
    ) -> Dict[str, Any]:
        """
        Validate that replication infrastructure is ready

        Args:
            resource_group: Resource group name
            vault_name: Recovery Services Vault name

        Returns:
            Dictionary with readiness status and details
        """
        try:
            # Get protection container mappings
            mappings = self.get_protection_container_mappings(
                resource_group, vault_name)

            # Get fabrics
            fabrics = self.get_replication_fabrics(resource_group, vault_name)

            # Analyze readiness
            healthy_mappings = 0
            paired_mappings = 0
            total_mappings = len(mappings)

            mapping_details = []
            for mapping in mappings:
                properties = mapping.get('properties', {})
                health = properties.get('health', 'Unknown')
                state = properties.get('state', 'Unknown')

                if health == 'Normal':
                    healthy_mappings += 1
                if state == 'Paired':
                    paired_mappings += 1

                mapping_details.append({
                    'name': mapping.get('name', ''),
                    'health': health,
                    'state': state,
                    'source_container': properties.get('sourceProtectionContainerFriendlyName', ''),
                    'target_container': properties.get('targetProtectionContainerFriendlyName', ''),
                    'policy': properties.get('policyFriendlyName', '')
                })

            # Determine overall readiness
            is_ready = (
                total_mappings > 0 and
                healthy_mappings == total_mappings and
                paired_mappings == total_mappings
            )

            return {
                'ready': is_ready,
                'total_mappings': total_mappings,
                'healthy_mappings': healthy_mappings,
                'paired_mappings': paired_mappings,
                'total_fabrics': len(fabrics),
                'mapping_details': mapping_details,
                'summary': f"{paired_mappings}/{total_mappings} mappings paired, {healthy_mappings}/{total_mappings} healthy"
            }

        except Exception as e:
            return {
                'ready': False,
                'error': str(e),
                'summary': f"Error validating replication readiness: {str(e)}"
            }

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
