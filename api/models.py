"""
SQLAlchemy ORM models for database tables.
Defines all 9 core tables for the application.
"""

from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, ForeignKey,
    Text, JSON, Enum as SQLEnum, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from database import Base


# Enums
class UserRole(str, enum.Enum):
    """User role types."""
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class ProjectStatus(str, enum.Enum):
    """Project status types."""
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ValidationStatus(str, enum.Enum):
    """Validation job status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ValidationResultStatus(str, enum.Enum):
    """Individual validation result status."""
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    SKIPPED = "skipped"


class ReplicationState(str, enum.Enum):
    """Server replication state."""
    NOT_STARTED = "not_started"
    INITIALIZING = "initializing"
    REPLICATING = "replicating"
    PROTECTED = "protected"
    FAILED = "failed"
    DISABLED = "disabled"


class ReplicationHealth(str, enum.Enum):
    """Replication health status."""
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


# Models
class User(Base):
    """User accounts table."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(SQLEnum(UserRole), default=UserRole.OPERATOR, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    projects = relationship("Project", back_populates="owner")
    validation_jobs = relationship("ValidationJob", back_populates="created_by_user")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"


class Project(Base):
    """Migration projects table - Each project is tied to an Azure Tenant."""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(ProjectStatus), default=ProjectStatus.ACTIVE, nullable=False)
    
    # Azure Tenant - Required (multiple projects can belong to same tenant)
    azure_tenant_id = Column(String(255), nullable=False, index=True)  # Azure AD Tenant ID
    
    # Azure Authentication
    auth_method = Column(String(50), nullable=True)  # azure_cli, service_principal, managed_identity
    auth_credentials = Column(JSON, nullable=True)  # Encrypted credentials storage (SP client_id, client_secret)
    auth_token = Column(Text, nullable=True)  # Cached access token (encrypted)
    auth_token_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Ownership
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Metadata
    metadata_json = Column(JSON, nullable=True)  # Store custom project metadata (landing zones with subscriptions)

    # Relationships
    owner = relationship("User", back_populates="projects")
    landing_zone_configs = relationship("LandingZoneConfig", back_populates="project", cascade="all, delete-orphan")
    server_configs = relationship("ServerConfig", back_populates="project", cascade="all, delete-orphan")
    validation_jobs = relationship("ValidationJob", back_populates="project", cascade="all, delete-orphan")
    file_uploads = relationship("FileUpload", back_populates="project", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_project_owner_status", "owner_id", "status"),
        Index("idx_project_tenant", "azure_tenant_id"),
    )

    def __repr__(self):
        return f"<Project(id={self.id}, name={self.name}, status={self.status})>"

    @property
    def lz_migrate_projects(self):
        """Return landing zone migrate projects stored in metadata."""
        metadata = self.metadata_json
        if isinstance(metadata, dict):
            projects = metadata.get("lz_migrate_projects", [])
            return projects if isinstance(projects, list) else []
        return []

    @property
    def validation_settings(self):
        """Return validation settings stored in metadata."""
        metadata = self.metadata_json
        if isinstance(metadata, dict):
            settings = metadata.get("validation_settings")
            return settings if isinstance(settings, dict) else None
        return None


class LandingZoneConfig(Base):
    """Landing zone configurations table."""
    __tablename__ = "landing_zone_configs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    # Azure Migrate Project
    migrate_project_name = Column(String(255), nullable=False)
    migrate_project_rg = Column(String(255), nullable=False)
    
    # Recovery Services Vault
    recovery_vault_name = Column(String(255), nullable=False)
    recovery_vault_rg = Column(String(255), nullable=False)
    
    # Cache Storage
    cache_storage_account = Column(String(255), nullable=False)
    cache_storage_rg = Column(String(255), nullable=False)
    auto_create_storage = Column(Boolean, default=True)
    
    # Appliance
    appliance_name = Column(String(255), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="landing_zone_configs")
    validation_results = relationship("LZValidationResult", back_populates="config", cascade="all, delete-orphan")

    # Ensure one config per project
    __table_args__ = (
        UniqueConstraint("project_id", name="uq_one_lz_per_project"),
        Index("idx_lz_project", "project_id"),
    )

    def __repr__(self):
        return f"<LandingZoneConfig(id={self.id}, project_id={self.project_id})>"


