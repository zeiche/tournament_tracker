#!/usr/bin/env python3
"""
Conversational search engine for tournament data
Understands natural language queries and returns relevant results
"""

import re
from typing import List, Dict, Any, Tuple
from utils.database import get_session
from database.tournament_models import Tournament, Organization
from sqlalchemy import or_, and_, func
import json

class ConversationalSearch:
    """Natural language search engine for tournament data"""
    
    def __init__(self):
        self.session = None
        
    def interpret_query(self, query: str) -> Dict[str, Any]:
        """
        Interpret natural language query and extract search parameters
        Returns dict with search type and parameters
        """
        query_lower = query.lower().strip()
        
        # Extract numbers from query
        numbers = re.findall(r'\d+', query)
        
        # Extract quoted phrases
        quoted = re.findall(r'"([^"]*)"', query)
        
        # Determine search type and parameters
        params = {
            'original_query': query,
            'type': 'general',
            'filters': {},
            'sort': 'relevance'
        }
        
        # Check for attendance-related queries
        if any(word in query_lower for word in ['attendance', 'attendees', 'people', 'crowd']):
            params['type'] = 'attendance'
            if 'most' in query_lower or 'highest' in query_lower or 'top' in query_lower:
                params['sort'] = 'attendance_desc'
            elif 'least' in query_lower or 'lowest' in query_lower:
                params['sort'] = 'attendance_asc'
            
            # Check for specific attendance ranges
            if numbers and len(numbers) >= 1:
                if 'over' in query_lower or 'more than' in query_lower or '>' in query:
                    params['filters']['min_attendance'] = int(numbers[0])
                elif 'under' in query_lower or 'less than' in query_lower or '<' in query:
                    params['filters']['max_attendance'] = int(numbers[0])
                elif 'between' in query_lower and len(numbers) >= 2:
                    params['filters']['min_attendance'] = int(numbers[0])
                    params['filters']['max_attendance'] = int(numbers[1])
        
        # Check for organization queries
        if any(word in query_lower for word in ['org', 'organization', 'group', 'team', 'club']):
            params['type'] = 'organization'
            if quoted:
                params['filters']['name'] = quoted[0]
            elif 'unnamed' in query_lower or 'no name' in query_lower:
                params['filters']['unnamed'] = True
        
        # Check for tournament queries
        if any(word in query_lower for word in ['tournament', 'event', 'competition']):
            params['type'] = 'tournament'
            if quoted:
                params['filters']['name'] = quoted[0]
        
        # Check for venue queries
        if any(word in query_lower for word in ['venue', 'location', 'place', 'where']):
            params['type'] = 'venue'
            if quoted:
                params['filters']['venue'] = quoted[0]
        
        # Time-based queries
        if any(word in query_lower for word in ['recent', 'latest', 'newest', 'last']):
            params['sort'] = 'date_desc'
            params['filters']['recent'] = True
        elif any(word in query_lower for word in ['oldest', 'first', 'earliest']):
            params['sort'] = 'date_asc'
        
        # Year filtering
        year_match = re.search(r'\b(202[0-9])\b', query)
        if year_match:
            params['filters']['year'] = int(year_match.group(1))
        
        # Extract general search terms (remove common words)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                     'show', 'find', 'search', 'get', 'list', 'what', 'which', 'who', 'where', 'when'}
        
        words = query_lower.split()
        search_terms = [w for w in words if w not in stop_words and len(w) > 2]
        
        if search_terms and not quoted:
            params['filters']['search_terms'] = search_terms
        
        return params
    
    def search(self, query: str) -> Dict[str, Any]:
        """
        Execute a natural language search and return results
        """
        with get_session() as session:
            self.session = session
            
            # Interpret the query
            params = self.interpret_query(query)
            
            # Execute appropriate search based on type
            if params['type'] == 'organization':
                results = self._search_organizations(params)
            elif params['type'] == 'tournament':
                results = self._search_tournaments(params)
            elif params['type'] == 'attendance':
                results = self._search_by_attendance(params)
            elif params['type'] == 'venue':
                results = self._search_venues(params)
            else:
                # General search across all entities
                results = self._general_search(params)
            
            return {
                'query': query,
                'interpretation': params,
                'results': results,
                'count': len(results)
            }
    
    def _discover_resources(self) -> Dict[str, List[Dict]]:
        """Discover all available resources (files, visualizations, reports, etc.)"""
        import os
        
        resources = {
            'visualizations': [],
            'reports': [],
            'data_files': [],
            'services': []
        }
        
        # Define available resources with metadata
        resource_definitions = {
            'visualizations': [
                ('tournament_heatmap.png', 'Tournament Heat Map', 'Geographic density of tournament locations', ['heat', 'map', 'location', 'density', 'geographic']),
                ('tournament_heatmap_with_map.png', 'Tournament Heat Map with Streets', 'Heat map overlaid on street map', ['heat', 'map', 'street', 'location']),
                ('attendance_heatmap.png', 'Attendance Heat Map', 'Tournament attendance patterns', ['attendance', 'heat', 'map', 'pattern']),
                ('tournament_heatmap.html', 'Interactive Heat Map', 'Zoomable interactive map', ['interactive', 'map', 'zoom'])
            ],
            'reports': [
                ('tournament_report.html', 'Tournament Report', 'Full tournament statistics report', ['report', 'statistics', 'summary']),
                ('attendance_report.csv', 'Attendance Data', 'Raw attendance data export', ['attendance', 'data', 'csv', 'export'])
            ],
            'services': [
                ('web_editor', 'Organization Editor', 'Web interface for editing organizations', ['edit', 'organization', 'web']),
                ('discord_bot', 'Discord Bot', 'Natural language Discord interface', ['discord', 'bot', 'chat'])
            ]
        }
        
        # Check which resources actually exist
        base_path = '/home/ubuntu/claude/tournament_tracker/'
        
        for category, items in resource_definitions.items():
            for item in items:
                if category == 'services':
                    # Services are always "available" as concepts
                    name, title, description, keywords = item
                    resources[category].append({
                        'name': name,
                        'title': title,
                        'description': description,
                        'keywords': keywords,
                        'type': 'service'
                    })
                else:
                    filename, title, description, keywords = item
                    filepath = os.path.join(base_path, filename)
                    if os.path.exists(filepath):
                        resources[category].append({
                            'filename': filename,
                            'title': title,
                            'description': description,
                            'keywords': keywords,
                            'path': filepath,
                            'url': f'/resource/{filename}' if category == 'visualizations' else None,
                            'exists': True,
                            'type': category.rstrip('s')  # Remove plural
                        })
        
        return resources
    
    def _search_organizations(self, params: Dict) -> List[Dict]:
        """Search for organizations"""
        query = self.session.query(Organization)
        
        # Apply filters
        filters = params.get('filters', {})
        
        if filters.get('name'):
            query = query.filter(Organization.display_name.ilike(f"%{filters['name']}%"))
        
        if filters.get('unnamed'):
            query = query.filter(or_(
                Organization.display_name == None,
                Organization.display_name == '',
                Organization.display_name.ilike('%unnamed%')
            ))
        
        if filters.get('search_terms'):
            for term in filters['search_terms']:
                query = query.filter(Organization.display_name.ilike(f"%{term}%"))
        
        # Get results
        orgs = query.limit(50).all()
        
        results = []
        for org in orgs:
            attendance_sum = sum(r.attendance for r in org.attendance_records)
            tournament_count = len(org.attendance_records)
            
            results.append({
                'type': 'organization',
                'id': org.id,
                'name': org.display_name or 'Unnamed',
                'total_attendance': attendance_sum,
                'tournament_count': tournament_count,
                'avg_attendance': attendance_sum / tournament_count if tournament_count > 0 else 0
            })
        
        # Sort results
        if params.get('sort') == 'attendance_desc':
            results.sort(key=lambda x: x['total_attendance'], reverse=True)
        elif params.get('sort') == 'attendance_asc':
            results.sort(key=lambda x: x['total_attendance'])
        
        return results
    
    def _search_tournaments(self, params: Dict) -> List[Dict]:
        """Search for tournaments"""
        query = self.session.query(Tournament)
        
        filters = params.get('filters', {})
        
        if filters.get('name'):
            query = query.filter(Tournament.name.ilike(f"%{filters['name']}%"))
        
        if filters.get('min_attendance'):
            query = query.filter(Tournament.num_attendees >= filters['min_attendance'])
        
        if filters.get('max_attendance'):
            query = query.filter(Tournament.num_attendees <= filters['max_attendance'])
        
        if filters.get('year'):
            year = filters['year']
            # SQLite uses different date function
            from sqlalchemy import extract
            query = query.filter(
                extract('year', Tournament.end_at) == year
            )
        
        if filters.get('search_terms'):
            for term in filters['search_terms']:
                query = query.filter(Tournament.name.ilike(f"%{term}%"))
        
        # Sorting
        if params.get('sort') == 'date_desc':
            query = query.order_by(Tournament.end_at.desc())
        elif params.get('sort') == 'date_asc':
            query = query.order_by(Tournament.end_at.asc())
        elif params.get('sort') == 'attendance_desc':
            query = query.order_by(Tournament.num_attendees.desc())
        elif params.get('sort') == 'attendance_asc':
            query = query.order_by(Tournament.num_attendees.asc())
        
        tournaments = query.limit(50).all()
        
        results = []
        for t in tournaments:
            results.append({
                'type': 'tournament',
                'id': t.id,
                'name': t.name,
                'attendance': t.num_attendees,
                'venue': t.venue_name or 'Unknown',
                'contact': t.primary_contact or 'None',
                'date': t.end_at if t.end_at else 'Unknown'
            })
        
        return results
    
    def _search_by_attendance(self, params: Dict) -> List[Dict]:
        """Search based on attendance criteria"""
        # Combine tournament and org results
        tournaments = self._search_tournaments(params)
        orgs = self._search_organizations(params)
        
        # Merge and sort by relevance
        results = tournaments + orgs
        
        if params.get('sort') == 'attendance_desc':
            results.sort(key=lambda x: x.get('attendance', x.get('total_attendance', 0)), reverse=True)
        elif params.get('sort') == 'attendance_asc':
            results.sort(key=lambda x: x.get('attendance', x.get('total_attendance', 0)))
        
        return results[:50]  # Limit total results
    
    def _search_venues(self, params: Dict) -> List[Dict]:
        """Search for venues"""
        query = self.session.query(
            Tournament.venue_name,
            func.count(Tournament.id).label('event_count'),
            func.sum(Tournament.num_attendees).label('total_attendance')
        ).filter(Tournament.venue_name != None)
        
        filters = params.get('filters', {})
        
        if filters.get('venue'):
            query = query.filter(Tournament.venue_name.ilike(f"%{filters['venue']}%"))
        
        if filters.get('search_terms'):
            for term in filters['search_terms']:
                query = query.filter(Tournament.venue_name.ilike(f"%{term}%"))
        
        query = query.group_by(Tournament.venue_name)
        venues = query.all()
        
        results = []
        for venue_name, event_count, total_attendance in venues:
            results.append({
                'type': 'venue',
                'name': venue_name,
                'event_count': event_count,
                'total_attendance': total_attendance or 0,
                'avg_attendance': (total_attendance or 0) / event_count if event_count > 0 else 0
            })
        
        # Sort by total attendance by default
        results.sort(key=lambda x: x['total_attendance'], reverse=True)
        
        return results[:30]
    
    def _general_search(self, params: Dict) -> List[Dict]:
        """Perform a general search across all entities and resources"""
        all_results = []
        query_lower = params['original_query'].lower()
        search_terms = params['filters'].get('search_terms', [])
        
        # First, check available resources for matches
        resources = self._discover_resources()
        for category, items in resources.items():
            for resource in items:
                # Check if any search terms match the resource keywords
                keywords = resource.get('keywords', [])
                title_lower = resource.get('title', '').lower()
                desc_lower = resource.get('description', '').lower()
                
                # Score the match
                score = 0
                for term in search_terms:
                    if term in keywords:
                        score += 3  # High score for keyword match
                    if term in title_lower:
                        score += 2  # Medium score for title match
                    if term in desc_lower:
                        score += 1  # Low score for description match
                
                # Also check full query against title/description
                if 'heat' in query_lower and 'map' in query_lower and 'heat' in keywords:
                    score += 5  # Boost for heat map queries
                
                if score > 0:
                    # Add resource to results
                    result = {
                        'type': resource.get('type', 'resource'),
                        'title': resource.get('title'),
                        'description': resource.get('description'),
                        'score': score
                    }
                    
                    # Add URL for visualizations
                    if resource.get('filename'):
                        result['filename'] = resource['filename']
                        result['url'] = f"/heatmap/{resource['filename']}"
                    
                    all_results.append(result)
        
        # Search database entities
        all_results.extend(self._search_organizations(params))
        all_results.extend(self._search_tournaments(params))
        all_results.extend(self._search_venues(params))
        
        # Sort by relevance (score for resources, attendance for entities)
        all_results.sort(
            key=lambda x: (
                x.get('score', 0) * 1000 +  # Prioritize scored resources
                x.get('attendance', x.get('total_attendance', 0))
            ), 
            reverse=True
        )
        
        return all_results[:50]
    
    def get_suggestions(self, partial_query: str) -> List[str]:
        """Get search suggestions based on partial query"""
        suggestions = []
        partial_lower = partial_query.lower()
        
        # Suggest query templates
        templates = [
            "tournaments with over 100 attendees",
            "organizations in 2025",
            "venues with most events",
            "recent tournaments",
            "top organizations by attendance",
            'search for "SoCal FGC"',
            "unnamed tournaments",
            "events between 50 and 200 people"
        ]
        
        for template in templates:
            if partial_lower in template.lower():
                suggestions.append(template)
        
        # Also get actual data suggestions
        if len(partial_query) >= 2:
            with get_session() as session:
                # Get org names
                orgs = session.query(Organization.display_name).filter(
                    Organization.display_name.ilike(f"{partial_query}%")
                ).limit(3).all()
                
                for org in orgs:
                    if org[0]:
                        suggestions.append(f'organization "{org[0]}"')
                
                # Get tournament names
                tournaments = session.query(Tournament.name).filter(
                    Tournament.name.ilike(f"{partial_query}%")
                ).limit(3).all()
                
                for t in tournaments:
                    if t[0]:
                        suggestions.append(f'tournament "{t[0][:30]}"')
        
        return suggestions[:8]  # Limit suggestions

# Singleton instance
_search_engine = ConversationalSearch()

def search(query: str) -> Dict[str, Any]:
    """Main search function"""
    return _search_engine.search(query)

def get_suggestions(partial: str) -> List[str]:
    """Get search suggestions"""
    return _search_engine.get_suggestions(partial)