#!/usr/bin/env python3
import os
import subprocess
import json
import psutil
import platform
import pwd
import signal
import time
import datetime
import asyncio
import logging
import re
import socket
import shutil
import glob
import threading
import requests
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Carregar configurações
try:
    with open('config.json', 'r') as f:
        CONFIG = json.load(f)
        TOKEN = CONFIG['token']
        DONO_USERNAME = CONFIG['dono_username'].lower()
        IDS_AUTORIZADOS = CONFIG['ids_autorizados']
except Exception as e:
    logger.error(f"Erro ao carregar configurações: {e}")
    exit(1)

# Constantes
MENU_PRINCIPAL = "menu_principal"
MENU_SISTEMA = "menu_sistema"
MENU_USUARIOS = "menu_usuarios"
MENU_SERVICOS = "menu_servicos"
MENU_SEGURANCA = "menu_seguranca"
MENU_REDE = "menu_rede"
MENU_LOGS = "menu_logs"

# Constantes para alertas
LIMITE_CPU = 80
LIMITE_RAM = 80
LIMITE_DISCO = 85
INTERVALO_MONITORAMENTO = 60

# Cache para evitar alertas repetidos
alertas_enviados = {
    "cpu": False,
    "ram": False,
    "disco": False,
    "processos": set(),
    "usuarios": set()
}

def escape_markdown(text: str) -> str:
    """Escapa caracteres especiais para Markdown V2"""
    if not isinstance(text, str):
        return str(text)
    chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in chars:
        text = text.replace(char, f"\\{char}")
    return text

async def verificar_autorizacao(update: Update) -> bool:
    """Verifica se o usuário está autorizado"""
    user = update.effective_user
    if user.username and user.username.lower() == DONO_USERNAME or user.id in IDS_AUTORIZADOS:
        return True
    await update.message.reply_text(
        escape_markdown("🚫 *Acesso Negado*\nVocê não está autorizado a usar este bot.\nEntre em contato com o administrador."),
        parse_mode=ParseMode.MARKDOWN_V2
    )
    return False

async def executar_comando(comando: str, timeout: int = 30) -> str:
    """Executa um comando com timeout"""
    try:
        processo = await asyncio.create_subprocess_shell(
            comando,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                processo.communicate(),
                timeout=timeout
            )
            
            if processo.returncode == 0:
                resultado = stdout.decode('utf-8', errors='replace')
                return resultado if resultado.strip() else "✅ Comando executado com sucesso"
            else:
                return f"❌ Erro:\n{stderr.decode('utf-8', errors='replace')}"
        except asyncio.TimeoutError:
            try:
                processo.kill()
            except:
                pass
            return "⚠️ Comando excedeu o tempo limite"
            
    except Exception as e:
        return f"❌ Erro ao executar comando: {e}"

