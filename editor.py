i#!/usr/bin/env python3
"""
contact_editor.py - Multi-column Curses TUI for primary contact cleanup
Shows tournaments with UN-NAMED primary contacts that need organization names
VERSION: xxxx
ARTIFACT: xxxx
"""
import curses
import sys
import os
import re
from tournament_models import Tournament, Organization, BaseModel, normalize_contact
from database_utils import init_db

class MultiColumnContactEditor:
    """Multi-column curses TUI for primary contact editing"""
    
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.changes = {}
        self.skipped = set()
        self.current_index = 0
        self.scroll_offset = 0
        self.status_message = ""
        self.tournaments = []
        
        curses.curs_set(0)
        if curses.has_colors():
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
            curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
            curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
            curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)
            curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)
            curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)
    
    def is_contact_unnamed(self, primary_contact):
        """Determine if a primary contact needs naming"""
        if not primary_contact:
            return False
            
        contact = primary_contact.strip().lower()
        
        # Check for patterns that indicate un-named contacts
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
        
        # If contact matches any pattern, it's considered un-named
        for pattern in patterns:
            if re.match(pattern, contact):
                return True
                
        # Additional checks for single word contacts that look like usernames
        if len(contact.split()) == 1 and len(contact) < 20:
            # Single word under 20 chars might be username/handle
            return True
            
        return False
    
    def run(self):
        """Main TUI loop - show tournaments with un-named primary contacts"""
        self.status_message = "Loading tournaments with un-named contacts..."
        self.draw_screen()
        
        all_tournaments = Tournament.all()
        
        # Filter for tournaments with un-named primary contacts
        self.tournaments = []
        for tournament in all_tournaments:
            if self.is_contact_unnamed(tournament.primary_contact):
                tournament_data = {
                    'id': tournament.id,
                    'name': tournament.name,
                    'primary_contact': tournament.primary_contact,
                    'num_attendees': tournament.num_attendees or 0,
                    'venue_name': tournament.venue_name,
                    'city': tournament.city,
                    'short_slug': tournament.short_slug,
                    'slug': tournament.slug,
                    'normalized_contact': tournament.normalized_contact
                }
                self.tournaments.append(tournament_data)
        
        # Sort by attendance (highest first)
        self.tournaments.sort(key=lambda x: x['num_attendees'], reverse=True)
        
        if not self.tournaments:
            self.status_message = "No tournaments with un-named contacts found"
            self.draw_screen()
            self.stdscr.getch()
            return
        
        self.status_message = f"Found {len(self.tournaments)} tournaments with un-named contacts. Use arrows, 'e' to edit, 'q' to quit."
        
        while True:
            self.draw_screen()
            key = self.stdscr.getch()
                
            if key == ord('q') or key == ord('Q'):
                if self.confirm_quit():
                    break
            elif key == curses.KEY_UP:
                self.move_selection(-1)
            elif key == curses.KEY_DOWN:
                self.move_selection(1)
            elif key == curses.KEY_LEFT:
                self.move_selection(-5)
            elif key == curses.KEY_RIGHT:
                self.move_selection(5)
            elif key == curses.KEY_PPAGE:
                self.move_selection(-20)
            elif key == curses.KEY_NPAGE:
                self.move_selection(20)
            elif key == ord('e') or key == ord('E'):
                if self.start_edit_mode():
                    break
            elif key == ord('s') or key == ord('S'):
                self.skip_current()
            elif key == ord('b') or key == ord('B'):
                self.bulk_skip_pattern()
            elif key == ord('r') or key == ord('R'):
                self.reset_current()
            elif key == ord('h') or key == ord('H'):
                self.show_help()
        
        self.save_changes()
    
    def move_selection(self, delta):
        """Move selection with proper bounds checking"""
        old_index = self.current_index
        self.current_index = max(0, min(len(self.tournaments) - 1, self.current_index + delta))
        
        if self.current_index != old_index:
            self.update_scroll()
    
    def update_scroll(self):
        """Update scroll offset to keep current selection visible"""
        height, width = self.stdscr.getmaxyx()
        available_height = height - 10
        column_width = 45
        columns = max(1, width // column_width)
        items_per_page = available_height * columns
        
        current_page = self.current_index // items_per_page
        self.scroll_offset = current_page * items_per_page
    
    def draw_screen(self):
        """Draw the multi-column tournament list"""
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        
        try:
            header = "Primary Contact Editor - Un-named Contacts"
            self.stdscr.addstr(0, (width - len(header)) // 2, header, 
                              curses.color_pair(1) | curses.A_BOLD)
            
            instructions = "q:quit e:edit s:skip b:bulk r:reset h:help  Arrows:navigate"
            self.stdscr.addstr(1, 1, instructions[:width-2], curses.color_pair(6))
        except curses.error:
            pass
        
        available_height = height - 10
        column_width = 45
        columns = max(1, width // column_width)
        rows_per_column = available_height
        items_per_page = rows_per_column * columns
        
        for i in range(items_per_page):
            tournament_index = self.scroll_offset + i
            if tournament_index >= len(self.tournaments):
                break
                
            tournament = self.tournaments[tournament_index]
            
            col = i // rows_per_column
            row = i % rows_per_column
            x = col * column_width
            y = 2 + row
            
            if x + column_width > width or y >= 2 + available_height:
                break
            
            display_contact = self.get_display_contact(tournament)[:25]
            attendees = tournament['num_attendees']
            
            entry_text = f"{tournament_index+1:3d}. {display_contact:<25} {attendees:>4}"
            
            attr = 0
            if tournament_index == self.current_index:
                attr |= curses.color_pair(2) | curses.A_BOLD
            else:
                attr |= self.get_contact_color_attr(tournament)
            
            try:
                self.stdscr.addstr(y, x, entry_text[:column_width-1], attr)
            except curses.error:
                pass
        
        if self.tournaments and 0 <= self.current_index < len(self.tournaments):
            self.draw_current_tournament_details(height, width)
        
        if self.status_message:
            try:
                self.stdscr.addstr(height - 2, 1, self.status_message[:width-2], curses.color_pair(5))
            except curses.error:
                pass
        
        changed_count = len(self.changes)
        skipped_count = len(self.skipped)
        if self.tournaments:
            current_page = (self.current_index // items_per_page) + 1
            total_pages = ((len(self.tournaments) - 1) // items_per_page) + 1
            progress = f"[{self.current_index + 1}/{len(self.tournaments)}] Page {current_page}/{total_pages}"
        else:
            progress = "[0/0] Page 1/1"
        stats_text = f"{progress} Changed: {changed_count}, Skipped: {skipped_count}"
        try:
            self.stdscr.addstr(height - 1, 1, stats_text[:width-2])
        except curses.error:
            pass
        
        self.stdscr.refresh()
    
    def draw_current_tournament_details(self, height, width):
        """Draw detailed info for current tournament at bottom"""
        tournament = self.tournaments[self.current_index]
        detail_start_y = height - 8
        
        try:
            self.stdscr.addstr(detail_start_y, 0, "-" * width)
            
            y = detail_start_y + 1
            tournament_name = tournament['name'][:50]
            self.stdscr.addstr(y, 1, f"Tournament: {tournament_name}", curses.A_BOLD)
            
            y += 1
            current_contact = self.get_display_contact(tournament)
            self.stdscr.addstr(y, 1, f"Current Contact: {current_contact}", 
                              self.get_contact_color(tournament) | curses.A_BOLD)
            
            y += 1
            venue_info = f"Venue: {tournament['venue_name'] or 'Unknown'}"
            if tournament['city']:
                venue_info += f" - {tournament['city']}"
            self.stdscr.addstr(y, 1, venue_info[:width-2])
            
            y += 1
            self.stdscr.addstr(y, 1, f"Attendance: {tournament['num_attendees']} people")
            
            y += 1
            if tournament['short_slug']:
                startgg_url = f"https://start.gg/{tournament['short_slug']}"
            elif tournament['slug']:
                startgg_url = f"https://start.gg/tournament/{tournament['slug']}"
            else:
                startgg_url = "No URL available"
            
            self.stdscr.addstr(y, 1, f"URL: {startgg_url}", curses.color_pair(6))
                
        except curses.error:
            pass
    
    def get_display_contact(self, tournament):
        """Get current display contact including pending changes"""
        tournament_id = tournament['id']
        if tournament_id in self.changes:
            return self.changes[tournament_id]
        return tournament['primary_contact'] or "No Contact"
    
    def get_contact_color(self, tournament):
        """Get color pair for contact"""
        tournament_id = tournament['id']
        if tournament_id in self.changes:
            return curses.color_pair(3)  # Green for changed
        elif tournament_id in self.skipped:
            return curses.color_pair(4)  # Red for skipped
        return curses.color_pair(5)     # Yellow for un-named
    
    def get_contact_color_attr(self, tournament):
        """Get color attribute"""
        return self.get_contact_color(tournament)
    
    def start_edit_mode(self):
        """Show suggestions dialog for current tournament's primary contact"""
        if self.current_index >= len(self.tournaments):
            return False
            
        tournament = self.tournaments[self.current_index]
        current_contact = self.get_display_contact(tournament)
        
        return self.show_name_suggestions(current_contact)
    
    def show_name_suggestions(self, current_contact):
        """Show numbered suggestions with integrated custom entry"""
        height, width = self.stdscr.getmaxyx()
        
        dialog_width = min(80, width - 4)
        dialog_height = min(28, height - 4)
        start_y = (height - dialog_height) // 2
        start_x = (width - dialog_width) // 2
        
        for y in range(start_y, start_y + dialog_height):
            try:
                self.stdscr.addstr(y, start_x, " " * dialog_width, curses.color_pair(2))
            except curses.error:
                pass
        
        try:
            self.stdscr.addstr(start_y + 1, start_x + 2, "Choose organization name for primary contact:", 
                              curses.color_pair(2) | curses.A_BOLD)
            
            current_truncated = current_contact[:dialog_width-15] 
            self.stdscr.addstr(start_y + 2, start_x + 2, f"Current: {current_truncated}", 
                              curses.color_pair(2))
            
            self.stdscr.addstr(start_y + 4, start_x + 2, "Organization name:", 
                              curses.color_pair(2) | curses.A_BOLD)
            self.stdscr.addstr(start_y + 5, start_x + 2, "> ", curses.color_pair(2))
        except curses.error:
            pass
        
        suggestions_per_column = 10
        col_width = (dialog_width - 6) // 2
        
        for i, suggestion in enumerate(self.name_suggestions[:20]):
            col = i // suggestions_per_column
            row = i % suggestions_per_column
            
            x_offset = start_x + 2 + (col * col_width)
            y_offset = start_y + 8 + row
            
            suggestion_text = f"{i+1:2d}. {suggestion}"[:col_width-1]
            
            try:
                self.stdscr.addstr(y_offset, x_offset, suggestion_text, curses.color_pair(2))
            except curses.error:
                break
        
        instruction_y = start_y + dialog_height - 2
        try:
            self.stdscr.addstr(instruction_y, start_x + 2, 
                              "Type above, Number (1-20), Enter save, 'q' quit, Esc cancel", 
                              curses.color_pair(2) | curses.A_BOLD)
        except curses.error:
            pass
        
        self.stdscr.refresh()
        
        edit_buffer = ""
        cursor_pos = 0
        custom_y = start_y + 5
        custom_x = start_x + 4
        
        curses.curs_set(1)
        
        while True:
            try:
                self.stdscr.addstr(custom_y, custom_x, " " * (dialog_width - 6), curses.color_pair(2))
                display_buffer = edit_buffer[:dialog_width - 8]
                self.stdscr.addstr(custom_y, custom_x, display_buffer, curses.color_pair(2))
                self.stdscr.move(custom_y, custom_x + min(cursor_pos, len(display_buffer)))
                self.stdscr.refresh()
            except curses.error:
                pass
            
            key = self.stdscr.getch()
            
            if key == 27:  # Esc
                curses.curs_set(0)
                return False
            elif key == ord('q') or key == ord('Q'):
                curses.curs_set(0)
                return True
            elif key == ord('\n') or key == curses.KEY_ENTER or key == 10:
                if edit_buffer.strip():
                    self.apply_contact_change(edit_buffer.strip())
                    curses.curs_set(0)
                    return False
            elif ord('1') <= key <= ord('9'):
                selection = key - ord('0')
                if 1 <= selection <= len(self.name_suggestions):
                    self.apply_contact_change(self.name_suggestions[selection - 1])
                    curses.curs_set(0)
                    return False
            elif key == ord('0'):
                try:
                    self.stdscr.addstr(height - 1, start_x + 2, "Second digit (0-9): ")
                    self.stdscr.refresh()
                except curses.error:
                    pass
                second_key = self.stdscr.getch()
                if ord('0') <= second_key <= ord('9'):
                    selection = 10 + (second_key - ord('0'))
                    if selection <= len(self.name_suggestions):
                        self.apply_contact_change(self.name_suggestions[selection - 1])
                        curses.curs_set(0)
                        return False
            elif key == curses.KEY_BACKSPACE or key == 127 or key == 8:
                if cursor_pos > 0:
                    edit_buffer = edit_buffer[:cursor_pos-1] + edit_buffer[cursor_pos:]
                    cursor_pos -= 1
            elif key == curses.KEY_LEFT:
                cursor_pos = max(0, cursor_pos - 1)
            elif key == curses.KEY_RIGHT:
                cursor_pos = min(len(edit_buffer), cursor_pos + 1)
            elif key == curses.KEY_HOME:
                cursor_pos = 0
            elif key == curses.KEY_END:
                cursor_pos = len(edit_buffer)
            elif 32 <= key <= 126:  # Printable ASCII
                edit_buffer = edit_buffer[:cursor_pos] + chr(key) + edit_buffer[cursor_pos:]
                cursor_pos += 1
    
    def apply_contact_change(self, new_name):
        """Apply organization name change to current tournament's primary contact"""
        tournament = self.tournaments[self.current_index]
        self.changes[tournament['id']] = new_name
        self.status_message = f"Will set organization to: {new_name}"
        
        if self.current_index < len(self.tournaments) - 1:
            self.move_selection(1)
    
    def skip_current(self):
        """Skip current tournament"""
        if self.current_index >= len(self.tournaments):
            return
            
        tournament = self.tournaments[self.current_index]
        tournament_id = tournament['id']
        
        if tournament_id in self.changes:
            del self.changes[tournament_id]
        
        self.skipped.add(tournament_id)
        self.status_message = f"Skipped: {tournament['primary_contact'][:40]}"
        if self.current_index < len(self.tournaments) - 1:
            self.move_selection(1)
    
    def bulk_skip_pattern(self):
        """Bulk skip tournaments with similar primary contact patterns"""
        if self.current_index >= len(self.tournaments):
            return
            
        current_tournament = self.tournaments[self.current_index]
        primary_contact = current_tournament['primary_contact'] or ""
        
        skipped_count = 0
        pattern = ""
        
        if 'discord.gg' in primary_contact.lower():
            pattern = "Discord URLs"
            for tournament in self.tournaments:
                if tournament['primary_contact'] and 'discord.gg' in tournament['primary_contact'].lower():
                    self.skipped.add(tournament['id'])
                    if tournament['id'] in self.changes:
                        del self.changes[tournament['id']]
                    skipped_count += 1
        elif '@' in primary_contact and '.com' in primary_contact:
            pattern = "Email addresses"
            for tournament in self.tournaments:
                contact = tournament['primary_contact'] or ""
                if '@' in contact and '.com' in contact:
                    self.skipped.add(tournament['id'])
                    if tournament['id'] in self.changes:
                        del self.changes[tournament['id']]
                    skipped_count += 1
        elif primary_contact.startswith('http'):
            pattern = "HTTP URLs"
            for tournament in self.tournaments:
                contact = tournament['primary_contact'] or ""
                if contact.startswith('http'):
                    self.skipped.add(tournament['id'])
                    if tournament['id'] in self.changes:
                        del self.changes[tournament['id']]
                    skipped_count += 1
        else:
            self.status_message = "No bulk skip pattern recognized"
            return
        
        self.status_message = f"Bulk skipped {skipped_count} {pattern}"
    
    def reset_current(self):
        """Reset current tournament"""
        if self.current_index >= len(self.tournaments):
            return
            
        tournament = self.tournaments[self.current_index]
        tournament_id = tournament['id']
        
        if tournament_id in self.changes:
            del self.changes[tournament_id]
            self.status_message = "Removed from changes"
        elif tournament_id in self.skipped:
            self.skipped.remove(tournament_id)
            self.status_message = "Removed from skipped"
        else:
            self.status_message = "Nothing to reset"
    
    def show_help(self):
        """Show help screen"""
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        
        help_text = [
            "Primary Contact Editor - Help",
            "",
            "Shows tournaments with un-named primary contacts that need",
            "to be converted to proper organization names.",
            "",
            "Navigation:",
            "  Up/Down      - Move between tournaments",
            "  Left/Right   - Jump by 5", 
            "  PgUp/PgDn    - Jump by 20",
            "",
            "Actions:",
            "  e            - Edit current tournament contact",
            "  s            - Skip current tournament",
            "  b            - Bulk skip similar contact patterns",
            "  r            - Reset current (undo changes/skip)",
            "  q            - Quit and save changes",
            "",
            "Edit Dialog:",
            "  Type         - Enter organization name in text field",
            "  1-20         - Select numbered suggestion",
            "  Enter        - Save current text field",
            "  q            - Quit from dialog",
            "  Esc          - Cancel",
            "",
            "Un-named contacts include emails, Discord URLs, raw",
            "usernames, and other contact data needing cleanup.",
            "",
            "Press any key to return..."
        ]
        
        for i, line in enumerate(help_text):
            if i < height - 1:
                attr = curses.A_BOLD if i == 0 else 0
                try:
                    self.stdscr.addstr(i, 2, line, attr)
                except curses.error:
                    pass
        
        self.stdscr.refresh()
        self.stdscr.getch()
    
    def confirm_quit(self):
        """Confirm quit with save dialog"""
        if not self.changes:
            return True
            
        height, width = self.stdscr.getmaxyx()
        
        dialog_width = 60
        dialog_height = 8
        start_y = (height - dialog_height) // 2
        start_x = (width - dialog_width) // 2
        
        for y in range(start_y, start_y + dialog_height):
            try:
                self.stdscr.addstr(y, start_x, " " * dialog_width, curses.color_pair(2))
            except curses.error:
                pass
        
        try:
            self.stdscr.addstr(start_y + 2, start_x + 2, 
                             f"Save {len(self.changes)} contact changes before quitting?", 
                              curses.color_pair(2) | curses.A_BOLD)
            self.stdscr.addstr(start_y + 4, start_x + 4, "y: Save and quit", curses.color_pair(2))
            self.stdscr.addstr(start_y + 5, start_x + 4, "n: Quit without saving", curses.color_pair(2))
            self.stdscr.addstr(start_y + 6, start_x + 4, "Esc: Cancel", curses.color_pair(2))
        except curses.error:
            pass
        
        self.stdscr.refresh()
        
        while True:
            key = self.stdscr.getch()
            if key == ord('y') or key == ord('Y'):
                return True
            elif key == ord('n') or key == ord('N'):
                self.changes = {}
                return True
            elif key == 27:  # Esc
                return False
    
    def save_changes(self):
        """Save changes to database - create/update organizations"""
        if not self.changes:
            return
            
        saved_count = 0
        
        for tournament_id, new_organization_name in self.changes.items():
            # Find the tournament
            tournament = Tournament.find(tournament_id)
            if not tournament:
                continue
            
            # Get or create organization with the new name
            normalized_key = normalize_contact(tournament.primary_contact)
            org = Organization.get_or_create(normalized_key, new_organization_name)
            
            # Update the organization's display name
            org.display_name = new_organization_name
            org.save()
            
            saved_count += 1
        
        height, width = self.stdscr.getmaxyx()
        completion_msg = f"Created/updated {saved_count} organizations. Press any key to exit."
        try:
            self.stdscr.clear()
            self.stdscr.addstr(height // 2, (width - len(completion_msg)) // 2, 
                              completion_msg, curses.A_BOLD)
            self.stdscr.refresh()
            self.stdscr.getch()
        except curses.error:
            pass

def main_curses(stdscr):
    """Main function for curses interface"""
    editor = MultiColumnContactEditor(stdscr)
    editor.run()

def run_contact_editor():
    """Launch the multi-column primary contact editor"""
    print("Initializing database...")
    try:
        init_db()
        print("Database initialized successfully")
        
        curses.wrapper(main_curses)
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure tournament_models.py and database_utils.py exist.")
        return
    except KeyboardInterrupt:
        print("\nEditor interrupted")
    except Exception as e:
        print(f"Editor error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Starting primary contact editor...")
    print("Loading tournaments with un-named primary contacts...")
    run_contact_editor()
