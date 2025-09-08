#!/usr/bin/env python3
"""
demo_polymorphic.py - Simple demonstration of the polymorphic pattern

Shows how ALL modules now use just ask/tell/do instead of 200+ methods
"""


class SimplePolymorphic:
    """Minimal polymorphic base for demonstration"""
    
    def ask(self, question):
        """Ask anything - object figures out intent"""
        q = str(question).lower()
        if 'status' in q:
            return "Active"
        if 'help' in q:
            return "Use ask/tell/do"
        return f"Unknown question: {question}"
    
    def tell(self, format="default"):
        """Tell in any format"""
        if format == "json":
            return '{"class": "SimplePolymorphic"}'
        return f"{self.__class__.__name__}"
    
    def do(self, action):
        """Do any action"""
        if 'test' in str(action).lower():
            return "Test successful"
        return f"Unknown action: {action}"


class DemoGo(SimplePolymorphic):
    """Demonstration of go.py using polymorphic pattern"""
    
    def __init__(self):
        self.services = ['discord', 'twilio', 'sync', 'editor']
    
    def ask(self, question):
        q = str(question).lower()
        if 'services' in q:
            return self.services
        if 'running' in q:
            return ["discord", "twilio"]  # Mock running services
        return super().ask(question)
    
    def do(self, action):
        act = str(action).lower()
        if 'start' in act:
            for service in self.services:
                if service in act:
                    return f"Starting {service}..."
        if 'sync' in act:
            return "Running sync..."
        return super().do(action)


class DemoDiscord(SimplePolymorphic):
    """Demonstration of Discord bridge using polymorphic pattern"""
    
    def __init__(self):
        self.connected = False
    
    def ask(self, question):
        q = str(question).lower()
        if 'connected' in q:
            return self.connected
        if 'channel' in q:
            return "#general" if self.connected else None
        return super().ask(question)
    
    def do(self, action):
        act = str(action).lower()
        if 'connect' in act:
            self.connected = True
            return "Connected to Discord"
        if 'send' in act:
            return "Message sent" if self.connected else "Not connected"
        return super().do(action)


class DemoTwilio(SimplePolymorphic):
    """Demonstration of Twilio bridge using polymorphic pattern"""
    
    def __init__(self):
        self.phone = "+1-878-879-4283"
    
    def ask(self, question):
        q = str(question).lower()
        if 'phone' in q:
            return self.phone
        if 'webhook' in q:
            return "Running on port 8082"
        return super().ask(question)
    
    def do(self, action):
        act = str(action).lower()
        if 'call' in act:
            return "Making call..."
        if 'sms' in act:
            return "Sending SMS..."
        return super().do(action)


class DemoTournament(SimplePolymorphic):
    """Demonstration of Tournament model using polymorphic pattern"""
    
    def __init__(self, name="Demo Tournament"):
        self.name = name
        self.attendees = 64
    
    def ask(self, question):
        q = str(question).lower()
        if 'winner' in q:
            return "Player WEST"
        if 'top' in q and '8' in q:
            return ["WEST", "EAST", "NORTH", "SOUTH", "UP", "DOWN", "LEFT", "RIGHT"]
        if 'attendance' in q:
            return self.attendees
        return super().ask(question)
    
    def tell(self, format="default"):
        if format == "discord":
            return f"**{self.name}** - {self.attendees} players"
        if format == "json":
            return f'{{"name": "{self.name}", "attendees": {self.attendees}}}'
        return super().tell(format)


def demonstrate():
    """Show the polymorphic pattern in action"""
    
    print("=" * 70)
    print("POLYMORPHIC PATTERN DEMONSTRATION")
    print("=" * 70)
    
    print("\n🎮 GO.PY - The Entry Point")
    print("-" * 40)
    go = DemoGo()
    print(f"go.ask('what services'): {go.ask('what services')}")
    print(f"go.ask('running'): {go.ask('running')}")
    print(f"go.do('start discord'): {go.do('start discord')}")
    print(f"go.do('sync'): {go.do('sync')}")
    
    print("\n💬 DISCORD BRIDGE")
    print("-" * 40)
    discord = DemoDiscord()
    print(f"discord.ask('connected'): {discord.ask('connected')}")
    print(f"discord.do('connect'): {discord.do('connect')}")
    print(f"discord.ask('connected'): {discord.ask('connected')}")
    print(f"discord.ask('channel'): {discord.ask('channel')}")
    print(f"discord.do('send message'): {discord.do('send message')}")
    
    print("\n📞 TWILIO BRIDGE")
    print("-" * 40)
    twilio = DemoTwilio()
    print(f"twilio.ask('phone'): {twilio.ask('phone')}")
    print(f"twilio.ask('webhook'): {twilio.ask('webhook')}")
    print(f"twilio.do('call 555-1234'): {twilio.do('call 555-1234')}")
    print(f"twilio.do('send sms'): {twilio.do('send sms')}")
    
    print("\n🏆 TOURNAMENT MODEL")
    print("-" * 40)
    tournament = DemoTournament("SoCal Regionals")
    print(f"tournament.ask('winner'): {tournament.ask('winner')}")
    print(f"tournament.ask('top 8'): {tournament.ask('top 8')}")
    print(f"tournament.ask('attendance'): {tournament.ask('attendance')}")
    print(f"tournament.tell('discord'): {tournament.tell('discord')}")
    print(f"tournament.tell('json'): {tournament.tell('json')}")
    
    print("\n" + "=" * 70)
    print("KEY INSIGHTS")
    print("=" * 70)
    print("""
✅ EVERYTHING uses just 3 methods: ask(), tell(), do()
✅ No more memorizing 200+ method names
✅ Objects understand intent polymorphically
✅ Consistent interface across all modules
✅ Natural language instead of rigid syntax

OLD WAY (Hard to remember):
- go.py --discord-bot
- discord.connect()
- twilio.make_call(number)
- tournament.get_winner()
- tournament.get_top_8_placements()
- organization.calculate_total_attendance()

NEW WAY (Simple and consistent):
- go.do("start discord")
- discord.do("connect")
- twilio.do("call 555-1234")
- tournament.ask("winner")
- tournament.ask("top 8")
- organization.ask("total attendance")

The objects FIGURE OUT what you want!
""")


if __name__ == "__main__":
    demonstrate()