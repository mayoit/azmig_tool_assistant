"""
Script to create a sample consolidated Excel file with both Landing Zone and Server configurations
"""
import pandas as pd
from pathlib import Path

def create_consolidated_excel_sample():
    """Create a sample consolidated Excel file"""
    
    # Sample data combining both Landing Zone and Server information
    data = [
        {
            # Landing Zone fields
            "Migrate Project Subscription": "12345678-1234-1234-1234-123456789012",
            "Migrate Project Name": "MigrateProject-EastUS",
            "Appliance Type": "VMware",
            "Appliance Name": "MigrateAppliance-VMware-EastUS",
            "Cache Storage Account": "cachestorage001",
            "Cache Storage Resource Group": "rg-storage-eastus",
            "Migrate Resource Group": "migrate-rg",
            
            # Server fields
            "Target Machine": "WEB-SERVER-01",
            "Target Region": "eastus",
            "Target Subscription": "87654321-4321-4321-4321-210987654321",
            "Target RG": "rg-web-servers",
            "Target VNet": "vnet-production",
            "Target Subnet": "subnet-web",
            "Target Machine SKU": "Standard_D4s_v3",
            "Target Disk Type": "Premium_LRS",
            
            # Optional fields
            "Source Machine": "WEB01-ONPREM",
            "Recovery Vault Name": "RecoveryVault-EastUS"
        },
        {
            # Landing Zone fields (same project, different server)
            "Migrate Project Subscription": "12345678-1234-1234-1234-123456789012",
            "Migrate Project Name": "MigrateProject-EastUS",
            "Appliance Type": "VMware", 
            "Appliance Name": "MigrateAppliance-VMware-EastUS",
            "Cache Storage Account": "cachestorage001",
            "Cache Storage Resource Group": "rg-storage-eastus",
            "Migrate Resource Group": "migrate-rg",
            
            # Server fields
            "Target Machine": "DB-SERVER-01",
            "Target Region": "eastus",
            "Target Subscription": "87654321-4321-4321-4321-210987654321",
            "Target RG": "rg-database",
            "Target VNet": "vnet-production",
            "Target Subnet": "subnet-database",
            "Target Machine SKU": "Standard_E8s_v3",
            "Target Disk Type": "Premium_LRS",
            
            # Optional fields
            "Source Machine": "DB01-ONPREM", 
            "Recovery Vault Name": "RecoveryVault-EastUS"
        },
        {
            # Different Landing Zone project
            "Migrate Project Subscription": "11111111-2222-3333-4444-555555555555",
            "Migrate Project Name": "MigrateProject-WestUS",
            "Appliance Type": "HyperV",
            "Appliance Name": "MigrateAppliance-HyperV-WestUS", 
            "Cache Storage Account": "cachestoragewest",
            "Cache Storage Resource Group": "rg-storage-westus",
            "Migrate Resource Group": "migrate-rg-west",
            
            # Server fields
            "Target Machine": "APP-SERVER-01",
            "Target Region": "westus2",
            "Target Subscription": "87654321-4321-4321-4321-210987654321",
            "Target RG": "rg-applications",
            "Target VNet": "vnet-production-west",
            "Target Subnet": "subnet-apps",
            "Target Machine SKU": "Standard_F4s_v2",
            "Target Disk Type": "StandardSSD_LRS",
            
            # Optional fields
            "Source Machine": "APP01-ONPREM",
            "Recovery Vault Name": "RecoveryVault-WestUS"
        }
    ]
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Save to Excel
    output_path = Path("examples") / "consolidated_migration_template.xlsx"
    output_path.parent.mkdir(exist_ok=True)
    
    df.to_excel(output_path, index=False)
    print(f"Created consolidated Excel template: {output_path}")
    
    # Also create a CSV version for reference
    csv_path = Path("examples") / "consolidated_migration_template.csv"
    df.to_csv(csv_path, index=False)
    print(f"Created consolidated CSV template: {csv_path}")

if __name__ == "__main__":
    create_consolidated_excel_sample()