#!/usr/bin/env python3
"""
tournament_stylesheet.py - Centralized CSS styles for tournament tracker
Provides consistent styling across all HTML generation
"""

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("utils.tournament_stylesheet")

# Color palette
COLORS = {
    'primary_gradient': 'linear-gradient(135deg, #667eea, #764ba2)',
    'secondary_gradient': 'linear-gradient(135deg, #2c3e50, #34495e)',
    'highlight_gradient': 'linear-gradient(135deg, #ff6b6b, #ee5a52)',
    'primary': '#667eea',
    'primary_hover': '#5563d1',
    'text_dark': '#333',
    'text_light': '#666',
    'background': '#f5f5f5',
    'white': 'white',
    'border': '#ddd'
}

def get_inline_styles():
    """Get inline styles as a dictionary for direct HTML generation"""
    return {
        'container': f"max-width:900px;margin:0 auto;padding:20px;font-family:sans-serif;",
        'page_container': f"max-width:1200px;margin:0 auto;padding:20px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:{COLORS['background']};",
        'h1': f"text-align:center;background:{COLORS['primary_gradient']};color:{COLORS['white']};padding:25px;border-radius:12px;",
        'h1_with_margin': f"text-align:center;background:{COLORS['primary_gradient']};color:{COLORS['white']};padding:25px;border-radius:12px;margin-bottom:20px;",
        'h2': f"color:{COLORS['text_dark']};border-bottom:2px solid {COLORS['primary']};padding-bottom:10px;",
        'table': f"width:100%;border-collapse:collapse;margin:20px 0;background:{COLORS['white']};box-shadow:0 6px 25px rgba(0,0,0,0.15);border-radius:12px;overflow:hidden;",
        'thead_tr': f"background:{COLORS['secondary_gradient']};color:{COLORS['white']};",
        'th': "padding:15px 12px;text-align:center;",
        'th_left': "padding:15px 12px;text-align:left;",
        'td': "padding:12px;",
        'td_center': "padding:12px;text-align:center;",
        'td_bold': "padding:12px;text-align:center;font-weight:bold;",
        'rank_highlight': f"background:{COLORS['highlight_gradient']};color:{COLORS['white']};border-radius:6px;padding:6px 8px;",
        'tbody_tr': f"border-bottom:1px solid {COLORS['border']};",
        'tbody_tr_hover': f"background-color:{COLORS['background']};",
        'footer_text': f"text-align:center;color:{COLORS['text_light']};",
        'stats_box': f"background:{COLORS['white']};padding:20px;border-radius:12px;box-shadow:0 4px 15px rgba(0,0,0,0.1);margin:20px 0;",
        'nav_links': "margin:20px 0;text-align:center;",
        'nav_link': f"color:{COLORS['primary']};text-decoration:none;padding:10px 20px;margin:0 10px;border:2px solid {COLORS['primary']};border-radius:8px;display:inline-block;transition:all 0.3s;",
        'nav_link_hover': f"background:{COLORS['primary']};color:{COLORS['white']};",
        'action_link': f"color:{COLORS['primary']};text-decoration:none;font-weight:bold;",
        'form': f"background:{COLORS['white']};padding:30px;border-radius:12px;box-shadow:0 4px 15px rgba(0,0,0,0.1);margin:20px 0;",
        'input': f"width:100%;padding:10px;margin:10px 0;border:1px solid {COLORS['border']};border-radius:6px;font-size:16px;",
        'submit': f"background:{COLORS['primary']};color:{COLORS['white']};padding:12px 30px;border:none;border-radius:6px;font-size:16px;cursor:pointer;margin-right:10px;",
        'submit_hover': f"background:{COLORS['primary_hover']};",
        'cancel_link': f"color:{COLORS['text_light']};text-decoration:none;padding:12px 30px;display:inline-block;"
    }

