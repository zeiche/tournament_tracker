#!/usr/bin/env python3
"""
Simpler script to identify organizations from tournament series patterns
"""

import re
from typing import Optional, Dict, List
from database_utils import get_session
from tournament_models import Tournament, Organization
from editor_service import editor_service get_unnamed_tournaments

def extract_series_name(tournament_name: str) -> Optional[str]:
    """
    Extract the series/organization name from a tournament name.
    E.g., "LIMIT/BREAK #32: CHOSEN ANEW" -> "LIMIT/BREAK"
    """
    
    # Common patterns for series tournaments
    patterns = [
        # Series with numbers: "Series Name #123" or "Series Name 123"
        r'^([^#\d]+?)\s*[#]\s*\d+',
        r'^([^#\d]+?)\s+\d+\s*[:|\-]',
        
        # Weekly/Monthly patterns: "Weekly Warriors Week 5"
        r'^((?:Weekly|Biweekly|Monthly|Daily)\s+\w+)',
        
        # Patterns with episode/edition: "Name Episode 5", "Name Vol. 3"
        r'^(.+?)\s+(?:Episode|Ep\.|Vol\.|Volume|Edition|Ed\.)\s+\d+',
        
        # Patterns with @ location: "Series Name @ Location"
        r'^([^@]+?)\s*@',
        
        # Patterns with year: "Tournament 2024" -> "Tournament"
        r'^(.+?)\s+20\d{2}(?:\s|$)',
        
        # Patterns with ordinal numbers: "1st Annual", "3rd Edition"
        r'^(.+?)\s+\d+(?:st|nd|rd|th)\s+(?:Annual|Edition|Tournament)',
    ]
    
    name_clean = tournament_name.strip()
    
    for pattern in patterns:
        match = re.search(pattern, name_clean, re.IGNORECASE)
        if match:
            series = match.group(1).strip()
            # Clean up the series name
            series = re.sub(r'\s+', ' ', series)  # Normalize whitespace
            series = series.rstrip(':').rstrip('-').strip()
            
            # Skip if too short or looks like a date
            if len(series) > 3 and not re.match(r'^\d+[/\-]\d+', series):
                return series
    
    return None

def analyze_tournament_groups():
    """
    Analyze unnamed tournaments to identify likely organizations based on patterns
    """
    print("=" * 60)
    print("Analyzing Tournament Patterns for Organizations")
    print("=" * 60)
    
    # Get unnamed tournaments
    tournaments = get_unnamed_tournaments()
    
    # Group by contact
    contact_groups = {}
    for t in tournaments:
        contact = t['primary_contact'] or 'unknown'
        if contact not in contact_groups:
            contact_groups[contact] = {
                'tournaments': [],
                'series_names': {},
                'total_attendance': 0
            }
        contact_groups[contact]['tournaments'].append(t)
        contact_groups[contact]['total_attendance'] += t['num_attendees']
        
        # Try to extract series name
        series = extract_series_name(t['name'])
        if series:
            if series not in contact_groups[contact]['series_names']:
                contact_groups[contact]['series_names'][series] = 0
            contact_groups[contact]['series_names'][series] += 1
    
    print(f"\nFound {len(contact_groups)} unique contacts")
    print(f"Analyzing tournament name patterns...\n")
    
    # Find contacts with consistent series names
    identified = []
    
    for contact, data in contact_groups.items():
        if not data['series_names']:
            continue
        
        # Find the most common series name
        series_counts = data['series_names']
        best_series = max(series_counts.items(), key=lambda x: x[1])
        series_name, count = best_series
        
        # Calculate confidence based on consistency
        total_tournaments = len(data['tournaments'])
        confidence = count / total_tournaments
        
        # Only include if we have good confidence
        if confidence >= 0.5 and count >= 2:  # At least 50% match and 2+ tournaments
            identified.append({
                'contact': contact,
                'organization_name': series_name,
                'confidence': confidence,
                'matched_count': count,
                'total_count': total_tournaments,
                'total_attendance': data['total_attendance'],
                'sample_tournaments': [t['name'] for t in data['tournaments'][:3]]
            })
    
    # Sort by confidence and matched count
    identified.sort(key=lambda x: (x['confidence'], x['matched_count']), reverse=True)
    
    # Display results
    print("=" * 60)
    print(f"Identified {len(identified)} Potential Organizations")
    print("=" * 60)
    
    for item in identified[:20]:  # Show top 20
        print(f"\n• {item['organization_name']}")
        print(f"  Contact: {item['contact'][:50]}...")
        print(f"  Pattern Match: {item['matched_count']}/{item['total_count']} tournaments ({item['confidence']:.1%})")
        print(f"  Total Attendance: {item['total_attendance']:,}")
        print(f"  Sample Tournaments:")
        for t_name in item['sample_tournaments']:
            print(f"    - {t_name}")
    
    if identified:
        print("\n" + "-" * 60)
        print("\nWould you like to:")
        print("1. Create ALL identified organizations")
        print("2. Review and select specific ones")
        print("3. Skip")
        
        choice = input("\nChoice (1/2/3): ").strip()
        
        if choice == '1':
            create_all_organizations(identified)
        elif choice == '2':
            review_and_create(identified)
        else:
            print("Skipped creating organizations")

