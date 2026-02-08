import discord
from discord.ext import commands
import os
from datetime import datetime

# CONFIGURAÇÃO DE AMBIENTE - Prioriza a variável do Railway
TOKEN = os.getenv("TOKEN_BOT") or "MTQ2OTI5NTA5Njg3MTc4MDQ2NQ.GHwnfC.COl0LdJ0bCuH2xLT_4WmPDK2nHHO9uMa0ytR1o"

# IDENTIDADE DO SERVIDOR (Ajuste conforme os nomes exatos no seu Discord)
CARGO_CEO = "CEO"
CARGO_CBM = "CBM-RJ"
CARGO_SETS = "Sets"

# CANAIS DE LOG (Nomes idênticos aos do seu servidor)
LOGS = {
    "REGISTRO": "📑-log-registros",
    "SETS": "📄-log-painel",
    "ARQUIVO": "📃-log-avisos"
}
CATEGORIA_TICKETS = "📋 REGISTROS"

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Garante que os botões voltem a funcionar após o bot reiniciar no Railway
        self.add_view(RegistroView())
        self.add_view(SetsView())
        self.add_view(ArquivoView())

    async def on_ready(self):
        print(f"✅ {self.user} está operacional no Railway!")

bot = MyBot()

# ================= 📂 SISTEMA DE ARQUIVO (CBM-RJ) =================

class ArquivoModal(discord.ui.Modal, title="📝 Registro de Arquivo CBM-RJ"):
    id_ref = discord.ui.TextInput(label="ID", placeholder="Ex: 102")
    nome_cargo = discord.ui.TextInput(label="NOME / CARGO", placeholder="Ex: João / Sargento")
    ocorrencia_aviso = discord.ui.TextInput(label="OCORRÊNCIA / AVISO", style=discord.TextStyle.paragraph)
    obs = discord.ui.TextInput(label="OBSERVAÇÃO (OPCIONAL)", required=False)
    provas = discord.ui.TextInput(label="PROVAS (OPCIONAL)", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        canal = discord.utils.get(interaction.guild.text_channels, name=LOGS["ARQUIVO"])
        if not canal:
            return await interaction.response.send_message("❌ Canal de logs não encontrado.", ephemeral=True)

        embed = discord.Embed(title="🚨 REGISTRO DE ARQUIVO", color=0x992d22, timestamp=datetime.now())
        embed.add_field(name="🆔 ID", value=self.id_ref.value, inline=True)
        embed.add_field(name="👤 Nome/Cargo", value=self.nome_cargo.value, inline=True)
        embed.add_field(name="📜 Ocorrência & Aviso", value=f"```{self.ocorrencia_aviso.value}```", inline=False)
        if self.obs.value: embed.add_field(name="🔍 Obs", value=self.obs.value, inline=True)
        if self.provas.value: embed.add_field(name="📸 Provas", value=self.provas.value, inline=True)
        embed.set_footer(text=f"Por: {interaction.user.display_name}")

        await canal.send(embed=embed)
        await interaction.response.send_message("✅ Arquivo registrado com sucesso!", ephemeral=True)

class ArquivoView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Registrar Arquivo", style=discord.ButtonStyle.danger, custom_id="bt_arq", emoji="📂")
    async def callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if discord.utils.get(interaction.guild.roles, name=CARGO_CBM) not in interaction.user.roles:
            return await interaction.response.send_message("❌ Apenas **CBM-RJ**!", ephemeral=True)
        await interaction.response.send_modal(ArquivoModal())

# ================= 📝 SISTEMA DE REGISTRO (Membro -> CEO) =================

class RegistroModal(discord.ui.Modal, title="Registro de Cidadão"):
    id_cid = discord.ui.TextInput(label="Informe seu ID", placeholder="ID in-game...")

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        ceo_role = discord.utils.get(guild.roles, name=CARGO_CEO)
        cat = discord.utils.get(guild.categories, name=CATEGORIA_TICKETS) or await guild.create_category(CATEGORIA_TICKETS)
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            ceo_role: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            interaction.user: discord.PermissionOverwrite(view_channel=False) # Só Staff vê o canal de avaliação
        }
        canal = await guild.create_text_channel(f"registro-{interaction.user.name}", category=cat, overwrites=overwrites)
        
        embed = discord.Embed(title="📋 Novo Pedido de Registro", color=0x2ecc71)
        embed.add_field(name="Usuário", value=interaction.user.mention)
        embed.add_field(name="ID", value=f"`{self.id_cid.value}`")

        await canal.send(content=ceo_role.mention, embed=embed, view=AprovacaoRegistro(interaction.user, self.id_cid.value))
        await interaction.response.send_message("✅ Seu pedido foi enviado para análise do CEO!", ephemeral=True)

