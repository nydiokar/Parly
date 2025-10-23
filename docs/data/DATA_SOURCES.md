# Data Sources Documentation

## Overview

This document provides comprehensive information about all data sources used in the Parly system, including URLs, data formats, field mappings, and extraction strategies.

---

## Base URLs and Endpoints

### Parliamentary Website (ourcommons.ca)

**Base URL:** `https://www.ourcommons.ca`

This is the primary source for member information, roles, votes, and interventions.

### Legislative Information Website (parl.ca)

**Base URL:** `https://www.parl.ca`

This is the primary source for bill information and legislative progress tracking.

---

## Data Source Catalog

### 1. Member List

**Purpose:** Obtain a complete list of all current Members of Parliament with their unique IDs.

**URL:** `https://www.ourcommons.ca/members/en/search?view=list`

**Format:** HTML

**HTTP Method:** GET

**Headers Required:**
```python
{
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}
```

**Extraction Strategy:**
1. Parse HTML using BeautifulSoup
2. Find all `<a>` tags with `href` attributes
3. Filter for links matching pattern: `/Members/en/{name}-{id}`
4. Extract member name and ID using regex: `/Members/en/(.*)-(\d+)`

**Data Fields:**
- `name`: Member's full name (extracted from URL, convert hyphens to spaces, Title Case)
- `id`: Unique member identifier (integer)
- `profile_url`: Full URL to member's profile page
- `search_pattern`: Format `{name-with-hyphens}({id})` (e.g., "ziad-aboultaif(89156)")

**Output Format:** CSV
**Output File:** `data/member_ids.csv`

**Sample Output:**
```csv
name,id,search_pattern
Ziad Aboultaif,89156,ziad-aboultaif(89156)
Scott Aitchison,105340,scott-aitchison(105340)
```

**Rate Limiting:** Single request, no rate limiting needed

**Script:** `scripts/extraction/member_id_scraper.py`

---

### 2. Member Roles

**Purpose:** Extract detailed role information for each member (MP status, committees, political affiliations, etc.).

**URL Template:** `https://www.ourcommons.ca/Members/en/{search_pattern}/roles`

**Example:** `https://www.ourcommons.ca/Members/en/ziad-aboultaif(89156)/roles`

**Format:** HTML

**HTTP Method:** GET

**Extraction Strategy:**
1. For each member in `member_ids.csv`, construct the roles URL
2. Parse HTML using BeautifulSoup
3. Extract data from multiple table sections identified by `<h2>` headers

**Data Sections to Extract:**

#### Section A: Member of Parliament
**HTML Identifier:** `<h2>` with text "Member of Parliament"

**Table Structure:**
| Constituency | Province/Territory | Start Date | End Date |
|--------------|-------------------|------------|----------|

**Field Mappings:**
- `role_type`: "Member of Parliament"
- `constituency`: Table cell 0
- `province`: Table cell 1
- `start_date`: Table cell 2
- `end_date`: Table cell 3 (may be empty)

#### Section B: Political Affiliation
**HTML Identifier:** `<h2>` with text "Political Affiliation"

**Table Structure:**
| Parliament | Affiliation | Start Date | End Date |
|------------|-------------|------------|----------|

**Field Mappings:**
- `role_type`: "Political Affiliation"
- `parliament_number`: Table cell 0
- `affiliation`: Table cell 1
- `start_date`: Table cell 2
- `end_date`: Table cell 3 (may be empty)

#### Section C: Committees
**HTML Identifier:** `<h2>` with text "Committees"

**Table Structure:**
| Parliament-Session | Role | Committee | Start Date | End Date |
|--------------------|------|-----------|------------|----------|

**Field Mappings:**
- `role_type`: "Committee Member"
- `parliament_session`: Table cell 0
- `role_name`: Table cell 1
- `committee_name`: Table cell 2
- `start_date`: Table cell 3
- `end_date`: Table cell 4 (may be empty)

#### Section D: Parliamentary Associations and Interparliamentary Groups
**HTML Identifier:** `<h2>` with text "Parliamentary Associations and Interparliamentary Groups"

