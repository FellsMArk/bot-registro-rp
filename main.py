import discord
from discord.ext import commands
import os
from datetime import datetime

# Busca primeiro pela nova variável para ignorar caches antigos
TOKEN_RAW = os.getenv("TOKEN_BOT") or os.getenv("TOKEN")
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
    # Garante que as views persistentes funcionem após reiniciar
    bot.add_view(RegistroView())
    bot.add_view(SetsView())
    bot.add_view(ArquivoView())
    print(f"✅ Sucesso! Bot logado como: {bot.user}")

# ================= SISTEMA ARQUIVO =================

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
            embed.add_field(name="Staff", value=interaction.user.mention)
            embed.add_field(name="ID", value=self.id_ref.value)
            embed.add_field(name="Nome", value=self.nome.value)
            embed.add_field(name="Cargo", value=self.cargo.value)
            embed.add_field(name="Ocorrência", value=self.ocorrencia.value)
            embed.add_field(name="Aviso", value=self.aviso.value)
            embed.add_field(name="Observação", value=self.obs.value or "Nenhuma")
            embed.add_field(name="Provas", value=self.provas.value or "Nenhuma")
            embed.set_footer(text=datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

            await canal_log.send(embed=embed)

        await interaction.response.send_message("Arquivo enviado com sucesso.", ephemeral=True)


class ArquivoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Criar Arquivo", style=discord.ButtonStyle.blurple, custom_id="arquivo_btn")
    async def abrir(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name=CARGO_REGISTRADO)

        if role and role not in interaction.user.roles:
            await interaction.response.send_message("Você não possui o cargo necessário.", ephemeral=True)
            return

        await interaction.response.send_modal(ArquivoModal())


@bot.command()
async def arquivo(ctx):
    embed = discord.Embed(title="Sistema de Arquivos", description="Clique no botão abaixo para registrar um aviso.")
    await ctx.send(embed=embed, view=ArquivoView())

# ================= PAINEIS (VIEWS VAZIAS PARA REGISTRO) =================

class RegistroView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

class SetsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

@bot.command()
async def painel_registro(ctx):
    embed = discord.Embed(title="Painel de Registro")
    await ctx.send(embed=embed, view=RegistroView())

@bot.command()
async def painel_sets(ctx):
    embed = discord.Embed(title="Painel SETS")
    await ctx.send(embed=embed, view=SetsView())

# ================= EXECUÇÃO COM DIAGNÓSTICO FINAL =================

if __name__ == "__main__":
    if TOKEN:
        print("--- DIAGNÓSTICO DE INICIALIZAÇÃO ---")
        print(f"Token utilizado: {TOKEN[:6]}...{TOKEN[-4:]}")
        print(f"Total de caracteres: {len(TOKEN)}")
        print("------------------------------------")
        
        try:
            bot.run(TOKEN)
        except discord.errors.LoginFailure:
            print("❌ ERRO FATAL: O Discord rejeitou este