class AprovacaoRegistro(discord.ui.View):
    def __init__(self, user, cid):
        super().__init__(timeout=None)
        self.user, self.cid = user, cid

    @discord.ui.button(label="Aprovar", style=discord.ButtonStyle.success, emoji="✅")
    async def aprovar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if discord.utils.get(interaction.guild.roles, name=CARGO_CEO) not in interaction.user.roles:
            return await interaction.response.send_message("❌ Apenas o **CEO** aprova.", ephemeral=True)

        membro = interaction.guild.get_member(self.user.id)
        cargo_cbm = discord.utils.get(interaction.guild.roles, name=CARGO_CBM)
        if membro and cargo_cbm:
            await membro.add_roles(cargo_cbm)
            try: await membro.edit(nick=f"{self.cid} | {membro.name}")
            except: pass
        
        log = discord.utils.get(interaction.guild.text_channels, name=LOGS["REGISTRO"])
        if log: await log.send(f"✅ **Aprovado:** {self.user.mention} por {interaction.user.mention}")
        await interaction.channel.delete()

# ================= 💎 SISTEMA DE SETS (Trava de Cargo) =================

class SetsModal(discord.ui.Modal, title="Solicitação de Sets"):
    uid = discord.ui.TextInput(label="ID do Alvo")
    motivo = discord.ui.TextInput(label="Motivo / Itens", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        cat = discord.utils.get(guild.categories, name=CATEGORIA_TICKETS)
        canal = await guild.create_text_channel(f"sets-{interaction.user.name}", category=cat)
        
        embed = discord.Embed(title="💎 Solicitação de Sets", color=0x3498db)
        embed.add_field(name="ID", value=self.uid.value)
        embed.add_field(name="Motivo", value=self.motivo.value)
        
        await canal.send(embed=embed, view=AprovacaoGeral())
        await interaction.response.send_message("✅ Solicitação aberta!", ephemeral=True)

class AprovacaoGeral(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Concluir/Fechar", style=discord.ButtonStyle.secondary)
    async def fechar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.delete()

class RegistroView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Iniciar Registro", style=discord.ButtonStyle.success, custom_id="bt_reg", emoji="📝")
    async def registrar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RegistroModal())

class SetsView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Solicitar Sets", style=discord.ButtonStyle.primary, custom_id="bt_set", emoji="💎")
    async def abrir(self, interaction: discord.Interaction, button: discord.ui.Button):
        if discord.utils.get(interaction.guild.roles, name=CARGO_SETS) not in interaction.user.roles:
            return await interaction.response.send_message("❌ Você não tem o cargo **Sets**.", ephemeral=True)
        await interaction.response.send_modal(SetsModal())

# ================= COMANDOS =================

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_painel(ctx):
    # Envia todos os painéis com design limpo
    await ctx.send(embed=discord.Embed(title="📂 ARQUIVAMENTO CBM-RJ", color=0x992d22), view=ArquivoView())
    await ctx.send(embed=discord.Embed(title="📝 REGISTRO DE CIDADÃO", color=0x2ecc71), view=RegistroView())
    await ctx.send(embed=discord.Embed(title="💎 SOLICITAÇÃO DE SETS", color=0x3498db), view=SetsView())

bot.run(TOKEN)
