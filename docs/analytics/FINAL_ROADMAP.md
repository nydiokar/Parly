# Parly Project - Final Actionable Roadmap

**Date**: 2025-10-23
**Role**: Data Analyst (not journalist)
**Goal**: Data visualization with stories as subproduct

---

## 🎯 **THE 5 COMPONENTS**

### **Priority Order:**
1. **General/Context** (Funny findings, easy to digest) - HIGHEST
2. **Budget Analysis** (if we can find systematic way) - HIGH
3. **Bills Visualization** - MEDIUM
4. **Vote Stories** (Opposition motions) - MEDIUM
5. **Petitions** - LOWEST

---

## 📊 **COMPONENT 1: GENERAL/CONTEXT (Funny & Interesting)**

### **What to Build:**

#### **A. Parliament Seating Visualization**
**Visualization**: Interactive seating chart colored by party
- Current parliament (45th)
- Dynamic (can switch between parliaments)
- Click seat → see MP details

**Data Needed**: ✅ We have (members + parties)
**Effort**: 1-2 days
**Tech**: D3.js or simple SVG

---

#### **B. Election Year Panic**
**Finding**: More bills introduced in election years
**Visualization**: Bar chart comparing election vs non-election years

**Data Needed**:
- ⚠️ Need to fix year calculations (parliament to actual years)
- ✅ Have bill counts

**Effort**: 1 day (after fixing year mapping)

---

#### **C. 4-Day Work Week Pattern**
**Finding**: 96% of votes happen Mon-Thu
**Visualization**: Simple bar chart by day of week

**Data Needed**: ✅ We have (verified)
**Effort**: 0.5 days
**Status**: READY TO BUILD

---

#### **D. Activity Heatmaps**
**Two versions:**
1. **Votes per month** (exclude budget votes for clarity)
2. **Bills introduced per month**

**Visualization**: Calendar heatmap (year × month)

**Data Needed**:
- ✅ Have dates
- ⚠️ Need to classify vote types (budget vs non-budget)

**Effort**: 1-2 days

---

#### **E. Party Switchers (Anne C. Cools)**
**Finding**: Who changed parties most over career
**Visualization**: Timeline showing party changes

**Data Needed**: ✅ We have (roles table with party + dates)
**Effort**: 1 day
**Status**: Query needs refinement

---

#### **F. Unlikely Friendships**
**Finding**: Cross-party voting patterns
**Visualization**: Network graph (MPs as nodes, voting similarity as edges)

**Data Needed**: ✅ We have
**Effort**: 2-3 days (compute similarity matrix)
**Complexity**: MEDIUM-HIGH

---

#### **G. Topic Shift Over Time**
**Finding**: Which topics get attention over years
**Visualization**: Stacked area chart or heatmap

**Data Needed**:
- ⚠️ Need topic extraction from bill titles
- ✅ Have bills with dates

**Effort**: 2-3 days (topic clustering)

---

## 💰 **COMPONENT 2: BUDGET ANALYSIS**

### **What to Build:**

#### **Budget Day Detector**
**Goal**: Automatically find budget voting days

**Algorithm**:
```python
def is_budget_day(date, vote_topics):
    # A day with 100+ votes on estimates/concurrence
    budget_keywords = ['estimate', 'concurrence', 'opposed', 'supplementary']
    budget_count = count_votes_with_keywords(vote_topics, budget_keywords)

    return budget_count > 100
```

**Output**: List of budget days: Dec 7 2023, June 17 2025, April 11 2024, etc.

---

#### **Budget Breakdown Extractor**
**Goal**: For each budget day, extract spending details

**Data Sources**:
1. **Votes table**: Who voted how
2. **Journal PDF**: Motion text with dollar amounts

**Process**:
1. Identify budget days automatically
2. Download corresponding Journal PDFs
3. Parse motion text + amounts
4. Structure as JSON

**Effort**: 3-4 days (PDF parsing is tricky)

---

#### **Budget Visualization**
**Shows**:
- Total approved per budget day
- Top 10 biggest allocations
- Funny items ($1 votes)
- Party voting patterns (who opposed what spending)
- Institutional spending breakdown

**Effort**: 2-3 days (after data extracted)

---

## 📜 **COMPONENT 3: BILLS VISUALIZATION**

### **What to Build:**

#### **Bill Title Analyzer**
**Goal**: Categorize bills by type and topic

**Categories (from long titles)**:
- "Act to amend..." → Law improvements
- "Act for granting to His Majesty..." → Budget bills
- "Act to establish..." → New frameworks
- "Act respecting..." → New topics/issues

**Extraction**:
```python
patterns = {
    'amend': r'Act to amend the (.+?) \(',
    'grant': r'granting to His Majesty',
    'establish': r'Act to establish (.+?)$',
    'respecting': r'Act respecting (.+?)$'
}
```

**Topics** (from brackets/short titles):
- Healthcare, Environment, Justice, Immigration, etc.

---

#### **Bill Progress Tracker**
**Goal**: Where do bills die?

