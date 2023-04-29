from __future__ import annotations
from typing import TYPE_CHECKING
from discord.ui import View, string_select, button
from discord import SelectOption

from errors import MyError
from .table import GatherTable, FormatTable, GameTable
from .utils import get_name


if TYPE_CHECKING:
    from discord.ui import Item, Select, Button
    from discord import Interaction


class _BaseView(View):


    def __init__(self, *items: Item) -> None:
        super().__init__(
            *items,
            disable_on_timeout=True,
            timeout=None
        )

    async def on_timeout(self):
        try:
            await self.message.edit(view=None)
        except:
            pass

    async def on_error(self, error: Exception, item: Item, interaction: Interaction):
        if isinstance(error, MyError):
            if interaction.response.is_done():
                await interaction.followup.send(
                    error.localize(interaction.locale),
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    error.localize(interaction.locale),
                    ephemeral=True
                )
            return

        raise error


class GatherView(_BaseView):

    def __init__(self) -> None:
        super().__init__()


    @button(label="Join", custom_id="_join_button")
    async def join(self, button: Button, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        table = GatherTable.from_message(interaction.message)
        table.names.add(get_name(interaction.user))

        if len(table.names) == 12:
            await interaction.message.edit(embed=table.embed, view=None)
            await interaction.followup.send(
                content="Select format you prefer." if interaction.locale != 'ja' else 'ゲームの形式を選択してください。',
                embed=FormatTable({-1: table.names.copy()}).embed,
                view=FormatView()
            )
        else:
            await interaction.message.edit(embed=table.embed, view=GatherView())
            await interaction.followup.send(
                "You have joined the Game" if interaction.locale != 'ja' else 'ゲームに参加しました。',
                ephemeral=True
            )


    @button(label="Cancel", custom_id="_cancel_button")
    async def cancel(self, button: Button, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        table = GatherTable.from_message(interaction.message)
        table.names.discard(get_name(interaction.user))
        await interaction.message.edit(embed=table.embed, view=GatherView())
        await interaction.followup.send(
            "You have canceled the Game" if interaction.locale != 'ja' else 'ゲームをキャンセルしました。',
            ephemeral=True
        )



class FormatView(_BaseView):

    def __init__(self) -> None:
        super().__init__()


    @string_select(
        custom_id="format",
        placeholder="Select your preferred format",
        options=[
            SelectOption(label="FFA", value="1"),
            SelectOption(label="2v2", value="2"),
            SelectOption(label="3v3", value="3"),
            SelectOption(label="4v4", value="4"),
            SelectOption(label="6v6", value="6")
        ]
    )
    async def select_format(
        self,
        select: Select,
        interaction: Interaction
    ) -> None:
        await interaction.response.defer(ephemeral=True)
        table = FormatTable.from_message(interaction.message)

        for k in {1, 2, 3, 4, 6, -1}:
            table.data[k].discard(get_name(interaction.user))

        table.data[int(select.values[0])].add(get_name(interaction.user))
        await interaction.message.edit(embed=table.embed, view=FormatView())
        await interaction.followup.send(
            "Your vote has been recorded" if interaction.locale != 'ja' else '投票が記録されました',
            ephemeral=True
        )

        if not table.data[-1]:
            format = max(table.data, key=lambda x: len(table.data[x]))
            await interaction.followup.send(embed=GameTable.initialize(format, set().union(*table.data.values())).embed, ephemeral=False)
            await self.message.edit(view=None)


    async def interaction_check(self, interaction: Interaction):
        table = FormatTable.from_message(interaction.message)
        return get_name(interaction.user)  in set().union(*table.data.values())


    async def on_check_failure(self, interaction: Interaction):
        await interaction.response.send_message(
            "You cannot vote." if interaction.locale != 'ja' else '投票する権限がありません。',
            ephemeral=True
        )