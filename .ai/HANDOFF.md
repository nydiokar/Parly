# Session Handoff Protocol

---

## Starting a Session

### First Time
```
Read .ai/ folder for context, then begin work as outlined in GUIDE.md.
```

### Continuing Work
```
Read .ai/CONTEXT.md for current state, then continue from the next incomplete task.
```

---

## Ending a Session

1. **Update CONTEXT.md**:
   - Mark completed tasks `[x]`
   - Update "Active" section
   - Add blockers if any
   - Update timestamp
   - Update "Updated By"

2. **Commit**:
   ```bash
   git add .ai/CONTEXT.md [and other changed files]
   git commit -m "type: brief description of work done"
   ```

3. **Summarize for User**:
   - What was completed
   - What's next
   - Any issues or blockers

---

## Handoff Between Agents

**Outgoing**:
- Complete current task if possible
- Update CONTEXT.md thoroughly
- Commit changes

**Incoming**:
- Read CONTEXT.md
- Continue from last task
- Update "Updated By"

---

## Recovery

### If Context is Unclear
1. Check git history: `git log --oneline -10`
2. Verify actual state: `ls -la`, `git status`
3. Update CONTEXT.md to reflect reality
4. Ask user if uncertain

---

**Keep CONTEXT.md updated and handoffs will be smooth.**
