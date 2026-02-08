import discord
from discord.ext import commands
import os
from datetime import datetime

# TOKEN: Pega do Railway ou usa o fornecido
TOKEN = os.getenv("TOKEN_BOT") or "MTQ2OTI5NTA5Njg3MTc4MDQ2NQ.GHwnfC.COl0LdJ0bCuH2xLT_4WmPDK2nHHO9uMa0ytR1o"

# Configurações de Identidade
CARGO_STAFF = "CEO"
CARGO_REGISTRADO = "CBM-RJ"
CARGO_SETS = "Sets"

CANAL_LOG_REGISTRO = "📑-log-registros"
CANAL_LOG_SETS = "📄-log-painel"
CANAL_LOG_ARQUIVO = "📃-log-avisos"
CATEGORIA_REGISTRO = "📋 REGISTROS"

INTENTS = discord.Intents.default()
INTENTS.members = True
INTENTS.message_content = True

bot = commands.Bot(command_prefix="!", intents=INTENTS)

@bot.event
async def on_ready():
    # Registra as views para persistência (botões não morrem)
    bot.add_view(RegistroView())
    bot.add_view(SetsView())
    bot.add_view(ArquivoView())
    print(f"🚀 Bot Online como {bot.user}")

# ================= SISTEMA DE ARQUIVO (CBM-RJ) =================

class ArquivoModal(discord.ui.Modal, title="Registro de Arquivo CBM-RJ"):
    # Limite de 5 campos respeitado aqui para evitar o erro de 'open space'
    id_nome = discord.ui.TextInput(label="ID e Nome", placeholder="Ex: 102 - João Silva")
    cargo = discord.ui.TextInput(label="Cargo", placeholder="Ex: Sargento")
    ocorrencia = discord.ui.TextInput(label="Ocorrência", style=discord.TextStyle.paragraph)
    aviso = discord.ui.TextInput(label="Aviso Aplicado", placeholder="Ex: Advertência 2")
    extras = discord.ui.TextInput(label="Observações e Provas", style=discord.TextStyle.paragraph, required=False, placeholder="Anote aqui observações e links de provas...")

    async def on_submit(self, interaction: discord.Interaction):
        canal = discord.utils.get(interaction.guild.text_channels, name=CANAL_LOG_ARQUIVO)
        if not canal:
            return await interaction.response.send_message(f"❌ Erro: Canal `{CANAL_LOG_ARQUIVO}` não encontrado.", ephemeral=True)

        embed = discord.Embed(title="🚨 REGISTRO DE ARQUIVO - CBM-RJ", color=0x992d22, timestamp=datetime.now())
        embed.add_field(name="👤 Indivíduo", value=self.id_nome.value, inline=True)
        embed.add_field(name="💼 Cargo", value=self.cargo.value, inline=True)
        embed.add_field(name="⚠️ Aviso", value=self.aviso.value, inline=False)
        embed.add_field(name="📝 Ocorrência", value=f"```{self.ocorrencia.value}```", inline=False)
        if self.extras.value:
            embed.add_field(name="🔍 Informações Extra / Provas", value=self.extras.value, inline=False)
        
        embed.set_footer(text=f"Registrado por Oficial: {interaction.user.display_name}")

        await canal.send(embed=embed)
        await interaction.response.send_message("✅ Arquivo CBM-RJ registrado com sucesso!", ephemeral=True)

class ArquivoView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Registrar Arquivo", style=discord.ButtonStyle.danger, custom_id="btn_arq_final", emoji="📂")
    async def abrir(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name=CARGO_REGISTRADO)
        if role not in interaction.user.roles:
            return await interaction.response.send_message("❌ Acesso restrito a oficiais da **CBM-RJ**.", ephemeral=True)
        await interaction.response.send_modal(ArquivoModal())

# ================= SISTEMA DE SETS (COM ID) =================