class ServerConfig(Base):
    """Server configurations table."""
    __tablename__ = "server_configs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    # Server identification
    target_machine_name = Column(String(255), nullable=False)
    
    # Target configuration
    target_region = Column(String(100), nullable=False)
    target_subscription = Column(String(255), nullable=False)
    target_resource_group = Column(String(255), nullable=False)
    target_vnet = Column(String(255), nullable=False)
    target_subnet = Column(String(255), nullable=False)
    target_machine_sku = Column(String(100), nullable=False)
    target_disk_type = Column(String(50), nullable=False)
    
    # Appliance selection - stores ID reference to Landing Zone migrate project
    # Note: This is a logical reference, not a FK constraint since LZ data is in JSON
    appliance_id = Column(Integer, nullable=True, index=True)
    
    # Auto-populated fields from selected appliance (denormalized for performance)
    migrate_project_name = Column(String(255), nullable=True, index=True)
    appliance_name = Column(String(255), nullable=True)
    appliance_type = Column(String(50), nullable=True)
    recovery_vault_name = Column(String(255), nullable=True)
    cache_storage_account = Column(String(255), nullable=True)
    cache_storage_rg = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Metadata
    metadata_json = Column(JSON, nullable=True)  # Store additional server details

    # Relationships
    project = relationship("Project", back_populates="server_configs")
    validation_results = relationship("ServerValidationResult", back_populates="server", cascade="all, delete-orphan")
    replication_status = relationship("ReplicationStatus", back_populates="server", uselist=False, cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        UniqueConstraint("project_id", "target_machine_name", name="uq_server_per_project"),
        Index("idx_server_project_name", "project_id", "target_machine_name"),
        Index("idx_server_region", "target_region"),
        Index("idx_server_migrate_project", "migrate_project_name"),
    )

    def __repr__(self):
        return f"<ServerConfig(id={self.id}, name={self.target_machine_name})>"


class LZValidationResult(Base):
    """Landing zone validation results table."""
    __tablename__ = "lz_validation_results"

    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, ForeignKey("landing_zone_configs.id"), nullable=False)
    validation_job_id = Column(Integer, ForeignKey("validation_jobs.id"), nullable=True)
    
    # Validation details
    validation_type = Column(String(100), nullable=False)  # access, appliance, storage, quota
    status = Column(SQLEnum(ValidationResultStatus), nullable=False)
    message = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)  # Additional validation details
    
    # Timestamps
    validated_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    config = relationship("LandingZoneConfig", back_populates="validation_results")
    validation_job = relationship("ValidationJob", back_populates="lz_results")

    # Indexes
    __table_args__ = (
        Index("idx_lz_validation_config", "config_id"),
        Index("idx_lz_validation_job", "validation_job_id"),
        Index("idx_lz_validation_type_status", "validation_type", "status"),
    )

    def __repr__(self):
        return f"<LZValidationResult(id={self.id}, type={self.validation_type}, status={self.status})>"


class ServerValidationResult(Base):
    """Server validation results table."""
    __tablename__ = "server_validation_results"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("server_configs.id"), nullable=False)
    validation_job_id = Column(Integer, ForeignKey("validation_jobs.id"), nullable=True)
    
    # Validation details
    validation_type = Column(String(100), nullable=False)  # region, rg, vnet, sku, disk, discovery, rbac, replication
    status = Column(SQLEnum(ValidationResultStatus), nullable=False)
    message = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)  # Additional validation details
    
    # Timestamps
    validated_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    server = relationship("ServerConfig", back_populates="validation_results")
    validation_job = relationship("ValidationJob", back_populates="server_results")

    # Indexes
    __table_args__ = (
        Index("idx_server_validation_server", "server_id"),
        Index("idx_server_validation_job", "validation_job_id"),
        Index("idx_server_validation_type_status", "validation_type", "status"),
    )

    def __repr__(self):
        return f"<ServerValidationResult(id={self.id}, type={self.validation_type}, status={self.status})>"


