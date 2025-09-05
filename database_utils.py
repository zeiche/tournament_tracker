"""
database_utils.py - Database Access Layer
Centralized database operations - all database access goes through this module
"""
import os
import re
from datetime import datetime
from contextlib import contextmanager
from sqlalchemy import create_engine, func, case, or_, and_, desc, distinct
from sqlalchemy.orm import sessionmaker, scoped_session
from points_system import PointsSystem

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
        results = []
        for org in orgs:
            org_dict = _org_to_dict(org)
            # Calculate tournament count while in session
            org_dict['tournament_count'] = org.tournament_count
            org_dict['total_attendance'] = org.total_attendance
            results.append(org_dict)
        return results

# DEPRECATED - normalized_key no longer exists
# def find_organization_by_key(normalized_key):
#     pass

def get_organizations_by_attendance(limit=None):
    """Get organizations ranked by attendance"""
    with get_session() as session:
        from tournament_models import Organization, Tournament
        # Sum attendance from tournaments grouped by organization
        query = session.query(
            Organization,
            func.sum(Tournament.num_attendees).label('total_attendance'),
            func.count(Tournament.id).label('tournament_count')
        ).outerjoin(
            Tournament, Tournament.primary_contact.like('%' + Organization.display_name + '%')
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

def save_organization_name(org_id, new_display_name):
    """Save organization display name change"""
    with get_session() as session:
        from tournament_models import Organization
        org = session.get(Organization, org_id)
        if org:
            org.display_name = new_display_name
            session.commit()
            return True
        return False

# DEPRECATED - use editor_core.get_or_create_organization instead
# def get_or_create_organization(normalized_key, display_name=None):
#     pass

def _org_to_dict(org):
    """Convert organization model to dictionary"""
    if not org:
        return None
        
    return {
        'id': org.id,
        'display_name': org.display_name,
        'tournament_count': getattr(org, 'tournament_count', 0),
        'total_attendance': getattr(org, 'total_attendance', 0),
        'contacts': org.contacts if hasattr(org, 'contacts') else [],
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

# DEPRECATED - normalized_contact no longer exists
# def get_tournament_slugs(normalized_key):
#     pass

def get_tournament_slugs_by_org(org_id):
    """Get tournament slugs for an organization"""
    with get_session() as session:
        from tournament_models import Tournament, Organization
        org = session.query(Organization).filter_by(id=org_id).first()
        if not org:
            return []
        tournaments = []
        # Find tournaments that match any of the org's contacts
        for contact in org.contacts:
            if contact.get('value'):
                matching = session.query(Tournament).filter(
                    Tournament.primary_contact.like(f"%{contact['value']}%")
                ).all()
                tournaments.extend(matching)
        
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
        
        # Get all tournaments to calculate attendance
        all_tournaments = session.query(Tournament).all()
        
        # Group tournaments by their matching organizations
        org_attendance = {}
        
        for tournament in all_tournaments:
            # Find which org this tournament belongs to (if any)
            org_match = None
            primary_contact = tournament.primary_contact
            
            if primary_contact:
                # Check all organizations for a matching contact
                orgs = session.query(Organization).all()
                for org in orgs:
                    for contact in org.contacts:
                        if contact.get('value') and contact['value'].lower() in primary_contact.lower():
                            org_match = org.display_name
                            break
                    if org_match:
                        break
            
            # If no org match, use primary contact as org name
            if not org_match:
                org_match = primary_contact or 'Unknown'
            
            # Add to totals
            if org_match not in org_attendance:
                org_attendance[org_match] = {
                    'display_name': org_match,
                    'tournament_count': 0,
                    'total_attendance': 0,
                    'tournaments': []
                }
            
            org_attendance[org_match]['tournament_count'] += 1
            org_attendance[org_match]['total_attendance'] += tournament.num_attendees or 0
            org_attendance[org_match]['tournaments'].append(tournament.name)
        
        # Convert to list and calculate averages
        rankings = []
        for org_name, data in org_attendance.items():
            rankings.append({
                'display_name': data['display_name'],
                'tournament_count': data['tournament_count'],
                'total_attendance': data['total_attendance'],
                'avg_attendance': data['total_attendance'] / data['tournament_count'] if data['tournament_count'] > 0 else 0
            })
        
        # Sort by total attendance
        rankings.sort(key=lambda x: x['total_attendance'], reverse=True)
        
        if limit:
            rankings = rankings[:limit]
        
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

# DEPRECATED - uses tables and columns that no longer exist
def merge_organizations_disabled():
    """Merge functionality disabled - needs reimplementation"""
    return False, "Merge functionality needs to be reimplemented"

def merge_organizations_old(primary_normalized_key, duplicate_normalized_keys):
    """DISABLED - references removed tables"""
    return False, "Function disabled - references removed tables"
    # Original function commented out:
    # with get_session() as session:
    #     from tournament_models import Organization, AttendanceRecord, OrganizationContact, Tournament
    #     primary_org = session.query(Organization).filter_by(normalized_key=primary_normalized_key).first()
    # Rest of function disabled

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
        duplicate_keys = [org['display_name'] for org in orgs if org['display_name'] != primary_org['display_name']]
        
        if duplicate_keys:
            # Merge functionality disabled
            success, stats = False, "Merge disabled"
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
            print(f"      - {org['display_name']} ({org['total_attendance']} attendance)")
    
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


def get_player_rankings(limit=50, event_type='all', event_filter=None):
    """
    Get player rankings based on placement points
    Only counts events with at least 4 players
    
    Args:
        limit: Number of top players to return
        event_type: 'all', 'singles', 'doubles' (deprecated, use event_filter)
        event_filter: Specific event name to filter by (e.g., 'Ultimate Singles')
    
    Returns:
        List of dicts with player rankings
    """
    from tournament_models import Player, TournamentPlacement, Tournament
    
    # Use centralized points system - SINGLE SOURCE OF TRUTH
    points_case = PointsSystem.get_sql_case_expression()
    
    with get_session() as session:
        # First, get events with at least 4 players
        # Subquery to count players per event in each tournament
        event_player_counts = session.query(
            TournamentPlacement.tournament_id,
            TournamentPlacement.event_name,
            func.count(distinct(TournamentPlacement.player_id)).label('player_count')
        ).group_by(
            TournamentPlacement.tournament_id,
            TournamentPlacement.event_name
        ).subquery()
        
        # Build main query - join with valid events (4+ players)
        query = session.query(
            Player,
            func.sum(points_case).label('total_points'),
            func.count(TournamentPlacement.id).label('tournament_count'),
            func.sum(case((TournamentPlacement.placement == 1, 1), else_=0)).label('first_places'),
            func.sum(case((TournamentPlacement.placement == 2, 1), else_=0)).label('second_places'),
            func.sum(case((TournamentPlacement.placement == 3, 1), else_=0)).label('third_places')
        ).join(
            TournamentPlacement
        ).join(
            event_player_counts,
            and_(
                event_player_counts.c.tournament_id == TournamentPlacement.tournament_id,
                event_player_counts.c.event_name == TournamentPlacement.event_name,
                event_player_counts.c.player_count >= 4  # Only count events with 4+ players
            )
        )
        
        # Filter by event - prefer event_filter over event_type
        if event_filter:
            # Filter by exact event name
            query = query.filter(TournamentPlacement.event_name == event_filter)
        elif event_type == 'singles':
            # Legacy filter for singles events - now uses normalized names
            query = query.filter(
                TournamentPlacement.event_name.like('%Singles%')
            )
        elif event_type == 'doubles':
            # Legacy filter for doubles/teams events - now uses normalized names
            query = query.filter(
                TournamentPlacement.event_name.like('%Doubles%')
            )
        elif event_type != 'all':
            # Filter by specific event name (partial match)
            query = query.filter(TournamentPlacement.event_name.ilike(f'%{event_type}%'))
        
        # Group by player (removed min_tournaments filter)
        query = query.group_by(Player.id)
        
        # Order by total points
        query = query.order_by(desc('total_points'))
        query = query.limit(limit)
        
        results = query.all()
        
        rankings = []
        current_rank = 1
        prev_points = None
        
        for idx, (player, points, tournaments, firsts, seconds, thirds) in enumerate(results):
            # Handle tied ranks - players with same points get same rank
            if prev_points is not None and points < prev_points:
                current_rank = idx + 1  # Next rank is position in list
            # If same points as previous, keep same rank
            
            rankings.append({
                'rank': current_rank,
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
            
            prev_points = points
        
        return rankings


def find_player_ranking(player_name, event_filter=None, fuzzy_threshold=0.7):
    """
    Find a specific player's ranking and stats with fuzzy matching
    
    Args:
        player_name: Player's gamer tag (case insensitive partial/fuzzy match)
        event_filter: Optional event filter (e.g., 'Ultimate Singles')
        fuzzy_threshold: Minimum similarity score (0.0 to 1.0) for fuzzy matches
    
    Returns:
        Dict with player info or None if not found
    """
    from tournament_models import Player, TournamentPlacement, Tournament
    from difflib import SequenceMatcher
    
    # Get all rankings (no limit) to find the player
    all_rankings = get_player_rankings(limit=1000, event_filter=event_filter)
    
    # Search for player (case insensitive)
    player_lower = player_name.lower()
    
    # First try exact substring match
    for player_data in all_rankings:
        if player_lower in player_data['gamer_tag'].lower():
            # Also get their recent placements
            with get_session() as session:
                # Get recent placements for this player
                query = session.query(
                    TournamentPlacement.placement,
                    TournamentPlacement.event_name,
                    Tournament.name,
                    Tournament.start_at
                ).join(
                    Tournament
                ).filter(
                    TournamentPlacement.player_id == player_data['player_id']
                )
                
                if event_filter:
                    query = query.filter(TournamentPlacement.event_name == event_filter)
                
                recent_placements = query.order_by(
                    Tournament.start_at.desc()
                ).limit(5).all()
                
                player_data['recent_placements'] = [
                    {
                        'placement': p[0],
                        'event': p[1],
                        'tournament': p[2],
                        'date': p[3]
                    }
                    for p in recent_placements
                ]
            
            return player_data
    
    # If no exact match, try fuzzy matching
    best_match = None
    best_score = 0
    
    for player_data in all_rankings:
        # Calculate similarity between input and player name
        gamer_tag_lower = player_data['gamer_tag'].lower()
        
        # Try both full string similarity and substring similarity
        full_similarity = SequenceMatcher(None, player_lower, gamer_tag_lower).ratio()
        
        # Also check if the input is similar to the start of the gamer tag
        prefix_similarity = 0
        if len(player_lower) <= len(gamer_tag_lower):
            prefix_similarity = SequenceMatcher(None, player_lower, gamer_tag_lower[:len(player_lower)]).ratio()
        
        # Take the best similarity score
        similarity = max(full_similarity, prefix_similarity)
        
        if similarity > best_score and similarity >= fuzzy_threshold:
            best_score = similarity
            best_match = player_data
    
    # If we found a fuzzy match, get their recent placements
    if best_match:
        with get_session() as session:
            # Get recent placements for this player
            query = session.query(
                TournamentPlacement.placement,
                TournamentPlacement.event_name,
                Tournament.name,
                Tournament.start_at
            ).join(
                Tournament,
                TournamentPlacement.tournament_id == Tournament.id
            ).filter(
                TournamentPlacement.player_id == best_match['player_id']
            ).order_by(
                Tournament.start_at.desc()
            ).limit(5)
            
            recent_placements = query.all()
            
            best_match['recent_placements'] = [
                {
                    'placement': p[0],
                    'event': p[1],
                    'tournament': p[2],
                    'date': p[3]
                }
                for p in recent_placements
            ]
        
        return best_match
    
    return None

