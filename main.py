import discord
from discord.ext import commands
import json
import os

TOKEN = "MTQ2OTI5NTA5Njg3MTc4MDQ2NQ.G957HJ.rtlnjq1rewaSc7Hx_myiBhAE8TxTJEO1dnQi6U"

CARGO_STAFF = "CEO"
CARGO_REGISTRADO = "CMB-RJ"
CARGO_SETS = "Sets"

CANAL_LOG_REG = "📑-log-registros"
CANAL_LOG_SETS = "📄-log-painel"
CATEGORIA = "📋 REGISTROS"

ARQUIVO = "registros.json"

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ================= UTIL =================

def salvar(dados):
    if not os.path.exists(ARQUIVO):
        with open(ARQUIVO, "w") as f:
            json.dump([], f)

    with open(ARQUIVO, "r") as f:
        data = json.load(f)

    data.append(dados)

    with open(ARQUIVO, "w") as f:
        json.dump(data, f, indent=4)


@bot.event
async def on_ready():
    await bot.tree.sync()
    print("Bot online")


# ================= REGISTRO =================

class RegistroModal(discord.ui.Modal, title="Registro"):
    cidade = discord.ui.TextInput(label="ID cidade")

    async def on_submit(self, interaction: discord.Interaction):

        guild = interaction.guild
        staff = discord.utils.get(guild.roles, name=CARGO_STAFF)

        categoria = discord.utils.get(guild.categories, name=CATEGORIA)
        if not categoria:
            categoria = await guild.create_category(CATEGORIA)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=False),
            staff: discord.PermissionOverwrite(view_channel=True),
            guild.me: discord.PermissionOverwrite(view_channel=True),
        }

        canal = await guild.create_text_channel(
            f"registro-{interaction.user.name}",
            category=categoria,
            overwrites=overwrites
        )

        embed = discord.Embed(title="Pedido registro")
        embed.add_field(name="Usuário", value=interaction.user.mention)
        embed.add_field(name="Cidade", value=self.cidade.value)

        await canal.send(embed=embed, view=AprovacaoRegistro(interaction.user, self.cidade.value))

        await interaction.response.send_message("Solicitação enviada", ephemeral=True)


class AprovacaoRegistro(discord.ui.View):
    def __init__(self, user, cidade):
        super().__init__(timeout=None)
        self.user = user
        self.cidade = cidade

    async def interaction_check(self, interaction):
        role = discord.utils.get(interaction.guild.roles, name=CARGO_STAFF)
        return role in interaction.user.roles

    @discord.ui.button(label="Aprovar", style=discord.ButtonStyle.green)
    async def aprovar(self, interaction, button):

        membro = interaction.guild.get_member(self.user.id)
        cargo = discord.utils.get(interaction.guild.roles, name=CARGO_REGISTRADO)

        if cargo:
            await membro.add_roles(cargo)

        await membro.edit(nick=f"{self.cidade} | {membro.name}")

        log = discord.utils.get(interaction.guild.text_channels, name=CANAL_LOG_REG)
        await log.send(
            f"✅ Registro aprovado\n"
            f"Usuário: {membro.mention}\n"
            f"Aprovado por: {interaction.user.mention}"
        )

        salvar({"user": str(membro), "status": "aprovado"})

        await interaction.message.delete()
        await interaction.channel.delete()

    @discord.ui.button(label="Negar", style=discord.ButtonStyle.red)
    async def negar(self, interaction, button):

        log = discord.utils.get(interaction.guild.text_channels, name=CANAL_LOG_REG)
        await log.send(
            f"❌ Registro negado\n"
            f"Usuário: {self.user.mention}\n"
            f"Negado por: {interaction.user.mention}"
        )

        salvar({"user": str(self.user), "status": "negado"})

        await interaction.message.delete()
        await interaction.channel.delete()


@bot.tree.command(name="registro")
async def registro(interaction: discord.Interaction):
    await interaction.response.send_modal(RegistroModal())


# ================= SETS =================

class SetsModal(discord.ui.Modal, title="Solicitação SETS"):
    uid = discord.ui.TextInput(label="ID")
    motivo = discord.ui.TextInput(label="Motivo")

    async def on_submit(self, interaction):

        guild = interaction.guild
        staff = discord.utils.get(guild.roles, name=CARGO_STAFF)

        categoria = discord.utils.get(guild.categories, name=CATEGORIA)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            staff: discord.PermissionOverwrite(view_channel=True),
            guild.me: discord.PermissionOverwrite(view_channel=True),
        }

        canal = await guild.create_text_channel(
            f"sets-{interaction.user.name}",
            category=categoria,
            overwrites=overwrites
        )

        embed = discord.Embed(title="Pedido SETS")
        embed.add_field(name="Solicitante", value=interaction.user.mention)
        embed.add_field(name="ID", value=self.uid.value)
        embed.add_field(name="Motivo", value=self.motivo.value)

        await canal.send(embed=embed, view=AprovacaoSets(interaction.user, self.uid.value, self.motivo.value))

        await interaction.response.send_message("Solicitação enviada", ephemeral=True)


class AprovacaoSets(discord.ui.View):
    def __init__(self, user, uid, motivo):
        super().__init__(timeout=None)
        self.user = user
        self.uid = uid
        self.motivo = motivo

    async def interaction_check(self, interaction):
        role = discord.utils.get(interaction.guild.roles, name=CARGO_STAFF)
        return role in interaction.user.roles

    @discord.ui.button(label="Aprovar", style=discord.ButtonStyle.green)
    async def aprovar(self, interaction, button):

        log = discord.utils.get(interaction.guild.text_channels, name=CANAL_LOG_SETS)
        await log.send(
            f"✅ SETS aprovado\n"
            f"Solicitante: {self.user.mention}\n"
            f"ID: {self.uid}\n"
            f"Motivo: {self.motivo}\n"
            f"Aprovado por: {interaction.user.mention}"
        )

        await interaction.message.delete()
        await interaction.channel.delete()

    @discord.ui.button(label="Negar", style=discord.ButtonStyle.red)
    async def negar(self, interaction, button):

        log = discord.utils.get(interaction.guild.text_channels, name=CANAL_LOG_SETS)
        await log.send(
            f"❌ SETS negado\n"
            f"Solicitante: {self.user.mention}\n"
            f"ID: {self.uid}\n"
            f"Motivo: {self.motivo}\n"
            f"Negado por: {interaction.user.mention}"
        )

        await interaction.message.delete()
        await interaction.channel.delete()


@bot.tree.command(name="sets")
async def sets(interaction: discord.Interaction):

    role = discord.utils.get(interaction.guild.roles, name=CARGO_SETS)
    if role not in interaction.user.roles:
        await interaction.response.send_message("Sem permissão", ephemeral=True)
        return

    await interaction.response.send_modal(SetsModal())


bot.run("MTQ2OTI5NTA5Njg3MTc4MDQ2NQ.G957HJ.rtlnjq1rewaSc7Hx_myiBhAE8TxTJEO1dnQi6U")