**Table Structure:**
| Parliament | Role | Organization | Start Date | End Date |
|------------|------|--------------|------------|----------|

**Field Mappings:**
- `role_type`: "Parliamentary Association"
- `parliament_number`: Table cell 0
- `role_name`: Table cell 1
- `organization_name`: Table cell 2
- `start_date`: Table cell 3
- `end_date`: Table cell 4 (may be empty)

#### Section E: Election Candidate
**HTML Identifier:** `<h2>` with text "Election Candidate"

**Table Structure:**
| Date | Type | Constituency | Province | Result |
|------|------|--------------|----------|--------|

**Field Mappings:**
- `role_type`: "Election Candidate"
- `date`: Table cell 0
- `election_type`: Table cell 1
- `constituency`: Table cell 2
- `province`: Table cell 3
- `result`: Table cell 4

#### Section F: Offices and Roles as a Parliamentarian
**HTML Identifier:** `<h2>` with text "Offices and Roles as a Parliamentarian"

**Table Structure:**
| Parliament | Office/Role | Start Date | End Date |
|------------|-------------|------------|----------|

**Field Mappings:**
- `role_type`: "Parliamentarian Office"
- `parliament_number`: Table cell 0
- `office_role`: Table cell 1
- `start_date`: Table cell 2
- `end_date`: Table cell 3 (may be empty)

**Output Format:** JSON
**Output File:** `data/member_roles.json`

**Sample Output Structure:**
```json
[
  {
    "member_id": "89156",
    "search_pattern": "ziad-aboultaif(89156)",
    "roles": [
      {
        "role_type": "Member of Parliament",
        "constituency": "Edmonton Manning",
        "province": "Alberta",
        "start_date": "Monday, September 20, 2021",
        "end_date": ""
      },
      {
        "role_type": "Committee Member",
        "parliament_session": "44-1",
        "role_name": "Member",
        "committee_name": "Foreign Affairs and International Development",
        "start_date": "Wednesday, September 20, 2023",
        "end_date": ""
      }
    ]
  }
]
```

**Date Format:** "Day, Month DD, YYYY" (e.g., "Monday, September 20, 2021")

**Rate Limiting:** 1 second delay between requests (time.sleep(1))

**Script:** `scripts/extraction/scrape_roles.py`

---

### 3. Member Votes

**Purpose:** Extract voting records for each member.

**URL Template:** `https://www.ourcommons.ca/Members/en/{search_pattern}/votes/xml`

**Example:** `https://www.ourcommons.ca/Members/en/ziad-aboultaif(89156)/votes/xml`

**Format:** XML

**HTTP Method:** GET

**XML Structure:**
```xml
<VoteParticipants>
  <MemberVote>
    <ParliamentNumber>44</ParliamentNumber>
    <SessionNumber>1</SessionNumber>
    <DecisionEventDateTime>2022-03-15T19:30:00</DecisionEventDateTime>
    <DecisionDivisionNumber>123</DecisionDivisionNumber>
    <DecisionDivisionSubject>Bill C-10, An Act to amend...</DecisionDivisionSubject>
    <DecisionResultName>Agreed To</DecisionResultName>
    <DecisionDivisionNumberOfYeas>180</DecisionDivisionNumberOfYeas>
    <DecisionDivisionNumberOfNays>145</DecisionDivisionNumberOfNays>
    <DecisionDivisionNumberOfPaired>5</DecisionDivisionNumberOfPaired>
    <VoteValueName>Yea</VoteValueName>
    <IsVoteYea>true</IsVoteYea>
    <IsVoteNay>false</IsVoteNay>
    <IsVotePaired>false</IsVotePaired>
  </MemberVote>
  ...
</VoteParticipants>
```

**Field Mappings to Database:**
- `ParliamentNumber` → `parliament_number` (Integer)
- `SessionNumber` → `session_number` (Integer)
- `DecisionEventDateTime` → `vote_date` (Date, extract date part only)
- `DecisionDivisionSubject` → `vote_topic` (String, first 255 chars) and `subject` (Text, full)
- `DecisionResultName` → `vote_result` (String)
- `VoteValueName` → `member_vote` (String)

