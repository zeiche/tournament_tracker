# ============================================================================
# PLAYER MODEL
# ============================================================================

class Player(Base, BaseModel, TimestampMixin):
    """Player in tournaments with comprehensive analytics and history"""
    __tablename__ = 'players'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    startgg_id = Column(String, unique=True, index=True)  # start.gg player ID
    gamer_tag = Column(String, nullable=False)
    name = Column(String)  # Real name (if available)
    
    # Relationships
    placements = relationship("TournamentPlacement", back_populates="player", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Player(tag='{self.gamer_tag}', id={self.startgg_id})>"
    
    def __str__(self):
        return self.gamer_tag
    
    # ========================================================================
    # BASIC PROPERTIES
    # ========================================================================
    
    @property
    def display_name(self) -> str:
        """Get display name (real name if available, otherwise gamer tag)"""
        return self.name if self.name else self.gamer_tag
    
    @property
    def has_real_name(self) -> bool:
        """Check if we have the player's real name"""
        return bool(self.name)
    
    @property
    def tournament_count(self) -> int:
        """Count of unique tournaments participated in"""
        return len(set(p.tournament_id for p in self.placements))
    
    @property
    def total_placements(self) -> int:
        """Total number of placements (can be multiple per tournament)"""
        return len(self.placements)
    
    # ========================================================================
    # PLACEMENT AND RESULTS
    # ========================================================================
    
    @property
    def tournaments_won(self) -> List[Tournament]:
        """Get tournaments this player won (1st place)"""
        return [p.tournament for p in self.placements if p.placement == 1]
    
    @property
    def win_count(self) -> int:
        """Number of tournament wins"""
        return len([p for p in self.placements if p.placement == 1])
    
    @property
    def podium_finishes(self) -> int:
        """Number of top 3 finishes"""
        return len([p for p in self.placements if p.placement <= 3])
    
    @property
    def top_8_finishes(self) -> int:
        """Number of top 8 finishes"""
        return len([p for p in self.placements if p.placement <= 8])
    
    def get_placement_distribution(self) -> Dict[int, int]:
        """Get distribution of placements"""
        distribution = Counter(p.placement for p in self.placements)
        return dict(sorted(distribution.items()))
    
    def get_best_placement(self) -> Optional[int]:
        """Get best placement ever achieved"""
        if not self.placements:
            return None
        return min(p.placement for p in self.placements)
    
    def get_worst_placement(self) -> Optional[int]:
        """Get worst placement"""
        if not self.placements:
            return None
        return max(p.placement for p in self.placements)
    
    def get_average_placement(self) -> float:
        """Calculate average placement"""
        if not self.placements:
            return 0.0
        return sum(p.placement for p in self.placements) / len(self.placements)
    
    def get_median_placement(self) -> Optional[int]:
        """Calculate median placement"""
        if not self.placements:
            return None
        placements = sorted(p.placement for p in self.placements)
        n = len(placements)
        if n % 2 == 0:
            return (placements[n//2 - 1] + placements[n//2]) // 2
        return placements[n//2]
    
    # ========================================================================
    # EARNINGS AND PRIZES
    # ========================================================================
    
    @property
    def total_earnings_cents(self) -> int:
        """Total prize money earned in cents"""
        return sum(p.prize_amount or 0 for p in self.placements)
    
    @property
    def total_earnings(self) -> float:
        """Total prize money earned in dollars"""
        return self.total_earnings_cents / 100.0
    
    def get_earnings_by_year(self) -> Dict[int, float]:
        """Get earnings broken down by year"""
        earnings = defaultdict(float)
        for p in self.placements:
            if p.tournament and p.tournament.start_date and p.prize_amount:
                year = p.tournament.start_date.year
                earnings[year] += p.prize_amount / 100.0
        return dict(earnings)
    
    def get_earnings_by_tournament(self) -> List[Tuple[str, float]]:
        """Get earnings by tournament"""
        earnings = []
        for p in self.placements:
            if p.prize_amount and p.prize_amount > 0:
                tournament_name = p.tournament.name if p.tournament else "Unknown"
                earnings.append((tournament_name, p.prize_amount / 100.0))
        return sorted(earnings, key=lambda x: x[1], reverse=True)
    
    def get_highest_earning(self) -> Optional[Tuple[str, float]]:
        """Get highest single tournament earning"""
        earnings = self.get_earnings_by_tournament()
        return earnings[0] if earnings else None
    
    # ========================================================================
    # PERFORMANCE METRICS
    # ========================================================================
    
    @property
    def win_rate(self) -> float:
        """Calculate win rate (percentage of tournaments won)"""
        if not self.placements:
            return 0.0
        wins = len([p for p in self.placements if p.placement == 1])
        return (wins / len(self.placements)) * 100
    
    @property
    def podium_rate(self) -> float:
        """Calculate podium finish rate (top 3)"""
        if not self.placements:
            return 0.0
        podiums = len([p for p in self.placements if p.placement <= 3])
        return (podiums / len(self.placements)) * 100
    
    @property
    def top_8_rate(self) -> float:
        """Calculate top 8 finish rate"""
        if not self.placements:
            return 0.0
        top8s = len([p for p in self.placements if p.placement <= 8])
        return (top8s / len(self.placements)) * 100
    
    def get_consistency_score(self) -> float:
        """Calculate consistency score based on placement variance"""
        if len(self.placements) < 2:
            return 0.0
        
        placements = [p.placement for p in self.placements]
        avg = sum(placements) / len(placements)
        variance = sum((p - avg) ** 2 for p in placements) / len(placements)
        
        # Lower variance = more consistent
        # Convert to 0-100 scale (100 = very consistent)
        return max(0, 100 - variance * 2)
    
    def get_improvement_trend(self) -> Optional[str]:
        """Analyze if player is improving, declining, or stable"""
        if len(self.placements) < 3:
            return None
        
        # Get recent placements sorted by date
        recent = sorted(self.placements, 
                       key=lambda p: p.tournament.end_at if p.tournament else 0)[-10:]
        
        if len(recent) < 3:
            return None
        
        # Compare first half to second half average
        mid = len(recent) // 2
        first_half_avg = sum(p.placement for p in recent[:mid]) / mid
        second_half_avg = sum(p.placement for p in recent[mid:]) / len(recent[mid:])
        
        # Lower placement number = better performance
        if second_half_avg < first_half_avg - 1:
            return "improving"
        elif second_half_avg > first_half_avg + 1:
            return "declining"
        else:
            return "stable"
    
    # ========================================================================
    # EVENT TYPE ANALYSIS
    # ========================================================================
    
    def get_singles_placements(self) -> List["TournamentPlacement"]:
        """Get singles event placements"""
        return [p for p in self.placements if p.is_singles]
    
    def get_doubles_placements(self) -> List["TournamentPlacement"]:
        """Get doubles/teams event placements"""
        return [p for p in self.placements if not p.is_singles]
    
    def get_event_breakdown(self) -> Dict[str, List["TournamentPlacement"]]:
        """Group placements by event name"""
        events = defaultdict(list)
        for p in self.placements:
            event = p.event_name or "Unknown Event"
            events[event].append(p)
        return dict(events)
    
    def get_best_event(self) -> Optional[str]:
        """Determine which event type the player performs best in"""
        event_stats = {}
        for event, placements in self.get_event_breakdown().items():
            if placements:
                avg_placement = sum(p.placement for p in placements) / len(placements)
                event_stats[event] = avg_placement
        
        if not event_stats:
            return None
        
        # Lower average placement is better
        return min(event_stats.items(), key=lambda x: x[1])[0]
    
    # ========================================================================
    # TEMPORAL ANALYSIS
    # ========================================================================
    
    def get_recent_results(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent tournament results"""
        recent = sorted(
            self.placements,
            key=lambda p: p.tournament.end_at if p.tournament and p.tournament.end_at else 0,
            reverse=True
        )[:limit]
        
        return [{
            'tournament': p.tournament.name if p.tournament else 'Unknown',
            'date': p.tournament.end_date.isoformat() if p.tournament and p.tournament.end_date else None,
            'placement': p.placement,
            'event': p.event_name,
            'prize': p.prize_dollars,
            'attendees': p.tournament.num_attendees if p.tournament else None
        } for p in recent]
    
    def get_activity_by_year(self) -> Dict[int, Dict[str, Any]]:
        """Get activity statistics by year"""
        yearly = defaultdict(lambda: {
            'tournaments': 0,
            'wins': 0,
            'podiums': 0,
            'earnings': 0.0,
            'best_placement': None,
            'events': []
        })
        
        for p in self.placements:
            if p.tournament and p.tournament.start_date:
                year = p.tournament.start_date.year
                yearly[year]['tournaments'] += 1
                
                if p.placement == 1:
                    yearly[year]['wins'] += 1
                if p.placement <= 3:
                    yearly[year]['podiums'] += 1
                if p.prize_amount:
                    yearly[year]['earnings'] += p.prize_amount / 100.0
                
                if yearly[year]['best_placement'] is None or p.placement < yearly[year]['best_placement']:
                    yearly[year]['best_placement'] = p.placement
                
                yearly[year]['events'].append(p.tournament.name)
        
        return dict(yearly)
    
    def get_active_years(self) -> List[int]:
        """Get list of years the player was active"""
        years = set()
        for p in self.placements:
            if p.tournament and p.tournament.start_date:
                years.add(p.tournament.start_date.year)
        return sorted(years)
    
    def get_career_span_years(self) -> Optional[int]:
        """Get career span in years"""
        years = self.get_active_years()
        if len(years) < 2:
            return None
        return max(years) - min(years) + 1
    
    def is_active_player(self, days: int = 90) -> bool:
        """Check if player has been active recently"""
        for p in self.placements:
            if p.tournament and p.tournament.is_past and p.tournament.days_since():
                if p.tournament.days_since() <= days:
                    return True
        return False
    
    # ========================================================================
    # OPPONENT ANALYSIS
    # ========================================================================
    
    def get_common_opponents(self, min_encounters: int = 2) -> Dict[int, int]:
        """Get players frequently encountered in tournaments"""
        opponents = defaultdict(int)
        
        for p in self.placements:
            if p.tournament:
                # Get all other players in the same tournament/event
                for other_p in p.tournament.placements:
                    if other_p.player_id != self.id and other_p.event_id == p.event_id:
                        opponents[other_p.player_id] += 1
        
        # Filter to minimum encounters
        return {pid: count for pid, count in opponents.items() if count >= min_encounters}
    
    def get_head_to_head(self, other_player_id: int) -> Dict[str, Any]:
        """Get head-to-head statistics against another player"""
        other_player = Player.find(other_player_id)
        if not other_player:
            return {'error': 'Player not found'}
        
        # Find common tournaments/events
        my_placements = {(p.tournament_id, p.event_id): p for p in self.placements}
        other_placements = {(p.tournament_id, p.event_id): p for p in other_player.placements}
        
        common_events = set(my_placements.keys()) & set(other_placements.keys())
        
        wins = 0
        losses = 0
        encounters = []
        
        for event_key in common_events:
            my_p = my_placements[event_key]
            other_p = other_placements[event_key]
            
            if my_p.placement < other_p.placement:
                wins += 1
                result = 'W'
            else:
                losses += 1
                result = 'L'
            
            encounters.append({
                'tournament': my_p.tournament.name if my_p.tournament else 'Unknown',
                'event': my_p.event_name,
                'date': my_p.tournament.end_date.isoformat() if my_p.tournament and my_p.tournament.end_date else None,
                'my_placement': my_p.placement,
                'their_placement': other_p.placement,
                'result': result
            })
        
        # Sort by date
        encounters.sort(key=lambda x: x['date'] or '', reverse=True)
        
        return {
            'vs_player': other_player.gamer_tag,
            'vs_player_name': other_player.name,
            'total_encounters': len(encounters),
            'wins': wins,
            'losses': losses,
            'win_rate': round(wins / len(encounters) * 100, 1) if encounters else 0,
            'recent_encounters': encounters[:10],
            'first_encounter': encounters[-1] if encounters else None,
            'last_encounter': encounters[0] if encounters else None
        }
    
    def get_rivals(self, min_encounters: int = 3) -> List[Dict[str, Any]]:
        """Get rival players (frequently faced with close records)"""
        rivals = []
        
        for opponent_id, encounter_count in self.get_common_opponents(min_encounters).items():
            h2h = self.get_head_to_head(opponent_id)
            
            # Consider a rival if win rate is between 30-70%
            if 30 <= h2h['win_rate'] <= 70 and encounter_count >= min_encounters:
                rivals.append({
                    'player_id': opponent_id,
                    'gamer_tag': h2h['vs_player'],
                    'encounters': encounter_count,
                    'wins': h2h['wins'],
                    'losses': h2h['losses'],
                    'win_rate': h2h['win_rate']
                })
        
        # Sort by number of encounters
        return sorted(rivals, key=lambda x: x['encounters'], reverse=True)
    
    # ========================================================================
    # LOCATION ANALYSIS
    # ========================================================================
    
    def get_tournament_locations(self) -> List[str]:
        """Get list of locations where player has competed"""
        locations = set()
        for p in self.placements:
            if p.tournament and p.tournament.city:
                city = p.tournament.city_state
                locations.add(city)
        return sorted(locations)
    
    def get_home_region(self) -> Optional[str]:
        """Guess player's home region based on tournament frequency"""
        location_counts = defaultdict(int)
        
        for p in self.placements:
            if p.tournament and p.tournament.city:
                location_counts[p.tournament.city_state] += 1
        
        if not location_counts:
            return None
        
        # Most frequent location is likely home
        return max(location_counts.items(), key=lambda x: x[1])[0]
    
    def get_travel_distance(self) -> Optional[float]:
        """Calculate total approximate travel distance in km"""
        tournaments_with_loc = []
        for p in self.placements:
            if p.tournament and p.tournament.has_location:
                tournaments_with_loc.append(p.tournament)
        
        if len(tournaments_with_loc) < 2:
            return None
        
        # Sort by date
        tournaments_with_loc.sort(key=lambda t: t.start_at or 0)
        
        total_distance = 0
        for i in range(1, len(tournaments_with_loc)):
            prev = tournaments_with_loc[i-1]
            curr = tournaments_with_loc[i]
            if prev.coordinates and curr.coordinates:
                distance = prev.distance_to(*curr.coordinates)
                if distance:
                    total_distance += distance
        
        return total_distance
    
    # ========================================================================
    # COMPREHENSIVE STATISTICS
    # ========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics for this player"""
        return {
            # Basic info
            'gamer_tag': self.gamer_tag,
            'real_name': self.name,
            'startgg_id': self.startgg_id,
            
            # Tournament participation
            'total_tournaments': self.tournament_count,
            'total_placements': self.total_placements,
            'active_years': self.get_active_years(),
            'career_span_years': self.get_career_span_years(),
            'is_active': self.is_active_player(),
            
            # Results
            'wins': self.win_count,
            'podiums': self.podium_finishes,
            'top_8s': self.top_8_finishes,
            'best_placement': self.get_best_placement(),
            'worst_placement': self.get_worst_placement(),
            'average_placement': round(self.get_average_placement(), 2),
            'median_placement': self.get_median_placement(),
            'placement_distribution': self.get_placement_distribution(),
            
            # Performance metrics
            'win_rate': round(self.win_rate, 1),
            'podium_rate': round(self.podium_rate, 1),
            'top_8_rate': round(self.top_8_rate, 1),
            'consistency_score': round(self.get_consistency_score(), 1),
            'improvement_trend': self.get_improvement_trend(),
            
            # Earnings
            'total_earnings_cents': self.total_earnings_cents,
            'total_earnings_dollars': self.total_earnings,
            'earnings_by_year': self.get_earnings_by_year(),
            'highest_earning': self.get_highest_earning(),
            
            # Event breakdown
            'singles_placements': len(self.get_singles_placements()),
            'doubles_placements': len(self.get_doubles_placements()),
            'best_event': self.get_best_event(),
            'events_played': list(self.get_event_breakdown().keys()),
            
            # Location
            'locations_played': self.get_tournament_locations(),
            'home_region': self.get_home_region(),
            'travel_distance_km': self.get_travel_distance(),
            
            # Recent activity
            'recent_results': self.get_recent_results(5)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'startgg_id': self.startgg_id,
            'gamer_tag': self.gamer_tag,
            'name': self.name,
            'display_name': self.display_name,
            'stats': self.get_stats(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'age_days': self.age_days
        }
    
    # ========================================================================
    # CLASS METHODS - QUERIES
    # ========================================================================
    
    @classmethod
    def get_or_create(cls, startgg_id: str, gamer_tag: str, name: Optional[str] = None) -> "Player":
        """Get existing player or create new one"""
        player = cls.find_by(startgg_id=startgg_id)
        
        if not player:
            player = cls(
                startgg_id=startgg_id,
                gamer_tag=gamer_tag,
                name=name
            )
            player.save()
            log_debug(f"Created player: {gamer_tag}", "model")
        else:
            # Update info if provided
            updated = False
            if gamer_tag and player.gamer_tag != gamer_tag:
                player.gamer_tag = gamer_tag
                updated = True
            if name and player.name != name:
                player.name = name
                updated = True
            
            if updated:
                player.save()
                log_debug(f"Updated player: {gamer_tag}", "model")
        
        return player
    
    @classmethod
    def search(cls, query: str) -> List["Player"]:
        """Search players by gamer tag or name"""
        session = cls.session()
        search_term = f"%{query}%"
        return session.query(cls).filter(
            (cls.gamer_tag.ilike(search_term)) |
            (cls.name.ilike(search_term))
        ).all()
    
    @classmethod
    def top_earners(cls, limit: int = 10) -> List["Player"]:
        """Get top players by prize money earned"""
        session = cls.session()
        
        # Subquery to calculate total earnings per player
        earnings_subq = session.query(
            TournamentPlacement.player_id,
            func.sum(TournamentPlacement.prize_amount).label('total_earnings')
        ).group_by(TournamentPlacement.player_id).subquery()
        
        # Join and order by earnings
        return session.query(cls).join(
            earnings_subq,
            cls.id == earnings_subq.c.player_id
        ).order_by(
            desc(earnings_subq.c.total_earnings)
        ).limit(limit).all()
    
    @classmethod
    def most_wins(cls, limit: int = 10) -> List["Player"]:
        """Get players with most tournament wins"""
        session = cls.session()
        
        # Subquery to count wins
        wins_subq = session.query(
            TournamentPlacement.player_id,
            func.count(TournamentPlacement.id).label('win_count')
        ).filter(
            TournamentPlacement.placement == 1
        ).group_by(TournamentPlacement.player_id).subquery()
        
        # Join and order by win count
        return session.query(cls).join(
            wins_subq,
            cls.id == wins_subq.c.player_id
        ).order_by(
            desc(wins_subq.c.win_count)
        ).limit(limit).all()
    
    @classmethod
    def most_tournaments(cls, limit: int = 10) -> List["Player"]:
        """Get players who have played in the most tournaments"""
        session = cls.session()
        
        # Subquery to count unique tournaments
        tournament_subq = session.query(
            TournamentPlacement.player_id,
            func.count(func.distinct(TournamentPlacement.tournament_id)).label('tournament_count')
        ).group_by(TournamentPlacement.player_id).subquery()
        
        return session.query(cls).join(
            tournament_subq,
            cls.id == tournament_subq.c.player_id
        ).order_by(
            desc(tournament_subq.c.tournament_count)
        ).limit(limit).all()
    
    @classmethod
    def active_players(cls, days: int = 90) -> List["Player"]:
        """Get recently active players"""
        session = cls.session()
        players = session.query(cls).all()
        return [p for p in players if p.is_active_player(days)]
    
    @classmethod
    def elite_players(cls, min_wins: int = 5) -> List["Player"]:
        """Get elite players with minimum number of wins"""
        session = cls.session()
        players = session.query(cls).all()
        return [p for p in players if p.win_count >= min_wins]