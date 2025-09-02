#!/usr/bin/env python3
"""
Curses-based AI Chat Interface for Tournament Tracker
Terminal UI for chatting with the AI assistant
"""

import curses
import sys
import os
from datetime import datetime
from typing import List, Tuple

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_service import get_ai_service, ChannelType

class CursesAIChat:
    """Terminal-based AI chat interface"""
    
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.ai_service = get_ai_service()
        self.messages: List[Tuple[str, str, str]] = []  # (sender, message, time)
        self.input_buffer = ""
        self.mode = ChannelType.CURSES
        self.scroll_offset = 0
        
        # Initialize colors
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)    # Header
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)   # User messages
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # AI messages
        curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)   # Input
        curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK) # Status
        
        # Setup screen
        self.setup_screen()
        
        # Add welcome message
        self.add_message("AI", "Welcome to Tournament Tracker AI! I can help with tournament stats, rankings, or just chat. Type /help for commands.")
    
    def setup_screen(self):
        """Setup the curses screen"""
        self.stdscr.clear()
        curses.curs_set(1)  # Show cursor
        self.stdscr.keypad(True)
        
        # Get dimensions
        self.height, self.width = self.stdscr.getmaxyx()
        
        # Define regions
        self.header_height = 3
        self.footer_height = 3
        self.chat_height = self.height - self.header_height - self.footer_height
    
    def draw_header(self):
        """Draw the header"""
        header_text = "🎮 Tournament Tracker AI Chat"
        mode_text = f"Mode: {self.mode.value}"
        
        self.stdscr.attron(curses.color_pair(1))
        self.stdscr.addstr(0, 2, "═" * (self.width - 4))
        self.stdscr.addstr(1, 2, header_text.center(self.width - 4))
        self.stdscr.addstr(1, self.width - len(mode_text) - 3, mode_text)
        self.stdscr.addstr(2, 2, "═" * (self.width - 4))
        self.stdscr.attroff(curses.color_pair(1))
    
    def draw_messages(self):
        """Draw the chat messages"""
        chat_start = self.header_height
        
        # Calculate visible messages
        visible_messages = []
        y = 0
        
        for sender, message, timestamp in self.messages[-50:]:  # Keep last 50 messages
            # Word wrap long messages
            wrapped_lines = self.wrap_text(f"[{timestamp}] {sender}: {message}", self.width - 4)
            visible_messages.extend([(sender, line) for line in wrapped_lines])
        
        # Apply scroll
        start_idx = max(0, len(visible_messages) - self.chat_height + self.scroll_offset)
        end_idx = start_idx + self.chat_height
        
        # Draw visible messages
        for i, (sender, line) in enumerate(visible_messages[start_idx:end_idx]):
            if i >= self.chat_height:
                break
            
            y = chat_start + i
            if sender == "You":
                self.stdscr.attron(curses.color_pair(2))
            else:
                self.stdscr.attron(curses.color_pair(3))
            
            try:
                self.stdscr.addstr(y, 2, line[:self.width-4])
            except:
                pass  # Ignore errors at screen edge
            
            self.stdscr.attroff(curses.color_pair(2))
            self.stdscr.attroff(curses.color_pair(3))
    
    def draw_input(self):
        """Draw the input area"""
        input_y = self.height - self.footer_height
        
        self.stdscr.attron(curses.color_pair(4))
        self.stdscr.addstr(input_y, 2, "─" * (self.width - 4))
        self.stdscr.addstr(input_y + 1, 2, "> " + self.input_buffer[-self.width+6:])
        self.stdscr.attroff(curses.color_pair(4))
        
        # Draw help text
        help_text = "Enter: Send | /mode: Change mode | /clear: Clear | /quit: Exit"
        self.stdscr.attron(curses.color_pair(5))
        try:
            self.stdscr.addstr(input_y + 2, 2, help_text[:self.width-4])
        except:
            pass
        self.stdscr.attroff(curses.color_pair(5))
    
    def wrap_text(self, text: str, width: int) -> List[str]:
        """Wrap text to fit within width"""
        lines = []
        words = text.split()
        current_line = ""
        
        for word in words:
            if len(current_line) + len(word) + 1 <= width:
                current_line += word + " "
            else:
                if current_line:
                    lines.append(current_line.strip())
                current_line = word + " "
        
        if current_line:
            lines.append(current_line.strip())
        
        return lines if lines else [""]
    
    def add_message(self, sender: str, message: str):
        """Add a message to the chat"""
        timestamp = datetime.now().strftime("%H:%M")
        self.messages.append((sender, message, timestamp))
        self.scroll_offset = 0  # Reset scroll to bottom
    
    def process_command(self, command: str):
        """Process special commands"""
        if command == "/quit" or command == "/exit":
            return False
        
        elif command == "/clear":
            self.messages.clear()
            self.add_message("System", "Chat cleared")
        
        elif command == "/help":
            help_text = """Commands:
/mode [general|stats|dev] - Change AI mode
/clear - Clear chat history
/quit or /exit - Exit chat
/stats - Show database statistics
/top - Show top organizations"""
            self.add_message("System", help_text)
        
        elif command.startswith("/mode "):
            mode = command.split()[1].lower()
            mode_map = {
                'general': ChannelType.CURSES,
                'stats': ChannelType.STATS,
                'dev': ChannelType.DEVELOPER,
                'developer': ChannelType.DEVELOPER
            }
            if mode in mode_map:
                self.mode = mode_map[mode]
                self.add_message("System", f"Mode changed to: {mode}")
            else:
                self.add_message("System", "Invalid mode. Use: general, stats, or dev")
        
        elif command == "/stats":
            self.add_message("You", "Show me the tournament statistics")
            self.get_ai_response("Show me the tournament statistics")
        
        elif command == "/top":
            self.add_message("You", "Show me the top organizations")
            self.get_ai_response("Show me the top organizations")
        
        else:
            self.add_message("System", f"Unknown command: {command}")
        
        return True
    
    def get_ai_response(self, message: str):
        """Get response from AI service"""
        self.add_message("AI", "Thinking...")
        self.draw()
        self.stdscr.refresh()
        
        # Get actual response
        context = {'interface': 'curses'}
        response = self.ai_service.get_response_sync(message, self.mode, context)
        
        # Replace thinking message
        self.messages[-1] = ("AI", response, datetime.now().strftime("%H:%M"))
    
    def draw(self):
        """Draw the entire interface"""
        self.stdscr.clear()
        self.draw_header()
        self.draw_messages()
        self.draw_input()
    
    def run(self):
        """Main loop"""
        while True:
            self.draw()
            
            # Position cursor
            cursor_x = 4 + len(self.input_buffer)
            cursor_y = self.height - 2
            if cursor_x < self.width - 2:
                self.stdscr.move(cursor_y, cursor_x)
            
            self.stdscr.refresh()
            
            # Get input
            try:
                key = self.stdscr.getch()
                
                if key == ord('\n'):  # Enter
                    if self.input_buffer.strip():
                        message = self.input_buffer.strip()
                        self.input_buffer = ""
                        
                        if message.startswith('/'):
                            if not self.process_command(message):
                                break
                        else:
                            self.add_message("You", message)
                            self.get_ai_response(message)
                
                elif key == curses.KEY_BACKSPACE or key == 127:
                    if self.input_buffer:
                        self.input_buffer = self.input_buffer[:-1]
                
                elif key == curses.KEY_UP:
                    self.scroll_offset = min(self.scroll_offset + 1, 10)
                
                elif key == curses.KEY_DOWN:
                    self.scroll_offset = max(self.scroll_offset - 1, 0)
                
                elif key == 27:  # ESC
                    break
                
                elif 32 <= key <= 126:  # Printable characters
                    self.input_buffer += chr(key)
                
            except KeyboardInterrupt:
                break

def main(stdscr):
    """Main function"""
    chat = CursesAIChat(stdscr)
    chat.run()

if __name__ == "__main__":
    # Check if AI is available
    ai = get_ai_service()
    if not ai.enabled:
        print("⚠️  Warning: AI service not enabled. Using fallback responses.")
        print("Set ANTHROPIC_API_KEY to enable full AI capabilities.")
        input("Press Enter to continue...")
    
    curses.wrapper(main)