**Output:** Insert directly into database `votes` table

**Rate Limiting:** 2 second delay between requests with exponential backoff on failures

**Script:** `scripts/extraction/fetch_votes.py` (needs completion)

---

### 4. Bills Sponsored by Member

**Purpose:** Extract bills sponsored by each member.

**URL Template:** `https://www.parl.ca/legisinfo/en/bills/xml?parlsession=all&sponsor={member_id}&advancedview=true`

**Example:** `https://www.parl.ca/legisinfo/en/bills/xml?parlsession=all&sponsor=89156&advancedview=true`

**Format:** XML

**HTTP Method:** GET

**XML Structure:**
```xml
<Bills>
  <Bill>
    <BillId>11473439</BillId>
    <NumberCode>C-215</NumberCode>
    <ParliamentNumber>44</ParliamentNumber>
    <SessionNumber>1</SessionNumber>
    <StatusName>First Reading</StatusName>
    <OriginatingChamberName>House of Commons</OriginatingChamberName>
    <SponsorPersonId>89156</SponsorPersonId>
    ...
  </Bill>
</Bills>
```

**Field Mappings to Database:**
- `NumberCode` → `bill_number` (String)
- `ParliamentNumber` → `parliament_number` (Integer)
- `SessionNumber` → `session_number` (Integer)
- `StatusName` → `status` (String)
- `SponsorPersonId` → `sponsor_id` (Integer, FK to members)
- `OriginatingChamberName` → `chamber` (String)

**Output:** Insert directly into database `bills` table

**Rate Limiting:** 2 second delay between requests

**Script:** To be created: `scripts/extraction/fetch_bills.py`

---

### 5. Bill Progress Details

**Purpose:** Extract the legislative progress stages for each bill.

**URL Template:** `https://www.parl.ca/LegisInfo/en/bill/{parliament}-{session}/{bill_type}-{bill_number}/json?view=progress`

**Example:** `https://www.parl.ca/LegisInfo/en/bill/44-1/C-215/json?view=progress`

**Format:** JSON

**HTTP Method:** GET

**JSON Structure:**
```json
{
  "BillStages": {
    "HouseBillStages": [
      {
        "BillStageName": "First reading",
        "State": 4,
        "StateName": "Completed",
        "StateAsOfDate": "2021-11-23T14:20:19.547"
      },
      {
        "BillStageName": "Second reading",
        "State": 1,
        "StateName": "Not reached"
      }
    ]
  }
}
```

**Field Mappings to Database:**
- `BillStageName` → `status` (String)
- `StateAsOfDate` → `progress_date` (Date)
- Bill ID → `bill_id` (FK to bills)

**Extraction Logic:**
- Only extract stages where `State` = 4 (Completed)
- Parse both `HouseBillStages` and `SenateBillStages`

**Output:** Insert directly into database `bill_progress` table

**Rate Limiting:** 1 second delay between requests

**Script:** To be created: `scripts/extraction/fetch_bill_progress.py`

---

### 6. Chamber Interventions (Hansard)

**Purpose:** Extract debate transcripts and speeches by members.

**URL Template:** `https://www.ourcommons.ca/publicationsearch/en/?per={member_id}&pubType=37&xml=1`

**Example:** `https://www.ourcommons.ca/publicationsearch/en/?per=89156&pubType=37&xml=1`

**Format:** XML

**HTTP Method:** GET

**XML Structure:** (Very large files, contains full debate transcripts)

**Note:** This data source is for future implementation in the Analysis Layer. For Phase 1, this is **NOT REQUIRED**.

**Field Mappings:** To be determined in future phases

**Script:** To be created in future: `scripts/extraction/fetch_interventions.py`

---

### 7. Committee Interventions

**Purpose:** Extract committee meeting transcripts and member participation.

**URL Template:** `https://www.ourcommons.ca/publicationsearch/en/?per={member_id}&pubType=40017&xml=1`

**Example:** `https://www.ourcommons.ca/publicationsearch/en/?per=89156&pubType=40017&xml=1`

**Format:** XML

**HTTP Method:** GET

**Note:** This data source is for future implementation in the Analysis Layer. For Phase 1, this is **NOT REQUIRED**.

