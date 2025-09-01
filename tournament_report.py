"""
tournament_report.py - Tournament Reporting and Publishing
Handles HTML generation, console reports, and Shopify publishing
"""
import os
import json
import httpx
import datetime
import time
from collections import defaultdict
from database_utils import get_attendance_rankings, get_summary_stats
from log_utils import log_info, log_debug, log_error
from html_utils import load_template, get_timestamp
from tournament_stylesheet import get_inline_styles, format_rank_badge

def get_display_name(primary_contact, data, org_names):
    """Get the best display name for a contact group"""
    contacts = data.get("contacts", [primary_contact])
    
    # Check if any contact has a mapped organization name
    if org_names:
        for contact in contacts:
            for org_data in org_names.values():
                mapped_contacts = [c.lower() for c in org_data["contacts"]]
                if contact.lower() in mapped_contacts:
                    return org_data["display_name"]
    
    # Prefer organization names over email/discord
    for contact in contacts:
        if '@' not in contact and 'discord' not in contact.lower():
            return contact
    
    # For discord entries, return the first contact (original Discord URL)
    if primary_contact.startswith('discord:'):
        return contacts[0] if contacts else primary_contact
    
    # Otherwise return the primary contact
    return primary_contact


def format_html_table(attendance_tracker, org_names):
    """Generate complete HTML table from attendance data using templates"""
    log_debug(f"Formatting HTML table with {len(attendance_tracker)} entries", "report")
    
    if not attendance_tracker:
        log_error("No attendance data for HTML table", "report")
        return "<p>No tournament data available.</p>"
    
    # Sort by attendance
    sorted_orgs = sorted(attendance_tracker.items(), key=lambda x: x[1]["total_attendance"], reverse=True)
    
    total_orgs = len(sorted_orgs)
    grand_total_attendance = sum(org[1]["total_attendance"] for org in sorted_orgs)
    total_tournaments = sum(len(org[1]["tournaments"]) for org in sorted_orgs)
    
    # Get timestamp using shared utility
    last_updated = get_timestamp()
    
    html_template = load_template("tournament_table.html")
    
    table_rows = ""
    for rank, (primary_contact, data) in enumerate(sorted_orgs, 1):
        num_tournaments = len(data["tournaments"])
        total_attendance = data["total_attendance"]
        
        # Get display name (handles the contact mapping logic)
        org_name = get_display_name(primary_contact, data, org_names)
        
        table_rows += f"""
            <tr>
                <td class="rank">{rank}</td>
                <td class="organization">{org_name}</td>
                <td class="tournaments-count">{num_tournaments}</td>
                <td class="attendance-count">{total_attendance:,}</td>
            </tr>
        """
    
    if html_template:
        log_debug("Using HTML template file", "report")
        html = html_template.replace("{{title}}", "SoCal FGC Tournament Attendance")
        html = html.replace("{{total_orgs}}", f"{total_orgs:,}")
        html = html.replace("{{total_tournaments}}", f"{total_tournaments:,}")
        html = html.replace("{{grand_total_attendance}}", f"{grand_total_attendance:,}")
        html = html.replace("{{table_rows}}", table_rows)
        html = html.replace("{{last_updated}}", last_updated)
        
        return html
    else:
        log_debug("Using fallback HTML (template not found)", "report")
        return generate_fallback_html(sorted_orgs, org_names, total_orgs, total_tournaments, grand_total_attendance, last_updated)

def generate_fallback_html(sorted_orgs, org_names, total_orgs, total_tournaments, grand_total_attendance, last_updated):
    """Generate fallback HTML when template is not available using centralized styles"""
    styles = get_inline_styles()
    
    html = f"""<div style="{styles['container']}">
<h1 style="{styles['h1']}">SoCal FGC Tournament Attendance</h1>
<table style="{styles['table']}">
<thead><tr style="{styles['thead_tr']}">
<th style="{styles['th']}">#</th>
<th style="{styles['th_left']}">Organization</th>
<th style="{styles['th']}">Tournaments</th>
<th style="{styles['th']}">Attendance</th>
</tr></thead><tbody>"""
    
    for rank, (primary_contact, data) in enumerate(sorted_orgs, 1):
        org_name = get_display_name(primary_contact, data, org_names)
        
        # Use centralized rank formatting
        rank_display = format_rank_badge(rank) if rank <= 3 else str(rank)
        
        html += f"""<tr>
<td style='{styles["td_center"]}'>{rank_display}</td>
<td style='{styles["td"]}'>{org_name}</td>
<td style='{styles["td_center"]}'>{len(data['tournaments'])}</td>
<td style='{styles["td_bold"]}'>{data['total_attendance']:,}</td>
</tr>"""
    
    html += f"""</tbody></table>
<p style='{styles["footer_text"]}'>Last updated: {last_updated}<br><small>Data courtesy of start.gg</small></p>
</div>"""
    
    return html