class ReplicationStatus(Base):
    """Server replication status tracking table."""
    __tablename__ = "replication_status"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("server_configs.id"), nullable=False, unique=True)
    
    # Replication state
    state = Column(SQLEnum(ReplicationState), default=ReplicationState.NOT_STARTED, nullable=False)
    health = Column(SQLEnum(ReplicationHealth), default=ReplicationHealth.UNKNOWN, nullable=False)
    
    # Replication details
    vault_name = Column(String(255), nullable=True)
    protected_item_id = Column(String(500), nullable=True)  # Azure resource ID
    last_sync_time = Column(DateTime(timezone=True), nullable=True)
    rpo_minutes = Column(Integer, nullable=True)  # Recovery Point Objective in minutes
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    
    # Timestamps
    replication_started_at = Column(DateTime(timezone=True), nullable=True)
    last_checked_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    server = relationship("ServerConfig", back_populates="replication_status")

    # Indexes
    __table_args__ = (
        Index("idx_replication_state_health", "state", "health"),
        Index("idx_replication_vault", "vault_name"),
    )

    def __repr__(self):
        return f"<ReplicationStatus(id={self.id}, server_id={self.server_id}, state={self.state})>"


class FileUpload(Base):
    """File upload tracking table."""
    __tablename__ = "file_uploads"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    # File details
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)  # Path in storage
    file_size_bytes = Column(Integer, nullable=False)
    file_type = Column(String(50), nullable=False)  # xlsx, xls, csv
    
    # Processing status
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    processed = Column(Boolean, default=False)
    servers_count = Column(Integer, nullable=True)  # Number of servers in file
    errors_count = Column(Integer, default=0)
    error_details = Column(JSON, nullable=True)
    
    # Timestamps
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="file_uploads")
    uploaded_by = relationship("User")

    # Indexes
    __table_args__ = (
        Index("idx_upload_project_date", "project_id", "uploaded_at"),
    )

    def __repr__(self):
        return f"<FileUpload(id={self.id}, filename={self.filename})>"


class ValidationJob(Base):
    """Validation job tracking table for background processing."""
    __tablename__ = "validation_jobs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    # Job details
    job_type = Column(String(50), nullable=False)  # landing_zone, servers, full
    status = Column(SQLEnum(ValidationStatus), default=ValidationStatus.PENDING, nullable=False)
    celery_task_id = Column(String(255), nullable=True, unique=True)  # Celery task UUID
    
    # Progress tracking
    total_items = Column(Integer, default=0)
    processed_items = Column(Integer, default=0)
    passed_items = Column(Integer, default=0)
    warning_items = Column(Integer, default=0)
    failed_items = Column(Integer, default=0)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    
    # Timestamps
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="validation_jobs")
    created_by_user = relationship("User", back_populates="validation_jobs")
    lz_results = relationship("LZValidationResult", back_populates="validation_job")
    server_results = relationship("ServerValidationResult", back_populates="validation_job")

    # Indexes
    __table_args__ = (
        Index("idx_job_project_status", "project_id", "status"),
        Index("idx_job_celery_task", "celery_task_id"),
    )

    def __repr__(self):
        return f"<ValidationJob(id={self.id}, type={self.job_type}, status={self.status})>"


