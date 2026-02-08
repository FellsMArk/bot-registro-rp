import discord
from discord.ext import commands
import os
from datetime import datetime

# ================= CONFIGURAÇÃO DE AMBIENTE =================
TOKEN = os.getenv("TOKEN_BOT")

# CONFIGURAÇÕES DE IDENTIDADE DO SERVIDOR
CARGOS = {
    "STAFF": "CEO",
    "CBM_RJ": "CBM-RJ", 
    "SETS": "Sets"
}

CANAIS_LOG = {
    "REGISTRO": "📑-log-registros",
    "SETS": "📄-log-painel",
    "ARQUIVO": "📃-log-avisos"
}

CATEGORIA_TICKETS = "📋 REGISTROS"

# ================= INTERFACES (MODALS & VIEWS) =================

# --- 📂 SISTEMA DE ARQUIVAMENTO (CBM-RJ) ---
class ArquivoModal(discord.ui.Modal, title="📝 Formulário de Arquivamento"):
    id_ref = discord.ui.TextInput(label="ID do Indivíduo", placeholder="Ex: 102", min_length=1)
    nome = discord.ui.TextInput(label="Nome Completo", placeholder="Nome do cidadão...")
    cargo = discord.ui.TextInput(label="Cargo do Indivíduo", placeholder="Cargo ocupado...")
    ocorrencia = discord.ui.TextInput(label="Descrição da Ocorrência", style=discord.TextStyle.paragraph, placeholder="Detalhe o que aconteceu...")
    aviso = discord.ui.TextInput(label="Tipo de Aviso", placeholder="Ex: Aviso 1, Suspensão...")
    obs = discord.ui.TextInput(label="Observações Adicionais", required=False, placeholder="Algo a acrescentar?")
    provas = discord.ui.TextInput(label="Links de Provas", placeholder="Imgur, YouTube, etc.", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        canal = discord.utils.get(interaction.guild.text_channels, name=CANAIS_LOG["ARQUIVO"])
        if not canal:
            return await interaction.response.send_message("❌ Erro: Canal de log não encontrado.", ephemeral=True)

        embed = discord.Embed(
            title="⚠️ NOVO ARQUIVO REGISTRADO - CBM-RJ",
            description=f"Um novo registro foi efetuado por {interaction.user.mention}",
            color=0x992d22, # Dark Red
            timestamp=datetime.now()
        )
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        embed.add_field(name="👤 Indivíduo", value=f"**ID:** {self.id_ref}\n**Nome:** {self.nome}", inline=True)
        embed.add_field(name="💼 Cargo", value=self.cargo, inline=True)
        embed.add_field(name="📜 Aviso Aplicado", value=f"**{self.aviso}**", inline=False)
        embed.add_field(name="📝 Ocorrência", value=f"```{self.ocorrencia}```", inline=False)
        
        if self.obs.value: embed.add_field(name="🔍 Observação", value=self.obs, inline=True)
        if self.provas.value: embed.add_field(name="📸 Provas anexadas", value=self.provas, inline=True)
        
        embed.set_footer(text="Sistema de Gestão CBM-RJ")

        await canal.send(embed=embed)
        await interaction.response.send_message("✅ **Registro de arquivo enviado com sucesso para a log!**", ephemeral=True)

class ArquivoView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Registrar Arquivo", style=discord.ButtonStyle.danger, custom_id="btn_arq_cbm", emoji="📂")
    async def callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name=CARGOS["CBM_RJ"])
        if role not in interaction.user.roles:
            return await interaction.response.send_message("❌ **Acesso Negado:** Somente oficiais da **CBM-RJ** podem realizar arquivamentos.", ephemeral=True)
        await interaction.response.send_modal(ArquivoModal())

# --- 📝 SISTEMA DE REGISTRO DE CIDADÃO ---
class RegistroModal(discord.ui.Modal, title="📋 Registro de Cidadão"):
    id_cidade = discord.ui.TextInput(label="ID na Cidade", placeholder="Digite seu ID in-game", min_length=1, max_length=10)
    
    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        staff_role = discord.utils.get(guild.roles, name=CARGOS["STAFF"])
        cat = discord.utils.get(guild.categories, name=CATEGORIA_TICKETS) or await guild.create_category(CATEGORIA_TICKETS)
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True),
            staff_role: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        
        canal = await guild.create_text_channel(f"🎫-{interaction.user.name}", category=cat, overwrites=overwrites)
        
        embed = discord.Embed(
            title="📥 Novo Pedido de Registro",
            description=f"Olá {interaction.user.mention}, bem-vindo! Aguarde um membro da Staff para realizar sua aprovação.\n\n**ID Informado:** `{self.id_cidade}`",
            color=0x2ecc71 # Green
        )
        embed.set_footer(text="Use os botões abaixo para gerenciar este ticket.")
        
        await canal.send(content=f"{interaction.user.mention} | {staff_role.mention}", embed=embed, view=AprovacaoRegistro(interaction.user, self.id_cidade.value))
        await interaction.response.send_message(f"✅ Seu ticket foi criado com sucesso: {canal.mention}", ephemeral=True)

