# ============================================================================
# ORGANIZATION MODEL
# ============================================================================

class Organization(Base, BaseModel, TimestampMixin):
    """Organization that runs tournaments with comprehensive analytics"""
    __tablename__ = 'organizations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    display_name = Column(String, nullable=False)
    contacts_json = Column(String, default='[]')  # JSON array of contact objects
    
    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.display_name}')>"
    
    def __str__(self):
        return self.display_name
    
    # ========================================================================
    # CONTACT MANAGEMENT
    # ========================================================================
    
    @property
    def contacts(self) -> List[Dict[str, str]]:
        """Get contacts as a Python list"""
        import json
        try:
            return json.loads(self.contacts_json or '[]')
        except:
            return []
    
    @contacts.setter
    def contacts(self, value: List[Dict[str, str]]):
        """Set contacts from a Python list"""
        import json
        self.contacts_json = json.dumps(value)
    
    def add_contact(self, contact_type: str, contact_value: str) -> "Organization":
        """Add a new contact"""
        contacts = self.contacts
        contacts.append({'type': contact_type, 'value': contact_value})
        self.contacts = contacts
        self.save()
        return self
    
    def remove_contact(self, index: int) -> bool:
        """Remove a contact by index"""
        contacts = self.contacts
        if 0 <= index < len(contacts):
            contacts.pop(index)
            self.contacts = contacts
            self.save()
            return True
        return False
    
    def update_contact(self, index: int, contact_type: str, contact_value: str) -> bool:
        """Update a contact by index"""
        contacts = self.contacts
        if 0 <= index < len(contacts):
            contacts[index] = {'type': contact_type, 'value': contact_value}
            self.contacts = contacts
            self.save()
            return True
        return False
    
    def has_contact(self, contact_value: str) -> bool:
        """Check if organization has a specific contact"""
        from database_utils import normalize_contact
        normalized = normalize_contact(contact_value)
        for contact in self.contacts:
            if normalize_contact(contact.get('value', '')) == normalized:
                return True
        return False
    
    def get_contact_by_type(self, contact_type: str) -> List[str]:
        """Get all contacts of a specific type"""
        return [c['value'] for c in self.contacts if c.get('type') == contact_type]
    
    def get_primary_contact(self) -> Optional[str]:
        """Get the primary (first) contact"""
        if self.contacts:
            return self.contacts[0].get('value')
        return None
    
    def get_contact_types(self) -> Set[str]:
        """Get unique contact types"""
        return set(c.get('type', 'unknown') for c in self.contacts)
    
    # ========================================================================
    # TOURNAMENT RELATIONSHIPS
    # ========================================================================
    
    @property
    def tournaments(self) -> List[Tournament]:
        """Get all tournaments for this organization"""
        from database_utils import normalize_contact
        
        # Collect all normalized contacts for this org
        org_contacts_normalized = set()
        for contact in self.contacts:
            value = contact.get('value', '')
            if value:
                org_contacts_normalized.add(normalize_contact(value))
        
        # Find tournaments that match any of these contacts
        session = self.session()
        tournaments = session.query(Tournament).all()
        matching = []
        for t in tournaments:
            if t.primary_contact:
                t_normalized = normalize_contact(t.primary_contact)
                if t_normalized in org_contacts_normalized:
                    matching.append(t)
        
        return matching
    
    @property
    def tournament_count(self) -> int:
        """Count of tournaments"""
        return len(self.tournaments)
    
    @property
    def total_attendance(self) -> int:
        """Calculate total attendance across all tournaments"""
        return sum(t.num_attendees or 0 for t in self.tournaments)
    
    @property
    def average_attendance(self) -> float:
        """Calculate average attendance"""
        tournaments = self.tournaments
        if not tournaments:
            return 0.0
        total = sum(t.num_attendees or 0 for t in tournaments)
        return total / len(tournaments)
    
    def get_tournaments_by_year(self, year: int) -> List[Tournament]:
        """Get tournaments for a specific year"""
        return [t for t in self.tournaments 
                if t.start_date and t.start_date.year == year]
    
    def get_upcoming_tournaments(self) -> List[Tournament]:
        """Get upcoming tournaments"""
        return sorted([t for t in self.tournaments if t.is_upcoming],
                     key=lambda t: t.start_at)
    
    def get_recent_tournaments(self, days: int = 90) -> List[Tournament]:
        """Get recent tournaments"""
        return [t for t in self.tournaments 
                if t.is_past and t.days_since() and t.days_since() <= days]
    
    def get_active_tournaments(self) -> List[Tournament]:
        """Get currently active tournaments"""
        return [t for t in self.tournaments if t.is_active]
    
    def get_largest_tournament(self) -> Optional[Tournament]:
        """Get the largest tournament by attendance"""
        tournaments = self.tournaments
        if not tournaments:
            return None
        return max(tournaments, key=lambda t: t.num_attendees or 0)
    
    def get_first_tournament(self) -> Optional[Tournament]:
        """Get the earliest tournament"""
        tournaments = [t for t in self.tournaments if t.start_at]
        if not tournaments:
            return None
        return min(tournaments, key=lambda t: t.start_at)
    
    def get_latest_tournament(self) -> Optional[Tournament]:
        """Get the most recent tournament"""
        tournaments = [t for t in self.tournaments if t.end_at]
        if not tournaments:
            return None
        return max(tournaments, key=lambda t: t.end_at)
    
    # ========================================================================
    # LOCATION ANALYTICS
    # ========================================================================
    
    def get_location_coverage(self) -> Dict[str, int]:
        """Get breakdown of tournaments by location"""
        coverage = {}
        for t in self.tournaments:
            if t.city:
                city_key = f"{t.city}, {t.addr_state}" if t.addr_state else t.city
                coverage[city_key] = coverage.get(city_key, 0) + 1
        return dict(sorted(coverage.items(), key=lambda x: x[1], reverse=True))
    
    def get_unique_cities(self) -> Set[str]:
        """Get unique cities where tournaments are held"""
        return set(t.city for t in self.tournaments if t.city)
    
    def get_unique_venues(self) -> Set[str]:
        """Get unique venues"""
        return set(t.venue_name for t in self.tournaments if t.venue_name)
    
    def get_geographic_spread(self) -> Optional[float]:
        """Calculate geographic spread (max distance between tournaments) in km"""
        tournaments_with_loc = [t for t in self.tournaments if t.has_location]
        if len(tournaments_with_loc) < 2:
            return None
        
        max_distance = 0
        for i, t1 in enumerate(tournaments_with_loc):
            for t2 in tournaments_with_loc[i+1:]:
                if t1.coordinates and t2.coordinates:
                    distance = t1.distance_to(*t2.coordinates)
                    if distance and distance > max_distance:
                        max_distance = distance
        
        return max_distance if max_distance > 0 else None
    
    def is_local_org(self) -> bool:
        """Check if this is a local organization (all tournaments in same city)"""
        cities = self.get_unique_cities()
        return len(cities) == 1
    
    def is_regional_org(self) -> bool:
        """Check if this is a regional organization (multiple cities)"""
        cities = self.get_unique_cities()
        return len(cities) > 1
    
    # ========================================================================
    # TEMPORAL ANALYTICS
    # ========================================================================
    
    def get_activity_span_days(self) -> Optional[int]:
        """Get the span of activity in days (first to last tournament)"""
        first = self.get_first_tournament()
        last = self.get_latest_tournament()
        
        if first and last and first.start_at and last.end_at:
            return (last.end_at - first.start_at) // 86400
        return None
    
    def get_frequency(self) -> Optional[float]:
        """Get average frequency of tournaments (per month)"""
        span_days = self.get_activity_span_days()
        if not span_days or span_days == 0:
            return None
        
        months = span_days / 30
        return self.tournament_count / months if months > 0 else None
    
    def get_monthly_distribution(self) -> Dict[str, int]:
        """Get distribution of tournaments by month"""
        distribution = defaultdict(int)
        for t in self.tournaments:
            if t.start_date:
                month_key = t.start_date.strftime("%B")
                distribution[month_key] += 1
        return dict(distribution)
    
    def get_weekday_distribution(self) -> Dict[str, int]:
        """Get distribution of tournaments by day of week"""
        distribution = defaultdict(int)
        for t in self.tournaments:
            if t.start_date:
                weekday = t.start_date.strftime("%A")
                distribution[weekday] += 1
        return dict(distribution)
    
    def get_yearly_stats(self) -> Dict[int, Dict[str, Any]]:
        """Get statistics broken down by year"""
        yearly = defaultdict(lambda: {'count': 0, 'attendance': 0, 'tournaments': []})
        
        for t in self.tournaments:
            if t.start_date:
                year = t.start_date.year
                yearly[year]['count'] += 1
                yearly[year]['attendance'] += t.num_attendees or 0
                yearly[year]['tournaments'].append(t.name)
        
        # Calculate averages
        for year, stats in yearly.items():
            if stats['count'] > 0:
                stats['avg_attendance'] = stats['attendance'] / stats['count']
        
        return dict(yearly)
    
    # ========================================================================
    # PERFORMANCE METRICS
    # ========================================================================
    
    def get_growth_rate(self) -> Optional[float]:
        """Calculate year-over-year growth rate in attendance"""
        yearly = self.get_yearly_stats()
        if len(yearly) < 2:
            return None
        
        years = sorted(yearly.keys())
        recent = yearly[years[-1]]['attendance']
        previous = yearly[years[-2]]['attendance']
        
        if previous == 0:
            return None
        
        return ((recent - previous) / previous) * 100
    
    def get_consistency_score(self) -> float:
        """Calculate consistency score (0-100) based on regular tournament schedule"""
        freq = self.get_frequency()
        if not freq:
            return 0.0
        
        # Score based on frequency (1-4 per month is good)
        if 1 <= freq <= 4:
            return min(100, freq * 25)
        elif freq < 1:
            return freq * 100  # Less than monthly
        else:
            return max(0, 100 - (freq - 4) * 10)  # Too frequent
    
    def get_retention_metrics(self) -> Dict[str, Any]:
        """Calculate player retention metrics"""
        # Track players across tournaments
        player_tournaments = defaultdict(list)
        
        for t in self.tournaments:
            for p in t.placements:
                player_tournaments[p.player_id].append(t.id)
        
        # Calculate metrics
        total_players = len(player_tournaments)
        returning_players = sum(1 for tournaments in player_tournaments.values() 
                               if len(tournaments) > 1)
        
        retention_rate = (returning_players / total_players * 100) if total_players > 0 else 0
        
        # Average tournaments per player
        avg_tournaments = (sum(len(t) for t in player_tournaments.values()) / total_players) if total_players > 0 else 0
        
        return {
            'total_unique_players': total_players,
            'returning_players': returning_players,
            'retention_rate': round(retention_rate, 1),
            'avg_tournaments_per_player': round(avg_tournaments, 2),
            'loyal_players': sum(1 for t in player_tournaments.values() if len(t) >= 5)
        }
    
    # ========================================================================
    # COMPREHENSIVE STATISTICS
    # ========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics for this organization"""
        tournaments = self.tournaments
        
        if not tournaments:
            return self._empty_stats()
        
        largest = self.get_largest_tournament()
        retention = self.get_retention_metrics()
        
        return {
            # Basic metrics
            'total_tournaments': len(tournaments),
            'total_attendance': self.total_attendance,
            'average_attendance': round(self.average_attendance, 1),
            
            # Size metrics
            'largest_tournament': {
                'name': largest.name,
                'attendance': largest.num_attendees
            } if largest else None,
            
            # Temporal metrics
            'upcoming_count': len(self.get_upcoming_tournaments()),
            'recent_count': len(self.get_recent_tournaments()),
            'activity_span_days': self.get_activity_span_days(),
            'frequency_per_month': round(self.get_frequency() or 0, 2),
            'growth_rate': self.get_growth_rate(),
            'consistency_score': round(self.get_consistency_score(), 1),
            
            # Location metrics
            'unique_cities': len(self.get_unique_cities()),
            'unique_venues': len(self.get_unique_venues()),
            'cities': sorted(self.get_unique_cities()),
            'is_local': self.is_local_org(),
            'is_regional': self.is_regional_org(),
            'geographic_spread_km': round(self.get_geographic_spread() or 0, 1),
            
            # Location breakdown
            'location_coverage': self.get_location_coverage(),
            'socal_tournaments': len([t for t in tournaments if t.is_in_socal()]),
            
            # Player metrics
            'retention_metrics': retention,
            
            # Tournament categories
            'major_tournaments': len([t for t in tournaments if t.is_major()]),
            'premier_tournaments': len([t for t in tournaments if t.is_premier()]),
            'finished_tournaments': len([t for t in tournaments if t.is_finished()]),
            
            # Distributions
            'monthly_distribution': self.get_monthly_distribution(),
            'weekday_distribution': self.get_weekday_distribution()
        }
    
    def _empty_stats(self) -> Dict[str, Any]:
        """Return empty stats structure"""
        return {
            'total_tournaments': 0,
            'total_attendance': 0,
            'average_attendance': 0,
            'largest_tournament': None,
            'upcoming_count': 0,
            'recent_count': 0,
            'activity_span_days': None,
            'frequency_per_month': 0,
            'growth_rate': None,
            'consistency_score': 0,
            'unique_cities': 0,
            'unique_venues': 0,
            'cities': [],
            'is_local': False,
            'is_regional': False,
            'geographic_spread_km': 0,
            'location_coverage': {},
            'socal_tournaments': 0,
            'retention_metrics': {
                'total_unique_players': 0,
                'returning_players': 0,
                'retention_rate': 0,
                'avg_tournaments_per_player': 0,
                'loyal_players': 0
            },
            'major_tournaments': 0,
            'premier_tournaments': 0,
            'finished_tournaments': 0,
            'monthly_distribution': {},
            'weekday_distribution': {}
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'display_name': self.display_name,
            'contacts': self.contacts,
            'contact_types': list(self.get_contact_types()),
            'primary_contact': self.get_primary_contact(),
            'tournament_count': self.tournament_count,
            'total_attendance': self.total_attendance,
            'average_attendance': round(self.average_attendance, 1),
            'stats': self.get_stats(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'age_days': self.age_days,
            'last_modified_days': self.last_modified_days
        }
    
    # ========================================================================
    # CLASS METHODS - QUERIES
    # ========================================================================
    
    @classmethod
    def search(cls, query: str) -> List["Organization"]:
        """Search organizations by name"""
        session = cls.session()
        search_term = f"%{query}%"
        return session.query(cls).filter(
            cls.display_name.ilike(search_term)
        ).all()
    
    @classmethod
    def by_contact(cls, contact: str) -> Optional["Organization"]:
        """Find organization by contact"""
        from database_utils import normalize_contact
        normalized = normalize_contact(contact)
        
        session = cls.session()
        orgs = session.query(cls).all()
        for org in orgs:
            for c in org.contacts:
                if normalize_contact(c.get('value', '')) == normalized:
                    return org
        return None
    
    @classmethod
    def top_by_attendance(cls, limit: int = 10) -> List["Organization"]:
        """Get top organizations by total attendance"""
        session = cls.session()
        orgs = session.query(cls).all()
        
        # Calculate attendance for each
        org_attendance = []
        for org in orgs:
            total = org.total_attendance
            if total > 0:
                org_attendance.append((org, total))
        
        # Sort and return top N
        org_attendance.sort(key=lambda x: x[1], reverse=True)
        return [org for org, _ in org_attendance[:limit]]
    
    @classmethod
    def top_by_tournament_count(cls, limit: int = 10) -> List["Organization"]:
        """Get top organizations by number of tournaments"""
        session = cls.session()
        orgs = session.query(cls).all()
        
        # Calculate count for each
        org_counts = []
        for org in orgs:
            count = org.tournament_count
            if count > 0:
                org_counts.append((org, count))
        
        # Sort and return top N
        org_counts.sort(key=lambda x: x[1], reverse=True)
        return [org for org, _ in org_counts[:limit]]
    
    @classmethod
    def active(cls) -> List["Organization"]:
        """Get organizations with recent or upcoming tournaments"""
        session = cls.session()
        orgs = session.query(cls).all()
        
        active_orgs = []
        for org in orgs:
            if org.get_upcoming_tournaments() or org.get_recent_tournaments(days=90):
                active_orgs.append(org)
        
        return active_orgs
    
    @classmethod
    def local(cls) -> List["Organization"]:
        """Get local organizations (single city)"""
        session = cls.session()
        orgs = session.query(cls).all()
        return [org for org in orgs if org.is_local_org()]
    
    @classmethod
    def regional(cls) -> List["Organization"]:
        """Get regional organizations (multiple cities)"""
        session = cls.session()
        orgs = session.query(cls).all()
        return [org for org in orgs if org.is_regional_org()]