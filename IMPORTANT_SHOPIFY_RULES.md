# ⚠️ CRITICAL SHOPIFY RULES - READ BEFORE MAKING ANY CHANGES ⚠️

## 🚨 ABSOLUTE RULE: NEVER CREATE NEW SHOPIFY PAGES 🚨

### The ONLY page we update is: `/pages/attendance`

## How Shopify Publishing Works in This Project:

1. **We update the THEME TEMPLATE**: `templates/page.attendance.json`
2. **We NEVER create new pages via the Pages API**
3. **We NEVER create pages with handles like:**
   - ❌ `/pages/player-rankings-data`
   - ❌ `/pages/organization-rankings-data`  
   - ❌ `/pages/tournament-rankings`
   - ❌ Any other new pages

## The Correct Approach:

```python
# CORRECT - Updates the theme template
template = "templates/page.attendance.json"
asset_url = f"https://{store_url}/admin/api/2023-10/themes/{theme_id}/assets.json"

# WRONG - Creates new pages
page_url = f"https://{store_url}/admin/api/2023-10/pages.json"  # NEVER DO THIS!
```

## File Location:
- Working implementation: `tournament_report.py:update_template()`
- This updates the existing `/pages/attendance` page by modifying its theme template

## Configuration:
- `use_separated_files` in `publish_operation.py` must ALWAYS be `False`
- The separated publisher (`shopify_separated_publisher.py`) should NOT be used in production

## Why This Matters:
- The Shopify store has ONE attendance page that displays tournament data
- Creating new pages breaks the site structure and user navigation
- The attendance page uses a specific theme template that we update with new data

## If You're Tempted to Create New Pages:
**DON'T!** Instead:
1. Update the existing `templates/page.attendance.json` template
2. Use the working code in `tournament_report.py` as reference
3. Ask before making any changes to how Shopify publishing works

---
Last Updated: 2025-09-06
This file exists because this mistake has been made multiple times. Please respect these rules.