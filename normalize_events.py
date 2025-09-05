#!/usr/bin/env python3
"""
Post-sync event normalization
Normalizes event names in the database that haven't been normalized yet
"""

from sqlalchemy import func, distinct
from event_standardizer import EventStandardizer
from database import session_scope
from tournament_models import TournamentPlacement
from log_utils import log_info, log_debug, log_error

def get_unnormalized_events(session):
    """Find event names that appear to be unnormalized"""
    # Get distinct event names
    event_names = session.query(distinct(TournamentPlacement.event_name)).all()
    
    unnormalized = []
    for (event_name,) in event_names:
        if not event_name:
            continue
            
        # Check if this looks like a normalized name already
        standardized = EventStandardizer.standardize(event_name)
        
        # If the standardized name differs from current, it needs normalization
        if standardized['standard_name'] != event_name:
            # Only process Ultimate events
            if standardized['game'] == 'ultimate':
                unnormalized.append({
                    'original': event_name,
                    'normalized': standardized['standard_name'],
                    'game': standardized['game'],
                    'format': standardized['format'],
                    'is_special': standardized['is_special']
                })
    
    return unnormalized

def normalize_database_events(dry_run=False):
    """
    Normalize all event names in the database
    
    Args:
        dry_run: If True, show what would be changed without making changes
    
    Returns:
        dict: Statistics about the normalization
    """
    log_info("Starting event name normalization", "normalize")
    
    stats = {
        'events_checked': 0,
        'events_normalized': 0,
        'placements_updated': 0,
        'errors': 0,
        'non_ultimate_skipped': 0
    }
    
    with session_scope() as session:
        # Find unnormalized events
        unnormalized_events = get_unnormalized_events(session)
        stats['events_checked'] = len(unnormalized_events)
        
        if dry_run:
            print("\nDRY RUN - No changes will be made")
            print("=" * 60)
        
        for event_info in unnormalized_events:
            original = event_info['original']
            normalized = event_info['normalized']
            
            try:
                # Count how many placements will be affected
                count = session.query(TournamentPlacement).filter_by(
                    event_name=original
                ).count()
                
                if dry_run:
                    print(f"\nWould normalize: {original}")
                    print(f"  → {normalized}")
                    print(f"  Affects {count} placements")
                else:
                    # Update all placements with this event name
                    session.query(TournamentPlacement).filter_by(
                        event_name=original
                    ).update({
                        'event_name': normalized
                    })
                    
                    stats['events_normalized'] += 1
                    stats['placements_updated'] += count
                    
                    log_info(f"Normalized '{original}' → '{normalized}' ({count} placements)", "normalize")
                    
            except Exception as e:
                stats['errors'] += 1
                log_error(f"Failed to normalize '{original}': {e}", "normalize")
                if not dry_run:
                    session.rollback()
                    raise
        
        if not dry_run:
            session.commit()
            log_info(f"Normalization complete: {stats['events_normalized']} events normalized", "normalize")
    
    return stats

def show_event_distribution():
    """Show distribution of event names in the database"""
    with session_scope() as session:
        # Get event name counts
        results = session.query(
            TournamentPlacement.event_name,
            func.count(TournamentPlacement.id).label('count')
        ).group_by(
            TournamentPlacement.event_name
        ).order_by(
            func.count(TournamentPlacement.id).desc()
        ).all()
        
        print("\nCurrent Event Name Distribution:")
        print("=" * 60)
        
        total = 0
        for event_name, count in results:
            if event_name:
                print(f"  {event_name:<40} {count:>5} placements")
                total += count
        
        print("-" * 60)
        print(f"  {'TOTAL':<40} {total:>5} placements")
        print()

def main():
    """Main entry point for event normalization"""
    import sys
    
    # Check for command line arguments
    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv
    show_dist = '--show' in sys.argv or '-s' in sys.argv
    
    if show_dist:
        show_event_distribution()
        return
    
    # Run normalization
    stats = normalize_database_events(dry_run=dry_run)
    
    print("\nNormalization Statistics:")
    print("=" * 40)
    print(f"Events checked:     {stats['events_checked']}")
    print(f"Events normalized:  {stats['events_normalized']}")
    print(f"Placements updated: {stats['placements_updated']}")
    if stats['non_ultimate_skipped'] > 0:
        print(f"Non-Ultimate skipped: {stats['non_ultimate_skipped']}")
    if stats['errors'] > 0:
        print(f"Errors:            {stats['errors']}")
    
    if dry_run:
        print("\nThis was a DRY RUN - no changes were made")
        print("Run without --dry-run to apply changes")

if __name__ == "__main__":
    main()