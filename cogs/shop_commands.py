import asyncio

import discord 
from discord.ext import commands, vbu

from cogs import utils


class ShopCommands(vbu.Cog):

    async def calculate_price(self, db: vbu.Database, item_name: str) -> int:
        """
        Calculate the price of a given item
        """

        return 1

    @vbu.command()
    @commands.defer()
    async def sell(self, ctx: vbu.Context):
        """
        Sell some of your combs on the honey market.
        """

        # Grab the items that the user has
        async with vbu.Database() as db:
            rows = await db(
                """SELECT * FROM user_inventory WHERE guild_id = $1 AND user_id = $2""",
                utils.get_bee_guild_id(ctx), ctx.author.id,
            )
        if not rows:
            return await ctx.send("You don't have any items available to senll :<")

        # See how much each item sells for
        item_prices = {
            (name := i['item_name']): await self.calculate_price(None, name)
            for i in rows
        }

        # Show the items that they can sell
        components = discord.ui.MessageComponents(
            discord.ui.ActionRow(
                discord.ui.SelectMenu(
                    custom_id="INVENTORY_SELECT",
                    options=[
                        discord.ui.SelectOption(
                            label=(name := i['item_name']),
                            description=f"You have {quantity}, and they sell for {item_prices[name]} honey each."
                        )
                        for i in rows if (quantity := i['quantity']) > 0
                    ],
                    placeholder="What item would you like to sell?",
                ),
            ),
            discord.ui.ActionRow(
                discord.ui.Button(
                    label="CANCEL",
                    style=discord.ui.ButtonStyle.danger,
                ),
            ),
        )

        # Ask what they want to sell
        ask_message = await ctx.send("Which of your items would you like to sell?", components=components)
        try:
            interaction: discord.Interaction = await self.bot.wait_for(
                "component_interaction",
                check=vbu.component_check(ctx.author, ask_message),
                timeout=120,
            )
        except asyncio.TimeoutError:
            try:
                await ask_message.edit(components=components.disable_components())
            except Exception:
                pass
            return await ctx.send("Timed out asking what you want to sell.")
        user_item_sell_name = interaction.values[0]

        # Ask how many they'd like to send
        current_sell_amount = 1
        number_components = discord.ui.MessageComponents.add_number_buttons(add_negative=True)
        number_components.add_component(discord.ui.ActionRow(
            discord.ui.Button(label=f"Confirm NaN", custom_id="CONFIRM", style=discord.ui.ButtonStyle.success)
        ))
        while True:
            number_components.get_component("CONFIRM").label = f"Confirm {current_sell_amount}"
            await interaction.response.edit_message(content=f"How many of that item would you like to sell?", components=number_components)
            try:
                interaction: discord.Interaction = await self.bot.wait_for(
                    "component_interaction",
                    check=vbu.component_check(ctx.author, ask_message),
                    timeout=120,
                )
                if interaction.component.custom_id == "CONFIRM":
                    break
                current_sell_amount += int(interaction.component.custom_id.split(" ")[1])
                current_sell_amount = max(current_sell_amount, 1)
                current_sell_amount = min(current_sell_amount, [i['quantity'] for i in rows if i['item_name'] == user_item_sell_name][0])
            except asyncio.TimeoutError:
                return await interaction.followup.send("Timed out asking how much you want to sell.")

        # Sell their items
        return await interaction.response.edit_message(content=f"fake sold {current_sell_amount} {user_item_sell_name} items")
        # async with vbu.Database() as db:
        #     async with db.transaction() as trans:
        #         await trans("UPDATE ")


def setup(bot: vbu.Bot):
    x = ShopCommands(bot)
    bot.add_cog(x)