class RegistroView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Iniciar Registro", style=discord.ButtonStyle.success, custom_id="btn_reg_cbm", emoji="📝")
    async def callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RegistroModal())

class AprovacaoRegistro(discord.ui.View):
    def __init__(self, user, cid):
        super().__init__(timeout=None)
        self.user, self.cid = user, cid

    @discord.ui.button(label="Aprovar", style=discord.ButtonStyle.success, emoji="✅")
    async def aprovar(self, interaction: discord.Interaction, button: discord.ui.Button):
        membro = interaction.guild.get_member(self.user.id)
        role = discord.utils.get(interaction.guild.roles, name=CARGOS["CBM_RJ"])
        staff_role = discord.utils.get(interaction.guild.roles, name=CARGOS["STAFF"])

        if staff_role not in interaction.user.roles:
            return await interaction.response.send_message("❌ Somente a Staff pode aprovar registros.", ephemeral=True)

        if membro and role:
            await membro.add_roles(role)
            try: await membro.edit(nick=f"{self.cid} | {membro.name}")
            except: pass
        
        log = discord.utils.get(interaction.guild.text_channels, name=CANAIS_LOG["REGISTRO"])
        if log:
            embed = discord.Embed(title="✅ Registro Aprovado", color=0x2ecc71, timestamp=datetime.now())
            embed.add_field(name="Membro", value=self.user.mention, inline=True)
            embed.add_field(name="Staff", value=interaction.user.mention, inline=True)
            embed.add_field(name="ID", value=f"`{self.cid}`", inline=True)
            await log.send(embed=embed)
            
        await interaction.channel.delete()

# --- 💎 SISTEMA DE SETS ---
class SetsModal(discord.ui.Modal, title="💎 Solicitação de Sets"):
    motivo = discord.ui.TextInput(label="Motivo da Solicitação", style=discord.TextStyle.paragraph, placeholder="Descreva o que você precisa e por quê...")
    async def on_submit(self, interaction: discord.Interaction):
        staff_role = discord.utils.get(interaction.guild.roles, name=CARGOS["STAFF"])
        cat = discord.utils.get(interaction.guild.categories, name=CATEGORIA_TICKETS)
        
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True),
            staff_role: discord.PermissionOverwrite(view_channel=True)
        }
        canal = await interaction.guild.create_text_channel(f"💎-sets-{interaction.user.name}", category=cat, overwrites=overwrites)
        
        embed = discord.Embed(title="💎 Solicitação de Sets", color=0x3498db)
        embed.add_field(name="Solicitante", value=interaction.user.mention)
        embed.add_field(name="Motivo", value=f"```{self.motivo.value}```")
        
        await canal.send(embed=embed)
        await interaction.response.send_message(f"✅ Solicitação aberta em {canal.mention}", ephemeral=True)

class SetsView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Solicitar Sets", style=discord.ButtonStyle.primary, custom_id="btn_sets_cbm", emoji="💎")
    async def callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name=CARGOS["SETS"])
        if role not in interaction.user.roles:
            return await interaction.response.send_message("❌ Você não possui o cargo **Sets** necessário.", ephemeral=True)
        await interaction.response.send_modal(SetsModal())

# ================= BOT CORE =================

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(ArquivoView())
        self.add_view(RegistroView())
        self.add_view(SetsView())

    async def on_ready(self):
        print(f"🚀 {self.user} está online e operacional!")

bot = MyBot()

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_tudo(ctx):
    # Painel Arquivo
    emb_arq = discord.Embed(title="📂 Central de Arquivamento - CBM-RJ", description="Espaço destinado ao registro de ocorrências e avisos internos dos oficiais.", color=0x992d22)
    emb_arq.set_footer(text="Acesso exclusivo para CBM-RJ")
    
    # Painel Registro
    emb_reg = discord.Embed(title="📝 Registro de Cidadão", description="Seja bem-vindo ao servidor! Clique no botão abaixo para iniciar seu processo de registro.", color=0x2ecc71)
    
    # Painel Sets
    emb_set = discord.Embed(title="💎 Solicitação de Sets", description="Se você já possui o cargo Sets, clique abaixo para solicitar novos itens.", color=0x3498db)

    await ctx.send(embed=emb_arq, view=ArquivoView())
    await ctx.send(embed=emb_reg, view=RegistroView())
    await ctx.send(embed=emb_set, view=SetsView())

@bot.command()
async def arquivo(ctx):
    embed = discord.Embed(title="📂 Registro de Arquivos - CBM-RJ", color=0x992d22)
    await ctx.send(embed=embed, view=ArquivoView())

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ ERRO: Variável TOKEN_BOT não configurada no Railway!")
