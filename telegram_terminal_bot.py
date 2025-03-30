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
        USUARIOS_BLOQUEADOS = CONFIG.get('usuarios_bloqueados', [])
        TENTATIVAS_MAXIMAS = CONFIG.get('tentativas_maximas', 3)
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
    user_id = update.effective_user.id
    username = update.effective_user.username.lower() if update.effective_user.username else None

    # Verifica se é o dono ou está autorizado
    if username == DONO_USERNAME or user_id in IDS_AUTORIZADOS:
        return True

    logger.warning(f"Tentativa de acesso não autorizado - ID: {user_id}, Username: {username}")
    await update.message.reply_text("❌ Você não está autorizado!")
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
        
        if processo.returncode != 0 and stderr:
            return f"❌ Erro:\n{stderr.decode()}"
        
        resultado = stdout.decode()
        return resultado if resultado else "✅ Comando executado com sucesso!"
        
    except Exception as e:
        return f"❌ Erro: {str(e)}"

def verificar_comando_permitido(comando: str) -> bool:
    """Verifica se o comando é permitido"""
    comando_base = comando.split()[0]
    
    if comando_base in CONFIG.get("comandos_bloqueados", []):
        return False
        
    if CONFIG.get("comandos_permitidos"):
        return comando_base in CONFIG["comandos_permitidos"]
        
    return True

async def cmd_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Executa comandos no servidor"""
    if not await verificar_autorizacao(update):
        return

    if not context.args:
        await update.message.reply_text(
            "ℹ️ Use: /cmd <comando>\n"
            "Exemplo: /cmd ls -la"
        )
        return

    comando = " ".join(context.args)
    
    if not verificar_comando_permitido(comando):
        await update.message.reply_text("❌ Comando não permitido!")
        return

    resultado = await executar_comando(comando)
    
    # Divide a resposta se for muito grande
    if len(resultado) > 4000:
        partes = [resultado[i:i+4000] for i in range(0, len(resultado), 4000)]
        for parte in partes:
            await update.message.reply_text(f"```\n{parte}\n```", parse_mode="MarkdownV2")
    else:
        await update.message.reply_text(f"```\n{resultado}\n```", parse_mode="MarkdownV2")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    if not await verificar_autorizacao(update):
        return

    keyboard = [
        [
            InlineKeyboardButton("📊 Status", callback_data="status"),
            InlineKeyboardButton("💾 Memória", callback_data="memoria")
        ],
        [
            InlineKeyboardButton("💿 Disco", callback_data="disco"),
            InlineKeyboardButton("🌐 Rede", callback_data="rede")
        ],
        [
            InlineKeyboardButton("📝 Processos", callback_data="processos"),
            InlineKeyboardButton("ℹ️ Ajuda", callback_data="ajuda")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🤖 *BOT\\-T\\-Terminal*\n"
        "Controle remoto do servidor via Telegram\n\n"
        "Escolha uma opção:",
        reply_markup=reply_markup,
        parse_mode="MarkdownV2"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manipula callbacks dos botões"""
    if not await verificar_autorizacao(update):
        return

    query = update.callback_query
    await query.answer()

    if query.data == "status":
        # Informações do sistema
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        disco = psutil.disk_usage('/')
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time

        status = (
            "📊 *Status do Servidor*\n\n"
            f"CPU: {cpu}%\n"
            f"RAM: {mem.percent}%\n"
            f"Disco: {disco.percent}%\n"
            f"Uptime: {uptime.days}d {uptime.seconds//3600}h"
        )
        
        await query.edit_message_text(
            text=status,
            parse_mode="MarkdownV2"
        )

    elif query.data == "memoria":
        # Informações de memória
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        memoria = (
            "💾 *Memória*\n\n"
            f"RAM Total: {mem.total/1024/1024/1024:.1f}GB\n"
            f"RAM Usada: {mem.used/1024/1024/1024:.1f}GB\n"
            f"RAM Livre: {mem.free/1024/1024/1024:.1f}GB\n"
            f"RAM Cache: {mem.cached/1024/1024/1024:.1f}GB\n\n"
            f"Swap Total: {swap.total/1024/1024/1024:.1f}GB\n"
            f"Swap Usada: {swap.used/1024/1024/1024:.1f}GB\n"
            f"Swap Livre: {swap.free/1024/1024/1024:.1f}GB"
        )

        await query.edit_message_text(
            text=memoria,
            parse_mode="MarkdownV2"
        )

    elif query.data == "disco":
        # Informações de disco
        discos = []
        for particao in psutil.disk_partitions():
            try:
                uso = psutil.disk_usage(particao.mountpoint)
                discos.append(
                    f"📁 {particao.mountpoint}\n"
                    f"Total: {uso.total/1024/1024/1024:.1f}GB\n"
                    f"Usado: {uso.used/1024/1024/1024:.1f}GB\n"
                    f"Livre: {uso.free/1024/1024/1024:.1f}GB\n"
                    f"Uso: {uso.percent}%\n"
                )
            except:
                continue

        await query.edit_message_text(
            text="💿 *Discos*\n\n" + "\n".join(discos),
            parse_mode="MarkdownV2"
        )

    elif query.data == "rede":
        # Informações de rede
        rede = psutil.net_io_counters()
        
        info_rede = (
            "🌐 *Rede*\n\n"
            f"Download: {rede.bytes_recv/1024/1024:.1f}MB\n"
            f"Upload: {rede.bytes_sent/1024/1024:.1f}MB\n"
            f"Pacotes Recebidos: {rede.packets_recv}\n"
            f"Pacotes Enviados: {rede.packets_sent}\n"
            f"Erros (IN): {rede.errin}\n"
            f"Erros (OUT): {rede.errout}"
        )

        await query.edit_message_text(
            text=info_rede,
            parse_mode="MarkdownV2"
        )

    elif query.data == "processos":
        # Lista de processos
        processos = []
        for proc in sorted(
            psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']),
            key=lambda p: p.info['cpu_percent'],
            reverse=True
        )[:10]:
            try:
                processos.append(
                    f"PID: {proc.info['pid']}\n"
                    f"Nome: {proc.info['name']}\n"
                    f"CPU: {proc.info['cpu_percent']}%\n"
                    f"RAM: {proc.info['memory_percent']:.1f}%\n"
                )
            except:
                continue

        await query.edit_message_text(
            text="📝 *Top 10 Processos*\n\n" + "\n".join(processos),
            parse_mode="MarkdownV2"
        )

    elif query.data == "ajuda":
        ajuda = (
            "ℹ️ *Comandos Disponíveis*\n\n"
            "/start \\- Menu principal\n"
            "/cmd \\- Executa comando\n"
            "Exemplo: `/cmd ls -la`\n\n"
            "Use /cmd seguido do comando que deseja executar\\.\n"
            "O bot tem acesso root ao sistema\\."
        )

        await query.edit_message_text(
            text=ajuda,
            parse_mode="MarkdownV2"
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Trata erros do bot"""
    print(f"Erro: {context.error}")
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                f"❌ Ocorreu um erro: {context.error}"
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