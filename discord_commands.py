#!/usr/bin/env python3
"""
Discord command hooks for tournament_tracker
Provides Discord bot commands that interface with tournament_report functions
"""
import discord
from discord.ext import commands
import asyncio
import sys
import os

# Add tournament_tracker to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tournament_report import (
    format_console_table,
    generate_html_report,
    get_legacy_attendance_data,
    publish_to_shopify
)
from database_utils import get_attendance_rankings, get_summary_stats
from log_utils import log_info, log_error

class TournamentCommands(commands.Cog):
    """Discord commands for tournament tracker"""
    
    def __init__(self, bot):
        self.bot = bot
        log_info("Tournament commands loaded", "discord")
    
    @commands.command(name='top', aliases=['leaderboard', 'ranks'])
    async def show_top_orgs(self, ctx, limit: int = 10):
        """Show top organizations by attendance
        Usage: !top [number]
        Example: !top 5
        """
        try:
            rankings = get_attendance_rankings(limit)
            
            if not rankings:
                await ctx.send("No attendance data available")
                return
            
            # Build Discord embed for nice formatting
            embed = discord.Embed(
                title=f"Top {limit} Organizations by Attendance",
                color=discord.Color.blue()
            )
            
            leaderboard = ""
            for rank, org_data in enumerate(rankings, 1):
                medal = ""
                if rank == 1:
                    medal = "🥇 "
                elif rank == 2:
                    medal = "🥈 "
                elif rank == 3:
                    medal = "🥉 "
                
                org_name = org_data['display_name'][:30]  # Truncate long names
                attendance = org_data['total_attendance']
                events = org_data['tournament_count']
                
                leaderboard += f"{medal}**{rank}.** {org_name}\n"
                leaderboard += f"   {attendance:,} attendees across {events} events\n\n"
            
            embed.description = leaderboard
            
            # Add summary footer
            stats = get_summary_stats()
            embed.set_footer(text=f"Total: {stats['total_organizations']} orgs, {stats['total_tournaments']} tournaments")
            
            await ctx.send(embed=embed)
            log_info(f"Displayed top {limit} orgs for {ctx.author}", "discord")
            
        except Exception as e:
            await ctx.send(f"Error getting rankings: {e}")
            log_error(f"Failed to get rankings: {e}", "discord")
    
    @commands.command(name='stats', aliases=['summary'])
    async def show_stats(self, ctx):
        """Show tournament tracker statistics"""
        try:
            stats = get_summary_stats()
            
            embed = discord.Embed(
                title="Tournament Tracker Statistics",
                color=discord.Color.green()
            )
            
            embed.add_field(name="Organizations", value=f"{stats['total_organizations']:,}", inline=True)
            embed.add_field(name="Tournaments", value=f"{stats['total_tournaments']:,}", inline=True)
            embed.add_field(name="Total Attendance", value=f"{stats['total_attendance']:,}", inline=True)
            
            # Get top org for highlight
            top_org = get_attendance_rankings(1)
            if top_org:
                embed.add_field(
                    name="Top Organization",
                    value=f"{top_org[0]['display_name']}\n{top_org[0]['total_attendance']:,} attendees",
                    inline=False
                )
            
            await ctx.send(embed=embed)
            log_info(f"Displayed stats for {ctx.author}", "discord")
            
        except Exception as e:
            await ctx.send(f"Error getting stats: {e}")
            log_error(f"Failed to get stats: {e}", "discord")
    
    @commands.command(name='report')
    async def generate_report(self, ctx, limit: int = 20):
        """Generate a tournament report
        Usage: !report [limit]
        """
        try:
            # Use format_console_table but capture output
            import io
            from contextlib import redirect_stdout
            
            f = io.StringIO()
            with redirect_stdout(f):
                format_console_table(limit)
            output = f.getvalue()
            
            # Send as code block for monospace formatting
            if len(output) > 1900:
                # Split into multiple messages if too long
                lines = output.split('\n')
                current_msg = "```\n"
                
                for line in lines:
                    if len(current_msg) + len(line) + 4 > 1900:  # 4 for closing ``` and newline
                        current_msg += "```"
                        await ctx.send(current_msg)
                        current_msg = "```\n"
                    current_msg += line + "\n"
                
                if current_msg != "```\n":
                    current_msg += "```"
                    await ctx.send(current_msg)
            else:
                await ctx.send(f"```\n{output}\n```")
            
            log_info(f"Generated report for {ctx.author}", "discord")
            
        except Exception as e:
            await ctx.send(f"Error generating report: {e}")
            log_error(f"Failed to generate report: {e}", "discord")
    
    @commands.command(name='org', aliases=['organization'])
    async def org_info(self, ctx, *, org_name: str):
        """Get information about a specific organization
        Usage: !org <name>
        """
        try:
            from tournament_models import Organization
            from database_utils import get_session
            
            session = get_session()
            
            # Search for organization (case insensitive)
            orgs = session.query(Organization).filter(
                Organization.display_name.ilike(f"%{org_name}%")
            ).all()
            
            if not orgs:
                await ctx.send(f"No organization found matching '{org_name}'")
                return
            
            if len(orgs) > 1:
                # Multiple matches
                matches = "\n".join([f"• {org.display_name}" for org in orgs[:10]])
                await ctx.send(f"Multiple organizations found:\n{matches}\n\nPlease be more specific.")
                return
            
            org = orgs[0]
            
            # Get attendance records
            attendance_sum = sum(record.attendance for record in org.attendance_records)
            tournament_count = len(org.attendance_records)
            
            embed = discord.Embed(
                title=org.display_name,
                color=discord.Color.purple()
            )
            
            embed.add_field(name="Total Attendance", value=f"{attendance_sum:,}", inline=True)
            embed.add_field(name="Tournaments", value=tournament_count, inline=True)
            
            if tournament_count > 0:
                avg_attendance = attendance_sum / tournament_count
                embed.add_field(name="Avg Attendance", value=f"{avg_attendance:.1f}", inline=True)
            
            # List contacts
            if org.contacts:
                contact_list = "\n".join([f"• {c.contact_value}" for c in org.contacts[:5]])
                embed.add_field(name="Contacts", value=contact_list, inline=False)
            
            # Recent tournaments
            recent_tournaments = sorted(
                org.attendance_records,
                key=lambda x: x.tournament.end_at if x.tournament.end_at else 0,
                reverse=True
            )[:5]
            
            if recent_tournaments:
                tournament_list = "\n".join([
                    f"• {record.tournament.name} ({record.attendance:,})"
                    for record in recent_tournaments
                ])
                embed.add_field(name="Recent Tournaments", value=tournament_list, inline=False)
            
            await ctx.send(embed=embed)
            log_info(f"Displayed info for org '{org.display_name}' to {ctx.author}", "discord")
            
        except Exception as e:
            await ctx.send(f"Error getting organization info: {e}")
            log_error(f"Failed to get org info: {e}", "discord")
    
    @commands.command(name='search')
    async def search_tournaments(self, ctx, *, query: str):
        """Search for tournaments
        Usage: !search <query>
        """
        try:
            from tournament_models import Tournament
            from database_utils import get_session
            
            session = get_session()
            
            # Search tournaments
            tournaments = session.query(Tournament).filter(
                Tournament.name.ilike(f"%{query}%")
            ).limit(10).all()
            
            if not tournaments:
                await ctx.send(f"No tournaments found matching '{query}'")
                return
            
            embed = discord.Embed(
                title=f"Search Results for '{query}'",
                color=discord.Color.orange()
            )
            
            result_list = ""
            for t in tournaments:
                result_list += f"**{t.name}**\n"
                result_list += f"   {t.num_attendees:,} attendees"
                if t.primary_contact:
                    result_list += f" • Contact: {t.primary_contact[:30]}"
                result_list += "\n\n"
            
            embed.description = result_list
            
            await ctx.send(embed=embed)
            log_info(f"Searched for '{query}' by {ctx.author}", "discord")
            
        except Exception as e:
            await ctx.send(f"Error searching: {e}")
            log_error(f"Failed to search: {e}", "discord")

