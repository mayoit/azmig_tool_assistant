"""
Appliance Validator - Azure Migrate appliance health validation

Handles validation of Azure Migrate appliances:
- Appliance connectivity and heartbeat status
- Health status monitoring
- Active alerts and issues
"""
from typing import List
from datetime import datetime, timedelta
from azure.core.credentials import TokenCredential

from ...core.models import (
    MigrateProjectConfig,
    ApplianceHealthResult,
    ValidationStatus,
    ApplianceInfo,
    HealthStatus,
    ApplianceType
)
from ...clients.azure_client import AzureMigrateApiClient


class ApplianceValidator:
    """
    Validates Azure Migrate appliance health and connectivity
    
    Checks:
    - Appliance availability and responsiveness
    - Last heartbeat timestamp
    - Health status (Healthy, Warning, Unhealthy, Critical)
    - Active alerts and issues
    """

    def __init__(self, credential: TokenCredential):
        """
        Initialize appliance validator

        Args:
            credential: Azure token credential for API calls
        """
        self.credential = credential
        self._migrate_clients = {}

    def _get_migrate_client(self, subscription_id: str) -> AzureMigrateApiClient:
        """Get or create cached Azure Migrate API client"""
        if subscription_id not in self._migrate_clients:
            self._migrate_clients[subscription_id] = AzureMigrateApiClient(
                self.credential, subscription_id
            )
        return self._migrate_clients[subscription_id]

    def validate(self, config: MigrateProjectConfig) -> ApplianceHealthResult:
        """
        Validate health status of replication appliances

        Args:
            config: Migrate project configuration

        Returns:
            ApplianceHealthResult with detailed appliance status
        """
        try:
            migrate_client = self._get_migrate_client(config.migrate_project_subscription)

            # Get appliances from Azure Migrate project
            appliances_data = migrate_client.get_appliances(
                config.migrate_resource_group,
                config.migrate_project_name
            )

            appliances: List[ApplianceInfo] = []
            unhealthy_count = 0

            for appliance_data in appliances_data:
                appliance_info = self._process_appliance_data(appliance_data, config)
                appliances.append(appliance_info)
                
                if appliance_info.needs_attention():
                    unhealthy_count += 1

            # Determine overall status and message
            status, message = self._determine_overall_status(appliances, unhealthy_count)

            return ApplianceHealthResult(
                subscription_id=config.subscription_id,
                status=status,
                appliances=appliances,
                unhealthy_count=unhealthy_count,
                message=message
            )

        except Exception as e:
            return ApplianceHealthResult(
                subscription_id=config.subscription_id,
                status=ValidationStatus.FAILED,
                appliances=[],
                unhealthy_count=0,
                message=f"Error validating appliance health: {str(e)}"
            )

    def _process_appliance_data(self, appliance_data: dict, config: MigrateProjectConfig) -> ApplianceInfo:
        """
        Process raw appliance data into ApplianceInfo object

        Args:
            appliance_data: Raw appliance data from Azure API
            config: Project configuration for defaults

        Returns:
            ApplianceInfo with processed health status
        """
        properties = appliance_data.get('properties', {})

        # Determine appliance type
        appliance_type = self._parse_appliance_type(properties.get('applianceType', 'VMWARE'))

        # Get health status and alerts
        health_status, alerts = self._analyze_appliance_health(properties)

        return ApplianceInfo(
            name=appliance_data.get('name', 'Unknown'),
            health_status=health_status,
            appliance_type=appliance_type,
            subscription_id=config.subscription_id,
            resource_group=config.migrate_resource_group,
            region=appliance_data.get('location', config.region),
            alerts=alerts,
            last_heartbeat=properties.get('lastHeartbeatUtc', ''),
            version=properties.get('version', 'Unknown')
        )

    def _parse_appliance_type(self, appliance_type_str: str) -> ApplianceType:
        """Parse appliance type string to enum"""
        try:
            return ApplianceType[appliance_type_str.upper()]
        except (KeyError, AttributeError):
            return ApplianceType.VMWARE

    def _analyze_appliance_health(self, properties: dict) -> tuple[HealthStatus, List[str]]:
        """
        Analyze appliance health status and generate alerts

        Args:
            properties: Appliance properties from Azure API

        Returns:
            Tuple of (HealthStatus, list of alert messages)
        """
        health_status = HealthStatus.HEALTHY
        alerts = []

        # Check heartbeat timing
        last_heartbeat_str = properties.get('lastHeartbeatUtc', '')
        if last_heartbeat_str:
            try:
                last_heartbeat = datetime.fromisoformat(
                    last_heartbeat_str.replace('Z', '+00:00'))
                time_since_heartbeat = datetime.now(last_heartbeat.tzinfo) - last_heartbeat

                if time_since_heartbeat > timedelta(days=1):
                    health_status = HealthStatus.UNHEALTHY
                    alerts.extend([
                        "Last heartbeat > 24 hours ago",
                        "Appliance not communicating"
                    ])
                elif time_since_heartbeat > timedelta(hours=6):
                    health_status = HealthStatus.WARNING
                    alerts.append("Last heartbeat > 6 hours ago")
            except Exception:
                health_status = HealthStatus.WARNING
                alerts.append("Unable to parse heartbeat timestamp")

        # Check explicit health state
        health_state = properties.get('healthState', 'Unknown')
        if health_state.lower() in ['unhealthy', 'critical', 'error']:
            health_status = HealthStatus.UNHEALTHY
            if not alerts:
                alerts.append(f"Health state: {health_state}")
        elif health_state.lower() == 'warning':
            if health_status == HealthStatus.HEALTHY:
                health_status = HealthStatus.WARNING
            if not alerts:
                alerts.append(f"Health state: {health_state}")

        return health_status, alerts

    def _determine_overall_status(self, appliances: List[ApplianceInfo], unhealthy_count: int) -> tuple[ValidationStatus, str]:
        """
        Determine overall validation status and message

        Args:
            appliances: List of appliance info objects
            unhealthy_count: Count of unhealthy appliances

        Returns:
            Tuple of (ValidationStatus, descriptive message)
        """
        if not appliances:
            return ValidationStatus.WARNING, "No appliances found in project"
        elif unhealthy_count == 0:
            return ValidationStatus.OK, f"Found {len(appliances)} healthy appliance(s)"
        elif unhealthy_count < len(appliances):
            return ValidationStatus.WARNING, f"Found {len(appliances)} appliance(s), {unhealthy_count} need(s) attention"
        else:
            return ValidationStatus.FAILED, f"All {len(appliances)} appliance(s) are unhealthy"