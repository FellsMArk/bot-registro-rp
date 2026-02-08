import discord
from discord.ext import commands
import os
from datetime import datetime

# Pega o token da variável de ambiente (Railway) ou usa o que você forneceu
TOKEN = os.getenv("TOKEN_BOT") or "MTQ2OTI5NTA5Njg3MTc4MDQ2NQ.GHwnfC.COl0LdJ0bCuH2xLT_4WmPDK2nHHO9uMa0ytR1o"

# Configurações de Nomes
CARGO_STAFF = "CEO"
CARGO_REGISTRADO = "CBM-RJ" # Corrigido para CBM
CARGO_SETS = "Sets"

CANAL_LOG_REGISTRO = "📑-log-registros"
CANAL_LOG_SETS = "📄-log-painel"
CANAL_LOG_ARQUIVO = "📃-log-avisos"
CATEGORIA_REGISTRO = "📋 REGISTROS"

INTENTS = discord.Intents.default()
INTENTS.members = True
INTENTS.message_content = True

bot = commands.Bot(command_prefix="!", intents=INTENTS)

# ================= READY (Com Persistência) =================
@bot.event
async def on_ready():
    await bot.tree.sync()
    # Adicionando as views ao listener para os botões não pararem de funcionar
    bot.add_view(RegistroView())
    bot.add_view(SetsView())
    bot.add_view(ArquivoView())
    print(f"✅ Sistema Online como {bot.user}")

# ================= NOVO SISTEMA: ARQUIVO (CBM-RJ) =================

class ArquivoModal(discord.ui.Modal, title="📝 Registro de Arquivo CBM-RJ"):
    id_ref = discord.ui.TextInput(label="ID", placeholder="ID do cidadão...")
    nome = discord.ui.TextInput(label="NOME", placeholder="Nome do cidadão...")
    cargo = discord.ui.TextInput(label="CARGO", placeholder="Cargo ocupado...")
    ocorrencia = discord.ui.TextInput(label="OCORRÊNCIA", style=discord.TextStyle.paragraph)
    aviso = discord.ui.TextInput(label="AVISO", placeholder="Tipo de aviso...")
    obs = discord.ui.TextInput(label="OBSERVAÇÃO (Opcional)", required=False)
    provas = discord.ui.TextInput(label="PROVAS (Opcional)", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        canal_log = discord.utils.get(interaction.guild.text_channels, name=CANAL_LOG_ARQUIVO)
        
        if not canal_log:
            return await interaction.response.send_message(f"❌ Canal de log `{CANAL_LOG_ARQUIVO}` não encontrado.", ephemeral=True)

        embed = discord.Embed(title="🚨 NOVO REGISTRO DE ARQUIVO", color=0x992d22, timestamp=datetime.now())
        embed.set_author(name=f"Staff: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        
        embed.add_field(name="🆔 ID", value=self.id_ref.value, inline=True)
        embed.add_field(name="👤 Nome", value=self.nome.value, inline=True)
        embed.add_field(name="💼 Cargo", value=self.cargo.value, inline=True)
        embed.add_field(name="📝 Ocorrência", value=f"```{self.ocorrencia.value}```", inline=False)
        embed.add_field(name="⚠️ Aviso", value=self.aviso.value, inline=True)
        
        if self.obs.value: embed.add_field(name="🔍 Observação", value=self.obs.value, inline=True)
        if self.provas.value: embed.add_field(name="📸 Provas", value=self.provas.value, inline=False)
        
        embed.set_footer(text=f"Registrado por: {interaction.user.name}")

        await canal_log.send(embed=embed)
        await interaction.response.send_message("✅ Arquivo enviado com sucesso!", ephemeral=True)

class ArquivoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Abrir Formulário de Arquivo", style=discord.ButtonStyle.danger, custom_id="btn_arquivo_cbm", emoji="📂")
    async def abrir(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name=CARGO_REGISTRADO)
        if role not in interaction.user.roles:
            return await interaction.response.send_message("❌ Somente membros da **CBM-RJ** podem usar este comando.", ephemeral=True)
        await interaction.response.send_modal(ArquivoModal())

# ================= REGISTRO (ORIGINAL REMODELADO) =================

class RegistroModal(discord.ui.Modal, title="Registro RP"):
    id_cidade = discord.ui.TextInput(label="ID da cidade")

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        staff_role = discord.utils.get(guild.roles, name=CARGO_STAFF)
        categoria = discord.utils.get(guild.categories, name=CATEGORIA_REGISTRO)

        if not categoria:
            categoria = await guild.create_category(CATEGORIA_REGISTRO)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True),
            staff_role: discord.PermissionOverwrite(view_channel=True),
            guild.me: discord.PermissionOverwrite(view_channel=True)
        }

        canal = await guild.create_text_channel(f"registro-{interaction.user.name}", category=categoria, overwrites=overwrites)
        
        embed = discord.Embed(title="📋 Novo Pedido de Registro", color=0x2ecc71)
        embed.add_field(name="Usuário", value=interaction.user.mention, inline=True)
        embed.add_field(name="Cidade (ID)", value=f"`{self.id_cidade.value}`", inline=True)
        embed.set_footer(text="Aguarde a Staff para realizar sua aprovação.")

        await canal.send(embed=embed, view=AprovacaoRegistro(interaction.user, self.id_cidade.value))
        await interaction.response.send_message(f"✅ Ticket criado em {canal.mention}", ephemeral=True)

