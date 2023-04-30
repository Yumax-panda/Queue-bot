from __future__ import annotations
from typing import TYPE_CHECKING
from discord.ui import View, string_select, button
from discord import SelectOption

from errors import MyError
from .table import GatherTable, FormatTable, GameTable
from .utils import get_name
from .game import State


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


    @button(label="Join", custom_id="gather_join_button")
    async def join(self, button: Button, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        table = GatherTable.from_message(interaction.message)
        table.names.add(get_name(interaction.user))

        if len(table.names) == 12:
            table.state = State.DONE
            await interaction.message.edit(embed=table.embed, view=None)
            await interaction.followup.send(
                content="Select format you prefer." if interaction.locale != 'ja' else 'ゲームの形式を選択してください。',
                embed=FormatTable({-1: table.names.copy()}).embed,
                view=FormatView(),
                ephemeral=False
            )
        else:
            await interaction.message.edit(embed=table.embed, view=GatherView())
            await interaction.followup.send(
                "You have joined the Game" if interaction.locale != 'ja' else 'ゲームに参加しました。',
                ephemeral=True
            )


    @button(label="Cancel", custom_id="gather_cancel_button")
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
        custom_id="format_select",
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

        if not table.data[-1]:
            format = max(table.data, key=lambda x: len(table.data[x]))
            await interaction.followup.send(
                embed=GameTable.initialize(format, list(set().union(*table.data.values()))).embed,
                view=GameView(),
                ephemeral=False
            )
            table.state = State.DONE
            await interaction.message.edit(embed=table.embed, view=None)
        else:
            await interaction.message.edit(embed=table.embed, view=FormatView())
            await interaction.followup.send(
                "Your vote has been recorded" if interaction.locale != 'ja' else '投票が記録されました',
                ephemeral=True
            )




    @button(label="Start", custom_id="format_start_button")
    async def start(self, button: Button, interaction: Interaction) -> None:
        await interaction.response.defer(ephemeral=False)
        table = FormatTable.from_message(interaction.message)
        data = table.data.copy()
        print(data)
        data.pop(-1, None)
        print(data)
        format = max(data, key=lambda x: len(table.data[x]))
        print(format)
        await interaction.followup.send(
            embed=GameTable.initialize(format, list(set().union(*table.data.values()))).embed,
            view=GameView(),
            ephemeral=False
        )
        table.state = State.DONE
        await table.message.edit(embed=table.embed, view=None)


    async def interaction_check(self, interaction: Interaction):
        table = FormatTable.from_message(interaction.message)
        return get_name(interaction.user)  in set().union(*table.data.values())


    async def on_check_failure(self, interaction: Interaction):
        await interaction.response.send_message(
            "You cannot vote." if interaction.locale != 'ja' else '投票する権限がありません。',
            ephemeral=True
        )


class GameView(_BaseView):

    def __init__(self) -> None:
        super().__init__()


    @button(label="End", custom_id="game_finish_button")
    async def end(self, button: Button, interaction: Interaction) -> None:
        await interaction.response.defer(ephemeral=False)
        table = GameTable.from_message(interaction.message)
        table.state = State.DONE
        await interaction.message.edit(embed=table.embed, view=ResumeView())
        await interaction.followup.send(
            "ゲームを終了しました。" if interaction.locale == 'ja' else 'Game has ended.',
        )


class ResumeView(_BaseView):

    def __init__(self) -> None:
        super().__init__()

    @button(label="Resume", custom_id="resume_button")
    async def resume(self, button: Button, interaction: Interaction) -> None:
        await interaction.response.defer(ephemeral=False)
        table = GameTable.from_message(interaction.message)
        table.state = State.ONGOING
        await interaction.message.edit(embed=table.embed, view=GameView())
        await interaction.followup.send(
            "ゲームを再開しました。" if interaction.locale == 'ja' else 'Game has resumed.',
        )