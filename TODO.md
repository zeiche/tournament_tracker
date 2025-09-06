# TODO

## ✅ COMPLETED: Discord Voice Recording Integration

### What Was Done
Connected the Discord voice recording flow! The bot now automatically records audio when joining voice channels.

### Implementation Complete
1. **discord_voice_bot.py** - Added recording functionality ✅
   - Auto-starts recording when joining voice channel
   - Stops recording when leaving
   - Added `!record [start|stop|status]` command for manual control
2. **PolymorphicAudioSink** integration ✅
   - Bot attaches sink when joining voice
   - Calls `voice_client.start_recording(sink)`
   - Handles cleanup on disconnect
3. **Bonjour announcements** working ✅
   - Announces "VOICE_RECORDING" when starting
   - Announces "RECORDING_FINISHED" when done
   - Audio flows through polymorphic pipeline

### The Working Flow
1. User speaks in Discord → 2. Audio sink captures → 3. Announces "AUDIO_RECEIVED" 
4. Storage service stores → 5. Transcription service processes → 6. Claude can respond

### New Commands
- `!join` - Join voice channel (auto-starts recording)
- `!leave` - Leave voice channel (stops recording)
- `!record [start|stop|status]` - Manual recording control

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