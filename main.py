import discord
from discord.ext import commands
import json
import os

# ========================
# CONFIGURAÇÕES
# ========================

TOKEN = os.getenv("TOKEN")

CARGO_STAFF = "CEO"
CARGO_REGISTRADO = "CBM-RJ"
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
            "✅ Seu pedido de registro foi enviado para análise.",
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
                "❌ Apenas a STAFF pode aprovar ou negar.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="✅ Aprovar", style=discord.ButtonStyle.success)
    async def aprovar(self, interaction: discord.Interaction, button: discord.ui.Button):
        mensagem = interaction.message

        membro = interaction.guild.get_member(self.usuario.id)
        cargo = discord.utils.get(interaction.guild.roles, name=CARGO_REGISTRADO)

        if cargo:
            await membro.add_roles(cargo)

        await membro.edit(nick=f"{self.id_cidade} | {membro.name}")

        salvar_registro({
            "usuario": str(membro),
            "id_cidade": self.id_cidade,
            "status": "Aprovado"
        })

        canal_log = discord.utils.get(interaction.guild.text_channels, name=CANAL_LOG)
        if canal_log:
            await canal_log.send(
                f"✅ **Registro aprovado**\n"
                f"👤 Usuário: {membro.mention}\n"
                f"🏙️ Cidade: {self.id_cidade}\n"
                f"🛡️ Aprovado por: {interaction.user.mention}"
            )

        await mensagem.delete()
        await interaction.channel.delete()

    @discord.ui.button(label="❌ Negar", style=discord.ButtonStyle.danger)
    async def negar(self, interaction: discord.Interaction, button: discord.ui.Button):
        mensagem = interaction.message

        salvar_registro({
            "usuario": str(self.usuario),
            "id_cidade": self.id_cidade,
            "status": "Negado"
        })

        canal_log = discord.utils.get(interaction.guild.text_channels, name=CANAL_LOG)
        if canal_log:
            await canal_log.send(
                f"❌ **Registro negado**\n"
                f"👤 Usuário: {self.usuario.mention}\n"
                f"🏙️ Cidade: {self.id_cidade}\n"
                f"🛡️ Negado por: {interaction.user.mention}"
            )

        await mensagem.delete()
        await interaction.channel.delete()

# ========================
# COMANDO SLASH (SEM MENSAGEM NO CANAL)
# ========================

@bot.tree.command(name="registro", description="Abrir painel de registro RP")
async def registro(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📋 Registro RP",
        description="Clique no botão abaixo para iniciar seu registro.",
        color=discord.Color.blue()
    )

    await interaction.response.send_message(
        embed=embed,
        view=RegistroView(),
        ephemeral=True
    )

# ========================
# INICIAR BOT
# ========================

bot.run(TOKEN)
