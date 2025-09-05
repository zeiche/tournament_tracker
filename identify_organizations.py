#!/usr/bin/env python3
"""
Script to identify organizations from tournament slugs using web scraping and AI analysis
"""

import sys
import time
import json
from typing import Optional, Dict, List, Tuple
from database_utils import get_session, normalize_contact
from tournament_models import Tournament, Organization
from editor_service import editor_service get_unnamed_tournaments

def analyze_tournament_page(slug: str, contact: str) -> Tuple[Optional[str], float]:
    """
    Analyze a tournament page to identify the organization name.
    Returns (organization_name, confidence_score)
    """
    if not slug:
        return None, 0.0
    
    url = f"https://start.gg/{slug}"
    
    # Use subprocess to call claude with WebFetch through go.py
    import subprocess
    import os
    
    prompt = f"""Analyze this tournament page to identify the organization running it.
Look for:
1. Organization name in the title, description, or organizer section
2. Series name (e.g., "Weekly Warriors #45" suggests "Weekly Warriors" organization)
3. Any recurring tournament series patterns
4. Organizer names or group names
5. Contact info that might indicate an organization

Current contact info we have: {contact}

Return ONLY a JSON response in this format:
{{
    "organization_name": "Name Here or null if unknown",
    "confidence": 0.0 to 1.0,
    "reasoning": "Brief explanation"
}}

Be conservative - only return high confidence if you find clear organization info."""

    try:
        # Build the command to ask Claude
        cmd = [
            "/home/ubuntu/claude/tournament_tracker/venv/bin/python",
            "/home/ubuntu/claude/tournament_tracker/go.py",
            "--ai-ask",
            f"Please fetch {url} and analyze it. {prompt}"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            env={**os.environ, 'ANTHROPIC_API_KEY': os.environ.get('ANTHROPIC_API_KEY', '')}
        )
        
        if result.returncode != 0:
            print(f"  Error calling AI for {slug}: {result.stderr}")
            return None, 0.0
        
        # Parse the response to extract JSON
        response = result.stdout
        
        # Try to find JSON in the response
        import re
        json_match = re.search(r'\{[^{}]*"organization_name"[^{}]*\}', response, re.DOTALL)
        
        if json_match:
            try:
                data = json.loads(json_match.group())
                org_name = data.get("organization_name")
                confidence = float(data.get("confidence", 0.0))
                
                if org_name and org_name.lower() != "null":
                    return org_name, confidence
            except json.JSONDecodeError:
                pass
        
        return None, 0.0
        
    except subprocess.TimeoutExpired:
        print(f"  Timeout analyzing {slug}")
        return None, 0.0
    except Exception as e:
        print(f"  Error analyzing {slug}: {e}")
        return None, 0.0