**Visualization**: Sankey diagram
- Introduced → 1st Reading → 2nd Reading → Committee → 3rd Reading → Royal Assent
- Show dropout at each stage
- Color by topic

**Data Needed**: ✅ We have (bill_progress table)
**Effort**: 2-3 days

---

#### **Combined View**
**Dashboard showing**:
- Bill categories distribution (pie chart)
- Topics over time (line chart)
- Success rate by category (bar chart)
- Where bills die (Sankey)

**Effort**: 3-4 days total

---

## 🗳️ **COMPONENT 4: VOTE STORIES (Opposition Motions)**

### **What to Build:**

#### **A. Opposition Motion Identifier**
**Goal**: Filter votes to Opposition motions only

```python
def is_opposition_motion(vote_topic):
    return 'opposition motion' in vote_topic.lower()
```

**Data Enhancement Needed**:
- ❌ Currently missing: Who proposed it
- ❌ Currently missing: Full motion text

**Solution**: Extract from Journal PDFs

---

#### **B. Journal Scraper**
**Goal**: Download and parse Journal PDFs

**URL Pattern**:
```
https://www.ourcommons.ca/Content/House/{parl}{sess}/Journals/{sitting:03d}/Journal{sitting:03d}.PDF

Example:
Parliament 45, Session 1, Sitting 26:
https://www.ourcommons.ca/Content/House/451/Journals/026/Journal026.PDF
```

**Extract From PDF**:
1. Motion text (what they voted on)
2. Proposer (which MP/party)
3. Vote number (to link to our database)

**Effort**: 3-4 days (PDF parsing + matching to our votes)

---

#### **C. Opposition Motion Dashboard**
**Shows**:
- List of all Opposition motions (last 2-3 years)
- Filter by: Party, Topic, Result
- Click one → full story:
  - Motion text
  - Who proposed
  - How each party voted
  - Result (passed/failed)
  - Context/analysis

**Effort**: 2-3 days (after journal parsing)

---

#### **D. Opposition Party Analysis**
**Goal**: What does opposition prioritize?

**Shows**:
- Topics by party (Conservatives focus on crime, NDP on housing, etc.)
- Success rate by party
- Party strategy patterns

**Effort**: 1-2 days

---

## 📮 **COMPONENT 5: PETITIONS (Lowest Priority)**

### **What to Build:**

#### **Petition Scraper**
**Data Source**:
```
Current parliament:
https://www.ourcommons.ca/petitions/en/Petition/Search?Category=All&order=Recent&output=xml

Historical:
https://www.ourcommons.ca/petitions/en/Petition/Search?parl=44&type=&keyword=&sponsor=&status=&Text=&RPP=20&order=Recent&category=All&output=xml
```

**Extract**:
- Petition topic
- Sponsor (which MP)
- Signatures count
- Status (open, certified, government response, etc.)
- Date

---

#### **Petition Dashboard**
**Shows**:
- Most signed petitions (top 20)
- Topics people care about (word cloud or categories)
- Most active MPs (who presents most petitions)
- Success rate (how many get government response)

**Effort**: 2-3 days

---

## 🔗 **URL TEMPLATES TO ADD**

Update `config/url_templates.py`:

```python
# Journals
JOURNAL_PDF = "https://www.ourcommons.ca/Content/House/{parliament}{session}/Journals/{sitting:03d}/Journal{sitting:03d}.PDF"
JOURNAL_VIEWER = "https://www.ourcommons.ca/documentviewer/en/{parliament}-{session}/house/sitting-{sitting}/journals"

# Petitions
PETITIONS_XML = "https://www.ourcommons.ca/petitions/en/Petition/Search"
# Params: parl=X, Category=All, order=Recent, output=xml
```

---

## 📅 **PHASED IMPLEMENTATION PLAN**

### **Phase 1: Quick Wins (Week 1-2)** - HIGHEST PRIORITY
**Goal**: Ship something visible quickly

**Build**:
1. ✅ 4-Day Work Week (0.5 days)
2. ✅ Parliament Seating (1-2 days)
3. ✅ Activity Heatmap - Bills per month (1 day)
4. ✅ Party Switchers timeline (1 day)

**Total**: 3.5-5.5 days
**Output**: 4 visualizations live

---

### **Phase 2: Bill Analysis (Week 3-4)** - HIGH PRIORITY
**Goal**: Show what bills are about and where they die

**Build**:
1. Bill title categorization (1 day)
2. Topic extraction (1-2 days)
3. Bill progress Sankey diagram (1 day)
4. Bills dashboard (1-2 days)

**Total**: 4-6 days
**Output**: Bills visualization suite

---

### **Phase 3: Budget Analysis (Week 5-6)** - HIGH PRIORITY (if feasible)
**Goal**: Follow the money

**Build**:
1. Budget day detector (1 day)
2. Journal PDF scraper for budgets (2 days)
3. Budget breakdown parser (2 days)
4. Budget visualization (2 days)

**Total**: 7 days
**Output**: Budget tracker

---

