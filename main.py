import os
import discord
from discord.ext import commands
from discord import app_commands

TOKEN = os.getenv("token")
 
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

CEO_ROLE = "CEO"
SETS_ROLE = "Sets"
MEMBER_ROLE = "CBM-RJ"

LOG_CHANNEL_ID = 000000000000000000  # coloque o ID do canal log
CATEGORY_NAME = "REGISTRO"


# ================= READY =================
@bot.event
async def on_ready():
    await tree.sync()
    print("Bot online")


# ================= BOTÕES APROVAÇÃO =================
class AprovarView(discord.ui.View):
    def __init__(self, user, tipo):
        super().__init__(timeout=None)
        self.user = user
        self.tipo = tipo

    @discord.ui.button(label="ACEITAR", style=discord.ButtonStyle.green)
    async def aceitar(self, interaction: discord.Interaction, button: discord.ui.Button):

        role = discord.utils.get(interaction.guild.roles, name=CEO_ROLE)
        if role not in interaction.user.roles:
            await interaction.response.send_message("Sem permissão.", ephemeral=True)
            return

        membro = interaction.guild.get_member(self.user)

        if self.tipo == "registro":
            cargo = discord.utils.get(interaction.guild.roles, name=MEMBER_ROLE)
            await membro.add_roles(cargo)

        log = bot.get_channel(LOG_CHANNEL_ID)
        await log.send(
            f"✅ {interaction.user.mention} aprovou solicitação de {membro.mention}"
        )

        await interaction.channel.delete()

    @discord.ui.button(label="NEGAR", style=discord.ButtonStyle.red)
    async def negar(self, interaction: discord.Interaction, button: discord.ui.Button):

        role = discord.utils.get(interaction.guild.roles, name=CEO_ROLE)
        if role not in interaction.user.roles:
            await interaction.response.send_message("Sem permissão.", ephemeral=True)
            return

        membro = interaction.guild.get_member(self.user)

        log = bot.get_channel(LOG_CHANNEL_ID)
        await log.send(
            f"❌ {interaction.user.mention} negou solicitação de {membro.mention}"
        )

        await interaction.channel.delete()


# ================= PAINEL =================
class PainelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Registro RP", style=discord.ButtonStyle.green)
    async def registro(self, interaction: discord.Interaction, button: discord.ui.Button):

        guild = interaction.guild
        category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
        ceo_role = discord.utils.get(guild.roles, name=CEO_ROLE)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            ceo_role: discord.PermissionOverwrite(view_channel=True)
        }

        canal = await guild.create_text_channel(
            f"registro-{interaction.user.name}",
            overwrites=overwrites,
            category=category
        )

        await canal.send(
            f"Solicitação de registro de {interaction.user.mention}",
            view=AprovarView(interaction.user.id, "registro")
        )

        await interaction.response.send_message("Registro enviado.", ephemeral=True)

    @discord.ui.button(label="Solicitar SETS", style=discord.ButtonStyle.blurple)
    async def sets(self, interaction: discord.Interaction, button: discord.ui.Button):

        role = discord.utils.get(interaction.guild.roles, name=SETS_ROLE)
        if role not in interaction.user.roles:
            await interaction.response.send_message("Você não possui permissão.", ephemeral=True)
            return

        guild = interaction.guild
        category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
        ceo_role = discord.utils.get(guild.roles, name=CEO_ROLE)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            ceo_role: discord.PermissionOverwrite(view_channel=True)
        }

        canal = await guild.create_text_channel(
            f"sets-{interaction.user.name}",
            overwrites=overwrites,
            category=category
        )

        await canal.send(
            f"Solicitação SETS de {interaction.user.mention}",
            view=AprovarView(interaction.user.id, "sets")
        )

        await interaction.response.send_message("Solicitação enviada.", ephemeral=True)


# ================= COMANDO CRIAR PAINEL =================
@tree.command(name="painel", description="Criar painel")
async def painel(interaction: discord.Interaction):

    role = discord.utils.get(interaction.guild.roles, name=CEO_ROLE)
    if role not in interaction.user.roles:
        await interaction.response.send_message("Apenas CEO.", ephemeral=True)
        return

    embed = discord.Embed(
        title="PAINEL RP",
        description="Clique no botão abaixo",
        color=0x2b2d31
    )

    await interaction.channel.send(embed=embed, view=PainelView())
    await interaction.response.send_message("Painel criado.", ephemeral=True)


bot.run(token)
