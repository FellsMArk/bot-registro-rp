import os
import discord
from discord.ext import commands
from discord.ui import View
from datetime import datetime

TOKEN = os.getenv("MTQ2OTI5NTA5Njg3MTc4MDQ2NQ.GHwnfC.COl0LdJ0bCuH2xLT_4WmPDK2nHHO9uMa0ytR1o")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================= VIEW REGISTRO =================

class RegistroView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Fazer Registro", style=discord.ButtonStyle.green, custom_id="registro_btn")
    async def registro(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Seu registro foi iniciado.",
            ephemeral=True
        )

# ================= VIEW SET =================

class SetView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Solicitar Set", style=discord.ButtonStyle.blurple, custom_id="set_btn")
    async def set(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Sua solicitação de set foi enviada.",
            ephemeral=True
        )

# ================= COMANDO PAINEL REGISTRO =================

@bot.command()
@commands.has_permissions(administrator=True)
async def painel_registro(ctx):
    embed = discord.Embed(
        title="Painel de Registro",
        description="Clique no botão abaixo para iniciar seu registro.",
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    await ctx.send(embed=embed, view=RegistroView())

# ================= COMANDO PAINEL SET =================

@bot.command()
@commands.has_permissions(administrator=True)
async def painel_sets(ctx):
    embed = discord.Embed(
        title="Painel de Sets",
        description="Clique no botão abaixo para solicitar seu set.",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    await ctx.send(embed=embed, view=SetView())

# ================= READY =================

@bot.event
async def on_ready():
    bot.add_view(RegistroView())
    bot.add_view(SetView())
    print(f"Bot online como {bot.user}")

bot.run("MTQ2OTI5NTA5Njg3MTc4MDQ2NQ.GHwnfC.COl0LdJ0bCuH2xLT_4WmPDK2nHHO9uMa0ytR1o")
