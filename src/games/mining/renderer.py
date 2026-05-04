from __future__ import annotations

import discord

from src.config import mining as mining_config
from src.config.emojis import COIN_ICON_URL, TIER_COMPUTER_ROWS, TIER_EMOJIS
from src.games.mining.models import MiningComputerSummary, MiningShopTier
from src.utils.footer import random_footer_text
from src.utils.money import format_coin, format_number
from src.utils.time import format_duration


def render_shop_embed(tiers: list[MiningShopTier], bot_name: str | None = None) -> discord.Embed:
    embed = discord.Embed(
        title="Lucky Mining Shop",
        description=(
            "Buy computers to generate coins over real time.\n"
            f"Storage is capped at **{format_duration(mining_config.MAX_ACCUMULATION_SECONDS)}**. "
            "Computers cannot be sold yet."
        ),
        color=0x3498DB,
    )
    for tier in tiers:
        embed.add_field(
            name=f"{TIER_EMOJIS[tier.tier]} Tier {format_number(tier.tier)} Computer",
            value=(
                f"{_computer_art(tier.tier)}\n\n"
                f"Price: {format_coin(tier.next_price)}\n"
                f"Income/day: {format_coin(tier.daily_income)}\n"
                f"Storage: {format_coin(tier.storage_income)}\n"
                f"Owned: {format_number(tier.owned)}"
            ),
            inline=True,
        )
    embed.set_footer(text=random_footer_text(bot_name), icon_url=COIN_ICON_URL)
    return embed


def render_computers_embed(player: discord.abc.User, summaries: list[MiningComputerSummary], bot_name: str | None = None) -> discord.Embed:
    embed = discord.Embed(title="Lucky Mining Computers", color=0x3498DB)
    embed.set_author(name=f"{player.display_name}'s Computers", icon_url=player.display_avatar.url)
    if not summaries:
        embed.description = "You do not own any Lucky Mining computers yet. Use `/mine shop` to view the shop."
        embed.set_footer(text=random_footer_text(bot_name), icon_url=COIN_ICON_URL)
        return embed

    total_daily = sum(summary.daily_income for summary in summaries)
    total_stored = sum(summary.stored_income for summary in summaries)
    for index, summary in enumerate(summaries, start=1):
        embed.add_field(
            name=f"{TIER_EMOJIS[summary.tier]} Computer {format_number(index)} — Tier {format_number(summary.tier)}",
            value=(
                f"{_computer_art(summary.tier)}\n\n"
                f"Income/day: {format_coin(summary.daily_income)}\n"
                f"Stored now: {format_coin(summary.stored_income)}\n"
                f"Storage: {format_duration(summary.stored_seconds)} / {format_duration(mining_config.MAX_ACCUMULATION_SECONDS)}\n"
                f"Remaining: {format_duration(summary.remaining_storage_seconds)}"
            ),
            inline=True,
        )
    embed.add_field(
        name="Total",
        value=(
            f"Computers: {format_number(sum(summary.count for summary in summaries))}\n"
            f"Income/day: {format_coin(total_daily)}\n"
            f"Stored now: {format_coin(total_stored)}\n"
            f"Storage cap: {format_duration(mining_config.MAX_ACCUMULATION_SECONDS)} per computer"
        ),
        inline=False,
    )
    embed.set_footer(text=random_footer_text(bot_name), icon_url=COIN_ICON_URL)
    return embed


def render_info_embed(bot_name: str | None = None) -> discord.Embed:
    embed = discord.Embed(
        title="Lucky Mining Info",
        description="Buy computers and claim coins generated over real time.",
        color=0x3498DB,
    )
    embed.add_field(
        name="Commands",
        value=(
            "`/mine shop` or `!mine shop`\n"
            "`/mine buy <tier>` or `!mine buy <tier>`\n"
            "`/mine computer` or `!mine computer`\n"
            "`/mine claim` or `!mine claim`\n"
            "`/mine info` or `!mine info`"
        ),
        inline=False,
    )
    embed.add_field(
        name="Rules",
        value=(
            f"Max computers: **{format_number(mining_config.MAX_COMPUTERS_PER_USER)}**\n"
            f"Storage cap: **{format_duration(mining_config.MAX_ACCUMULATION_SECONDS)}**\n"
            f"Claim cooldown: **{format_duration(mining_config.CLAIM_COOLDOWN_SECONDS)}**\n"
            f"Same-tier next price multiplier: **x{mining_config.PRICE_MULTIPLIER_PER_OWNED_COMPUTER:g}**\n"
            "Computers cannot be sold yet. Choose carefully before buying."
        ),
        inline=False,
    )
    embed.set_footer(text=random_footer_text(bot_name), icon_url=COIN_ICON_URL)
    return embed


def _computer_art(tier: int) -> str:
    return "\n".join("".join(row) for row in TIER_COMPUTER_ROWS[tier])



