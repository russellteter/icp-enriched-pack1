# Google Sheets Master Ledger Setup

## Prerequisites
1. Google Cloud Project with Sheets API enabled
2. Service Account with appropriate permissions
3. Google Sheets document shared with the service account

## Setup Steps

### 1. Create Google Cloud Service Account
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select or create a project
3. Navigate to "IAM & Admin" > "Service Accounts"
4. Click "Create Service Account"
5. Name it (e.g., "icp-discovery-ledger")
6. Grant role: "Editor" or "Sheets API User"
7. Create and download JSON key

### 2. Enable Google Sheets API
1. In Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for "Google Sheets API"
3. Click and enable it

### 3. Configure Service Account JSON
1. Copy the downloaded JSON key to project root as `service_account.json`
2. Or update `.env` with the correct path:
   ```
   GOOGLE_SERVICE_ACCOUNT_JSON=/path/to/your/service_account.json
   ```

### 4. Share Google Sheet with Service Account
1. Open your Google Sheet (ID: 1GvGZJreKvTYNlOlH9pEgX4-2L9RdB0q4V-FuhRxkWU8)
2. Click "Share" button
3. Add the service account email (found in JSON as `client_email`)
4. Grant "Editor" permissions
5. Click "Send"

### 5. Verify Setup
Run the following test:
```python
from src.tools.sheets import SheetsLedger
ledger = SheetsLedger()
orgs = ledger.load_orgs("healthcare")
print(f"Connected! Found {len(orgs)} existing organizations")
```

## Sheet Structure
The Master Ledger will automatically create sheets with these columns:
- Organization
- Segment
- Region
- Status
- Score
- FirstAdded
- LastValidated
- EvidenceURL1
- Notes

Each ICP segment gets its own sheet:
- `ledger_healthcare`
- `ledger_corporate`
- `ledger_providers`

## Troubleshooting
- **"File not found"**: Ensure service_account.json exists in project root
- **"Permission denied"**: Share the Google Sheet with service account email
- **"API not enabled"**: Enable Google Sheets API in Cloud Console
- **"Invalid grant"**: Service account may need domain-wide delegation for workspace accounts