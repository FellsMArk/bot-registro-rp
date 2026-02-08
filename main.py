import discord
from discord.ext import commands
import os
from datetime import datetime

# CONFIGURAÇÃO DE AMBIENTE
TOKEN = os.getenv("TOKEN_BOT") or "MTQ2OTI5NTA5Njg3MTc4MDQ2NQ.GHwnfC.COl0LdJ0bCuH2xLT_4WmPDK2nHHO9uMa0ytR1o"

# IDENTIDADE DO SERVIDOR
CARGO_CEO = "CEO"
CARGO_CBM = "CBM-RJ"
CARGO_SETS = "Sets"

CANAL_LOG_REGISTRO = "📑-log-registros"
CANAL_LOG_SETS = "📄-log-painel"
CANAL_LOG_ARQUIVO = "📃-log-avisos"
CATEGORIA_REGISTRO = "📋 REGISTROS"

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(RegistroView())
        self.add_view(SetsView())
        self.add_view(ArquivoView())

bot = MyBot()

# ================= 📂 SISTEMA DE ARQUIVO (CBM-RJ) =================

class ArquivoModal(discord.ui.Modal, title="Registro de Arquivo"):
    id_ref = discord.ui.TextInput(label="ID", placeholder="ID do cidadão...")
    nome_cargo = discord.ui.TextInput(label="NOME/CARGO", placeholder="Nome e cargo...")
    ocorrencia_aviso = discord.ui.TextInput(label="OCORRÊNCIA/AVISO", style=discord.TextStyle.paragraph)
    obs = discord.ui.TextInput(label="OBSERVAÇÃO (Opcional)", required=False)
    provas = discord.ui.TextInput(label="PROVAS (Opcional)", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        canal = discord.utils.get(interaction.guild.text_channels, name=CANAL_LOG_ARQUIVO)
        if not canal: return await interaction.response.send_message("Canal de log não encontrado.", ephemeral=True)

        embed = discord.Embed(title="🚨 NOVO REGISTRO DE ARQUIVO", color=0x992d22, timestamp=datetime.now())
        embed.add_field(name="🆔 ID", value=self.id_ref.value, inline=True)
        embed.add_field(name="👤 Nome/Cargo", value=self.nome_cargo.value, inline=True)
        embed.add_field(name="📝 Ocorrência/Aviso", value=f"```{self.ocorrencia_aviso.value}```", inline=False)
        if self.obs.value: embed.add_field(name="🔍 Obs", value=self.obs.value, inline=True)
        if self.provas.value: embed.add_field(name="📸 Provas", value=self.provas.value, inline=True)
        embed.set_footer(text=f"Oficial: {interaction.user.display_name}")

        await canal.send(embed=embed)
        await interaction.response.send_message("✅ Arquivo enviado com sucesso!", ephemeral=True)

class ArquivoView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Registrar Arquivo", style=discord.ButtonStyle.danger, custom_id="btn_arq_v4", emoji="📂")
    async def abrir(self, interaction: discord.Interaction, button: discord.ui.Button):
        if discord.utils.get(interaction.guild.roles, name=CARGO_CBM) not in interaction.user.roles:
            return await interaction.response.send_message("❌ Acesso restrito a CBM-RJ.", ephemeral=True)
        await interaction.response.send_modal(ArquivoModal())

# ================= 📝 SISTEMA DE REGISTRO (ID -> CEO -> CBM-RJ) =================

class RegistroModal(discord.ui.Modal, title="Registro de Cidadão"):
    id_cid = discord.ui.TextInput(label="ID da Cidade")

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        staff_role = discord.utils.get(guild.roles, name=CARGO_CEO)
        cat = discord.utils.get(guild.categories, name=CATEGORIA_REGISTRO) or await guild.create_category(CATEGORIA_REGISTRO)
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            staff_role: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True)
        }
        canal = await guild.create_text_channel(f"registro-{interaction.user.name}", category=cat, overwrites=overwrites)
        
        embed = discord.Embed(title="📋 Solicitação de Registro", color=0x2ecc71)
        embed.add_field(name="Cidadão", value=interaction.user.mention)
        embed.add_field(name="ID", value=f"`{self.id_cid.value}`")

        await canal.send(content=staff_role.mention, embed=embed, view=AprovacaoRegistro(interaction.user, self.id_cid.value))
        await interaction.response.send_message(f"✅ Pedido enviado!", ephemeral=True)

class AprovacaoRegistro(discord.ui.View):
    def __init__(self, user, cid):
        super().__init__(timeout=None)
        self.user, self.cid = user, cid

    @discord.ui.button(label="Aprovar", style=discord.ButtonStyle.success, emoji="✅")
    async def aprovar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if discord.utils.get(interaction.guild.roles, name=CARGO_CEO) not in interaction.user.roles:
            return await interaction.response.send_message("❌ Apenas o CEO!", ephemeral=True)

        membro = interaction.guild.get_member(self.user.id)
        cargo_cbm = discord.utils.get(interaction.guild.roles, name=CARGO_CBM)
        if membro and cargo_cbm:
            await membro.add_roles(cargo_cbm)
            try: await membro.edit(nick=f"{self.cid} | {membro.name}")
            except: pass
        
        log = discord.utils.get(interaction.guild.text_channels, name=CANAL_LOG_REGISTRO)
        if log: await log.send(f"✅ **Registro Aprovado:** {self.user.mention} (ID: {self.cid}) por {interaction.user.mention}")
        await interaction.channel.delete()

    @discord.ui.button(label="Negar", style=discord.ButtonStyle.danger, emoji="❌")
    async def negar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if discord.utils.get(interaction.guild.roles, name=CARGO_CEO) not in interaction.user.roles:
            return await interaction.response.send_message("❌ Apenas o CEO!", ephemeral=True)
        await interaction.channel.delete()

