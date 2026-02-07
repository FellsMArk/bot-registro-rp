import discord
from discord.ext import commands
import json
import os

# ========================
# CONFIGURAÇÕES
# ========================

TOKEN = os.getenv("TOKEN")

CARGO_STAFF = "CEO"
CARGO_REGISTRADO = "CMB-RJ"
CANAL_LOG = "📑-log-registros"
CATEGORIA_REGISTRO = "📋 REGISTROS"

ARQUIVO_REGISTROS = "registros.json"

INTENTS = discord.Intents.default()
INTENTS.members = True
INTENTS.message_content = True

bot = commands.Bot(command_prefix="!", intents=INTENTS)

# ========================
# UTILIDADES
# ========================

def carregar_registros():
    if not os.path.exists(ARQUIVO_REGISTROS):
        return []
    with open(ARQUIVO_REGISTROS, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_registro(dados):
    registros = carregar_registros()
    registros.append(dados)
    with open(ARQUIVO_REGISTROS, "w", encoding="utf-8") as f:
        json.dump(registros, f, indent=4, ensure_ascii=False)

# ========================
# EVENTOS
# ========================

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"🤖 Bot online como {bot.user}")

# ========================
# MODAL DE REGISTRO
# ========================

class RegistroModal(discord.ui.Modal, title="Registro RP"):
    id_cidade = discord.ui.TextInput(
        label="ID da cidade RP",
        placeholder="Ex: 1542",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild

        staff_role = discord.utils.get(guild.roles, name=CARGO_STAFF)

        categoria = discord.utils.get(guild.categories, name=CATEGORIA_REGISTRO)
        if not categoria:
            categoria = await guild.create_category(CATEGORIA_REGISTRO)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=False),
            staff_role: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True)
        }

        canal = await guild.create_text_channel(
            name=f"registro-{interaction.user.name}",
            category=categoria,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title="📥 Novo pedido de registro",
            color=discord.Color.orange()
        )
        embed.add_field(name="Usuário", value=interaction.user.mention, inline=False)
        embed.add_field(name="ID da Cidade", value=self.id_cidade.value, inline=False)

        await canal.send(
            embed=embed,
            view=AprovacaoView(interaction.user, self.id_cidade.value)
        )

        await interaction.response.send_message(
            "✅ Seu pedido foi enviado para a staff.",
            ephemeral=True
        )

# ========================
# VIEW REGISTRO
# ========================

class RegistroView(discord.ui.View):
    @discord.ui.button(label="📋 Iniciar Registro", style=discord.ButtonStyle.green)
    async def registrar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RegistroModal())

# ========================
# APROVAÇÃO (SÓ CEO)
# ========================

class AprovacaoView(discord.ui.View):
    def __init__(self, usuario, id_cidade):
        super().__init__(timeout=None)
        self.usuario = usuario
        self.id_cidade = id_cidade

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        staff_role = discord.utils.get(interaction.guild.roles, name=CARGO_STAFF)
        if staff_role not in interaction.user.roles:
            await interaction.response.send_message(
                "❌ Apenas a STAFF pode usar isso.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="✅ Aprovar", style=discord.ButtonStyle.success)
    async def aprovar(self, interaction: discord.Interaction, button: discord.ui.Button):
        membro = interaction.guild.get_member(self.usuario.id)
        cargo = discord.utils.get(interaction.guild.roles, name=CARGO_REGISTRADO)

        if cargo:
            await membro.add_roles(cargo)

        await membro.edit(nick=f"{self.id_cidade} | {membro.name}")

        salvar_registro({
            "usuario
