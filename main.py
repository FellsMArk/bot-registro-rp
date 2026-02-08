import discord
from discord.ext import commands
import os
from datetime import datetime

# TOKEN DO RAILWAY
TOKEN = os.getenv("TOKEN_BOT") or "MTQ2OTI5NTA5Njg3MTc4MDQ2NQ.GHwnfC.COl0LdJ0bCuH2xLT_4WmPDK2nHHO9uMa0ytR1o"

# NOMES DOS CARGOS (Devem ser iguais aos do Discord)
CARGO_CEO = "CEO"
CARGO_CBM = "CBM-RJ"
CARGO_SETS = "Sets"

# NOMES DOS CANAIS DE LOG
LOG_ARQUIVO = "📃-log-avisos"
LOG_REGISTRO = "📑-log-registros"
LOG_SETS = "📄-log-painel"
CATEGORIA_TICKETS = "📋 REGISTROS"

class FireBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def setup_hook(self):
        # Registra as views para que os botões não morram ao reiniciar
        self.add_view(ArquivoView())
        self.add_view(RegistroView())
        self.add_view(SetsView())

    async def on_ready(self):
        print(f"\n" + "="*30)
        print(f"✅ BOT ESTÁ ON: {self.user.name}")
        print(f"🚀 LOGS DE SETS E NEGAR REGISTRO: ATIVADAS")
        print("="*30 + "\n")

bot = FireBot()

# ================= 📂 SISTEMA DE ARQUIVO =================
class ArquivoModal(discord.ui.Modal, title="Registro de Arquivo"):
    id_ref = discord.ui.TextInput(label="ID")
    nome = discord.ui.TextInput(label="NOME/CARGO")
    aviso = discord.ui.TextInput(label="OCORRÊNCIA/AVISO", style=discord.TextStyle.paragraph)
    obs = discord.ui.TextInput(label="OBSERVAÇÃO (Opcional)", required=False)
    prv = discord.ui.TextInput(label="PROVAS (Opcional)", required=False)

    async def on_submit(self, it: discord.Interaction):
        canal = discord.utils.get(it.guild.text_channels, name=LOG_ARQUIVO)
        emb = discord.Embed(title="🚨 NOVO ARQUIVO CBM-RJ", color=0x992d22, timestamp=datetime.now())
        emb.add_field(name="🆔 ID", value=self.id_ref.value, inline=True)
        emb.add_field(name="👤 Nome", value=self.nome.value, inline=True)
        emb.add_field(name="📝 Descrição", value=f"```{self.aviso.value}```", inline=False)
        if self.obs.value: emb.add_field(name="🔍 Obs", value=self.obs.value)
        if self.prv.value: emb.add_field(name="📸 Provas", value=self.prv.value)
        if canal: await canal.send(embed=emb)
        await it.response.send_message("✅ Enviado com sucesso!", ephemeral=True)

class ArquivoView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Registrar Arquivo", style=discord.ButtonStyle.danger, custom_id="v8_arq", emoji="📂")
    async def cb(self, it: discord.Interaction, bt):
        if discord.utils.get(it.user.roles, name=CARGO_CBM): await it.response.send_modal(ArquivoModal())
        else: await it.response.send_message("❌ Apenas CBM-RJ.", ephemeral=True)

# ================= 📝 SISTEMA DE REGISTRO (APROVAR/NEGAR) =================
class AprovReg(discord.ui.View):
    def __init__(self, user, cid):
        super().__init__(timeout=None)
        self.user, self.cid = user, cid

    @discord.ui.button(label="Aprovar", style=discord.ButtonStyle.success, emoji="✅")
    async def sim(self, it: discord.Interaction, bt):
        if not discord.utils.get(it.user.roles, name=CARGO_CEO): return
        cargo = discord.utils.get(it.guild.roles, name=CARGO_CBM)
        if self.user and cargo:
            await self.user.add_roles(cargo)
            try: await self.user.edit(nick=f"{self.cid} | {self.user.name}")
            except: pass
        log = discord.utils.get(it.guild.text_channels, name=LOG_REGISTRO)
        if log: await log.send(f"✅ **REGISTRO ACEITO:** {self.user.mention} (ID: {self.cid}) | CEO: {it.user.mention}")
        await it.channel.delete()

    @discord.ui.button(label="Negar", style=discord.ButtonStyle.danger, emoji="❌")
    async def nao(self, it: discord.Interaction, bt):
        if not discord.utils.get(it.user.roles, name=CARGO_CEO): return
        log = discord.utils.get(it.guild.text_channels, name=LOG_REGISTRO)
        if log: await log.send(f"❌ **REGISTRO NEGADO:** {self.user.mention} | Por CEO: {it.user.mention}")
        await it.channel.delete()

