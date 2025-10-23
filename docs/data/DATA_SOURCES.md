# Parliamentary Data Sources

**Last Updated**: 2025-10-23
**Purpose**: Document all data sources, URL patterns, and extraction methods

---

## 📊 **DATA WE HAVE (In Database)**

### **Current Database Contents:**
- **Members**: 1,701 MPs (1993-2025)
- **Senators**: 99 current senators
- **Roles**: 19,930 role records
- **Votes**: 118,494 individual MP votes
- **Bills**: 7,061 bills (House + Senate)
- **Bill Progress**: Tracking for all bills

### **Data Quality:**
- ✅ 100% vote dates
- ✅ Comprehensive 32-year coverage
- ⚠️ Missing: Bill summaries (available, not yet scraped)
- ⚠️ Missing: Motion text from Journals (available, not yet scraped)
- ⚠️ Missing: Petitions (available, not yet scraped)

---

## 🔗 **DATA SOURCE PATTERNS**

All URL patterns are in: `db_setup/url_templates.py`

### **1. Bills - Full Text & Summaries**

**URL Pattern:**
```
https://www.parl.ca/Content/Bills/{parl}{sess}/{chamber}/C-{num}/C-{num}_1/C-{num}_E.xml
```

**Examples:**
- Government bill: `/Bills/451/Government/C-5/C-5_1/C-5_E.xml`
- Private bill: `/Bills/451/Private/C-214/C-214_1/C-214_E.xml`
- Senate bill: `/Bills/451/Senate/S-15/S-15_1/S-15_E.xml` (pattern TBD)

**How to Determine Chamber:**
- `C-1` to `C-200`: Government bills
- `C-200+`: Private Member bills
- `S-xxx`: Senate bills

**What's Available:**
- ✅ Bill summary (clear description of what it does)
- ✅ Long title
- ✅ Short title
- ✅ Sponsor name
- ✅ Bill history (stages + dates)
- ✅ Preamble ("Whereas..." context)
- ✅ Full legislative text

**Status:** ⚠️ **Need scraper** - not yet collected

---

### **2. Journal PDFs - Motion Text & Context**

**URL Pattern:**
```
https://www.ourcommons.ca/Content/House/{parl}{sess}/Journals/{sitting:03d}/Journal{sitting:03d}.PDF
```

**Example:**
- Parliament 45-1, Sitting 26: `/House/451/Journals/026/Journal026.PDF`

**Viewer URL (alternative):**
```
https://www.ourcommons.ca/documentviewer/en/{parl}-{sess}/house/sitting-{sitting}/journals
```

**What's Available:**
- ✅ Motion text (what was actually voted on)
- ✅ Who proposed the motion
- ✅ Budget line items with dollar amounts
- ✅ Vote numbers (to link to our votes table)
- ✅ Daily routine of business
- ✅ Petitions presented

**Status:** ⚠️ **Need scraper** - critical for Opposition Motion analysis

---

### **3. Vote Details**

**URL Pattern:**
```
https://www.ourcommons.ca/members/en/votes/{parl}/{sess}/{vote_num}
```

**Party View:**
```
https://www.ourcommons.ca/members/en/votes/{parl}/{sess}/{vote_num}?view=party
```

**What's Available:**
- ✅ Vote result (Agreed To / Negatived)
- ✅ Vote counts by party
- ✅ Individual MP votes
- ✅ Vote topic/subject

**Status:** ✅ **Already scraped** (in votes table)

---

### **4. Petitions**

**URL Pattern:**
```
https://www.ourcommons.ca/petitions/en/Petition/Search?Category=All&order=Recent&output=xml
```

**With Parliament Filter:**
```
https://www.ourcommons.ca/petitions/en/Petition/Search?parl=44&Category=All&order=Recent&output=xml
```

**What's Available:**
- ✅ Petition topic
- ✅ Sponsor (which MP)
- ✅ Signatures count
- ✅ Status (open, certified, government response, etc.)
- ✅ Date presented

**Status:** ⚠️ **Need scraper** (low priority)

---

## 📋 **SCRAPER STATUS**

### **✅ DONE:**
1. **Members Scraper** - All MPs + senators
2. **Roles Scraper** - Party affiliations, committees, offices
3. **Votes Scraper** - Individual MP votes
4. **Bills Basic Scraper** - Bill numbers, titles, sponsors
5. **Bill Progress Scraper** - Legislative stages

### **⚠️ NEEDED:**
1. **Bill XML Scraper** (HIGH PRIORITY)
   - Extract summaries for better topic analysis
   - Location: `scripts/extraction/bills/fetch_bill_xml.py`
   - Effort: 1-2 days

2. **Journal PDF Scraper** (HIGH PRIORITY)
   - Extract motion text for Opposition Motions
   - Location: `scripts/extraction/journals/fetch_journals.py`
   - Effort: 2-3 days (PDF parsing is complex)

3. **Petition Scraper** (LOW PRIORITY)
   - Extract petition data
   - Location: `scripts/extraction/petitions/fetch_petitions.py`
   - Effort: 1 day

---

## 🎯 **DATA EXTRACTION PRIORITIES**

### **Phase 0: Complete Data Pipeline** (Before building frontend)

**Week 1:**
1. Build Bill XML scraper
2. Run on recent bills (Parliament 42-45)
3. Add `summary` column to bills table
4. Verify extraction quality

