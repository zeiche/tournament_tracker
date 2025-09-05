#!/usr/bin/env python3
"""
Discord Conversational Bot for Tournament Tracker
Natural language interface to tournament data
"""
import discord
import asyncio
import os
import sys
from datetime import datetime
import random

# Add tournament_tracker to path
sys.path.insert(0, '/home/ubuntu/claude/tournament_tracker')

# Import tournament tracker modules
from conversational_search import ConversationalSearch
from database import session_scope
from database_service import database_service
from tournament_models import Tournament, Organization, Player
from formatters import PlayerFormatter
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def handle_player_stats_query(message, player_name):
    """Handle player stats requests using the Pythonic approach"""
    try:
        logger.info(f"Looking for player stats: {player_name}")
        
        with session_scope() as session:
            # Search for player by gamer_tag or name (case insensitive)
            player = session.query(Player).filter(
                (Player.gamer_tag.ilike(f"%{player_name}%")) |
                (Player.name.ilike(f"%{player_name}%"))
            ).first()
            
            if not player:
                await message.channel.send(f"Sorry, I couldn't find a player named '{player_name}'. Try being more specific!")
                return
            
            # The Player object provides the data
            stats = player.get_stats() if hasattr(player, 'get_stats') else {}
            
            if not stats:
                await message.channel.send(f"No stats available for {player.gamer_tag or player.name}")
                return
            
            # Build player data for the formatter
            player_data = {
                'id': player.id,
                'name': player.gamer_tag or player.name or 'Unknown',
                'rank': 1,  # TODO: Calculate actual rank
                'total_points': stats.get('wins', 0) * 100 + stats.get('podiums', 0) * 25,
                'tournament_count': stats.get('total_tournaments', 0),
                'win_count': stats.get('wins', 0),
                'win_rate': stats.get('win_rate', 0),
                'podium_rate': stats.get('podium_rate', 0),
                'avg_placement': stats.get('average_placement', 0),
                'recent_results': []
            }
            
            # Add recent results
            if 'recent_results' in stats:
                player_data['recent_results'] = [
                    {
                        'tournament_name': r.get('tournament', 'Unknown'),
                        'placement': r.get('placement', 'N/A'),
                        'date': r.get('date', 'N/A')[:10] if r.get('date') else 'N/A'
                    }
                    for r in stats['recent_results'][:5]  # Top 5 recent
                ]
            
            # Use the PlayerFormatter to format for Discord
            discord_message = PlayerFormatter.format_discord(player_data)
            
            # Discord has message length limits, so send in chunks if needed
            if len(discord_message) > 2000:
                # Split the message at natural break points
                parts = discord_message.split('\\n\\n')
                current_message = ""
                
                for part in parts:
                    if len(current_message + part) > 1900:  # Leave some room
                        await message.channel.send(current_message)
                        current_message = part
                    else:
                        current_message += "\\n\\n" + part if current_message else part
                
                if current_message:
                    await message.channel.send(current_message)
            else:
                await message.channel.send(discord_message)
    
    except Exception as e:
        logger.error(f"Error handling player stats query: {e}")
        await message.channel.send(f"Sorry, I had trouble getting stats for {player_name}. Please try again!")

# Bot token - set via environment variable
TOKEN = os.getenv('DISCORD_BOT_TOKEN', '')

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

client = discord.Client(intents=intents)

# Initialize conversational search
search_engine = ConversationalSearch()

# Response patterns
GREETINGS = ['hello', 'hi', 'hey', 'greetings', 'yo', 'sup', 'howdy']
FAREWELLS = ['bye', 'goodbye', 'see you', 'later', 'farewell', 'cya']

@client.event
async def on_ready():
    print(f'[{datetime.now()}] Tournament Tracker Bot is ready!')
    print(f'Logged in as: {client.user.name} ({client.user.id})')
    print(f'Connected to {len(client.guilds)} guild(s):')
    for guild in client.guilds:
        print(f'  - {guild.name} ({guild.id})')
    print('-' * 50)
    
    # Set status
    await client.change_presence(
        activity=discord.Game(name="Tracking FGC tournaments"),
        status=discord.Status.online
    )

