# .ai Folder - AI Agent Context

Universal AI agent contract for the Parly project.

---

## What is This?

The `.ai/` folder provides **persistent session context** for AI agents working on the Parly project. It enables smooth handoffs between sessions and maintains continuity across multiple work sessions.

---

## How .ai/ Relates to PROGRESS_LOG.md

### PROGRESS_LOG.md (Project Artifact)
- **Purpose**: Historical record of work completed
- **Scope**: Captures major milestones, changes, and project evolution
- **Audience**: Team members, future developers, project stakeholders
- **Update Frequency**: After significant feature completion or milestone
- **Persistence**: Permanent project documentation

### .ai/CONTEXT.md (Session State)
- **Purpose**: Current work-in-progress state for AI agents
- **Scope**: Active tasks, immediate next steps, current blockers
- **Audience**: AI agents across sessions
- **Update Frequency**: After each task completion, end of each session
- **Persistence**: Updated continuously during development

**Analogy**:
- `PROGRESS_LOG.md` is like a project **changelog** or **release notes**
- `.ai/CONTEXT.md` is like a developer's **working notes** or **scratch pad**

---

## Folder Structure

```
.ai/
├── README.md      # This file - explains the system
├── CONTEXT.md     # MUTABLE - AI updates this continuously
├── GUIDE.md       # REFERENCE - Task list and project guide
├── RULES.md       # IMMUTABLE - Execution contract (rarely changes)
└── HANDOFF.md     # PROTOCOL - Session transfer procedures
```

---

## Usage for AI Agents

### Starting a New Session
```
Read .ai/ folder for context, then continue from the next incomplete task in CONTEXT.md.
```

### During Work
1. Check `CONTEXT.md` for current state
2. Reference `GUIDE.md` for task priorities and documentation
3. Follow `RULES.md` for execution guidelines
4. Update `CONTEXT.md` after each task completion

### Ending a Session
1. Update `CONTEXT.md` with progress
2. Mark completed tasks
3. Note any blockers or decisions
4. Update timestamp and agent name
5. (Optional) Update `PROGRESS_LOG.md` if major milestone reached

---

## Workflow Example

**Session 1**:
- AI reads `.ai/CONTEXT.md` → sees "Phase 1.2: Data audit" is next
- AI completes data source inventory
- AI updates `.ai/CONTEXT.md` → marks task complete
- Session ends

**Session 2** (different AI or same AI, new context):
- AI reads `.ai/CONTEXT.md` → sees "Data source inventory" complete
- AI sees next task: "Data quality verification"
- AI continues from where Session 1 left off
- No context loss!

**Milestone Reached**:
- After completing entire Phase 1.2
- AI updates both `.ai/CONTEXT.md` (current state)
- Developer updates `PROGRESS_LOG.md` (historical record)

---

## Benefits

✅ **Session Continuity**: No context loss between sessions
✅ **Task Tracking**: Clear view of completed vs. pending work
✅ **Standardized**: Works with any LLM (Claude, GPT-4, Cursor, etc.)
✅ **Lightweight**: ~10KB total, easy to maintain
✅ **Self-Documenting**: AI keeps context updated automatically

---

## Integration with Parly Documentation

Parly has extensive documentation in `docs/`:
- **ROADMAP.md** - Strategic 4-phase vision
- **IMPLEMENTATION_GUIDE.md** - Detailed implementation steps
- **ARCHITECTURE.md**, **DATABASE_SCHEMA.md**, etc.

The `.ai/GUIDE.md` **references** these docs rather than duplicating them.

**Hierarchy**:
1. `.ai/CONTEXT.md` - What's happening NOW
2. `.ai/GUIDE.md` - What to build NEXT (references full docs)
3. `docs/*` - HOW to build it (detailed specs and patterns)
4. `PROGRESS_LOG.md` - What was built BEFORE

---

## Maintenance

### AI Agents Should:
- ✅ Update `CONTEXT.md` frequently (after each task)
- ✅ Read `GUIDE.md` for task priorities
- ✅ Follow `RULES.md` execution contract
- ❌ NEVER modify `RULES.md` or `GUIDE.md` without human approval

### Humans Should:
- Update `GUIDE.md` as project priorities change
- Review `CONTEXT.md` periodically to ensure accuracy
- Update `PROGRESS_LOG.md` after major milestones
- Modify `RULES.md` only when execution contract changes (rare)

---

**This system was adapted from the time-lab project's `.ai-template/` and customized for Parly's specific needs.**
