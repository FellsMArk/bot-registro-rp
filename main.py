import discord
from discord.ext import commands
import os
import sys

# ================= CONFIGURAÇÃO =================
TOKEN = os.getenv("TOKEN_BOT") or "MTQ2OTI5NTA5Njg3MTc4MDQ2NQ.GHwnfC.COl0LdJ0bCuH2xLT_4WmPDK2nHHO9uMa0ytR1o"

# Configurações de Identidade
CARGO_CEO = "CEO"
CARGO_CBM = "CBM-RJ"
CARGO_SETS = "Sets"
CANAL_LOG_ARQUIVO = "📃-log-avisos"
CANAL_LOG_REGISTRO = "📑-log-registros"
CANAL_LOG_SETS = "📄-log-painel"
CATEGORIA_TICKETS = "📋 REGISTROS"

class FireBot(commands.Bot):
    def __init__(self):
        # Intents Totais para garantir que nada seja bloqueado
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def setup_hook(self):
        # Reativa os botões em caso de reinício do Railway
        self.add_view(ArquivoView())
        self.add_view(RegistroView())
        self.add_view(SetsView())
        print("📌 [LOG] Views persistentes carregadas com sucesso.")

    async def on_ready(self):
        print("\n" + "="*40)
        print(f"✅ BOT STATUS: ONLINE")
        print(f"🤖 USUÁRIO: {self.user.name}#{self.user.discriminator}")
        print(f"🆔 ID: {self.user.id}")
        print(f"📡 SERVIDORES: {len(self.guilds)}")
        print("="*40 + "\n")
        
        # Tenta enviar uma mensagem de teste no primeiro canal que encontrar (opcional)
        print("🚀 [LOG] Bot pronto para receber comandos '!'")

# ================= VIEWS E COMPONENTES =================

