#!/usr/bin/env python3
import os
import subprocess
import json
import psutil
import platform
import pwd
import signal
from datetime import datetime
from typing import List, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import logging
import asyncio

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def verificar_root():
    """Verifica se o script está sendo executado como root"""
    if os.geteuid() != 0:
        print("❌ Este bot precisa ser executado como root!")
        exit(1)

# Verificar privilégios root
verificar_root()

# Carregar configurações
try:
    with open('config.json', 'r') as f:
        CONFIG = json.load(f)
        TOKEN = CONFIG['token']
        DONO_USERNAME = CONFIG['dono_username'].lower()
        IDS_AUTORIZADOS = CONFIG['ids_autorizados']
except Exception as e:
    print(f"❌ Erro ao carregar configurações: {e}")
    print("⚠️ Execute o script de instalação (install.py) primeiro!")
    exit(1)

# Mapa para armazenar tentativas de acesso
tentativas_falhas = {}

def salvar_configuracoes():
    """Salva as configurações atualizadas no arquivo"""
    try:
        with open('config.json', 'w') as f:
            json.dump({
                'token': TOKEN,
                'dono_username': DONO_USERNAME,
                'ids_autorizados': IDS_AUTORIZADOS,
                'usuarios_bloqueados': USUARIOS_BLOQUEADOS,
                'tentativas_maximas': TENTATIVAS_MAXIMAS
            }, f, indent=4)
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar configurações: {e}")
        return False

async def verificar_autorizacao(update: Update) -> bool:
    """Verifica se o usuário está autorizado"""
    user = update.effective_user
    
    # Verifica se é o dono ou está na lista de autorizados
    if user.username and user.username.lower() == DONO_USERNAME or user.id in IDS_AUTORIZADOS:
        return True
    
    # Usuário não autorizado
    await update.message.reply_text(
        "❌ Você não está autorizado a usar este bot!\n"
        "🔑 Peça autorização ao administrador."
    )
    return False

def registrar_tentativa_falha(user_id: int):
    """Registra uma tentativa falha de acesso"""
    if user_id not in tentativas_falhas:
        tentativas_falhas[user_id] = 1
    else:
        tentativas_falhas[user_id] += 1
    
    # Bloquear após exceder tentativas
    if tentativas_falhas[user_id] >= TENTATIVAS_MAXIMAS:
        if user_id not in USUARIOS_BLOQUEADOS:
            USUARIOS_BLOQUEADOS.append(user_id)
            salvar_configuracoes()

