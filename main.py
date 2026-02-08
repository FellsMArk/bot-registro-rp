import discord
from discord.ext import commands
import os
from datetime import datetime

# Pega o token da variável TOKEN_BOT no Railway
TOKEN = os.getenv("TOKEN_BOT")

# Configurações
CARGO_STAFF = "CEO"
CARGO_REGISTRADO = "CMB-RJ"
CARGO_SETS = "Sets"

CANAL_LOG_REGISTRO = "📑-log-registros"
CANAL_LOG_SETS = "📄-log-painel"
CANAL_LOG_ARQUIVO = "📃-log-avisos"

CATEGORIA_REGISTRO = "📋 REGISTROS"

INTENTS = discord.Intents.default()
INTENTS.members = True
INTENTS.message_content = True

bot = commands.Bot(command_prefix="!", intents=INTENTS)

# ================= READY =================
@bot.event
async def on_ready():
    bot.add_view(RegistroView())
    bot.add_view(SetsView())
    bot.add_view(ArquivoView())
    print(f"✅ Bot Online: {bot.user}")

# ================= SISTEMA DE ARQUIVO (CMB-RJ) =================

class ArquivoModal(discord.ui.Modal, title="Registro de Arquivo"):
    id_ref = discord.ui.TextInput(label="ID", placeholder="Digite o ID...")
    nome = discord.ui.TextInput(label="NOME", placeholder="Nome...")
    cargo = discord.ui.TextInput(label="CARGO", placeholder="Cargo...")
    ocorrencia = discord.ui.TextInput(label="OCORRÊNCIA", style=discord.TextStyle.paragraph)
    aviso = discord.ui.TextInput(label="AVISO", placeholder="Tipo de aviso...")
    obs = discord.ui.TextInput(label="OBSERVAÇÃO", required=False)
    provas = discord.ui.TextInput(label="PROVAS", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        canal_log = discord.utils.get(interaction.guild.text_channels, name=CANAL_LOG_ARQUIVO)
        if not canal_log:
            return await interaction.response.send_message(f"Canal {CANAL_LOG_ARQUIVO} não encontrado!", ephemeral=True)

        embed = discord.Embed(title="📁 Novo Registro de Arquivo", color=discord.Color.red())
        embed.add_field(name="👮 Staff", value=interaction.user.mention, inline=False)
        embed.add_field(name="🆔 ID", value=self.id_ref.value, inline=True)
        embed.add_field(name="👤 Nome", value=self.nome.value, inline=True)
        embed.add_field(name="📝 Ocorrência", value=self.ocorrencia.value, inline=False)
        embed.set_footer(text=f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

        await canal_log.send(embed=embed)
        await interaction.response.send_message("✅ Arquivo registrado!", ephemeral=True)

class ArquivoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Criar Arquivo", style=discord.ButtonStyle.danger, custom_id="btn_arq")
    async def abrir(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name=CARGO_REGISTRADO)
        if role not in interaction.user.roles:
            return await interaction.response.send_message("❌ Apenas CMB-RJ pode usar!", ephemeral=True)
        await interaction.response.send_modal(ArquivoModal())

# ================= SISTEMA DE REGISTRO =================

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
            interaction.user: discord.PermissionOverwrite(view_channel=True),
            staff_role: discord.PermissionOverwrite(view_channel=True)
        }
        canal = await guild.create_text_channel(f"registro-{interaction.user.name}", category=categoria, overwrites=overwrites)
        await canal.send(f"{interaction.user.mention}", view=AprovacaoRegistro(interaction.user, self.id_cidade.value))
        await interaction.response.send_message(f"Canal criado: {canal.mention}", ephemeral=True)

class RegistroView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Iniciar Registro", style=discord.ButtonStyle.green, custom_id="reg_btn")
    async def registrar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RegistroModal())

class AprovacaoRegistro(discord.ui.View):
    def __init__(self, usuario, cidade):
        super().__init__(timeout=None)
        self.usuario = usuario
        self.cidade = cidade

    @discord.ui.button(label="Aprovar", style=discord.ButtonStyle.success)
    async def aprovar(self, interaction: discord.Interaction, button: discord.ui.Button):
        membro = interaction.guild.get_member(self.usuario.id)
        cargo = discord.utils.get(interaction.guild.roles, name=CARGO_REGISTRADO)
        if membro and cargo:
            await membro.add_roles(cargo)
            try: await membro.edit(nick=f"{self.cidade} | {membro.name}")
            except: pass
        await interaction.channel.delete()

# ================= SISTEMA DE SETS =================

class SetsModal(discord.ui.Modal, title="Solicitação Sets"):
    uid = discord.ui.TextInput(label="ID")
    motivo = discord.ui.TextInput(label="Motivo")

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        staff_role = discord.utils.get(guild.roles, name=CARGO_STAFF)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True),
            staff_role: discord.PermissionOverwrite(view_channel=True)
        }
        canal = await guild.create_text_channel(f"sets-{interaction.user.name}", overwrites=overwrites)
        await canal.send(f"Solicitação de {interaction.user.mention}", view=AprovacaoSets(interaction.user))
        await interaction.response.send_message("Solicitação aberta!", ephemeral=True)

class SetsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Abrir Sets", style=discord.ButtonStyle.blurple, custom_id="sets_btn")
    async def abrir(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name=CARGO_SETS)
        if role not in interaction.user.roles:
            return await interaction.response.send_message("Sem permissão!", ephemeral=True)
        await interaction.response.send_modal(SetsModal())

class AprovacaoSets(discord.ui.View):
    def __init__(self, solicitante):
        super().__init__(timeout=None)
        self.solicitante = solicitante

    @discord.ui.button(label="Concluir", style=discord.ButtonStyle.success)
    async def concluir(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.delete()

# ================= COMANDOS =================

@bot.command()
async def arquivo(ctx):
    await ctx.send(embed=discord.Embed(title="📁 Sistema de Arquivo"), view=ArquivoView())

@bot.command()
async def painel_registro(ctx):
    await ctx.send("Painel de Registro", view=RegistroView())

@bot.command()
async def painel_sets(ctx):
    await ctx.send("Painel de Sets", view=SetsView())

if TOKEN:
    bot.run(TOKEN)
