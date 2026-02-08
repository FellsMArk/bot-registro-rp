import discord
from discord.ext import commands
import os
from datetime import datetime

# ================= CONFIGURAÇÃO DE AMBIENTE =================
TOKEN = os.getenv("TOKEN_BOT") or "MTQ2OTI5NTA5Njg3MTc4MDQ2NQ.GHwnfC.COl0LdJ0bCuH2xLT_4WmPDK2nHHO9uMa0ytR1o"

# Identidade do Servidor
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
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def setup_hook(self):
        # Garante a persistência dos botões após o bot reiniciar
        self.add_view(ArquivoView())
        self.add_view(RegistroView())
        self.add_view(SetsView())

    async def on_ready(self):
        print(f"\n✅ BOT ONLINE: {self.user.name}\n🚀 Pronto para operar no Railway!\n")

bot = FireBot()

# ================= SISTEMA DE ARQUIVO (CBM-RJ) =================

class ArquivoModal(discord.ui.Modal, title="Registro de Arquivo"):
    id_ref = discord.ui.TextInput(label="ID")
    nome_cargo = discord.ui.TextInput(label="NOME/CARGO")
    ocorrencia = discord.ui.TextInput(label="OCORRÊNCIA/AVISO", style=discord.TextStyle.paragraph)
    obs = discord.ui.TextInput(label="OBSERVAÇÃO (Opcional)", required=False)
    provas = discord.ui.TextInput(label="PROVAS (Opcional)", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        canal = discord.utils.get(interaction.guild.text_channels, name=LOG_ARQUIVO)
        embed = discord.Embed(title="🚨 NOVO ARQUIVO CBM-RJ", color=0x992d22, timestamp=datetime.now())
        embed.add_field(name="🆔 ID", value=self.id_ref.value, inline=True)
        embed.add_field(name="👤 Nome/Cargo", value=self.nome_cargo.value, inline=True)
        embed.add_field(name="📝 Descrição", value=f"```{self.ocorrencia.value}```", inline=False)
        if self.obs.value: embed.add_field(name="🔍 Obs", value=self.obs.value)
        if self.provas.value: embed.add_field(name="📸 Provas", value=self.provas.value)
        embed.set_footer(text=f"Registrado por: {interaction.user.display_name}")
        
        if canal: await canal.send(embed=embed)
        await interaction.response.send_message("✅ Arquivo registrado!", ephemeral=True)

class ArquivoView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Registrar Arquivo", style=discord.ButtonStyle.danger, custom_id="v7_arq", emoji="📂")
    async def cb(self, it: discord.Interaction, bt):
        if discord.utils.get(it.user.roles, name=CARGO_CBM): await it.response.send_modal(ArquivoModal())
        else: await it.response.send_message("❌ Apenas membros da CBM-RJ.", ephemeral=True)

# ================= SISTEMA DE REGISTRO (LOG DE APROVAR/NEGAR) =================

class RegistroModal(discord.ui.Modal, title="Pedido de Registro"):
    id_cid = discord.ui.TextInput(label="Seu ID da Cidade")
    async def on_submit(self, it: discord.Interaction):
        ceo = discord.utils.get(it.guild.roles, name=CARGO_CEO)
        cat = discord.utils.get(it.guild.categories, name=CATEGORIA_TICKETS) or await it.guild.create_category(CATEGORIA_TICKETS)
        ch = await it.guild.create_text_channel(f"registro-{it.user.name}", category=cat)
        await ch.set_permissions(it.guild.default_role, view_channel=False)
        await ch.set_permissions(ceo, view_channel=True)
        
        embed = discord.Embed(title="📋 SOLICITAÇÃO DE REGISTRO", color=0x2ecc71)
        embed.add_field(name="Cidadão", value=it.user.mention)
        embed.add_field(name="ID Informado", value=self.id_cid.value)
        await ch.send(content=f"{ceo.mention if ceo else ''}", embed=embed, view=AprovReg(it.user, self.id_cid.value))
        await it.response.send_message("✅ Seu ticket foi aberto!", ephemeral=True)

class AprovReg(discord.ui.View):
    def __init__(self, u, c): super().__init__(timeout=None); self.u, self.c = u, c
    
    @discord.ui.button(label="Aprovar", style=discord.ButtonStyle.success, emoji="✅")
    async def sim(self, it: discord.Interaction, bt):
        if not discord.utils.get(it.user.roles, name=CARGO_CEO): return
        cargo = discord.utils.get(it.guild.roles, name=CARGO_CBM)
        if self.u and cargo: 
            await self.u.add_roles(cargo)
            try: await self.u.edit(nick=f"{self.c} | {self.u.name}")
            except: pass
        log = discord.utils.get(it.guild.text_channels, name=LOG_REGISTRO)
        if log: await log.send(f"✅ **REGISTRO ACEITO:** {self.u.mention} (ID: {self.c}) | CEO: {it.user.mention}")
        await it.channel.delete()

    @discord.ui.button(label="Negar", style=discord.ButtonStyle.danger, emoji="❌")
    async def nao(self, it: discord.Interaction, bt):
        if not discord.utils.get(it.user.roles, name=CARGO_CEO): return
        log = discord.utils.get(it.guild.text_channels, name=LOG_REGISTRO)
        if log: await log.send(f"❌ **REGISTRO NEGADO:** {self.u.mention} | Por CEO: {it.user.mention}")
        await it.channel.delete()

class RegistroView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Iniciar Registro", style=discord.ButtonStyle.success, custom_id="v7_reg", emoji="📝")
    async def cb(self, it: discord.Interaction, bt): await it.response.send_modal(RegistroModal())

# ================= SISTEMA DE SETS (LOG DE ACEITAR/NEGAR) =================

class SetsModal(discord.ui.Modal, title="Pedido de Set"):
    id_a = discord.ui.TextInput(label="ID do Alvo")
    mot = discord.ui.TextInput(label="Motivo/Itens", style=discord.TextStyle.paragraph)
    async def on_submit(self, it: discord.Interaction):
        ceo = discord.utils.get(it.guild.roles, name=CARGO_CEO)
        cat = discord.utils.get(it.guild.categories, name=CATEGORIA_TICKETS)
        ch = await it.guild.create_text_channel(f"set-{it.user.name}", category=cat)
        await ch.set_permissions(it.guild.default_role, view_channel=False)
        await ch.set_permissions(ceo, view_channel=True)
        await ch.set_permissions(it.user, view_channel=True)
        
        embed = discord.Embed(title="💎 SOLICITAÇÃO DE SETS", color=0x3498db)
        embed.add_field(name="Solicitante", value=it.user.mention)
        embed.add_field(name="ID Alvo", value=f"`{self.id_a.value}`")
        embed.add_field(name="Motivo", value=f"```{self.mot.value}```")
        await ch.send(content=f"{ceo.mention if ceo else ''}", embed=embed, view=AprovSet(it.user, self.id_a.value, self.mot.value))
        await it.response.send_message("✅ Solicitação de Set aberta!", ephemeral=True)

class AprovSet(discord.ui.View):
    def __init__(self, s, a, m): super().__init__(timeout=None); self.s, self.a, self.m = s, a, m
    
    @discord.ui.button(label="Aceitar", style=discord.ButtonStyle.success, emoji="✅")
    async def ok(self, it: discord.Interaction, bt):
        if not discord.utils.get(it.user.roles, name=CARGO_CEO): return
        log = discord.utils.get(it.guild.text_channels, name=LOG_SETS)
        if log:
            embed = discord.Embed(title="💎 SET ENTREGUE", color=0x2ecc71, timestamp=datetime.now())
            embed.add_field(name="Solicitante", value=self.s.mention)
            embed.add_field(name="ID Alvo", value=self.a)
            embed.add_field(name="CEO Responsável", value=it.user.mention)
            embed.add_field(name="Itens", value=f"```{self.m}```")
            await log.send(embed=embed)
        await it.channel.delete()

    @discord.ui.button(label="Negar", style=discord.ButtonStyle.danger, emoji="❌")
    async def no(self, it: discord.Interaction, bt):
        if not discord.utils.get(it.user.roles, name=CARGO_CEO): return
        log = discord.utils.get(it.guild.text_channels, name=LOG_SETS)
        if log:
            embed = discord.Embed(title="❌ SET NEGADO", color=0xe74c3c, timestamp=datetime.now())
            embed.add_field(name="Solicitante", value=self.s.mention)
            embed.add_field(name="ID Alvo", value=self.a)
            embed.add_field(name="CEO Responsável", value=it.user.mention)
            await log.send(embed=embed)
        await it.channel.delete()

class SetsView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Solicitar Set", style=discord.ButtonStyle.primary, custom_id="v7_set", emoji="💎")
    async def cb(self, it: discord.Interaction, bt):
        if discord.utils.get(it.user.roles, name=CARGO_SETS): await it.response.send_modal(SetsModal())
        else: await it.response.send_message("❌ Acesso exclusivo para o cargo Sets.", ephemeral=True)

# ================= COMANDOS =================

@bot.command()
async def setup(ctx):
    """Envia os painéis de controle"""
    await ctx.send(embed=discord.Embed(title="📂 CENTRAL DE ARQUIVO", description="Clique abaixo para registrar ocorrências.", color=0x992d22), view=ArquivoView())
    await ctx.send(embed=discord.Embed(title="📝 REGISTRO DE CIDADÃO", description="Inicie seu registro clicando no botão abaixo.", color=0x2ecc71), view=RegistroView())
    await ctx.send(embed=discord.Embed(title="💎 SOLICITAÇÃO DE SETS", description="Área para solicitação de itens e sets.", color=0x3498db), view=SetsView())

@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 Pong! Bot ativo. Latência: {round(bot.latency * 1000)}ms")

bot.run(TOKEN)
