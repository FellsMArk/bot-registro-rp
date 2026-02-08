import discord
from discord.ext import commands
import os
from datetime import datetime

# Lógica para pegar o token da variável que você criou no Railway
TOKEN = os.getenv("TOKEN_BOT")

# Configurações de Cargos e Canais
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

# ================= READY =================
@bot.event
async def on_ready():
    # Registra as views persistentes para os botões não pararem de funcionar
    bot.add_view(RegistroView())
    bot.add_view(SetsView())
    bot.add_view(ArquivoView())
    print(f"✅ Bot Online como {bot.user}")

# ================= SISTEMA DE ARQUIVO (CMB-RJ) =================

class ArquivoModal(discord.ui.Modal, title="Registro de Arquivo"):
    id_ref = discord.ui.TextInput(label="ID", placeholder="Digite o ID...")
    nome = discord.ui.TextInput(label="NOME", placeholder="Nome do indivíduo...")
    cargo = discord.ui.TextInput(label="CARGO", placeholder="Cargo ocupado...")
    ocorrencia = discord.ui.TextInput(label="OCORRÊNCIA", style=discord.TextStyle.paragraph)
    aviso = discord.ui.TextInput(label="AVISO", placeholder="Tipo de aviso aplicado...")
    obs = discord.ui.TextInput(label="OBSERVAÇÃO (Opcional)", required=False)
    provas = discord.ui.TextInput(label="PROVAS (Opcional)", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        canal_log = discord.utils.get(interaction.guild.text_channels, name=CANAL_LOG_ARQUIVO)
        if not canal_log:
            return await interaction.response.send_message(f"Canal {CANAL_LOG_ARQUIVO} não encontrado!", ephemeral=True)

        embed = discord.Embed(title="📁 Novo Registro de Arquivo", color=discord.Color.red())
        embed.add_field(name="👮 Staff Responsável", value=interaction.user.mention, inline=False)
        embed.add_field(name="🆔 ID", value=self.id_ref.value, inline=True)
        embed.add_field(name="👤 Nome", value=self.nome.value, inline=True)
        embed.add_field(name="💼 Cargo", value=self.cargo.value, inline=True)
        embed.add_field(name="📝 Ocorrência", value=self.ocorrencia.value, inline=False)
        embed.add_field(name="⚠️ Aviso", value=self.aviso.value, inline=True)
        embed.add_field(name="🔍 Observação", value=self.obs.value or "Nenhuma", inline=True)
        embed.add_field(name="📸 Provas", value=self.provas.value or "Nenhuma", inline=False)
        embed.set_footer(text=f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

        await canal_log.send(embed=embed)
        await interaction.response.send_message("✅ Arquivo registrado com sucesso!", ephemeral=True)

class ArquivoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Abrir Registro de Arquivo", style=discord.ButtonStyle.danger, custom_id="btn_arquivo")
    async def abrir_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name=CARGO_REGISTRADO)
        if role not in interaction.user.roles:
            return await interaction.response.send_message("❌ Você não tem permissão (Cargo CMB-RJ necessário).", ephemeral=True)
        await interaction.response.send_modal(ArquivoModal())

# ================= SISTEMA DE REGISTRO (TICKET) =================

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
        
        embed = discord.Embed(title="Novo Registro", color=discord.Color.orange())
        embed.add_field(name="Usuário", value=interaction.user.mention)
        embed.add_field(name="Cidade", value=self.id_cidade.value)

        await canal.send(f"{interaction.user.mention} aguarde um Staff.", embed=embed, view=AprovacaoRegistro(interaction.user, self.id_cidade.value))
        await interaction.response.send_message(f"Seu canal de registro foi criado: {canal.mention}", ephemeral=True)

class RegistroView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Iniciar Registro", style=discord.ButtonStyle.green, custom_id="registro_btn")
    async def registrar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RegistroModal())

class AprovacaoRegistro(discord.ui.View):
    def __init__(self, usuario, cidade):
        super().__init__(timeout=None)
        self.usuario = usuario
        self.cidade = cidade

    @discord.ui.button(label="Aprovar", style=discord.ButtonStyle.success)
    async def aprovar(self, interaction: discord.Interaction, button: discord.ui.Button):
        role_staff = discord.utils.get(interaction.guild.roles, name=CARGO_STAFF)
        if role_staff not in interaction.user.roles:
            return await interaction.response.send_message("Apenas Staff pode aprovar.", ephemeral=True)

        membro = interaction.guild.get_member(self.usuario.id)
        cargo_reg = discord.utils.get(interaction.guild.roles, name=CARGO_REGISTRADO)
        
        if membro and cargo_reg:
            await membro.add_roles(cargo_reg)
            try:
                await membro.edit(nick=f"{self.cidade} | {membro.name}")
            except:
                pass
        
        canal_log = discord.utils.get(interaction.guild.text_channels, name=CANAL_LOG_REGISTRO)
        if canal_log:
            await canal_log.send(f"✅ **Registro Aprovado**\nMembro: {self.usuario.mention}\nStaff: {interaction.user.mention}")
        
        await interaction.channel.delete()

    @discord.ui.button(label="Negar", style=discord.ButtonStyle.danger)
    async def negar(self, interaction: discord.Interaction, button: discord.ui.Button):
        role_staff = discord.utils.get(interaction.guild.roles, name=CARGO_STAFF)
        if role_staff not in interaction.user.roles:
            return await interaction.response.send_message("Apenas Staff pode negar.", ephemeral=True)
            
        await interaction.channel.delete()

# ================= SISTEMA DE SETS =================

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
            staff_role: discord.PermissionOverwrite(view_channel=True)
        }

        canal = await guild.create_text_channel(f"sets-{interaction.user.name}", category=categoria, overwrites=overwrites)
        
        embed = discord.Embed(title="Solicitação de SETS", color=discord.Color.blue())
        embed.add_field(name="ID", value=self.user_id.value)
        embed.add_field(name="Motivo", value=self.motivo.value)

        await canal.send(embed=embed, view=AprovacaoSets(interaction.user, self.user_id.value, self.motivo.value))
        await interaction.response.send_message(f"Solicitação criada em {canal.mention}", ephemeral=True)

class SetsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Abrir Solicitação", style=discord.ButtonStyle.green, custom_id="sets_btn")
    async def abrir(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name=CARGO_SETS)
        if role not in interaction.user.roles:
            return await interaction.response.send_message("Você não tem o cargo 'Sets' para solicitar.", ephemeral=True)
        await interaction.response.send_modal(SetsModal())

class AprovacaoSets(discord.ui.View):
    def __init__(self, solicitante, uid, motivo):
        super().__init__(timeout=None)
        self.solicitante = solicitante
        self.uid = uid
        self.motivo = motivo

    @
