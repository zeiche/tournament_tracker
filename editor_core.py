#!/usr/bin/env python3
"""
editor_core.py - Core logic for editing tournament contacts
Uses existing infrastructure from database_utils and tournament_models
"""

import re
from database_utils import get_session, normalize_contact
from tournament_models import Tournament, Organization
from log_utils import log_info, log_debug

def is_contact_unnamed(contact):
    """Check if a contact needs a proper organization name"""
    if not contact:
        return False
    
    contact = contact.strip().lower()
    
    # Patterns that indicate unnamed contacts
    patterns = [
        r'.*@.*\.(com|org|net|edu)',    # Email addresses
        r'.*discord\.gg/.*',            # Discord invite links
        r'.*discord\.com/invite/.*',    # Discord invite links
        r'.*twitter\.com/.*',           # Twitter handles
        r'.*facebook\.com/.*',          # Facebook URLs
        r'.*instagram\.com/.*',         # Instagram handles
        r'^https?://.*',                # Any HTTP URL
        r'.*\.com$',                    # Ends with .com (likely URL)
        r'.*\d{10,}.*',                 # Contains long numbers (phone, ID)
    ]
    
    for pattern in patterns:
        if re.match(pattern, contact):
            return True
    
    # Single word under 20 chars might be username/handle
    if len(contact.split()) == 1 and len(contact) < 20:
        return True
    
    return False

def get_unnamed_tournaments():
    """Get all tournaments with unnamed contacts (excluding those that match organizations)"""
    from database_utils import normalize_contact
    
    with get_session() as session:
        tournaments = session.query(Tournament).filter(
            Tournament.primary_contact != None
        ).all()
        
        # Get all organization contacts for matching
        orgs = session.query(Organization).all()
        org_contacts_normalized = set()
        for org in orgs:
            for contact in org.contacts:
                value = contact.get('value', '')
                if value:
                    org_contacts_normalized.add(normalize_contact(value))
        
        unnamed = []
        for t in tournaments:
            # Skip if contact matches an organization
            if t.primary_contact:
                normalized = normalize_contact(t.primary_contact)
                if normalized in org_contacts_normalized:
                    continue  # This tournament belongs to an organization
            
            # Only include if it's truly unnamed
            if is_contact_unnamed(t.primary_contact):
                unnamed.append({
                    'id': t.id,
                    'name': t.name,
                    'primary_contact': t.primary_contact,
                    'num_attendees': t.num_attendees or 0,
                    'venue_name': t.venue_name,
                    'city': t.city,
                    'short_slug': t.short_slug
                })
        
        # Sort by attendance (highest first)
        unnamed.sort(key=lambda x: x['num_attendees'], reverse=True)
        log_info(f"Found {len(unnamed)} tournaments with unnamed contacts")
        return unnamed

def update_tournament_contact(tournament_id, new_contact):
    """Update a tournament's primary contact"""
    with get_session() as session:
        tournament = session.query(Tournament).get(tournament_id)
        if tournament:
            tournament.primary_contact = new_contact
            tournament.normalized_contact = normalize_contact(new_contact)
            session.commit()
            log_info(f"Updated tournament {tournament_id} contact to: {new_contact}")
            return True
        return False

def get_or_create_organization(name, contact_email=None, contact_discord=None):
    """Get existing organization or create new one"""
    with get_session() as session:
        # Check if organization exists by display_name
        org = session.query(Organization).filter_by(display_name=name).first()
        if org:
            log_debug(f"Found existing organization: {name}")
            return org.id
        
        # Create new organization
        org = Organization()
        org.display_name = name
        # normalized_key no longer exists
        session.add(org)
        session.commit()
        
        # Add contact info if provided
        if contact_email:
            from tournament_models import OrganizationContact
            contact = OrganizationContact()
            contact.organization_id = org.id
            contact.contact_value = contact_email
            contact.contact_type = 'email'
            session.add(contact)
        
        if contact_discord:
            from tournament_models import OrganizationContact
            contact = OrganizationContact()
            contact.organization_id = org.id
            contact.contact_value = contact_discord
            contact.contact_type = 'discord'
            session.add(contact)
        
        session.commit()
        log_info(f"Created new organization: {name}")
        return org.id

def batch_update_contacts(updates):
    """Batch update multiple tournament contacts
    updates: list of (tournament_id, new_contact) tuples
    """
    with get_session() as session:
        count = 0
        for tournament_id, new_contact in updates:
            tournament = session.query(Tournament).get(tournament_id)
            if tournament:
                tournament.primary_contact = new_contact
                tournament.normalized_contact = normalize_contact(new_contact)
                count += 1
        
        session.commit()
        log_info(f"Batch updated {count} tournament contacts")
        return count