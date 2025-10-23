# 🌍 External Correlations - Parliament vs. The Real World

**⚠️ DATA VERIFICATION NEEDED - These findings need thorough validation before going viral! ⚠️**

Generated: 2025-10-22 from initial data mining
Status: **PRELIMINARY - VERIFY BEFORE PUBLISHING**

---

## 🔥 **THE SMOKING GUNS (PENDING VERIFICATION)**

### 1. **THE SUMMER VACATION SCANDAL** ☀️

**The Finding:**
- **July: 0 votes**
- **August: 0 votes**
- June: 27.8% of annual votes (cramming before vacation)
- December: 17.1% (end-of-year rush)

**Why It's Viral:**
- Everyone can relate to summer vacation
- MPs make $194,000/year
- "Must be nice to take 2 months off"
- Explains why nothing gets done

**VERIFY:**
- ✅ Is this consistent across all years?
- ✅ Do they genuinely do ZERO work or is it committee work not in our data?
- ✅ Is July/August officially "recess" or are they supposed to work?
- ✅ Check against official parliamentary calendar

**Visualization Ideas:**
- Calendar heatmap showing vote density by month
- "Your job vs. Their job" comparison
- Title: **"Parliament Takes 2 Months Off Every Summer (On Your Dime)"**

---

### 2. **THE 4-DAY WORK WEEK (FOR MPs ONLY)** 📅

**The Finding:**
- Monday-Thursday: 96% of all votes
- Friday: 4.0% of votes
- Saturday: 0.0%
- Sunday: 0.0%
- Wednesday is peak (31.4%)

**Why It's Viral:**
- Friday = basically a long weekend
- Most Canadians work 5 days
- MPs have privileged schedule
- Relatable frustration

**VERIFY:**
- ✅ Is Friday officially a sitting day?
- ✅ Do they do constituency work on Fridays?
- ✅ Is this pattern consistent across all years?
- ✅ Compare to House of Commons schedule

**Visualization Ideas:**
- Bar chart: Mon-Thu vs. Fri-Sun
- Weekly calendar with activity heatmap
- Title: **"MPs Work 4 Days. You Work 5. They Make $194,000."**

---

### 3. **OLYMPIC DISTRACTION** 🏅

**The Finding:**
- **23% LESS work during Olympic years**
- Average work Olympic years: 206.5
- Average work other years: 266.6
- Pattern holds across multiple Olympics

**Why It's Viral:**
- Proves they're distracted
- Olympics = national pride vs. governance
- Quantifiable neglect
- Relatable: "I watch Olympics at work too, but I get fired"

**VERIFY:**
- ✅ Are Olympic years also election years? (confounding variable)
- ✅ Check if pattern is statistically significant
- ✅ Look at individual Olympic years separately
- ✅ Control for parliament session length

**Visualization Ideas:**
- Side-by-side: Olympic medals vs. bills passed
- Line graph showing productivity dip
- Title: **"What Parliament Cares About During Olympics (Hint: Not You)"**

---

### 4. **CRISIS = PARALYSIS** 😱

**The Finding:**
- **23% FEWER bills during economic crises**
- Average crisis years: 480 bills
- Average normal years: 625 bills
- Pattern: 2008 financial crisis, 2020 COVID

