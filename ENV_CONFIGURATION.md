# 🔑 ENVIRONMENT CONFIGURATION - CRITICAL DOCUMENTATION

## ⚠️ ALL CONFIGURATION IS IN THE .env FILE ⚠️

### Location: `/home/ubuntu/claude/tournament_tracker/.env`

## Available Environment Variables:

```bash
# Shopify Configuration
SHOPIFY_ACCESS_TOKEN=shpat_xxxxx  # The REAL Shopify API token (starts with shpat_)
SHOPIFY_DOMAIN=8ccd49-4.myshopify.com  # The Shopify store domain
ACCESS_TOKEN=73546ba524xxxxx  # Legacy token - DO NOT USE FOR SHOPIFY

# Discord Configuration  
DISCORD_BOT_TOKEN=xxxxx  # Discord bot token

# Other Services
ANTHROPIC_API_KEY=xxxxx  # For AI features (optional)
```

## CRITICAL RULES:

1. **NEVER hardcode tokens or domains in Python files**
2. **ALWAYS load from environment variables**
3. **The .env file is already loaded by go.py at startup**
4. **Use SHOPIFY_ACCESS_TOKEN for Shopify API calls, NOT ACCESS_TOKEN**

## How to Load Environment Variables:

### ✅ CORRECT - Variables are already loaded by go.py:
```python
import os

# These are already available after go.py loads .env
shopify_token = os.getenv('SHOPIFY_ACCESS_TOKEN')
shopify_domain = os.getenv('SHOPIFY_DOMAIN')
```

### ❌ WRONG - Don't hardcode:
```python
# NEVER DO THIS
store_url = "8ccd49-4.myshopify.com"  # WRONG!
access_token = "shpat_xxxxx"  # WRONG!
```

### ❌ WRONG - Don't use the wrong token:
```python
# ACCESS_TOKEN is NOT for Shopify!
access_token = os.getenv('ACCESS_TOKEN')  # WRONG for Shopify!
```

## The .env File is Loaded Here:

In `go.py` lines 21-33:
```python
# Load environment variables from .env file
env_file = Path(__file__).parent / '.env'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            # ... loads all variables into os.environ
```

## Common Mistakes We Keep Making:

1. **Using ACCESS_TOKEN instead of SHOPIFY_ACCESS_TOKEN**
   - ACCESS_TOKEN is a legacy token, not for Shopify
   - Always use SHOPIFY_ACCESS_TOKEN for Shopify API

2. **Hardcoding the Shopify domain**
   - The domain is in .env as SHOPIFY_DOMAIN
   - Never hardcode "8ccd49-4.myshopify.com"

3. **Not sourcing .env when testing**
   - When running scripts directly, source .env first:
   - `source /home/ubuntu/claude/tournament_tracker/.env && python3 script.py`

4. **Creating duplicate token loading code**
   - go.py already loads .env
   - Don't add more .env loading code

## Files That Need These Variables:

- `tournament_report.py` - Updates /pages/attendance
- `publish_operation.py` - Publishing orchestrator
- Any Shopify-related modules

---
Last Updated: 2025-09-06
This file exists because we keep making the same token/domain mistakes repeatedly.