from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from src.config.unlocks import FEATURE_MINING
from src.core.errors import (
    FeatureLockedError,
    InvalidBetAmountError,
    MiningClaimCooldownError,
    MiningComputerLimitError,
    MiningNoComputerError,
    MiningNoStoredCoinsError,
    NotEnoughCoinsError,
)
from src.games.mining.renderer import render_computers_embed, render_info_embed, render_shop_embed
from src.utils.money import format_coin, format_number


class MiningCog(commands.Cog):
    mining = app_commands.Group(name="mine", description="Lucky Mining commands.")

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @mining.command(name="shop", description="View the Lucky Mining computer shop.")
    async def slash_shop(self, interaction: discord.Interaction) -> None:
        if not await self._require_slash_unlocked(interaction):
            return
        service = self.bot.mining_service  # type: ignore[attr-defined]
        tiers = await service.shop(str(interaction.user.id))
        await interaction.response.send_message(embed=render_shop_embed(tiers, _bot_name(self.bot)), ephemeral=True)

    @mining.command(name="buy", description="Buy a Lucky Mining computer.")
    @app_commands.describe(tier="Computer tier from 1 to 7")
    async def slash_buy(self, interaction: discord.Interaction, tier: int) -> None:
        await self._handle_slash_buy(interaction, tier)

    @mining.command(name="computer", description="View your Lucky Mining computers.")
    async def slash_computer(self, interaction: discord.Interaction) -> None:
        if not await self._require_slash_unlocked(interaction):
            return
        service = self.bot.mining_service  # type: ignore[attr-defined]
        summaries = await service.summaries(str(interaction.user.id))
        await interaction.response.send_message(embed=render_computers_embed(interaction.user, summaries, _bot_name(self.bot)), ephemeral=True)

    @mining.command(name="claim", description="Claim coins from your Lucky Mining computers.")
    async def slash_claim(self, interaction: discord.Interaction) -> None:
        await self._handle_slash_claim(interaction)

    @mining.command(name="info", description="View Lucky Mining rules.")
    async def slash_info(self, interaction: discord.Interaction) -> None:
        if not await self._require_slash_unlocked(interaction):
            return
        await interaction.response.send_message(embed=render_info_embed(_bot_name(self.bot)), ephemeral=True)

    @commands.group(name="mine", aliases=["mining"])
    async def prefix_mine(self, ctx: commands.Context) -> None:
        if ctx.invoked_subcommand is None:
            if not await self._require_prefix_unlocked(ctx):
                return
            await ctx.reply(f"Usage: `{ctx.clean_prefix}mine <shop|buy|computer|claim|info>`", mention_author=True)

    @prefix_mine.command(name="shop")
    async def prefix_shop(self, ctx: commands.Context) -> None:
        if not await self._require_prefix_unlocked(ctx):
            return
        service = self.bot.mining_service  # type: ignore[attr-defined]
        tiers = await service.shop(str(ctx.author.id))
        await ctx.reply(embed=render_shop_embed(tiers, _bot_name(self.bot)), mention_author=True)

    @prefix_mine.command(name="buy")
    async def prefix_buy(self, ctx: commands.Context, tier: int) -> None:
        if not await self._require_prefix_unlocked(ctx):
            return
        service = self.bot.mining_service  # type: ignore[attr-defined]
        try:
            result = await service.buy(str(ctx.author.id), tier)
        except (InvalidBetAmountError, MiningComputerLimitError, NotEnoughCoinsError) as exc:
            await ctx.reply(str(exc), mention_author=True)
            return
        await ctx.reply(_purchase_message(result.tier, result.price, result.total_computers), mention_author=True)

    @prefix_mine.command(name="computer", aliases=["computers", "pcs", "pc"])
    async def prefix_computer(self, ctx: commands.Context) -> None:
        if not await self._require_prefix_unlocked(ctx):
            return
        service = self.bot.mining_service  # type: ignore[attr-defined]
        summaries = await service.summaries(str(ctx.author.id))
        await ctx.reply(embed=render_computers_embed(ctx.author, summaries, _bot_name(self.bot)), mention_author=True)

    @prefix_mine.command(name="claim")
    async def prefix_claim(self, ctx: commands.Context) -> None:
        if not await self._require_prefix_unlocked(ctx):
            return
        service = self.bot.mining_service  # type: ignore[attr-defined]
        try:
            result = await service.claim(str(ctx.author.id))
        except (MiningClaimCooldownError, MiningNoComputerError, MiningNoStoredCoinsError) as exc:
            await ctx.reply(str(exc), mention_author=True)
            return
        await ctx.reply(_claim_message(result.claimed, result.computer_count, result.next_claim_at), mention_author=True)

    @prefix_mine.command(name="info")
    async def prefix_info(self, ctx: commands.Context) -> None:
        if not await self._require_prefix_unlocked(ctx):
            return
        await ctx.reply(embed=render_info_embed(_bot_name(self.bot)), mention_author=True)

    async def _handle_slash_buy(self, interaction: discord.Interaction, tier: int) -> None:
        if not await self._require_slash_unlocked(interaction):
            return
        service = self.bot.mining_service  # type: ignore[attr-defined]
        try:
            result = await service.buy(str(interaction.user.id), tier)
        except (InvalidBetAmountError, MiningComputerLimitError, NotEnoughCoinsError) as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        await interaction.response.send_message(_purchase_message(result.tier, result.price, result.total_computers), ephemeral=True)

    async def _handle_slash_claim(self, interaction: discord.Interaction) -> None:
        if not await self._require_slash_unlocked(interaction):
            return
        service = self.bot.mining_service  # type: ignore[attr-defined]
        try:
            result = await service.claim(str(interaction.user.id))
        except (MiningClaimCooldownError, MiningNoComputerError, MiningNoStoredCoinsError) as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        await interaction.response.send_message(_claim_message(result.claimed, result.computer_count, result.next_claim_at), ephemeral=True)

    async def _require_slash_unlocked(self, interaction: discord.Interaction) -> bool:
        try:
            await self.bot.unlock_service.require_unlocked(str(interaction.user.id), FEATURE_MINING)  # type: ignore[attr-defined,union-attr]
        except FeatureLockedError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return False
        return True

    async def _require_prefix_unlocked(self, ctx: commands.Context) -> bool:
        try:
            await self.bot.unlock_service.require_unlocked(str(ctx.author.id), FEATURE_MINING)  # type: ignore[attr-defined,union-attr]
        except FeatureLockedError as exc:
            await ctx.reply(str(exc), mention_author=True)
            return False
        return True


def _purchase_message(tier: int, price: int, total_computers: int) -> str:
    return (
        f"Bought a Tier {format_number(tier)} Lucky Mining computer for {format_coin(price)}. "
        f"You now own {format_number(total_computers)} computer(s)."
    )


def _claim_message(claimed: int, computer_count: int, next_claim_at: int) -> str:
    return (
        f"Claimed {format_coin(claimed)} from {format_number(computer_count)} Lucky Mining computer(s). "
        f"You can claim again <t:{next_claim_at}:R>."
    )


def _bot_name(bot: commands.Bot) -> str | None:
    return bot.user.display_name if bot.user is not None else None


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MiningCog(bot))