async def obter_status_sistema() -> str:
    """Obtém status detalhado do sistema"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_freq = psutil.cpu_freq()
        cpu_count = psutil.cpu_count()
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        disk = psutil.disk_usage('/')
        uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
        
        status = (
            "🖥️ *Status do Sistema*\n\n"
            f"📊 *CPU*:\n"
            f"  • Uso: {cpu_percent}%\n"
            f"  • Frequência: {cpu_freq.current:.1f} MHz\n"
            f"  • Núcleos: {cpu_count}\n\n"
            f"🧠 *Memória*:\n"
            f"  • RAM Total: {mem.total/1024/1024/1024:.1f} GB\n"
            f"  • RAM Usada: {mem.used/1024/1024/1024:.1f} GB ({mem.percent}%)\n"
            f"  • Swap Usada: {swap.used/1024/1024/1024:.1f} GB ({swap.percent}%)\n\n"
            f"💾 *Disco*:\n"
            f"  • Total: {disk.total/1024/1024/1024:.1f} GB\n"
            f"  • Usado: {disk.used/1024/1024/1024:.1f} GB ({disk.percent}%)\n"
            f"  • Livre: {disk.free/1024/1024/1024:.1f} GB\n\n"
            f"⏰ *Uptime*: {uptime.days}d {uptime.seconds//3600}h {(uptime.seconds//60)%60}m"
        )
        
        return escape_markdown(status)
    except Exception as e:
        return escape_markdown(f"❌ Erro ao obter status: {e}")

async def obter_processos(limite: int = 10) -> str:
    """Obtém lista dos processos mais ativos"""
    try:
        processos = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status', 'username']):
            try:
                pinfo = proc.info
                pinfo['cpu_percent'] = proc.cpu_percent()
                processos.append(pinfo)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        processos.sort(key=lambda x: x['cpu_percent'], reverse=True)
        
        texto = "🔄 *Top Processos*\n\n"
        for proc in processos[:limite]:
            texto += (
                f"📌 *{proc['name'][:20]}*\n"
                f"  • PID: `{proc['pid']}`\n"
                f"  • CPU: {proc['cpu_percent']:.1f}%\n"
                f"  • RAM: {proc['memory_percent']:.1f}%\n"
                f"  • Status: {proc['status']}\n"
                f"  • Usuário: {proc['username']}\n\n"
            )
        
        return escape_markdown(texto)
    except Exception as e:
        return escape_markdown(f"❌ Erro ao listar processos: {e}")

async def obter_info_rede() -> str:
    """Obtém informações detalhadas da rede"""
    try:
        interfaces = psutil.net_if_stats()
        io_counters = psutil.net_io_counters(pernic=True)
        
        texto = "🌐 *Informações de Rede*\n\n"
        
        try:
            response = requests.get('https://api.ipify.org?format=json')
            ip_publico = response.json()['ip']
            texto += f"🌍 *IP Público*: `{ip_publico}`\n\n"
        except:
            pass
        
        texto += "📡 *Interfaces*:\n\n"
        for nome, stats in interfaces.items():
            if nome != 'lo':
                io = io_counters.get(nome, None)
                texto += (
                    f"*{nome}*:\n"
                    f"  • Status: {'🟢 Ativo' if stats.isup else '🔴 Inativo'}\n"
                    f"  • Velocidade: {stats.speed} Mbps\n"
                )
                if io:
                    texto += (
                        f"  • Download: {io.bytes_recv/1024/1024:.1f} MB\n"
                        f"  • Upload: {io.bytes_sent/1024/1024:.1f} MB\n"
                    )
                texto += "\n"
        
        conns = psutil.net_connections()
        estabelecidas = len([c for c in conns if c.status == 'ESTABLISHED'])
        listening = len([c for c in conns if c.status == 'LISTEN'])
        
        texto += (
            "🔌 *Conexões*:\n"
            f"  • Estabelecidas: {estabelecidas}\n"
            f"  • Escutando: {listening}\n"
        )
        
        return escape_markdown(texto)
    except Exception as e:
        return escape_markdown(f"❌ Erro ao obter informações de rede: {e}")

def executar_speedtest() -> str:
    """Executa um teste de velocidade"""
    try:
        import speedtest
        s = speedtest.Speedtest()
        s.get_best_server()
        s.download()
        s.upload()
        
        resultado = s.results.dict()
        download = resultado["download"] / 1_000_000
        upload = resultado["upload"] / 1_000_000
        ping = resultado["ping"]
        servidor = resultado["server"]["sponsor"]
        cidade = resultado["server"]["name"]
        
        texto = (
            "🚀 *Resultado do Speed Test*\n\n"
            f"⬇️ *Download*: `{download:.2f} Mbps`\n"
            f"⬆️ *Upload*: `{upload:.2f} Mbps`\n"
            f"🔄 *Ping*: `{ping:.0f} ms`\n"
            f"🌐 *Servidor*: `{servidor} ({cidade})`\n"
        )
        
        return escape_markdown(texto)
    except Exception as e:
        return escape_markdown(f"❌ Erro ao executar speedtest: {e}")

def monitorar_sistema_thread(app: Application):
    """Função que roda em uma thread separada para monitorar o sistema"""
    logger.info("Iniciando monitoramento do sistema em thread separada")
    
    def enviar_alerta_sync(mensagem: str):
        """Versão síncrona da função de enviar alerta"""
        try:
            if IDS_AUTORIZADOS:
                app.bot.send_message(
                    chat_id=IDS_AUTORIZADOS[0],
                    text=escape_markdown(mensagem),
                    parse_mode=ParseMode.MARKDOWN_V2
                )
        except Exception as e:
            logger.error(f"Erro ao enviar alerta: {e}")
    
    while True:
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > LIMITE_CPU and not alertas_enviados["cpu"]:
                enviar_alerta_sync(f"⚠️ *Alerta de CPU*\n\nUso de CPU está em {cpu_percent}%!")
                alertas_enviados["cpu"] = True
            elif cpu_percent < LIMITE_CPU:
                alertas_enviados["cpu"] = False
            
            mem = psutil.virtual_memory()
            if mem.percent > LIMITE_RAM and not alertas_enviados["ram"]:
                enviar_alerta_sync(f"⚠️ *Alerta de RAM*\n\nUso de RAM está em {mem.percent}%!")
                alertas_enviados["ram"] = True
            elif mem.percent < LIMITE_RAM:
                alertas_enviados["ram"] = False
            
            disk = psutil.disk_usage('/')
            if disk.percent > LIMITE_DISCO and not alertas_enviados["disco"]:
                enviar_alerta_sync(f"⚠️ *Alerta de Disco*\n\nUso de disco está em {disk.percent}%!")
                alertas_enviados["disco"] = True
            elif disk.percent < LIMITE_DISCO:
                alertas_enviados["disco"] = False
            
            time.sleep(INTERVALO_MONITORAMENTO)
            
        except Exception as e:
            logger.error(f"Erro no monitoramento: {e}")
            time.sleep(INTERVALO_MONITORAMENTO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start - Menu principal"""
    if not await verificar_autorizacao(update):
        return
    
    keyboard = [
        [
            InlineKeyboardButton("💻 Sistema", callback_data=MENU_SISTEMA),
            InlineKeyboardButton("👥 Usuários", callback_data=MENU_USUARIOS)
        ],
        [
            InlineKeyboardButton("🔧 Serviços", callback_data=MENU_SERVICOS),
            InlineKeyboardButton("🔒 Segurança", callback_data=MENU_SEGURANCA)
        ],
        [
            InlineKeyboardButton("🌐 Rede", callback_data=MENU_REDE),
            InlineKeyboardButton("📝 Logs", callback_data=MENU_LOGS)
        ]
    ]
    
    welcome_msg = escape_markdown(
        "🤖 *Bem-vindo ao BOT-T-Terminal*\n\n"
        "Controle e monitore seu servidor através deste bot.\n"
        "Escolha uma opção abaixo:"
    )
    
    await update.message.reply_text(
        welcome_msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN_V2
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para botões inline"""
    if not await verificar_autorizacao(update):
        return
    
    query = update.callback_query
    await query.answer()
    
    if query.data == MENU_SISTEMA:
        keyboard = [
            [
                InlineKeyboardButton("📊 Status", callback_data="status"),
                InlineKeyboardButton("🔄 Processos", callback_data="processos")
            ],
            [
                InlineKeyboardButton("💾 Disco", callback_data="disco"),
                InlineKeyboardButton("🧠 Memória", callback_data="memoria")
            ],
            [
                InlineKeyboardButton("⬅️ Voltar", callback_data=MENU_PRINCIPAL)
            ]
        ]
        await query.edit_message_text(
            escape_markdown("💻 *Menu Sistema*\nEscolha uma opção:"),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN_V2
        )
    
    elif query.data == MENU_USUARIOS:
        keyboard = [
            [
                InlineKeyboardButton("👥 Listar", callback_data="usuarios_listar"),
                InlineKeyboardButton("🔑 SSH", callback_data="usuarios_ssh")
            ],
            [
                InlineKeyboardButton("⬅️ Voltar", callback_data=MENU_PRINCIPAL)
            ]
        ]
        await query.edit_message_text(
            escape_markdown("👥 *Menu Usuários*\nEscolha uma opção:"),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN_V2
        )
    
    elif query.data == MENU_SERVICOS:
        keyboard = [
            [
                InlineKeyboardButton("📊 Status", callback_data="servicos_status"),
                InlineKeyboardButton("🔄 Reiniciar", callback_data="servicos_restart")
            ],
            [
                InlineKeyboardButton("⬅️ Voltar", callback_data=MENU_PRINCIPAL)
            ]
        ]
        await query.edit_message_text(
            escape_markdown("🔧 *Menu Serviços*\nEscolha uma opção:"),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN_V2
        )
    
    elif query.data == MENU_SEGURANCA:
        keyboard = [
            [
                InlineKeyboardButton("🔒 Firewall", callback_data="seguranca_firewall"),
                InlineKeyboardButton("🛡️ Fail2Ban", callback_data="seguranca_fail2ban")
            ],
            [
                InlineKeyboardButton("⬅️ Voltar", callback_data=MENU_PRINCIPAL)
            ]
        ]
        await query.edit_message_text(
            escape_markdown("🔒 *Menu Segurança*\nEscolha uma opção:"),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN_V2
        )
    
    elif query.data == MENU_REDE:
        keyboard = [
            [
                InlineKeyboardButton("📊 Status", callback_data="rede_status"),
                InlineKeyboardButton("🚀 Speed Test", callback_data="rede_speedtest")
            ],
            [
                InlineKeyboardButton("⬅️ Voltar", callback_data=MENU_PRINCIPAL)
            ]
        ]
        await query.edit_message_text(
            escape_markdown("🌐 *Menu Rede*\nEscolha uma opção:"),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN_V2
        )
    
    elif query.data == MENU_LOGS:
        keyboard = [
            [
                InlineKeyboardButton("🖥️ Sistema", callback_data="logs_sistema"),
                InlineKeyboardButton("🔒 Segurança", callback_data="logs_seguranca")
            ],
            [
                InlineKeyboardButton("⬅️ Voltar", callback_data=MENU_PRINCIPAL)
            ]
        ]
        await query.edit_message_text(
            escape_markdown("📝 *Menu Logs*\nEscolha uma opção:"),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN_V2
        )
    
    elif query.data == MENU_PRINCIPAL:
        keyboard = [
            [
                InlineKeyboardButton("💻 Sistema", callback_data=MENU_SISTEMA),
                InlineKeyboardButton("👥 Usuários", callback_data=MENU_USUARIOS)
            ],
            [
                InlineKeyboardButton("🔧 Serviços", callback_data=MENU_SERVICOS),
                InlineKeyboardButton("🔒 Segurança", callback_data=MENU_SEGURANCA)
            ],
            [
                InlineKeyboardButton("🌐 Rede", callback_data=MENU_REDE),
                InlineKeyboardButton("📝 Logs", callback_data=MENU_LOGS)
            ]
        ]
        await query.edit_message_text(
            escape_markdown("🤖 *Menu Principal*\nEscolha uma opção:"),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN_V2
        )
    
    elif query.data == "status":
        status_texto = await obter_status_sistema()
        keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data=MENU_SISTEMA)]]
        await query.edit_message_text(
            status_texto,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN_V2
        )
    
    elif query.data == "processos":
        processos_texto = await obter_processos()
        keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data=MENU_SISTEMA)]]
        await query.edit_message_text(
            processos_texto,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN_V2
        )
    
    elif query.data == "rede_status":
        rede_texto = await obter_info_rede()
        keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data=MENU_REDE)]]
        await query.edit_message_text(
            rede_texto,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN_V2
        )
    
    elif query.data == "rede_speedtest":
        await query.edit_message_text(
            escape_markdown("🚀 *Speed Test*\n\n⏳ Iniciando teste de velocidade...\nIsso pode levar alguns segundos."),
            parse_mode=ParseMode.MARKDOWN_V2
        )
        
        resultado = executar_speedtest()
        keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data=MENU_REDE)]]
        await query.edit_message_text(
            resultado,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN_V2
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Trata erros do bot"""
    logger.error(f"Erro: {context.error}")
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                escape_markdown("❌ *Erro*\nOcorreu um erro ao processar seu comando.\nO erro foi registrado e será analisado."),
                parse_mode=ParseMode.MARKDOWN_V2
            )
    except:
        pass

def main():
    """Função principal"""
    try:
        app = Application.builder().token(TOKEN).build()
        
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CallbackQueryHandler(button_handler))
        app.add_error_handler(error_handler)
        
        monitoring_thread = threading.Thread(target=monitorar_sistema_thread, args=(app,), daemon=True)
        monitoring_thread.start()
        
        logger.info("🚀 Bot iniciado!")
        app.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Erro fatal: {e}")
        exit(1)

if __name__ == "__main__":
    main()