async def executar_comando(comando: str) -> str:
    """Executa um comando no sistema"""
    try:
        processo = await asyncio.create_subprocess_shell(
            comando,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await processo.communicate()
        
        if processo.returncode == 0:
            resultado = stdout.decode()
            if not resultado.strip():
                return "✅ Comando executado com sucesso (sem saída)"
            return resultado
        else:
            erro = stderr.decode()
            return f"❌ Erro ao executar comando:\n{erro}"
            
    except Exception as e:
        return f"❌ Erro: {e}"

def verificar_comando_permitido(comando: str) -> bool:
    """Verifica se o comando é permitido"""
    comando_base = comando.split()[0]
    
    if comando_base in CONFIG.get("comandos_bloqueados", []):
        return False
        
    if CONFIG.get("comandos_permitidos"):
        return comando_base in CONFIG["comandos_permitidos"]
        
    return True

async def cmd_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /cmd"""
    if not await verificar_autorizacao(update):
        return
    
    # Verifica se foi enviado um comando
    if not context.args:
        await update.message.reply_text(
            "ℹ️ Use: /cmd <comando>\n"
            "📝 Exemplo: /cmd ls -la"
        )
        return
    
    # Executa o comando
    comando = ' '.join(context.args)
    resultado = await executar_comando(comando)
    
    # Envia o resultado em partes se for muito grande
    if len(resultado) > 4000:
        partes = [resultado[i:i+4000] for i in range(0, len(resultado), 4000)]
        for parte in partes:
            await update.message.reply_text(f"```\n{parte}\n```", parse_mode='MarkdownV2')
    else:
        await update.message.reply_text(f"```\n{resultado}\n```", parse_mode='MarkdownV2')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    if not await verificar_autorizacao(update):
        return
    
    # Cria o teclado inline
    keyboard = [
        [
            InlineKeyboardButton("💻 Status", callback_data="status"),
            InlineKeyboardButton("📊 Processos", callback_data="processos")
        ],
        [
            InlineKeyboardButton("🧠 Memória", callback_data="memoria"),
            InlineKeyboardButton("💾 Disco", callback_data="disco")
        ],
        [
            InlineKeyboardButton("🌐 Rede", callback_data="rede"),
            InlineKeyboardButton("❓ Ajuda", callback_data="ajuda")
        ]
    ]
    
    # Envia mensagem de boas-vindas
    await update.message.reply_text(
        f"👋 Olá {update.effective_user.first_name}!\n\n"
        "🤖 Bem-vindo ao BOT-T-Terminal\n"
        "🔧 Use /cmd para executar comandos\n"
        "📊 Ou use os botões abaixo:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para botões inline"""
    if not await verificar_autorizacao(update):
        return
    
    query = update.callback_query
    await query.answer()
    
    if query.data == "status":
        # Status do sistema
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        disco = psutil.disk_usage('/')
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        
        status = (
            "📊 Status do Sistema:\n\n"
            f"🔄 CPU: {cpu}%\n"
            f"🧠 RAM: {mem.percent}%\n"
            f"💾 Disco: {disco.percent}%\n"
            f"⏰ Uptime: {uptime.days}d {uptime.seconds//3600}h"
        )
        await query.edit_message_text(status)
    
    elif query.data == "processos":
        # Top 10 processos
        processos = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                pinfo = proc.info
                processos.append(pinfo)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Ordena por uso de CPU
        processos.sort(key=lambda x: x['cpu_percent'], reverse=True)
        
        texto = "📊 Top 10 Processos:\n\n"
        for proc in processos[:10]:
            texto += f"• {proc['name'][:15]:<15} "
            texto += f"CPU: {proc['cpu_percent']:>5.1f}% "
            texto += f"RAM: {proc['memory_percent']:>5.1f}%\n"
        
        await query.edit_message_text(texto)
    
    elif query.data == "memoria":
        # Informações de memória
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        texto = (
            "🧠 Memória:\n\n"
            f"RAM Total: {mem.total/1024/1024/1024:.1f} GB\n"
            f"RAM Usada: {mem.used/1024/1024/1024:.1f} GB ({mem.percent}%)\n"
            f"RAM Livre: {mem.free/1024/1024/1024:.1f} GB\n\n"
            f"Swap Total: {swap.total/1024/1024/1024:.1f} GB\n"
            f"Swap Usada: {swap.used/1024/1024/1024:.1f} GB ({swap.percent}%)\n"
            f"Swap Livre: {swap.free/1024/1024/1024:.1f} GB"
        )
        await query.edit_message_text(texto)
    
    elif query.data == "disco":
        # Uso do disco
        texto = "💾 Uso do Disco:\n\n"
        for part in psutil.disk_partitions():
            try:
                uso = psutil.disk_usage(part.mountpoint)
                texto += f"📁 {part.mountpoint}\n"
                texto += f"Total: {uso.total/1024/1024/1024:.1f} GB\n"
                texto += f"Usado: {uso.used/1024/1024/1024:.1f} GB ({uso.percent}%)\n"
                texto += f"Livre: {uso.free/1024/1024/1024:.1f} GB\n\n"
            except:
                pass
        await query.edit_message_text(texto)
    
    elif query.data == "rede":
        # Informações de rede
        texto = "🌐 Interfaces de Rede:\n\n"
        for nome, stats in psutil.net_if_stats().items():
            if stats.isup:
                texto += f"📡 {nome}\n"
                texto += f"Status: {'🟢 Ativo' if stats.isup else '🔴 Inativo'}\n"
                texto += f"Velocidade: {stats.speed} Mbps\n\n"
        await query.edit_message_text(texto)
    
    elif query.data == "ajuda":
        # Menu de ajuda
        texto = (
            "❓ Ajuda:\n\n"
            "🤖 Comandos disponíveis:\n\n"
            "/start - Menu principal\n"
            "/cmd - Executa comando\n"
            "  Ex: /cmd ls -la\n\n"
            "📊 Botões:\n"
            "• Status - CPU, RAM, Disco\n"
            "• Processos - Top 10 processos\n"
            "• Memória - RAM e Swap\n"
            "• Disco - Uso das partições\n"
            "• Rede - Interfaces de rede"
        )
        await query.edit_message_text(texto)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Trata erros do bot"""
    logger.error(f"Erro: {context.error}")
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Ocorreu um erro ao processar seu comando!\n"
                "🔄 Tente novamente mais tarde."
            )
    except:
        pass

def main():
    """Função principal"""
    try:
        # Criar aplicação
        app = Application.builder().token(TOKEN).build()
        
        # Adicionar handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("cmd", cmd_handler))
        
        # Handler para botões
        app.add_handler(CallbackQueryHandler(button_handler))
        
        # Handler de erros
        app.add_error_handler(error_handler)
        
        # Iniciar bot
        logger.info("🚀 Bot iniciado!")
        app.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        exit(1)

if __name__ == "__main__":
    main() 