@client.event
async def on_message(message):
    # Don't respond to ourselves or other bots
    if message.author == client.user or message.author.bot:
        return
    
    content_lower = message.content.lower()
    
    # Log the message
    logger.info(f'{message.author}: {message.content}')
    
    # Check for player stats queries first (more specific)
    if any(phrase in content_lower for phrase in ['stats for', 'show me stats', 'player stats', 'stats of']):
        # Extract player name from natural language
        import re
        
        # Common patterns for asking about player stats
        patterns = [
            r'stats for ([a-zA-Z0-9_]+)',
            r'show me.*stats.*for ([a-zA-Z0-9_]+)',
            r'show.*stats.*([a-zA-Z0-9_]+)',
            r'([a-zA-Z0-9_]+).*stats',
            r'stats.*([a-zA-Z0-9_]+)'
        ]
        
        player_name = None
        for pattern in patterns:
            match = re.search(pattern, content_lower)
            if match:
                player_name = match.group(1).strip()
                break
        
        if player_name:
            await handle_player_stats_query(message, player_name)
            return
        else:
            await message.channel.send("Which player's stats would you like to see? Try: 'show me stats for Monte'")
            return
    
    # Basic greetings
    if any(greeting in content_lower for greeting in GREETINGS):
        await message.channel.send(
            f"Hello {message.author.mention}! I'm the Tournament Tracker bot. "
            f"Ask me about FGC tournaments, attendance rankings, or organizations!"
        )
        return
    
    # Tournament-specific queries
    tournament_keywords = ['tournament', 'attendance', 'ranking', 'organization', 'top', 
                          'stats', 'fgc', 'socal', 'leaderboard', 'event', 'player', 
                          'singles', 'doubles', 'squad', 'show', 'where', 'what', 'rank']
    
    if any(keyword in content_lower for keyword in tournament_keywords):
        await handle_tournament_query(message)
        return
    
    # Direct questions about the bot
    if 'who are you' in content_lower or 'what are you' in content_lower:
        await message.channel.send(
            "I'm the Tournament Tracker bot! I track Fighting Game Community tournaments "
            "in Southern California. I can tell you about:\n"
            "• Top organizations by attendance\n"
            "• Player rankings (overall, singles, doubles)\n"
            "• Tournament statistics\n"
            "• Event information\n"
            "\nJust ask me naturally, like:\n"
            "• 'show top 8 singles players'\n"
            "• 'top 10 organizations'\n"
            "• 'player rankings for doubles'"
        )
        return
    
    # If mentioned directly, provide help
    if client.user in message.mentions:
        await message.channel.send(
            f"Hi {message.author.mention}! Ask me about:\n"
            f"• Tournament rankings: 'show top organizations'\n"
            f"• Statistics: 'what are the stats?'\n"
            f"• Specific orgs: 'tell me about [organization name]'\n"
        )
        return