class ArquivoModal(discord.ui.Modal, title="Registro de Arquivo"):
    id_ref = discord.ui.TextInput(label="ID")
    nome_cargo = discord.ui.TextInput(label="NOME/CARGO")
    ocorrencia = discord.ui.TextInput(label="OCORRÊNCIA/AVISO", style=discord.TextStyle.paragraph)
    obs = discord.ui.TextInput(label="OBSERVAÇÃO (Opcional)", required=False)
    provas = discord.ui.TextInput(label="PROVAS (Opcional)", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        canal = discord.utils.get(interaction.guild.text_channels, name=CANAL_LOG_ARQUIVO)
        embed = discord.Embed(title="🚨 NOVO ARQUIVO", color=0x992d22)
        embed.add_field(name="🆔 ID", value=self.id_ref.value)
        embed.add_field(name="👤 Nome/Cargo", value=self.nome_cargo.value)
        embed.add_field(name="📝 Descrição", value=f"```{self.ocorrencia.value}```", inline=False)
        if canal: await canal.send(embed=embed)
        await interaction.response.send_message("✅ Registrado!", ephemeral=True)

class ArquivoView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Registrar Arquivo", style=discord.ButtonStyle.danger, custom_id="v6_arq")
    async def cb(self, it: discord.Interaction, bt):
        if discord.utils.get(it.user.roles, name=CARGO_CBM): await it.response.send_modal(ArquivoModal())
        else: await it.response.send_message("❌ Acesso restrito CBM-RJ.", ephemeral=True)

class RegistroModal(discord.ui.Modal, title="Registro"):
    id_cid = discord.ui.TextInput(label="Seu ID")
    async def on_submit(self, it: discord.Interaction):
        ceo = discord.utils.get(it.guild.roles, name=CARGO_CEO)
        cat = discord.utils.get(it.guild.categories, name=CATEGORIA_TICKETS) or await it.guild.create_category(CATEGORIA_TICKETS)
        ch = await it.guild.create_text_channel(f"registro-{it.user.name}", category=cat)
        await ch.set_permissions(it.guild.default_role, view_channel=False)
        await ch.set_permissions(ceo, view_channel=True)
        await ch.send(content=f"{ceo.mention if ceo else ''}", embed=discord.Embed(title="NOVO REGISTRO", description=f"Membro: {it.user.mention}\nID: {self.id_cid.value}"), view=AprovReg(it.user, self.id_cid.value))
        await it.response.send_message("✅ Ticket Criado!", ephemeral=True)

class AprovReg(discord.ui.View):
    def __init__(self, u, c): super().__init__(timeout=None); self.u, self.c = u, c
    @discord.ui.button(label="Aprovar", style=discord.ButtonStyle.success)
    async def sim(self, it: discord.Interaction, bt):
        if not discord.utils.get(it.user.roles, name=CARGO_CEO): return
        cargo = discord.utils.get(it.guild.roles, name=CARGO_CBM)
        m = it.guild.get_member(self.u.id)
        if m and cargo: 
            await m.add_roles(cargo)
            try: await m.edit(nick=f"{self.c} | {m.name}")
            except: print(f"⚠️ Erro ao trocar nick de {m.name}")
        log = discord.utils.get(it.guild.text_channels, name=CANAL_LOG_REGISTRO)
        if log: await log.send(f"✅ {self.u.mention} aprovado por {it.user.mention}")
        await it.channel.delete()

class RegistroView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Iniciar Registro", style=discord.ButtonStyle.success, custom_id="v6_reg")
    async def cb(self, it: discord.Interaction, bt): await it.response.send_modal(RegistroModal())

class SetsModal(discord.ui.Modal, title="Pedido de Set"):
    id_a = discord.ui.TextInput(label="ID Alvo"); mot = discord.ui.TextInput(label="Motivo")
    async def on_submit(self, it: discord.Interaction):
        cat = discord.utils.get(it.guild.categories, name=CATEGORIA_TICKETS)
        ch = await it.guild.create_text_channel(f"set-{it.user.name}", category=cat)
        await ch.send(embed=discord.Embed(title="PEDIDO DE SET", description=f"ID: {self.id_a.value}\nMotivo: {self.mot.value}"), view=AprovSet(it.user, self.id_a.value, self.mot.value))
        await it.response.send_message("✅ Ticket de Set aberto!", ephemeral=True)

class AprovSet(discord.ui.View):
    def __init__(self, s, a, m): super().__init__(timeout=None); self.s, self.a, self.m = s, a, m
    @discord.ui.button(label="Aceitar", style=discord.ButtonStyle.success)
    async def ok(self, it: discord.Interaction, bt):
        log = discord.utils.get(it.guild.text_channels, name=CANAL_LOG_SETS)
        if log: await log.send(f"💎 SET ACEITO: ID {self.a} para {self.s.mention} | CEO: {it.user.mention}")
        await it.channel.delete()
    @discord.ui.button(label="Negar", style=discord.ButtonStyle.danger)
    async def no(self, it: discord.Interaction, bt): await it.channel.delete()

class SetsView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Solicitar Set", style=discord.ButtonStyle.primary, custom_id="v6_set")
    async def cb(self, it: discord.Interaction, bt):
        if discord.utils.get(it.user.roles, name=CARGO_SETS): await it.response.send_modal(SetsModal())
        else: await it.response.send_message("❌ Sem permissão Sets.", ephemeral=True)

# ================= COMANDOS =================

bot = FireBot()

@bot.command()
async def setup(ctx):
    print(f"📢 [COMANDO] !setup usado por {ctx.author}")
    await ctx.send(embed=discord.Embed(title="📂 CENTRAL ARQUIVO", color=0x992d22), view=ArquivoView())
    await ctx.send(embed=discord.Embed(title="📝 REGISTRO CBM", color=0x2ecc71), view=RegistroView())
    await ctx.send(embed=discord.Embed(title="💎 PAINEL SETS", color=0x3498db), view=SetsView())

@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 Pong! Latência: {round(bot.latency * 1000)}ms")

bot.run(TOKEN)
