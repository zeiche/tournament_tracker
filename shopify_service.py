#!/usr/bin/env python3
"""
shopify_service.py - SINGLE SOURCE OF TRUTH for Shopify Operations
This is the ONLY place where Shopify API interactions should happen.
All Shopify publishing, product management, and store operations MUST go through this service.
"""
import os
import json
import requests
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import time

# Use the single database entry point
from database import session_scope, get_session
# Use the single HTML renderer for content generation
from html_renderer import HTMLRenderer
# Use the single log manager
from log_manager import LogManager


class PublishFormat(Enum):
    """Supported publishing formats"""
    HTML = "html"
    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"


class ShopifyResource(Enum):
    """Shopify resource types"""
    PAGE = "pages"
    PRODUCT = "products"
    COLLECTION = "collections"
    BLOG = "blogs"
    ARTICLE = "articles"


@dataclass
class ShopifyConfig:
    """Configuration for Shopify service"""
    store_domain: Optional[str] = None
    access_token: Optional[str] = None
    api_version: str = "2024-01"
    default_resource: ShopifyResource = ShopifyResource.PAGE
    default_format: PublishFormat = PublishFormat.HTML
    rate_limit_delay: float = 0.5  # Seconds between API calls
    max_retries: int = 3
    timeout: int = 30
    
    def __post_init__(self):
        """Load configuration from environment"""
        if not self.store_domain:
            self.store_domain = os.getenv('SHOPIFY_DOMAIN', '')
        if not self.access_token:
            self.access_token = os.getenv('SHOPIFY_ACCESS_TOKEN') or os.getenv('ACCESS_TOKEN')
    
    @property
    def is_enabled(self) -> bool:
        """Check if Shopify service is enabled"""
        return bool(self.store_domain and self.access_token)
    
    @property
    def api_base_url(self) -> str:
        """Get base URL for Shopify API"""
        if not self.store_domain:
            return ""
        return f"https://{self.store_domain}/admin/api/{self.api_version}"


@dataclass
class PublishResult:
    """Result from a Shopify publish operation"""
    success: bool
    resource_id: Optional[str] = None
    resource_url: Optional[str] = None
    error: Optional[str] = None
    response_code: Optional[int] = None
    data_size: int = 0
    publish_time: Optional[datetime] = None


@dataclass
class ShopifyStatistics:
    """Statistics for Shopify operations"""
    total_publishes: int = 0
    successful_publishes: int = 0
    failed_publishes: int = 0
    total_api_calls: int = 0
    api_errors: int = 0
    total_bytes_published: int = 0
    last_publish_time: Optional[datetime] = None
    resources_created: Dict[str, int] = field(default_factory=dict)
    resources_updated: Dict[str, int] = field(default_factory=dict)


