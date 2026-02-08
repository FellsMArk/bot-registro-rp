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

INTENTS = discord.Intents.default()
INTENTS.members = True
INTENTS.message_content = True

bot = commands.Bot(command_prefix="!", intents=INTENTS)

@bot.event
async def on_ready():
    # Registra as views para que os botões sejam persistentes (não morram no reboot)
    bot.add_view(RegistroView())
    bot.add_view(SetsView())
    bot.add_view(ArquivoView())
    print(f"✅ Sistema CBM-RJ espelhado e online como {bot.user}")

# ================= 📂 SISTEMA DE ARQUIVO (CBM-RJ) =================

class ArquivoModal(discord.ui.Modal, title="Registro de Arquivo"):
    id_ref = discord.ui.TextInput(label="ID", placeholder="ID do cidadão...")
    nome_cargo = discord.ui.TextInput(label="NOME/CARGO", placeholder="Nome e cargo do indivíduo...")
    ocorrencia_aviso = discord.ui.TextInput(label="OCORRÊNCIA/AVISO", style=discord.TextStyle.paragraph, placeholder="Descreva a ocorrência e o aviso aplicado...")
    obs = discord.ui.TextInput(label="OBSERVAÇÃO (Opcional)", required=False, placeholder="Algo a acrescentar?")
    provas = discord.ui.TextInput(label="PROVAS (Opcional)", required=False, placeholder="Links de imagens ou vídeos...")

    async def on_submit(self, interaction: discord.Interaction):
        canal = discord.utils.get(interaction.guild.text_channels, name=CANAL_LOG_ARQUIVO)
        if not canal:
            return await interaction.response.send_message(f"❌ Canal `{CANAL_LOG_ARQUIVO}` não encontrado.", ephemeral=True)

        embed = discord.Embed(title="🚨 NOVO REGISTRO DE ARQUIVO", color=0x992d22, timestamp=datetime.now())
        embed.add_field(name="🆔 ID", value=self.id_ref.value, inline=True)
        embed.add_field(name="👤 Nome/Cargo", value=self.nome_cargo.value, inline=True)
        embed.add_field(name="📝 Ocorrência/Aviso", value=f"```{self.ocorrencia_aviso.value}```", inline=False)
        
        if self.obs.value: embed.add_field(name="🔍 Observação", value=self.obs.value, inline=True)
        if self.provas.value: embed.add_field(name="📸 Provas", value=self.provas.value, inline=True)
        
        embed.set_footer(text=f"Oficial Responsável: {interaction.user.display_name}")

        await canal.send(embed=embed)
        await interaction.response.send_message("✅ Arquivo enviado com sucesso para a log!", ephemeral=True)

class ArquivoView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Registrar Arquivo", style=discord.ButtonStyle.danger, custom_id="btn_arq_v3", emoji="📂")
    async def abrir(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Somente quem tem a tag CBM-RJ pode usar
        role = discord.utils.get(interaction.guild.roles, name=CARGO_CBM)
        if role not in interaction.user.roles:
            return await interaction.response.send_message("❌ Acesso restrito a oficiais da **CBM-RJ**.", ephemeral=True)
        await interaction.response.send_modal(ArquivoModal())

# ================= 📝 SISTEMA DE REGISTRO (ID -> CEO -> CBM-RJ) =================

class RegistroModal(discord.ui.Modal, title="Registro de Cidadão"):
    id_cid = discord.ui.TextInput(label="ID da Cidade", placeholder="Informe o seu ID in-game")

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        staff_role = discord.utils.get(guild.roles, name=CARGO_CEO)
        cat = discord.utils.get(guild.categories, name=CATEGORIA_REGISTRO) or await guild.create_category(CATEGORIA_REGISTRO)
        
        # O membro não vê o canal, apenas o CEO e o Bot
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=False), 
            staff_role: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True)
        }

        canal = await guild.create_text_channel(f"registro-{interaction.user.name}", category=cat, overwrites=overwrites)
        
        embed = discord.Embed(title="📋 Solicitação de Registro", color=0x2ecc71)
        embed.add_field(name="Cidadão", value=interaction.user.mention, inline=True)
        embed.add_field(name="ID Informado", value=f"`{self.id_cid.value}`", inline=True)
        embed.set_footer(text="Aguardando aprovação do CEO")

        await canal.send(content=staff_role.mention, embed=embed, view=AprovacaoRegistro(interaction.user, self.id_cid.value))
        await interaction.response.send_message(f"✅ Seu pedido foi enviado para análise da Staff!", ephemeral=True)