def identify_organizations(limit: int = 10, min_confidence: float = 0.7):
    """
    Identify organizations for unnamed tournaments
    """
    print("=" * 60)
    print("Organization Identification from Tournament Pages")
    print("=" * 60)
    
    # Get unnamed tournaments
    tournaments = get_unnamed_tournaments()
    
    # Group by contact for efficiency
    contact_groups = {}
    for t in tournaments:
        contact = t['primary_contact'] or 'unknown'
        if contact not in contact_groups:
            contact_groups[contact] = []
        contact_groups[contact].append(t)
    
    print(f"\nFound {len(contact_groups)} unique contacts with {len(tournaments)} tournaments")
    print(f"Analyzing up to {limit} contact groups...\n")
    
    identified = []
    processed = 0
    
    for contact, group_tournaments in list(contact_groups.items())[:limit]:
        processed += 1
        
        # Use the tournament with the shortest/cleanest slug
        best_tournament = None
        for t in group_tournaments:
            if t.get('short_slug'):
                if not best_tournament or len(t['short_slug']) < len(best_tournament.get('short_slug', '')):
                    best_tournament = t
        
        if not best_tournament or not best_tournament.get('short_slug'):
            print(f"[{processed}/{limit}] {contact[:40]}... - No slug available")
            continue
        
        slug = best_tournament['short_slug']
        print(f"[{processed}/{limit}] Analyzing {slug} for {contact[:40]}...")
        
        # Rate limit to avoid overwhelming
        time.sleep(2)
        
        org_name, confidence = analyze_tournament_page(slug, contact)
        
        if org_name and confidence >= min_confidence:
            print(f"  ✓ Found: {org_name} (confidence: {confidence:.1%})")
            identified.append({
                'contact': contact,
                'organization_name': org_name,
                'confidence': confidence,
                'tournament_count': len(group_tournaments),
                'total_attendance': sum(t['num_attendees'] for t in group_tournaments),
                'sample_slug': slug
            })
        else:
            if org_name:
                print(f"  ? Low confidence: {org_name} ({confidence:.1%})")
            else:
                print(f"  ✗ Could not identify organization")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"SUMMARY: Identified {len(identified)} organizations")
    print("=" * 60)
    
    if identified:
        # Sort by confidence and tournament count
        identified.sort(key=lambda x: (x['confidence'], x['tournament_count']), reverse=True)
        
        print("\nIdentified Organizations:")
        for item in identified:
            print(f"\n• {item['organization_name']}")
            print(f"  Contact: {item['contact']}")
            print(f"  Confidence: {item['confidence']:.1%}")
            print(f"  Tournaments: {item['tournament_count']} ({item['total_attendance']} total attendance)")
            print(f"  Sample: https://start.gg/{item['sample_slug']}")
        
        # Ask about creating organizations
        print("\n" + "-" * 60)
        print("Would you like to create these organizations? (y/n)")
        print("This will:")
        print("1. Create new organizations with the identified names")
        print("2. Add the contacts to each organization")
        
        response = input("> ").strip().lower()
        
        if response == 'y':
            create_identified_organizations(identified)
    else:
        print("\nNo organizations could be confidently identified.")
        print("Try adjusting the confidence threshold or checking different tournaments.")

def create_identified_organizations(identified_list: List[Dict]):
    """Create organizations from identified list"""
    
    with get_session() as session:
        created_count = 0
        
        for item in identified_list:
            org_name = item['organization_name']
            contact = item['contact']
            
            # Check if organization already exists
            existing = session.query(Organization).filter_by(display_name=org_name).first()
            
            if existing:
                print(f"Organization '{org_name}' already exists, adding contact...")
                # Determine contact type
                if '@' in contact and '.' in contact:
                    contact_type = 'email'
                elif 'discord' in contact.lower():
                    contact_type = 'discord'
                else:
                    contact_type = 'other'
                
                existing.add_contact(contact_type, contact)
            else:
                # Create new organization
                org = Organization(display_name=org_name)
                
                # Add the contact
                if '@' in contact and '.' in contact:
                    contact_type = 'email'
                elif 'discord' in contact.lower():
                    contact_type = 'discord'
                else:
                    contact_type = 'other'
                
                org.add_contact(contact_type, contact)
                
                session.add(org)
                created_count += 1
                print(f"Created organization: {org_name}")
        
        session.commit()
        print(f"\n✓ Created {created_count} new organizations")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Identify organizations from tournament slugs")
    parser.add_argument('--limit', type=int, default=10, 
                       help='Maximum number of contacts to analyze (default: 10)')
    parser.add_argument('--confidence', type=float, default=0.7,
                       help='Minimum confidence threshold (0.0-1.0, default: 0.7)')
    parser.add_argument('--test', action='store_true',
                       help='Test mode - analyze one tournament')
    
    args = parser.parse_args()
    
    if args.test:
        # Test mode - just analyze one tournament
        print("TEST MODE: Analyzing LIMIT/BREAK tournament...")
        org_name, confidence = analyze_tournament_page("BreakLimit", "https://discord.gg/Y6QfvdhnzJ")
        print(f"Result: {org_name} (confidence: {confidence:.1%})")
    else:
        identify_organizations(limit=args.limit, min_confidence=args.confidence)