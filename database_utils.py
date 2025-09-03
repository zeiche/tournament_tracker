"""
database_utils.py - Database Access Layer
Centralized database operations - all database access goes through this module
"""
import os
import re
from datetime import datetime
from contextlib import contextmanager
from sqlalchemy import create_engine, func, case, or_, desc
from sqlalchemy.orm import sessionmaker, scoped_session

# Global session registry
engine = None
Session = None

def init_db(database_url=None):
    """Initialize database connection"""
    global engine, Session
    
    if database_url is None:
        # Use absolute path for database to work from any directory
        db_path = os.path.join(os.path.dirname(__file__), 'tournament_tracker.db')
        database_url = os.getenv('DATABASE_URL', f'sqlite:///{db_path}')
    
    engine = create_engine(database_url, echo=False)
    Session = scoped_session(sessionmaker(bind=engine))
    
    # Import models after Session is created to avoid circular imports
    from tournament_models import Base
    Base.metadata.create_all(engine)
    
    return engine, Session

@contextmanager
def get_session():
    """Context manager for database sessions"""
    if Session is None:
        # Auto-initialize if not already done
        init_db()
    
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

@contextmanager
def batch_session():
    """Context manager for batch database operations"""
    if Session is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
        
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def clear_session_cache():
    """Clear SQLAlchemy session cache"""
    if Session:
        Session.remove()

# Contact normalization utilities
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

# Organization operations
def get_all_organizations():
    """Get all organizations"""
    with get_session() as session:
        from tournament_models import Organization
        orgs = session.query(Organization).all()
        return [_org_to_dict(org) for org in orgs]

def find_organization_by_key(normalized_key):
    """Find organization by normalized key"""
    with get_session() as session:
        from tournament_models import Organization
        org = session.query(Organization).filter_by(normalized_key=normalized_key).first()
        return _org_to_dict(org) if org else None

def get_organizations_by_attendance(limit=None):
    """Get organizations ranked by attendance"""
    with get_session() as session:
        from tournament_models import Organization, Tournament
        # Sum attendance from tournaments grouped by organization
        query = session.query(
            Organization,
            func.sum(Tournament.num_attendees).label('total_attendance'),
            func.count(Tournament.id).label('tournament_count')
        ).join(
            Tournament, Tournament.normalized_contact == Organization.normalized_key
        ).group_by(Organization.id).order_by(
            func.sum(Tournament.num_attendees).desc()
        )
        
        if limit:
            query = query.limit(limit)
            
        results = query.all()
        org_dicts = []
        for org, total_attendance, tournament_count in results:
            org_dict = _org_to_dict(org)
            org_dict['total_attendance'] = total_attendance or 0
            org_dict['tournament_count'] = tournament_count or 0
            org_dicts.append(org_dict)
        return org_dicts

def save_organization_name(normalized_key, new_display_name):
    """Save organization display name change"""
    with get_session() as session:
        from tournament_models import Organization
        org = session.query(Organization).filter_by(normalized_key=normalized_key).first()
        if org:
            org.display_name = new_display_name
            return True
        return False

def get_or_create_organization(normalized_key, display_name=None):
    """Get existing organization or create new one"""
    with get_session() as session:
        from tournament_models import Organization
        org = session.query(Organization).filter_by(normalized_key=normalized_key).first()
        
        if not org:
            if not display_name:
                display_name = normalized_key
            
            org = Organization(
                normalized_key=normalized_key,
                display_name=display_name
            )
            session.add(org)
        
        return _org_to_dict(org)

def _org_to_dict(org):
    """Convert organization model to dictionary"""
    if not org:
        return None
        
    return {
        'id': org.id,
        'normalized_key': org.normalized_key,
        'display_name': org.display_name,
        'tournament_count': org.tournament_count,
        'total_attendance': org.total_attendance,
        'contacts': [contact.contact_value for contact in org.contacts],
        'created_at': org.created_at,
        'updated_at': org.updated_at
    }

# Tournament operations
def get_all_tournaments():
    """Get all tournaments"""
    with get_session() as session:
        from tournament_models import Tournament
        tournaments = session.query(Tournament).all()
        return [_tournament_to_dict(t) for t in tournaments]

def find_tournament_by_id(tournament_id):
    """Find tournament by ID"""
    with get_session() as session:
        from tournament_models import Tournament
        tournament = session.query(Tournament).filter_by(id=tournament_id).first()
        return _tournament_to_dict(tournament) if tournament else None