class ValidationEvent(Base):
    """Validation event log table - Azure Activity Log style event logging."""
    __tablename__ = "validation_events"

    id = Column(Integer, primary_key=True, index=True)
    validation_job_id = Column(Integer, ForeignKey("validation_jobs.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    # Event identification
    event_name = Column(String(100), nullable=False)  # e.g., "Access Validation", "Appliance Health Check"
    event_category = Column(String(50), nullable=False)  # landing_zone, server, appliance, storage, quota
    validation_type = Column(String(100), nullable=False)  # access, appliance, storage, quota, region, vnet, etc.
    
    # Target resource info
    resource_type = Column(String(100), nullable=True)  # MigrateProject, AppLandingZone, ServerConfig
    resource_name = Column(String(500), nullable=True)  # Name of the resource being validated
    resource_id = Column(String(500), nullable=True)  # Azure resource ID if applicable
    
    # Event status
    status = Column(SQLEnum(ValidationResultStatus), nullable=False)
    operation_status = Column(String(20), nullable=False)  # Started, InProgress, Completed, Failed
    
    # Event details
    message = Column(Text, nullable=True)  # Human-readable message
    details = Column(JSON, nullable=True)  # Detailed validation results
    error_message = Column(Text, nullable=True)  # Error if failed
    
    # Request/Response info (like Azure Activity Log)
    request_payload = Column(JSON, nullable=True)  # What was being validated
    response_payload = Column(JSON, nullable=True)  # Validation result details
    
    # Timestamps (Azure-style)
    event_timestamp = Column(DateTime(timezone=True), server_default=func.now())  # When event occurred
    submitted_at = Column(DateTime(timezone=True), nullable=True)  # When validation started
    completed_at = Column(DateTime(timezone=True), nullable=True)  # When validation completed
    duration_ms = Column(Integer, nullable=True)  # Duration in milliseconds
    
    # Relationships
    validation_job = relationship("ValidationJob")
    project = relationship("Project")
    
    # Indexes for fast querying (like Azure Activity Log filtering)
    __table_args__ = (
        Index("idx_event_job_timestamp", "validation_job_id", "event_timestamp"),
        Index("idx_event_project_timestamp", "project_id", "event_timestamp"),
        Index("idx_event_category_type", "event_category", "validation_type"),
        Index("idx_event_status", "status"),
        Index("idx_event_operation_status", "operation_status"),
    )

    def __repr__(self):
        return f"<ValidationEvent(id={self.id}, name={self.event_name}, status={self.status}, operation={self.operation_status})>"


class MigrateProjectValidation(Base):
    """Stores validation results for individual Azure Migrate Projects."""
    __tablename__ = "migrate_project_validations"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    migrate_project_index = Column(Integer, nullable=False)  # Index in project's lz_migrate_projects array
    
    # Validation status
    status = Column(SQLEnum(ValidationResultStatus), nullable=False)
    
    # Validation results (JSON structure matching ProjectReadinessResult)
    access_result = Column(JSON, nullable=True)  # AccessValidationResult
    appliance_result = Column(JSON, nullable=True)  # ApplianceHealthResult
    storage_result = Column(JSON, nullable=True)  # StorageCacheResult
    quota_result = Column(JSON, nullable=True)  # QuotaValidationResult
    
    # Summary
    overall_status = Column(String(20), nullable=False)  # PASSED, WARNING, FAILED
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    project = relationship("Project", backref="migrate_project_validations")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("project_id", "migrate_project_index", name="uq_project_mp_index"),
        Index("idx_mp_validation_project", "project_id"),
        Index("idx_mp_validation_status", "status"),
    )

    def __repr__(self):
        return f"<MigrateProjectValidation(id={self.id}, project_id={self.project_id}, index={self.migrate_project_index}, status={self.status})>"


class AppLandingZoneValidation(Base):
    """Stores validation results for individual Application Landing Zones within Migrate Projects."""
    __tablename__ = "app_landing_zone_validations"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    migrate_project_index = Column(Integer, nullable=False)  # Parent migrate project index
    app_lz_index = Column(Integer, nullable=False)  # Index in app_landing_zones array
    
    # Validation status
    status = Column(SQLEnum(ValidationResultStatus), nullable=False)
    
    # Validation results (JSON structure)
    subscription_access = Column(JSON, nullable=True)  # Subscription access validation
    region_validation = Column(JSON, nullable=True)  # Region availability
    storage_account_validation = Column(JSON, nullable=True)  # Cache storage account
    resource_group_validation = Column(JSON, nullable=True)  # Resource group access
    
    # Summary
    overall_status = Column(String(20), nullable=False)  # PASSED, WARNING, FAILED
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    project = relationship("Project", backref="app_landing_zone_validations")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("project_id", "migrate_project_index", "app_lz_index", name="uq_project_mp_alz_index"),
        Index("idx_alz_validation_project", "project_id"),
        Index("idx_alz_validation_status", "status"),
    )

    def __repr__(self):
        return f"<AppLandingZoneValidation(id={self.id}, project_id={self.project_id}, mp_index={self.migrate_project_index}, alz_index={self.app_lz_index}, status={self.status})>"

