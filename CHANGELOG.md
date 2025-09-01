# Tournament Tracker Changelog

## 2025-09-01 Session Changes

### Infrastructure
- ✅ Fixed disk space issues (moved /usr files to /usr/local partition)
- ✅ Installed netstat and other system tools
- ✅ Fixed .profile syntax error (removed leading '.')
- ✅ Installed Python dependencies via apt (sqlalchemy, httpx, alembic)

### Webhook Server
- ✅ Set up webhook server (webhook_server.py) on port 8080
- ✅ Created systemd service for persistence (webhook-server.service)
- ✅ Server auto-starts on boot
- ✅ Logs to /var/log/webhook-server.log

### Database Management
- ✅ Created web-based editor (web_editor.py) to replace curses TUI
- ✅ Running on port 8081 (localhost only for security)
- ✅ Accessible via lynx or web browser
- ✅ Routes:
  - / - Home page
  - /unnamed - List tournaments with unnamed contacts (emails/Discord links)
  - /organizations - List all organizations
  - /edit/{id} - Edit tournament organization mapping

### Current Issues
- 🔧 Organizations identified by contact info instead of proper names
- 🔧 Need to map emails/Discord links to organization names like "BACKYARD TRY-HARDS"
- 🔧 Duplicates in database need cleanup

### Files Modified/Created
- `/home/ubuntu/webhook_server.py` - GitHub webhook receiver
- `/home/ubuntu/claude/tournament_tracker/web_editor.py` - Web-based DB editor
- `/home/ubuntu/claude/tournament_tracker/TODO.md` - Project task tracking
- `/etc/systemd/system/webhook-server.service` - Systemd service
- `/home/ubuntu/.profile` - Fixed syntax error

### Services Running
- webhook-server (port 8080) - GitHub webhooks
- web_editor.py (port 8081) - Database management interface

### Next Steps
- Use web interface to map unnamed contacts to proper organization names
- Clean up duplicate organizations
- Test the complete workflow