class AdminCommands(commands.Cog):
    """Admin-only Discord commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def cog_check(self, ctx):
        """Check if user has admin permissions"""
        # You can customize this check
        return ctx.author.guild_permissions.administrator
    
    @commands.command(name='sync')
    async def sync_tournaments(self, ctx):
        """Sync tournaments from start.gg (Admin only)"""
        try:
            await ctx.send("Starting tournament sync from start.gg... This may take a few minutes.")
            
            from startgg_sync import sync_from_startgg
            
            # Run sync in background
            loop = asyncio.get_event_loop()
            stats = await loop.run_in_executor(
                None,
                sync_from_startgg,
                250,  # page_size
                False,  # fetch_standings
                5  # standings_limit
            )
            
            if stats:
                embed = discord.Embed(
                    title="✅ Sync Complete",
                    color=discord.Color.green()
                )
                embed.add_field(name="Tournaments", value=stats['summary']['tournaments_processed'], inline=True)
                embed.add_field(name="Organizations", value=stats['summary']['organizations_created'], inline=True)
                embed.add_field(name="API Calls", value=stats['api_stats']['api_calls'], inline=True)
                embed.add_field(name="Success Rate", value=f"{stats['summary']['success_rate']:.1f}%", inline=True)
                embed.add_field(name="Time", value=f"{stats['summary']['total_processing_time']:.1f}s", inline=True)
                
                await ctx.send(embed=embed)
                log_info(f"Sync completed by {ctx.author}", "discord")
            else:
                await ctx.send("❌ Sync failed - check logs for details")
                
        except Exception as e:
            await ctx.send(f"❌ Sync error: {e}")
            log_error(f"Sync failed: {e}", "discord")
    
    @commands.command(name='publish')
    async def publish_shopify(self, ctx):
        """Publish to Shopify (Admin only)"""
        try:
            await ctx.send("Publishing to Shopify...")
            
            success = await asyncio.get_event_loop().run_in_executor(
                None,
                publish_to_shopify
            )
            
            if success:
                await ctx.send("✅ Successfully published to Shopify!")
                log_info(f"Published to Shopify by {ctx.author}", "discord")
            else:
                await ctx.send("❌ Failed to publish to Shopify - check logs")
                
        except Exception as e:
            await ctx.send(f"❌ Publishing error: {e}")
            log_error(f"Publishing failed: {e}", "discord")

async def setup(bot):
    """Setup function for loading cogs"""
    await bot.add_cog(TournamentCommands(bot))
    await bot.add_cog(AdminCommands(bot))

# Standalone bot if running directly
if __name__ == "__main__":
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix='!', intents=intents)
    
    @bot.event
    async def on_ready():
        print(f'Tournament bot ready as {bot.user}')
        await setup(bot)
    
    token = os.getenv('DISCORD_BOT_TOKEN')
    if token:
        bot.run(token)
    else:
        print("Set DISCORD_BOT_TOKEN environment variable")