class ShopifyService:
    """
    SINGLE SOURCE OF TRUTH for all Shopify operations.
    This is the ONLY service that should interact with Shopify API.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Singleton pattern - only ONE Shopify service"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Optional[ShopifyConfig] = None):
        """Initialize Shopify service (only runs once)"""
        if not self._initialized:
            self.config = config or ShopifyConfig()
            self.logger = LogManager().get_logger('shopify')
            self.stats = ShopifyStatistics()
            self._session = None  # Requests session for connection pooling
            
            # Content generators
            self.html_renderer = HTMLRenderer(theme='light')  # Light theme for Shopify
            
            # Cache for resource IDs
            self._resource_cache = {}
            
            ShopifyService._initialized = True
            
            if self.config.is_enabled:
                self.logger.info("✅ Shopify service initialized (SINGLE SOURCE OF TRUTH)")
                self.logger.info(f"   Store: {self.config.store_domain}")
                self.logger.info(f"   API Version: {self.config.api_version}")
            else:
                self.logger.warning("⚠️  Shopify service disabled (no credentials)")
    
    @property
    def is_enabled(self) -> bool:
        """Check if Shopify service is enabled"""
        return self.config.is_enabled
    
    def _ensure_enabled(self):
        """Ensure Shopify service is enabled"""
        if not self.is_enabled:
            raise RuntimeError(
                "Shopify service is not enabled. "
                "Set SHOPIFY_DOMAIN and SHOPIFY_ACCESS_TOKEN environment variables."
            )
    
    @property
    def session(self) -> requests.Session:
        """Get or create HTTP session for connection pooling"""
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update({
                'X-Shopify-Access-Token': self.config.access_token,
                'Content-Type': 'application/json'
            })
        return self._session
    
    # ========================================================================
    # TOURNAMENT DATA PUBLISHING - Primary use case
    # ========================================================================
    
    def publish_tournament_rankings(self, 
                                   format: Optional[PublishFormat] = None,
                                   resource_id: Optional[str] = None) -> PublishResult:
        """
        Publish tournament rankings to Shopify.
        This is the PRIMARY method for publishing tournament data.
        """
        self._ensure_enabled()
        self.logger.info("Publishing tournament rankings to Shopify")
        
        format = format or self.config.default_format
        
        try:
            # Gather tournament data
            data = self._gather_tournament_data()
            
            if not data:
                return PublishResult(
                    success=False,
                    error="No tournament data available"
                )
            
            # Generate content based on format
            content = self._generate_content(data, format)
            
            # Publish to Shopify
            result = self._publish_content(
                title="Tournament Rankings",
                content=content,
                resource_type=ShopifyResource.PAGE,
                resource_id=resource_id
            )
            
            # Update statistics
            if result.success:
                self.stats.successful_publishes += 1
                self.stats.total_bytes_published += result.data_size
            else:
                self.stats.failed_publishes += 1
            
            self.stats.total_publishes += 1
            self.stats.last_publish_time = datetime.now()
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to publish tournament rankings: {e}")
            return PublishResult(
                success=False,
                error=str(e)
            )
    
    def _gather_tournament_data(self) -> Dict[str, Any]:
        """Gather tournament data from database"""
        with session_scope() as session:
            from tournament_models import Tournament, Organization
            from sqlalchemy import func
            
            # Get organization rankings
            org_rankings = session.query(
                Organization,
                func.count(Tournament.id).label('tournament_count'),
                func.sum(Tournament.num_attendees).label('total_attendance')
            ).outerjoin(
                Tournament,
                Organization.normalized_key == Tournament.normalized_contact
            ).group_by(
                Organization.id
            ).order_by(
                func.sum(Tournament.num_attendees).desc()
            ).limit(50).all()
            
            # Get recent tournaments
            recent = session.query(Tournament).order_by(
                Tournament.start_at.desc()
            ).limit(20).all()
            
            # Get statistics
            stats = {
                'total_tournaments': session.query(Tournament).count(),
                'total_organizations': session.query(Organization).count(),
                'total_attendance': session.query(func.sum(Tournament.num_attendees)).scalar() or 0
            }
            
            return {
                'rankings': [
                    {
                        'rank': i + 1,
                        'organization': org.display_name,
                        'tournaments': count,
                        'attendance': attendance or 0
                    }
                    for i, (org, count, attendance) in enumerate(org_rankings)
                ],
                'recent_tournaments': [
                    {
                        'name': t.name,
                        'date': t.start_at.isoformat() if t.start_at else None,
                        'attendance': t.num_attendees,
                        'location': f"{t.city}, {t.state}" if t.city else "Online"
                    }
                    for t in recent
                ],
                'statistics': stats,
                'generated_at': datetime.now().isoformat()
            }
    
    def _generate_content(self, data: Dict[str, Any], format: PublishFormat) -> str:
        """Generate content in specified format"""
        if format == PublishFormat.HTML:
            return self._generate_html(data)
        elif format == PublishFormat.JSON:
            return json.dumps(data, indent=2, default=str)
        elif format == PublishFormat.MARKDOWN:
            return self._generate_markdown(data)
        elif format == PublishFormat.CSV:
            return self._generate_csv(data)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _generate_html(self, data: Dict[str, Any]) -> str:
        """Generate HTML content"""
        self.html_renderer.start_page(
            "Tournament Rankings",
            f"Fighting Game Community • {data['statistics']['total_tournaments']} Tournaments"
        )
        
        # Add statistics
        self.html_renderer.add_stats_cards([
            {
                'title': 'Total Tournaments',
                'value': str(data['statistics']['total_tournaments']),
                'subtitle': 'Events tracked'
            },
            {
                'title': 'Total Organizations',
                'value': str(data['statistics']['total_organizations']),
                'subtitle': 'Active organizers'
            },
            {
                'title': 'Total Attendance',
                'value': f"{data['statistics']['total_attendance']:,}",
                'subtitle': 'Players total'
            }
        ])
        
        # Add rankings table
        headers = ['Rank', 'Organization', 'Tournaments', 'Total Attendance']
        rows = [
            [r['rank'], r['organization'], r['tournaments'], f"{r['attendance']:,}"]
            for r in data['rankings']
        ]
        
        self.html_renderer.add_section(
            "Organization Rankings",
            self.html_renderer._data_table_component(headers, rows)
        )
        
        # Add recent tournaments
        if data['recent_tournaments']:
            recent_headers = ['Tournament', 'Date', 'Attendance', 'Location']
            recent_rows = [
                [t['name'], t['date'][:10] if t['date'] else 'TBD', t['attendance'], t['location']]
                for t in data['recent_tournaments']
            ]
            
            self.html_renderer.add_section(
                "Recent Tournaments",
                self.html_renderer._data_table_component(recent_headers, recent_rows)
            )
        
        return self.html_renderer.finish_page()
    
    def _generate_markdown(self, data: Dict[str, Any]) -> str:
        """Generate Markdown content"""
        md = "# Tournament Rankings\n\n"
        md += f"Generated: {data['generated_at']}\n\n"
        
        # Statistics
        md += "## Statistics\n\n"
        md += f"- Total Tournaments: {data['statistics']['total_tournaments']}\n"
        md += f"- Total Organizations: {data['statistics']['total_organizations']}\n"
        md += f"- Total Attendance: {data['statistics']['total_attendance']:,}\n\n"
        
        # Rankings
        md += "## Organization Rankings\n\n"
        md += "| Rank | Organization | Tournaments | Attendance |\n"
        md += "|------|-------------|-------------|------------|\n"
        
        for r in data['rankings']:
            md += f"| {r['rank']} | {r['organization']} | {r['tournaments']} | {r['attendance']:,} |\n"
        
        return md
    
    def _generate_csv(self, data: Dict[str, Any]) -> str:
        """Generate CSV content"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(['Rank', 'Organization', 'Tournaments', 'Total Attendance'])
        
        # Write data
        for r in data['rankings']:
            writer.writerow([r['rank'], r['organization'], r['tournaments'], r['attendance']])
        
        return output.getvalue()
    
    # ========================================================================
    # SHOPIFY API OPERATIONS - Low level
    # ========================================================================
    
    def _publish_content(self, 
                        title: str, 
                        content: str,
                        resource_type: ShopifyResource = ShopifyResource.PAGE,
                        resource_id: Optional[str] = None) -> PublishResult:
        """Publish content to Shopify resource"""
        self._ensure_enabled()
        
        try:
            # Prepare API endpoint
            if resource_id:
                # Update existing resource
                url = f"{self.config.api_base_url}/{resource_type.value}/{resource_id}.json"
                method = 'PUT'
            else:
                # Create new resource
                url = f"{self.config.api_base_url}/{resource_type.value}.json"
                method = 'POST'
            
            # Prepare payload based on resource type
            if resource_type == ShopifyResource.PAGE:
                payload = {
                    'page': {
                        'title': title,
                        'body_html': content,
                        'published': True
                    }
                }
            elif resource_type == ShopifyResource.ARTICLE:
                payload = {
                    'article': {
                        'title': title,
                        'content': content,
                        'published': True
                    }
                }
            else:
                payload = {
                    resource_type.value[:-1]: {  # Remove 's' from plural
                        'title': title,
                        'body_html': content
                    }
                }
            
            # Make API request with retries
            response = self._api_request(method, url, payload)
            
            if response and response.status_code in [200, 201]:
                # Parse response
                response_data = response.json()
                resource_key = resource_type.value[:-1]  # Remove 's'
                resource_data = response_data.get(resource_key, {})
                
                # Update statistics
                if resource_id:
                    self.stats.resources_updated[resource_type.value] = \
                        self.stats.resources_updated.get(resource_type.value, 0) + 1
                else:
                    self.stats.resources_created[resource_type.value] = \
                        self.stats.resources_created.get(resource_type.value, 0) + 1
                
                return PublishResult(
                    success=True,
                    resource_id=str(resource_data.get('id')),
                    resource_url=resource_data.get('handle') or resource_data.get('slug'),
                    data_size=len(content.encode('utf-8')),
                    publish_time=datetime.now(),
                    response_code=response.status_code
                )
            else:
                error_msg = f"API request failed: {response.status_code if response else 'No response'}"
                if response:
                    error_msg += f" - {response.text}"
                
                return PublishResult(
                    success=False,
                    error=error_msg,
                    response_code=response.status_code if response else None
                )
                
        except Exception as e:
            self.logger.error(f"Publish failed: {e}")
            return PublishResult(
                success=False,
                error=str(e)
            )
    
    def _api_request(self, method: str, url: str, 
                    data: Optional[Dict] = None) -> Optional[requests.Response]:
        """Make API request with retry logic"""
        self.stats.total_api_calls += 1
        
        for attempt in range(self.config.max_retries):
            try:
                # Rate limiting
                time.sleep(self.config.rate_limit_delay)
                
                # Make request
                response = self.session.request(
                    method=method,
                    url=url,
                    json=data,
                    timeout=self.config.timeout
                )
                
                # Check for rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 2))
                    self.logger.warning(f"Rate limited, waiting {retry_after} seconds")
                    time.sleep(retry_after)
                    continue
                
                return response
                
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"API request failed (attempt {attempt + 1}): {e}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    self.stats.api_errors += 1
                    raise
        
        return None
    
    # ========================================================================
    # RESOURCE MANAGEMENT
    # ========================================================================
    
    def list_resources(self, resource_type: ShopifyResource = ShopifyResource.PAGE) -> List[Dict]:
        """List all resources of a given type"""
        self._ensure_enabled()
        
        try:
            url = f"{self.config.api_base_url}/{resource_type.value}.json"
            response = self._api_request('GET', url)
            
            if response and response.status_code == 200:
                data = response.json()
                return data.get(resource_type.value, [])
            
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to list resources: {e}")
            return []
    
    def get_resource(self, resource_id: str, 
                    resource_type: ShopifyResource = ShopifyResource.PAGE) -> Optional[Dict]:
        """Get a specific resource"""
        self._ensure_enabled()
        
        try:
            url = f"{self.config.api_base_url}/{resource_type.value}/{resource_id}.json"
            response = self._api_request('GET', url)
            
            if response and response.status_code == 200:
                data = response.json()
                resource_key = resource_type.value[:-1]  # Remove 's'
                return data.get(resource_key)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get resource: {e}")
            return None
    
    def delete_resource(self, resource_id: str,
                       resource_type: ShopifyResource = ShopifyResource.PAGE) -> bool:
        """Delete a resource"""
        self._ensure_enabled()
        
        try:
            url = f"{self.config.api_base_url}/{resource_type.value}/{resource_id}.json"
            response = self._api_request('DELETE', url)
            
            return response and response.status_code in [200, 204]
            
        except Exception as e:
            self.logger.error(f"Failed to delete resource: {e}")
            return False
    
    # ========================================================================
    # STATISTICS AND MONITORING
    # ========================================================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get Shopify service statistics"""
        return {
            'enabled': self.is_enabled,
            'config': {
                'store_domain': self.config.store_domain,
                'api_version': self.config.api_version,
                'default_resource': self.config.default_resource.value,
                'default_format': self.config.default_format.value
            },
            'statistics': {
                'total_publishes': self.stats.total_publishes,
                'successful_publishes': self.stats.successful_publishes,
                'failed_publishes': self.stats.failed_publishes,
                'success_rate': (
                    self.stats.successful_publishes / self.stats.total_publishes * 100
                    if self.stats.total_publishes > 0 else 0
                ),
                'total_api_calls': self.stats.total_api_calls,
                'api_errors': self.stats.api_errors,
                'total_bytes_published': self.stats.total_bytes_published,
                'last_publish_time': self.stats.last_publish_time.isoformat() if self.stats.last_publish_time else None,
                'resources_created': self.stats.resources_created,
                'resources_updated': self.stats.resources_updated
            }
        }
    
    def reset_statistics(self):
        """Reset service statistics"""
        self.stats = ShopifyStatistics()
    
    def test_connection(self) -> bool:
        """Test connection to Shopify API"""
        self._ensure_enabled()
        
        try:
            # Try to get shop info
            url = f"{self.config.api_base_url}/shop.json"
            response = self._api_request('GET', url)
            
            if response and response.status_code == 200:
                shop_data = response.json().get('shop', {})
                self.logger.info(f"Connected to shop: {shop_data.get('name')}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False


# ============================================================================
# GLOBAL INSTANCE - The ONE and ONLY Shopify service
# ============================================================================

shopify_service = ShopifyService()


# ============================================================================
# CONVENIENCE FUNCTIONS - These all go through the single service
# ============================================================================

def publish_to_shopify(format: str = "html") -> bool:
    """Publish tournament rankings to Shopify"""
    try:
        format_enum = PublishFormat(format.lower())
    except ValueError:
        print(f"Invalid format: {format}")
        return False
    
    if not shopify_service.is_enabled:
        print("Shopify service is not enabled")
        return False
    
    result = shopify_service.publish_tournament_rankings(format=format_enum)
    
    if result.success:
        print(f"✅ Published to Shopify successfully")
        print(f"   Resource ID: {result.resource_id}")
        print(f"   Size: {result.data_size} bytes")
        return True
    else:
        print(f"❌ Failed to publish: {result.error}")
        return False


def get_shopify_stats() -> Dict[str, Any]:
    """Get Shopify service statistics"""
    return shopify_service.get_statistics()


def is_shopify_enabled() -> bool:
    """Check if Shopify service is enabled"""
    return shopify_service.is_enabled


# ============================================================================
# MAIN - Test the service
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Shopify Service (SINGLE SOURCE OF TRUTH)')
    parser.add_argument('--publish', action='store_true', help='Publish tournament rankings')
    parser.add_argument('--format', choices=['html', 'json', 'markdown', 'csv'], 
                       default='html', help='Publishing format')
    parser.add_argument('--list', choices=['pages', 'products', 'articles'],
                       help='List resources')
    parser.add_argument('--test', action='store_true', help='Test connection')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    
    args = parser.parse_args()
    
    if not shopify_service.is_enabled:
        print("❌ Shopify service is not enabled")
        print("   Set SHOPIFY_DOMAIN and SHOPIFY_ACCESS_TOKEN environment variables")
        sys.exit(1)
    
    if args.test:
        if shopify_service.test_connection():
            print("✅ Connection successful")
        else:
            print("❌ Connection failed")
    
    elif args.list:
        resource_type = ShopifyResource[args.list.upper()]
        resources = shopify_service.list_resources(resource_type)
        print(f"Found {len(resources)} {args.list}:")
        for r in resources:
            print(f"  - {r.get('title', 'Untitled')} (ID: {r.get('id')})")
    
    elif args.publish:
        if publish_to_shopify(args.format):
            print("Publishing completed")
        else:
            print("Publishing failed")
    
    elif args.stats:
        stats = get_shopify_stats()
        print("Shopify Service Statistics:")
        print(f"  Enabled: {stats['enabled']}")
        print(f"  Store: {stats['config']['store_domain']}")
        print(f"\nPublishing Statistics:")
        for key, value in stats['statistics'].items():
            print(f"  {key}: {value}")