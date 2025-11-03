#!/usr/bin/env python3
"""Create test Excel file for validation testing"""

import sys
import pandas as pd
from pathlib import Path

if len(sys.argv) < 2:
    print("Usage: create_test_excel.py <output_file>")
    sys.exit(1)

output_file = sys.argv[1]

servers_data = [
    {
        "Target Machine Name": "web-server-01",
        "Target Region": "eastus",
        "Target Subscription": "12345678-1234-1234-1234-123456789abc",
        "Target RG": "test-web-rg",
        "Target Vnet": "test-vnet",
        "Target Subnet": "web-subnet",
        "Target Machine Sku": "Standard_D2s_v3",
        "Target Disk Type": "Premium_LRS"
    },
    {
        "Target Machine Name": "db-server-01",
        "Target Region": "eastus",
        "Target Subscription": "12345678-1234-1234-1234-123456789abc",
        "Target RG": "test-db-rg",
        "Target Vnet": "test-vnet",
        "Target Subnet": "db-subnet",
        "Target Machine Sku": "Standard_D4s_v3",
        "Target Disk Type": "Premium_LRS"
    },
    {
        "Target Machine Name": "app-server-01",
        "Target Region": "eastus",
        "Target Subscription": "12345678-1234-1234-1234-123456789abc",
        "Target RG": "test-app-rg",
        "Target Vnet": "test-vnet",
        "Target Subnet": "app-subnet",
        "Target Machine Sku": "Standard_D2s_v3",
        "Target Disk Type": "StandardSSD_LRS"
    }
]

df = pd.DataFrame(servers_data)
df.to_excel(output_file, index=False, sheet_name="Servers")

print(f"{output_file}")  # Output just the filename
