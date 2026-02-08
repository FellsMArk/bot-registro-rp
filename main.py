import discord
from discord.ext import commands
import os
from datetime import datetime

# ================= CONFIGURAÇÃO TÉCNICA =================
# O TOKEN deve estar nas variáveis de ambiente do Railway como TOKEN_BOT
TOKEN = os.getenv("TOKEN_BOT") or "MTQ2OTI5NTA5Njg3MTc4MDQ2NQ.GHwnfC.COl0LdJ0bCuH2xLT_4WmPDK2nHHO9uMa0ytR1o"

# Configurações de Identidade (Nomes EXATOS do seu Discord)
CARGO_CEO = "CEO"
CARGO_CBM = "CBM-RJ"
CARGO_SETS = "Sets"

# Canais de Log
LOG_ARQUIVO = "📃-log-avisos"
LOG_REGISTRO = "📑-log-registros"
LOG_SETS = "📄-log-painel"
CATEGORIA_TICKETS = "📋 REGISTROS"

class FireBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True          # Necessário para dar cargos e trocar nicks
        intents.message_content = True  # CRÍTICO: Necessário para o bot ler os comandos !
        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def setup_hook(self):
        # Isso faz os botões funcionarem mesmo se o bot reiniciar
        self.add_view(ArquivoView())
        self.add_view(RegistroView())
        self.add_view(SetsView())

    async def on_ready(self):
        print(f"🚀 {self.user} ONLINE E FUNCIONAL!")

bot = FireBot()

# ================= COMPONENTES VISUAIS (MODALS & VIEWS) =================

# --- SISTEMA DE ARQUIVO ---
class ArquivoModal(discord.ui.Modal, title="Registro de Arquivo"):
    id_ref = discord.ui.TextInput(label="ID", placeholder="ID do cidadão")
    nome_cargo = discord.ui.TextInput(label="NOME/CARGO", placeholder="Nome e cargo")
    ocorrencia = discord.ui.TextInput(label="OCORRÊNCIA/AVISO", style=discord.TextStyle.paragraph)
    obs = discord.ui.TextInput(label="OBSERVAÇÃO (Opcional)", required=False)
    provas = discord.ui.TextInput(label="PROVAS (Opcional)", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        canal = discord.utils.get(interaction.guild.text_channels, name=LOG_ARQUIVO)
        embed = discord.Embed(title="🚨 NOVO ARQUIVO CBM-RJ", color=0x992d22, timestamp=datetime.now())
        embed.add_field(name="🆔 ID", value=self.id_ref.value, inline=True)
        embed.add_field(name="👤 Nome/Cargo", value=self.nome_cargo.value, inline=True)
        embed.add_field(name="📝 Ocorrência", value=f"```{self.ocorrencia.value}```", inline=False)
        if self.obs.value: embed.add_field(name="🔍 Obs", value=self.obs.value)
        if self.provas.value: embed.add_field(name="📸 Provas", value=self.provas.value)
        embed.set_footer(text=f"Oficial: {interaction.user.display_name}")
        
        if canal: await canal.send(embed=embed)
        await interaction.response.send_message("✅ Arquivo enviado!", ephemeral=True)

class ArquivoView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Registrar Arquivo", style=discord.ButtonStyle.danger, custom_id="v1_arq", emoji="📂")
    async def callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if discord.utils.get(interaction.guild.roles, name=CARGO_CBM) not in interaction.user.roles:
            return await interaction.response.send_message("❌ Acesso restrito a CBM-RJ.", ephemeral=True)
        await interaction.response.send_modal(ArquivoModal())

# --- SISTEMA DE REGISTRO ---
class RegistroModal(discord.ui.Modal, title="Registro RP"):
    id_cid = discord.ui.TextInput(label="Informe seu ID")
    async def on_submit(self, interaction: discord.Interaction):
        staff = discord.utils.get(interaction.guild.roles, name=CARGO_CEO)
        cat = discord.utils.get(interaction.guild.categories, name=CATEGORIA_TICKETS) or await interaction.guild.create_category(CATEGORIA_TICKETS)
        overwrites = {interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False), staff: discord.PermissionOverwrite(view_channel=True)}
        canal = await interaction.guild.create_text_channel(f"registro-{interaction.user.name}", category=cat, overwrites=overwrites)
        
        embed = discord.Embed(title="📋 PEDIDO DE REGISTRO", color=0x2ecc71)
        embed.add_field(name="Cidadão", value=interaction.user.mention)
        embed.add_field(name="ID", value=self.id_cid.value)
        await canal.send(content=staff.mention if staff else None, embed=embed, view=AprovacaoRegistro(interaction.user, self.id_cid.value))
        await interaction.response.send_message("✅ Pedido enviado ao CEO!", ephemeral=True)

