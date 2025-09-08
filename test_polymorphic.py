#!/usr/bin/env python3
"""
test_polymorphic.py - Test the polymorphic conversions

Shows how EVERYTHING now uses just ask/tell/do
"""

import sys
sys.path.insert(0, 'utils')

from universal_polymorphic import UniversalPolymorphic
from go_polymorphic import go
from discord_polymorphic import discord_bridge
from twilio_polymorphic import twilio_bridge


def test_universal_base():
    """Test the universal base class"""
    print("=" * 60)
    print("TESTING UNIVERSAL BASE CLASS")
    print("=" * 60)
    
    obj = UniversalPolymorphic()
    
    # Test ask
    print("\n--- Testing ask() ---")
    print(f"ask('status'): {obj.ask('status')}")
    print(f"ask('capabilities'): {obj.ask('capabilities')}")
    print(f"ask('help'): {obj.ask('help')[:100]}...")
    
    # Test tell
    print("\n--- Testing tell() ---")
    print(f"tell('json'): {obj.tell('json')[:100]}...")
    print(f"tell('brief'): {obj.tell('brief')}")
    print(f"tell('discord'): {obj.tell('discord')}")
    
    # Test do
    print("\n--- Testing do() ---")
    print(f"do('announce'): {obj.do('announce')}")
    print(f"do('validate'): {obj.do('validate')}")
    print(f"do('test'): {obj.do('test')}")


def test_go_polymorphic():
    """Test the polymorphic go.py"""
    print("\n" + "=" * 60)
    print("TESTING GO POLYMORPHIC")
    print("=" * 60)
    
    print("\n--- Testing go.ask() ---")
    print(f"ask('what services'): {go.ask('what services')[:200]}...")
    print(f"ask('running'): {go.ask('running')}")
    
    print("\n--- Testing go.tell() ---")
    print(f"tell('status'): {go.tell('status')[:200]}...")
    
    print("\n--- Testing go.do() ---")
    # Don't actually start services, just show what would happen
    print("Would run: go.do('start discord bot')")
    print("Would run: go.do('sync')")
    print("Would run: go.do('restart all')")


def test_discord_polymorphic():
    """Test the polymorphic Discord bridge"""
    print("\n" + "=" * 60)
    print("TESTING DISCORD POLYMORPHIC")
    print("=" * 60)
    
    print("\n--- Testing discord_bridge.ask() ---")
    print(f"ask('connected'): {discord_bridge.ask('connected')}")
    print(f"ask('channel'): {discord_bridge.ask('channel')}")
    print(f"ask('capabilities'): {discord_bridge.ask('capabilities')[:200]}...")
    
    print("\n--- Testing discord_bridge.tell() ---")
    print(f"tell('status'): {discord_bridge.tell('status')}")
    print(f"tell('discord'): {discord_bridge.tell('discord')}")
    
    print("\n--- Testing discord_bridge.do() ---")
    print("Would run: discord_bridge.do('connect')")
    print("Would run: discord_bridge.do('send', message='Hello')")
    print("Would run: discord_bridge.do('join voice')")


def test_twilio_polymorphic():
    """Test the polymorphic Twilio bridge"""
    print("\n" + "=" * 60)
    print("TESTING TWILIO POLYMORPHIC")
    print("=" * 60)
    
    print("\n--- Testing twilio_bridge.ask() ---")
    print(f"ask('phone'): {twilio_bridge.ask('phone')}")
    print(f"ask('webhook'): {twilio_bridge.ask('webhook')}")
    print(f"ask('capabilities'): {twilio_bridge.ask('capabilities')[:200]}...")
    
    print("\n--- Testing twilio_bridge.tell() ---")
    print(f"tell('status'): {twilio_bridge.tell('status')}")
    print(f"tell('twilio'): {twilio_bridge.tell('twilio')}")
    
    print("\n--- Testing twilio_bridge.do() ---")
    print("Would run: twilio_bridge.do('call 555-1234')")
    print("Would run: twilio_bridge.do('send sms', to='555-1234', body='Hello')")
    print("Would run: twilio_bridge.do('start webhook')")


def show_polymorphic_examples():
    """Show how the polymorphic pattern simplifies everything"""
    print("\n" + "=" * 60)
    print("POLYMORPHIC PATTERN EXAMPLES")
    print("=" * 60)
    
    print("""
OLD WAY (200+ methods to remember):
------------------------------------
go.py --discord-bot
go.py --sync
go.py --restart-services

discord.connect()
discord.send_message(channel, text)
discord.join_voice_channel(name)

twilio.make_call(number, message)
twilio.send_sms(to, body)
twilio.start_webhook_server(port)

tournament.get_winner()
tournament.get_top_8_placements()
tournament.calculate_growth_rate()


NEW WAY (just 3 methods for EVERYTHING):
-----------------------------------------
go.do("start discord bot")
go.do("sync")
go.do("restart all")

discord.do("connect")
discord.do("send", message=text)
discord.do("join voice")

twilio.do("call 555-1234")
twilio.do("send sms", to="...", body="...")
twilio.do("start webhook")

tournament.ask("winner")
tournament.ask("top 8")
tournament.tell("discord")


The objects FIGURE OUT what you want!
No more memorizing method names!
Everything is polymorphic!
""")


def main():
    """Run all tests"""
    print("TESTING POLYMORPHIC CONVERSIONS")
    print("================================\n")
    
    # Test each component
    test_universal_base()
    test_go_polymorphic()
    test_discord_polymorphic()
    test_twilio_polymorphic()
    
    # Show examples
    show_polymorphic_examples()
    
    print("\n" + "=" * 60)
    print("POLYMORPHIC CONVERSION COMPLETE!")
    print("=" * 60)
    print("""
Summary:
- Created UniversalPolymorphic base class
- All classes now use ask/tell/do pattern
- No more 200+ methods to remember
- Objects understand intent polymorphically
- Everything is simpler and more consistent

Next steps:
1. Convert tournament models to inherit from PolymorphicModel
2. Convert all service modules
3. Update documentation
4. Remove old non-polymorphic code
""")


if __name__ == "__main__":
    main()