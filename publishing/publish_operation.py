"""
publish_operation.py - Shopify Publishing Operation Service
Modern OOP replacement for shopify_publish.py and shopify_query.py
Encapsulates all publishing logic as a stateful operation
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, field
import os
import json
import requests

from database_service import DatabaseService
from log_manager import LogManager
from visualizer import UnifiedVisualizer
from database.tournament_models import Tournament, Organization
# REMOVED: shopify_separated_publisher.py has been deprecated and renamed to .bak
# We ONLY update /pages/attendance via theme template - NEVER create new pages!
# See IMPORTANT_SHOPIFY_RULES.md and ENV_CONFIGURATION.md


@dataclass
class PublishConfig:
    """Configuration for publish operation
    
    ⚠️ ALL configuration comes from .env file:
    - SHOPIFY_ACCESS_TOKEN: The real Shopify token (shpat_...)
    - SHOPIFY_DOMAIN: The store domain
    - Never use ACCESS_TOKEN for Shopify!
    See ENV_CONFIGURATION.md for details.
    """
    shopify_domain: str = ""  # Loaded from SHOPIFY_DOMAIN in .env
    access_token: str = ""  # Loaded from SHOPIFY_ACCESS_TOKEN in .env
    org_page_id: Optional[str] = None  # Page ID for organization rankings
    player_page_id: Optional[str] = None  # Page ID for player rankings
    publish_html: bool = True
    publish_json: bool = False
    include_stats: bool = True
    min_attendance: int = 0
    days_back: int = 90
    use_separated_files: bool = False  # NEVER SET TO TRUE - We only update /pages/attendance, not create new pages!


@dataclass
class PublishStatistics:
    """Statistics for publish operation"""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    organizations_published: int = 0
    tournaments_included: int = 0
    total_attendance: int = 0
    html_size_bytes: int = 0
    json_size_bytes: int = 0
    api_calls: int = 0
    api_errors: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'duration': (self.end_time - self.start_time).total_seconds() if self.end_time else 0,
            'organizations_published': self.organizations_published,
            'tournaments_included': self.tournaments_included,
            'total_attendance': self.total_attendance,
            'output_sizes': {
                'html_bytes': self.html_size_bytes,
                'json_bytes': self.json_size_bytes
            },
            'api': {
                'calls': self.api_calls,
                'errors': self.api_errors
            }
        }


class PublishOperation:
    """Manages publishing tournament data to Shopify and other platforms"""
    
    def __init__(self, config: Optional[PublishConfig] = None):
        """Initialize publish operation"""
        self.config = config or PublishConfig()
        self.db = DatabaseService()
        self.logger = LogManager().get_logger('publish')
        self.renderer = UnifiedVisualizer()  # Unified visualizer for all content
        self.stats = PublishStatistics()
        
        # Load Shopify config from .env file - NEVER hardcode!
        # See ENV_CONFIGURATION.md for token documentation
        if not self.config.shopify_domain:
            self.config.shopify_domain = os.getenv('SHOPIFY_DOMAIN', '')
        if not self.config.access_token:
            # CRITICAL: Use SHOPIFY_ACCESS_TOKEN, not ACCESS_TOKEN!
            self.config.access_token = os.getenv('SHOPIFY_ACCESS_TOKEN', '')
    
    def execute(self) -> Dict[str, Any]:
        """Execute the publish operation"""
        self.logger.info("Starting publish operation")
        self.stats.start_time = datetime.now()
        
        try:
            with self.logger.manager.context("publish_operation"):
                # DEPRECATED - Never use separated files approach
                # We ONLY update /pages/attendance via theme template
                if self.config.use_separated_files:
                    self.logger.error("CRITICAL: use_separated_files is True - this creates NEW pages which is WRONG!")
                    self.logger.error("We must ONLY update /pages/attendance via theme template")
                    self.logger.error("Setting use_separated_files to False and continuing...")
                    self.config.use_separated_files = False
                
                # Original combined HTML approach
                # Gather data
                data = self._gather_tournament_data()
                
                if not data:
                    self.logger.warning("No data to publish")
                    return self._get_result(success=False, error="No data available")
                
                # Generate outputs
                outputs = self._generate_outputs(data)
                
                # Publish to platforms
                publish_results = self._publish_to_platforms(outputs)
                
                self.stats.end_time = datetime.now()
                self._log_summary()
                
                return self._get_result(
                    success=all(r['success'] for r in publish_results),
                    outputs=outputs,
                    publish_results=publish_results
                )
                
        except Exception as e:
            self.logger.error(f"Publish operation failed: {e}")
            self.logger.manager.log_exception(e, "publish_operation")
            self.stats.end_time = datetime.now()
            return self._get_result(success=False, error=str(e))
    
    def _gather_tournament_data(self) -> Dict[str, Any]:
        """Gather tournament data for publishing"""
        self.logger.info("Gathering tournament data")
        
        # Get organizations with statistics
        org_stats = self.db.get_organizations_with_stats()
        
        # Filter and sort
        filtered_orgs = []
        for stat in org_stats:
            org = stat['organization']
            tournament_count = stat['tournament_count']
            total_attendance = stat['total_attendance']
            
            if total_attendance >= self.config.min_attendance:
                filtered_orgs.append({
                    'organization': org,
                    'tournament_count': tournament_count,
                    'total_attendance': total_attendance,
                    'average_attendance': (
                        total_attendance / tournament_count if tournament_count > 0 else 0
                    )
                })
        
        # Get recent tournaments
        recent_tournaments = self.db.get_recent_tournaments(days=self.config.days_back)
        
        # Get player rankings
        player_rankings = self.db.get_player_rankings(limit=50)
        
        # Update statistics
        self.stats.organizations_published = len(filtered_orgs)
        self.stats.tournaments_included = len(recent_tournaments)
        self.stats.total_attendance = sum(o['total_attendance'] for o in filtered_orgs)
        
        self.logger.info(f"Gathered data for {len(filtered_orgs)} organizations, "
                        f"{len(recent_tournaments)} tournaments, "
                        f"{len(player_rankings)} players")
        
        return {
            'organizations': filtered_orgs,
            'recent_tournaments': recent_tournaments,
            'player_rankings': player_rankings,
            'summary': {
                'total_organizations': len(filtered_orgs),
                'total_tournaments': sum(o['tournament_count'] for o in filtered_orgs),
                'total_attendance': self.stats.total_attendance,
                'total_players': len(player_rankings),
                'date_generated': datetime.now().isoformat()
            }
        }
    
    def _generate_outputs(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate output formats (HTML, JSON, etc.)"""
        outputs = {}
        
        if self.config.publish_html:
            # Generate combined tabbed HTML for organization page
            outputs['org_html'] = self._generate_combined_tabbed_html(data)
            # Generate separate player rankings HTML
            outputs['player_html'] = self._generate_player_rankings_html(data)
            self.stats.html_size_bytes = (
                len(outputs['org_html'].encode('utf-8')) + 
                len(outputs['player_html'].encode('utf-8'))
            )
        
        if self.config.publish_json:
            outputs['json'] = self._generate_json_output(data)
            self.stats.json_size_bytes = len(outputs['json'].encode('utf-8'))
        
        return outputs
    
    def _generate_html_output(self, data: Dict[str, Any]) -> str:
        """Generate HTML output for publishing"""
        self.logger.debug("Generating HTML output")
        
        # Build HTML manually since UnifiedVisualizer doesn't have the methods we need
        html_parts = []
        
        # HTML header
        html_parts.append("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tournament Rankings</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        h2 { color: #555; margin-top: 30px; }
        .stats { display: flex; gap: 20px; margin: 20px 0; }
        .stat-card { background: #f5f5f5; padding: 15px; border-radius: 8px; flex: 1; }
        .stat-value { font-size: 24px; font-weight: bold; color: #333; }
        .stat-title { color: #666; margin-bottom: 5px; }
        .stat-subtitle { color: #999; font-size: 12px; margin-top: 5px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th { background: #f0f0f0; padding: 10px; text-align: left; }
        td { padding: 8px; border-bottom: 1px solid #ddd; }
        tr:hover { background: #f9f9f9; }
    </style>
</head>
<body>
""")
        
        # Title
        html_parts.append(f"<h1>Tournament Rankings</h1>")
        html_parts.append(f"<p>Southern California FGC • {data['summary']['total_tournaments']} Tournaments • {data['summary']['total_organizations']} Organizations</p>")
        html_parts.append(f"<p style='color: #666; font-size: 12px;'>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S PST')} | Data version: 2.0</p>")
        
        # Stats cards
        if self.config.include_stats:
            html_parts.append('<div class="stats">')
            html_parts.append(f'''
                <div class="stat-card">
                    <div class="stat-title">Total Organizations</div>
                    <div class="stat-value">{data['summary']['total_organizations']}</div>
                    <div class="stat-subtitle">Active organizers</div>
                </div>
                <div class="stat-card">
                    <div class="stat-title">Total Tournaments</div>
                    <div class="stat-value">{data['summary']['total_tournaments']}</div>
                    <div class="stat-subtitle">Last {self.config.days_back} days</div>
                </div>
                <div class="stat-card">
                    <div class="stat-title">Total Attendance</div>
                    <div class="stat-value">{data['summary']['total_attendance']:,}</div>
                    <div class="stat-subtitle">Unique players</div>
                </div>
            ''')
            html_parts.append('</div>')
        
        # Organization rankings table
        html_parts.append('<h2>Organization Rankings</h2>')
        html_parts.append('<table>')
        html_parts.append('<thead><tr>')
        for header in ['Rank', 'Organization', 'Tournaments', 'Total Attendance', 'Avg Attendance']:
            html_parts.append(f'<th>{header}</th>')
        html_parts.append('</tr></thead>')
        html_parts.append('<tbody>')
        
        for idx, org_data in enumerate(data['organizations'][:50], 1):  # Top 50
            org = org_data['organization']
            html_parts.append('<tr>')
            html_parts.append(f'<td>{idx}</td>')
            html_parts.append(f'<td>{org["display_name"]}</td>')
            html_parts.append(f'<td>{org_data["tournament_count"]}</td>')
            html_parts.append(f'<td>{org_data["total_attendance"]:,}</td>')
            html_parts.append(f'<td>{org_data["average_attendance"]:.1f}</td>')
            html_parts.append('</tr>')
        
        html_parts.append('</tbody></table>')
        
        # Recent tournaments
        if len(data['recent_tournaments']) > 0:
            html_parts.append('<h2>Recent Tournaments</h2>')
            html_parts.append('<table>')
            html_parts.append('<thead><tr>')
            for header in ['Date', 'Tournament', 'Attendees', 'Location']:
                html_parts.append(f'<th>{header}</th>')
            html_parts.append('</tr></thead>')
            html_parts.append('<tbody>')
            
            for tournament in data['recent_tournaments'][:20]:  # Top 20 recent
                html_parts.append('<tr>')
                date_str = tournament['start_date'].strftime('%Y-%m-%d') if tournament['start_date'] else 'TBD'
                html_parts.append(f'<td>{date_str}</td>')
                html_parts.append(f'<td>{tournament["name"]}</td>')
                html_parts.append(f'<td>{tournament["num_attendees"]}</td>')
                location = f"{tournament['city']}, {tournament['state']}" if tournament['city'] else 'Online'
                html_parts.append(f'<td>{location}</td>')
                html_parts.append('</tr>')
            
            html_parts.append('</tbody></table>')
        
        # Footer
        html_parts.append('</body></html>')
        
        return ''.join(html_parts)
    
    def _generate_combined_tabbed_html(self, data: Dict[str, Any]) -> str:
        """Generate combined HTML with tabs for both player and organization rankings"""
        self.logger.debug("Generating combined tabbed HTML")
        
        html_parts = []
        
        # HTML header with tab styles
        total_orgs = data['summary']['total_organizations']
        total_players = len(data['player_rankings'])
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S PST')
        
        html_parts.append(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tournament Rankings</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .update-info {{ color: #666; font-size: 12px; margin: 10px 0; }}
        .tab-nav {{ display: flex; gap: 10px; margin: 20px 0; border-bottom: 2px solid #ddd; }}
        .tab-button {{ padding: 10px 20px; background: #f5f5f5; border: none; cursor: pointer; border-radius: 5px 5px 0 0; }}
        .tab-button:hover {{ background: #e0e0e0; }}
        .tab-button.active {{ background: #333; color: white; }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th {{ background: #f0f0f0; padding: 10px; text-align: left; }}
        td {{ padding: 8px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background: #f9f9f9; }}
    </style>
</head>
<body>
    <h1>Tournament Rankings</h1>
    <p>Southern California FGC • {total_orgs} Organizations • {total_players} Players</p>
    <p class="update-info">Last updated: {timestamp} | Version: 3.0 TABBED</p>
    
    <div class="tab-nav">
        <button class="tab-button active" onclick="showTab('organizations')">Organization Rankings</button>
        <button class="tab-button" onclick="showTab('players')">Player Rankings</button>
    </div>
    
    <div id="organizations" class="tab-content active">
        <h2>Organization Rankings</h2>
        <table>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Organization</th>
                    <th>Tournaments</th>
                    <th>Total Attendance</th>
                    <th>Avg Attendance</th>
                </tr>
            </thead>
            <tbody>
""")
        
        # Add organization rows
        for idx, org_data in enumerate(data['organizations'][:50], 1):
            org = org_data['organization']
            html_parts.append(f"""
                <tr>
                    <td>{idx}</td>
                    <td>{org['display_name']}</td>
                    <td>{org_data['tournament_count']}</td>
                    <td>{org_data['total_attendance']:,}</td>
                    <td>{org_data['average_attendance']:.1f}</td>
                </tr>""")
        
        html_parts.append("""
            </tbody>
        </table>
    </div>
    
    <div id="players" class="tab-content">
        <h2>Player Rankings</h2>
        <table>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Player</th>
                    <th>Points</th>
                    <th>Events</th>
                    <th>1st Places</th>
                    <th>Top 3s</th>
                    <th>Win %</th>
                    <th>Podium %</th>
                </tr>
            </thead>
            <tbody>
""")
        
        # Add player rows
        for idx, player in enumerate(data['player_rankings'][:50], 1):
            html_parts.append(f"""
                <tr>
                    <td>{idx}</td>
                    <td>{player['name']}</td>
                    <td>{player['points']}</td>
                    <td>{player['events']}</td>
                    <td>{player['first_places']}</td>
                    <td>{player['top_3s']}</td>
                    <td>{player['win_rate']:.1f}%</td>
                    <td>{player['podium_rate']:.1f}%</td>
                </tr>""")
        
        html_parts.append("""
            </tbody>
        </table>
    </div>
    
    <script>
        function showTab(tabName) {
            // Hide all tabs
            var tabs = document.querySelectorAll('.tab-content');
            tabs.forEach(function(tab) {
                tab.classList.remove('active');
            });
            
            // Remove active from all buttons
            var buttons = document.querySelectorAll('.tab-button');
            buttons.forEach(function(button) {
                button.classList.remove('active');
            });
            
            // Show selected tab
            document.getElementById(tabName).classList.add('active');
            
            // Mark button as active
            event.target.classList.add('active');
        }
    </script>
</body>
</html>
""")
        
        return ''.join(html_parts)
    
    def _generate_player_rankings_html(self, data: Dict[str, Any]) -> str:
        """Generate HTML for player rankings"""
        self.logger.debug("Generating player rankings HTML")
        
        html_parts = []
        
        # HTML header
        html_parts.append("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Player Rankings</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        h2 { color: #555; margin-top: 30px; }
        .stats { display: flex; gap: 20px; margin: 20px 0; }
        .stat-card { background: #f5f5f5; padding: 15px; border-radius: 8px; flex: 1; }
        .stat-value { font-size: 24px; font-weight: bold; color: #333; }
        .stat-title { color: #666; margin-bottom: 5px; }
        .stat-subtitle { color: #999; font-size: 12px; margin-top: 5px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th { background: #f0f0f0; padding: 10px; text-align: left; }
        td { padding: 8px; border-bottom: 1px solid #ddd; }
        tr:hover { background: #f9f9f9; }
    </style>
</head>
<body>
""")
        
        # Title
        html_parts.append(f"<h1>Player Rankings</h1>")
        html_parts.append(f"<p>Southern California FGC • Top {len(data['player_rankings'])} Players</p>")
        html_parts.append(f"<p style='color: #666; font-size: 12px;'>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S PST')}</p>")
        
        # Player rankings table
        html_parts.append('<h2>Top Players by Points</h2>')
        html_parts.append('<table>')
        html_parts.append('<thead><tr>')
        for header in ['Rank', 'Player', 'Points', 'Events', '1st Places', 'Top 3s', 'Win %', 'Podium %']:
            html_parts.append(f'<th>{header}</th>')
        html_parts.append('</tr></thead>')
        html_parts.append('<tbody>')
        
        for idx, player in enumerate(data['player_rankings'][:50], 1):  # Top 50
            html_parts.append('<tr>')
            html_parts.append(f'<td>{idx}</td>')
            html_parts.append(f'<td>{player["name"]}</td>')
            html_parts.append(f'<td>{player["points"]}</td>')
            html_parts.append(f'<td>{player["events"]}</td>')
            html_parts.append(f'<td>{player["first_places"]}</td>')
            html_parts.append(f'<td>{player["top_3s"]}</td>')
            html_parts.append(f'<td>{player["win_rate"]:.1f}%</td>')
            html_parts.append(f'<td>{player["podium_rate"]:.1f}%</td>')
            html_parts.append('</tr>')
        
        html_parts.append('</tbody></table>')
        
        # Footer
        html_parts.append('</body></html>')
        
        return ''.join(html_parts)
    
    def _generate_json_output(self, data: Dict[str, Any]) -> str:
        """Generate JSON output for API consumption"""
        self.logger.debug("Generating JSON output")
        
        # Serialize organizations
        org_list = []
        for org_data in data['organizations']:
            org = org_data['organization']
            org_list.append({
                'id': org['id'],
                'name': org['display_name'],
                'tournament_count': org_data['tournament_count'],
                'total_attendance': org_data['total_attendance'],
                'average_attendance': org_data['average_attendance']
            })
        
        # Serialize tournaments  
        tournament_list = []
        for tournament in data['recent_tournaments']:
            tournament_list.append({
                'id': tournament['id'],
                'name': tournament['name'],
                'date': tournament['start_date'].isoformat() if tournament['start_date'] else None,
                'attendees': tournament['num_attendees'],
                'location': {
                    'venue': tournament['venue_name'],
                    'city': tournament['city'],
                    'state': tournament['state'],
                    'coordinates': {
                        'lat': tournament['lat'],
                        'lng': tournament['lng']
                    } if tournament['lat'] and tournament['lng'] else None
                }
            })
        
        output = {
            'generated_at': data['summary']['date_generated'],
            'summary': data['summary'],
            'organizations': org_list,
            'recent_tournaments': tournament_list
        }
        
        return json.dumps(output, indent=2)
    
    def _publish_to_platforms(self, outputs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Publish to configured platforms"""
        results = []
        
        # Publish to Shopify if configured
        if self.config.shopify_domain and self.config.access_token:
            shopify_result = self._publish_to_shopify(outputs)
            results.append(shopify_result)
        
        # Could add other platforms here (WordPress, etc.)
        
        return results
    
    def _publish_to_shopify(self, outputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        ⚠️ CRITICAL: We ONLY update /pages/attendance via theme template
        NEVER create new pages! See IMPORTANT_SHOPIFY_RULES.md
        
        This method should update templates/page.attendance.json ONLY
        """
        self.logger.info("Publishing to Shopify /pages/attendance")
        
        # Use combined HTML output for the attendance page
        html_content = outputs.get('org_html') or outputs.get('html', '')
        if not html_content:
            return {
                'platform': 'shopify',
                'success': False,
                'error': 'No HTML content to publish'
            }
        
        try:
            # Import the correct update function from tournament_report
            from tournament_report import find_store_and_theme, update_template
            
            # Find store and theme
            store_url, theme_id, access_token = find_store_and_theme()
            
            # Update the attendance template - this is the ONLY correct way
            # This updates templates/page.attendance.json in the theme
            success = update_template(
                store_url, theme_id, access_token, 
                html_content, 
                {},  # attendance_tracker - not used in new version
                []   # org_names - not used in new version
            )
            
            self.stats.api_calls += 1
            
            if success:
                self.logger.info("Successfully updated /pages/attendance via theme template")
                return {
                    'platform': 'shopify',
                    'success': True,
                    'message': 'Updated /pages/attendance successfully',
                    'url': f"https://{store_url}/pages/attendance"
                }
            else:
                self.stats.api_errors += 1
                self.logger.error("Failed to update /pages/attendance")
                return {
                    'platform': 'shopify',
                    'success': False,
                    'error': 'Failed to update attendance page template'
                }
                
        except requests.exceptions.RequestException as e:
            self.stats.api_errors += 1
            self.logger.error(f"Shopify request failed: {e}")
            
            return {
                'platform': 'shopify',
                'success': False,
                'error': str(e)
            }
    
    def _log_summary(self):
        """Log operation summary"""
        self.logger.info("Publish operation completed")
        self.logger.info(f"  Organizations: {self.stats.organizations_published}")
        self.logger.info(f"  Tournaments: {self.stats.tournaments_included}")
        self.logger.info(f"  Total attendance: {self.stats.total_attendance:,}")
        self.logger.info(f"  HTML size: {self.stats.html_size_bytes:,} bytes")
        if self.stats.json_size_bytes:
            self.logger.info(f"  JSON size: {self.stats.json_size_bytes:,} bytes")
        self.logger.info(f"  API calls: {self.stats.api_calls} "
                        f"(errors: {self.stats.api_errors})")
    
    def _get_result(self, success: bool = True, error: Optional[str] = None, 
                   outputs: Optional[Dict] = None, 
                   publish_results: Optional[List] = None) -> Dict[str, Any]:
        """Get operation result"""
        return {
            'success': success,
            'error': error,
            'statistics': self.stats.to_dict(),
            'outputs': outputs or {},
            'publish_results': publish_results or []
        }
    
    def publish_rankings(self) -> Dict[str, Any]:
        """Convenience method to publish rankings"""
        return self.execute()
    
    def save_local(self, filename: str = "tournament_rankings.html") -> str:
        """Save output locally without publishing"""
        data = self._gather_tournament_data()
        outputs = self._generate_outputs(data)
        
        if 'html' in outputs:
            self.renderer.save_page(outputs['html'], filename)
            self.logger.info(f"Saved output to {filename}")
            return filename
        
        raise ValueError("No HTML output generated")


# Convenience functions for backward compatibility
def publish_to_shopify(**kwargs) -> Dict[str, Any]:
    """Publish to Shopify with custom configuration"""
    config = PublishConfig(**kwargs)
    operation = PublishOperation(config)
    return operation.execute()

def publish_shopify_separated() -> Dict[str, Any]:
    """Publish to Shopify using separated files format"""
    config = PublishConfig(use_separated_files=True)
    operation = PublishOperation(config)
    return operation.execute()

def generate_rankings_html() -> str:
    """Generate rankings HTML without publishing"""
    operation = PublishOperation()
    data = operation._gather_tournament_data()
    outputs = operation._generate_outputs(data)
    return outputs.get('html', '')