def get_finished_tournaments():
    """Get finished tournaments only"""
    with get_session() as session:
        from tournament_models import Tournament
        tournaments = session.query(Tournament).filter(
            Tournament.num_attendees > 0,
            Tournament.tournament_state >= 3
        ).all()
        return [_tournament_to_dict(t) for t in tournaments]

def get_tournaments_by_contact(normalized_contact):
    """Find tournaments by contact"""
    with get_session() as session:
        from tournament_models import Tournament
        tournaments = session.query(Tournament).filter_by(normalized_contact=normalized_contact).all()
        return [_tournament_to_dict(t) for t in tournaments]

def get_tournament_slugs(normalized_key):
    """Get tournament slugs for start.gg lookup"""
    with get_session() as session:
        from tournament_models import Tournament
        tournaments = session.query(Tournament).filter_by(normalized_contact=normalized_key).all()
        
        finished_tournaments = []
        for t in tournaments:
            num_attendees = t.num_attendees or 0
            tournament_state = t.tournament_state or 0
            if num_attendees > 0 and tournament_state >= 3:
                finished_tournaments.append(t)
        
        slugs = []
        for tournament in finished_tournaments:
            if tournament.short_slug:
                slugs.append(tournament.short_slug)
            elif tournament.slug:
                slugs.append(tournament.slug)
        
        unique_slugs = list(set(slugs))
        unique_slugs.sort(key=len)
        return unique_slugs[:3]

def _tournament_to_dict(tournament):
    """Convert tournament model to dictionary"""
    if not tournament:
        return None
        
    return {
        'id': tournament.id,
        'name': tournament.name,
        'num_attendees': tournament.num_attendees,
        'start_at': tournament.start_at,
        'end_at': tournament.end_at,
        'normalized_contact': tournament.normalized_contact,
        'primary_contact': tournament.primary_contact,
        'tournament_state': tournament.tournament_state,
        'short_slug': tournament.short_slug,
        'slug': tournament.slug,
        'url': tournament.url
    }

# Statistics operations
def get_summary_stats():
    """Get overall summary statistics"""
    with get_session() as session:
        from tournament_models import Organization, Tournament, Player
        total_orgs = session.query(Organization).count()
        total_tournaments = session.query(Tournament).count()
        total_players = session.query(Player).count()
        total_attendance = session.query(func.coalesce(func.sum(Tournament.num_attendees), 0)).scalar()
        
        return {
            'total_organizations': total_orgs,
            'total_tournaments': total_tournaments,
            'total_players': total_players,
            'total_attendance': int(total_attendance)
        }

def get_attendance_rankings(limit=None):
    """Get attendance rankings for reporting"""
    with get_session() as session:
        from tournament_models import Organization, Tournament
        # Sum attendance from tournaments grouped by organization
        query = session.query(
            Organization,
            func.sum(Tournament.num_attendees).label('total_attendance'),
            func.count(Tournament.id).label('tournament_count')
        ).join(
            Tournament, Tournament.normalized_contact == Organization.normalized_key
        ).group_by(Organization.id).order_by(
            func.sum(Tournament.num_attendees).desc()
        )
        
        if limit:
            query = query.limit(limit)
            
        results = query.all()
        
        rankings = []
        for org, total_attendance, tournament_count in results:
            rankings.append({
                'display_name': org.display_name,
                'normalized_key': org.normalized_key,
                'tournament_count': tournament_count or 0,
                'total_attendance': total_attendance or 0,
                'contacts': []  # Contacts table was removed
            })
        
        return rankings

# Player operations
def get_or_create_player(startgg_id, gamer_tag, name=None):
    """Get existing player or create new one"""
    with get_session() as session:
        from tournament_models import Player
        player = session.query(Player).filter_by(startgg_id=startgg_id).first()
        
        if not player:
            player = Player(
                startgg_id=startgg_id,
                gamer_tag=gamer_tag,
                name=name
            )
            session.add(player)
        else:
            # Update info if provided
            if gamer_tag and player.gamer_tag != gamer_tag:
                player.gamer_tag = gamer_tag
            if name and player.name != name:
                player.name = name
        
        return {
            'id': player.id,
            'startgg_id': player.startgg_id,
            'gamer_tag': player.gamer_tag,
            'name': player.name
        }

# Attendance operations
def record_attendance(tournament_id, organization_id, attendance):
    """Record or update attendance"""
    with get_session() as session:
        from tournament_models import AttendanceRecord
        existing = session.query(AttendanceRecord).filter_by(
            tournament_id=tournament_id,
            organization_id=organization_id
        ).first()
        
        if existing:
            if existing.attendance != attendance:
                existing.attendance = attendance
                existing.updated_at = datetime.now()
        else:
            record = AttendanceRecord(
                tournament_id=tournament_id,
                organization_id=organization_id,
                attendance=attendance
            )
            session.add(record)