**Week 2:**
1. Build Journal PDF scraper
2. Extract motion text for top 100 interesting votes
3. Store in new `vote_motions` table
4. Link to votes by vote_number + date

**Week 3:**
1. Data validation & quality checks
2. Fix any extraction issues
3. Document what we actually have
4. THEN start building API/frontend

---

## 🗄️ **DATABASE ADDITIONS NEEDED**

### **1. Bills Table - Add Summary Column:**
```sql
ALTER TABLE bills ADD COLUMN summary TEXT;
ALTER TABLE bills ADD COLUMN preamble TEXT;
ALTER TABLE bills ADD COLUMN xml_fetched_date DATE;
```

### **2. New Table - Vote Motions:**
```sql
CREATE TABLE vote_motions (
    motion_id INTEGER PRIMARY KEY,
    vote_date DATE,
    vote_number INTEGER,
    parliament_number INTEGER,
    session_number INTEGER,
    sitting_number INTEGER,
    motion_text TEXT,
    proposer_name TEXT,
    proposer_party TEXT,
    journal_pdf_url TEXT,
    extracted_date DATE
);
```

### **3. New Table - Petitions (later):**
```sql
CREATE TABLE petitions (
    petition_id INTEGER PRIMARY KEY,
    petition_number VARCHAR,
    title TEXT,
    topic_category VARCHAR,
    sponsor_mp_id INTEGER,
    signatures_count INTEGER,
    status VARCHAR,
    date_presented DATE,
    response_tabled_date DATE,
    parliament_number INTEGER
);
```

---

## 🔍 **DATA CLASSIFICATION**

### **Vote Types** (for filtering):
Based on `vote_topic` field:

- **Budget votes**: Contains "estimate", "concurrence", "opposed", "supplementary"
- **Policy votes**: Contains "bill", "reading", "motion"
- **Opposition motions**: Contains "opposition motion"
- **Procedural**: Everything else

**Implementation:**
```python
def classify_vote_type(vote_topic):
    topic_lower = vote_topic.lower()

    if any(kw in topic_lower for kw in ['estimate', 'concurrence', 'opposed item', 'supplementary']):
        return 'budget'
    elif 'opposition motion' in topic_lower:
        return 'opposition_motion'
    elif any(kw in topic_lower for kw in ['bill c-', 'bill s-', 'reading']):
        return 'bill_vote'
    else:
        return 'procedural'
```

### **Bill Types** (for categorization):
Based on long title patterns:

- **"Act to amend..."** → Law improvements
- **"Act for granting..."** → Budget bills
- **"Act to establish..."** → New frameworks
- **"Act respecting..."** → New policies

---

## 📝 **EXTRACTION GUIDELINES**

### **Bill XML Scraper:**
1. Start with recent parliaments (42-45) ≈ 1,500 bills
2. Rate limit: 1 request per second
3. Handle 404s gracefully (old bills might not have XMLs)
4. Cache fetched XMLs (don't re-fetch)
5. Store summary in database
6. Log failures for manual review

### **Journal PDF Scraper:**
1. Start with known interesting sitting days
2. Download PDF to temp storage
3. Extract motion text using pdfplumber or PyPDF2
4. Match motion numbers to votes by date + parliament
5. Store motion text separately
6. Clean up temp PDFs after extraction

### **Petition Scraper:**
1. Fetch XML for each parliament
2. Parse XML structure
3. Store in database with parliament context
4. Can re-run periodically for new petitions

---

## 🛠️ **UTILITY FUNCTIONS NEEDED**

### **URL Builders:**
```python
from db_setup.url_templates import URL_TEMPLATES

def build_bill_xml_url(bill_number, parliament, session):
    """Build URL for bill XML"""
    chamber = infer_chamber(bill_number)
    bill_prefix, bill_num = bill_number.split('-')

    return URL_TEMPLATES['bill_text_xml'].format(
        parliament=parliament,
        session=session,
        chamber=chamber,
        bill_type=bill_prefix,
        bill_number=bill_num
    )

def build_journal_pdf_url(parliament, session, sitting):
    """Build URL for journal PDF"""
    return URL_TEMPLATES['journal_pdf'].format(
        parliament=parliament,
        session=session,
        sitting=sitting
    )

def infer_chamber(bill_number):
    """Infer if bill is Government or Private"""
    match = re.search(r'C-(\d+)', bill_number)
    if match:
        num = int(match.group(1))
        return "Government" if num < 200 else "Private"
    return "Senate"  # S-bills
```

---

## ✅ **DATA VALIDATION CHECKLIST**

Before building frontend, verify:

- [ ] Bills have summaries (at least for recent parliaments)
- [ ] Opposition motions have motion text
- [ ] Vote types are properly classified
- [ ] No major gaps in data coverage
- [ ] All URL patterns work
- [ ] Extraction scripts are reusable
- [ ] Database schema updated
- [ ] Documentation reflects reality

---

## 🔗 **REFERENCES**

- URL Templates: `db_setup/url_templates.py`
- Existing Scrapers: `scripts/extraction/`
- Database Schema: `db_setup/create_database.py`
- Final Roadmap: `docs/FINAL_ROADMAP.md`

---

**Bottom Line:** We have the data. We know where to get more. Now we need to build the scrapers to fetch it before building the frontend.