### **Phase 4: Opposition Stories (Week 7-8)** - MEDIUM PRIORITY
**Goal**: Show what opposition wants

**Build**:
1. Journal scraper (general) (2 days)
2. Motion text extractor (2 days)
3. Opposition motion dashboard (2 days)
4. Party analysis (1 day)

**Total**: 7 days
**Output**: Opposition motion tracker

---

### **Phase 5: Advanced Context (Week 9-10)** - MEDIUM PRIORITY
**Goal**: Deeper patterns

**Build**:
1. Unlikely friendships (vote similarity) (2-3 days)
2. Topic shift over time (2 days)
3. Election year panic (1 day after year fix)

**Total**: 5-6 days
**Output**: Advanced analytics

---

### **Phase 6: Petitions (Week 11-12)** - LOWEST PRIORITY
**Goal**: What people care about

**Build**:
1. Petition scraper (1 day)
2. Petition dashboard (2 days)

**Total**: 3 days
**Output**: Petition tracker

---

## ⏱️ **REALISTIC TIMELINE SUMMARY**

```
Week 1-2:   Quick Wins (4 viz)
Week 3-4:   Bills Analysis
Week 5-6:   Budget Analysis
Week 7-8:   Opposition Stories
Week 9-10:  Advanced Context
Week 11-12: Petitions

Total: 12 weeks (3 months)
```

---

## 🎯 **IMMEDIATE NEXT STEPS (This Week)**

### **Day 1: Foundation**
1. ✅ Fix year calculation (parliament → actual years)
2. ✅ Add vote type classifier (budget vs policy)
3. ✅ Update url_templates.py

### **Day 2-3: First Visualization**
Build **4-Day Work Week** visualization:
- Backend: Simple API endpoint
- Frontend: Bar chart
- Deploy and test

### **Day 4-5: Second & Third Visualizations**
- Parliament seating chart
- Activity heatmap (bills per month)

### **Day 6-7: Fourth Visualization + Polish**
- Party switchers timeline
- Polish all 4 visualizations
- Create landing page
- LAUNCH Phase 1

---

## 🚫 **IMPORTANT: SCOPE MANAGEMENT**

### **Exclude from Initial Builds**:
- ❌ Bill-related votes (keep only Opposition motions for vote stories)
- ❌ Hansard speeches (too complex, defer to later)
- ❌ Media context (manual research, not scalable)
- ❌ Historical votes before 2020 (focus on recent)

### **Keep Simple**:
- ✅ Use structured data we have
- ✅ Add context only where easy to extract
- ✅ Manual work is OK for budget (5-10 days worth)
- ✅ Focus on visualization quality over quantity

---

## 📊 **TECHNICAL DECISIONS**

### **Frontend**:
- Next.js 14
- Recharts + D3.js
- Tailwind CSS
- Vercel deployment

### **Backend**:
- FastAPI (existing)
- New routes:
  - `/api/context/...` (funny findings)
  - `/api/bills/...` (bill analysis)
  - `/api/budget/...` (budget breakdown)
  - `/api/opposition/...` (opposition motions)
  - `/api/petitions/...` (petitions)

### **Data Processing**:
- Python scripts in `scripts/analysis/`
- PDF parsing: PyPDF2 or pdfplumber
- Store extracted context in JSON files initially
- Later: migrate to database if needed

---

## 🎯 **SUCCESS METRICS**

### **Phase 1 Success**:
- ✅ 4 visualizations live
- ✅ Clean, professional design
- ✅ Mobile responsive
- ✅ Share-worthy content

### **Overall Success**:
- Data-driven insights (not opinion)
- High-quality visualizations
- Interesting patterns revealed
- Scalable infrastructure for expansion

---

## 💬 **THE PITCH (After Phase 1)**

> "I analyzed 32 years of Canadian parliamentary data."
>
> "118,000 votes. 7,000 bills. 1,700 MPs."
>
> "Found patterns nobody talks about:"
> - Parliament works 4 days a week
> - Bills die at predictable stages
> - Opposition proposes, government blocks
> - Money flows follow party lines
>
> "All visualized. All data-driven. No opinions, just facts."

---

## 📂 **FILES TO UPDATE**

1. ✅ `config/url_templates.py` - Add journal and petition URLs
2. ⚠️ `scripts/analysis/fix_year_mapping.py` - Parliament to year converter
3. ⚠️ `scripts/analysis/classify_vote_types.py` - Budget vs policy classifier
4. ⚠️ `api/routes/context.py` - New endpoints for funny findings
5. ⚠️ `frontend/` - New Next.js project

---

## 🚀 **LET'S START**

**Today**: Build the 4-Day Work Week visualization end-to-end

**This proves**:
- ✅ Pipeline works (DB → API → Frontend)
- ✅ Visualization looks good
- ✅ Can ship something

**Then**: Build 3 more, launch Phase 1 in 1 week

---

**Ready to start? Which visualization should we build FIRST?**

My vote: **4-Day Work Week** (simplest, already verified, 0.5 days)