# Deduplication operations
def find_duplicate_organizations():
    """Find potential duplicate organizations"""
    with get_session() as session:
        from tournament_models import Organization
        all_orgs = session.query(Organization).all()
        
        duplicates = {}
        for org in all_orgs:
            # Group by similar characteristics
            name_key = org.display_name.lower().strip()
            
            # Check for exact name matches
            if name_key not in duplicates:
                duplicates[name_key] = []
            duplicates[name_key].append(org)
        
        # Find groups with multiple organizations
        duplicate_groups = []
        for name_key, orgs in duplicates.items():
            if len(orgs) > 1:
                duplicate_groups.append({
                    'name_pattern': name_key,
                    'organizations': [_org_to_dict(org) for org in orgs],
                    'total_attendance': sum(org.total_attendance for org in orgs),
                    'total_tournaments': sum(org.tournament_count for org in orgs)
                })
        
        return duplicate_groups

def merge_organizations(primary_normalized_key, duplicate_normalized_keys):
    """Merge duplicate organizations into primary organization"""
    with get_session() as session:
        from tournament_models import Organization, AttendanceRecord, OrganizationContact, Tournament
        primary_org = session.query(Organization).filter_by(normalized_key=primary_normalized_key).first()
        if not primary_org:
            return False, "Primary organization not found"
        
        merge_stats = {
            'attendance_records_moved': 0,
            'contacts_merged': 0,
            'organizations_deleted': 0
        }
        
        for dup_key in duplicate_normalized_keys:
            dup_org = session.query(Organization).filter_by(normalized_key=dup_key).first()
            if not dup_org:
                continue
            
            # Move attendance records
            attendance_records = session.query(AttendanceRecord).filter_by(organization_id=dup_org.id).all()
            for record in attendance_records:
                # Check if primary org already has record for this tournament
                existing = session.query(AttendanceRecord).filter_by(
                    tournament_id=record.tournament_id,
                    organization_id=primary_org.id
                ).first()
                
                if existing:
                    # Merge attendance counts
                    existing.attendance = max(existing.attendance, record.attendance)
                    session.delete(record)
                else:
                    # Move record to primary org
                    record.organization_id = primary_org.id
                
                merge_stats['attendance_records_moved'] += 1
            
            # Merge contacts
            contacts = session.query(OrganizationContact).filter_by(organization_id=dup_org.id).all()
            for contact in contacts:
                # Check if primary org already has this contact
                existing = session.query(OrganizationContact).filter_by(
                    organization_id=primary_org.id,
                    contact_value=contact.contact_value
                ).first()
                
                if not existing:
                    contact.organization_id = primary_org.id
                    merge_stats['contacts_merged'] += 1
                else:
                    session.delete(contact)
            
            # Update tournament references
            tournaments = session.query(Tournament).filter_by(normalized_contact=dup_key).all()
            for tournament in tournaments:
                tournament.normalized_contact = primary_normalized_key
            
            # Delete duplicate organization
            session.delete(dup_org)
            merge_stats['organizations_deleted'] += 1
        
        return True, merge_stats

def deduplicate_organizations():
    """Automatic deduplication of organizations"""
    duplicate_groups = find_duplicate_organizations()
    
    if not duplicate_groups:
        return 0, "No duplicates found"
    
    total_merged = 0
    merge_results = []
    
    for group in duplicate_groups:
        orgs = group['organizations']
        if len(orgs) < 2:
            continue
        
        # Use organization with highest attendance as primary
        primary_org = max(orgs, key=lambda x: x['total_attendance'])
        duplicate_keys = [org['normalized_key'] for org in orgs if org['normalized_key'] != primary_org['normalized_key']]
        
        if duplicate_keys:
            success, stats = merge_organizations(primary_org['normalized_key'], duplicate_keys)
            if success:
                total_merged += len(duplicate_keys)
                merge_results.append({
                    'primary_name': primary_org['display_name'],
                    'merged_count': len(duplicate_keys),
                    'stats': stats
                })
    
    return total_merged, merge_results

