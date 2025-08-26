import os
import json
import gspread
from google.oauth2.service_account import Credentials
from typing import List, Dict, Set
from datetime import datetime
import time


class SheetsLedger:
    """Google Sheets Master Ledger for deduplication and tracking"""
    
    def __init__(self):
        self.spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
        self.service_account_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        self.client = None
        self.spreadsheet = None
        # Local fallback ledger directory
        self._fallback_dir = os.path.join(".cache", "ledger")
        try:
            os.makedirs(self._fallback_dir, exist_ok=True)
        except Exception:
            pass
        self._connect()
    
    def _connect(self):
        """Connect to Google Sheets using service account"""
        try:
            # Define the required scopes
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Load credentials from service account JSON
            if self.service_account_path and os.path.exists(self.service_account_path):
                creds = Credentials.from_service_account_file(
                    self.service_account_path,
                    scopes=scopes
                )
                self.client = gspread.authorize(creds)
                
                # Open the spreadsheet
                if self.spreadsheet_id:
                    self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            else:
                # Fallback to stub mode if credentials not available
                print("Warning: Google Sheets credentials not configured, using stub mode")
                self.client = None
                self.spreadsheet = None
        except Exception as e:
            print(f"Warning: Failed to connect to Google Sheets: {e}")
            self.client = None
            self.spreadsheet = None
    
    def load_orgs(self, segment: str) -> Set[str]:
        """Load existing organization names for a segment to prevent duplicates"""
        orgs = set()
        
        if not self.spreadsheet:
            # Local fallback
            try:
                path = os.path.join(self._fallback_dir, f"ledger_{segment}.json")
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        data = json.load(f)
                        for row in data or []:
                            org_name = (row.get('Organization', '') or '').strip().lower()
                            if org_name:
                                orgs.add(org_name)
            except Exception as e:
                print(f"Warning: Failed to load local ledger for {segment}: {e}")
            return orgs
        
        try:
            # Get or create the sheet for this segment
            sheet_name = f"ledger_{segment}"
            try:
                sheet = self.spreadsheet.worksheet(sheet_name)
            except gspread.exceptions.WorksheetNotFound:
                # Create sheet if it doesn't exist
                sheet = self._create_ledger_sheet(sheet_name)
            
            # Get all records
            records = sheet.get_all_records()
            
            # Extract organization names (normalized to lowercase for comparison)
            for record in records:
                org_name = record.get('Organization', '').strip().lower()
                if org_name:
                    orgs.add(org_name)
            
            print(f"Loaded {len(orgs)} existing organizations for segment '{segment}'")
            
        except Exception as e:
            print(f"Error loading organizations from ledger: {e}")
        
        return orgs
    
    def _create_ledger_sheet(self, sheet_name: str):
        """Create a new ledger sheet with proper headers"""
        # Headers as per PRD Appendix B
        headers = [
            "Organization", "Segment", "Region", "Status", "Score", 
            "FirstAdded", "LastValidated", "EvidenceURL1", "Notes"
        ]
        
        # Create new worksheet
        sheet = self.spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=len(headers))
        
        # Set headers
        sheet.update('A1:I1', [headers])
        
        # Format headers (bold)
        sheet.format('A1:I1', {'textFormat': {'bold': True}})
        
        return sheet
    
    def upsert(self, rows: List[Dict]) -> Dict:
        """Insert or update rows in the master ledger"""
        if not rows:
            return {"upserted": 0, "status": "no_data"}
        if not self.spreadsheet:
            # Local fallback write
            try:
                segment = rows[0].get('segment', 'unknown')
                path = os.path.join(self._fallback_dir, f"ledger_{segment}.json")
                existing: list = []
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        existing = json.load(f) or []
                # Build index by org lower
                index = { (r.get('Organization','') or '').strip().lower(): i for i, r in enumerate(existing) }
                upserted = 0
                for row in rows:
                    org_name_l = (row.get('organization','') or '').strip().lower()
                    ledger_entry = {
                        "Organization": row.get('organization', ''),
                        "Segment": row.get('segment', 'unknown'),
                        "Region": row.get('region', ''),
                        "Status": row.get('tier', 'Needs Confirmation'),
                        "Score": str(row.get('score', 0)),
                        "FirstAdded": datetime.now().isoformat(),
                        "LastValidated": datetime.now().isoformat(),
                        "EvidenceURL1": row.get('evidence_url', ''),
                        "Notes": row.get('notes', '')
                    }
                    if org_name_l in index:
                        # Update existing record
                        prev = existing[index[org_name_l]]
                        ledger_entry["FirstAdded"] = prev.get("FirstAdded", ledger_entry["FirstAdded"])
                        existing[index[org_name_l]] = ledger_entry
                    else:
                        existing.append(ledger_entry)
                        index[org_name_l] = len(existing) - 1
                    upserted += 1
                with open(path, 'w') as f:
                    json.dump(existing, f)
                return {"upserted": upserted, "status": "success_local"}
            except Exception as e:
                print(f"Warning: Failed to write local ledger: {e}")
                return {"upserted": 0, "status": "failure_local"}
        
        upserted_count = 0
        
        try:
            for row in rows:
                segment = row.get('segment', 'unknown')
                sheet_name = f"ledger_{segment}"
                
                try:
                    sheet = self.spreadsheet.worksheet(sheet_name)
                except gspread.exceptions.WorksheetNotFound:
                    sheet = self._create_ledger_sheet(sheet_name)
                
                # Prepare ledger entry
                ledger_entry = {
                    "Organization": row.get('organization', ''),
                    "Segment": segment,
                    "Region": row.get('region', ''),
                    "Status": row.get('tier', 'Needs Confirmation'),
                    "Score": str(row.get('score', 0)),
                    "FirstAdded": datetime.now().isoformat(),
                    "LastValidated": datetime.now().isoformat(),
                    "EvidenceURL1": row.get('evidence_url', ''),
                    "Notes": row.get('notes', '')
                }
                
                # Check if organization already exists
                org_name = ledger_entry["Organization"].strip().lower()
                existing_records = sheet.get_all_records()
                
                row_to_update = None
                for idx, record in enumerate(existing_records, start=2):  # Start at row 2 (after headers)
                    if record.get('Organization', '').strip().lower() == org_name:
                        row_to_update = idx
                        break
                
                if row_to_update:
                    # Update existing row
                    ledger_entry["FirstAdded"] = existing_records[row_to_update - 2].get('FirstAdded', ledger_entry["FirstAdded"])
                    values = list(ledger_entry.values())
                    sheet.update(f'A{row_to_update}:I{row_to_update}', [values])
                    print(f"Updated existing entry for {ledger_entry['Organization']}")
                else:
                    # Append new row
                    values = list(ledger_entry.values())
                    sheet.append_row(values)
                    print(f"Added new entry for {ledger_entry['Organization']}")
                
                upserted_count += 1
                
                # Rate limiting to avoid API quota issues
                time.sleep(0.5)
                
        except Exception as e:
            print(f"Error upserting to ledger: {e}")
        
        return {
            "upserted": upserted_count,
            "status": "success" if upserted_count > 0 else "partial_failure"
        }


