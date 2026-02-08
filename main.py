import discord
from discord.ext import commands
import os
from datetime import datetime

# Lógica para pegar o token da variável que você criou no Railway
TOKEN = os.getenv("TOKEN_BOT")

# Configurações de Cargos e Canais
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
    # Registra as views persistentes para os botões não pararem de funcionar
    bot.add_view(RegistroView())
    bot.add_view(SetsView())
    bot.add_view(ArquivoView())
    print(f"✅ Bot Online como {bot.user}")

# ================= SISTEMA DE ARQUIVO (CMB-RJ) =================

class ArquivoModal(discord.ui.Modal, title="Registro de Arquivo"):
    id_ref = discord.ui.TextInput(label="ID", placeholder="Digite o ID...")
    nome = discord.ui.TextInput(label="NOME", placeholder="Nome do indivíduo...")
    cargo = discord.ui.TextInput(label="CARGO", placeholder="Cargo ocupado...")
    ocorrencia = discord.ui.TextInput(label="OCORRÊNCIA", style=discord.TextStyle.paragraph)
    aviso = discord.ui.TextInput(label="AVISO", placeholder="Tipo de aviso aplicado...")
    obs = discord.ui.TextInput(label="OBSERVAÇÃO (Opcional)", required=False)
    provas = discord.ui.TextInput(label="PROVAS (Opcional)", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        canal_log = discord.utils.get(interaction.guild.text_channels, name=CANAL_LOG_ARQUIVO)
        if not canal_log:
            return await interaction.response.send_message(f"Canal {CANAL_LOG_ARQUIVO} não encontrado!", ephemeral=True)

        embed = discord.Embed(title="📁 Novo Registro de Arquivo", color=discord.Color.red())
        embed.add_field(name="👮 Staff Responsável", value=interaction.user.mention, inline=False)
        embed.add_field(name="🆔 ID", value=self.id_ref.value, inline=True)
        embed.add_field(name="👤 Nome", value=self.nome.value, inline=True)
        embed.add_field(name="💼 Cargo", value=self.cargo.value, inline=True)
        embed.add_field(name="📝 Ocorrência", value=self.ocorrencia.value, inline=False)
        embed.add_field(name="⚠️ Aviso", value=self.aviso.value, inline=True)
        embed.add_field(name="🔍 Observação", value=self.obs.value or "Nenhuma", inline=True)
        embed.add_field(name="📸 Provas", value=self.provas.value or "Nenhuma", inline=False)
        embed.set_footer(text=f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

        await canal_log.send(embed=embed)
        await interaction.response.send_message("✅ Arquivo registrado com sucesso!", ephemeral=True)

class ArquivoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Abrir Registro de Arquivo", style=discord.ButtonStyle.danger, custom_id="btn_arquivo")
    async def abrir_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name=CARGO_REGISTRADO)
        if role not in interaction.user.roles:
            return await interaction.response.send_message("❌ Você não tem permissão (Cargo CMB-RJ necessário).", ephemeral=True)
        await interaction.response.send_modal(ArquivoModal())

# ================= SISTEMA DE REGISTRO (TICKET) =================

class RegistroModal(discord.ui.Modal, title="Registro
