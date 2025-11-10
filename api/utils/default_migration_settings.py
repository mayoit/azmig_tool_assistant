"""Default migration settings for new projects."""

def get_default_migration_settings() -> dict:
    """
    Returns default migration settings for a new project.
    
    These settings define the allowed values for:
    - Target regions (Azure regions)
    - VM SKUs (Azure virtual machine sizes)
    - Disk types (Azure managed disk types)
    
    Returns:
        dict: Default migration settings
    """
    return {
        "allowed_regions": [
            "eastus",
            "eastus2",
            "westus",
            "westus2",
            "centralus",
            "northcentralus",
            "southcentralus",
            "uksouth",
            "ukwest",
            "northeurope",
            "westeurope",
            "francecentral",
            "germanywestcentral",
        ],
        "allowed_vm_skus": [
            # D-series v2 (General Purpose)
            "Standard_DS1_v2",
            "Standard_DS2_v2",
            "Standard_DS3_v2",
            "Standard_DS4_v2",
            "Standard_DS5_v2",
            # D-series v3 (General Purpose - newer)
            "Standard_D2s_v3",
            "Standard_D4s_v3",
            "Standard_D8s_v3",
            "Standard_D16s_v3",
            # E-series v3 (Memory Optimized)
            "Standard_E2s_v3",
            "Standard_E4s_v3",
            "Standard_E8s_v3",
            "Standard_E16s_v3",
            # F-series v2 (Compute Optimized)
            "Standard_F2s_v2",
            "Standard_F4s_v2",
            "Standard_F8s_v2",
            # B-series (Burstable)
            "Standard_B1s",
            "Standard_B2s",
            "Standard_B4ms",
        ],
        "allowed_disk_types": [
            "Premium_LRS",      # Premium SSD (locally redundant)
            "Standard_LRS",     # Standard HDD (locally redundant)
            "StandardSSD_LRS",  # Standard SSD (locally redundant)
            "UltraSSD_LRS",     # Ultra SSD (locally redundant)
            "Premium_ZRS",      # Premium SSD (zone redundant)
            "StandardSSD_ZRS",  # Standard SSD (zone redundant)
        ],
    }