class SetsModal(discord.ui.Modal, title="Solicitação de Sets"):
    uid = discord.ui.TextInput(label="ID do Usuário", placeholder="ID de quem vai receber o set")
    motivo = discord.ui.TextInput(label="Motivo / Itens", style=discord.TextStyle.paragraph, placeholder="Descreva o que está sendo solicitado...")

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        staff_role = discord.utils.get(guild.roles, name=CARGO_STAFF)
        categoria = discord.utils.get(guild.categories, name=CATEGORIA_REGISTRO)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True),
            staff_role: discord.PermissionOverwrite(view_channel=True)
        }

        canal = await guild.create_text_channel(f"sets-{interaction.user.name}", category=categoria, overwrites=overwrites)
        
        embed = discord.Embed(title="💎 SOLICITAÇÃO DE SETS", color=0x3498db)
        embed.add_field(name="Solicitante", value=interaction.user.mention, inline=True)
        embed.add_field(name="ID Alvo", value=f"`{self.uid.value}`", inline=True)
        embed.add_field(name="Motivo", value=f"```{self.motivo.value}```", inline=False)

        await canal.send(embed=embed, view=AprovacaoSets(interaction.user, self.uid.value, self.motivo.value))
        await interaction.response.send_message(f"✅ Solicitação de Sets aberta em {canal.mention}", ephemeral=True)

class AprovacaoSets(discord.ui.View):
    def __init__(self, solicitante, uid, motivo):
        super().__init__(timeout=None)
        self.solicitante, self.uid, self.motivo = solicitante, uid, motivo

    @discord.ui.button(label="Concluir", style=discord.ButtonStyle.success, emoji="✅")
    async def concluir(self, interaction: discord.Interaction, button: discord.ui.Button):
        canal_log = discord.utils.get(interaction.guild.text_channels, name=CANAL_LOG_SETS)
        if canal_log:
            await canal_log.send(f"✅ **Sets Concluído**\nID: `{self.uid}`\nSolicitante: {self.solicitante.mention}\nStaff: {interaction.user.mention}")
        await interaction.channel.delete()

    @discord.ui.button(label="Negar", style=discord.ButtonStyle.danger, emoji="❌")
    async def negar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.delete()

class SetsView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Abrir Solicitação", style=discord.ButtonStyle.primary, custom_id="btn_sets_final", emoji="💎")
    async def abrir(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name=CARGO_SETS)
        if role not in interaction.user.roles:
            return await interaction.response.send_message("❌ Você não tem o cargo **Sets**.", ephemeral=True)
        await interaction.response.send_modal(SetsModal())

# ================= SISTEMA DE REGISTRO =================

class RegistroModal(discord.ui.Modal, title="Registro RP"):
    id_cid = discord.ui.TextInput(label="ID da Cidade")

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        staff_role = discord.utils.get(guild.roles, name=CARGO_STAFF)
        cat = discord.utils.get(guild.categories, name=CATEGORIA_REGISTRO) or await guild.create_category(CATEGORIA_REGISTRO)
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True),
            staff_role: discord.PermissionOverwrite(view_channel=True)
        }

        canal = await guild.create_text_channel(f"registro-{interaction.user.name}", category=cat, overwrites=overwrites)
        
        embed = discord.Embed(title="📋 NOVO REGISTRO", color=0x2ecc71)
        embed.add_field(name="Cidadão", value=interaction.user.mention, inline=True)
        embed.add_field(name="ID Informado", value=f"`{self.id_cid.value}`", inline=True)

        await canal.send(embed=embed, view=AprovacaoRegistro(interaction.user, self.id_cid.value))
        await interaction.response.send_message(f"✅ Ticket criado: {canal.mention}", ephemeral=True)

class AprovacaoRegistro(discord.ui.View):
    def __init__(self, user, cid):
        super().__init__(timeout=None)
        self.user, self.cid = user, cid

    @discord.ui.button(label="Aprovar", style=discord.ButtonStyle.success, emoji="✅")
    async def sim(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name=CARGO_REGISTRADO)
        membro = interaction.guild.get_member(self.user.id)
        if membro:
            await membro.add_roles(role)
            try: await membro.edit(nick=f"{self.cid} | {membro.name}")
            except: pass
        
        log = discord.utils.get(interaction.guild.text_channels, name=CANAL_LOG_REGISTRO)
        if log: await log.send(f"✅ **Aprovado:** {self.user.mention} (ID: {self.cid}) por {interaction.user.mention}")
        await interaction.channel.delete()

    @discord.ui.button(label="Negar", style=discord.ButtonStyle.danger, emoji="❌")
    async def nao(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.delete()

class RegistroView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Iniciar Registro", style=discord.ButtonStyle.success, custom_id="btn_reg_final", emoji="📝")
    async def registrar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RegistroModal())

# ================= COM