class RegistroView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Iniciar Registro", style=discord.ButtonStyle.success, custom_id="btn_reg_v4", emoji="📝")
    async def registrar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RegistroModal())

# ================= 💎 SISTEMA DE SETS (COM LOGS DE ACEITAR/NEGAR) =================

class SetsModal(discord.ui.Modal, title="Solicitação de Sets"):
    id_alvo = discord.ui.TextInput(label="ID do Membro", placeholder="ID de quem receberá o set")
    motivo = discord.ui.TextInput(label="Itens / Motivo", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        staff_role = discord.utils.get(guild.roles, name=CARGO_CEO)
        cat = discord.utils.get(guild.categories, name=CATEGORIA_REGISTRO)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True),
            staff_role: discord.PermissionOverwrite(view_channel=True)
        }
        canal = await guild.create_text_channel(f"sets-{interaction.user.name}", category=cat, overwrites=overwrites)
        
        embed = discord.Embed(title="💎 SOLICITAÇÃO DE SETS", color=0x3498db)
        embed.add_field(name="Solicitante", value=f"{interaction.user.mention} (ID: {interaction.user.id})", inline=False)
        embed.add_field(name="ID Alvo do Set", value=f"`{self.id_alvo.value}`", inline=True)
        embed.add_field(name="Itens/Motivo", value=f"```{self.motivo.value}```", inline=False)

        await canal.send(content=staff_role.mention, embed=embed, view=AprovacaoSets(interaction.user, self.id_alvo.value, self.motivo.value))
        await interaction.response.send_message(f"✅ Solicitação aberta: {canal.mention}", ephemeral=True)

class AprovacaoSets(discord.ui.View):
    def __init__(self, solicitante, id_alvo, motivo):
        super().__init__(timeout=None)
        self.solicitante = solicitante
        self.id_alvo = id_alvo
        self.motivo = motivo

    @discord.ui.button(label="Aceitar", style=discord.ButtonStyle.success, emoji="✅")
    async def aceitar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if discord.utils.get(interaction.guild.roles, name=CARGO_CEO) not in interaction.user.roles:
            return await interaction.response.send_message("❌ Apenas o CEO pode aceitar sets.", ephemeral=True)

        log = discord.utils.get(interaction.guild.text_channels, name=CANAL_LOG_SETS)
        if log:
            embed = discord.Embed(title="💎 SET ACEITO", color=0x2ecc71, timestamp=datetime.now())
            embed.add_field(name="Solicitante", value=f"{self.solicitante.mention} (ID: {self.solicitante.id})", inline=False)
            embed.add_field(name="ID Alvo", value=f"`{self.id_alvo}`", inline=True)
            embed.add_field(name="CEO Responsável", value=interaction.user.mention, inline=True)
            embed.add_field(name="Motivo/Itens", value=f"```{self.motivo}```", inline=False)
            await log.send(embed=embed)

        await interaction.channel.delete()

    @discord.ui.button(label="Negar", style=discord.ButtonStyle.danger, emoji="❌")
    async def negar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if discord.utils.get(interaction.guild.roles, name=CARGO_CEO) not in interaction.user.roles:
            return await interaction.response.send_message("❌ Apenas o CEO pode negar sets.", ephemeral=True)

        log = discord.utils.get(interaction.guild.text_channels, name=CANAL_LOG_SETS)
        if log:
            embed = discord.Embed(title="❌ SET NEGADO", color=0xe74c3c, timestamp=datetime.now())
            embed.add_field(name="Solicitante", value=f"{self.solicitante.mention} (ID: {self.solicitante.id})", inline=False)
            embed.add_field(name="ID Alvo", value=f"`{self.id_alvo}`", inline=True)
            embed.add_field(name="CEO Responsável", value=interaction.user.mention, inline=True)
            await log.send(embed=embed)

        await interaction.channel.delete()

class SetsView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Abrir Solicitação", style=discord.ButtonStyle.primary, custom_id="btn_sets_v4", emoji="💎")
    async def abrir(self, interaction: discord.Interaction, button: discord.ui.Button):
        if discord.utils.get(interaction.guild.roles, name=CARGO_SETS) not in interaction.user.roles:
            return await interaction.response.send_message("❌ Você não tem o cargo **Sets**.", ephemeral=True)
        await interaction.response.send_modal(SetsModal())

# ================= COMANDOS =================

@bot.command()
async def setup_geral(ctx):
    await ctx.send(embed=discord.Embed(title="📂 CENTRAL CBM-RJ", color=0x992d22), view=ArquivoView())
    await ctx.send(embed=discord.Embed(title="📝 REGISTRO", color=0x2ecc71), view=RegistroView())
    await ctx.send(embed=discord.Embed(title="💎 SOLICITAÇÃO DE SETS", color=0x3498db), view=SetsView())

bot.run(TOKEN)
