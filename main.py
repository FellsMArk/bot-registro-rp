import discord
from discord.ext import commands
from discord import app_commands
import json
import os

TOKEN = os.getenv("MTQ2OTI5NTA5Njg3MTc4MDQ2NQ.GHwnfC.COl0LdJ0bCuH2xLT_4WmPDK2nHHO9uMa0ytR1o")

CARGO_STAFF = "CEO"
CARGO_REGISTRADO = "CMB-RJ"
CARGO_SETS = "Sets"

CANAL_LOG_REGISTRO = "📑-log-registros"
CANAL_LOG_SETS = "📄-log-painel"

CATEGORIA_REGISTRO = "📋 REGISTROS"

INTENTS = discord.Intents.default()
INTENTS.members = True
INTENTS.message_content = True

bot = commands.Bot(command_prefix="!", intents=INTENTS)

# ================= READY =================

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Online como {bot.user}")

# ================= REGISTRO =================

class RegistroModal(discord.ui.Modal, title="Registro RP"):
    id_cidade = discord.ui.TextInput(label="ID da cidade")

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        staff_role = discord.utils.get(guild.roles, name=CARGO_STAFF)

        categoria = discord.utils.get(guild.categories, name=CATEGORIA_REGISTRO)
        if not categoria:
            categoria = await guild.create_category(CATEGORIA_REGISTRO)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=False),
            staff_role: discord.PermissionOverwrite(view_channel=True),
            guild.me: discord.PermissionOverwrite(view_channel=True)
        }

        canal = await guild.create_text_channel(
            f"registro-{interaction.user.name}",
            category=categoria,
            overwrites=overwrites
        )

        embed = discord.Embed(title="Novo Registro", color=discord.Color.orange())
        embed.add_field(name="Usuário", value=interaction.user.mention)
        embed.add_field(name="Cidade", value=self.id_cidade.value)

        await canal.send(embed=embed, view=AprovacaoRegistro(interaction.user, self.id_cidade.value))
        await interaction.response.send_message("Registro enviado.", ephemeral=True)

class RegistroView(discord.ui.View):
    @discord.ui.button(label="Iniciar Registro", style=discord.ButtonStyle.green)
    async def registrar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RegistroModal())

class AprovacaoRegistro(discord.ui.View):
    def __init__(self, usuario, cidade):
        super().__init__(timeout=None)
        self.usuario = usuario
        self.cidade = cidade

    async def interaction_check(self, interaction):
        role = discord.utils.get(interaction.guild.roles, name=CARGO_STAFF)
        return role in interaction.user.roles

    @discord.ui.button(label="Aprovar", style=discord.ButtonStyle.success)
    async def aprovar(self, interaction: discord.Interaction, button: discord.ui.Button):
        membro = interaction.guild.get_member(self.usuario.id)
        cargo = discord.utils.get(interaction.guild.roles, name=CARGO_REGISTRADO)

        await membro.add_roles(cargo)
        await membro.edit(nick=f"{self.cidade} | {membro.name}")

        canal_log = discord.utils.get(interaction.guild.text_channels, name=CANAL_LOG_REGISTRO)
        if canal_log:
            await canal_log.send(f"Registro aprovado: {membro.mention}")

        await interaction.channel.delete()

    @discord.ui.button(label="Negar", style=discord.ButtonStyle.danger)
    async def negar(self, interaction: discord.Interaction, button: discord.ui.Button):
        canal_log = discord.utils.get(interaction.guild.text_channels, name=CANAL_LOG_REGISTRO)
        if canal_log:
            await canal_log.send(f"Registro negado: {self.usuario.mention}")

        await interaction.channel.delete()

@bot.tree.command(name="registro")
async def registro(interaction: discord.Interaction):
    embed = discord.Embed(title="Registro RP")
    await interaction.response.send_message(embed=embed, view=RegistroView(), ephemeral=True)

# ================= SETS =================

class SetsModal(discord.ui.Modal, title="Solicitação Sets"):
    user_id = discord.ui.TextInput(label="ID do usuário")
    motivo = discord.ui.TextInput(label="Motivo", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        staff_role = discord.utils.get(guild.roles, name=CARGO_STAFF)

        categoria = discord.utils.get(guild.categories, name=CATEGORIA_REGISTRO)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=False),
            staff_role: discord.PermissionOverwrite(view_channel=True),
            guild.me: discord.PermissionOverwrite(view_channel=True)
        }

        canal = await guild.create_text_channel(
            f"sets-{interaction.user.name}",
            category=categoria,
            overwrites=overwrites
        )

        embed = discord.Embed(title="Solicitação SETS", color=discord.Color.orange())
        embed.add_field(name="Solicitante", value=interaction.user.mention)
        embed.add_field(name="ID", value=self.user_id.value)
        embed.add_field(name="Motivo", value=self.motivo.value)

        await canal.send(embed=embed, view=AprovacaoSets(interaction.user, self.user_id.value, self.motivo.value))
        await interaction.response.send_message("Solicitação enviada.", ephemeral=True)

class AprovacaoSets(discord.ui.View):
    def __init__(self, solicitante, uid, motivo):
        super().__init__(timeout=None)
        self.solicitante = solicitante
        self.uid = uid
        self.motivo = motivo

    async def interaction_check(self, interaction):
        role = discord.utils.get(interaction.guild.roles, name=CARGO_STAFF)
        return role in interaction.user.roles

    @discord.ui.button(label="Aprovar", style=discord.ButtonStyle.success)
    async def aprovar(self, interaction: discord.Interaction, button: discord.ui.Button):
        canal_log = discord.utils.get(interaction.guild.text_channels, name=CANAL_LOG_SETS)
        if canal_log:
            await canal_log.send(f"SETS aprovado\nSolicitante: {self.solicitante.mention}\nID: {self.uid}\nMotivo: {self.motivo}")

        await interaction.channel.delete()

    @discord.ui.button(label="Negar", style=discord.ButtonStyle.danger)
    async def negar(self, interaction: discord.Interaction, button: discord.ui.Button):
        canal_log = discord.utils.get(interaction.guild.text_channels, name=CANAL_LOG_SETS)
        if canal_log:
            await canal_log.send(f"SETS negado\nSolicitante: {self.solicitante.mention}\nID: {self.uid}\nMotivo: {self.motivo}")

        await interaction.channel.delete()

class SetsView(discord.ui.View):
    @discord.ui.button(label="Abrir Solicitação", style=discord.ButtonStyle.green)
    async def abrir(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SetsModal())

@bot.tree.command(name="sets")
async def sets(interaction: discord.Interaction):
    role = discord.utils.get(interaction.guild.roles, name=CARGO_SETS)
    if role not in interaction.user.roles:
        await interaction.response.send_message("Você não possui permissão.", ephemeral=True)
        return

    embed = discord.Embed(title="Painel SETS")
    await interaction.response.send_message(embed=embed, view=SetsView(), ephemeral=True)

bot.run("MTQ2OTI5NTA5Njg3MTc4MDQ2NQ.GHwnfC.COl0LdJ0bCuH2xLT_4WmPDK2nHHO9uMa0ytR1o")