async def handle_tournament_query(message):
    """Handle tournament-related queries using conversational search"""
    try:
        logger.info(f"handle_tournament_query called with: {message.content}")
        content_lower = message.content.lower()
        
        # First, try to find if any word in the message is a player name
        # This avoids false positives
        found_player = None
        skip_words = {'the', 'is', 'in', 'at', 'for', 'what', 'where', 'how', 'who', 
                     'singles', 'doubles', 'ultimate', 'squad', 'strike', 'ranking', 
                     'rank', 'player', 'top', 'best', 'list', 'get', 'of', 'me', 
                     'and', 'or', 'but', 'with', 'from', 'to', 'by', 'about', 'show'}
        
        # Quick scan for player names in messages that might be about players
        if ('ranking' in content_lower or 'rank' in content_lower or 'show' in content_lower or 
            'where' in content_lower or 'what' in content_lower):
            logger.info(f"Scanning message for players: {message.content}")
            for word in message.content.split():
                # Clean the word - remove apostrophes and punctuation
                clean_word = word.strip("'\".,!?:;").rstrip("'s")
                logger.info(f"  Checking word: '{word}' → '{clean_word}' (skip={clean_word.lower() in skip_words})")
                if clean_word.lower() not in skip_words and len(clean_word) > 2:
                    # Try with standard threshold first
                    try:
                        temp_info = find_player_ranking(clean_word, None, fuzzy_threshold=0.7)
                        if temp_info:
                            logger.info(f"Found player '{temp_info['gamer_tag']}' from word '{clean_word}'")
                            found_player = (clean_word, temp_info)
                            break
                        else:
                            logger.info(f"  No player found for '{clean_word}'")
                    except Exception as e:
                        logger.error(f"Error finding player for '{clean_word}': {e}")
        
        # If we found a player, handle the query
        if found_player:
            try:
                player_match, player_info = found_player
                logger.info(f"Processing player query for {player_info['gamer_tag']}")
                
                # Check for event type in message
                event_type = None
                if 'singles' in content_lower or 'single' in content_lower:
                    event_type = 'singles'
                elif 'doubles' in content_lower or 'double' in content_lower:
                    event_type = 'doubles'
                elif 'squad' in content_lower:
                    event_type = 'squad'
                
                # Determine event filter based on event_type
                event_filter = None
                if event_type == 'singles':
                    event_filter = 'Ultimate Singles'
                elif event_type == 'doubles':
                    event_filter = 'Ultimate Doubles'
                elif event_type == 'squad':
                    event_filter = 'Ultimate Squad Strike'
                
                # If we need event-specific data, re-fetch with filter
                if event_filter:
                    player_info = find_player_ranking(player_match, event_filter)
                
                if player_info:
                    # Create embed with player info
                    event_title = event_filter if event_filter else 'All Events'
                    embed = discord.Embed(
                        title=f"Player Ranking: {player_info['gamer_tag']}",
                        color=discord.Color.gold(),
                        timestamp=datetime.utcnow()
                    )
                    
                    # Rank with medal
                    rank = player_info['rank']
                    if rank == 1:
                        rank_display = "🥇 #1"
                    elif rank == 2:
                        rank_display = "🥈 #2"
                    elif rank == 3:
                        rank_display = "🥉 #3"
                    else:
                        rank_display = f"#{rank}"
                
                # Main stats
                embed.add_field(name="Ranking", value=f"{rank_display} in {event_title}", inline=True)
                embed.add_field(name="Total Points", value=str(player_info['total_points']), inline=True)
                embed.add_field(name="Events Played", value=str(player_info['tournament_count']), inline=True)
                    
                    # Medal count if any
                medals = []
                if player_info.get('first_places', 0) > 0:
                    medals.append(f"🥇 x{player_info['first_places']}")
                if player_info.get('second_places', 0) > 0:
                    medals.append(f"🥈 x{player_info['second_places']}")
                if player_info.get('third_places', 0) > 0:
                    medals.append(f"🥉 x{player_info['third_places']}")
                    
                if medals:
                    embed.add_field(name="Medals", value=" ".join(medals), inline=False)
                    
                # Recent placements if available
                if 'recent_placements' in player_info and player_info['recent_placements']:
                    recent_text = ""
                    for p in player_info['recent_placements'][:3]:  # Show top 3 recent
                        place_emoji = "🥇" if p['placement'] == 1 else "🥈" if p['placement'] == 2 else "🥉" if p['placement'] == 3 else f"#{p['placement']}"
                        recent_text += f"{place_emoji} at {p['tournament'][:30]}\n"
                    
                    if recent_text:
                        embed.add_field(name="Recent Results", value=recent_text, inline=False)
                    
                    embed.set_footer(text=f"Requested by {message.author}")
                    await message.channel.send(embed=embed)
                else:
                    await message.channel.send(f"Could not find player '{player_match}' in {event_filter if event_filter else 'the rankings'}.")
            except Exception as e:
                logger.error(f"Error processing player query: {e}", exc_info=True)
                await message.channel.send(f"Sorry, I encountered an error processing that request: {e}")
            return
            
            # If we think it's a player query but didn't find a player name, don't block other handlers
            # Only return early if we definitely found and processed a player query
        
        # Check if asking for player rankings (but only if it's a general request, not about a specific player)
        elif (any(phrase in content_lower for phrase in ['top', 'leaderboard', 'best']) and 
              any(phrase in content_lower for phrase in ['player', 'singles', 'doubles', 'squad'])) or \
             ('top 8' in content_lower) or \
             (any(phrase in content_lower for phrase in ['show', 'list', 'get']) and 
              any(phrase in content_lower for phrase in ['player', 'singles', 'doubles']) and
              'ranking' not in content_lower):
            # Extract number if present
            import re
            numbers = re.findall(r'\d+', message.content)
            limit = int(numbers[0]) if numbers else 8
            limit = min(limit, 50)  # Cap at 50
            
            # Determine event filter
            event_filter = 'all'
            if 'singles' in content_lower or 'single' in content_lower:
                event_filter = 'Ultimate Singles'
            elif 'doubles' in content_lower or 'double' in content_lower or 'teams' in content_lower:
                event_filter = 'Ultimate Doubles'
            elif 'squad' in content_lower:
                event_filter = 'Ultimate Squad Strike'
            
            # Get player rankings
            rankings = get_player_rankings(limit=limit, event_filter=event_filter if event_filter != 'all' else None)
            
            if not rankings:
                await message.channel.send("No player ranking data available yet.")
                return
            
            # Format as Discord embed
            event_title = event_filter if event_filter != 'all' else 'All Events'
            embed = discord.Embed(
                title=f"Top {len(rankings)} Players - {event_title}",
                color=discord.Color.purple(),
                timestamp=datetime.utcnow()
            )
            
            ranking_text = ""
            prev_rank = None
            for player in rankings:
                rank = player['rank']
                # Show medal for top 3
                if rank == 1:
                    medal = "🥇"
                elif rank == 2:
                    medal = "🥈"
                elif rank == 3:
                    medal = "🥉"
                else:
                    medal = f"{rank}."
                
                # Handle ties
                if prev_rank == rank:
                    medal = f"{rank}."  # Same rank for ties
                
                ranking_text += f"{medal} **{player['gamer_tag']}**: {player['total_points']} pts ({player['tournament_count']} events)\n"
                prev_rank = rank
            
            embed.description = ranking_text
            embed.set_footer(text=f"Requested by {message.author} | Points: 1st=8, 2nd=7, ..., 8th=1")
            
            await message.channel.send(embed=embed)
            return
            
        # Check for organization rankings
        elif any(phrase in content_lower for phrase in ['top', 'ranking', 'leaderboard', 'best', 'organization', 'org']):
            # Extract number if present
            import re
            numbers = re.findall(r'\d+', message.content)
            limit = int(numbers[0]) if numbers else 10
            limit = min(limit, 50)  # Cap at 50
            
            # Get rankings
            rankings = database_service.get_attendance_rankings(limit)
            
            if not rankings:
                await message.channel.send("No attendance data available yet.")
                return
            
            # Format as Discord embed
            embed = discord.Embed(
                title=f"Top {len(rankings)} Organizations by Attendance",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            
            ranking_text = ""
            for i, (org, count) in enumerate(rankings, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                ranking_text += f"{medal} **{org}**: {count} attendees\n"
            
            embed.description = ranking_text
            embed.set_footer(text=f"Requested by {message.author}")
            
            await message.channel.send(embed=embed)
            
        elif any(phrase in content_lower for phrase in ['stats', 'statistics', 'summary', 'total']):
            # Get summary statistics
            stats = database_service.get_summary_stats()
            
            if not stats:
                await message.channel.send("No statistics available yet.")
                return
            
            embed = discord.Embed(
                title="Tournament Tracker Statistics",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(name="Total Tournaments", value=stats.get('total_tournaments', 0), inline=True)
            embed.add_field(name="Total Organizations", value=stats.get('total_organizations', 0), inline=True)
            embed.add_field(name="Total Attendance", value=f"{stats.get('total_attendance', 0):,}", inline=True)
            
            if stats.get('date_range'):
                embed.add_field(
                    name="Date Range", 
                    value=f"{stats['date_range']['start']} to {stats['date_range']['end']}", 
                    inline=False
                )
            
            embed.set_footer(text=f"Requested by {message.author}")
            
            await message.channel.send(embed=embed)
            
        elif 'about' in content_lower or 'tell me' in content_lower:
            # Try to use conversational search
            results = search_engine.search(message.content)
            
            if results and results.get('results'):
                result = results['results'][0]  # Get first result
                
                embed = discord.Embed(
                    title=f"Search Results",
                    description=f"Found information about: {result.get('name', 'Unknown')}",
                    color=discord.Color.purple()
                )
                
                if 'attendance' in result:
                    embed.add_field(name="Attendance", value=result['attendance'], inline=True)
                if 'tournaments' in result:
                    embed.add_field(name="Tournaments", value=result['tournaments'], inline=True)
                
                await message.channel.send(embed=embed)
            else:
                await message.channel.send(
                    f"I couldn't find specific information about that. "
                    f"Try asking about 'top organizations' or 'tournament stats'."
                )
                
        else:
            # Try AI interpretation for natural queries
            # Check if it's asking about a specific player
            import re
            
            # Simple check if message mentions a potential player name
            words = content_lower.split()
            potential_player = None
            
            # Look for any words that might be player names (not just capitalized)
            skip_words = {'the', 'is', 'in', 'at', 'for', 'what', 'where', 'how', 'who', 
                         'singles', 'doubles', 'ultimate', 'squad', 'strike', 'ranking', 
                         'rank', 'player', 'top', 'best', 'show', 'list', 'get', 'of', 
                         'and', 'or', 'but', 'with', 'from', 'to', 'by', 'about'}
            
            original_words = message.content.split()
            for word in original_words:
                # Clean the word - remove apostrophes and punctuation
                clean_word = word.strip("'\".,!?:;").rstrip("'s")
                if clean_word.lower() not in skip_words and len(clean_word) > 2:
                    # Try to find this as a player with fuzzy matching
                    player_info = find_player_ranking(clean_word, None, fuzzy_threshold=0.7)
                    if player_info:
                        potential_player = player_info
                        break
            
            if potential_player:
                # Found a player! Show their info
                embed = discord.Embed(
                    title=f"Player: {potential_player['gamer_tag']}",
                    color=discord.Color.gold(),
                    timestamp=datetime.utcnow()
                )
                
                # Rank with medal
                rank = potential_player['rank']
                if rank == 1:
                    rank_display = "🥇 #1"
                elif rank == 2:
                    rank_display = "🥈 #2"
                elif rank == 3:
                    rank_display = "🥉 #3"
                else:
                    rank_display = f"#{rank}"
                
                embed.add_field(name="Overall Ranking", value=rank_display, inline=True)
                embed.add_field(name="Total Points", value=str(potential_player['total_points']), inline=True)
                embed.add_field(name="Events Played", value=str(potential_player['tournament_count']), inline=True)
                
                # Medal count
                medals = []
                if potential_player.get('first_places', 0) > 0:
                    medals.append(f"🥇 x{potential_player['first_places']}")
                if potential_player.get('second_places', 0) > 0:
                    medals.append(f"🥈 x{potential_player['second_places']}")
                if potential_player.get('third_places', 0) > 0:
                    medals.append(f"🥉 x{potential_player['third_places']}")
                
                if medals:
                    embed.add_field(name="Medals", value=" ".join(medals), inline=False)
                
                # Add note about asking for specific event rankings
                embed.add_field(
                    name="💡 Tip", 
                    value="Ask about 'singles' or 'doubles' to see event-specific rankings!", 
                    inline=False
                )
                
                embed.set_footer(text=f"Requested by {message.author}")
                await message.channel.send(embed=embed)
            else:
                # General help message
                await message.channel.send(
                    "I can help with tournament data! Try asking:\n"
                    "• 'Show top players' or 'top 8 singles'\n"
                    "• 'What's West's ranking?' (or any player name)\n"
                    "• 'Top 10 organizations'\n"
                    "• 'Tournament statistics'"
                )
            
    except Exception as e:
        logger.error(f"Error handling tournament query: {e}")
        await message.channel.send(
            "Sorry, I encountered an error processing that request. "
            "Try asking something like 'show top 10 organizations' or 'what are the stats?'"
        )

@client.event
async def on_guild_join(guild):
    print(f'[{datetime.now()}] Joined guild: {guild.name} ({guild.id})')
    # Send a greeting message
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            await channel.send(
                "Hello! I'm the Tournament Tracker bot for SoCal FGC events.\n"
                "I can provide tournament statistics, attendance rankings, and organization information.\n"
                "Try asking: 'Show me the top organizations' or 'What are the tournament stats?'"
            )
            break

# Run the bot
if __name__ == "__main__":
    print(f"[{datetime.now()}] Starting Tournament Tracker Discord bot...")
    try:
        client.run(TOKEN)
    except discord.LoginFailure:
        print("Failed to login. Please check your token.")
    except Exception as e:
        print(f"An error occurred: {e}")