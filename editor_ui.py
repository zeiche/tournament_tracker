#!/usr/bin/env python3
"""
editor_ui.py - Curses TUI for organization name cleanup
UI layer separated from business logic
"""
import curses
from editor import OrganizationEditor

class MultiColumnNameEditorUI:
    """Multi-column curses TUI interface"""
    
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.editor = OrganizationEditor()
        self.current_index = 0
        self.scroll_offset = 0
        self.status_message = ""
        
        curses.curs_set(0)
        if curses.has_colors():
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
            curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
            curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
            curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)
            curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)
            curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)
    
    def run(self):
        """Main TUI loop"""
        self.status_message = "Loading un-named organization data..."
        self.draw_screen()
        
        org_count = self.editor.load_organizations()
        
        if org_count == 0:
            self.status_message = "No organizations need naming"
            self.draw_screen()
            self.stdscr.getch()
            return
        
        self.status_message = f"Loaded {org_count} organizations needing names. Use arrows, 'e' to edit, 'q' to quit."
        
        while True:
            self.draw_screen()
            key = self.stdscr.getch()
            
            # Dictionary dispatch for main navigation keys
            def quit_handler():
                return self.confirm_quit()
            
            def edit_handler():
                return self.start_edit_mode()
            
            def skip_handler():
                self.skip_current()
                return False
            
            def bulk_skip_handler():
                self.bulk_skip_pattern()
                return False
            
            def reset_handler():
                self.reset_current()
                return False
            
            def help_handler():
                self.show_help()
                return False
            
            key_handlers = {
                ord('q'): quit_handler,
                ord('Q'): quit_handler,
                curses.KEY_UP: lambda: self.move_selection(-1) or False,
                curses.KEY_DOWN: lambda: self.move_selection(1) or False,
                curses.KEY_LEFT: lambda: self.move_selection(-5) or False,
                curses.KEY_RIGHT: lambda: self.move_selection(5) or False,
                curses.KEY_PPAGE: lambda: self.move_selection(-20) or False,
                curses.KEY_NPAGE: lambda: self.move_selection(20) or False,
                ord('e'): edit_handler,
                ord('E'): edit_handler,
                ord('s'): skip_handler,
                ord('S'): skip_handler,
                ord('b'): bulk_skip_handler,
                ord('B'): bulk_skip_handler,
                ord('r'): reset_handler,
                ord('R'): reset_handler,
                ord('h'): help_handler,
                ord('H'): help_handler
            }
            
            if key in key_handlers:
                should_break = key_handlers[key]()
                if should_break:
                    break
        
        self.save_and_exit()
    
    def move_selection(self, delta):
        """Move selection with proper bounds checking"""
        old_index = self.current_index
        self.current_index = max(0, min(len(self.editor.organizations) - 1, self.current_index + delta))
        
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
        """Draw the multi-column organization list"""
        self.stdscr.clear()
        height, width = self.stdscr.getmaxyx()
        
        try:
            header = "Organization Name Editor - Un-named Organizations"
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
            org_index = self.scroll_offset + i
            if org_index >= len(self.editor.organizations):
                break
                
            org = self.editor.organizations[org_index]
            
            col = i // rows_per_column
            row = i % rows_per_column
            x = col * column_width
            y = 2 + row
            
            if x + column_width > width or y >= 2 + available_height:
                break
            
            display_name = self.editor.get_display_name(org)[:35]
            attendance = org['total_attendance']
            
            entry_text = f"{org_index+1:3d}. {display_name:<30} {attendance:>4}"
            
            attr = 0
            if org_index == self.current_index:
                attr |= curses.color_pair(2) | curses.A_BOLD
            else:
                attr |= self.get_name_color_attr(org)
            
            try:
                self.stdscr.addstr(y, x, entry_text[:column_width-1], attr)
            except curses.error:
                pass
        
        if self.editor.organizations and 0 <= self.current_index < len(self.editor.organizations):
            self.draw_current_org_details(height, width)
        
        if self.status_message:
            try:
                self.stdscr.addstr(height - 2, 1, self.status_message[:width-2], curses.color_pair(5))
            except curses.error:
                pass
        
        stats = self.editor.get_stats()
        current_page = (self.current_index // items_per_page) + 1 if items_per_page > 0 else 1
        total_pages = ((len(self.editor.organizations) - 1) // items_per_page) + 1 if self.editor.organizations and items_per_page > 0 else 1
        progress = f"[{self.current_index + 1}/{stats['total_organizations']}] Page {current_page}/{total_pages}"
        stats_text = f"{progress} Changed: {stats['changes_pending']}, Skipped: {stats['organizations_skipped']}"
        try:
            self.stdscr.addstr(height - 1, 1, stats_text[:width-2])
        except curses.error:
            pass
        
        self.stdscr.refresh()
    
    def draw_current_org_details(self, height, width):
        """Draw detailed info for current organization at bottom"""
        org = self.editor.organizations[self.current_index]
        detail_start_y = height - 8
        
        try:
            self.stdscr.addstr(detail_start_y, 0, "-" * width)
            
            y = detail_start_y + 1
            current_name = self.editor.get_display_name(org)
            self.stdscr.addstr(y, 1, f"Selected: {current_name}", 
                              self.get_name_color(org) | curses.A_BOLD)
            
            y += 1
            self.stdscr.addstr(y, 1, f"Stats: {org['total_attendance']:,} attendance across {org['tournament_count']} tournaments")
            
            y += 1
            contacts = org['contacts'][:2] if org['contacts'] else []
            contacts_text = f"Contacts: {', '.join(contacts)}"
            if len(org['contacts']) > 2:
                contacts_text += f" + {len(org['contacts']) - 2} more"
            self.stdscr.addstr(y, 1, contacts_text[:width-2])
            
            y += 1
            tournament_slugs = self.editor.get_tournament_slugs(org['normalized_key'])
            if tournament_slugs:
                first_slug = tournament_slugs[0]
                if first_slug.startswith('tournament/'):
                    startgg_url = f"https://start.gg/{first_slug}"
                else:
                    startgg_url = f"https://start.gg/tournament/{first_slug}"
                
                self.stdscr.addstr(y, 1, f"URL: {startgg_url}", curses.color_pair(6))
            else:
                self.stdscr.addstr(y, 1, "URL: No tournament slugs found", curses.color_pair(4))
                
        except curses.error:
            pass
    
    def get_name_color(self, org):
        """Get color pair for organization name"""
        if self.editor.has_changes(org):
            return curses.color_pair(3)
        elif self.editor.is_skipped(org):
            return curses.color_pair(4)
        return 0
    
    def get_name_color_attr(self, org):
        """Get color attribute"""
        return self.get_name_color(org)
    
    def start_edit_mode(self):
        """Show edit dialog for current organization"""
        if self.current_index >= len(self.editor.organizations):
            return False
            
        org = self.editor.organizations[self.current_index]
        current_name = self.editor.get_display_name(org)
        
        return self.show_edit_dialog(current_name)
    
    def show_edit_dialog(self, current_name):
        """Show edit dialog with manually entered names as reference"""
        height, width = self.stdscr.getmaxyx()
        
        dialog_width = min(80, width - 4)
        dialog_height = min(28, height - 4)
        start_y = (height - dialog_height) // 2
        start_x = (width - dialog_width) // 2
        
        # Draw dialog background
        for y in range(start_y, start_y + dialog_height):
            try:
                self.stdscr.addstr(y, start_x, " " * dialog_width, curses.color_pair(2))
            except curses.error:
                pass
        
        try:
            self.stdscr.addstr(start_y + 1, start_x + 2, "Enter organization name:", 
                              curses.color_pair(2) | curses.A_BOLD)
            
            current_truncated = current_name[:dialog_width-15] 
            self.stdscr.addstr(start_y + 2, start_x + 2, f"Current: {current_truncated}", 
                              curses.color_pair(2))
            
            self.stdscr.addstr(start_y + 4, start_x + 2, "New name:", 
                              curses.color_pair(2) | curses.A_BOLD)
            self.stdscr.addstr(start_y + 5, start_x + 2, "> ", curses.color_pair(2))
        except curses.error:
            pass
        
        # Show previously entered names as reference
        suggestions_per_column = 10
        col_width = (dialog_width - 6) // 2
        
        current_suggestions = self.editor.get_current_suggestions_page()
        current_page, total_pages = self.editor.get_suggestions_page_info()
        
        # Only show reference names if we have any
        if current_suggestions:
            try:
                self.stdscr.addstr(start_y + 7, start_x + 2, "Previously entered names (reference only):", 
                                  curses.color_pair(2) | curses.A_BOLD)
            except curses.error:
                pass
            
            for i, suggestion in enumerate(current_suggestions):
                col = i // suggestions_per_column
                row = i % suggestions_per_column
                
                x_offset = start_x + 2 + (col * col_width)
                y_offset = start_y + 9 + row
                
                # Show as reference only (no numbers)
                suggestion_text = f"• {suggestion[:col_width-3]}"
                
                try:
                    self.stdscr.addstr(y_offset, x_offset, suggestion_text, curses.color_pair(2))
                except curses.error:
                    break
            
            # Add pagination info
            if total_pages > 1:
                page_info = f"Page {current_page}/{total_pages} - Use '[' and ']' to navigate"
                try:
                    self.stdscr.addstr(start_y + 20, start_x + 2, page_info[:dialog_width-4], curses.color_pair(2))
                except curses.error:
                    pass
        
        instruction_y = start_y + dialog_height - 2
        try:
            self.stdscr.addstr(instruction_y, start_x + 2, 
                              "Type name above, Enter to save, 'q' to quit, Esc to cancel", 
                              curses.color_pair(2) | curses.A_BOLD)
        except curses.error:
            pass
        
        self.stdscr.refresh()
        
        # Handle text input
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
            
            if key == 27:  # Escape
                curses.curs_set(0)
                return False
            elif key == ord('q') or key == ord('Q'):
                curses.curs_set(0)
                return True
            elif key == ord('\n') or key == curses.KEY_ENTER or key == 10:
                if edit_buffer.strip():
                    self.apply_name_change(edit_buffer.strip())
                    curses.curs_set(0)
                    return False
            elif key == ord('['):
                if self.editor.prev_suggestions_page():
                    # Redraw dialog with new page
                    return self.show_edit_dialog(current_name)
            elif key == ord(']'):
                if self.editor.next_suggestions_page():
                    # Redraw dialog with new page  
                    return self.show_edit_dialog(current_name)
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
            elif 32 <= key <= 126:  # Printable characters
                edit_buffer = edit_buffer[:cursor_pos] + chr(key) + edit_buffer[cursor_pos:]
                cursor_pos += 1
    
    def apply_name_change(self, new_name):
        """Apply a name change to current organization"""
        if self.editor.apply_name_change(self.current_index, new_name):
            self.status_message = f"Changed to: {new_name}"
            
            if self.current_index < len(self.editor.organizations) - 1:
                self.move_selection(1)
    
    def skip_current(self):
        """Skip current organization"""
        display_name = self.editor.skip_organization(self.current_index)
        if display_name:
            self.status_message = f"Skipped: {display_name[:40]}"
            self.move_selection(1)
    
    def bulk_skip_pattern(self):
        """Bulk skip organizations matching pattern"""
        skipped_count, message = self.editor.bulk_skip_pattern(self.current_index)
        self.status_message = message
    
    def reset_current(self):
        """Reset current organization"""
        message = self.editor.reset_organization(self.current_index)
        self.status_message = message
    
    def show_help(self):
        """Show help screen"""
        self.stdscr.clear()
        
        help_text = [
            "Organization Name Editor - Help",
            "",
            "Shows only organizations needing names (emails/discord handles).",
            "",
            "Navigation:",
            "  Up/Down      - Move between organizations",
            "  Left/Right   - Jump by 5", 
            "  PgUp/PgDn    - Jump by 20",
            "",
            "Actions:",
            "  e            - Edit current organization",
            "  s            - Skip current organization",
            "  b            - Bulk skip similar organizations",
            "  r            - Reset current (undo changes/skip)",
            "  q            - Quit and save changes",
            "",
            "Edit Dialog:",
            "  Type         - Enter custom name",
            "  Enter        - Save name",
            "  [ ]          - Navigate reference names",
            "  q            - Quit from dialog",
            "  Esc          - Cancel",
            "",
            "Reference names shown are previously manually entered.",
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
        stats = self.editor.get_stats()
        if stats['changes_pending'] == 0:
            return True
            
        height, width = self.stdscr.getmaxyx()
        
        dialog_width = 60
        dialog_height = 8  # Fixed typo: was "dilog_height"
        start_y = (height - dialog_height) // 2
        start_x = (width - dialog_width) // 2
        
        for y in range(start_y, start_y + dialog_height):
            try:
                self.stdscr.addstr(y, start_x, " " * dialog_width, curses.color_pair(2))
            except curses.error:
                pass
        
        try:
            self.stdscr.addstr(start_y + 2, start_x + 2, 
                              f"Save {stats['changes_pending']} changes before quitting?", 
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
                self.editor.changes = {}
                return True
            elif key == 27:
                return False
    
    def save_and_exit(self):
        """Save changes and show completion message"""
        saved_count = self.editor.save_changes()
        
        if saved_count > 0:
            height, width = self.stdscr.getmaxyx()
            completion_msg = f"Saved {saved_count} changes to database. Press any key to exit."
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
    editor_ui = MultiColumnNameEditorUI(stdscr)
    editor_ui.run()

def run_editor_ui():
    """Launch the multi-column name editor UI"""
    try:
        curses.wrapper(main_curses)
    except KeyboardInterrupt:
        print("\nEditor interrupted")
    except Exception as e:
        print(f"Editor UI error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Starting organization name editor UI...")
    from models import init_db
    init_db()
    run_editor_ui()