def get_css_stylesheet():
    """Get complete CSS stylesheet for <style> tags"""
    styles = f"""
        body {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: {COLORS['background']};
        }}
        
        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        h1 {{
            text-align: center;
            background: {COLORS['primary_gradient']};
            color: {COLORS['white']};
            padding: 25px;
            border-radius: 12px;
            margin-bottom: 20px;
        }}
        
        h2 {{
            color: {COLORS['text_dark']};
            border-bottom: 2px solid {COLORS['primary']};
            padding-bottom: 10px;
        }}
        
        h3 {{
            color: {COLORS['text_dark']};
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: {COLORS['white']};
            box-shadow: 0 6px 25px rgba(0,0,0,0.15);
            border-radius: 12px;
            overflow: hidden;
        }}
        
        thead tr {{
            background: {COLORS['secondary_gradient']};
            color: {COLORS['white']};
        }}
        
        th, td {{
            padding: 12px 15px;
            text-align: left;
        }}
        
        th.center, td.center {{
            text-align: center;
        }}
        
        tbody tr {{
            border-bottom: 1px solid {COLORS['border']};
        }}
        
        tbody tr:hover {{
            background-color: {COLORS['background']};
        }}
        
        tbody tr:last-child {{
            border-bottom: none;
        }}
        
        .rank-highlight {{
            background: {COLORS['highlight_gradient']};
            color: {COLORS['white']};
            border-radius: 6px;
            padding: 6px 8px;
        }}
        
        .nav-links {{
            margin: 20px 0;
            text-align: center;
        }}
        
        .nav-links a {{
            color: {COLORS['primary']};
            text-decoration: none;
            padding: 10px 20px;
            margin: 0 10px;
            border: 2px solid {COLORS['primary']};
            border-radius: 8px;
            display: inline-block;
            transition: all 0.3s;
        }}
        
        .nav-links a:hover {{
            background: {COLORS['primary']};
            color: {COLORS['white']};
        }}
        
        .stats-box {{
            background: {COLORS['white']};
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            margin: 20px 0;
        }}
        
        .action-link {{
            color: {COLORS['primary']};
            text-decoration: none;
            font-weight: bold;
        }}
        
        .action-link:hover {{
            text-decoration: underline;
        }}
        
        form {{
            background: {COLORS['white']};
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            margin: 20px 0;
        }}
        
        input[type="text"], select {{
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            border: 1px solid {COLORS['border']};
            border-radius: 6px;
            font-size: 16px;
        }}
        
        input[type="submit"] {{
            background: {COLORS['primary']};
            color: {COLORS['white']};
            padding: 12px 30px;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            cursor: pointer;
            margin-right: 10px;
        }}
        
        input[type="submit"]:hover {{
            background: {COLORS['primary_hover']};
        }}
        
        .cancel-link {{
            color: {COLORS['text_light']};
            text-decoration: none;
            padding: 12px 30px;
            display: inline-block;
        }}
        
        .cancel-link:hover {{
            text-decoration: underline;
        }}
        
        .footer-text {{
            text-align: center;
            color: {COLORS['text_light']};
            margin-top: 30px;
        }}
        
        .subtitle {{
            text-align: center;
            color: {COLORS['text_light']};
            margin-top: -10px;
        }}
        
        /* Responsive design */
        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}
            
            table {{
                font-size: 14px;
            }}
            
            th, td {{
                padding: 8px;
            }}
            
            .nav-links a {{
                display: block;
                margin: 10px auto;
                max-width: 200px;
            }}
        }}
    """
    return styles

def get_themed_style_tag():
    """Get a complete <style> tag with all CSS"""
    return f"<style>{get_css_stylesheet()}</style>"

def apply_inline_style(element, style_name):
    """Apply an inline style to an HTML element
    Example: apply_inline_style('<h1>Title</h1>', 'h1')
    """
    styles = get_inline_styles()
    if style_name in styles:
        # Extract the tag name
        import re
        match = re.match(r'<(\w+)', element)
        if match:
            tag = match.group(1)
            return element.replace(f'<{tag}', f'<{tag} style="{styles[style_name]}"', 1)
    return element

def format_rank_badge(rank):
    """Format a rank number with appropriate styling"""
    styles = get_inline_styles()
    if rank <= 3:
        return f'<span style="{styles["rank_highlight"]}">{rank}</span>'
    return str(rank)