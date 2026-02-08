import discord
from discord.ext import commands
import os
from datetime import datetime

# Lógica de conexão com o Railway
TOKEN = os.getenv("TOKEN_BOT")

# Configurações do Bot
INTENTS = discord.Intents.default()
INTENTS.members = True
INTENTS.message_content = True

bot = commands.Bot(command_prefix="!", intents=INTENTS)

# --- SISTEMA DE LOGS ---
CANAL_LOG_ARQUIVO = "📃-log-avisos"
CARGO_REGISTRADO = "CMB-RJ"

@bot.event
async def on_ready():
    # Isso garante que os botões voltem a funcionar se o bot cair e voltar
    bot.add_view(ArquivoView())
    print(f"✅ BOT ONLINE: {bot.user}")
    print(f"📡 Servidores: {len(bot.guilds)}")

# --- INTERFACE DO FORMULÁRIO ---
class ArquivoModal(discord.ui.Modal, title="Registro de Arquivo"):
    id_ref = discord.ui.TextInput(label="ID")
    nome = discord.ui.TextInput(label="Nome")
    cargo = discord.ui.TextInput(label="Cargo")
    ocorrencia = discord.ui.TextInput(label="Ocorrência", style=discord.TextStyle.paragraph)
    aviso = discord.ui.TextInput(label="Aviso")
    obs = discord.ui.TextInput(label="Observação", required=False)
    provas = discord.ui.TextInput(label="Provas (Link)", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        canal_log = discord.utils.get(interaction.guild.text_channels, name=CANAL_LOG_ARQUIVO)
        
        if not canal_log:
            return await interaction.response.send_message(f"Erro: Canal {CANAL_LOG_ARQUIVO} não encontrado!", ephemeral=True)

        embed = discord.Embed(title="📝 Novo Registro", color=discord.Color.blue())
        embed.add_field(name="Staff", value=interaction.user.mention)
        embed.add_field(name="ID/Nome", value=f"{self.id_ref.value} - {self.nome.value}")
        embed.add_field(name="Cargo", value=self.cargo.value)
        embed.add_field(name="Ocorrência", value=self.ocorrencia.value, inline=False)
        embed.add_field(name="Aviso", value=self.aviso.value, inline=False)
        embed.set_footer(text=f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

        await canal_log.send(embed=embed)
        await interaction.response.send_message("✅ Registro enviado com sucesso!", ephemeral=True)

class ArquivoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Criar Arquivo", style=discord.ButtonStyle.blurple, custom_id="btn_arq_fixo")
    async def abrir_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ArquivoModal())

# --- COMANDO DE SETUP ---
@bot.command()
async def setup(ctx):
    embed = discord.Embed(title="Painel de Controle", description="Clique abaixo para abrir o formulário.")
    await ctx.send(embed=embed, view=ArquivoView())

# --- INICIALIZAÇÃO ---
if __name__ == "__main__":
    if TOKEN:
        try:
            bot.run(TOKEN)
        except Exception as e:
            print(f"❌ Erro de Login: {e}")
    else:
        print("❌ Variável TOKEN_BOT não encontrada!")
