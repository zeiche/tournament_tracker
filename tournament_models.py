"""
tournament_models.py - SQLAlchemy Models for Tournament Tracker
Pure data models that use centralized session management from database_utils
"""
import re
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

# Import centralized session management
from database_utils import Session, get_session
from log_utils import log_debug, log_info, log_error

Base = declarative_base()

class BaseModel:
    """Base model with session-safe REPL-friendly methods"""
    
    @classmethod
    def session(cls):
        """Get current session from centralized database_utils"""
        if Session is None:
            raise RuntimeError("Database not initialized. Call database_utils.init_db() first.")
        return Session()
    
    def save(self):
        """Save this instance using centralized session"""
        session = self.session()
        session.add(self)
        session.commit()
        
        # Clear cache after save to ensure consistency
        from database_utils import clear_session_cache
        clear_session_cache()
        
        log_debug(f"Saved {self.__class__.__name__}: {getattr(self, 'id', 'unknown')}", "model")
        return self
    
    def delete(self):
        """Delete this instance using centralized session"""
        session = self.session()
        session.delete(self)
        session.commit()
        
        # Clear cache after delete
        from database_utils import clear_session_cache
        clear_session_cache()
        
        log_debug(f"Deleted {self.__class__.__name__}: {getattr(self, 'id', 'unknown')}", "model")
    
    def refresh(self):
        """Reload from database"""
        session = self.session()
        session.refresh(self)
        return self
    
    def update(self, **kwargs):
        """Update attributes"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self
    
    @classmethod
    def find(cls, id):
        """Find by primary key"""
        session = cls.session()
        return session.get(cls, id)
    
    @classmethod
    def find_by(cls, **kwargs):
        """Find first record matching criteria"""
        session = cls.session()
        result = session.query(cls).filter_by(**kwargs).first()
        log_debug(f"Found {cls.__name__} by {kwargs}: {'Yes' if result else 'No'}", "model")
        return result
    
    @classmethod
    def where(cls, **kwargs):
        """Find all records matching criteria"""
        session = cls.session()
        results = session.query(cls).filter_by(**kwargs).all()
        log_debug(f"Found {len(results)} {cls.__name__} records matching {kwargs}", "model")
        return results
    
    @classmethod
    def all(cls):
        """Get all records"""
        session = cls.session()
        results = session.query(cls).all()
        log_debug(f"Loaded all {len(results)} {cls.__name__} records", "model")
        return results
    
    @classmethod
    def count(cls):
        """Count all records"""
        session = cls.session()
        count = session.query(cls).count()
        log_debug(f"{cls.__name__} count: {count}", "model")
        return count

class Tournament(Base, BaseModel):
    """Tournament from start.gg API with comprehensive data"""
    __tablename__ = 'tournaments'
    
    # Primary data
    id = Column(String, primary_key=True)  # start.gg tournament ID
    name = Column(String, nullable=False)
    
    # Attendance and sizing
    num_attendees = Column(Integer, default=0)
    
    # Dates and timing
    start_at = Column(Integer)  # Unix timestamp
    end_at = Column(Integer)  # Unix timestamp
    registration_closes_at = Column(Integer)  # Unix timestamp
    timezone = Column(String)
    
    # Location data
    venue_name = Column(String)
    venue_address = Column(String)
    city = Column(String)
    country_code = Column(String)
    postal_code = Column(String)
    tournament_state = Column(Integer, default=0)  # Tournament status (1,2,3...)
    addr_state = Column(String)  # Address state/province
    lat = Column(String)  # Latitude
    lng = Column(String)  # Longitude
    
    # Owner information
    owner_id = Column(String)  # Tournament owner ID
    owner_name = Column(String)  # Owner display name
    
    # Contact and URLs
    primary_contact = Column(String)
    primary_contact_type = Column(String)  # Type of primary contact
    short_slug = Column(String)  # Short URL slug
    slug = Column(String)  # Full URL slug
    url = Column(String)  # Full start.gg URL
    
    # Registration and settings
    is_registration_open = Column(Integer, default=0)  # Boolean as int
    currency = Column(String)
    has_offline_events = Column(Integer, default=1)  # Boolean as int
    has_online_events = Column(Integer, default=0)  # Boolean as int
    tournament_type = Column(Integer)  # Tournament type enum
    
    # Additional metadata
    sync_timestamp = Column(Integer)  # When we last synced
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    # Removed attendance_records relationship - table deleted
    placements = relationship("TournamentPlacement", back_populates="tournament", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tournament(id='{self.id}', name='{self.name}', attendees={self.num_attendees})>"
    
    def __str__(self):
        return f"Tournament: {self.name} ({self.num_attendees} attendees)"
    
    @property
    def organization(self):
        """Get the organization that runs this tournament based on contact matching"""
        if not self.primary_contact:
            return None
        from database_utils import normalize_contact
        normalized = normalize_contact(self.primary_contact)
        
        # Find organization that has this normalized contact
        from database_utils import get_session
        with get_session() as session:
            orgs = session.query(Organization).all()
            for org in orgs:
                # Check if any of the org's contacts match
                for contact in org.contacts:
                    if normalize_contact(contact.get('value', '')) == normalized:
                        return org
        return None
    
    @classmethod
    def by_contact(cls, contact):
        """Find tournaments by contact (compares normalized values)"""
        from database_utils import normalize_contact, get_session
        normalized = normalize_contact(contact)
        
        with get_session() as session:
            tournaments = session.query(cls).all()
            matching = []
            for t in tournaments:
                if t.primary_contact and normalize_contact(t.primary_contact) == normalized:
                    matching.append(t)
            return matching
    
    @classmethod
    def finished(cls):
        """Get finished tournaments only"""
        session = cls.session()
        results = session.query(cls).filter(
            cls.num_attendees > 0,
            cls.tournament_state >= 3
        ).all()
        log_debug(f"Found {len(results)} finished tournaments", "model")
        return results
    
    def is_finished(self):
        """Check if tournament is finished"""
        return self.num_attendees > 0 and self.tournament_state >= 3
    
    @property
    def top_8(self):
        """Get top 8 placements for this tournament"""
        return sorted(self.placements, key=lambda p: p.placement)[:8]
    
    @property
    def winner(self):
        """Get tournament winner (1st place)"""
        first_place = next((p for p in self.placements if p.placement == 1), None)
        return first_place.player if first_place else None
    
    def add_placement(self, player_startgg_id, gamer_tag, placement, prize_amount=0):
        """Add a top 8 placement"""
        # Get or create player using database_utils pattern
        player = Player.get_or_create(player_startgg_id, gamer_tag)
        
        # Check if placement already exists
        existing = TournamentPlacement.find_by(tournament_id=self.id, player_id=player.id)
        if existing:
            existing.placement = placement
            existing.prize_amount = prize_amount
            existing.save()
            return existing
        else:
            placement_record = TournamentPlacement(
                tournament_id=self.id,
                player_id=player.id,
                placement=placement,
                prize_amount=prize_amount
            )
            placement_record.save()
            return placement_record
    
    def get_top_8_dict(self):
        """Get top 8 as dictionary for storage efficiency"""
        top_8_dict = {}
        for placement in self.top_8:
            top_8_dict[placement.placement] = {
                'player_tag': placement.player.gamer_tag,
                'player_startgg_id': placement.player.startgg_id,
                'prize': placement.prize_amount
            }
        return top_8_dict
    
    def show_top_8(self):
        """Display top 8 placements organized by event"""
        print(f"\n{self.name} Top 8:")
        if not self.placements:
            print("  No standings data")
            return
        
        # Group by event
        events = {}
        for p in self.placements:
            event = p.event_name or "Main Event"
            if event not in events:
                events[event] = []
            events[event].append(p)
        
        for event_name, placements in events.items():
            print(f"  {event_name}:")
            sorted_placements = sorted(placements, key=lambda x: x.placement)
            for p in sorted_placements:
                print(f"    {p.placement}. {p.player.gamer_tag}")
        print()

class Organization(Base, BaseModel):
    """Organization that runs tournaments"""
    __tablename__ = 'organizations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    display_name = Column(String, nullable=False)
    contacts_json = Column(String, default='[]')  # JSON array of contact objects
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Removed relationships to deleted tables
    
    @property
    def contacts(self):
        """Get contacts as a Python list"""
        import json
        try:
            return json.loads(self.contacts_json or '[]')
        except:
            return []
    
    @contacts.setter
    def contacts(self, value):
        """Set contacts from a Python list"""
        import json
        self.contacts_json = json.dumps(value)
    
    def add_contact(self, contact_type, contact_value):
        """Add a new contact"""
        contacts = self.contacts
        contacts.append({'type': contact_type, 'value': contact_value})
        self.contacts = contacts
    
    def remove_contact(self, index):
        """Remove a contact by index"""
        contacts = self.contacts
        if 0 <= index < len(contacts):
            contacts.pop(index)
            self.contacts = contacts
    
    def update_contact(self, index, contact_type, contact_value):
        """Update a contact by index"""
        contacts = self.contacts
        if 0 <= index < len(contacts):
            contacts[index] = {'type': contact_type, 'value': contact_value}
            self.contacts = contacts
    
    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.display_name}')>"
    
    def __str__(self):
        return f"Organization: {self.display_name}"
    
    @property
    def tournaments(self):
        """Get all tournaments for this organization by matching contacts"""
        from database_utils import normalize_contact, get_session
        
        # Collect all normalized contacts for this org
        org_contacts_normalized = set()
        for contact in self.contacts:
            value = contact.get('value', '')
            if value:
                org_contacts_normalized.add(normalize_contact(value))
        
        # Find tournaments that match any of these contacts
        matching = []
        with get_session() as session:
            tournaments = session.query(Tournament).all()
            for t in tournaments:
                if t.primary_contact:
                    t_normalized = normalize_contact(t.primary_contact)
                    if t_normalized in org_contacts_normalized:
                        matching.append(t)
        
        return matching
    
    @property
    def total_attendance(self):
        """Calculate total attendance across all tournaments"""
        return sum(t.num_attendees or 0 for t in self.tournaments)
    
    @property
    def tournament_count(self):
        """Count of tournaments"""
        return len(self.tournaments)
    
    
    @classmethod
    def get_or_create(cls, normalized_key, display_name=None):
        """Get existing organization or create new one"""
        org = cls.find_by(normalized_key=normalized_key)
        
        if not org:
            if not display_name:
                display_name = normalized_key
            
            org = cls(
                normalized_key=normalized_key,
                display_name=display_name
            )
            org.save()
            log_debug(f"Created organization: {display_name}", "model")
        
        return org
    
    @classmethod
    def top_by_attendance(cls, limit=20):
        """Get organizations ranked by attendance"""
        session = cls.session()
        
        from sqlalchemy import desc, func
        results = session.query(cls).join(AttendanceRecord).group_by(cls.id).order_by(
            desc(func.sum(AttendanceRecord.attendance))
        ).limit(limit).all()
        
        log_debug(f"Loaded top {len(results)} organizations by attendance", "model")
        return results

class Player(Base, BaseModel):
    """Player in tournaments"""
    __tablename__ = 'players'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    startgg_id = Column(String, unique=True, index=True)  # start.gg player ID
    gamer_tag = Column(String, nullable=False)
    name = Column(String)  # Real name (if available)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    placements = relationship("TournamentPlacement", back_populates="player", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Player(tag='{self.gamer_tag}', id={self.startgg_id})>"
    
    def __str__(self):
        return self.gamer_tag
    
    @classmethod
    def get_or_create(cls, startgg_id, gamer_tag, name=None):
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
    
    @property
    def tournaments_won(self):
        """Get tournaments this player won (1st place)"""
        return [p.tournament for p in self.placements if p.placement == 1]
    
    @property
    def total_winnings(self):
        """Calculate total prize money"""
        return sum(p.prize_amount for p in self.placements if p.prize_amount)

# Removed OrganizationContact and AttendanceRecord classes - tables deleted
    

class TournamentPlacement(Base, BaseModel):
    """Top 8 placements in tournaments"""
    __tablename__ = 'tournament_placements'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tournament_id = Column(String, ForeignKey('tournaments.id'), nullable=False)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    placement = Column(Integer, nullable=False)  # 1-8 for top 8
    prize_amount = Column(Integer, default=0)  # Prize money in cents
    event_name = Column(String)  # Name of the specific event (e.g. "SF6 Singles", "SF6 Doubles")
    event_id = Column(String)  # start.gg event ID
    
    recorded_at = Column(DateTime, default=func.now())
    
    # Relationships
    tournament = relationship("Tournament", back_populates="placements")
    player = relationship("Player", back_populates="placements")
    
    # Unique constraint per event (player can place in multiple events per tournament)
    __table_args__ = (
        Index('ix_tournament_player_event', tournament_id, player_id, event_id, unique=True),
    )
    
    def __repr__(self):
        event_info = f" ({self.event_name})" if self.event_name else ""
        return f"<Placement(tournament={self.tournament_id}, player={self.player.gamer_tag if self.player else 'Unknown'}, place={self.placement}{event_info})>"
    
    def __str__(self):
        return f"{self.placement}. {self.player.gamer_tag if self.player else 'Unknown'}"
    
    @property
    def prize_dollars(self):
        """Prize amount in dollars"""
        return self.prize_amount / 100.0 if self.prize_amount else 0.0
    
    @property 
    def is_singles(self):
        """Check if this is a singles event"""
        if not self.event_name:
            return True  # Default assumption
        
        event_name = self.event_name.lower()
        # Check for doubles/teams indicators
        if any(keyword in event_name for keyword in ['doubles', 'teams', 'crew', '2v2', 'tag']):
            return False
        return True

# Utility functions (moved from database_utils to avoid circular imports)
def normalize_contact(contact):
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

def get_display_name_from_contact(contact):
    """Get display name from contact"""
    if not contact:
        return "Unknown"
    
    # If it's not email or discord, use as display name
    if '@' not in contact and 'discord' not in contact.lower():
        return contact
    
    return contact

def determine_contact_type(contact):
    """Determine contact type"""
    if '@' in contact:
        return 'email'
    elif 'discord' in contact.lower():
        return 'discord'
    else:
        return 'name'

# Test functions for model validation
def test_models():
    """Test model operations with session-safe functions"""
    log_info("=" * 60, "test")
    log_info("TESTING MODEL OPERATIONS", "test")
    log_info("=" * 60, "test")
    
    try:
        # Test 1: Create tournament
        log_info("TEST 1: Create tournament", "test")
        tournament = Tournament(
            id="test_model_123",
            name="Test Model Tournament",
            num_attendees=50,
            primary_contact="test@model.com",
            normalized_contact=normalize_contact("test@model.com"),
            tournament_state=3
        )
        tournament.save()
        log_info("✅ Tournament created", "test")
        
        # Test 2: Create organization
        log_info("TEST 2: Create organization", "test")
        org = Organization.get_or_create("test@model.com", "Test Model Organization")
        org.add_contact("test@model.com", "email", True)
        log_info("✅ Organization created", "test")
        
        # Test 3: Record attendance
        log_info("TEST 3: Record attendance", "test")
        AttendanceRecord.record_attendance(tournament.id, org.id, 50)
        log_info("✅ Attendance recorded", "test")
        
        # Test 4: Test queries and relationships
        log_info("TEST 4: Test queries", "test")
        found_tournament = Tournament.find("test_model_123")
        if found_tournament:
            log_info(f"✅ Found tournament: {found_tournament.name}", "test")
        
        top_orgs = Organization.top_by_attendance(5)
        log_info(f"✅ Found {len(top_orgs)} top organizations", "test")
        
        # Test 5: Test session consistency
        log_info("TEST 5: Test session consistency", "test")
        org_before = Organization.find_by(normalized_key="test@model.com")
        original_name = org_before.display_name
        
        # Change name and save
        org_before.display_name = "Updated Model Test Org"
        org_before.save()
        
        # Load again and verify
        org_after = Organization.find_by(normalized_key="test@model.com") 
        if org_after.display_name == "Updated Model Test Org":
            log_info("✅ Session consistency verified", "test")
        else:
            log_error(f"❌ Session inconsistency: Expected 'Updated Model Test Org', Got '{org_after.display_name}'", "test")
        
        # Cleanup
        log_info("Cleaning up test data", "test")
        found_tournament.delete()
        org_after.delete()
        
        log_info("✅ Model tests completed successfully", "test")
        
    except Exception as e:
        log_error(f"Model test failed: {e}", "test")
        import traceback
        traceback.print_exc()

def test_model_relationships():
    """Test model relationships and properties"""
    log_info("=" * 60, "test")
    log_info("TESTING MODEL RELATIONSHIPS", "test")  
    log_info("=" * 60, "test")
    
    try:
        # Create test data
        tournament = Tournament(
            id="rel_test_123",
            name="Relationship Test Tournament",
            num_attendees=100,
            normalized_contact="relationships@test.com",
            tournament_state=3
        )
        tournament.save()
        
        org = Organization.get_or_create("relationships@test.com", "Relationships Test Org")
        
        # Test attendance relationship
        AttendanceRecord.record_attendance(tournament.id, org.id, 100)
        
        # Create test player and placement
        player = Player.get_or_create("player123", "TestPlayer", "Test Player Name")
        
        placemt = TournamentPlacement(
            tournament_id=tournament.id,
            player_id=player.id,
            placement=1,
            event_name="Test Event",
            event_id="event123"
        )
        placement.save()
        
        # Test relationships
        log_info("Testing tournament relationships", "test")
        
        # Tournament -> Organization
        tournament_org = tournament.organization
        if tournament_org and tournament_org.normalized_key == "relationships@test.com":
            log_info("✅ Tournament -> Organization relationship works", "test")
        else:
            log_error("❌ Tournament -> Organization relationship failed", "test")
        
        # Tournament -> Placements
        if tournament.top_8 and len(tournament.top_8) >= 1:
            log_info("✅ Tournament -> Placements relationship works", "test")
        else:
            log_error("❌ Tournament -> Placements relationship failed", "test")
        
        # Organization -> Tournaments
        org_tournaments = org.tournaments
        if org_tournaments and len(org_tournaments) >= 1:
            log_info("✅ Organization -> Tournaments relationship works", "test")
        else:
            log_error("❌ Organization -> Tournaments relationship failed", "test")
        
        # Organization properties
        if org.total_attendance == 100:
            log_info("✅ Organization.total_attendance property works", "test")
        else:
            log_error(f"❌ Organization.total_attendance failed: got {org.total_attendance}, expected 100", "test")
        
        if org.tournament_count == 1:
            log_info("✅ Organization.tournament_count property works", "test")
        else:
            log_error(f"❌ Organization.tournament_count failed: got {org.tournament_count}, expected 1", "test")
        
        # Player -> Placements
        player_placements = player.placements
        if player_placements and len(player_placements) >= 1:
            log_info("✅ Player -> Placements relationship works", "test")
        else:
            log_error("❌ Player -> Placements relationship failed", "test")
        
        # Cleanup
        placement.delete()
        player.delete()
        tournament.delete()
        org.delete()
        
        log_info("✅ Relationship tests completed", "test")
        
    except Exception as e:
        log_error(f"Relationship test failed: {e}", "test")
        import traceback
        traceback.print_exc()

def run_model_tests():
    """Run all model tests"""
    try:
        # Initialize logging
        from log_utils import init_logging, LogLevel
        init_logging(console=True, level=LogLevel.DEBUG, debug_file="model_test.txt")
        
        log_info("Starting model tests", "test")
        
        # Initialize database using centralized function
        from database_utils import init_db
        init_db()
        
        # Run test suites
        test_models()
        print()  # Spacing
        test_model_relationships()
        
        log_info("All model tests completed - check model_test.txt for details", "test")
        
    except Exception as e:
        log_error(f"Model test suite failed: {e}", "test")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Running tournament model tests...")
    run_model_tests()

