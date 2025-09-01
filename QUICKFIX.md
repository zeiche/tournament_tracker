# Quick Fix Guide

## Priority 1: Fix Organization Names

### The Problem
Tournaments show email/Discord instead of organization names:
- "tryhardsbackyard@gmail.com" should be "BACKYARD TRY-HARDS"
- "onemustfallgaming@gmail.com" should be "OneMustFall Gaming"

### Quick Fix via Web UI
1. Access http://localhost:8081
2. Click "View Unnamed Tournaments"
3. For each tournament, click Edit and enter proper org name

### Quick Fix via SQL
```bash
sqlite3 tournament_tracker.db

-- See the problem
SELECT DISTINCT primary_contact 
FROM tournament 
WHERE primary_contact LIKE '%@%' 
   OR primary_contact LIKE '%discord%';

-- Fix specific ones
UPDATE tournament 
SET primary_contact = 'BACKYARD TRY-HARDS',
    normalized_contact = 'backyard-try-hards'
WHERE primary_contact = 'tryhardsbackyard@gmail.com';

UPDATE tournament
SET primary_contact = 'OneMustFall Gaming',
    normalized_contact = 'onemustfall-gaming'  
WHERE primary_contact = 'onemustfallgaming@gmail.com';

-- Verify
SELECT primary_contact, COUNT(*) as events, SUM(num_attendees) as total
FROM tournament
GROUP BY primary_contact
ORDER BY total DESC;
```

## Priority 2: Organization Mapping

### Known Mappings
```
Email/Discord → Organization Name
---------------------------------
tryhardsbackyard@gmail.com → BACKYARD TRY-HARDS
onemustfallgaming@gmail.com → OneMustFall Gaming
pow.gaming.official@gmail.com → POW?! Gaming
info@coopers.gg → Cooper's Irvine
gamecrossingllc@gmail.com → Game Crossing
Gglasthero@gmail.com → LAN Hero
considergamingllc@gmail.com → Consider Gaming
https://discord.gg/vwFG4Jxr3G → Shark Tank
https://discord.gg/Y6QfvdhnzJ → Runback Thursday
https://discord.gg/bqD7M2ZK5z → Soul Melter Smash
https://discord.gg/MCSp4N2Enc → UCI
```

## Priority 3: Prevent Future Issues

### Update Sync Logic
File: `startgg_sync.py`
Look for where primary_contact is set
Change to map emails/Discord to organization names

### Add Validation
```python
# In tournament_models.py or startgg_sync.py
def validate_primary_contact(contact):
    """Ensure contact is an org name, not email/discord"""
    if '@' in contact or 'discord' in contact.lower():
        # Look up mapping
        return map_to_organization(contact)
    return contact
```

## Testing After Fixes

```bash
# Check if fixes worked
./go.py --console

# Should show org names, not emails:
# 1st  BACKYARD TRY-HARDS         X events    663 attendance
# 2nd  OneMustFall Gaming         X events    XXX attendance
# NOT: tryhardsbackyard@gmail.com

# Verify in database
sqlite3 tournament_tracker.db
SELECT primary_contact, COUNT(*), SUM(num_attendees) 
FROM tournament 
GROUP BY primary_contact 
ORDER BY SUM(num_attendees) DESC 
LIMIT 10;
```

## Common Commands

```bash
# View current rankings
./go.py --console

# Sync new tournaments
./go.py --sync

# See statistics
./go.py --stats

# Fix via web UI
lynx http://localhost:8081

# Direct database access
sqlite3 tournament_tracker.db
```

## Emergency Rollback

```bash
# Backup before changes
cp tournament_tracker.db tournament_tracker.db.backup

# Restore if needed
cp tournament_tracker.db.backup tournament_tracker.db
```