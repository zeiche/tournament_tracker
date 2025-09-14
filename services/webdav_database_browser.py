#!/usr/bin/env python3
"""
WebDAV Database Browser - Expose database models as virtual file system
Maps database objects to virtual folders with their built-in visualizations.

Structure:
/tournaments/
  /tournament_123/
    data.json           <- Raw tournament data
    analytics.html      <- Performance dashboard  
    heatmap_data.json   <- Geographic visualization data
    relationships.txt   <- Related objects
/players/
  /player_west/
    data.json           <- Raw player data
    stats.html          <- Built-in analytics
    performance.json    <- Win rates, consistency
/organizations/
  /org_runback/
    data.json           <- Raw org data
    tournaments.html    <- Tournament list
    contacts.json       <- Contact information
"""
import sys
import os
import json
import io
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

# Add path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# CRITICAL: Enforce go.py execution - this module CANNOT be run directly
from polymorphic_core.execution_guard import require_go_py
require_go_py("services.webdav_database_browser")

from wsgidav.wsgidav_app import WsgiDAVApp
from wsgidav.fs_dav_provider import FilesystemProvider
from wsgidav import util
from wsgidav.dav_provider import DAVProvider, _DAVResource, DAVCollection
from wsgidav.dav_error import DAVError, HTTP_NOT_FOUND, HTTP_FORBIDDEN

# Import database and models
from utils.database import get_session
from database.tournament_models import Tournament, Player, Organization

# Bonjour system imports for /bonjour filesystem
import time
import psutil
from polymorphic_core.local_bonjour import local_announcer
from polymorphic_core.real_bonjour import announcer as real_announcer

# Logging setup for Bonjour filesystem
from polymorphic_core.service_locator import get_service


class DatabaseResource(_DAVResource):
    """Represents a virtual file backed by database object intelligence"""
    
    def __init__(self, path, environ, obj_data, content_func):
        super().__init__(path, False, environ)
        self.obj_data = obj_data
        self.content_func = content_func
        self._content = None
    
    def get_content_length(self):
        if self._content is None:
            self._content = self.content_func(self.obj_data)
        return len(self._content.encode('utf-8'))
    
    def get_content_type(self):
        if self.path.endswith('.json'):
            return "application/json"
        elif self.path.endswith('.html'):
            return "text/html"
        elif self.path.endswith('.txt'):
            return "text/plain"
        return "text/plain"
    
    def get_creation_date(self):
        return util.get_rfc1123_time()
    
    def get_last_modified(self):
        return util.get_rfc1123_time()
    
    def get_content(self):
        if self._content is None:
            self._content = self.content_func(self.obj_data)
        return io.BytesIO(self._content.encode('utf-8'))
    
    def support_ranges(self):
        return False


class DatabaseCollection(DAVCollection):
    """Represents a virtual directory backed by database queries"""

    def __init__(self, path, environ, model_class, get_objects_func):
        super().__init__(path, environ)
        self.model_class = model_class
        self.get_objects_func = get_objects_func
        self._logger = None

    @property
    def logger(self):
        if self._logger is None:
            try:
                self._logger = get_service("logger", prefer_network=False)
            except Exception:
                import logging
                self._logger = logging.getLogger(__name__)
        return self._logger
    
    def get_member_names(self):
        """Return list of child names (object IDs/names)"""
        try:
            objects = self.get_objects_func()
            names = []
            for obj in objects:
                if hasattr(obj, 'id'):
                    names.append(f"{self.model_class.__name__.lower()}_{obj.id}")
                elif hasattr(obj, 'name'):
                    clean_name = "".join(c for c in obj.name if c.isalnum() or c in '-_')
                    names.append(f"{self.model_class.__name__.lower()}_{clean_name}")
            return names
        except Exception as e:
            self.logger.error(f"Error getting database collection member names: {e}")
            return []
    
    def get_member(self, name):
        """Return child resource/collection by name"""
        try:
            # Extract object ID from name
            if '_' in name:
                obj_id = name.split('_', 1)[1]
                
                objects = self.get_objects_func()
                target_obj = None
                
                for obj in objects:
                    if hasattr(obj, 'id') and str(obj.id) == obj_id:
                        target_obj = obj
                        break
                    elif hasattr(obj, 'name'):
                        clean_name = "".join(c for c in obj.name if c.isalnum() or c in '-_')
                        if clean_name == obj_id:
                            target_obj = obj
                            break
                
                if target_obj:
                    return ObjectCollection(
                        util.join_uri(self.path, name),
                        self.environ,
                        target_obj
                    )
            
            return None
        except Exception as e:
            self.logger.error(f"Error getting database collection member {name}: {e}")
            return None