class AprovacaoRegistro(discord.ui.View):
    def __init__(self, user, cid):
        super().__init__(timeout=None)
        self.user, self.cid = user, cid
    @discord.ui.button(label="Aprovar", style=discord.ButtonStyle.success, emoji="✅")
    async def aprovar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if discord.utils.get(interaction.guild.roles, name=CARGO_CEO) not in interaction.user.roles:
            return await interaction.response.send_message("❌ Apenas o CEO!", ephemeral=True)
        membro = interaction.guild.get_member(self.user.id)
        cargo = discord.utils.get(interaction.guild.roles, name=CARGO_CBM)
        if membro and cargo:
            await membro.add_roles(cargo)
            try: await membro.edit(nick=f"{self.cid} | {membro.name}")
            except: pass
        log = discord.utils.get(interaction.guild.text_channels, name=LOG_REGISTRO)
        if log: await log.send(f"✅ **Registro Aprovado:** {self.user.mention} por {interaction.user.mention}")
        await interaction.channel.delete()

class RegistroView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Iniciar Registro", style=discord.ButtonStyle.success, custom_id="v1_reg", emoji="📝")
    async def callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RegistroModal())

# --- SISTEMA DE SETS ---
class SetsModal(discord.ui.Modal, title="Solicitação de Sets"):
    id_alvo = discord.ui.TextInput(label="ID")
    motivo = discord.ui.TextInput(label="Motivo", style=discord.TextStyle.paragraph)
    async def on_submit(self, interaction: discord.Interaction):
        staff = discord.utils.get(interaction.guild.roles, name=CARGO_CEO)
        cat = discord.utils.get(interaction.guild.categories, name=CATEGORIA_TICKETS)
        canal = await interaction.guild.create_text_channel(f"sets-{interaction.user.name}", category=cat)
        embed = discord.Embed(title="💎 SOLICITAÇÃO DE SETS", color=0x3498db)
        embed.add_field(name="Solicitante", value=interaction.user.mention)
        embed.add_field(name="ID Alvo", value=self.id_alvo.value)
        embed.add_field(name="Motivo", value=self.motivo.value)
        await canal.send(embed=embed, view=AprovacaoSets(interaction.user, self.id_alvo.value, self.motivo.value))
        await interaction.response.send_message("✅ Solicitação aberta!", ephemeral=True)

class AprovacaoSets(discord.ui.View):
    def __init__(self, sol, alvo, mot):
        super().__init__(timeout=None)
        self.sol, self.alvo, self.mot = sol, alvo, mot
    @discord.ui.button(label="Aceitar", style=discord.ButtonStyle.success, emoji="✅")
    async def aceitar(self, interaction: discord.Interaction, button: discord.ui.Button):
        log = discord.utils.get(interaction.guild.text_channels, name=LOG_SETS)
        if log:
            embed = discord.Embed(title="💎 SET ACEITO", color=0x2ecc71)
            embed.add_field(name="Solicitante", value=self.sol.mention)
            embed.add_field(name="ID Alvo", value=self.alvo)
            embed.add_field(name="CEO", value=interaction.user.mention)
            await log.send(embed=embed)
        await interaction.channel.delete()
    @discord.ui.button(label="Negar", style=discord.ButtonStyle.danger, emoji="❌")
    async def negar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.delete()

class SetsView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Solicitar Sets", style=discord.ButtonStyle.primary, custom_id="v1_set", emoji="💎")
    async def callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if discord.utils.get(interaction.guild.roles, name=CARGO_SETS) not in interaction.user.roles:
            return await interaction.response.send_message("❌ Sem cargo Sets!", ephemeral=True)
        await interaction.response.send_modal(SetsModal())

# ================= COMANDOS DIRETOS =================

@bot.command()
async def setup(ctx):
    """Envia todos os painéis de uma vez"""
    await ctx.send(embed=discord.Embed(title="📂 CENTRAL CBM-RJ", color=0x992d22), view=ArquivoView())
    await ctx.send(embed=discord.Embed(title="📝 REGISTRO RP", color=0x2ecc71), view=RegistroView())
    await ctx.send(embed=discord.Embed(title="💎 PAINEL DE SETS", color=0x3498db), view=SetsView())

@bot.command()
async def arquivo(ctx):
    await ctx.send(embed=discord.Embed(title="📂 ARQUIVAMENTO", color=0x992d22), view=ArquivoView())

@bot.command()
async def painel_registro(ctx):
    await ctx.send(embed=discord.Embed(title="📝 REGISTRO", color=0x2ecc71), view=RegistroView())

@bot.command()
async def painel_sets(ctx):
    await ctx.send(embed=discord.Embed(title="💎 SETS", color=0x3498db), view=SetsView())

bot.run(TOKEN)
