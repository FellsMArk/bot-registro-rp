import os
import discord
from discord.ext import commands
from discord.ui import View, Button
from datetime import datetime

TOKEN = os.getenv("MTQ2OTI5NTA5Njg3MTc4MDQ2NQ.GHwnfC.COl0LdJ0bCuH2xLT_4WmPDK2nHHO9uMa0ytR1o")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================= BOTÕES =================

class PainelView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Registro", style=discord.ButtonStyle.green, custom_id="registro_btn")
    async def registro(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Sistema de registro iniciado.",
            ephemeral=True
        )

    @discord.ui.button(label="Solicitar Set", style=discord.ButtonStyle.blurple, custom_id="set_btn")
    async def set(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Solicitação de set enviada.",
            ephemeral=True
        )

# ================= COMANDO PAINEL =================

@bot.command()
@commands.has_permissions(administrator=True)
async def painel(ctx):
    embed = discord.Embed(
        title="Painel de Registro e Set",
        description="Clique nos botões abaixo para realizar o registro ou solicitar set.",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )

    await ctx.send(embed=embed, view=PainelView())

# ================= READY =================

@bot.event
async def on_ready():
    bot.add_view(PainelView())
    print(f"Bot online como {bot.user}")

bot.run("MTQ2OTI5NTA5Njg3MTc4MDQ2NQ.GHwnfC.COl0LdJ0bCuH2xLT_4WmPDK2nHHO9uMa0ytR1o")
