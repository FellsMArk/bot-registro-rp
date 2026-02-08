import discord
from discord.ext import commands
import os
from datetime import datetime

# Lógica para pegar o token da variável TOKEN_BOT que está no seu Railway
TOKEN_RAW = os.getenv("TOKEN_BOT")
TOKEN = TOKEN_RAW.strip() if TOKEN_RAW else None

# Configurações de Cargos e Canais
CARGO_REGISTRADO = "CMB-RJ"
CANAL_LOG_ARQUIVO = "📃-log-avisos"

# Intents necessários (já ativados no seu portal do desenvolvedor)
INTENTS = discord.Intents.default()
INTENTS.members = True
INTENTS.message_content = True

bot = commands.Bot(command_prefix="!", intents=INTENTS)

# ================= EVENTO READY =================
@bot.event
async def on_ready():
    # Carrega as views para que os botões funcionem mesmo após o bot reiniciar
    bot.add_view(ArquivoView())
    print(f"✅ Bot Online: {bot.user}")
    if TOKEN:
        print(f"✅ Token carregado com sucesso (Início: {TOKEN[:6]}...)")

# ================= SISTEMA DE ARQUIVO (MODAL) =================

class ArquivoModal(discord.ui.Modal, title="Registro de Arquivo"):
    id_ref = discord.ui.TextInput(label="ID")
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
            embed.add_field(name="Staff", value=interaction.user.mention, inline=True)
            embed.add_field(name="ID", value=self.id_ref.value, inline=True)
            embed.add_field(name="Nome", value=self.nome.value, inline=True)
            embed.add_field(name="Cargo", value=self.cargo.value, inline=True)
            embed.add_field(name="Ocorrência", value=self.ocorrencia.value, inline=False)
            embed.add_field(name="Aviso", value=self.aviso.value, inline=False)
            embed.add_field(name="Observação", value=self.obs.value or "Nenhuma", inline=False)
            embed.add_field(name="Provas", value=self.provas.value or "Nenhuma", inline=False)
            embed.set_footer(text=f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

            await canal_log.send(embed=embed)
            await interaction.response.send_message("✅ Arquivo enviado com sucesso para a log.", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Erro: Canal '{CANAL_LOG_ARQUIVO}' não encontrado.", ephemeral=True)

class ArquivoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Criar Arquivo", style=discord.ButtonStyle.blurple, custom_id="btn_arquivo_fixo")
    async def abrir_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Verifica se o usuário tem o cargo necessário
        role = discord.utils.get(interaction.guild.roles, name=CARGO_REGISTRADO)
        if role and role not in interaction.user.roles:
            await interaction.response.send_message("❌ Você não tem permissão para usar este sistema.", ephemeral=True)
            return
        
        await interaction.response.send_modal(ArquivoModal())

# ================= COMANDO PARA ENVIAR O PAINEL =================

@bot.command()
async def setup_arquivo(ctx):
    embed = discord.Embed(
        title="📂 Sistema de Arquivamento",
        description="Clique no botão abaixo para abrir o formulário de registro.",
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed, view=ArquivoView())

# ================= EXECUÇÃO =================

if __name__ == "__main__":
    if TOKEN:
        try:
            bot.run(TOKEN)
        except Exception as e:
            print(f"❌ Erro ao iniciar o bot: {e}")
    else:
        print("❌ ERRO CRÍTICO: Variável 'TOKEN_BOT' não encontrada no Railway.")
