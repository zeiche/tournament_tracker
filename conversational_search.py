#!/usr/bin/env python3
"""
Conversational search engine for tournament data
Understands natural language queries and returns relevant results
"""

import re
from typing import List, Dict, Any, Tuple
from database_utils import get_session
from tournament_models import Tournament, Organization, AttendanceRecord
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
        """Perform a general search across all entities"""
        all_results = []
        
        # Search everything and combine
        all_results.extend(self._search_organizations(params))
        all_results.extend(self._search_tournaments(params))
        all_results.extend(self._search_venues(params))
        
        # Sort by relevance (for now, by attendance/popularity)
        all_results.sort(
            key=lambda x: x.get('attendance', x.get('total_attendance', 0)), 
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