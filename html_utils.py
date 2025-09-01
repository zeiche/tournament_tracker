#!/usr/bin/env python3
"""
html_utils.py - Shared HTML generation utilities
Common functions for generating consistent HTML across the application
"""

import html
from datetime import datetime, timezone, timedelta
from log_utils import log_debug
from tournament_stylesheet import get_themed_style_tag, get_css_stylesheet

def load_template(template_name):
    """Load HTML template from current directory"""
    try:
        with open(template_name, "r") as f:
            return f.read()
    except FileNotFoundError:
        return None

def get_page_header(title, subtitle=None):
    """Generate consistent page header HTML using centralized styles"""
    header = f"""<!DOCTYPE html>
<html>
<head>
    <title>{html.escape(title)}</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    {get_themed_style_tag()}
</head>
<body>
    <h1>{html.escape(title)}</h1>"""
    
    if subtitle:
        header += f"\n    <p class='subtitle'>{html.escape(subtitle)}</p>"
    
    return header

def get_page_footer():
    """Generate consistent page footer HTML"""
    return """
</body>
</html>"""

def get_nav_links(links):
    """Generate navigation links
    links: list of (url, text) tuples
    """
    nav_html = '<div class="nav-links">'
    for url, text in links:
        nav_html += f'<a href="{html.escape(url)}">{html.escape(text)}</a>'
    nav_html += '</div>'
    return nav_html

def format_table(headers, rows, row_formatter=None):
    """Generate a formatted HTML table
    headers: list of column headers
    rows: list of data rows
    row_formatter: optional function to format each row
    """
    table_html = '<table>\n<thead>\n<tr>'
    
    # Add headers
    for header in headers:
        table_html += f'<th>{html.escape(str(header))}</th>'
    table_html += '</tr>\n</thead>\n<tbody>'
    
    # Add rows
    for row in rows:
        if row_formatter:
            table_html += row_formatter(row)
        else:
            table_html += '\n<tr>'
            for cell in row:
                table_html += f'<td>{html.escape(str(cell))}</td>'
            table_html += '</tr>'
    
    table_html += '\n</tbody>\n</table>'
    return table_html

def format_stats_box(title, stats):
    """Generate a stats box
    stats: dict of stat_name -> stat_value
    """
    stats_html = f'<div class="stats-box">\n<h3>{html.escape(title)}</h3>\n<ul>'
    for name, value in stats.items():
        stats_html += f'\n<li><strong>{html.escape(name)}:</strong> {html.escape(str(value))}</li>'
    stats_html += '\n</ul>\n</div>'
    return stats_html

def get_timestamp():
    """Generate Pacific time timestamp for reports"""
    pacific_offset = timedelta(hours=-7)  # PDT
    pacific_tz = timezone(pacific_offset)
    utc_now = datetime.now(timezone.utc)
    pacific_time = utc_now.astimezone(pacific_tz)
    return pacific_time.strftime("%B %d, %Y at %I:%M %p Pacific")

def format_form(action, method="POST", fields=None):
    """Generate a form
    fields: list of dicts with 'type', 'name', 'label', 'value', 'options' (for select)
    """
    form_html = f'<form method="{method}" action="{html.escape(action)}">'
    
    if fields:
        for field in fields:
            field_type = field.get('type', 'text')
            name = field.get('name', '')
            label = field.get('label', '')
            value = field.get('value', '')
            
            if label:
                form_html += f'\n<p>\n<label for="{name}">{html.escape(label)}:</label><br>'
            
            if field_type == 'select':
                form_html += f'\n<select name="{name}" id="{name}">'
                for option_value, option_text in field.get('options', []):
                    selected = 'selected' if option_value == value else ''
                    form_html += f'\n<option value="{html.escape(option_value)}" {selected}>{html.escape(option_text)}</option>'
                form_html += '\n</select>'
            elif field_type == 'submit':
                form_html += f'\n<input type="submit" value="{html.escape(label)}">'
            elif field_type == 'text':
                form_html += f'\n<input type="text" id="{name}" name="{name}" value="{html.escape(value)}">'
            
            if label and field_type != 'submit':
                form_html += '\n</p>'
    
    form_html += '\n</form>'
    return form_html

def wrap_page(content, title, subtitle=None, nav_links=None):
    """Wrap content in a complete HTML page"""
    page = get_page_header(title, subtitle)
    
    if nav_links:
        page += get_nav_links(nav_links)
    
    page += content
    page += get_page_footer()
    
    return page