def find_store_and_theme():
    """Find Shopify store and theme configuration"""
    access_token = os.getenv("ACCESS_TOKEN")
    if not access_token:
        raise RuntimeError("ACCESS_TOKEN not set")
    
    store_url = "8ccd49-4.myshopify.com"
    headers = {"X-Shopify-Access-Token": access_token, "Content-Type": "application/json"}
    
    with httpx.Client(timeout=10.0) as client:
        response = client.get(f"https://{store_url}/admin/api/2023-10/themes.json", headers=headers)
        if response.status_code == 200:
            themes = response.json()["themes"]
            main_theme = next((t for t in themes if t.get("role") == "main"), themes[0])
            return store_url, main_theme["id"], access_token
    raise RuntimeError("Could not connect to Shopify store")

def update_template(store_url, theme_id, access_token, html_content, attendance_tracker, org_names):
    """Update Shopify template with tournament data"""
    template = "templates/page.attendance.json"
    headers = {"X-Shopify-Access-Token": access_token, "Content-Type": "application/json"}
    
    with httpx.Client(timeout=30.0) as client:
        asset_url = f"https://{store_url}/admin/api/2023-10/themes/{theme_id}/assets.json"
        
        try:
            response = client.get(asset_url, headers=headers, params={"asset[key]": template})
            if response.status_code == 200:
                current_data = json.loads(response.json()["asset"]["value"])
            else:
                current_data = {"sections": {"main": {"type": "page", "settings": {}}}, "order": ["main"]}
        except Exception as e:
            current_data = {"sections": {"main": {"type": "page", "settings": {}}}, "order": ["main"]}
        
        html_sections = []
        for section_id, section_data in current_data.get("sections", {}).items():
            section_type = section_data.get("type", "")
            if "custom-liquid" in section_type or "liquid" in section_type:
                html_sections.append((section_id, "custom_liquid"))
            elif "html" in section_type:
                html_sections.append((section_id, "html"))
        
        if html_sections:
            section_id, setting_name = html_sections[0]
            if "settings" not in current_data["sections"][section_id]:
                current_data["sections"][section_id]["settings"] = {}
            current_data["sections"][section_id]["settings"][setting_name] = format_html_table(attendance_tracker, org_names)
        else:
            new_section_id = f"tournament_html_{int(time.time())}"
            current_data["sections"][new_section_id] = {
                "type": "custom-liquid",
                "settings": {
                    "custom_liquid": format_html_table(attendance_tracker, org_names)
                }
            }
            
            if "order" in current_data:
                if new_section_id not in current_data["order"]:
                    current_data["order"].append(new_section_id)
            else:
                current_data["order"] = ["main", new_section_id]
        
        update_data = {"asset": {"key": template, "value": json.dumps(current_data, indent=2)}}
        response = client.put(asset_url, headers=headers, json=update_data)
        response.raise_for_status()
        return True

def publish_table(attendance_tracker, org_names, console_only=False):
    """Publish tournament table to Shopify or console"""
    try:
        html_content = format_html_table(attendance_tracker, org_names)
        
        if console_only:
            log_info("Console output mode - not publishing to Shopify", "report")
            
            # Show rankings in console
            sorted_orgs = sorted(attendance_tracker.items(), key=lambda x: x[1]["total_attendance"], reverse=True)
            
            print(f"{'RANK':<6} {'ORGANIZATION':<50} {'TOURNAMENTS':<12} {'ATTENDANCE':<12}")
            print("-" * 80)
            
            for rank, (primary_contact, data) in enumerate(sorted_orgs[:20], 1):  # Show top 20
                org_name = get_display_name(primary_contact, data, org_names)
                tournaments = len(data["tournaments"])
                attendance = data["total_attendance"]
                
                print(f"{rank:<6} {org_name[:48]:<50} {tournaments:<12} {attendance:<12}")
            
            print("-" * 80)
            print(f"Total organizations: {len(sorted_orgs)}")
            print(f"Total tournaments: {sum(len(org[1]['tournaments']) for org in sorted_orgs)}")
            print(f"Total attendance: {sum(org[1]['total_attendance'] for org in sorted_orgs):,}")
            
            return True
        else:
            store_url, theme_id, access_token = find_store_and_theme()
            success = update_template(store_url, theme_id, access_token, html_content, attendance_tracker, org_names)
            
            if success:
                log_info(f"Published to {store_url}", "report")
            else:
                log_error("Failed to update template", "report")
            return success
            
    except Exception as e:
        log_error(f"Publishing error: {e}", "report")
        return False

