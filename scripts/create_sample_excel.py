"""
Create a sample Excel template for Azure bulk migration
"""
import pandas as pd
from pathlib import Path

# Sample migration data - using Title Case column names to match user's template
sample_data = {
    "Target Subscription": [
        "SubA",
        "SubB",
        "SubA",
        "SubB"
    ],
    "Target RG": [
        "RG-App",
        "RG-Web",
        "RG-DB",
        "RG-App"
    ],
    "Target VNet": [
        "VNet-East",
        "VNet-West",
        "VNet-East",
        "VNet-West"
    ],
    "Target Subnet": [
        "Subnet-01",
        "Subnet-02",
        "Subnet-03",
        "Subnet-01"
    ],
    "Target Machine SKU": [
        "Standard_D4s_v3",
        "Standard_D2s_v3",
        "Standard_E8s_v3",
        "Standard_D4s_v3"
    ],
    "Target Disk Type": [
        "Premium_LRS",
        "Standard_LRS",
        "Premium_LRS",
        "Premium_LRS"
    ],
    "Target Region": [
        "eastus",
        "westus",
        "eastus",
        "westus"
    ],
    "Target Machine": [
        "app01",
        "web01",
        "db01",
        "app02"
    ],
    "Source Machine": [
        "onprem-app-01",
        "onprem-web-01",
        "onprem-db-01",
        ""
    ],
    "Recovery Vault Name": [
        "vault-east",
        "vault-west",
        "vault-east",
        "vault-west"
    ]
}

# Create DataFrame
df = pd.DataFrame(sample_data)

# Save to Excel
output_path = Path(__file__).parent.parent / "tests/data/sample_migration.xlsx"
df.to_excel(output_path, index=False, sheet_name="Migration")

print(f"✓ Sample Excel template created: {output_path}")
print(f"  Records: {len(df)}")
print(f"  Columns: {', '.join(df.columns)}")