**Script:** To be created in future: `scripts/extraction/fetch_committee_interventions.py`

---

## Data Extraction Best Practices

### 1. Politeness Policy
- Always include a `User-Agent` header
- Implement delays between requests (minimum 1 second)
- Use exponential backoff on failures
- Respect robots.txt (if applicable)

### 2. Error Handling
- Implement retry logic (3 attempts with exponential backoff)
- Log all failed requests with member ID and URL
- Continue processing on individual failures (don't stop entire batch)
- Save progress periodically to allow resuming

### 3. Data Validation
- Validate XML/HTML structure before parsing
- Check for required fields before database insertion
- Log warnings for missing or malformed data
- Implement data type conversions with error handling

### 4. Incremental Updates
- Track last successful extraction date
- Support filtering by date range where available
- Allow re-scraping specific members or date ranges
- Implement upsert logic to handle updates vs. new records

---

## Date Format Conversions

### Input Formats Encountered:
1. **HTML Format:** "Monday, September 20, 2021"
2. **XML DateTime:** "2021-11-23T14:20:19.547"
3. **JSON Date:** "2021-11-23T00:00:00"

### Target Format (Database):
- **Type:** DATE
- **Format:** YYYY-MM-DD (ISO 8601)

### Parsing Function (Python):
```python
from datetime import datetime

def parse_date(date_string: str) -> date | None:
    """Parse various date formats to database format."""
    if not date_string:
        return None
    
    formats = [
        '%A, %B %d, %Y',           # Monday, September 20, 2021
        '%Y-%m-%dT%H:%M:%S.%f',    # 2021-11-23T14:20:19.547
        '%Y-%m-%dT%H:%M:%S',       # 2021-11-23T00:00:00
        '%Y-%m-%d',                # 2021-11-23
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt).date()
        except ValueError:
            continue
    
    return None
```

---

## Data Refresh Strategy

### Initial Load (Full Scrape):
1. Scrape all members (1 request)
2. Scrape roles for all members (338 requests, ~6 minutes with delays)
3. Scrape votes for all members (338 requests, ~11 minutes with delays)
4. Scrape bills for all members (338 requests, ~11 minutes with delays)

**Total Time:** ~30 minutes

### Incremental Updates (Recommended Schedule):
- **Members:** Monthly (list changes infrequently)
- **Roles:** Weekly (new committee assignments, party changes)
- **Votes:** Daily (during parliamentary sessions)
- **Bills:** Weekly (bill progress updates)

---

## Example Data Files

The `data/raw/` directory contains example files for each data source:

- `data/raw/members/membership/membership.xml` - Member profile XML
- `data/raw/members/roles/roles.xml` - Member roles XML
- `data/raw/members/votes/votes_example.xml` - Voting records XML
- `data/raw/members/sponsored_bills/bills_sponsored.xml` - Sponsored bills XML
- `data/raw/bills/all_bill_example.json` - Bill details JSON
- `data/raw/bills/progress/bills_progress.json` - Bill progress JSON
- `data/raw/members/interventions/hansard.xml` - Hansard interventions XML
- `data/raw/members/interventions/committee_interventions.xml` - Committee interventions XML

These files serve as reference for the expected data structures and can be used for testing parsing logic.

---

## Summary Table

| Data Type | Source | Format | Script Status | Priority |
|-----------|--------|--------|---------------|----------|
| Member List | ourcommons.ca | HTML | ✅ Complete | High |
| Member Roles | ourcommons.ca | HTML | ✅ Complete | High |
| Member Votes | ourcommons.ca | XML | ⚠️ Partial | High |
| Bills | parl.ca | XML | ❌ Not Started | High |
| Bill Progress | parl.ca | JSON | ❌ Not Started | High |
| Hansard | ourcommons.ca | XML | ❌ Not Started | Low (Future) |
| Committee Interventions | ourcommons.ca | XML | ❌ Not Started | Low (Future) |

**Legend:**
- ✅ Complete: Script exists and is functional
- ⚠️ Partial: Script exists but needs completion/fixes
- ❌ Not Started: Script needs to be created

