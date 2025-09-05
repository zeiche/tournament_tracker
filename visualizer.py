#!/usr/bin/env python3
"""
visualizer.py - Unified Polymorphic Visualization System
ONE visualizer that accepts ANY data format and creates appropriate visualizations
INCLUDING all HTML generation, reports, tables, and web output
"""

import json
import numpy as np
from typing import Any, Union, List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import os
import html
from pathlib import Path

# Import polymorphic handler
from polymorphic_inputs import InputHandler, to_list, to_dict
from database import session_scope
from tournament_models import Tournament, Organization, Player, TournamentPlacement
from log_manager import LogManager

# Get logger
logger = LogManager().get_logger('visualizer')


class UnifiedVisualizer:
    """
    The ONE and ONLY visualizer for the entire system
    Accepts ANY input and creates appropriate visualizations
    """
    
    def __init__(self):
        """Initialize visualizer with lazy-loaded dependencies"""
        self._plt = None
        self._folium = None
        self._ctx = None
        self._session = None
        
    @property
    def plt(self):
        """Lazy load matplotlib"""
        if self._plt is None:
            try:
                import matplotlib.pyplot as plt
                self._plt = plt
            except ImportError:
                logger.error("matplotlib not installed. Run: pip install matplotlib")
        return self._plt
    
    @property
    def folium(self):
        """Lazy load folium"""
        if self._folium is None:
            try:
                import folium
                self._folium = folium
            except ImportError:
                logger.error("folium not installed. Run: pip install folium")
        return self._folium
    
    @property
    def ctx(self):
        """Lazy load contextily for map backgrounds"""
        if self._ctx is None:
            try:
                import contextily as ctx
                self._ctx = ctx
            except ImportError:
                logger.warning("contextily not installed for map backgrounds")
        return self._ctx
    
    def visualize(self, input_data: Any, output: Optional[str] = None, **kwargs) -> Any:
        """
        Main entry point - visualize ANYTHING
        
        Examples:
            visualize(tournament)                    # Single tournament location
            visualize([tournaments])                 # Multiple tournament heatmap
            visualize({"type": "skill", "data": placements})  # Skill heatmap
            visualize("heatmap of riverside")        # Natural language query
            visualize(Player.all())                  # Player distribution
            visualize({"lat": 33.9, "lng": -117.4})  # Single point
            
        Args:
            input_data: ANY type of input data
            output: Optional output file (auto-detected from extension)
            **kwargs: Additional visualization options
            
        Returns:
            Visualization object or file path
        """
        # Parse input using polymorphic handler
        parsed = InputHandler.parse(input_data, 'visualization')
        
        # Determine visualization type
        viz_type = self._determine_viz_type(parsed, kwargs)
        
        # Route to appropriate visualization method
        if viz_type == 'heatmap':
            return self._create_heatmap(parsed, output, **kwargs)
        elif viz_type == 'points':
            return self._create_point_map(parsed, output, **kwargs)
        elif viz_type == 'cluster':
            return self._create_cluster_map(parsed, output, **kwargs)
        elif viz_type == 'timeline':
            return self._create_timeline(parsed, output, **kwargs)
        elif viz_type == 'stats':
            return self._create_stats_chart(parsed, output, **kwargs)
        elif viz_type == 'network':
            return self._create_network_graph(parsed, output, **kwargs)
        else:
            # Default to heatmap
            return self._create_heatmap(parsed, output, **kwargs)
    
    def heatmap(self, input_data: Any, output: Optional[str] = None, **kwargs) -> Any:
        """
        Create a heatmap from ANY input
        
        Examples:
            heatmap(tournaments)                     # Tournament density
            heatmap({"skill": True, "data": placements})  # Skill concentration
            heatmap("player activity")               # Natural language
            heatmap([{"lat": 33, "lng": -117, "weight": 10}, ...])  # Raw data
        """
        parsed = InputHandler.parse(input_data, 'heatmap_data')
        return self._create_heatmap(parsed, output, **kwargs)
    
    def map(self, input_data: Any, output: Optional[str] = None, **kwargs) -> Any:
        """
        Create a map visualization from ANY input
        Alias for visualize() with map-specific defaults
        """
        kwargs.setdefault('interactive', True)
        return self.visualize(input_data, output, **kwargs)
    
    def chart(self, input_data: Any, output: Optional[str] = None, **kwargs) -> Any:
        """
        Create a chart/graph from ANY input
        
        Examples:
            chart(player_stats)                      # Player statistics
            chart({"x": dates, "y": attendance})     # Time series
            chart(Tournament.monthly_stats())        # Monthly trends
        """
        parsed = InputHandler.parse(input_data, 'chart_data')
        return self._create_stats_chart(parsed, output, **kwargs)
    
    def html(self, input_data: Any, output: Optional[str] = None, **kwargs) -> str:
        """
        Generate HTML from ANY input - reports, tables, pages, etc.
        
        Examples:
            html(tournaments)                        # Tournament table
            html({"type": "report", "data": stats}) # Statistical report
            html(players, template="player_cards")  # Player cards
            html("attendance report")               # Natural language
        """
        parsed = InputHandler.parse(input_data, 'html_content')
        
        # Determine HTML type
        html_type = kwargs.get('type', self._determine_html_type(parsed))
        
        if html_type == 'table':
            html_content = self._create_html_table(parsed, **kwargs)
        elif html_type == 'report':
            html_content = self._create_html_report(parsed, **kwargs)
        elif html_type == 'cards':
            html_content = self._create_html_cards(parsed, **kwargs)
        elif html_type == 'page':
            html_content = self._create_html_page(parsed, **kwargs)
        else:
            # Default to table
            html_content = self._create_html_table(parsed, **kwargs)
        
        # Save or return
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"HTML saved to {output}")
            return output
        else:
            return html_content
    
    def report(self, input_data: Any, output: Optional[str] = None, **kwargs) -> str:
        """
        Generate a report (HTML or text) from ANY input
        
        Examples:
            report(Tournament.all())                 # Tournament report
            report({"attendance": stats})           # Attendance report
            report(player_rankings)                 # Player rankings report
        """
        kwargs['type'] = 'report'
        
        # Check output format
        if output and output.endswith('.txt'):
            return self._create_text_report(input_data, output, **kwargs)
        else:
            return self.html(input_data, output, **kwargs)
    
    def table(self, input_data: Any, output: Optional[str] = None, **kwargs) -> str:
        """
        Generate an HTML table from ANY input
        
        Examples:
            table(tournaments)                       # Tournament table
            table([{"name": "John", "score": 100}]) # Dict list to table
            table(players, columns=["name", "wins"]) # Specific columns
        """
        kwargs['type'] = 'table'
        return self.html(input_data, output, **kwargs)
    
    def _determine_viz_type(self, parsed: Dict, kwargs: Dict) -> str:
        """Determine the best visualization type from parsed input"""
        # Explicit type in kwargs
        if 'type' in kwargs:
            return kwargs['type']
        
        # Check parsed data structure
        if isinstance(parsed, dict):
            # Explicit type in data
            if 'type' in parsed:
                return parsed['type']
            
            # Infer from metadata
            metadata = parsed.get('_metadata', {})
            if metadata.get('type') == 'entity':
                return 'points'
            elif 'skill' in parsed or 'weight' in parsed:
                return 'heatmap'
            elif 'timeline' in parsed or 'dates' in parsed:
                return 'timeline'
            elif 'network' in parsed or 'connections' in parsed:
                return 'network'
            elif 'stats' in parsed or 'metrics' in parsed:
                return 'stats'
        
        # Default based on data count
        if isinstance(parsed, dict) and 'count' in parsed:
            if parsed['count'] > 100:
                return 'heatmap'
            elif parsed['count'] > 20:
                return 'cluster'
            else:
                return 'points'
        
        return 'heatmap'  # Default
    
    def _create_heatmap(self, parsed: Dict, output: Optional[str], **kwargs) -> Any:
        """Create a heatmap visualization"""
        # Extract location data
        points = self._extract_location_data(parsed)
        
        if not points:
            logger.error("No location data found for heatmap")
            return None
        
        # Determine output format
        if output and output.endswith('.html'):
            return self._create_interactive_heatmap(points, output, **kwargs)
        else:
            return self._create_static_heatmap(points, output, **kwargs)
    
    def _create_static_heatmap(self, points: List[Tuple], output: Optional[str], **kwargs) -> str:
        """Create static heatmap image"""
        if not self.plt:
            return None
        
        try:
            import matplotlib.cm as cm
            from scipy.stats import gaussian_kde
        except ImportError:
            logger.error("scipy required for static heatmaps. Run: pip install scipy")
            return None
        
        # Extract coordinates and weights
        lats = [p[0] for p in points]
        lngs = [p[1] for p in points]
        weights = [p[2] if len(p) > 2 else 1 for p in points]
        
        # Create figure
        fig, ax = self.plt.subplots(figsize=kwargs.get('figsize', (12, 8)))
        
        # SoCal boundaries
        lat_min = kwargs.get('lat_min', 32.5)
        lat_max = kwargs.get('lat_max', 34.5)
        lng_min = kwargs.get('lng_min', -119)
        lng_max = kwargs.get('lng_max', -116)
        
        # Add map background if available
        if kwargs.get('map_background', True) and self.ctx:
            try:
                # Convert to Web Mercator
                import contextily as ctx
                from matplotlib import patheffects
                
                ax.set_xlim(lng_min, lng_max)
                ax.set_ylim(lat_min, lat_max)
                
                # Add basemap
                ctx.add_basemap(ax, crs='EPSG:4326', source=ctx.providers.CartoDB.Positron)
            except Exception as e:
                logger.warning(f"Could not add map background: {e}")
        
        # Create density plot
        if len(points) > 1:
            try:
                # Create KDE
                positions = np.vstack([lngs, lats])
                kernel = gaussian_kde(positions, weights=weights)
                
                # Create grid
                xx, yy = np.mgrid[lng_min:lng_max:100j, lat_min:lat_max:100j]
                positions_grid = np.vstack([xx.ravel(), yy.ravel()])
                density = kernel(positions_grid).T.reshape(xx.shape)
                
                # Plot density
                im = ax.contourf(xx, yy, density, levels=15, cmap='hot', alpha=0.6)
                self.plt.colorbar(im, ax=ax, label='Density')
            except:
                # Fallback to scatter plot
                scatter = ax.scatter(lngs, lats, s=weights, c=weights, cmap='hot', alpha=0.6)
                self.plt.colorbar(scatter, ax=ax, label='Weight')
        else:
            # Single point
            ax.scatter(lngs, lats, s=100, c='red', marker='o')
        
        # Labels
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.set_title(kwargs.get('title', 'Tournament Heatmap'))
        
        # Save or show
        if output:
            self.plt.savefig(output, dpi=kwargs.get('dpi', 150), bbox_inches='tight')
            logger.info(f"Static heatmap saved to {output}")
            self.plt.close()
            return output
        else:
            self.plt.show()
            return fig
    
    def _create_interactive_heatmap(self, points: List[Tuple], output: Optional[str], **kwargs) -> str:
        """Create interactive folium heatmap"""
        if not self.folium:
            return None
        
        from folium.plugins import HeatMap
        
        # Create map centered on data
        center_lat = np.mean([p[0] for p in points])
        center_lng = np.mean([p[1] for p in points])
        
        m = self.folium.Map(
            location=[center_lat, center_lng],
            zoom_start=kwargs.get('zoom', 9),
            tiles=kwargs.get('tiles', 'CartoDB positron')
        )
        
        # Add heatmap layer - extract only numeric values
        heatmap_data = [[p[0], p[1], p[2] if len(p) > 2 else 1] for p in points]
        
        HeatMap(
            heatmap_data,
            min_opacity=kwargs.get('min_opacity', 0.2),
            max_zoom=kwargs.get('max_zoom', 18),
            radius=kwargs.get('radius', 15),
            blur=kwargs.get('blur', 15),
            gradient=kwargs.get('gradient', None)
        ).add_to(m)
        
        # Add title
        if 'title' in kwargs:
            title_html = f'''
                <div style="position: fixed; 
                            top: 10px; left: 50%; transform: translateX(-50%);
                            background-color: white; padding: 10px;
                            border: 2px solid grey; z-index: 9999;
                            font-size: 16px; font-weight: bold;">
                    {kwargs['title']}
                </div>
            '''
            m.get_root().html.add_child(self.folium.Element(title_html))
        
        # Save
        if output:
            m.save(output)
            logger.info(f"Interactive heatmap saved to {output}")
            return output
        else:
            return m
    
    def _create_point_map(self, parsed: Dict, output: Optional[str], **kwargs) -> Any:
        """Create a point map for individual locations"""
        points = self._extract_location_data(parsed)
        
        if not points:
            logger.error("No location data found for point map")
            return None
        
        if not self.folium:
            # Fallback to static
            return self._create_static_heatmap(points, output, **kwargs)
        
        # Create interactive map
        center_lat = np.mean([p[0] for p in points])
        center_lng = np.mean([p[1] for p in points])
        
        m = self.folium.Map(
            location=[center_lat, center_lng],
            zoom_start=kwargs.get('zoom', 10)
        )
        
        # Add markers
        for point in points:
            lat, lng = point[0], point[1]
            popup_text = point[3] if len(point) > 3 else f"Location: {lat:.3f}, {lng:.3f}"
            
            self.folium.Marker(
                [lat, lng],
                popup=popup_text,
                tooltip=popup_text
            ).add_to(m)
        
        # Save
        if output:
            m.save(output)
            logger.info(f"Point map saved to {output}")
            return output
        else:
            return m
    
    def _create_stats_chart(self, parsed: Dict, output: Optional[str], **kwargs) -> Any:
        """Create statistical charts"""
        if not self.plt:
            return None
        
        # Extract chart data
        chart_data = self._extract_chart_data(parsed)
        
        if not chart_data:
            logger.error("No data found for chart")
            return None
        
        fig, ax = self.plt.subplots(figsize=kwargs.get('figsize', (10, 6)))
        
        # Determine chart type
        chart_type = kwargs.get('chart_type', 'bar')
        
        if chart_type == 'bar':
            ax.bar(chart_data['x'], chart_data['y'])
        elif chart_type == 'line':
            ax.plot(chart_data['x'], chart_data['y'], marker='o')
        elif chart_type == 'scatter':
            ax.scatter(chart_data['x'], chart_data['y'])
        elif chart_type == 'pie':
            ax.pie(chart_data['y'], labels=chart_data['x'], autopct='%1.1f%%')
        
        # Labels
        ax.set_xlabel(kwargs.get('xlabel', 'X'))
        ax.set_ylabel(kwargs.get('ylabel', 'Y'))
        ax.set_title(kwargs.get('title', 'Statistics'))
        
        # Rotate x labels if needed
        if len(chart_data['x']) > 10:
            self.plt.xticks(rotation=45, ha='right')
        
        self.plt.tight_layout()
        
        # Save or show
        if output:
            self.plt.savefig(output, dpi=kwargs.get('dpi', 150), bbox_inches='tight')
            logger.info(f"Chart saved to {output}")
            self.plt.close()
            return output
        else:
            self.plt.show()
            return fig
    
    def _extract_location_data(self, parsed: Any) -> List[Tuple]:
        """Extract location data from parsed input"""
        points = []
        
        with session_scope() as session:
            if isinstance(parsed, dict):
                # Direct coordinate data
                if 'lat' in parsed and 'lng' in parsed:
                    weight = parsed.get('weight', 1)
                    points.append((parsed['lat'], parsed['lng'], weight))
                
                # List of items
                elif 'items' in parsed:
                    for item in parsed['items']:
                        if isinstance(item, tuple):
                            # Direct tuple format: (lat, lng) or (lat, lng, weight)
                            if len(item) >= 2:
                                lat, lng = item[0], item[1]
                                weight = item[2] if len(item) > 2 else 1
                                points.append((float(lat), float(lng), float(weight)))
                        elif isinstance(item, dict):
                            if 'lat' in item and 'lng' in item:
                                points.append((item['lat'], item['lng'], item.get('weight', 1)))
                        elif hasattr(item, 'lat') and hasattr(item, 'lng'):
                            if item.lat and item.lng:
                                weight = item.get_heatmap_weight() if hasattr(item, 'get_heatmap_weight') else 1
                                points.append((float(item.lat), float(item.lng), float(weight), str(item)))
                
                # Model data
                elif 'model' in parsed and parsed['model'] == 'Tournament':
                    # Get tournament from database
                    if 'id' in parsed:
                        t = session.query(Tournament).get(parsed['id'])
                        if t and t.has_location:
                            points.append((*t.coordinates, t.get_heatmap_weight(), str(t)))
            
            # If no points yet, try to get all tournaments
            if not points and ('tournament' in str(parsed).lower() or not parsed):
                tournaments = session.query(Tournament).filter(
                    Tournament.lat.isnot(None),
                    Tournament.lng.isnot(None)
                ).all()
                
                for t in tournaments:
                    if t.has_location:
                        lat, lng = t.coordinates
                        weight = t.get_heatmap_weight() if hasattr(t, 'get_heatmap_weight') else 1
                        points.append((float(lat), float(lng), float(weight), str(t)))
        
        return points
    
    def _extract_chart_data(self, parsed: Any) -> Dict:
        """Extract chart data from parsed input"""
        chart_data = {'x': [], 'y': []}
        
        if isinstance(parsed, dict):
            # Direct x/y data
            if 'x' in parsed and 'y' in parsed:
                chart_data['x'] = to_list(parsed['x'])
                chart_data['y'] = to_list(parsed['y'])
            
            # Stats data
            elif 'stats' in parsed:
                stats = parsed['stats']
                if isinstance(stats, dict):
                    chart_data['x'] = list(stats.keys())
                    chart_data['y'] = list(stats.values())
            
            # Items with attributes
            elif 'items' in parsed:
                for item in parsed['items']:
                    if isinstance(item, dict):
                        chart_data['x'].append(item.get('name', ''))
                        chart_data['y'].append(item.get('value', 0))
        
        return chart_data if chart_data['x'] else None
    
    def _create_cluster_map(self, parsed: Dict, output: Optional[str], **kwargs) -> Any:
        """Create a cluster map for grouped locations"""
        # Delegate to point map with clustering enabled
        kwargs['cluster'] = True
        return self._create_point_map(parsed, output, **kwargs)
    
    def _create_timeline(self, parsed: Dict, output: Optional[str], **kwargs) -> Any:
        """Create a timeline visualization"""
        # Extract time series data and create line chart
        kwargs['chart_type'] = 'line'
        return self._create_stats_chart(parsed, output, **kwargs)
    
    def _create_network_graph(self, parsed: Dict, output: Optional[str], **kwargs) -> Any:
        """Create a network graph visualization"""
        # TODO: Implement network visualization
        logger.warning("Network visualization not yet implemented")
        return None
    
    def _determine_html_type(self, parsed: Dict) -> str:
        """Determine the type of HTML to generate"""
        if isinstance(parsed, dict):
            if 'type' in parsed:
                return parsed['type']
            elif 'report' in str(parsed).lower():
                return 'report'
            elif 'table' in str(parsed).lower():
                return 'table'
        
        # Default based on data structure
        if isinstance(parsed, dict) and 'items' in parsed:
            return 'table'
        
        return 'page'
    
    def _create_html_table(self, parsed: Any, **kwargs) -> str:
        """Create an HTML table from parsed data"""
        # Extract data
        data = self._extract_table_data(parsed)
        
        if not data:
            return "<p>No data to display</p>"
        
        # Start HTML
        html_parts = []
        
        # Add CSS if not embedded
        if not kwargs.get('embedded', False):
            html_parts.append(self._get_html_header(kwargs.get('title', 'Data Table')))
        
        # Table
        html_parts.append('<table class="data-table">')
        
        # Headers
        if data and len(data) > 0:
            headers = kwargs.get('columns')
            if not headers and isinstance(data[0], dict):
                headers = list(data[0].keys())
            elif not headers:
                headers = [f"Column {i+1}" for i in range(len(data[0]) if isinstance(data[0], (list, tuple)) else 1)]
            
            html_parts.append('<thead><tr>')
            for header in headers:
                html_parts.append(f'<th>{html.escape(str(header))}</th>')
            html_parts.append('</tr></thead>')
        
        # Body
        html_parts.append('<tbody>')
        for row in data:
            html_parts.append('<tr>')
            if isinstance(row, dict):
                for header in headers:
                    value = row.get(header, '')
                    html_parts.append(f'<td>{html.escape(str(value))}</td>')
            elif isinstance(row, (list, tuple)):
                for value in row:
                    html_parts.append(f'<td>{html.escape(str(value))}</td>')
            else:
                html_parts.append(f'<td>{html.escape(str(row))}</td>')
            html_parts.append('</tr>')
        html_parts.append('</tbody>')
        
        html_parts.append('</table>')
        
        # Footer if not embedded
        if not kwargs.get('embedded', False):
            html_parts.append(self._get_html_footer())
        
        return '\n'.join(html_parts)
    
    def _create_html_report(self, parsed: Any, **kwargs) -> str:
        """Create an HTML report from parsed data"""
        html_parts = []
        
        # Header
        title = kwargs.get('title', 'Report')
        html_parts.append(self._get_html_header(title))
        
        # Extract report data
        report_data = self._extract_report_data(parsed)
        
        # Summary section
        if 'summary' in report_data:
            html_parts.append('<div class="summary">')
            html_parts.append('<h2>Summary</h2>')
            for key, value in report_data['summary'].items():
                html_parts.append(f'<p><strong>{html.escape(str(key))}:</strong> {html.escape(str(value))}</p>')
            html_parts.append('</div>')
        
        # Main content
        if 'content' in report_data:
            html_parts.append('<div class="content">')
            # If content is a table, embed it
            if isinstance(report_data['content'], (list, tuple)):
                table_html = self._create_html_table(report_data['content'], embedded=True, **kwargs)
                html_parts.append(table_html)
            else:
                html_parts.append(str(report_data['content']))
            html_parts.append('</div>')
        
        # Charts section
        if 'charts' in report_data:
            html_parts.append('<div class="charts">')
            html_parts.append('<h2>Charts</h2>')
            # Generate inline charts or links
            html_parts.append('</div>')
        
        # Footer
        html_parts.append(self._get_html_footer())
        
        return '\n'.join(html_parts)
    
    def _create_html_cards(self, parsed: Any, **kwargs) -> str:
        """Create HTML cards layout from parsed data"""
        html_parts = []
        
        # Header
        html_parts.append(self._get_html_header(kwargs.get('title', 'Cards')))
        
        # Extract items
        items = self._extract_items(parsed)
        
        # Cards container
        html_parts.append('<div class="cards-container">')
        
        for item in items:
            html_parts.append('<div class="card">')
            
            # Card title
            title = item.get('name', item.get('title', 'Item'))
            html_parts.append(f'<h3>{html.escape(str(title))}</h3>')
            
            # Card content
            for key, value in item.items():
                if key not in ['name', 'title', 'id']:
                    html_parts.append(f'<p><strong>{html.escape(str(key))}:</strong> {html.escape(str(value))}</p>')
            
            html_parts.append('</div>')
        
        html_parts.append('</div>')
        
        # Footer
        html_parts.append(self._get_html_footer())
        
        return '\n'.join(html_parts)
    
    def _create_html_page(self, parsed: Any, **kwargs) -> str:
        """Create a complete HTML page"""
        html_parts = []
        
        # Header
        html_parts.append(self._get_html_header(kwargs.get('title', 'Page')))
        
        # Navigation
        if 'nav' in kwargs:
            html_parts.append('<nav>')
            for link in kwargs['nav']:
                html_parts.append(f'<a href="{link["url"]}">{html.escape(link["text"])}</a>')
            html_parts.append('</nav>')
        
        # Main content
        html_parts.append('<main>')
        
        # Convert parsed data to HTML
        if isinstance(parsed, str):
            html_parts.append(f'<p>{html.escape(parsed)}</p>')
        elif isinstance(parsed, dict):
            for key, value in parsed.items():
                if key != '_metadata':
                    html_parts.append(f'<section>')
                    html_parts.append(f'<h2>{html.escape(str(key))}</h2>')
                    if isinstance(value, (list, tuple)):
                        table_html = self._create_html_table(value, embedded=True)
                        html_parts.append(table_html)
                    else:
                        html_parts.append(f'<p>{html.escape(str(value))}</p>')
                    html_parts.append('</section>')
        
        html_parts.append('</main>')
        
        # Footer
        html_parts.append(self._get_html_footer())
        
        return '\n'.join(html_parts)
    
    def _get_html_header(self, title: str) -> str:
        """Get HTML header with styles"""
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{html.escape(title)}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f4f4f4;
        }}
        h1, h2, h3 {{ color: #2c3e50; }}
        table {{
            width: auto;
            margin: 0 auto;
            border-collapse: collapse;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th, td {{
            padding: 6px 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
            color: #333;
        }}
        td {{
            color: #333 !important;
        }}
        td:first-child,
        td:nth-child(3),
        td:nth-child(4),
        td:nth-child(5),
        th:first-child,
        th:nth-child(3),
        th:nth-child(4),
        th:nth-child(5) {{
            text-align: center;
        }}
        th {{
            background: #3498db;
            color: white;
            font-weight: bold;
        }}
        tbody tr:nth-child(even) {{ background: #f9f9f9; }}
        tbody tr:nth-child(odd) {{ background: white; }}
        tr:hover {{ background: #e8f4f8 !important; }}
        .summary {{
            background: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .card {{
            background: white;
            padding: 20px;
            margin: 10px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            display: inline-block;
            width: 300px;
            vertical-align: top;
        }}
        .cards-container {{
            text-align: center;
        }}
        nav {{
            background: #2c3e50;
            padding: 10px;
            margin: -20px -20px 20px -20px;
        }}
        nav a {{
            color: white;
            text-decoration: none;
            padding: 10px 20px;
            display: inline-block;
        }}
        nav a:hover {{
            background: #34495e;
        }}
    </style>
</head>
<body>
    <h1>{html.escape(title)}</h1>"""
    
    def _get_html_footer(self) -> str:
        """Get HTML footer"""
        return """
    <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #666;">
        <p>Generated by Unified Visualizer • {}</p>
    </footer>
</body>
</html>""".format(datetime.now().strftime('%Y-%m-%d %H:%M'))
    
    def _extract_table_data(self, parsed: Any) -> List:
        """Extract table data from parsed input"""
        if isinstance(parsed, list):
            return parsed
        elif isinstance(parsed, dict):
            if 'items' in parsed:
                return parsed['items']
            elif 'data' in parsed:
                return parsed['data']
            else:
                # Convert dict to list of key-value pairs
                return [{"Key": k, "Value": v} for k, v in parsed.items() if k != '_metadata']
        else:
            return []
    
    def _extract_report_data(self, parsed: Any) -> Dict:
        """Extract report data from parsed input"""
        report_data = {}
        
        if isinstance(parsed, dict):
            # Look for specific report sections
            if 'summary' in parsed:
                report_data['summary'] = parsed['summary']
            if 'content' in parsed:
                report_data['content'] = parsed['content']
            elif 'data' in parsed:
                report_data['content'] = parsed['data']
            elif 'items' in parsed:
                report_data['content'] = parsed['items']
            
            # Extract statistics
            if 'stats' in parsed or 'statistics' in parsed:
                report_data['summary'] = parsed.get('stats', parsed.get('statistics'))
        else:
            report_data['content'] = parsed
        
        return report_data
    
    def _extract_items(self, parsed: Any) -> List[Dict]:
        """Extract items for cards display"""
        if isinstance(parsed, list):
            items = []
            for item in parsed:
                if isinstance(item, dict):
                    items.append(item)
                elif hasattr(item, '__dict__'):
                    items.append(item.__dict__)
                else:
                    items.append({"value": str(item)})
            return items
        elif isinstance(parsed, dict) and 'items' in parsed:
            return self._extract_items(parsed['items'])
        else:
            return [parsed] if parsed else []
    
    def _create_text_report(self, input_data: Any, output: Optional[str], **kwargs) -> str:
        """Create a text report"""
        parsed = InputHandler.parse(input_data, 'report')
        
        text_lines = []
        
        # Title
        title = kwargs.get('title', 'Report')
        text_lines.append('=' * len(title))
        text_lines.append(title)
        text_lines.append('=' * len(title))
        text_lines.append('')
        
        # Content
        if isinstance(parsed, dict):
            for key, value in parsed.items():
                if key != '_metadata':
                    text_lines.append(f"{key}: {value}")
        else:
            text_lines.append(str(parsed))
        
        text_content = '\n'.join(text_lines)
        
        # Save or return
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(text_content)
            logger.info(f"Text report saved to {output}")
            return output
        else:
            return text_content


# ============================================================================
# GLOBAL INSTANCE - The ONE visualizer
# ============================================================================

visualizer = UnifiedVisualizer()


# ============================================================================
# CONVENIENCE FUNCTIONS - Direct access to common visualizations
# ============================================================================

def visualize(input_data: Any, output: Optional[str] = None, **kwargs) -> Any:
    """Visualize ANY data"""
    return visualizer.visualize(input_data, output, **kwargs)


def heatmap(input_data: Any, output: Optional[str] = None, **kwargs) -> Any:
    """Create a heatmap from ANY data"""
    return visualizer.heatmap(input_data, output, **kwargs)


def map(input_data: Any, output: Optional[str] = None, **kwargs) -> Any:
    """Create a map from ANY data"""
    return visualizer.map(input_data, output, **kwargs)


def chart(input_data: Any, output: Optional[str] = None, **kwargs) -> Any:
    """Create a chart from ANY data"""
    return visualizer.chart(input_data, output, **kwargs)


# ============================================================================
# MAIN - Test the visualizer
# ============================================================================

if __name__ == "__main__":
    print("Unified Polymorphic Visualizer")
    print("=" * 60)
    print("\nThis visualizer accepts ANY input format:")
    print("\nExamples:")
    print("  visualize(tournament)")
    print("  visualize([tournaments])")
    print("  visualize({'type': 'skill', 'data': placements})")
    print("  visualize('heatmap of riverside')")
    print("  heatmap(Tournament.all())")
    print("  chart(player_stats)")
    print("  map({'lat': 33.9, 'lng': -117.4})")
    print("\nTesting with tournament data...")
    
    # Test with actual data
    with session_scope() as session:
        # Get some tournaments
        tournaments = session.query(Tournament).filter(
            Tournament.lat.isnot(None)
        ).limit(10).all()
        
        if tournaments:
            print(f"\nFound {len(tournaments)} tournaments with location data")
            
            # Test different visualizations
            print("\n1. Testing heatmap with tournament list...")
            result = heatmap(tournaments, "test_heatmap.html")
            if result:
                print(f"   ✅ Created: {result}")
            
            print("\n2. Testing point map with single tournament...")
            result = map(tournaments[0], "test_point.html")
            if result:
                print(f"   ✅ Created: {result}")
            
            print("\n3. Testing with dictionary input...")
            result = visualize({
                "type": "heatmap",
                "items": tournaments[:5],
                "title": "Top 5 Tournaments"
            }, "test_dict.html")
            if result:
                print(f"   ✅ Created: {result}")
            
            print("\n4. Testing chart generation...")
            stats = {
                "January": 10,
                "February": 15,
                "March": 20
            }
            result = chart({"stats": stats}, "test_chart.png")
            if result:
                print(f"   ✅ Created: {result}")
        else:
            print("No tournament data found - run sync first")
    
    print("\n" + "=" * 60)
    print("✅ Unified Visualizer ready!")
    print("Import with: from visualizer import visualize, heatmap, map, chart")