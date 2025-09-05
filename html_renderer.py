"""
html_renderer.py - HTML Rendering Service
Modern OOP replacement for html_utils.py
Stateful HTML renderer with templates, themes, and component generation
"""
from typing import List, Tuple, Dict, Any, Optional, Callable
from datetime import datetime, timezone, timedelta
from pathlib import Path
import html
import json


class HTMLRenderer:
    """Stateful HTML rendering service with theming and templates"""
    
    def __init__(self, theme: str = 'dark', template_dir: Optional[Path] = None):
        """Initialize HTML renderer with theme and template configuration"""
        self.theme = theme
        self.template_dir = template_dir or Path('.')
        self._templates_cache = {}
        self._components = {}
        self._current_page = []
        
        # Theme configurations
        self.themes = {
            'dark': {
                'bg_color': '#1a1a2e',
                'text_color': '#eee',
                'accent_color': '#e74c3c',
                'link_color': '#3498db',
                'border_color': '#444',
                'table_header_bg': '#16213e'
            },
            'light': {
                'bg_color': '#ffffff',
                'text_color': '#333',
                'accent_color': '#e74c3c',
                'link_color': '#2980b9',
                'border_color': '#ddd',
                'table_header_bg': '#f8f9fa'
            },
            'hacker': {
                'bg_color': '#000000',
                'text_color': '#00ff00',
                'accent_color': '#ff0000',
                'link_color': '#00ffff',
                'border_color': '#00ff00',
                'table_header_bg': '#001100'
            }
        }
        
        # Register default components
        self._register_default_components()
    
    def _register_default_components(self):
        """Register default HTML components"""
        self.register_component('nav_bar', self._nav_bar_component)
        self.register_component('stats_card', self._stats_card_component)
        self.register_component('data_table', self._data_table_component)
        self.register_component('footer', self._footer_component)
    
    @property
    def current_theme(self) -> Dict[str, str]:
        """Get current theme configuration"""
        return self.themes.get(self.theme, self.themes['dark'])
    
    def set_theme(self, theme: str):
        """Change the current theme"""
        if theme in self.themes:
            self.theme = theme
        else:
            raise ValueError(f"Unknown theme: {theme}. Available: {list(self.themes.keys())}")
    
    def add_theme(self, name: str, config: Dict[str, str]):
        """Add a custom theme"""
        self.themes[name] = config
    
    def register_component(self, name: str, renderer: Callable):
        """Register a reusable component"""
        self._components[name] = renderer
    
    def start_page(self, title: str, subtitle: Optional[str] = None, 
                   meta_tags: Optional[Dict[str, str]] = None) -> 'HTMLRenderer':
        """Start building a new HTML page"""
        self._current_page = []
        
        # Build head section
        self._current_page.append('<!DOCTYPE html>')
        self._current_page.append('<html lang="en">')
        self._current_page.append('<head>')
        self._current_page.append(f'    <title>{html.escape(title)}</title>')
        self._current_page.append('    <meta charset="utf-8">')
        self._current_page.append('    <meta name="viewport" content="width=device-width, initial-scale=1">')
        
        # Add custom meta tags
        if meta_tags:
            for name, content in meta_tags.items():
                self._current_page.append(
                    f'    <meta name="{html.escape(name)}" content="{html.escape(content)}">'
                )
        
        # Add theme styles
        self._current_page.append(self._generate_styles())
        self._current_page.append('</head>')
        self._current_page.append('<body>')
        
        # Add header
        self._current_page.append(f'    <h1 class="page-title">{html.escape(title)}</h1>')
        if subtitle:
            self._current_page.append(f'    <p class="page-subtitle">{html.escape(subtitle)}</p>')
        
        return self
    
    def add_component(self, component_name: str, **kwargs) -> 'HTMLRenderer':
        """Add a registered component to the current page"""
        if component_name not in self._components:
            raise ValueError(f"Component '{component_name}' not registered")
        
        component_html = self._components[component_name](**kwargs)
        self._current_page.append(component_html)
        return self
    
    def add_html(self, html_content: str) -> 'HTMLRenderer':
        """Add raw HTML content to the current page"""
        self._current_page.append(html_content)
        return self
    
    def add_section(self, title: str, content: str, section_class: str = "content-section") -> 'HTMLRenderer':
        """Add a content section with title"""
        section_html = f'''
    <div class="{section_class}">
        <h2>{html.escape(title)}</h2>
        <div class="section-content">
            {content}
        </div>
    </div>'''
        self._current_page.append(section_html)
        return self
    
    def add_table(self, headers: List[str], rows: List[List[Any]], 
                  table_id: Optional[str] = None,
                  sortable: bool = False,
                  row_formatter: Optional[Callable] = None) -> 'HTMLRenderer':
        """Add a data table to the current page"""
        table_html = self._data_table_component(
            headers, rows, table_id, sortable, row_formatter
        )
        self._current_page.append(table_html)
        return self
    
    def add_nav_links(self, links: List[Tuple[str, str]]) -> 'HTMLRenderer':
        """Add navigation links"""
        nav_html = self._nav_bar_component(links)
        self._current_page.append(nav_html)
        return self
    
    def add_stats_cards(self, stats: List[Dict[str, Any]]) -> 'HTMLRenderer':
        """Add statistics cards"""
        cards_html = '<div class="stats-container">'
        for stat in stats:
            cards_html += self._stats_card_component(
                stat.get('title', ''),
                stat.get('value', ''),
                stat.get('subtitle', ''),
                stat.get('icon', '')
            )
        cards_html += '</div>'
        self._current_page.append(cards_html)
        return self
    
    def finish_page(self) -> str:
        """Finish building the page and return HTML"""
        self._current_page.append(self._footer_component())
        self._current_page.append('</body>')
        self._current_page.append('</html>')
        
        result = '\n'.join(self._current_page)
        self._current_page = []  # Clear for next page
        return result
    
    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render a template file with context"""
        template_path = self.template_dir / template_name
        
        # Cache templates
        if template_name not in self._templates_cache:
            if not template_path.exists():
                raise FileNotFoundError(f"Template not found: {template_path}")
            
            with open(template_path, 'r') as f:
                self._templates_cache[template_name] = f.read()
        
        template = self._templates_cache[template_name]
        
        # Simple template variable replacement
        for key, value in context.items():
            template = template.replace(f'{{{{{key}}}}}', str(value))
        
        return template
    
    def save_page(self, content: str, filename: str):
        """Save HTML content to file"""
        output_path = Path(filename)
        output_path.write_text(content)
        return output_path
    
    # Component implementations
    
    def _generate_styles(self) -> str:
        """Generate CSS styles based on current theme"""
        theme = self.current_theme
        return f'''
    <style>
        :root {{
            --bg-color: {theme['bg_color']};
            --text-color: {theme['text_color']};
            --accent-color: {theme['accent_color']};
            --link-color: {theme['link_color']};
            --border-color: {theme['border_color']};
            --table-header-bg: {theme['table_header_bg']};
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
            padding: 2rem;
        }}
        
        h1.page-title {{
            color: var(--accent-color);
            margin-bottom: 0.5rem;
            font-size: 2.5rem;
        }}
        
        p.page-subtitle {{
            color: var(--text-color);
            opacity: 0.8;
            margin-bottom: 2rem;
        }}
        
        a {{
            color: var(--link-color);
            text-decoration: none;
        }}
        
        a:hover {{
            text-decoration: underline;
        }}
        
        .nav-links {{
            background: rgba(255, 255, 255, 0.05);
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
        }}
        
        .nav-links a {{
            padding: 0.5rem 1rem;
            background: var(--accent-color);
            color: white;
            border-radius: 4px;
            transition: opacity 0.3s;
        }}
        
        .nav-links a:hover {{
            opacity: 0.8;
            text-decoration: none;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
            background: rgba(255, 255, 255, 0.02);
        }}
        
        th {{
            background: var(--table-header-bg);
            padding: 0.75rem;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid var(--border-color);
        }}
        
        td {{
            padding: 0.75rem;
            border-bottom: 1px solid var(--border-color);
        }}
        
        tr:hover {{
            background: rgba(255, 255, 255, 0.05);
        }}
        
        .stats-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
            margin: 2rem 0;
        }}
        
        .stat-card {{
            background: rgba(255, 255, 255, 0.05);
            padding: 1.5rem;
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }}
        
        .stat-value {{
            font-size: 2rem;
            font-weight: bold;
            color: var(--accent-color);
        }}
        
        .stat-title {{
            font-size: 0.9rem;
            opacity: 0.8;
            margin-bottom: 0.5rem;
        }}
        
        .stat-subtitle {{
            font-size: 0.8rem;
            opacity: 0.6;
            margin-top: 0.5rem;
        }}
        
        .content-section {{
            margin: 2rem 0;
            padding: 1.5rem;
            background: rgba(255, 255, 255, 0.02);
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }}
        
        .content-section h2 {{
            color: var(--accent-color);
            margin-bottom: 1rem;
        }}
        
        .footer {{
            margin-top: 3rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border-color);
            text-align: center;
            opacity: 0.6;
            font-size: 0.9rem;
        }}
        
        @media (max-width: 768px) {{
            body {{
                padding: 1rem;
            }}
            
            h1.page-title {{
                font-size: 1.8rem;
            }}
            
            .stats-container {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>'''
    
    def _nav_bar_component(self, links: List[Tuple[str, str]]) -> str:
        """Generate navigation bar component"""
        nav_html = '<div class="nav-links">'
        for url, text in links:
            nav_html += f'<a href="{html.escape(url)}">{html.escape(text)}</a>'
        nav_html += '</div>'
        return nav_html
    
    def _stats_card_component(self, title: str, value: str, subtitle: str = "", icon: str = "") -> str:
        """Generate statistics card component"""
        return f'''
    <div class="stat-card">
        <div class="stat-title">{html.escape(title)}</div>
        <div class="stat-value">{html.escape(str(value))}</div>
        {f'<div class="stat-subtitle">{html.escape(subtitle)}</div>' if subtitle else ''}
    </div>'''
    
    def _data_table_component(self, headers: List[str], rows: List[List[Any]], 
                             table_id: Optional[str] = None,
                             sortable: bool = False,
                             row_formatter: Optional[Callable] = None) -> str:
        """Generate data table component"""
        table_attrs = f'id="{table_id}"' if table_id else ''
        if sortable:
            table_attrs += ' class="sortable"'
        
        table_html = f'<table {table_attrs}>\n<thead>\n<tr>'
        
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
    
    def _footer_component(self) -> str:
        """Generate footer component"""
        from datetime import datetime, timezone, timedelta
        
        # Get current time in Pacific timezone (UTC-8)
        pacific_offset = timedelta(hours=-8)
        pacific_tz = timezone(pacific_offset)
        pacific_time = datetime.now(pacific_tz)
        time_str = pacific_time.strftime('%Y-%m-%d %I:%M:%S %p PST')
        
        return f'''
    <div class="footer">
        Generated by Tournament Tracker • {time_str} • 
        Theme: {self.theme}
    </div>'''
    
    def create_error_page(self, error_title: str, error_message: str, 
                         suggestions: Optional[List[str]] = None) -> str:
        """Create a formatted error page"""
        self.start_page(f"Error: {error_title}")
        
        error_html = f'''
    <div class="error-container" style="background: rgba(231, 76, 60, 0.1); 
                                       border: 2px solid #e74c3c; 
                                       border-radius: 8px; 
                                       padding: 2rem; 
                                       margin: 2rem 0;">
        <h2 style="color: #e74c3c;">⚠️ {html.escape(error_title)}</h2>
        <p style="margin: 1rem 0;">{html.escape(error_message)}</p>'''
        
        if suggestions:
            error_html += '<h3>Suggestions:</h3><ul>'
            for suggestion in suggestions:
                error_html += f'<li>{html.escape(suggestion)}</li>'
            error_html += '</ul>'
        
        error_html += '</div>'
        
        self.add_html(error_html)
        return self.finish_page()
    
    def create_redirect_page(self, target_url: str, message: str = "Redirecting...", delay: int = 0) -> str:
        """Create a redirect page with optional delay"""
        self.start_page("Redirecting")
        
        redirect_html = f'''
    <meta http-equiv="refresh" content="{delay}; url={html.escape(target_url)}">
    <div style="text-align: center; margin-top: 4rem;">
        <h2>{html.escape(message)}</h2>
        <p>You will be redirected in {delay} seconds...</p>
        <p>Or <a href="{html.escape(target_url)}">click here</a> to continue.</p>
    </div>'''
        
        self.add_html(redirect_html)
        return self.finish_page()


# Global renderer instance with default dark theme
html_renderer = HTMLRenderer(theme='dark')

# Convenience function for backward compatibility
def get_html_renderer(theme: str = 'dark') -> HTMLRenderer:
    """Get HTML renderer instance"""
    return HTMLRenderer(theme=theme)