class RegistroView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Iniciar Registro", style=discord.ButtonStyle.green, custom_id="registro_btn", emoji="📝")
    async def registrar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RegistroModal())

class AprovacaoRegistro(discord.ui.View):
    def __init__(self, usuario, cidade):
        super().__init__(timeout=None)
        self.usuario = usuario
        self.cidade = cidade

    async def interaction_check(self, interaction):
        role = discord.utils.get(interaction.guild.roles, name=CARGO_STAFF)
        if role not in interaction.user.roles:
            await interaction.response.send_message("❌ Apenas Staff pode usar estes botões.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Aprovar", style=discord.ButtonStyle.success, emoji="✅")
    async def aprovar(self, interaction: discord.Interaction, button: discord.ui.Button):
        membro = interaction.guild.get_member(self.usuario.id)
        cargo = discord.utils.get(interaction.guild.roles, name=CARGO_REGISTRADO)

        if membro and cargo:
            await membro.add_roles(cargo)
            try: await membro.edit(nick=f"{self.cidade} | {membro.name}")
            except: pass

        canal_log = discord.utils.get(interaction.guild.text_channels, name=CANAL_LOG_REGISTRO)
        if canal_log:
            await canal_log.send(f"✅ **Registro aprovado:** {membro.mention}\nStaff: {interaction.user.mention}")

        await interaction.channel.delete()

    @discord.ui.button(label="Negar", style=discord.ButtonStyle.danger, emoji="❌")
    async def negar(self, interaction: discord.Interaction, button: discord.ui.Button):
        canal_log = discord.utils.get(interaction.guild.text_channels, name=CANAL_LOG_REGISTRO)
        if canal_log:
            await canal_log.send(f"❌ **Registro negado:** {self.usuario.mention}\nStaff: {interaction.user.mention}")
        await interaction.channel.delete()

# ================= SETS (ORIGINAL REMODELADO) =================

class SetsModal(discord.ui.Modal, title="Solicitação Sets"):
    user_id = discord.ui.TextInput(label="ID do usuário")
    motivo = discord.ui.TextInput(label="Motivo", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        staff_role = discord.utils.get(guild.roles, name=CARGO_STAFF)
        categoria = discord.utils.get(guild.categories, name=CATEGORIA_REGISTRO)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True),
            staff_role: discord.PermissionOverwrite(view_channel=True),
            guild.me: discord.PermissionOverwrite(view_channel=True)
        }

        canal = await guild.create_text_channel(f"sets-{interaction.user.name}", category=categoria, overwrites=overwrites)
        
        embed = discord.Embed(title="💎 Solicitação de SETS", color=0x3498db)
        embed.add_field(name="Solicitante", value=interaction.user.mention)
        embed.add_field(name="ID", value=self.user_id.value)
        embed.add_field(name="Motivo", value=f"```{self.motivo.value}```")

        await canal.send(embed=embed, view=AprovacaoSets(interaction.user, self.user_id.value, self.motivo.value))
        await interaction.response.send_message(f"✅ Solicitação aberta: {canal.mention}", ephemeral=True)

class AprovacaoSets(discord.ui.View):
    def __init__(self, solicitante, uid, motivo):
        super().__init__(timeout=None)
        self.solicitante = solicitante
        self.uid = uid
        self.motivo = motivo

    async def interaction_check(self, interaction):
        role = discord.utils.get(interaction.guild.roles, name=CARGO_STAFF)
        return role in interaction.user.roles

    @discord.ui.button(label="Concluir", style=discord.ButtonStyle.success, emoji="✅")
    async def aprovar(self, interaction: discord.Interaction, button: discord.ui.Button):
        canal_log = discord.utils.get(interaction.guild.text_channels, name=CANAL_LOG_SETS)
        if canal_log:
            await canal_log.send(f"💎 **SETS concluído:** {self.solicitante.mention} | Staff: {interaction.user.mention}")
        await interaction.channel.delete()

    @discord.ui.button(label="Negar", style=discord.ButtonStyle.danger, emoji="❌")
    async def negar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.delete()

class SetsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Abrir Solicitação", style=discord.ButtonStyle.primary, custom_id="sets_btn", emoji="💎")
    async def abrir(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name=CARGO_SETS)
        if role not in interaction.user.roles:
            return await interaction.response.send_message("❌ Você não possui o cargo necessário.", ephemeral=True)
        await interaction.response.send_modal(SetsModal())

# ================= COMANDOS =================

@bot.command()
async def arquivo(ctx):
    embed = discord.Embed(
        title="📂 Central de Arquivamento - CBM-RJ",
        description="Clique no botão abaixo para preencher as informações de registro, avisos e ocorrências.",
        color=0x992d22
    )
    await ctx.send(embed=embed, view=ArquivoView())

@bot.command()
async def painel_registro(ctx):
    embed = discord.Embed(title="📝 Iniciar Registro", color=0x2ecc71)
    await ctx.send(embed=embed, view=RegistroView())

@bot.command()
async def painel_sets(ctx):
    embed = discord.Embed(title="💎 Painel de Solicitação de Sets", color=0x3498db)
    await ctx.send(embed=embed, view=SetsView())

bot.run(TOKEN)
