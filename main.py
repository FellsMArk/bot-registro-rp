import discord
from discord.ext import commands
import os
from datetime import datetime

# ================= CONFIGURAÇÃO AMBIENTE =================
TOKEN = os.getenv("TOKEN_BOT")

# NOMES EXATOS DE CARGOS E CANAIS (Verifique no seu Discord)
CARGOS = {
    "STAFF": "CEO",
    "REGISTRADO": "CMB-RJ",
    "SETS": "Sets"
}

CANAIS_LOG = {
    "REGISTRO": "📑-log-registros",
    "SETS": "📄-log-painel",
    "ARQUIVO": "📃-log-avisos"
}

CATEGORIA_TICKETS = "📋 REGISTROS"

# ================= CLASSES DE INTERFACE (VIEWS/MODALS) =================

# --- SISTEMA DE ARQUIVO ---
class ArquivoModal(discord.ui.Modal, title="Registro de Arquivo"):
    id_ref = discord.ui.TextInput(label="ID", placeholder="Ex: 102")
    nome = discord.ui.TextInput(label="NOME", placeholder="Nome completo...")
    cargo = discord.ui.TextInput(label="CARGO", placeholder="Cargo do indivíduo...")
    ocorrencia = discord.ui.TextInput(label="OCORRÊNCIA", style=discord.TextStyle.paragraph)
    aviso = discord.ui.TextInput(label="AVISO", placeholder="Tipo de aviso...")
    obs = discord.ui.TextInput(label="OBSERVAÇÃO", required=False)
    provas = discord.ui.TextInput(label="PROVAS", placeholder="Links de imagens/vídeos", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        canal = discord.utils.get(interaction.guild.text_channels, name=CANAIS_LOG["ARQUIVO"])
        if not canal:
            return await interaction.response.send_message("Canal de log não encontrado.", ephemeral=True)

        embed = discord.Embed(title="📁 NOVO ARQUIVO REGISTRADO", color=discord.Color.red(), timestamp=datetime.now())
        embed.add_field(name="👮 Responsável", value=interaction.user.mention, inline=False)
        embed.add_field(name="👤 Indivíduo", value=f"ID: {self.id_ref}\nNome: {self.nome}", inline=True)
        embed.add_field(name="💼 Cargo", value=self.cargo, inline=True)
        embed.add_field(name="📝 Ocorrência", value=self.ocorrencia, inline=False)
        embed.add_field(name="⚠️ Aviso", value=self.aviso, inline=True)
        embed.add_field(name="🔍 Obs", value=self.obs.value or "Nenhuma", inline=True)
        if self.provas.value: embed.add_field(name="📸 Provas", value=self.provas, inline=False)

        await canal.send(embed=embed)
        await interaction.response.send_message("✅ Arquivo enviado com sucesso!", ephemeral=True)

class ArquivoView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Criar Arquivo", style=discord.ButtonStyle.danger, custom_id="btn_arq")
    async def callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name=CARGOS["REGISTRADO"])
        if role not in interaction.user.roles:
            return await interaction.response.send_message("Acesso restrito à CMB-RJ.", ephemeral=True)
        await interaction.response.send_modal(ArquivoModal())

# --- SISTEMA DE REGISTRO RP ---
class RegistroModal(discord.ui.Modal, title="Formulário de Registro"):
    id_cidade = discord.ui.TextInput(label="ID da Cidade", placeholder="Seu ID in-game")
    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        staff_role = discord.utils.get(guild.roles, name=CARGOS["STAFF"])
        cat = discord.utils.get(guild.categories, name=CATEGORIA_TICKETS) or await guild.create_category(CATEGORIA_TICKETS)
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            staff_role: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        canal = await guild.create_text_channel(f"registro-{interaction.user.name}", category=cat, overwrites=overwrites)
        await canal.send(f"📌 {interaction.user.mention}, aguarde a análise.", view=AprovacaoRegistro(interaction.user, self.id_cidade.value))
        await interaction.response.send_message(f"Canal criado: {canal.mention}", ephemeral=True)

class RegistroView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Iniciar Registro", style=discord.ButtonStyle.success, custom_id="btn_reg")
    async def callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RegistroModal())

class AprovacaoRegistro(discord.ui.View):
    def __init__(self, user, cid):
        super().__init__(timeout=None)
        self.user, self.cid = user, cid
    @discord.ui.button(label="Aprovar", style=discord.ButtonStyle.success)
    async def aprovar(self, interaction: discord.Interaction, button: discord.ui.Button):
        membro = interaction.guild.get_member(self.user.id)
        role = discord.utils.get(interaction.guild.roles, name=CARGOS["REGISTRADO"])
        if membro and role:
            await membro.add_roles(role)
            try: await membro.edit(nick=f"{self.cid} | {membro.name}")
            except: pass
        await interaction.channel.delete()

# --- SISTEMA DE SETS ---
class SetsView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Solicitar Sets", style=discord.ButtonStyle.primary, custom_id="btn_sets")
    async def callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name=CARGOS["SETS"])
        if role not in interaction.user.roles:
            return await interaction.response.send_message("Sem permissão.", ephemeral=True)
        await interaction.response.send_message("Ticket de SETS aberto!", ephemeral=True)

# ================= BOT CORE =================

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Carrega as views para que os botões funcionem após reinicialização
        self.add_view(ArquivoView())
        self.add_view(RegistroView())
        self.add_view(SetsView())

    async def on_ready(self):
        print(f"✅ Logado como {self.user} | Railway Operacional")

bot = MyBot()

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_tudo(ctx):
    # Envia todos os painéis de uma vez para organização
    await ctx.send(embed=discord.Embed(title="📂 ARQUIVAMENTO CMB-RJ", color=discord.Color.red()), view=ArquivoView())
    await ctx.send(embed=discord.Embed(title="📝 REGISTRO DE CIDADÃO", color=discord.Color.green()), view=RegistroView())
    await ctx.send(embed=discord.Embed(title="💎 SOLICITAÇÃO DE SETS", color=discord.Color.blue()), view=SetsView())

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ TOKEN_BOT não configurado nas variáveis do Railway!")