def create_all_organizations(identified_list: List[Dict]):
    """Create all identified organizations"""
    
    with get_session() as session:
        created = 0
        updated = 0
        
        for item in identified_list:
            org_name = item['organization_name']
            contact = item['contact']
            
            # Check if exists
            existing = session.query(Organization).filter_by(display_name=org_name).first()
            
            if existing:
                # Add contact to existing
                if '@' in contact and '.' in contact:
                    existing.add_contact('email', contact)
                elif 'discord' in contact.lower():
                    existing.add_contact('discord', contact)
                else:
                    existing.add_contact('other', contact)
                updated += 1
            else:
                # Create new
                org = Organization(display_name=org_name, contacts_json='[]')
                if '@' in contact and '.' in contact:
                    org.add_contact('email', contact)
                elif 'discord' in contact.lower():
                    org.add_contact('discord', contact)
                else:
                    org.add_contact('other', contact)
                session.add(org)
                created += 1
        
        session.commit()
        print(f"\n✓ Created {created} new organizations")
        print(f"✓ Updated {updated} existing organizations")

def review_and_create(identified_list: List[Dict]):
    """Review each organization and decide whether to create"""
    
    selected = []
    
    for i, item in enumerate(identified_list, 1):
        print(f"\n[{i}/{len(identified_list)}] {item['organization_name']}")
        print(f"  Contact: {item['contact'][:50]}...")
        print(f"  Confidence: {item['confidence']:.1%} ({item['matched_count']} tournaments)")
        
        response = input("  Create this organization? (y/n/q to quit): ").strip().lower()
        
        if response == 'y':
            selected.append(item)
            print("  ✓ Added to create list")
        elif response == 'q':
            break
    
    if selected:
        print(f"\nCreating {len(selected)} organizations...")
        create_all_organizations(selected)

def analyze_and_auto_create(auto_mode=True, confidence_threshold=0.8):
    """
    Analyze tournaments and automatically create high-confidence organizations.
    Used for automatic identification after sync.
    Returns the number of organizations created.
    """
    # Get unnamed tournaments
    tournaments = get_unnamed_tournaments()
    
    if not tournaments:
        return 0
    
    # Group by contact
    contact_groups = {}
    for t in tournaments:
        contact = t['primary_contact'] or 'unknown'
        if contact not in contact_groups:
            contact_groups[contact] = {
                'tournaments': [],
                'series_names': {},
                'total_attendance': 0
            }
        contact_groups[contact]['tournaments'].append(t)
        contact_groups[contact]['total_attendance'] += t['num_attendees']
        
        # Try to extract series name
        series = extract_series_name(t['name'])
        if series:
            if series not in contact_groups[contact]['series_names']:
                contact_groups[contact]['series_names'][series] = 0
            contact_groups[contact]['series_names'][series] += 1
    
    # Find high-confidence organizations
    to_create = []
    
    for contact, data in contact_groups.items():
        if not data['series_names']:
            continue
        
        # Find the most common series name
        series_counts = data['series_names']
        best_series = max(series_counts.items(), key=lambda x: x[1])
        series_name, count = best_series
        
        # Calculate confidence
        total_tournaments = len(data['tournaments'])
        confidence = count / total_tournaments
        
        # Only auto-create if we have very high confidence
        if confidence >= confidence_threshold and count >= 3:  # At least 80% match and 3+ tournaments
            to_create.append({
                'contact': contact,
                'organization_name': series_name,
                'confidence': confidence,
                'count': count
            })
    
    if not to_create:
        return 0
    
    # Create organizations
    created_count = 0
    with get_session() as session:
        for item in to_create:
            org_name = item['organization_name']
            contact = item['contact']
            
            # Check if organization already exists
            existing = session.query(Organization).filter_by(display_name=org_name).first()
            
            if not existing:
                # Create new organization
                org = Organization(display_name=org_name, contacts_json='[]')
                
                # Add the contact
                if '@' in contact and '.' in contact:
                    org.add_contact('email', contact)
                elif 'discord' in contact.lower():
                    org.add_contact('discord', contact)
                else:
                    org.add_contact('other', contact)
                
                session.add(org)
                created_count += 1
                
                if not auto_mode:
                    print(f"Created organization: {org_name} (confidence: {item['confidence']:.1%})")
        
        session.commit()
    
    return created_count

if __name__ == "__main__":
    analyze_tournament_groups()