# HTML Report Fix Summary

## Problem
The HTML report generation was failing with the error:
```
format_html_table() got an unexpected keyword argument 'limit'
```

## Root Cause
The `generate_html_report()` method in `tournament_tracker.py` was calling `format_html_table(limit=limit)`, but the function signature expected `format_html_table(attendance_tracker, org_names)` - it needed data parameters, not a limit parameter.

## Solution

### 1. Fixed the function call
Changed from:
```python
html = format_html_table(limit=limit)
```

To:
```python
# Get data from database in the format expected by format_html_table
attendance_tracker, org_names = get_legacy_attendance_data()

# Generate HTML
html = format_html_table(attendance_tracker, org_names)
```

### 2. Fixed tournament count display
The tournament counts were showing as 0 because:
- `get_attendance_rankings()` returns `tournament_count` field
- `get_legacy_attendance_data()` was looking for `num_events` field

Fixed by using the correct field name:
```python
tournament_count = org_data.get('tournament_count', 0)
attendance_tracker[key] = {
    'tournaments': [''] * tournament_count,  # Create list with correct count
    'total_attendance': org_data.get('total_attendance', 0),
    'contacts': []
}
```

## Files Modified
- `tournament_tracker.py` - Fixed the HTML report generation method
- `tournament_report.py` - Fixed the tournament count field mapping

## Testing
Confirmed working with:
```bash
./go.py --html /tmp/test_report.html
```

The report now correctly shows:
- Organization names
- Tournament counts
- Total attendance
- Proper formatting and styling

## Result
✅ HTML report generation is now fully functional and compatible with the enhanced models.