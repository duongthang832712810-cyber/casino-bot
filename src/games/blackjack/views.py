from __future__ import annotations

import discord

from src.config.emojis import (
    BUTTON_DOUBLE_EMOJI_ID,
    BUTTON_DOUBLE_EMOJI_NAME,
    BUTTON_HIT_EMOJI_ID,
    BUTTON_HIT_EMOJI_NAME,
    BUTTON_STAND_EMOJI_ID,
    BUTTON_STAND_EMOJI_NAME,
)
from src.core.errors import GameNotFoundError, NotEnoughCoinsError
from src.games.blackjack.renderer import content_for_player, render_from_action


class BlackjackView(discord.ui.View):
    def __init__(self, user_id: str) -> None:
        super().__init__(timeout=900)
        self.user_id = str(user_id)

        self.hit_button.custom_id = f"blackjack:hit:{self.user_id}"
        self.hit_button.emoji = discord.PartialEmoji(name=BUTTON_HIT_EMOJI_NAME, id=BUTTON_HIT_EMOJI_ID)
        self.stand_button.custom_id = f"blackjack:stand:{self.user_id}"
        self.stand_button.emoji = discord.PartialEmoji(name=BUTTON_STAND_EMOJI_NAME, id=BUTTON_STAND_EMOJI_ID)
        self.double_button.custom_id = f"blackjack:double:{self.user_id}"
        self.double_button.emoji = discord.PartialEmoji(name=BUTTON_DOUBLE_EMOJI_NAME, id=BUTTON_DOUBLE_EMOJI_ID)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("This is not your Blackjack game.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.secondary)
    async def hit_button(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._handle_action(interaction, "hit")

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.secondary)
    async def stand_button(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._handle_action(interaction, "stand")

    @discord.ui.button(label="Double", style=discord.ButtonStyle.secondary)
    async def double_button(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await self._handle_action(interaction, "double")

    async def _handle_action(self, interaction: discord.Interaction, action_name: str) -> None:
        service = interaction.client.blackjack_service  # type: ignore[attr-defined]
        try:
            if action_name == "hit":
                action = await service.hit(self.user_id)
            elif action_name == "stand":
                action = await service.stand(self.user_id)
            else:
                action = await service.double(self.user_id)
        except NotEnoughCoinsError as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        except GameNotFoundError:
            await interaction.response.send_message("This Blackjack game has already ended.", ephemeral=True)
            return

        footer_text = _current_footer_text(interaction)
        embed = render_from_action(action, interaction.user, footer_text=footer_text)
        view = discord.ui.View() if action.finished else BlackjackView(self.user_id)
        content = content_for_player(self.user_id, action.finished)
        await interaction.response.edit_message(content=content, embed=embed, view=view)


def _current_footer_text(interaction: discord.Interaction) -> str | None:
    message = interaction.message
    if message is None or not message.embeds:
        return None
    return message.embeds[0].footer.text