class RegistroView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Iniciar Registro", style=discord.ButtonStyle.success, custom_id="v8_reg", emoji="📝")
    async def cb(self, it: discord.Interaction, bt):
        modal = discord.ui.Modal(title="Registro")
        id_in = discord.ui.TextInput(label="Informe seu ID")
        async def on_sub(it2):
            cat = discord.utils.get(it2.guild.categories, name=CATEGORIA_TICKETS) or await it2.guild.create_category(CATEGORIA_TICKETS)
            ch = await it2.guild.create_text_channel(f"registro-{it2.user.name}", category=cat)
            await ch.set_permissions(it2.guild.default_role, view_channel=False)
            await ch.set_permissions(discord.utils.get(it2.guild.roles, name=CARGO_CEO), view_channel=True)
            await ch.send(content=it2.user.mention, embed=discord.Embed(title="PEDIDO", description=f"ID: {id_in.value}"), view=AprovReg(it2.user, id_in.value))
            await it2.response.send_message("✅ Ticket Criado!", ephemeral=True)
        modal.add_item(id_in); modal.on_submit = on_sub
        await it.response.send_modal(modal)

# ================= 💎 SISTEMA DE SETS (COM LOGS) =================
class AprovSet(discord.ui.View):
    def __init__(self, solicitante, alvo, motivo):
        super().__init__(timeout=None)
        self.sol, self.alvo, self.mot = solicitante, alvo, motivo

    @discord.ui.button(label="Aceitar", style=discord.ButtonStyle.success, emoji="✅")
    async def ok(self, it: discord.Interaction, bt):
        if not discord.utils.get(it.user.roles, name=CARGO_CEO): return
        log = discord.utils.get(it.guild.text_channels, name=LOG_SETS)
        if log:
            emb = discord.Embed(title="💎 SET ACEITO", color=0x2ecc71, timestamp=datetime.now())
            emb.add_field(name="Solicitante", value=self.sol.mention)
            emb.add_field(name="ID Alvo", value=self.alvo)
            emb.add_field(name="Motivo", value=self.mot)
            emb.add_field(name="CEO", value=it.user.mention)
            await log.send(embed=emb)
        await it.channel.delete()

    @discord.ui.button(label="Negar", style=discord.ButtonStyle.danger, emoji="❌")
    async def no(self, it: discord.Interaction, bt):
        if not discord.utils.get(it.user.roles, name=CARGO_CEO): return
        log = discord.utils.get(it.guild.text_channels, name=LOG_SETS)
        if log:
            emb = discord.Embed(title="❌ SET NEGADO", color=0xe74c3c, timestamp=datetime.now())
            emb.add_field(name="Solicitante", value=self.sol.mention)
            emb.add_field(name="CEO", value=it.user.mention)
            await log.send(embed=emb)
        await it.channel.delete()

class SetsView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Solicitar Set", style=discord.ButtonStyle.primary, custom_id="v8_set", emoji="💎")
    async def cb(self, it: discord.Interaction, bt):
        if not discord.utils.get(it.user.roles, name=CARGO_SETS): return await it.response.send_message("❌ Apenas cargo Sets.", ephemeral=True)
        modal = discord.ui.Modal(title="Solicitação de Sets")
        ida = discord.ui.TextInput(label="ID do Alvo")
        mtt = discord.ui.TextInput(label="Motivo / Itens", style=discord.TextStyle.paragraph)
        async def on_sub(it2):
            ch = await it2.guild.create_text_channel(f"set-{it2.user.name}", category=discord.utils.get(it2.guild.categories, name=CATEGORIA_TICKETS))
            await ch.send(embed=discord.Embed(title="PEDIDO DE SET", description=f"ID: {ida.value}\nMotivo: {mtt.value}"), view=AprovSet(it2.user, ida.value, mtt.value))
            await it2.response.send_message("✅ Aberto!", ephemeral=True)
        modal.add_item(ida); modal.add_item(mtt); modal.on_submit = on_sub
        await it.response.send_modal(modal)

# ================= COMANDOS =================
@bot.command()
async def setup(ctx):
    await ctx.send(embed=discord.Embed(title="📂 CENTRAL ARQUIVO", color=0x992d22), view=ArquivoView())
    await ctx.send(embed=discord.Embed(title="📝 REGISTRO CBM", color=0x2ecc71), view=RegistroView())
    await ctx.send(embed=discord.Embed(title="💎 PAINEL SETS", color=0x3498db), view=SetsView())

bot.run(TOKEN)