class ObjectCollection(DAVCollection):
    """Represents a single database object as a virtual directory with visualization files"""
    
    def __init__(self, path, environ, db_object):
        super().__init__(path, environ)
        self.db_object = db_object
    
    def get_member_names(self):
        """Return available views for this object"""
        base_files = ['data.json']
        
        # Add model-specific visualization files
        if isinstance(self.db_object, Tournament):
            base_files.extend([
                'analytics.html',
                'heatmap_data.json',
                'location_info.txt',
                'relationships.txt'
            ])
        elif isinstance(self.db_object, Player):
            base_files.extend([
                'stats.html', 
                'performance.json',
                'tournaments.txt'
            ])
        elif isinstance(self.db_object, Organization):
            base_files.extend([
                'tournaments.html',
                'contacts.json',
                'summary.txt'
            ])
        
        return base_files
    
    def get_member(self, name):
        """Return virtual file resource"""
        content_func = self._get_content_function(name)
        if content_func:
            return DatabaseResource(
                util.join_uri(self.path, name),
                self.environ,
                self.db_object,
                content_func
            )
        return None
    
    def _get_content_function(self, filename):
        """Return function to generate content for virtual file"""
        
        if filename == 'data.json':
            return self._generate_raw_data
        
        # Tournament-specific files
        elif isinstance(self.db_object, Tournament):
            if filename == 'analytics.html':
                return self._generate_tournament_analytics
            elif filename == 'heatmap_data.json':
                return self._generate_heatmap_data
            elif filename == 'location_info.txt':
                return self._generate_location_info
            elif filename == 'relationships.txt':
                return self._generate_tournament_relationships
                
        # Player-specific files  
        elif isinstance(self.db_object, Player):
            if filename == 'stats.html':
                return self._generate_player_stats
            elif filename == 'performance.json':
                return self._generate_player_performance
            elif filename == 'tournaments.txt':
                return self._generate_player_tournaments
                
        # Organization-specific files
        elif isinstance(self.db_object, Organization):
            if filename == 'tournaments.html':
                return self._generate_org_tournaments
            elif filename == 'contacts.json':
                return self._generate_org_contacts
            elif filename == 'summary.txt':
                return self._generate_org_summary
        
        return None
    
    def _generate_raw_data(self, obj):
        """Generate raw JSON data for object"""
        data = {}
        for column in obj.__table__.columns:
            value = getattr(obj, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            data[column.name] = value
        return json.dumps(data, indent=2)
    
    def _generate_tournament_analytics(self, tournament):
        """Generate analytics HTML using built-in tournament methods"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Tournament Analytics: {tournament.name or 'Unnamed'}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .metric {{ margin: 10px 0; padding: 10px; background: #f5f5f5; }}
        .value {{ font-weight: bold; color: #2196F3; }}
    </style>
</head>
<body>
    <h1>Tournament Analytics</h1>
    <h2>{tournament.name or 'Unnamed Tournament'}</h2>
    
    <div class="metric">
        <strong>Tournament ID:</strong> <span class="value">{tournament.id}</span>
    </div>
    
    <div class="metric">
        <strong>Attendees:</strong> <span class="value">{tournament.num_attendees or 'Unknown'}</span>
    </div>
    
    <div class="metric">
        <strong>Is Major Event:</strong> <span class="value">{'Yes' if hasattr(tournament, 'is_major') and tournament.is_major() else 'No'}</span>
    </div>
    
    <div class="metric">
        <strong>Has Location:</strong> <span class="value">{'Yes' if hasattr(tournament, 'has_location') and tournament.has_location else 'No'}</span>
    </div>
    
    <div class="metric">
        <strong>Date:</strong> <span class="value">{tournament.date or 'Unknown'}</span>
    </div>
    
    <div class="metric">
        <strong>Days Ago:</strong> <span class="value">{getattr(tournament, 'days_ago', 'Unknown')}</span>
    </div>
</body>
</html>"""
        return html
    
    def _generate_heatmap_data(self, tournament):
        """Generate heatmap data using built-in methods"""
        data = {
            'tournament_id': tournament.id,
            'name': tournament.name,
            'coordinates': None,
            'heatmap_weight': 0
        }
        
        if hasattr(tournament, 'coordinates') and tournament.coordinates:
            data['coordinates'] = tournament.coordinates
            
        if hasattr(tournament, 'get_heatmap_weight'):
            try:
                data['heatmap_weight'] = tournament.get_heatmap_weight()
            except:
                data['heatmap_weight'] = 1
                
        return json.dumps(data, indent=2)
    
    def _generate_location_info(self, tournament):
        """Generate location information"""
        info = f"Tournament Location Information\n"
        info += f"===============================\n\n"
        info += f"Tournament: {tournament.name or 'Unnamed'}\n"
        info += f"ID: {tournament.id}\n\n"
        
        if hasattr(tournament, 'lat') and tournament.lat:
            info += f"Latitude: {tournament.lat}\n"
            info += f"Longitude: {tournament.lng}\n"
            
            if hasattr(tournament, 'coordinates'):
                coords = tournament.coordinates
                if coords:
                    info += f"Coordinates: {coords}\n"
        else:
            info += "No location data available\n"
            
        return info
    
    def _generate_tournament_relationships(self, tournament):
        """Generate relationship information"""
        info = f"Tournament Relationships\n"
        info += f"========================\n\n"
        info += f"Tournament: {tournament.name or 'Unnamed'}\n\n"
        
        # Add organization info if available
        if hasattr(tournament, 'organization_id') and tournament.organization_id:
            info += f"Organization ID: {tournament.organization_id}\n"
            
        # Add any other relationships we can find
        info += f"Database relationships would be enumerated here...\n"
        
        return info
    
    def _generate_player_stats(self, player):
        """Generate player statistics HTML"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Player Stats: {player.name or 'Unnamed'}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .metric {{ margin: 10px 0; padding: 10px; background: #f5f5f5; }}
        .value {{ font-weight: bold; color: #4CAF50; }}
    </style>
</head>
<body>
    <h1>Player Statistics</h1>
    <h2>{player.name or 'Unnamed Player'}</h2>
    
    <div class="metric">
        <strong>Player ID:</strong> <span class="value">{player.id}</span>
    </div>
    
    <div class="metric">
        <strong>Win Rate:</strong> <span class="value">{getattr(player, 'win_rate', 'N/A')}</span>
    </div>
    
    <div class="metric">
        <strong>Podium Rate:</strong> <span class="value">{getattr(player, 'podium_rate', 'N/A')}</span>
    </div>
    
    <div class="metric">
        <strong>Points Per Event:</strong> <span class="value">{getattr(player, 'points_per_event', 'N/A')}</span>
    </div>
</body>
</html>"""
        return html
    
    def _generate_player_performance(self, player):
        """Generate player performance JSON"""
        data = {
            'player_id': player.id,
            'name': player.name,
            'performance_metrics': {}
        }
        
        # Add built-in performance metrics if available
        for attr in ['win_rate', 'podium_rate', 'points_per_event', 'consistency_score']:
            if hasattr(player, attr):
                try:
                    data['performance_metrics'][attr] = getattr(player, attr)
                except:
                    data['performance_metrics'][attr] = None
                    
        return json.dumps(data, indent=2)
    
    def _generate_player_tournaments(self, player):
        """Generate player tournament list"""
        info = f"Player Tournament History\n"
        info += f"=========================\n\n"
        info += f"Player: {player.name or 'Unnamed'}\n\n"
        info += f"Tournament relationships would be listed here...\n"
        return info
    
    def _generate_org_tournaments(self, org):
        """Generate organization tournaments HTML"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Organization: {org.name or 'Unnamed'}</title>
</head>
<body>
    <h1>Organization Tournaments</h1>
    <h2>{org.name or 'Unnamed Organization'}</h2>
    <p>Tournament list would be generated here using built-in methods...</p>
</body>
</html>"""
        return html
    
    def _generate_org_contacts(self, org):
        """Generate organization contacts JSON"""
        data = {
            'organization_id': org.id,
            'name': org.name,
            'contacts': []
        }
        
        # Add contact information if available
        if hasattr(org, 'get_contacts'):
            try:
                contacts = org.get_contacts()
                data['contacts'] = contacts
            except:
                pass
                
        return json.dumps(data, indent=2)
    
    def _generate_org_summary(self, org):
        """Generate organization summary"""
        info = f"Organization Summary\n"
        info += f"===================\n\n"
        info += f"Name: {org.name or 'Unnamed'}\n"
        info += f"ID: {org.id}\n\n"
        info += f"Summary information would be generated here...\n"
        return info


class DatabaseDAVProvider(DAVProvider):
    """WebDAV provider that maps database to virtual file system"""
    
    def __init__(self):
        super().__init__()
        
    def get_resource_inst(self, path, environ):
        """Map URL path to database resource"""
        
        # Root directory
        if path == "/":
            return RootCollection("/", environ)
            
        # Main collection directories
        elif path in ["/tournaments", "/tournaments/"]:
            return DatabaseCollection(
                "/tournaments/",
                environ, 
                Tournament,
                self._get_tournaments
            )
        elif path in ["/players", "/players/"]:
            return DatabaseCollection(
                "/players/",
                environ,
                Player, 
                self._get_players
            )
        elif path in ["/organizations", "/organizations/"]:
            return DatabaseCollection(
                "/organizations/",
                environ,
                Organization,
                self._get_organizations
            )
        elif path in ["/bonjour", "/bonjour/"]:
            return BonjourRootCollection("/bonjour/", environ)

        # Bonjour-specific paths
        elif path.startswith("/bonjour/"):
            return self._get_bonjour_resource(path, environ)

        # Object-specific paths
        elif path.startswith("/tournaments/"):
            return self._get_tournament_resource(path, environ)
        elif path.startswith("/players/"):
            return self._get_player_resource(path, environ)
        elif path.startswith("/organizations/"):
            return self._get_organization_resource(path, environ)
            
        return None
    
    def _get_tournaments(self):
        """Get all tournaments from database"""
        with get_session() as session:
            return session.query(Tournament).limit(50).all()
    
    def _get_players(self):
        """Get all players from database"""
        with get_session() as session:
            return session.query(Player).limit(50).all()
    
    def _get_organizations(self):
        """Get all organizations from database"""
        with get_session() as session:
            return session.query(Organization).limit(50).all()
    
    def _get_tournament_resource(self, path, environ):
        """Get tournament-specific resource"""
        path_parts = path.strip('/').split('/')
        if len(path_parts) >= 2:
            tournament_name = path_parts[1]
            
            # If it's a directory request
            if len(path_parts) == 2 or path.endswith('/'):
                with get_session() as session:
                    # Extract ID from tournament name
                    if '_' in tournament_name:
                        obj_id = tournament_name.split('_', 1)[1]
                        tournament = session.query(Tournament).filter(Tournament.id == obj_id).first()
                        if tournament:
                            return ObjectCollection(f"/tournaments/{tournament_name}/", environ, tournament)
            
            # If it's a file request within tournament directory
            elif len(path_parts) == 3:
                tournament_name = path_parts[1]
                filename = path_parts[2]
                
                with get_session() as session:
                    if '_' in tournament_name:
                        obj_id = tournament_name.split('_', 1)[1]
                        tournament = session.query(Tournament).filter(Tournament.id == obj_id).first()
                        if tournament:
                            obj_collection = ObjectCollection(f"/tournaments/{tournament_name}/", environ, tournament)
                            return obj_collection.get_member(filename)
        
        return None
    
    def _get_player_resource(self, path, environ):
        """Get player-specific resource"""
        # Similar implementation for players
        path_parts = path.strip('/').split('/')
        if len(path_parts) >= 2:
            player_name = path_parts[1]
            
            if len(path_parts) == 2 or path.endswith('/'):
                with get_session() as session:
                    if '_' in player_name:
                        obj_id = player_name.split('_', 1)[1]
                        player = session.query(Player).filter(Player.id == obj_id).first()
                        if player:
                            return ObjectCollection(f"/players/{player_name}/", environ, player)
        
        return None
    
    def _get_organization_resource(self, path, environ):
        """Get organization-specific resource"""
        # Similar implementation for organizations
        path_parts = path.strip('/').split('/')
        if len(path_parts) >= 2:
            org_name = path_parts[1]
            
            if len(path_parts) == 2 or path.endswith('/'):
                with get_session() as session:
                    if '_' in org_name:
                        obj_id = org_name.split('_', 1)[1]
                        org = session.query(Organization).filter(Organization.id == obj_id).first()
                        if org:
                            return ObjectCollection(f"/organizations/{org_name}/", environ, org)
        
        return None

    def _get_bonjour_resource(self, path, environ):
        """Get Bonjour-specific resource based on path hierarchy"""
        path_parts = [p for p in path.strip('/').split('/') if p]  # Filter empty parts

        if len(path_parts) < 2:  # /bonjour/ should be handled by BonjourRootCollection
            return None

        category = path_parts[1]  # services, ports, capabilities, switches, stats

        # Category collection (e.g., /bonjour/services/)
        if len(path_parts) == 2 or path.endswith('/'):
            return BonjourCategoryCollection(
                f"/bonjour/{category}/",
                environ,
                category
            )

        # Specific resource within category (e.g., /bonjour/services/WebDAV/)
        elif len(path_parts) == 3:
            resource_name = path_parts[2]

            if category == 'services':
                services = local_announcer.list_services()
                if resource_name in services:
                    return BonjourServiceCollection(
                        f"/bonjour/services/{resource_name}/",
                        environ,
                        resource_name,
                        services[resource_name]
                    )
            elif category == 'ports':
                try:
                    port = int(resource_name)
                    return BonjourPortCollection(
                        f"/bonjour/ports/{resource_name}/",
                        environ,
                        port
                    )
                except ValueError:
                    pass
            elif category == 'capabilities':
                return BonjourCapabilityCollection(
                    f"/bonjour/capabilities/{resource_name}/",
                    environ,
                    resource_name
                )
            elif category == 'stats':
                return BonjourResource(
                    f"/bonjour/stats/{resource_name}",
                    environ,
                    {'filename': resource_name},
                    self._generate_stats_content
                )

        # Deep drill-down (e.g., /bonjour/services/WebDAV/info.json)
        elif len(path_parts) == 4:
            resource_name = path_parts[2]
            file_name = path_parts[3]

            if category == 'services':
                services = local_announcer.list_services()
                if resource_name in services:
                    service_collection = BonjourServiceCollection(
                        f"/bonjour/services/{resource_name}/",
                        environ,
                        resource_name,
                        services[resource_name]
                    )
                    return service_collection.get_member(file_name)

        return None

    def _generate_stats_content(self, data):
        """Generate statistics content for Bonjour stats files"""
        filename = data['filename']
        if filename == 'service_count.txt':
            count = len(local_announcer.list_services())
            return f"Total services announced: {count}\n"
        elif filename == 'uptime.txt':
            try:
                import psutil
                boot_time = psutil.boot_time()
                uptime = time.time() - boot_time
                return f"System uptime: {uptime/3600:.1f} hours\n"
            except:
                return "System uptime: unavailable\n"
        elif filename == 'memory_usage.txt':
            try:
                import psutil
                mem = psutil.virtual_memory()
                return f"Memory usage: {mem.percent}%\n" \
                       f"Total: {mem.total/(1024**3):.1f} GB\n" \
                       f"Available: {mem.available/(1024**3):.1f} GB\n"
            except:
                return "Memory usage: unavailable\n"
        elif filename == 'system_info.txt':
            try:
                import psutil
                cpu_count = psutil.cpu_count()
                load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else ('N/A', 'N/A', 'N/A')
                return f"CPU cores: {cpu_count}\n" \
                       f"Load average: {load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}\n" \
                       f"Python PID: {os.getpid()}\n"
            except:
                return "System info: unavailable\n"
        return "Unknown stats file"


class BonjourBaseCollection(DAVCollection):
    """Base class for Bonjour collections with logging support"""

    def __init__(self, path, environ):
        super().__init__(path, environ)
        self._logger = None

    @property
    def logger(self):
        if self._logger is None:
            try:
                self._logger = get_service("logger", prefer_network=False)
            except Exception:
                # Fallback if logger service not available
                import logging
                self._logger = logging.getLogger(__name__)
        return self._logger


class BonjourServiceCollection(BonjourBaseCollection):
    """Collection showing individual service details"""

    def __init__(self, path, environ, service_name, service_data):
        super().__init__(path, environ)
        self.service_name = service_name
        self.service_data = service_data

    def get_member_names(self):
        return ['info.json', 'capabilities.txt', 'examples.txt', 'status.txt']

    def get_member(self, name):
        if name == 'info.json':
            return BonjourResource(
                util.join_uri(self.path, name),
                self.environ,
                self.service_data,
                lambda data: json.dumps(data, indent=2, default=str)
            )
        elif name == 'capabilities.txt':
            return BonjourResource(
                util.join_uri(self.path, name),
                self.environ,
                self.service_data,
                lambda data: '\n'.join(data.get('capabilities', []))
            )
        elif name == 'examples.txt':
            return BonjourResource(
                util.join_uri(self.path, name),
                self.environ,
                self.service_data,
                lambda data: '\n'.join(data.get('examples', []))
            )
        elif name == 'status.txt':
            return BonjourResource(
                util.join_uri(self.path, name),
                self.environ,
                self.service_data,
                self._generate_status
            )
        return None

    def _generate_status(self, data):
        now = time.time()
        announced_at = data.get('announced_at', now)
        uptime = now - announced_at
        return f"Service: {self.service_name}\n" \
               f"Uptime: {uptime:.1f} seconds\n" \
               f"PID: {data.get('pid', 'unknown')}\n" \
               f"Announced: {time.ctime(announced_at)}\n"


class BonjourPortCollection(BonjourBaseCollection):
    """Collection showing services bound to a specific port"""

    def __init__(self, path, environ, port):
        super().__init__(path, environ)
        self.port = port

    def get_member_names(self):
        services = []
        all_services = local_announcer.list_services()

        # Find services that mention this port
        for name, data in all_services.items():
            capabilities = data.get('capabilities', [])
            if any(str(self.port) in str(cap) for cap in capabilities):
                services.append(name.replace(' ', '_').replace('/', '_'))

        # Add system info
        services.extend(['port_info.txt', 'processes.txt'])
        return services

    def get_member(self, name):
        if name == 'port_info.txt':
            return BonjourResource(
                util.join_uri(self.path, name),
                self.environ,
                {'port': self.port},
                self._generate_port_info
            )
        elif name == 'processes.txt':
            return BonjourResource(
                util.join_uri(self.path, name),
                self.environ,
                {'port': self.port},
                self._generate_processes
            )
        else:
            # Find the service by name
            all_services = local_announcer.list_services()
            for service_name, data in all_services.items():
                clean_name = service_name.replace(' ', '_').replace('/', '_')
                if clean_name == name:
                    return BonjourServiceCollection(
                        util.join_uri(self.path, name),
                        self.environ,
                        service_name,
                        data
                    )
        return None

    def _generate_port_info(self, data):
        port = data['port']
        try:
            # Check if port is in use
            connections = psutil.net_connections()
            port_info = []
            for conn in connections:
                if hasattr(conn, 'laddr') and conn.laddr and conn.laddr.port == port:
                    port_info.append(f"Protocol: {conn.type.name if hasattr(conn.type, 'name') else conn.type}")
                    port_info.append(f"Status: {conn.status}")
                    port_info.append(f"PID: {conn.pid}")

            if port_info:
                return f"Port {port} Status:\n" + '\n'.join(port_info)
            else:
                return f"Port {port} is not currently in use by system processes"
        except:
            return f"Port {port} - Unable to check system status"

    def _generate_processes(self, data):
        port = data['port']
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if str(port) in cmdline:
                        processes.append(f"PID {proc.info['pid']}: {proc.info['name']} - {cmdline}")
                except:
                    continue

            if processes:
                return f"Processes using port {port}:\n" + '\n'.join(processes)
            else:
                return f"No processes found explicitly using port {port}"
        except:
            return f"Unable to scan processes for port {port}"


class BonjourCapabilityCollection(BonjourBaseCollection):
    """Collection showing services that provide a specific capability"""

    def __init__(self, path, environ, capability):
        super().__init__(path, environ)
        self.capability = capability

    def get_member_names(self):
        services = []
        all_services = local_announcer.list_services()

        for name, data in all_services.items():
            capabilities = data.get('capabilities', [])
            if any(self.capability.lower() in str(cap).lower() for cap in capabilities):
                services.append(name.replace(' ', '_').replace('/', '_'))

        return services

    def get_member(self, name):
        all_services = local_announcer.list_services()
        for service_name, data in all_services.items():
            clean_name = service_name.replace(' ', '_').replace('/', '_')
            if clean_name == name:
                return BonjourServiceCollection(
                    util.join_uri(self.path, name),
                    self.environ,
                    service_name,
                    data
                )
        return None


class BonjourCategoryCollection(BonjourBaseCollection):
    """Collection showing different Bonjour categories (services, ports, capabilities, etc.)"""

    def __init__(self, path, environ, category):
        super().__init__(path, environ)
        self.category = category

    def get_member_names(self):
        if self.category == 'services':
            return list(local_announcer.list_services().keys())
        elif self.category == 'ports':
            # Extract ports from service capabilities
            ports = set()
            all_services = local_announcer.list_services()
            for data in all_services.values():
                capabilities = data.get('capabilities', [])
                for cap in capabilities:
                    # Look for port numbers in capabilities
                    import re
                    port_matches = re.findall(r'\b(\d{4,5})\b', str(cap))
                    for port in port_matches:
                        if 1024 <= int(port) <= 65535:  # Valid port range
                            ports.add(port)
            return sorted(ports)
        elif self.category == 'capabilities':
            # Extract unique capabilities
            capabilities = set()
            all_services = local_announcer.list_services()
            for data in all_services.values():
                for cap in data.get('capabilities', []):
                    # Clean capability name
                    clean_cap = str(cap).lower().replace(' ', '_').replace('/', '_')
                    capabilities.add(clean_cap)
            return sorted(capabilities)
        elif self.category == 'switches':
            # Extract go.py switches from service names
            switches = set()
            all_services = local_announcer.list_services()
            for name in all_services.keys():
                if 'GoSwitch' in name or 'switch' in name.lower():
                    switch_name = name.replace('GoSwitch__', '').replace('GoSwitch', '')
                    if switch_name:
                        switches.add(switch_name)
            return sorted(switches)
        elif self.category == 'stats':
            return ['service_count.txt', 'uptime.txt', 'memory_usage.txt', 'system_info.txt']
        return []

    def get_member(self, name):
        if self.category == 'services':
            services = local_announcer.list_services()
            if name in services:
                return BonjourServiceCollection(
                    util.join_uri(self.path, name),
                    self.environ,
                    name,
                    services[name]
                )
        elif self.category == 'ports':
            try:
                port = int(name)
                return BonjourPortCollection(
                    util.join_uri(self.path, name),
                    self.environ,
                    port
                )
            except ValueError:
                pass
        elif self.category == 'capabilities':
            return BonjourCapabilityCollection(
                util.join_uri(self.path, name),
                self.environ,
                name
            )
        elif self.category == 'switches':
            # Find the switch service
            all_services = local_announcer.list_services()
            for service_name, data in all_services.items():
                if f'__{name}' in service_name or name in service_name:
                    return BonjourServiceCollection(
                        util.join_uri(self.path, name),
                        self.environ,
                        service_name,
                        data
                    )
        elif self.category == 'stats':
            return BonjourResource(
                util.join_uri(self.path, name),
                self.environ,
                {'filename': name},
                self._generate_stats
            )
        return None

    def _generate_stats(self, data):
        filename = data['filename']
        if filename == 'service_count.txt':
            count = len(local_announcer.list_services())
            return f"Total services announced: {count}\n"
        elif filename == 'uptime.txt':
            try:
                boot_time = psutil.boot_time()
                uptime = time.time() - boot_time
                return f"System uptime: {uptime/3600:.1f} hours\n"
            except:
                return "System uptime: unavailable\n"
        elif filename == 'memory_usage.txt':
            try:
                mem = psutil.virtual_memory()
                return f"Memory usage: {mem.percent}%\n" \
                       f"Total: {mem.total/(1024**3):.1f} GB\n" \
                       f"Available: {mem.available/(1024**3):.1f} GB\n"
            except:
                return "Memory usage: unavailable\n"
        elif filename == 'system_info.txt':
            try:
                cpu_count = psutil.cpu_count()
                load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else ('N/A', 'N/A', 'N/A')
                return f"CPU cores: {cpu_count}\n" \
                       f"Load average: {load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}\n" \
                       f"Python PID: {os.getpid()}\n"
            except:
                return "System info: unavailable\n"
        return "Unknown stats file"


class BonjourRootCollection(BonjourBaseCollection):
    """Root collection for /bonjour filesystem"""

    def __init__(self, path, environ):
        super().__init__(path, environ)

    def get_member_names(self):
        self.logger.debug("Accessed /bonjour root directory")
        return ['services', 'ports', 'capabilities', 'switches', 'stats']

    def get_member(self, name):
        self.logger.debug(f"Accessing /bonjour/{name}/")
        if name in ['services', 'ports', 'capabilities', 'switches', 'stats']:
            return BonjourCategoryCollection(
                util.join_uri(self.path, name),
                self.environ,
                name
            )
        self.logger.warning(f"Unknown bonjour category: {name}")
        return None


class BonjourResource(_DAVResource):
    """Resource for Bonjour virtual files"""

    def __init__(self, path, environ, data, content_func):
        super().__init__(path, False, environ)
        self.data = data
        self.content_func = content_func
        self._content = None

    def get_content_length(self):
        if self._content is None:
            self._content = self.content_func(self.data)
        return len(self._content.encode('utf-8'))

    def get_content_type(self):
        if self.path.endswith('.json'):
            return 'application/json'
        else:
            return 'text/plain'

    def get_content(self):
        if self._content is None:
            self._content = self.content_func(self.data)
        return io.BytesIO(self._content.encode('utf-8'))

    def get_creation_date(self):
        return time.time()

    def get_last_modified(self):
        return time.time()

    def support_ranges(self):
        return False


class RootCollection(DAVCollection):
    """Root directory showing main categories"""
    
    def __init__(self, path, environ):
        super().__init__(path, environ)
    
    def get_member_names(self):
        return ["tournaments", "players", "organizations", "bonjour"]
    
    def get_member(self, name):
        if name == "tournaments":
            return DatabaseCollection("/tournaments/", self.environ, Tournament, self._get_tournaments)
        elif name == "players":
            return DatabaseCollection("/players/", self.environ, Player, self._get_players)
        elif name == "organizations":
            return DatabaseCollection("/organizations/", self.environ, Organization, self._get_organizations)
        elif name == "bonjour":
            return BonjourRootCollection("/bonjour/", self.environ)
        return None
    
    def _get_tournaments(self):
        with get_session() as session:
            return session.query(Tournament).limit(50).all()
    
    def _get_players(self):
        with get_session() as session:
            return session.query(Player).limit(50).all()
    
    def _get_organizations(self):
        with get_session() as session:
            return session.query(Organization).limit(50).all()


def create_webdav_app():
    """Create and configure WebDAV application"""
    
    config = {
        "host": "0.0.0.0",
        "port": 8081,
        "provider_mapping": {
            "/": DatabaseDAVProvider(),
        },
        "verbose": 1,
        "logging": {
            "enable_loggers": [],
        },
        "property_manager": True,
        "lock_storage": True,
        # Allow both anonymous and dummy user access
        "simple_dc": {
            "user_mapping": {
                "/": {
                    "anonymous": {"password": "", "description": "Anonymous access", "roles": []},
                    "user": {"password": "pass", "description": "Dummy user", "roles": []},
                    "admin": {"password": "admin", "description": "Admin user", "roles": []}
                },
                "*": {
                    "anonymous": {"password": "", "description": "Anonymous access", "roles": []},
                    "user": {"password": "pass", "description": "Dummy user", "roles": []},
                    "admin": {"password": "admin", "description": "Admin user", "roles": []}
                }
            }
        },
        "http_authenticator": {
            "accept_basic": True,
            "accept_digest": False,
            "default_to_digest": False,
        },
        # Make it read-only for safety
        "readonly": True,
    }
    
    return WsgiDAVApp(config)


if __name__ == "__main__":
    # This should never run due to execution guard
    # This module should be run through go.py (execution guard handles the error)
    pass