def run_deduplication():
    """Interactive deduplication with user confirmation"""
    print("Starting organization deduplication...")
    
    # Find duplicates first
    print("Scanning for duplicate organizations...")
    duplicate_groups = find_duplicate_organizations()
    
    if not duplicate_groups:
        print("No duplicate organizations found")
        return
    
    print(f"Found {len(duplicate_groups)} duplicate groups:")
    for i, group in enumerate(duplicate_groups, 1):
        orgs = group['organizations']
        print(f"   {i}. '{group['name_pattern']}' - {len(orgs)} organizations, {group['total_attendance']} total attendance")
        for org in orgs:
            print(f"      - {org['normalized_key']} ({org['total_attendance']} attendance)")
    
    # Confirm deduplication
    response = input(f"\nMerge {len(duplicate_groups)} duplicate groups? (y/N): ")
    if response.lower() != 'y':
        print("Deduplication cancelled")
        return
    
    # Perform deduplication
    print("Merging duplicate organizations...")
    total_merged, results = deduplicate_organizations()
    
    if total_merged > 0:
        print(f"Successfully merged {total_merged} duplicate organizations:")
        for result in results:
            print(f"   - {result['primary_name']}: merged {result['merged_count']} duplicates")
            stats = result['stats']
            print(f"     Moved {stats['attendance_records_moved']} attendance records")
            print(f"     Merged {stats['contacts_merged']} contacts")
            print(f"     Deleted {stats['organizations_deleted']} duplicate records")
        
        # Clear session cache so editor sees clean data
        clear_session_cache()
        print("Session cache cleared - editor will show deduplicated data")
        
    else:
        print("No organizations were merged")


def get_player_rankings(limit=50, event_type='all', min_tournaments=2):
    """
    Get player rankings based on placement points
    
    Args:
        limit: Number of top players to return
        event_type: 'all', 'singles', 'doubles', or specific event name
        min_tournaments: Minimum tournaments to qualify for ranking
    
    Returns:
        List of dicts with player rankings
    """
    from tournament_models import Player, TournamentPlacement
    
    # Points system for placements - simple descending
    PLACEMENT_POINTS = {
        1: 8,  # 1st place
        2: 7,  # 2nd place  
        3: 6,  # 3rd place
        4: 5,  # 4th place
        5: 4,  # 5th place
        6: 3,  # 6th place
        7: 2,  # 7th place
        8: 1   # 8th place
    }
    
    with get_session() as session:
        # Build query
        query = session.query(
            Player,
            func.sum(
                case(
                    *[(TournamentPlacement.placement == p, PLACEMENT_POINTS[p]) 
                      for p in PLACEMENT_POINTS.keys()],
                    else_=0
                )
            ).label('total_points'),
            func.count(TournamentPlacement.id).label('tournament_count'),
            func.sum(case((TournamentPlacement.placement == 1, 1), else_=0)).label('first_places'),
            func.sum(case((TournamentPlacement.placement == 2, 1), else_=0)).label('second_places'),
            func.sum(case((TournamentPlacement.placement == 3, 1), else_=0)).label('third_places')
        ).join(
            TournamentPlacement
        )
        
        # Filter by event type
        if event_type == 'singles':
            # Filter for singles events
            query = query.filter(
                ~TournamentPlacement.event_name.ilike('%doubles%'),
                ~TournamentPlacement.event_name.ilike('%teams%'),
                ~TournamentPlacement.event_name.ilike('%crew%'),
                ~TournamentPlacement.event_name.ilike('%2v2%'),
                ~TournamentPlacement.event_name.ilike('%tag%')
            )
        elif event_type == 'doubles':
            # Filter for doubles/teams events
            query = query.filter(
                or_(
                    TournamentPlacement.event_name.ilike('%doubles%'),
                    TournamentPlacement.event_name.ilike('%teams%'),
                    TournamentPlacement.event_name.ilike('%2v2%'),
                    TournamentPlacement.event_name.ilike('%tag%')
                )
            )
        elif event_type != 'all':
            # Filter by specific event name
            query = query.filter(TournamentPlacement.event_name.ilike(f'%{event_type}%'))
        
        # Group by player and filter by minimum tournaments
        query = query.group_by(Player.id)
        query = query.having(func.count(TournamentPlacement.id) >= min_tournaments)
        
        # Order by total points
        query = query.order_by(desc('total_points'))
        query = query.limit(limit)
        
        results = query.all()
        
        rankings = []
        for rank, (player, points, tournaments, firsts, seconds, thirds) in enumerate(results, 1):
            rankings.append({
                'rank': rank,
                'player_id': player.id,
                'gamer_tag': player.gamer_tag,
                'name': player.name,
                'total_points': int(points),
                'tournament_count': tournaments,
                'first_places': firsts,
                'second_places': seconds,
                'third_places': thirds,
                'avg_points': round(points / tournaments, 1) if tournaments > 0 else 0
            })
        
        return rankings