**Why It's Viral:**
- When you need them most, they do least
- Counter-intuitive (shouldn't crises = more action?)
- Recent (COVID) = very relatable
- Shows system failure

**VERIFY:**
- ✅ Are crisis years also minority governments? (different dynamics)
- ✅ Check if "fewer bills" but "more important bills"?
- ✅ Look at bill passage rate, not just introduction
- ✅ Compare to other countries during same crises

**Visualization Ideas:**
- Line graph with crisis markers
- "When you need them" vs. "What they do"
- Title: **"Why Parliament Does 23% Less When You Need Them Most"**

---

### 5. **SCANDAL PATTERNS: HIDE OR FLOOD** 🎭

**The Finding:**
- 2011 Robocall Scandal: **+59% MORE bills** (distraction/deflection?)
- 2019 SNC-Lavalin: 0 bills (total freeze)
- 2020 WE Charity: -36% (hiding)
- Pattern inconsistent: sometimes flood, sometimes freeze

**Why It's Viral:**
- Reveals political calculation
- "Are they distracting us?"
- Pattern recognition = conspiracy catnip
- Proves they're reactive, not proactive

**VERIFY:**
- ✅ Check exact timing (scandal month vs. bill introduction)
- ✅ Correlation ≠ causation (could be coincidence)
- ✅ Look at bill topics during scandal years (relevant or random?)
- ✅ Compare to scandal-free years in same parliament

**Visualization Ideas:**
- Scatter plot: Scandal severity vs. bill count
- Timeline showing scandal and bill spikes
- Title: **"How To Spot A Cover-Up: Parliament's Bill Pattern During Scandals"**

---

### 6. **PM HONEYMOON IS A MYTH** 💔

**The Finding:**
- **EVERY new PM's first year: ~0 bills or major drop**
- Chrétien 1993: -21% vs. later years
- Martin 2003: -100% (data issue?)
- Harper 2006: -100% (data issue?)
- Trudeau 2015: -100% (data issue?)

**Why It's Viral:**
- "First 100 days" rhetoric is lies
- They take a year to figure things out
- Campaigned on change, delivered nothing
- Election promises = empty

**VERIFY:**
- ⚠️ THIS LOOKS LIKE A DATA ISSUE!
- ✅ Check parliament start dates vs. PM appointment dates
- ✅ Many 0 bills = likely data mapping error (year estimation is rough)
- ✅ Need actual dates, not estimated years
- ✅ **PROBABLY WRONG - FIX THE YEAR CALCULATION FIRST**

**Status:** 🚨 **LIKELY DATA ERROR - DON'T USE UNTIL FIXED** 🚨

---

### 7. **ELECTION YEAR PANIC (FROM EARLIER)**

**The Finding:**
- **84% MORE bills in election years**
- Election years: 1,024 bills average
- Regular years: 557 bills average

**Why It's Viral:**
- (Already covered in WILD_DISCOVERIES.md)
- Most reliable finding so far
- Clear pattern, makes sense

**VERIFY:**
- ✅ This one looks solid
- ✅ Recheck with exact dates
- ✅ Control for parliament session length

---

## 📊 **DATA QUALITY ISSUES TO FIX**

### **Critical Issues:**

1. **Year Estimation is Rough**
   - Current method: `year = 1993 + (parliament_number - 35) * 3`
   - Problem: Parliaments don't last exactly 3 years
   - Fix: Use actual `from_date` and `to_date` from roles/bills
   - Impact: Affects PM honeymoon, crisis timing, scandal timing

2. **Missing Vote Dates**
   - Some votes have no `vote_date`
   - Can't analyze day-of-week or month patterns accurately
   - Fix: Check data source, might need to scrape dates

3. **Bill Progress "Stages" Confusion**
   - Heartbreak bills showing 16 stages but dying at "First Reading"?
   - Might be counting all progress events, not distinct stages
   - Fix: Clarify what "stage" means

4. **December 7, 2023 Anomaly**
   - 11,356 votes in one day is suspicious
   - Likely bundled votes or data error
   - Fix: Investigate that specific date

### **Validation Checklist for Tomorrow:**

- [ ] Fix year calculation (use actual dates, not estimates)
- [ ] Verify summer break pattern across multiple years
- [ ] Check official parliamentary calendar for sitting days
- [ ] Investigate December 7, 2023 vote count
- [ ] Validate Olympic year correlation with proper controls
- [ ] Cross-reference scandal dates with bill introduction dates
- [ ] Check if Friday is officially a sitting day
- [ ] Verify crisis year bill counts manually for 2-3 examples

---

## 🎯 **MOST PROMISING FOR VIRAL CONTENT**

Ranked by: Data reliability × Viral potential × Relatability

### **Tier 1: Probably Solid** ✅
1. **Election Year Panic** (84% more bills)
   - Pattern is clear and consistent
   - Verify with exact dates
   - HIGH CONFIDENCE

2. **4-Day Work Week** (Friday = 4% of votes)
   - Easy to verify against official schedule
   - Very relatable
   - MEDIUM-HIGH CONFIDENCE

3. **Summer Vacation** (July/August = 0 votes)
   - Likely accurate (matches known recess)
   - Need to check if it's official
   - MEDIUM-HIGH CONFIDENCE

### **Tier 2: Needs Verification** ⚠️
4. **Olympic Distraction** (23% less work)
   - Interesting but needs controls
   - Could be confounding variables
   - MEDIUM CONFIDENCE

5. **Crisis Paralysis** (23% fewer bills)
   - Intriguing but needs more data
   - Check for minority government correlation
   - MEDIUM CONFIDENCE

### **Tier 3: Probably Wrong** 🚨
6. **PM Honeymoon** (all -100%)
   - Looks like data error
   - Year calculation is broken
   - LOW CONFIDENCE - DON'T USE

7. **Scandal Deflection** (inconsistent pattern)
   - Correlation might be coincidence
   - Needs more rigorous analysis
   - LOW CONFIDENCE

---

## 🛠️ **TECHNICAL FIXES NEEDED**

### **Priority 1: Fix Year Calculation**

Replace this:
```python
year = 1993 + (bill.parliament_number - 35) * 3
```

With actual date-based calculation:
```python
# Use role dates or bill introduction dates
# Map parliament numbers to actual year ranges
PARLIAMENT_YEARS = {
    35: (1994, 1997),
    36: (1997, 2000),
    # ... etc
}
```

### **Priority 2: Validate Vote Dates**

```python
# Check for missing dates
votes_with_dates = session.query(Vote).filter(Vote.vote_date.isnot(None)).count()
total_votes = session.query(Vote).count()
print(f"Votes with dates: {votes_with_dates}/{total_votes}")
```

### **Priority 3: Cross-Reference External Events**

Create proper timeline mappings with EXACT dates:
```python
SCANDALS = {
    datetime(2019, 2, 7): "SNC-Lavalin story breaks",
    datetime(2019, 3, 29): "Jody Wilson-Raybould testifies",
    # ... exact dates
}
```

---

## 💡 **TOMORROW'S ACTION PLAN**

1. **Morning: Data Audit**
   - Run validation queries
   - Fix year calculation
   - Document data quality issues

2. **Afternoon: Re-run Analysis**
   - Use corrected data
   - Verify findings
   - Identify which discoveries hold up

3. **Evening: Pick Winner**
   - Choose most solid finding
   - Start building visualization
   - Prepare for launch

---

## 🎨 **IF DATA CHECKS OUT: BUILD THESE FIRST**

1. **"The Summer Vacation Nobody Talks About"**
   - Easiest to verify
   - Most relatable
   - Calendar heatmap visual

2. **"The 4-Day Work Week (For MPs Only)"**
   - Simple to validate
   - Very shareable
   - Bar chart visual

3. **"Election Year Panic Button"**
   - Already partially validated
   - Always relevant
   - Animated bar chart

---

## ⚠️ **FINAL WARNING**

**DO NOT GO VIRAL WITH UNVERIFIED DATA!**

The findings are exciting, but:
- Some are likely data errors
- Some need more rigorous analysis
- Some might be coincidences
- Some require domain expertise to interpret

**Tomorrow: Validate, then build. Not the other way around.** ✅

---

**These correlations COULD be explosive... if they're real. Let's make sure they are.** 🔥
