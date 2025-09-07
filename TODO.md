# TODO

## 🚨 CURRENT FOCUS: TWILIO VOICE CALLS - MAKE THEM CONVERSATIONAL 🚨

### What User Wants
- Call the phone number (878-879-4283)
- Have a CONVERSATION with Claude via voice
- System listens to speech, sends to Claude, speaks response
- Keeps conversation going (not just one message and hangup)

### Current State
- ✅ Twilio connected (Account: try-hards, Phone: +18788794283)  
- ✅ Can make outbound calls with messages (`simple_call.py` WORKS)
- ✅ Bridges running: port 8082 (simple), 8084 (claude bridge attempt)
- ❌ Interactive webhooks fail with "application error"
- ❌ Speech recognition not working yet

### Key Files
- `simple_call.py` - WORKS for basic TwiML calls
- `twilio_to_claude.py` - Claude bridge on 8084 (webhook issues)
- `twilio_simple_bridge.py` - Basic bridge on 8082  
- `interactive_call.py` - Failed attempt at conversation

### Next Steps for New Claude
1. Fix webhook "application error" issue
2. Get speech recognition working
3. Connect to Claude intelligence (polymorphic queries)
4. Make it conversational (loop until goodbye)

### Test Commands
```bash
# This works - makes call with message
python3 simple_call.py 3233771681 "Hello test"

# Check what's running
ps aux | grep -E "8082|8084"
```

---

## Previous Issue: Discord Voice Connection Error 4006

### Problem
Discord bot gets error 4006 ("Session is no longer valid") when trying to join voice channel #General. The bot HAS successfully connected to voice before, but now consistently fails with this error. After 5 retries it sometimes succeeds but then the event loop gets completely blocked.

### Key Findings
1. Bot connects to Discord text successfully as `try-hard#8718`
2. Bot HAS proper voice permissions (Can connect: True, Can speak: True)  
3. Error 4006 happens immediately when trying to establish voice WebSocket
4. The event loop blocking was caused by `voice_receiver.setup_voice_client()` calling `start_recording()` immediately
5. Even with recording disabled, still getting 4006 errors

### Current Hypothesis
**Discord may still have a stale voice session from a previous connection that wasn't properly closed.** Error 4006 specifically means Discord thinks we're trying to create a duplicate session or reuse an invalid session token.

### What We've Done
1. ✅ Identified that `start_recording()` was blocking the event loop
2. ✅ Disabled voice recording to prevent blocking
3. ✅ Added cleanup code to force disconnect before joining
4. ✅ Reverted to earlier working version (commit 88b8880)
5. ⚠️ Still getting 4006 errors despite fixes

### Next Steps for Next Claude
1. **The bot may need to be manually kicked from voice in Discord** to clear stale session
2. Try waiting longer (10+ seconds) after connecting before joining voice
3. Check if UDP ports are blocked (voice uses UDP, not just WebSocket)
4. Consider that Discord may have flagged this VPS IP (though it worked before)

### How to Test
```bash
./go.py --discord-bot  # Should auto-join #General voice on startup
```

---

## Current Status
- ✅ Tournament data fetching from start.gg is working
- ✅ Database storage in SQLite 
- ✅ Webhook server configured for GitHub integration
- ⚠️ Organization naming/mapping issues need resolution

## Priority Issues

### 1. Organization Naming Problems
- Organizations are not being properly identified/named when syncing from start.gg
- May be duplicates in the database (e.g., "Shark Tank" appears twice in attendance rankings)
- Need to review and fix organization mapping logic

### 2. Database Maintenance
- Use `python3 editor.py` to examine and update organization data
- Clean up duplicate organizations
- Ensure proper organization-tournament associations

## Next Steps

### High Priority
- [ ] Fix organization identification during start.gg sync
- [ ] Deduplicate organizations in database
- [ ] Add validation to prevent future duplicates
- [ ] Test organization mapping with recent tournaments

### Medium Priority
- [ ] Improve editor.py UI for easier organization management
- [ ] Add merge functionality for duplicate organizations
- [ ] Create backup before major database changes
- [ ] Add data validation checks

### Low Priority
- [ ] Document organization naming conventions
- [ ] Add automated tests for organization sync
- [ ] Consider adding organization aliases/alternate names
- [ ] Improve attendance calculation accuracy

## Notes
- The attendance page shows BACKYARD TRY-HARDS at #6 with 663 attendance
- Some organizations appear multiple times in rankings (data quality issue)
- editor.py is the main tool for database inspection and fixes