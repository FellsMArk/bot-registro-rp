import discord
from discord.ext import commands
import os
from datetime import datetime

# ================= CONFIGURAÇÃO AMBIENTE =================
TOKEN = os.getenv("TOKEN_BOT")

# NOMES CORRIGIDOS: CBM-RJ
CARGOS = {
    "STAFF": "CEO",
    "REGISTRADO": "CBM-RJ", 
    "SETS": "Sets"
}

CANAIS_LOG = {
    "REGISTRO": "📑-log-registros",
    "SETS": "📄-log-painel",
    "ARQUIVO": "📃-log-avisos"
}

CATEGORIA_TICKETS = "📋 REGISTROS"

# ================= CLASSES DE INTERFACE =================

# --- SISTEMA DE ARQUIVO (EXCLUSIVO CBM-RJ) ---
class ArquivoModal(discord.ui.Modal, title="Registro de Arquivo CBM-RJ"):
    id_ref = discord.ui.TextInput(label="ID", placeholder="Ex: 102")
    nome = discord.ui.TextInput(label="NOME", placeholder="Nome completo...")
    cargo = discord.ui.TextInput(label="CARGO", placeholder="Cargo ocupado...")
    ocorrencia = discord.ui.TextInput(label="OCORRÊNCIA", style=discord.TextStyle.paragraph)
    aviso = discord.ui.TextInput(label="AVISO", placeholder="Tipo de aviso aplicado...")
    obs = discord.ui.TextInput(label="OBSERVAÇÃO", required=False)
    provas = discord.ui.TextInput(label="PROVAS", placeholder="Links de imagens/vídeos", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        canal = discord.utils.get(interaction.guild.text_channels, name=CANAIS_LOG["ARQUIVO"])
        if not canal:
            return await interaction.response.send_message(f"Canal {CANAIS_LOG['ARQUIVO']} não encontrado.", ephemeral=True)

        embed = discord.Embed(title="🚨 NOVO REGISTRO: CBM-RJ", color=discord.Color.red(), timestamp=datetime.now())
        embed.add_field(name="👮 Staff Responsável", value=interaction.user.mention, inline=False)
        embed.add_field(name="👤 Indivíduo", value=f"ID: {self.id_ref.value}\nNome: {self.nome.value}", inline=True)
        embed.add_field(name="💼 Cargo", value=self.cargo.value, inline=True)
        embed.add_field(name="📝 Ocorrência", value=self.ocorrencia.value, inline=False)
        embed.add_field(name
