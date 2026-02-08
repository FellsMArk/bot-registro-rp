import discord
from discord.ext import commands
import os
from datetime import datetime

# PEGA O TOKEN E LIMPA ESPAÇOS/QUEBRAS DE LINHA AUTOMATICAMENTE
TOKEN_RAW = os.getenv("TOKEN")
TOKEN = TOKEN_RAW.strip() if TOKEN_RAW else None

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
    print(f"✅ Bot Online como {bot.user}")

# ================= SISTEMA ARQUIVO =================

class ArquivoModal(discord.ui.Modal, title="Registro de Arquivo"):
    id = discord.ui.TextInput(label="ID")
    nome = discord.ui.TextInput(label="Nome")
    cargo = discord.ui.TextInput(label="Cargo")
    ocorrencia = discord.ui.TextInput(label="Ocorrência")
    aviso = discord.ui.TextInput(label="Aviso")
    obs = discord.ui.TextInput(label="Observação", required=False)
    provas = discord.ui.TextInput(label="Provas", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        canal_log = discord.utils.get(interaction.guild.text_channels, name=CANAL_LOG_ARQUIVO)

        if canal_log:
            embed = discord.Embed(title="Novo Aviso Registrado", color=discord.Color.blue())
            embed.add_field(name="Staff", value=interaction.user.mention)
            embed.add_field(name="ID", value=self.id.value)
            embed.add_field(name="Nome", value=self.nome.value)
            embed.add_field(name="Cargo", value=self.cargo.value)
            embed.add_field(name="Ocorrência", value=self.ocorrencia.value)
            embed.add_field(name="Aviso", value=self.aviso.value)
            embed.add_field(name="Observação", value=self.obs.value or "Nenhuma")
            embed.add_field(name="Provas", value=self.provas.value or "Nenhuma")
            embed.set_footer(text=datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

            await canal_log.send(embed=embed)

        await interaction.response.send_message("Arquivo enviado.", ephemeral=True)


class ArquivoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Criar Arquivo", style=discord.ButtonStyle.blurple, custom_id="arquivo_btn")
    async def abrir(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction
