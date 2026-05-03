from __future__ import annotations

import discord

from src.config import lottery as lottery_config
from src.config.emojis import COIN_ICON_URL, PARTICIPANT_EMOJI, TICKET_EMOJI
from src.games.lottery.models import LotteryDrawResult, LotteryPurchaseResult, LotteryState, LotteryTicket
from src.utils.money import format_coin, format_number


def render_announcement_embed(state: LotteryState) -> discord.Embed:
    embed = discord.Embed(
        description=f"Ends <t:{state.ends_at}:R>",
        color=discord.Color.gold(),
    )
    embed.set_author(name=f"Lottery Draw #{format_number(state.draw_id)}")
    embed.add_field(name="Jackpot Pool", value=format_coin(state.jackpot_pool), inline=True)
    embed.add_field(name="Ticket Price", value=format_coin(lottery_config.TICKET_PRICE), inline=True)
    embed.add_field(name="Participants", value=f"{format_number(state.participants)} {PARTICIPANT_EMOJI}", inline=True)
    embed.add_field(name="Tickets Sold", value=f"{format_number(state.tickets_sold)} {TICKET_EMOJI}", inline=True)
    if state.last_draw_number:
        embed.add_field(name="Last Draw", value=state.last_draw_number, inline=True)
        embed.add_field(name="Last Payout", value=format_coin(state.last_total_payout), inline=True)
    embed.set_footer(text="Pick a number from 0001 to 9999.", icon_url=COIN_ICON_URL)
    return embed


def render_purchase_embed(result: LotteryPurchaseResult, player: discord.abc.User) -> discord.Embed:
    embed = discord.Embed(color=discord.Color.gold())
    embed.set_author(name=f"{player.display_name}'s Lottery Tickets", icon_url=player.display_avatar.url)
    embed.add_field(name="Draw", value=f"#{format_number(result.state.draw_id)}", inline=True)
    embed.add_field(name="Tickets", value=f"{format_number(result.total_quantity)} {TICKET_EMOJI}", inline=True)
    embed.add_field(name="Cost", value=format_coin(result.total_cost), inline=True)
    embed.add_field(name="Numbers", value=_format_numbers(result.numbers), inline=False)
    embed.set_footer(text=f"Draw ends <t:{result.state.ends_at}:R>", icon_url=COIN_ICON_URL)
    return embed


def render_user_tickets_embed(state: LotteryState, tickets: list[LotteryTicket], player: discord.abc.User) -> discord.Embed:
    embed = discord.Embed(color=discord.Color.gold())
    embed.set_author(name=f"{player.display_name}'s Lottery Tickets", icon_url=player.display_avatar.url)
    embed.add_field(name="Draw", value=f"#{format_number(state.draw_id)}", inline=True)
    embed.add_field(name="Ends", value=f"<t:{state.ends_at}:R>", inline=True)
    if not tickets:
        embed.add_field(name="Tickets", value="No tickets bought yet.", inline=False)
    else:
        total = sum(ticket.quantity for ticket in tickets)
        embed.add_field(name="Total", value=f"{format_number(total)} {TICKET_EMOJI}", inline=True)
        lines = [f"{ticket.number} × {format_number(ticket.quantity)}" for ticket in tickets[:20]]
        if len(tickets) > 20:
            lines.append(f"...and {format_number(len(tickets) - 20)} more numbers")
        embed.add_field(name="Numbers", value="\n".join(lines), inline=False)
    embed.set_footer(text="Only current draw tickets are shown.", icon_url=COIN_ICON_URL)
    return embed


def render_draw_result_embed(result: LotteryDrawResult) -> discord.Embed:
    embed = discord.Embed(color=discord.Color.gold())
    embed.set_author(name=f"Lottery Draw #{format_number(result.old_draw_id)} Result")
    embed.add_field(name="Winning Number", value=result.winning_number, inline=True)
    embed.add_field(name="Tickets Sold", value=f"{format_number(result.tickets_sold)} {TICKET_EMOJI}", inline=True)
    embed.add_field(name="Participants", value=f"{format_number(result.participants)} {PARTICIPANT_EMOJI}", inline=True)
    embed.add_field(name="Jackpot Winners", value=format_number(result.jackpot_winners), inline=True)
    embed.add_field(name="Total Payout", value=format_coin(result.total_payout), inline=True)
    embed.set_footer(text="Congratulations to the winners.", icon_url=COIN_ICON_URL)
    return embed


def _format_numbers(numbers: dict[str, int]) -> str:
    lines = [f"{number} × {format_number(quantity)}" for number, quantity in sorted(numbers.items())]
    return "\n".join(lines[:20]) if len(lines) <= 20 else "\n".join(lines[:20] + [f"...and {format_number(len(lines) - 20)} more numbers"])
