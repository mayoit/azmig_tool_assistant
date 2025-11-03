# UI Mockups & Business Scenarios

## Table of Contents
1. [Screen Mockups](#screen-mockups)
2. [User Flows](#user-flows)
3. [Business Scenarios](#business-scenarios)
4. [Feature Coverage Matrix](#feature-coverage-matrix)

---

## Screen Mockups

### 1. Login Page

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                   🚀 Azure Migration Tool                   │
│                                                             │
│              ┌───────────────────────────────┐             │
│              │                               │             │
│              │  Email                        │             │
│              │  ┌─────────────────────────┐ │             │
│              │  │ user@example.com        │ │             │
│              │  └─────────────────────────┘ │             │
│              │                               │             │
│              │  Password                     │             │
│              │  ┌─────────────────────────┐ │             │
│              │  │ ●●●●●●●●●●●●●●●●        │ │             │
│              │  └─────────────────────────┘ │             │
│              │                               │             │
│              │  ┌─────────────────────────┐ │             │
│              │  │      Login              │ │             │
│              │  └─────────────────────────┘ │             │
│              │                               │             │
│              │  Don't have an account?       │             │
│              │  [Register]                   │             │
│              │                               │             │
│              └───────────────────────────────┘             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Features**:
- Email/password authentication
- "Remember me" checkbox
- "Forgot password" link
- Registration link

---

### 2. Projects Dashboard (Home Page)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ ☰ Azure Migration Tool                      👤 John Doe ▼    🔔    ⚙      │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  My Migration Projects                                  [+ New Project]      │
│  ────────────────────────────────────────────────────────────────────────   │
│                                                                              │
│  ┌──────────────────────────┐  ┌──────────────────────────┐  ┌────────────┐│
│  │ 📁 EMEA Migration 2025   │  │ 📁 APAC Datacenter Move │  │ 📁 US Prod ││
│  │ ─────────────────────── │  │ ─────────────────────── │  │ Migration  ││
│  │                          │  │                          │  │ ──────────  ││
│  │ Status: Active           │  │ Status: In Progress      │  │ Status:    ││
│  │ Servers: 245             │  │ Servers: 87              │  │ Completed  ││
│  │ Validated: 220 ✓         │  │ Validated: 45 ⚠         │  │ Servers: 12││
│  │ Replicating: 180 🔄     │  │ Replicating: 12 🔄      │  │ Done: 12 ✓ ││
│  │                          │  │                          │  │            ││
│  │ Owner: John Doe          │  │ Owner: Jane Smith        │  │ Owner: Me  ││
│  │ Created: Oct 1, 2025     │  │ Created: Oct 15, 2025    │  │ Oct 20     ││
│  │                          │  │                          │  │            ││
│  │ [Open Project]           │  │ [Open Project]           │  │ [Archive]  ││
│  └──────────────────────────┘  └──────────────────────────┘  └────────────┘│
│                                                                              │
│  Recent Activity                                                             │
│  ──────────────────────────────────────────────────────────────────────     │
│  • Oct 30, 10:45 AM - Server validation completed (EMEA Migration 2025)     │
│  • Oct 30, 09:30 AM - 50 servers uploaded (EMEA Migration 2025)            │
│  • Oct 29, 04:15 PM - Landing zone validated (APAC Datacenter Move)        │
│  • Oct 29, 02:00 PM - New project created (APAC Datacenter Move)           │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Features**:
- Project cards with key metrics
- Quick status overview (active, in progress, completed)
- Server counts and validation status
- Recent activity feed
- Create new project button
- User menu with logout

---

### 3. Project Detail Page (Main Navigation)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ ← Back to Projects        EMEA Migration 2025           👤 John Doe ▼        │
├──────┬───────────────────────────────────────────────────────────────────────┤
│      │                                                                       │
│ 🏠   │  Project Overview                                                     │
│ Home │  ═══════════════════════════════════════════════════════════════     │
│      │                                                                       │
│ 🔧   │  Subscription: xxxxx-xxxx-xxxx-xxxx                                  │
│ LZ   │  Created: October 1, 2025                                            │
│ Setup│  Status: Active                                                       │
│      │                                                                       │
│ 🖥️   │  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐       │
│Servers│  │  Total Servers  │ │  Validated      │ │  Replicating    │       │
│      │  │       245       │ │      220        │ │       180       │       │
│      │  │                 │ │   90% ✓         │ │   73% 🔄        │       │
│ ✓    │  └─────────────────┘ └─────────────────┘ └─────────────────┘       │
│Validate│                                                                     │
│      │  Quick Actions                                                        │
│ 🔄   │  ──────────────────────────────────────────────────────────────      │
│Replicate│ [Upload Excel]  [Validate Landing Zone]  [Validate Servers]       │
│      │                                                                       │
│ 📊   │  Validation Status Summary                                            │
│Reports│  ──────────────────────────────────────────────────────────────      │
│      │                                                                       │
│ ⚙    │  Landing Zone:  ✓ Access  ✓ Appliance  ⚠ Storage  ✓ Quota          │
│Settings│                                                                      │
│      │  Servers Status:                                                      │
│      │    ✓ Passed: 220 servers                                             │
│      │    ⚠ Warnings: 15 servers                                            │
│      │    ✗ Failed: 10 servers                                              │
│      │                                                                       │
│      │  Last Validation: Oct 30, 2025 10:45 AM                              │
│      │  [View Detailed Results →]                                           │
│      │                                                                       │
└──────┴───────────────────────────────────────────────────────────────────────┘
```

**Features**:
- Sidebar navigation with icons
- Project overview with key metrics
- Quick action buttons
- Status summary cards
- Validation status breakdown
- Link to detailed results

---

### 4. Landing Zone Configuration Page

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ EMEA Migration 2025 > Landing Zone Setup                                     │
├──────┬───────────────────────────────────────────────────────────────────────┤
│      │                                                                       │
│ 🏠   │  Landing Zone Configuration                                           │
│ Home │  ═══════════════════════════════════════════════════════════════     │
│      │                                                                       │
│ 🔧   │  Azure Migrate Project                                                │
│►LZ   │  ┌─────────────────────────────────────────────────────────────┐     │
│ Setup│  │ Project Name        [EMEA-Migrate-Project-01            ]  │     │
│      │  │ Resource Group      [rg-migrate-emea                    ]  │     │
│ 🖥️   │  │ Subscription ID     [xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx ]  │     │
│Servers│  └─────────────────────────────────────────────────────────────┘     │
│      │                                                                       │
│ ✓    │  Recovery Services Vault                                              │
│Validate│  ┌─────────────────────────────────────────────────────────────┐     │
│      │  │ Vault Name          [vault-emea-recovery                ]  │     │
│ 🔄   │  │ Resource Group      [rg-recovery-emea                   ]  │     │
│Replicate└─────────────────────────────────────────────────────────────┘     │
│      │                                                                       │
│ 📊   │  Cache Storage Account                                                │
│Reports│  ┌─────────────────────────────────────────────────────────────┐     │
│      │  │ Storage Account     [stcacheemea                        ]  │     │
│ ⚙    │  │ Resource Group      [rg-cache-emea                      ]  │     │
│Settings│  │ [✓] Auto-create if missing                               │     │
│      │  └─────────────────────────────────────────────────────────────┘     │
│      │                                                                       │
│      │  Appliance                                                            │
│      │  ┌─────────────────────────────────────────────────────────────┐     │
│      │  │ Appliance Name      [EMEA-Appliance-01                  ]  │     │
│      │  └─────────────────────────────────────────────────────────────┘     │
│      │                                                                       │
│      │  [Save Configuration]  [Validate Landing Zone]                       │
│      │                                                                       │
│      │  Last Validation: Oct 30, 2025 9:15 AM                               │
│      │  Status: ✓ All checks passed                                         │
│      │                                                                       │
└──────┴───────────────────────────────────────────────────────────────────────┘
```

**Features**:
- Form fields for all LZ components
- Auto-create option for storage
- Save and validate buttons
- Last validation status display
- Form validation and error messages

---

### 5. Servers Management Page

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ EMEA Migration 2025 > Servers                                                │
├──────┬───────────────────────────────────────────────────────────────────────┤
│      │                                                                       │
│ 🏠   │  Server Configurations                               245 servers      │
│ Home │  ═══════════════════════════════════════════════════════════════     │
│      │                                                                       │
│ 🔧   │  [📤 Upload Excel]  [+ Add Server]  [🔄 Refresh]  [⬇️ Download]      │
│ LZ   │                                                                       │
│ Setup│  🔍 Search: [_________________]  Filter: [All ▼] [Region ▼] [Status ▼]│
│      │                                                                       │
│►🖥️   │  ┌─────────────────────────────────────────────────────────────────┐│
│Servers│  │☑ Server Name    │Region    │RG      │VNet   │Status │Actions ││
│      │  ├─────────────────────────────────────────────────────────────────┤│
│ ✓    │  │☑ WEB-SERVER-01  │East US   │rg-web  │vnet-01│ ✓ OK  │[👁][✏]││
│Validate│  │☑ WEB-SERVER-02  │East US   │rg-web  │vnet-01│ ✓ OK  │[👁][✏]││
│      │  │☑ DB-SERVER-01   │East US 2 │rg-db   │vnet-02│ ⚠ Warn│[👁][✏]││
│ 🔄   │  │☑ APP-SERVER-01  │West US   │rg-app  │vnet-03│ ✗ Fail│[👁][✏]││
│Replicate│  │☑ FILE-SERVER-01 │East US   │rg-file │vnet-01│ - New │[👁][✏]││
│      │  │☑ CACHE-SERVER-01│East US   │rg-cache│vnet-01│ ✓ OK  │[👁][✏]││
│ 📊   │  │☑ API-SERVER-01  │Central US│rg-api  │vnet-04│ ⚠ Warn│[👁][✏]││
│Reports│  │  ... (showing 1-7 of 245)                                      ││
│      │  └─────────────────────────────────────────────────────────────────┘│
│ ⚙    │                                                                       │
│Settings│  Selected: 3 servers  [Validate Selected]  [Delete Selected]        │
│      │                                                                       │
│      │  Pagination: ◄ 1 2 3 ... 35 ►                      Show: [20 ▼]     │
│      │                                                                       │
└──────┴───────────────────────────────────────────────────────────────────────┘
```

**Features**:
- Upload Excel button (prominent)
- Add individual server manually
- Search and filter capabilities
- Bulk select checkboxes
- Status indicators (✓ OK, ⚠ Warning, ✗ Failed, - New)
- Quick actions (view, edit) per server
- Bulk operations (validate, delete)
- Pagination for large datasets
- Download results

---

### 6. Excel Upload Modal

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Upload Server Configuration                                            [✕]   │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Step 1: Download Template (Optional)                                        │
│  ─────────────────────────────────────────────────────────────────────       │
│  [📥 Download Excel Template]                                                │
│                                                                              │
│  Step 2: Upload Your Excel File                                             │
│  ─────────────────────────────────────────────────────────────────────       │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────┐         │
│  │                                                                │         │
│  │                    📂 Drag & Drop Excel File                   │         │
│  │                          or                                    │         │
│  │                    [Choose File]                               │         │
│  │                                                                │         │
│  │              Supported formats: .xlsx, .xls                    │         │
│  │                                                                │         │
│  └────────────────────────────────────────────────────────────────┘         │
│                                                                              │
│  Selected File: emea_servers.xlsx (245 KB)                                  │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%                                      │
│                                                                              │
│  ✓ File uploaded successfully                                               │
│  ✓ 245 servers found                                                        │
│  ⚠ 5 rows have warnings (missing optional fields)                           │
│  ✗ 2 rows have errors (invalid region names)                                │
│                                                                              │
│  [View Errors]  [Download Error Report]                                     │
│                                                                              │
│  Options:                                                                    │
│  [✓] Replace existing servers with same names                               │
│  [✓] Validate configurations after upload                                   │
│                                                                              │
│  [Cancel]                                    [Import 243 Valid Servers]     │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Features**:
- Template download link
- Drag & drop zone
- File browser fallback
- Upload progress bar
- Validation summary (success, warnings, errors)
- Error report download
- Import options (replace, auto-validate)
- Clear action buttons

---

### 7. Server Validation Results Page

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ EMEA Migration 2025 > Validation Results                                     │
├──────┬───────────────────────────────────────────────────────────────────────┤
│      │                                                                       │
│ 🏠   │  Server Validation Results                     Last run: Oct 30, 10:45│
│ Home │  ═══════════════════════════════════════════════════════════════     │
│      │                                                                       │
│ 🔧   │  Summary                                                              │
│ LZ   │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐               │
│ Setup│  │  Total   │ │  Passed  │ │ Warnings │ │  Failed  │               │
│      │  │   245    │ │   220    │ │    15    │ │    10    │               │
│►🖥️   │  │          │ │  90% ✓   │ │   6% ⚠   │ │   4% ✗   │               │
│Servers│  └──────────┘ └──────────┘ └──────────┘ └──────────┘               │
│      │                                                                       │
│►✓    │  [🔄 Re-run Validation]  [⬇️ Export to Excel]  [📧 Email Report]     │
│Validate│                                                                      │
│      │  Validation Breakdown                                                 │
│ 🔄   │  ┌─────────────────────────────────────────────────────────────────┐│
│Replicate│  │ Validation Type │ Passed │ Warnings │ Failed │ Pass Rate    ││
│      │  ├─────────────────────────────────────────────────────────────────┤│
│ 📊   │  │ Region          │   245  │     0    │    0   │   100%   ✓   ││
│Reports│  │ Resource Group  │   240  │     5    │    0   │    98%   ✓   ││
│      │  │ VNet/Subnet     │   230  │    10    │    5   │    94%   ⚠   ││
│ ⚙    │  │ VM SKU          │   245  │     0    │    0   │   100%   ✓   ││
│Settings│  │ Disk Type       │   243  │     2    │    0   │    99%   ✓   ││
│      │  │ Discovery       │   235  │     5    │    5   │    96%   ✓   ││
│      │  │ RBAC/Permissions│   220  │    15    │   10   │    90%   ⚠   ││
│      │  └─────────────────────────────────────────────────────────────────┘│
│      │                                                                       │
│      │  Failed Servers (10)                                                  │
│      │  ┌─────────────────────────────────────────────────────────────────┐│
│      │  │ Server Name     │ Failure Reason              │ Actions        ││
│      │  ├─────────────────────────────────────────────────────────────────┤│
│      │  │ APP-SERVER-01   │ VNet not found              │ [View][Fix]   ││
│      │  │ APP-SERVER-05   │ Insufficient RBAC permissions│ [View][Fix]   ││
│      │  │ DB-SERVER-10    │ Subnet IP exhausted         │ [View][Fix]   ││
│      │  │ ...                                                             ││
│      │  └─────────────────────────────────────────────────────────────────┘│
│      │                                                                       │
└──────┴───────────────────────────────────────────────────────────────────────┘
```

**Features**:
- Summary cards with metrics
- Re-run validation button
- Export to Excel/CSV
- Email report functionality
- Validation breakdown by type
- Pass rate percentages
- Failed servers detail table
- Quick fix suggestions
- View detailed results per server

---

### 8. Individual Server Validation Detail Modal

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Validation Details: WEB-SERVER-01                                      [✕]   │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Server Configuration                                                         │
│  ─────────────────────────────────────────────────────────────────────       │
│  Target Name:       WEB-SERVER-01                                            │
│  Region:           East US                                                   │
│  Resource Group:   rg-web-prod                                              │
│  VNet:             vnet-web-01                                              │
│  Subnet:           subnet-web-frontend                                       │
│  VM SKU:           Standard_D4s_v3                                          │
│  Disk Type:        Premium_SSD                                              │
│                                                                              │
│  Validation Results                                                          │
│  ─────────────────────────────────────────────────────────────────────       │
│                                                                              │
│  ✓ Region Validation                                                         │
│    Status: OK                                                                │
│    Message: Region 'East US' is available and supports migration            │
│                                                                              │
│  ✓ Resource Group Validation                                                │
│    Status: OK                                                                │
│    Message: Resource group 'rg-web-prod' exists and is accessible          │
│                                                                              │
│  ⚠ VNet/Subnet Validation                                                   │
│    Status: WARNING                                                           │
│    Message: Subnet has limited IP addresses available (15 of 256)           │
│    Suggestion: Consider using a larger subnet or creating a new one         │
│                                                                              │
│  ✓ VM SKU Validation                                                        │
│    Status: OK                                                                │
│    Message: SKU 'Standard_D4s_v3' is available in East US                  │
│                                                                              │
│  ✓ Disk Type Validation                                                     │
│    Status: OK                                                                │
│    Message: Premium SSD supported in target region                          │
│                                                                              │
│  ✓ Discovery Validation                                                     │
│    Status: OK                                                                │
│    Message: Server discovered in Azure Migrate project                      │
│    Discovered: Oct 28, 2025                                                 │
│    Last Heartbeat: Oct 30, 2025 10:30 AM                                    │
│                                                                              │
│  ⚠ Replication Status                                                       │
│    Status: WARNING                                                           │
│    Message: ⚠️ Machine 'WEB-SERVER-01' already has replication enabled     │
│    State: Protected                                                          │
│    Suggestion: Replication is already configured. If you need to            │
│               reconfigure, disable replication first before re-enabling.     │
│                                                                              │
│  ✓ RBAC Validation                                                          │
│    Status: OK                                                                │
│    Message: User has required permissions on target resources               │
│                                                                              │
│  Validation History                                                          │
│  ─────────────────────────────────────────────────────────────────────       │
│  Oct 30, 10:45 AM - All validations passed (1 warning)                      │
│  Oct 29, 03:00 PM - All validations passed                                  │
│  Oct 28, 11:00 AM - Initial validation                                      │
│                                                                              │
│  [Re-validate Server]  [Edit Configuration]                    [Close]      │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Features**:
- Complete server configuration display
- Each validation type shown separately
- Clear status indicators (✓ OK, ⚠ Warning, ✗ Failed)
- Detailed messages and suggestions
- Replication status warning (our new feature!)
- Validation history timeline
- Action buttons (re-validate, edit, close)

---

### 9. Replication Status Page

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ EMEA Migration 2025 > Replication Status                                     │
├──────┬───────────────────────────────────────────────────────────────────────┤
│      │                                                                       │
│ 🏠   │  Replication Monitoring                    Last refresh: Just now     │
│ Home │  ═══════════════════════════════════════════════════════════════     │
│      │                                                                       │
│ 🔧   │  Summary                                                              │
│ LZ   │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐       │
│ Setup│  │ Replicating│ │  Protected │ │   Syncing  │ │   Failed   │       │
│      │  │    180     │ │    165     │ │     12     │ │     3      │       │
│►🖥️   │  │   73%      │ │   92% ✓    │ │    7% 🔄   │ │    2% ✗    │       │
│Servers│  └────────────┘ └────────────┘ └────────────┘ └────────────┘       │
│      │                                                                       │
│ ✓    │  [🔄 Refresh Status]  [Enable Replication]  [⬇️ Export Report]       │
│Validate│                                                                      │
│      │  Filter: [All ▼] [Health ▼] [State ▼]      🔍 Search: [__________]   │
│►🔄   │                                                                       │
│Replicate│  ┌─────────────────────────────────────────────────────────────────┐│
│      │  │ Server         │State      │Health │Last Sync   │RPO  │Actions ││
│ 📊   │  ├─────────────────────────────────────────────────────────────────┤│
│Reports│  │WEB-SERVER-01   │Protected  │Normal │2 min ago   │5min │[👁][⏸]││
│      │  │WEB-SERVER-02   │Protected  │Normal │3 min ago   │5min │[👁][⏸]││
│ ⚙    │  │DB-SERVER-01    │Syncing    │Normal │Syncing...  │-    │[👁][⏸]││
│Settings│  │APP-SERVER-01   │Failed     │Critical│1 hour ago │-    │[👁][▶]││
│      │  │FILE-SERVER-01  │Protecting │Warning │10 min ago  │15min│[👁][⏸]││
│      │  │CACHE-SERVER-01 │Protected  │Normal │1 min ago   │5min │[👁][⏸]││
│      │  │API-SERVER-01   │Protected  │Normal │4 min ago   │5min │[👁][⏸]││
│      │  │  ... (showing 1-7 of 180)                                      ││
│      │  └─────────────────────────────────────────────────────────────────┘│
│      │                                                                       │
│      │  Legend: ✓ Normal  ⚠ Warning  ✗ Critical  🔄 Syncing  ⏸ Pause  ▶ Resume│
│      │                                                                       │
│      │  Pagination: ◄ 1 2 3 ... 18 ►                      Show: [10 ▼]     │
│      │                                                                       │
└──────┴───────────────────────────────────────────────────────────────────────┘
```

**Features**:
- Replication summary cards
- Refresh status button
- Enable replication for new servers
- Filter by state and health
- Search functionality
- Replication state indicators
- Health status (Normal, Warning, Critical)
- Last sync time
- RPO (Recovery Point Objective)
- Actions (view details, pause, resume)
- Legend for status icons

---

### 10. Validation Job Progress Modal

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Validation in Progress                                                 [✕]   │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Validating 245 servers...                                                   │
│                                                                              │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 67%            │
│                                                                              │
│  Current Status:                                                             │
│  ───────────────────────────────────────────────────────────────────         │
│                                                                              │
│  ✓ Region validation completed (245/245)                                    │
│  ✓ Resource Group validation completed (245/245)                            │
│  🔄 VNet/Subnet validation in progress (164/245)                            │
│  ⏳ VM SKU validation pending                                               │
│  ⏳ Disk Type validation pending                                            │
│  ⏳ Discovery validation pending                                            │
│  ⏳ RBAC validation pending                                                 │
│                                                                              │
│  Estimated time remaining: 2 minutes                                         │
│                                                                              │
│  Details:                                                                    │
│  • Validating WEB-SERVER-47 subnet configuration...                         │
│                                                                              │
│  [Cancel Validation]                                  [Run in Background]    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Features**:
- Overall progress bar with percentage
- Step-by-step status (✓ Done, 🔄 In Progress, ⏳ Pending)
- Item counts (164/245)
- Estimated time remaining
- Real-time current activity
- Cancel option
- Run in background option

---

## User Flows

### Flow 1: New User Onboarding

```
1. User Registration
   ↓
2. Email Verification (optional)
   ↓
3. First Login
   ↓
4. Welcome Screen / Quick Tour
   ↓
5. Create First Project
   ↓
6. Guided Setup:
   a. Configure Landing Zone
   b. Upload Server Excel
   c. Run First Validation
   ↓
7. View Results Dashboard
```

**Screens**: Login → Projects Dashboard → Create Project Modal → LZ Setup → Excel Upload → Validation Progress → Results

---

### Flow 2: Daily Usage - Validate New Batch of Servers

```
1. Login
   ↓
2. Select Existing Project
   ↓
3. Navigate to Servers Tab
   ↓
4. Upload New Excel File (50 servers)
   ↓
5. Review Upload Summary
   ↓
6. Click "Validate Servers"
   ↓
7. Monitor Progress (background job)
   ↓
8. Receive Notification (validation complete)
   ↓
9. Review Results
   ↓
10. Fix Failed Servers (if any)
   ↓
11. Re-validate Fixed Servers
   ↓
12. Export Report for Management
```

**Screens**: Login → Projects Dashboard → Project Detail → Servers → Upload Modal → Validation Progress → Results → Server Detail Modal → Export

---

### Flow 3: Landing Zone Setup for New Project

```
1. Create New Project
   ↓
2. Enter Project Details (name, subscription)
   ↓
3. Navigate to Landing Zone Setup
   ↓
4. Fill LZ Configuration:
   - Azure Migrate Project
   - Recovery Vault
   - Cache Storage
   - Appliance
   ↓
5. Save Configuration
   ↓
6. Click "Validate Landing Zone"
   ↓
7. View Validation Results:
   - Access: ✓
   - Appliance: ✓
   - Storage: ⚠ (will auto-create)
   - Quota: ✓
   ↓
8. Address Warnings (if any)
   ↓
9. Proceed to Server Upload
```

**Screens**: Projects → Create Modal → LZ Setup Form → Validation Results

---

### Flow 4: Monitor Replication Status

```
1. Login
   ↓
2. Select Active Project
   ↓
3. Navigate to Replication Tab
   ↓
4. View Replication Dashboard:
   - 180 servers replicating
   - 165 protected
   - 3 failed
   ↓
5. Click on Failed Server
   ↓
6. View Replication Details:
   - Error: Network connectivity issue
   - Last successful sync: 1 hour ago
   ↓
7. Click "Resume Replication"
   ↓
8. Monitor Recovery Progress
   ↓
9. Click "Refresh Status"
   ↓
10. Verify Server Now Protected
```

**Screens**: Login → Projects → Project Detail → Replication → Server Replication Detail Modal

---

### Flow 5: Bulk Server Configuration Edit

```
1. Navigate to Servers Tab
   ↓
2. Use Filters to find servers needing update
   (e.g., all servers in "East US")
   ↓
3. Select Multiple Servers (checkbox)
   ↓
4. Click "Bulk Edit"
   ↓
5. Change Target Region to "West US"
   ↓
6. Save Changes
   ↓
7. System prompts: "Re-validate affected servers?"
   ↓
8. Click "Yes, Validate Now"
   ↓
9. Monitor Validation Progress
   ↓
10. Review Updated Results
```

**Screens**: Servers → Filter/Select → Bulk Edit Modal → Validation Progress → Results

---

## Business Scenarios

### Scenario 1: Large Enterprise Migration (500+ Servers)

**Context**: Enterprise customer migrating 500 servers from on-premises to Azure across 3 regions.

**User Story**: As a Migration Architect, I need to validate all 500 servers efficiently and track validation status over time as configurations change.

**Workflow**:
1. Create project: "Enterprise Migration 2025"
2. Configure Landing Zone for primary region (East US)
3. Upload Excel with 500 servers
4. System validates in background (15 minutes)
5. Review results:
   - 450 passed ✓
   - 30 warnings ⚠ (subnet IP limitations)
   - 20 failed ✗ (invalid SKUs, missing VNets)
6. Export failed servers to Excel
7. Fix issues offline (correct SKUs, create VNets)
8. Re-upload corrected configurations
9. Re-validate only failed servers
10. All servers now pass
11. Enable replication for validated servers
12. Monitor replication status daily

**Key Features Used**:
- Bulk Excel upload
- Background validation for large datasets
- Filter by status (failed, warnings)
- Export to Excel
- Selective re-validation
- Replication monitoring
- Historical validation tracking

---

### Scenario 2: Multi-Region Migration

**Context**: Customer migrating to 3 Azure regions (East US, West Europe, Southeast Asia).

**User Story**: As a Cloud Engineer, I need to validate servers for different regions separately and track per-region progress.

**Workflow**:
1. Create project: "Multi-Region Migration"
2. Upload master Excel with all servers (300 total)
   - 120 servers → East US
   - 100 servers → West Europe
   - 80 servers → Southeast Asia
3. Filter servers by region "East US"
4. Validate East US servers
5. Review results and fix issues
6. Repeat for West Europe
7. Repeat for Southeast Asia
8. Use dashboard to see overall progress by region
9. Export region-specific reports

**Key Features Used**:
- Single project, multiple regions
- Filter by region
- Selective validation
- Region-based reporting
- Progress tracking per region

---

### Scenario 3: Phased Migration with Approval Gates

**Context**: Customer doing phased migration with management approval between phases.

**User Story**: As a Project Manager, I need to validate servers in batches, get approval, then move to next phase.

**Workflow**:
Phase 1 (Week 1):
1. Create project: "Phased Migration"
2. Upload Phase 1 servers (50 servers)
3. Validate all
4. Export validation report
5. Get management approval
6. Enable replication for Phase 1

Phase 2 (Week 3):
7. Upload Phase 2 servers (50 servers)
8. Validate new servers
9. Monitor Phase 1 replication status
10. Export combined report (Phase 1 + 2)
11. Get approval
12. Enable replication for Phase 2

Phase 3 (Week 5):
13. Upload Phase 3 servers (50 servers)
14. Validate
15. Monitor all 150 servers replication
16. Final report and cutover

**Key Features Used**:
- Incremental server addition
- Historical validation results
- Combined reporting across phases
- Replication status monitoring
- Export capabilities for approval process

---

### Scenario 4: Discovering Replication Conflicts

**Context**: Customer has some servers already replicating and wants to validate before adding more.

**User Story**: As a Migration Engineer, I need to know which servers are already replicating before I attempt to configure them.

**Workflow**:
1. Create new project for datacenter
2. Upload all servers from datacenter (200 servers)
3. Run validation
4. System detects 15 servers already have replication enabled
5. Validation results show warnings:
   - ⚠️ "Machine 'WEB-SERVER-01' already has replication enabled (State: Protected)"
   - Suggested action: "Disable replication first before re-enabling"
6. Filter to show only servers with replication warnings
7. Review list of already-replicating servers
8. Decide to:
   - Keep existing replication for 10 servers (don't reconfigure)
   - Disable and reconfigure 5 servers (different target)
9. Update configurations for 5 servers
10. Re-validate
11. Proceed with replication for remaining 185 servers

**Key Features Used**:
- **Replication status check** (NEW FEATURE!)
- Warning system
- Filter by validation type
- Selective server management
- Suggested actions

---

### Scenario 5: Troubleshooting Failed Validations

**Context**: Customer has multiple validation failures and needs to understand root causes.

**User Story**: As a Technical Support Engineer, I need detailed validation results to troubleshoot issues.

**Workflow**:
1. Customer reports 20 servers failed validation
2. Navigate to Validation Results page
3. See breakdown:
   - VNet/Subnet failures: 12 servers
   - RBAC failures: 5 servers
   - Discovery failures: 3 servers
4. Click on VNet failures
5. See detailed error: "Subnet 'subnet-web' not found in VNet 'vnet-prod'"
6. Check Azure Portal - subnet exists but different name
7. Bulk edit affected servers to correct subnet name
8. Re-validate
9. Click on RBAC failures
10. See error: "User lacks 'Contributor' role on resource group 'rg-prod'"
11. Grant required permissions in Azure
12. Re-validate
13. All servers now pass
14. Export final validation report

**Key Features Used**:
- Validation breakdown by type
- Detailed error messages
- Suggested actions
- Bulk edit
- Selective re-validation
- Export capabilities

---

### Scenario 6: Weekly Status Reporting

**Context**: Project manager needs weekly status reports for stakeholders.

**User Story**: As a Project Manager, I need to generate weekly reports showing migration progress.

**Workflow**:
Weekly Process:
1. Login to project
2. Navigate to Reports/Dashboard
3. Review summary metrics:
   - Total servers: 500
   - Validated: 500 (100%)
   - Replicating: 350 (70%)
   - Protected: 320 (64%)
   - Failed: 5 (1%)
4. Click "Export Weekly Report"
5. System generates Excel with:
   - Executive summary
   - Validation status by server
   - Replication status
   - Failed servers detail
   - Week-over-week progress
6. Download report
7. Email to stakeholders

**Key Features Used**:
- Dashboard with metrics
- Historical tracking
- Export to Excel
- Summary and detail views
- Progress tracking

---

## Feature Coverage Matrix

| Feature | Screen(s) | User Flow | Business Scenario |
|---------|-----------|-----------|-------------------|
| **User Authentication** | Login, Registration | 1 | All |
| **Project Management** | Projects Dashboard, Create Modal | 1, 2, 3 | All |
| **Landing Zone Config** | LZ Setup | 3 | 1, 2 |
| **Excel Upload** | Upload Modal, Servers | 2, 5 | 1, 2, 3 |
| **Manual Server Add** | Servers, Add Form | - | - |
| **Bulk Server Edit** | Servers, Bulk Edit | 5 | 2, 5 |
| **Server Validation** | Validation Progress, Results | 2, 3, 5 | All |
| **Validation Breakdown** | Results Page | 2 | 5, 6 |
| **Individual Server Detail** | Server Detail Modal | 4 | 5 |
| **Replication Status** | Replication Page | 4 | 1, 3, 4, 6 |
| **Replication Warning** | Server Detail Modal | 2 | 4 |
| **Background Jobs** | Progress Modal | 2, 3 | 1 |
| **Search & Filter** | Servers, Replication | 5 | 2, 4, 5 |
| **Export Reports** | Results, Replication | 2, 6 | 3, 6 |
| **Historical Results** | Results Page | - | 3, 6 |
| **Dashboard Metrics** | Project Detail | - | 6 |

---

## Questions for Review

Please review the mockups and scenarios above and confirm:

### Design Questions:
1. **Project Structure**: Does the project-centric navigation make sense for your use case?
2. **Excel Upload**: Is the upload flow intuitive? Do you need template customization?
3. **Validation Display**: Are the validation results detailed enough? Too detailed?
4. **Replication Monitoring**: Does the replication page show the right metrics?

### Functional Questions:
5. **Missing Features**: Are there any critical features not covered in the mockups?
6. **User Roles**: Do you need different user roles (Admin, Viewer, Operator)?
7. **Notifications**: Should users receive email/SMS notifications for validation completion?
8. **API Access**: Do you need REST API access for external tools?

### Workflow Questions:
9. **Approval Workflow**: Do you need built-in approval gates between phases?
10. **Audit Log**: Do you need to track who made what changes and when?
11. **Multi-tenant**: Will multiple teams/organizations use the same instance?
12. **Data Retention**: How long should validation history be kept?

---

## Next Steps

Based on your feedback, I can:
1. Adjust mockups and add missing features
2. Create more detailed wireframes for specific screens
3. Begin implementation of Phase 1 (Database)
4. Create interactive prototypes (Figma/Adobe XD)
5. Develop user stories and acceptance criteria

**Please provide feedback on:**
- ✅ What looks good and should stay as-is
- 🔄 What needs adjustment
- ➕ What's missing
- ❌ What should be removed/simplified
