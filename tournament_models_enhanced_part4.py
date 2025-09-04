# ============================================================================
# TOURNAMENT PLACEMENT MODEL
# ============================================================================

class TournamentPlacement(Base, BaseModel, TimestampMixin):
    """Top placements in tournaments with detailed analytics"""
    __tablename__ = 'tournament_placements'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tournament_id = Column(String, ForeignKey('tournaments.id'), nullable=False)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    placement = Column(Integer, nullable=False)  # 1-8 for top 8, higher for others
    prize_amount = Column(Integer, default=0)  # Prize money in cents
    event_name = Column(String)  # Name of the specific event (e.g. "SF6 Singles")
    event_id = Column(String)  # start.gg event ID
    
    recorded_at = Column(DateTime, default=func.now())
    
    # Relationships
    tournament = relationship("Tournament", back_populates="placements")
    player = relationship("Player", back_populates="placements")
    
    # Unique constraint per event
    __table_args__ = (
        Index('ix_tournament_player_event', tournament_id, player_id, event_id, unique=True),
    )
    
    def __repr__(self):
        event_info = f" ({self.event_name})" if self.event_name else ""
        player_tag = self.player.gamer_tag if self.player else 'Unknown'
        return f"<Placement(tournament={self.tournament_id}, player={player_tag}, place={self.placement}{event_info})>"
    
    def __str__(self):
        return f"{self.placement}. {self.player.gamer_tag if self.player else 'Unknown'}"
    
    # ========================================================================
    # BASIC PROPERTIES
    # ========================================================================
    
    @property
    def prize_dollars(self) -> float:
        """Prize amount in dollars"""
        return self.prize_amount / 100.0 if self.prize_amount else 0.0
    
    @property
    def is_singles(self) -> bool:
        """Check if this is a singles event"""
        if not self.event_name:
            return True  # Default assumption
        
        event_name = self.event_name.lower()
        # Check for doubles/teams indicators
        doubles_keywords = ['doubles', 'teams', 'crew', '2v2', '3v3', 'tag', 'duo', 'squad']
        return not any(keyword in event_name for keyword in doubles_keywords)
    
    @property
    def is_win(self) -> bool:
        """Check if this is a tournament win"""
        return self.placement == 1
    
    @property
    def is_podium(self) -> bool:
        """Check if this is a podium finish (top 3)"""
        return self.placement <= 3
    
    @property
    def is_top_8(self) -> bool:
        """Check if this is a top 8 finish"""
        return self.placement <= 8
    
    def get_placement_name(self) -> str:
        """Get human-readable placement name"""
        placements = {
            1: "1st (Winner)",
            2: "2nd",
            3: "3rd",
            4: "4th",
            5: "5th-6th",
            6: "5th-6th",
            7: "7th-8th",
            8: "7th-8th"
        }
        
        if self.placement in placements:
            return placements[self.placement]
        elif self.placement <= 12:
            return f"9th-12th"
        elif self.placement <= 16:
            return f"13th-16th"
        else:
            return f"{self.placement}th"
    
    def get_points(self, system: str = "standard") -> int:
        """Calculate points based on placement using various systems"""
        
        if system == "standard":
            # Standard points system
            points = {
                1: 100,
                2: 70,
                3: 45,
                4: 25,
                5: 13,
                6: 13,
                7: 7,
                8: 7
            }
            return points.get(self.placement, max(0, 9 - self.placement))
        
        elif system == "evo":
            # EVO-style points
            points = {
                1: 128,
                2: 64,
                3: 32,
                4: 16,
                5: 8,
                6: 8,
                7: 4,
                8: 4
            }
            return points.get(self.placement, 0)
        
        elif system == "linear":
            # Linear decrease
            return max(0, 101 - self.placement * 10)
        
        else:
            return 0
    
    # ========================================================================
    # TOURNAMENT CONTEXT
    # ========================================================================
    
    def get_tournament_size(self) -> Optional[int]:
        """Get the size of the tournament"""
        if self.tournament:
            return self.tournament.num_attendees
        return None
    
    def get_placement_percentage(self) -> Optional[float]:
        """Get placement as percentage of field"""
        size = self.get_tournament_size()
        if size and size > 0:
            return (self.placement / size) * 100
        return None
    
    def get_players_beaten(self) -> Optional[int]:
        """Calculate number of players beaten"""
        size = self.get_tournament_size()
        if size:
            return size - self.placement
        return None
    
    def is_major_placement(self) -> bool:
        """Check if this is a placement at a major tournament"""
        return self.tournament and self.tournament.is_major()
    
    def is_premier_placement(self) -> bool:
        """Check if this is a placement at a premier tournament"""
        return self.tournament and self.tournament.is_premier()
    
    def get_tournament_date(self) -> Optional[datetime]:
        """Get the date of the tournament"""
        if self.tournament:
            return self.tournament.end_date
        return None
    
    # ========================================================================
    # OPPONENT ANALYSIS
    # ========================================================================
    
    def get_other_placements(self) -> List["TournamentPlacement"]:
        """Get other placements in the same event"""
        if not self.tournament:
            return []
        
        return [p for p in self.tournament.placements 
                if p.event_id == self.event_id and p.id != self.id]
    
    def get_players_above(self) -> List["Player"]:
        """Get players who placed above this placement"""
        others = self.get_other_placements()
        return [p.player for p in others if p.placement < self.placement and p.player]
    
    def get_players_below(self) -> List["Player"]:
        """Get players who placed below this placement"""
        others = self.get_other_placements()
        return [p.player for p in others if p.placement > self.placement and p.player]
    
    def get_closest_rivals(self, range: int = 2) -> List["TournamentPlacement"]:
        """Get placements within a certain range"""
        others = self.get_other_placements()
        return [p for p in others 
                if abs(p.placement - self.placement) <= range and p.id != self.id]
    
    def beat_player(self, player_id: int) -> bool:
        """Check if this placement beat a specific player"""
        others = self.get_other_placements()
        for p in others:
            if p.player_id == player_id:
                return self.placement < p.placement
        return False
    
    # ========================================================================
    # VALUE AND QUALITY METRICS
    # ========================================================================
    
    def get_quality_score(self) -> float:
        """Calculate quality score based on placement and tournament size"""
        if not self.tournament:
            return 0.0
        
        # Base score from placement
        placement_score = 100 / self.placement if self.placement > 0 else 0
        
        # Weight by tournament size
        size_multiplier = 1.0
        if self.tournament.num_attendees:
            if self.tournament.num_attendees >= 500:
                size_multiplier = 3.0
            elif self.tournament.num_attendees >= 200:
                size_multiplier = 2.0
            elif self.tournament.num_attendees >= 100:
                size_multiplier = 1.5
            elif self.tournament.num_attendees >= 50:
                size_multiplier = 1.2
        
        return placement_score * size_multiplier
    
    def get_prize_percentage(self) -> Optional[float]:
        """Get prize as percentage of total tournament prize pool"""
        if not self.tournament or not self.prize_amount:
            return None
        
        total_prize = sum(p.prize_amount or 0 for p in self.tournament.placements)
        if total_prize > 0:
            return (self.prize_amount / total_prize) * 100
        return None
    
    def get_relative_performance(self) -> Optional[str]:
        """Categorize performance relative to tournament size"""
        percentage = self.get_placement_percentage()
        if not percentage:
            return None
        
        if percentage <= 1:
            return "elite"  # Top 1%
        elif percentage <= 5:
            return "excellent"  # Top 5%
        elif percentage <= 10:
            return "great"  # Top 10%
        elif percentage <= 25:
            return "good"  # Top 25%
        elif percentage <= 50:
            return "average"  # Top 50%
        else:
            return "below_average"
    
    # ========================================================================
    # COMPARISON METHODS
    # ========================================================================
    
    def is_better_than(self, other: "TournamentPlacement") -> bool:
        """Compare if this placement is better than another"""
        # First compare by placement number
        if self.placement != other.placement:
            return self.placement < other.placement
        
        # If same placement, compare by tournament size
        my_size = self.get_tournament_size() or 0
        other_size = other.get_tournament_size() or 0
        
        return my_size > other_size
    
    def compare_to(self, other: "TournamentPlacement") -> Dict[str, Any]:
        """Detailed comparison with another placement"""
        return {
            'better': self.is_better_than(other),
            'my_placement': self.placement,
            'their_placement': other.placement,
            'my_tournament': self.tournament.name if self.tournament else None,
            'their_tournament': other.tournament.name if other.tournament else None,
            'my_tournament_size': self.get_tournament_size(),
            'their_tournament_size': other.get_tournament_size(),
            'my_prize': self.prize_dollars,
            'their_prize': other.prize_dollars,
            'my_quality_score': self.get_quality_score(),
            'their_quality_score': other.get_quality_score()
        }
    
    # ========================================================================
    # STATISTICS
    # ========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics for this placement"""
        return {
            'placement': self.placement,
            'placement_name': self.get_placement_name(),
            'event': self.event_name,
            'event_id': self.event_id,
            'is_singles': self.is_singles,
            'is_win': self.is_win,
            'is_podium': self.is_podium,
            'is_top_8': self.is_top_8,
            
            # Tournament context
            'tournament': self.tournament.name if self.tournament else None,
            'tournament_id': self.tournament_id,
            'tournament_size': self.get_tournament_size(),
            'tournament_date': self.get_tournament_date().isoformat() if self.get_tournament_date() else None,
            'is_major': self.is_major_placement(),
            'is_premier': self.is_premier_placement(),
            
            # Performance metrics
            'placement_percentage': self.get_placement_percentage(),
            'players_beaten': self.get_players_beaten(),
            'relative_performance': self.get_relative_performance(),
            'quality_score': round(self.get_quality_score(), 2),
            
            # Prize
            'prize_cents': self.prize_amount,
            'prize_dollars': self.prize_dollars,
            'prize_percentage': self.get_prize_percentage(),
            
            # Points
            'points_standard': self.get_points('standard'),
            'points_evo': self.get_points('evo'),
            
            # Player info
            'player': self.player.gamer_tag if self.player else None,
            'player_id': self.player_id,
            
            # Metadata
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'tournament_id': self.tournament_id,
            'tournament_name': self.tournament.name if self.tournament else None,
            'player_id': self.player_id,
            'player_tag': self.player.gamer_tag if self.player else None,
            'placement': self.placement,
            'placement_name': self.get_placement_name(),
            'event_name': self.event_name,
            'event_id': self.event_id,
            'prize_dollars': self.prize_dollars,
            'is_singles': self.is_singles,
            'is_win': self.is_win,
            'is_podium': self.is_podium,
            'quality_score': round(self.get_quality_score(), 2),
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None
        }
    
    # ========================================================================
    # CLASS METHODS - QUERIES
    # ========================================================================
    
    @classmethod
    def wins(cls) -> List["TournamentPlacement"]:
        """Get all tournament wins"""
        session = cls.session()
        return session.query(cls).filter(cls.placement == 1).all()
    
    @classmethod
    def podiums(cls) -> List["TournamentPlacement"]:
        """Get all podium finishes"""
        session = cls.session()
        return session.query(cls).filter(cls.placement <= 3).all()
    
    @classmethod
    def top_8s(cls) -> List["TournamentPlacement"]:
        """Get all top 8 finishes"""
        session = cls.session()
        return session.query(cls).filter(cls.placement <= 8).all()
    
    @classmethod
    def by_event(cls, event_name: str) -> List["TournamentPlacement"]:
        """Get placements for a specific event"""
        session = cls.session()
        return session.query(cls).filter(cls.event_name == event_name).all()
    
    @classmethod
    def by_tournament(cls, tournament_id: str) -> List["TournamentPlacement"]:
        """Get all placements for a tournament"""
        session = cls.session()
        return session.query(cls).filter(
            cls.tournament_id == tournament_id
        ).order_by(cls.placement).all()
    
    @classmethod
    def by_player(cls, player_id: int) -> List["TournamentPlacement"]:
        """Get all placements for a player"""
        session = cls.session()
        return session.query(cls).filter(
            cls.player_id == player_id
        ).order_by(cls.placement).all()
    
    @classmethod
    def recent(cls, days: int = 30) -> List["TournamentPlacement"]:
        """Get recent placements"""
        session = cls.session()
        cutoff = datetime.now() - timedelta(days=days)
        
        return session.query(cls).join(Tournament).filter(
            Tournament.end_at >= cutoff.timestamp()
        ).order_by(desc(Tournament.end_at)).all()
    
    @classmethod
    def highest_prizes(cls, limit: int = 10) -> List["TournamentPlacement"]:
        """Get placements with highest prizes"""
        session = cls.session()
        return session.query(cls).filter(
            cls.prize_amount > 0
        ).order_by(desc(cls.prize_amount)).limit(limit).all()
    
    @classmethod
    def at_majors(cls) -> List["TournamentPlacement"]:
        """Get placements at major tournaments"""
        session = cls.session()
        return session.query(cls).join(Tournament).filter(
            Tournament.num_attendees >= 100
        ).all()
    
    @classmethod
    def singles_only(cls) -> List["TournamentPlacement"]:
        """Get singles event placements only"""
        session = cls.session()
        all_placements = session.query(cls).all()
        return [p for p in all_placements if p.is_singles]
    
    @classmethod
    def doubles_only(cls) -> List["TournamentPlacement"]:
        """Get doubles/teams event placements only"""
        session = cls.session()
        all_placements = session.query(cls).all()
        return [p for p in all_placements if not p.is_singles]


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def normalize_contact(contact: str) -> Optional[str]:
    """Normalize contact information for consistent grouping"""
    if not contact:
        return None
    
    contact = contact.strip().lower()
    
    # Normalize Discord URLs
    if 'discord.gg' in contact or 'discord.com' in contact:
        discord_match = re.search(r'discord\.(?:gg|com/invite)/([a-zA-Z0-9]+)', contact)
        if discord_match:
            return f"discord:{discord_match.group(1).lower()}"
    
    # Normalize email addresses
    if '@' in contact:
        return contact.lower()
    
    # For organization names, normalize spacing
    contact = re.sub(r'\s+', ' ', contact)
    return contact

def get_display_name_from_contact(contact: str) -> str:
    """Get display name from contact"""
    if not contact:
        return "Unknown"
    
    # If it's not email or discord, use as display name
    if '@' not in contact and 'discord' not in contact.lower():
        return contact
    
    return contact

def determine_contact_type(contact: str) -> str:
    """Determine contact type"""
    if not contact:
        return 'unknown'
    contact = contact.lower()
    
    if '@' in contact:
        return 'email'
    elif 'discord' in contact:
        return 'discord'
    elif contact.startswith('http'):
        return 'website'
    elif contact.replace(' ', '').replace('-', '').isdigit():
        return 'phone'
    else:
        return 'name'