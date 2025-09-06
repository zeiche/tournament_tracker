# 🔴 STOP! READ THIS BEFORE TOUCHING ANY SHOPIFY CODE 🔴

## THE THREE DOCUMENTS YOU MUST READ:

1. **`ENV_CONFIGURATION.md`** - Where all tokens are stored
2. **`IMPORTANT_SHOPIFY_RULES.md`** - How Shopify publishing works  
3. **`CLAUDE.md`** - General project guidelines

## QUICK REFERENCE:

### ✅ CORRECT:
```python
# Tokens are in .env file
token = os.getenv('SHOPIFY_ACCESS_TOKEN')  # Correct token
domain = os.getenv('SHOPIFY_DOMAIN')       # From .env

# We update ONE page only
template = "templates/page.attendance.json"  # The ONLY page we update
```

### ❌ WRONG:
```python
# NEVER do these:
token = os.getenv('ACCESS_TOKEN')           # WRONG TOKEN!
domain = "8ccd49-4.myshopify.com"          # NEVER HARDCODE!
create_page("/pages/player-rankings")       # NEVER CREATE PAGES!
```

## THE .env FILE HAS EVERYTHING:

- `SHOPIFY_ACCESS_TOKEN` - The real Shopify token (shpat_...)
- `SHOPIFY_DOMAIN` - The store domain
- `ACCESS_TOKEN` - NOT for Shopify (legacy token)

## WE ONLY UPDATE ONE PAGE:

- **Page**: `/pages/attendance`
- **Method**: Update theme template `templates/page.attendance.json`
- **Never**: Create new pages like `/pages/player-rankings`

---

If you're confused, check:
1. `tournament_report.py:update_template()` - The working implementation
2. The .env file for all configuration

This file exists because we keep making the same mistakes over and over.