def format_console_table(limit=20):
    """Generate console-friendly table for debugging"""
    print("Tournament Attendance Report")
    print("=" * 80)
    
    rankings = get_attendance_rankings(limit)
    stats = get_summary_stats()
    
    if not rankings:
        print("No attendance data available")
        return
    
    # Header
    print(f"{'Rank':<4} {'Organization':<40} {'Events':<8} {'Attendance':<12}")
    print("-" * 80)
    
    # Rows
    for rank, org_data in enumerate(rankings, 1):
        organization = org_data['display_name'][:38]  # Truncate long names
        tournament_count = org_data['tournament_count']
        total_attendance = org_data['total_attendance']
        
        medal = ""
        if rank == 1:
            medal = "1st"
        elif rank == 2:
            medal = "2nd"
        elif rank == 3:
            medal = "3rd"
        
        print(f"{medal}{rank:<3} {organization:<40} {tournament_count:<8} {total_attendance:<12,}")
    
    print("-" * 80)
    print(f"Summary: {stats['total_organizations']} orgs, "
          f"{stats['total_tournaments']} tournaments, "
          f"{stats['total_attendance']:,} total attendance")

def generate_html_report(limit=None, output_file=None):
    """Generate HTML attendance report"""
    log_info("Generating HTML report", "report")
    
    try:
        # Get data from database
        from shopify_query import get_legacy_attendance_data
        attendance_tracker, org_names = get_legacy_attendance_data()
        
        # Generate HTML
        html = format_html_table(attendance_tracker, org_names)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)
            log_info(f"HTML report saved to {output_file}", "report")
        else:
            print("HTML Report Generated:")
            print("-" * 80)
            print(html)
            print("-" * 80)
        
        return html
        
    except Exception as e:
        log_error(f"HTML generation failed: {e}", "report")
        return None

def get_legacy_attendance_data():
    """
    Convert SQLAlchemy data to legacy format for existing Shopify code
    Returns data in the format expected by existing publishing system
    """
    rankings = get_attendance_rankings()
    
    # Convert to old format (attendance_tracker, org_names)
    attendance_tracker = {}
    org_names = {}
    
    for rank, org_data in enumerate(rankings, 1):
        key = org_data['normalized_key']
        
        # Attendance tracker format
        attendance_tracker[key] = {
            'tournaments': [],  # Could populate if needed
            'total_attendance': org_data['total_attendance'],
            'contacts': org_data['contacts']
        }
        
        # Organization names format (only if display name differs from key)
        if org_data['display_name'] != key:
            org_names[f"org_{rank}"] = {
                'display_name': org_data['display_name'],
                'contacts': org_data['contacts']
            }
    
    return attendance_tracker, org_names

def publish_to_shopify():
    """Publish tournament data to Shopify"""
    log_info("Publishing to Shopify", "report")
    
    try:
        # Get data from database in legacy format
        from shopify_query import get_legacy_attendance_data
        attendance_tracker, org_names = get_legacy_attendance_data()
        
        # Publish using existing functionality
        success = publish_table(attendance_tracker, org_names)
        
        if success:
            log_info("Successfully published to Shopify", "report")
            return True
        else:
            log_error("Shopify publishing failed", "report")
            return False
            
    except Exception as e:
        log_error(f"Shopify publishing failed: {e}", "report")
        return False

def generate_geo_data(output_format='json'):
    """
    Generate geographic data for tournaments
    Returns GeoJSON for mapping or regular JSON for analysis
    """
    from database_utils import get_session
    from tournament_models import Tournament
    from collections import defaultdict
    import json
    
    geo_data = []
    city_stats = defaultdict(int)
    
    with get_session() as session:
        # Get all tournaments with geo data
        tournaments = session.query(Tournament).filter(
            Tournament.lat.isnot(None),
            Tournament.lng.isnot(None)
        ).all()
        
        for t in tournaments:
            try:
                lat = float(t.lat)
                lng = float(t.lng)
                
                geo_entry = {
                    'id': t.id,
                    'name': t.name,
                    'lat': lat,
                    'lng': lng,
                    'city': t.city,
                    'state': t.addr_state,
                    'venue': t.venue_name,
                    'address': t.venue_address,
                    'attendees': t.num_attendees or 0,
                    'date': t.start_at,
                    'slug': t.short_slug or t.slug
                }
                
                geo_data.append(geo_entry)
                
                # Track city statistics
                if t.city:
                    city_stats[t.city] += 1
                    
            except (ValueError, TypeError):
                continue
    
    if output_format == 'geojson':
        # Return GeoJSON format for mapping
        features = []
        for entry in geo_data:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [entry['lng'], entry['lat']]
                },
                "properties": {
                    "name": entry['name'],
                    "city": entry['city'],
                    "venue": entry['venue'],
                    "attendees": entry['attendees'],
                    "date": entry['date']
                }
            })
        
        return {
            "type": "FeatureCollection",
            "features": features
        }
    else:
        # Return regular JSON with stats
        return {
            'tournaments': geo_data,
            'city_stats': dict(city_stats),
            'total_with_geo': len(geo_data)
        }

if __name__ == "__main__":
    print("Testing tournament reporting...")
    
    # Test console report
    print("\nConsole Table Test:")
    format_console_table(10)
    
    # Test HTML generation
    print(f"\nHTML Report Test:")
    html = generate_html_report()
    if html:
        print(f"Generated {len(html)} characters of HTML")
    
    print("Tournament reporting tests completed!")

