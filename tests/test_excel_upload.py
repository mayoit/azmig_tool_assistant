#!/usr/bin/env python3
"""Quick test of Excel upload endpoint"""

import requests
import pandas as pd
from pathlib import Path
import tempfile

# Configuration
BASE_URL = "http://localhost:8000/api"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"

# Login
print("Logging in...")
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
)
token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Get latest project
print("Getting project...")
projects_response = requests.get(f"{BASE_URL}/projects?page=1&page_size=1", headers=headers)
project_id = projects_response.json()["items"][0]["id"]
print(f"Project ID: {project_id}")

# Create Excel file
print("Creating Excel file...")
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
    }
]

df = pd.DataFrame(servers_data)
excel_file = Path(tempfile.gettempdir()) / "test_upload.xlsx"
df.to_excel(excel_file, index=False, sheet_name="Servers")

print(f"Excel columns: {list(df.columns)}")
print(f"Excel file: {excel_file}")

# Upload
print("Uploading...")
with open(excel_file, "rb") as f:
    files = {"file": ("test_servers.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    upload_response = requests.post(
        f"{BASE_URL}/projects/{project_id}/servers/upload?update_existing=true",
        headers=headers,
        files=files
    )

print(f"Status: {upload_response.status_code}")
if upload_response.status_code == 200:
    result = upload_response.json()
    print(f"✓ Success: {result['message']}")
    print(f"  Servers created: {result['servers_created']}")
    print(f"  Servers updated: {result['servers_updated']}")
else:
    print(f"✗ Error: {upload_response.json()}")

# Cleanup
excel_file.unlink()
