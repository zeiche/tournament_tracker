# ⚠️ WEBDAV PORT 8443 - PERMANENT CONFIGURATION ⚠️

## CRITICAL: DO NOT CHANGE PORT 8443 FOR WEBDAV

**WebDAV PERMANENTLY uses port 8443. This is hardcoded to avoid confusion and debugging issues.**

### Why Port 8443?
- Port 443 requires root privileges (privileged port)
- Running as root causes python environment issues (missing modules)
- Port 8443 is a standard HTTPS alternative that doesn't require root
- Port 8443 is already working and tested

### Configuration Files Updated:
- `webdav_launcher.py` - Default port hardcoded to 8443
- `utils/webdav_switch.py` - Default port hardcoded to 8443
- All files have warning comments about not changing the port

### Access:
- **WebDAV URL**: http://localhost:8443
- **External URL**: https://vpn.zilogo.com:8443 (if firewall allows)
- **Web Editor**: http://localhost:8081 (separate service)

### DO NOT:
- ❌ Change port 8443 to anything else
- ❌ Try to use port 443 for WebDAV
- ❌ Remove the warning comments
- ❌ Debug port issues - 8443 is the permanent solution

### Service Commands:
```bash
./go.py --webdav-refactored        # Starts on port 8443
./go.py --webdav-refactored status # Check status
```

**This decision is FINAL to avoid future debugging confusion.**