"""
Create sample Excel template for server configurations.
This template can be used to bulk upload server migration settings.
"""

import pandas as pd
from pathlib import Path

# Sample server configurations
sample_data = [
    {
        "Target Machine Name": "web-server-01",
        "Target Region": "eastus",
        "Target Subscription": "12345678-1234-1234-1234-123456789abc",
        "Target RG": "migration-web-rg",
        "Target Vnet": "migration-vnet",
        "Target Subnet": "web-subnet",
        "Target Machine Sku": "Standard_D2s_v3",
        "Target Disk Type": "Premium_LRS",
    },
    {
        "Target Machine Name": "db-server-01",
        "Target Region": "eastus",
        "Target Subscription": "12345678-1234-1234-1234-123456789abc",
        "Target RG": "migration-db-rg",
        "Target Vnet": "migration-vnet",
        "Target Subnet": "database-subnet",
        "Target Machine Sku": "Standard_D4s_v3",
        "Target Disk Type": "Premium_LRS",
    },
    {
        "Target Machine Name": "app-server-01",
        "Target Region": "westus2",
        "Target Subscription": "12345678-1234-1234-1234-123456789abc",
        "Target RG": "migration-app-rg",
        "Target Vnet": "migration-vnet-west",
        "Target Subnet": "app-subnet",
        "Target Machine Sku": "Standard_D2s_v3",
        "Target Disk Type": "StandardSSD_LRS",
    },
    {
        "Target Machine Name": "cache-server-01",
        "Target Region": "eastus",
        "Target Subscription": "12345678-1234-1234-1234-123456789abc",
        "Target RG": "migration-cache-rg",
        "Target Vnet": "migration-vnet",
        "Target Subnet": "cache-subnet",
        "Target Machine Sku": "Standard_D2s_v3",
        "Target Disk Type": "Premium_LRS",
    },
    {
        "Target Machine Name": "monitoring-server-01",
        "Target Region": "centralus",
        "Target Subscription": "87654321-4321-4321-4321-cba987654321",
        "Target RG": "migration-monitoring-rg",
        "Target Vnet": "migration-vnet-central",
        "Target Subnet": "monitoring-subnet",
        "Target Machine Sku": "Standard_B2s",
        "Target Disk Type": "Standard_LRS",
    },
]

# Create DataFrame
df = pd.DataFrame(sample_data)

# Ensure examples directory exists
examples_dir = Path(__file__).parent.parent / "examples"
examples_dir.mkdir(exist_ok=True)

# Save to Excel
output_file = examples_dir / "server_template.xlsx"
df.to_excel(output_file, index=False, sheet_name="Servers")

print(f"✓ Created Excel template: {output_file}")
print(f"  Rows: {len(df)}")
print(f"  Columns: {', '.join(df.columns)}")
print("\nThis template can be used to bulk upload server configurations via:")
print("  POST /api/projects/{project_id}/servers/upload")
