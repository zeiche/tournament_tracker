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
from html_renderer import HTMLRenderer
from tournament_models import Tournament, Organization


@dataclass
class PublishConfig:
    """Configuration for publish operation"""
    shopify_domain: str = ""
    access_token: str = ""
    page_id: Optional[str] = None
    publish_html: bool = True
    publish_json: bool = False
    include_stats: bool = True
    min_attendance: int = 0
    days_back: int = 90


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
        self.renderer = HTMLRenderer(theme='light')  # Light theme for Shopify
        self.stats = PublishStatistics()
        
        # Load Shopify config from environment if not provided
        if not self.config.shopify_domain:
            self.config.shopify_domain = os.getenv('SHOPIFY_DOMAIN', '')
        if not self.config.access_token:
            self.config.access_token = os.getenv('SHOPIFY_ACCESS_TOKEN', '')
    
    def execute(self) -> Dict[str, Any]:
        """Execute the publish operation"""
        self.logger.info("Starting publish operation")
        self.stats.start_time = datetime.now()
        
        try:
            with self.logger.manager.context("publish_operation"):
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
        
        # Sort by total attendance
        filtered_orgs.sort(key=lambda x: x['total_attendance'], reverse=True)
        
        # Get recent tournaments
        recent_tournaments = self.db.get_recent_tournaments(days=self.config.days_back)
        
        # Update statistics
        self.stats.organizations_published = len(filtered_orgs)
        self.stats.tournaments_included = len(recent_tournaments)
        self.stats.total_attendance = sum(o['total_attendance'] for o in filtered_orgs)
        
        self.logger.info(f"Gathered data for {len(filtered_orgs)} organizations, "
                        f"{len(recent_tournaments)} tournaments")
        
        return {
            'organizations': filtered_orgs,
            'recent_tournaments': recent_tournaments,
            'summary': {
                'total_organizations': len(filtered_orgs),
                'total_tournaments': sum(o['tournament_count'] for o in filtered_orgs),
                'total_attendance': self.stats.total_attendance,
                'date_generated': datetime.now().isoformat()
            }
        }
    
    def _generate_outputs(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate output formats (HTML, JSON, etc.)"""
        outputs = {}
        
        if self.config.publish_html:
            outputs['html'] = self._generate_html_output(data)
            self.stats.html_size_bytes = len(outputs['html'].encode('utf-8'))
        
        if self.config.publish_json:
            outputs['json'] = self._generate_json_output(data)
            self.stats.json_size_bytes = len(outputs['json'].encode('utf-8'))
        
        return outputs
    
    def _generate_html_output(self, data: Dict[str, Any]) -> str:
        """Generate HTML output for publishing"""
        self.logger.debug("Generating HTML output")
        
        # Start page
        self.renderer.start_page(
            "Tournament Rankings",
            f"Southern California FGC • {data['summary']['total_tournaments']} Tournaments",
            meta_tags={
                'description': 'Fighting game tournament rankings and statistics',
                'generator': 'Tournament Tracker'
            }
        )
        
        # Add summary statistics
        if self.config.include_stats:
            self.renderer.add_stats_cards([
                {
                    'title': 'Total Organizations',
                    'value': str(data['summary']['total_organizations']),
                    'subtitle': 'Active organizers'
                },
                {
                    'title': 'Total Tournaments',
                    'value': str(data['summary']['total_tournaments']),
                    'subtitle': f"Last {self.config.days_back} days"
                },
                {
                    'title': 'Total Attendance',
                    'value': f"{data['summary']['total_attendance']:,}",
                    'subtitle': 'Unique players'
                }
            ])
        
        # Create rankings table
        headers = ['Rank', 'Organization', 'Tournaments', 'Total Attendance', 'Avg Attendance']
        rows = []
        
        for idx, org_data in enumerate(data['organizations'][:50], 1):  # Top 50
            org = org_data['organization']
            rows.append([
                idx,
                org.display_name,
                org_data['tournament_count'],
                f"{org_data['total_attendance']:,}",
                f"{org_data['average_attendance']:.1f}"
            ])
        
        self.renderer.add_section(
            "Organization Rankings",
            self.renderer._data_table_component(headers, rows, table_id="rankings-table")
        )
        
        # Add recent tournaments section
        if len(data['recent_tournaments']) > 0:
            recent_headers = ['Date', 'Tournament', 'Attendees', 'Location']
            recent_rows = []
            
            for tournament in data['recent_tournaments'][:20]:  # Top 20 recent
                recent_rows.append([
                    tournament.start_at.strftime('%Y-%m-%d') if tournament.start_at else 'TBD',
                    tournament.name,
                    tournament.num_attendees,
                    f"{tournament.city}, {tournament.state}" if tournament.city else 'Online'
                ])
            
            self.renderer.add_section(
                "Recent Tournaments",
                self.renderer._data_table_component(
                    recent_headers, recent_rows, table_id="recent-table"
                )
            )
        
        # Finish page
        return self.renderer.finish_page()
    
    def _generate_json_output(self, data: Dict[str, Any]) -> str:
        """Generate JSON output for API consumption"""
        self.logger.debug("Generating JSON output")
        
        # Serialize organizations
        org_list = []
        for org_data in data['organizations']:
            org = org_data['organization']
            org_list.append({
                'id': org.id,
                'name': org.display_name,
                'normalized_key': org.normalized_key,
                'tournament_count': org_data['tournament_count'],
                'total_attendance': org_data['total_attendance'],
                'average_attendance': org_data['average_attendance']
            })
        
        # Serialize tournaments  
        tournament_list = []
        for tournament in data['recent_tournaments']:
            tournament_list.append({
                'id': tournament.id,
                'name': tournament.name,
                'date': tournament.start_at.isoformat() if tournament.start_at else None,
                'attendees': tournament.num_attendees,
                'location': {
                    'venue': tournament.venue_name,
                    'city': tournament.city,
                    'state': tournament.state,
                    'coordinates': {
                        'lat': tournament.lat,
                        'lng': tournament.lng
                    } if tournament.lat and tournament.lng else None
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
        """Publish content to Shopify"""
        self.logger.info("Publishing to Shopify")
        
        if 'html' not in outputs:
            return {
                'platform': 'shopify',
                'success': False,
                'error': 'No HTML output available'
            }
        
        try:
            # Shopify Admin API endpoint
            if self.config.page_id:
                url = f"https://{self.config.shopify_domain}/admin/api/2024-01/pages/{self.config.page_id}.json"
                method = 'PUT'
            else:
                url = f"https://{self.config.shopify_domain}/admin/api/2024-01/pages.json"
                method = 'POST'
            
            headers = {
                'X-Shopify-Access-Token': self.config.access_token,
                'Content-Type': 'application/json'
            }
            
            page_data = {
                'page': {
                    'title': 'Tournament Rankings',
                    'body_html': outputs['html'],
                    'published': True
                }
            }
            
            response = requests.request(
                method, url, 
                headers=headers,
                json=page_data,
                timeout=30
            )
            
            self.stats.api_calls += 1
            
            if response.status_code in [200, 201]:
                page_id = response.json().get('page', {}).get('id')
                self.logger.info(f"Successfully published to Shopify (page_id: {page_id})")
                
                return {
                    'platform': 'shopify',
                    'success': True,
                    'page_id': page_id,
                    'url': f"https://{self.config.shopify_domain}/pages/tournament-rankings"
                }
            else:
                self.stats.api_errors += 1
                error_msg = f"Shopify API error: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                
                return {
                    'platform': 'shopify',
                    'success': False,
                    'error': error_msg
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

def generate_rankings_html() -> str:
    """Generate rankings HTML without publishing"""
    operation = PublishOperation()
    data = operation._gather_tournament_data()
    outputs = operation._generate_outputs(data)
    return outputs.get('html', '')