class AprovacaoRegistro(discord.ui.View):
    def __init__(self, user, cid):
        super().__init__(timeout=None)
        self.user, self.cid = user, cid

    async def interaction_check(self, interaction: discord.Interaction):
        role = discord.utils.get(interaction.guild.roles, name=CARGO_CEO)
        if role not in interaction.user.roles:
            await interaction.response.send_message("❌ Apenas o **CEO** pode aprovar este registro.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Aprovar", style=discord.ButtonStyle.success, emoji="✅")
    async def aprovar(self, interaction: discord.Interaction, button: discord.ui.Button):
        membro = interaction.guild.get_member(self.user.id)
        cargo_cbm = discord.utils.get(interaction.guild.roles, name=CARGO_CBM)

        if membro and cargo_cbm:
            await membro.add_roles(cargo_cbm) # Adiciona a tag CBM-RJ
            try: await membro.edit(nick=f"{self.cid} | {membro.name}") # Altera o Nick
            except: pass
        
        log = discord.utils.get(interaction.guild.text_channels, name=CANAL_LOG_REGISTRO)
        if log: await log.send(f"✅ **Registro Aprovado:** {self.user.mention} (ID: {self.cid}) | Aprovado por: {interaction.user.mention}")
        await interaction.channel.delete()

    @discord.ui.button(label="Negar", style=discord.ButtonStyle.danger, emoji="❌")
    async def negar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.delete()

class RegistroView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Iniciar Registro", style=discord.ButtonStyle.success, custom_id="btn_reg_v3", emoji="📝")
    async def registrar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RegistroModal())

# ================= 💎 SISTEMA DE SETS (ID/MOTIVO + TRAVA) =================

class SetsModal(discord.ui.Modal, title="Solicitação de Sets"):
    id_alvo = discord.ui.TextInput(label="ID", placeholder="ID de quem receberá o set")
    motivo = discord.ui.TextInput(label="Motivo", style=discord.TextStyle.paragraph, placeholder="Descreva o motivo da solicitação...")

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
        embed.add_field(name="Solicitante", value=interaction.user.mention, inline=True)
        embed.add_field(name="ID Alvo", value=f"`{self.id_alvo.value}`", inline=True)
        embed.add_field(name="Motivo", value=f"```{self.motivo.value}```", inline=False)

        await canal.send(embed=embed, view=AprovacaoSets(interaction.user, self.id_alvo.value, self.motivo.value))
        await interaction.response.send_message(f"✅ Solicitação aberta em {canal.mention}", ephemeral=True)

class AprovacaoSets(discord.ui.View):
    def __init__(self, solicitante, uid, motivo):
        super().__init__(timeout=None)
        self.solicitante, self.uid, self.motivo = solicitante, uid, motivo

    async def interaction_check(self, interaction: discord.Interaction):
        role = discord.utils.get(interaction.guild.roles, name=CARGO_CEO)
        return role in interaction.user.roles

    @discord.ui.button(label="Concluir", style=discord.ButtonStyle.success, emoji="✅")
    async def concluir(self, interaction: discord.Interaction, button: discord.ui.Button):
        log = discord.utils.get(interaction.guild.text_channels, name=CANAL_LOG_SETS)
        if log: await log.send(f"💎 **Sets Entregue:** ID `{self.uid}` | Solicitado por: {self.solicitante.mention} | Staff: {interaction.user.mention}")
        await interaction.channel.delete()

    @discord.ui.button(label="Negar", style=discord.ButtonStyle.danger, emoji="❌")
    async def negar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.delete()

class SetsView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Abrir Solicitação", style=discord.ButtonStyle.primary, custom_id="btn_sets_v3", emoji="💎")
    async def abrir(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Trava: Só quem tem cargo Sets pode usar
        role = discord.utils.get(interaction.guild.roles, name=CARGO_SETS)
        if role not in interaction.user.roles:
            return await interaction.response.send_message("❌ Você não possui permissão para solicitar Sets.", ephemeral=True)
        await interaction.response.send_modal(SetsModal())

# ================= COMANDOS =================

@bot.command()
async def arquivo(ctx):
    embed = discord.Embed(title="📂 CENTRAL DE ARQUIVAMENTO CBM-RJ", description="Espaço para oficiais registrarem ocorrências e avisos.", color=0x992d22)
    await ctx.send(embed=embed, view=ArquivoView())

@bot.command()
async def painel_registro(ctx):
    embed = discord.Embed(title="📝 REGISTRO DE CIDADÃO", description="Clique abaixo para iniciar seu registro. Seu pedido será avaliado pelo CEO.", color=0x2ecc71)
    await ctx.send(embed=embed, view=RegistroView())

@bot.command()
async def painel_sets(ctx):
    embed = discord.Embed(title="💎 PAINEL DE SETS", description="Solicitações exclusivas para membros com cargo Sets.", color=0x3498db)
    await ctx.send(embed=embed, view=SetsView())

bot.run(TOKEN)
