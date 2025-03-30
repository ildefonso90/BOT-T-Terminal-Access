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
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.constants import ParseMode
import threading

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
LIMITE_CPU = 80  # Alerta quando CPU > 80%
LIMITE_RAM = 80  # Alerta quando RAM > 80%
LIMITE_DISCO = 85  # Alerta quando Disco > 85%
INTERVALO_MONITORAMENTO = 60  # Verificar a cada 60 segundos

# Cache para evitar consultas frequentes
cache = {
    "ultima_atualizacao": {},
    "dados": {}
}

# Cache para evitar alertas repetidos
alertas_enviados = {
    "cpu": False,
    "ram": False,
    "disco": False,
    "processos": set(),
    "usuarios": set()
}

async def verificar_autorizacao(update: Update) -> bool:
    """Verifica se o usuário está autorizado"""
    user = update.effective_user
    if user.username and user.username.lower() == DONO_USERNAME or user.id in IDS_AUTORIZADOS:
        return True
    await update.message.reply_text(
        "🚫 *Acesso Negado*\n"
        "Você não está autorizado a usar este bot\\.\n"
        "Entre em contato com o administrador\\.",
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
                resultado = stdout.decode()
                return resultado if resultado.strip() else "✅ Comando executado com sucesso"
            else:
                return f"❌ Erro:\n{stderr.decode()}"
        except asyncio.TimeoutError:
            processo.kill()
            return "⚠️ Comando excedeu o tempo limite"
            
    except Exception as e:
        return f"❌ Erro ao executar comando: {e}"

async def obter_status_sistema() -> str:
    """Obtém status detalhado do sistema"""
    try:
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_freq = psutil.cpu_freq()
        cpu_count = psutil.cpu_count()
        
        # Memória
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # Disco
        disk = psutil.disk_usage('/')
        
        # Uptime
        uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
        
        # Temperatura (se disponível)
        temp = ""
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                temp = f"\n🌡️ *Temperatura*:\n"
                for name, entries in temps.items():
                    for entry in entries:
                        temp += f"  • {entry.label or name}: {entry.current:.1f}°C\n"
        except:
            pass
        
        # Formata a mensagem
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
            f"{temp}"
        )
        
        return status
    except Exception as e:
        return f"❌ Erro ao obter status: {e}"

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
        
        # Ordena por uso de CPU
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
        
        return texto
    except Exception as e:
        return f"❌ Erro ao listar processos: {e}"

async def obter_info_rede() -> str:
    """Obtém informações detalhadas da rede"""
    try:
        # Interfaces
        interfaces = psutil.net_if_stats()
        io_counters = psutil.net_io_counters(pernic=True)
        
        texto = "🌐 *Informações de Rede*\n\n"
        
        # IP público
        try:
            ip_publico = await executar_comando("curl -s ifconfig.me")
            texto += f"🌍 *IP Público*: `{ip_publico.strip()}`\n\n"
        except:
            pass
        
        # Interfaces
        texto += "📡 *Interfaces*:\n\n"
        for nome, stats in interfaces.items():
            if nome != 'lo':  # Ignora loopback
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
        
        # Conexões ativas
        conns = psutil.net_connections()
        estabelecidas = len([c for c in conns if c.status == 'ESTABLISHED'])
        listening = len([c for c in conns if c.status == 'LISTEN'])
        
        texto += (
            "🔌 *Conexões*:\n"
            f"  • Estabelecidas: {estabelecidas}\n"
            f"  • Escutando: {listening}\n"
        )
        
        return texto
    except Exception as e:
        return f"❌ Erro ao obter informações de rede: {e}"

async def obter_servicos() -> str:
    """Obtém status dos principais serviços"""
    servicos = [
        "ssh", "apache2", "nginx", "mysql", "postgresql",
        "mongodb", "redis-server", "docker"
    ]
    
    texto = "🔧 *Status dos Serviços*\n\n"
    
    for servico in servicos:
        try:
            resultado = await executar_comando(f"systemctl is-active {servico}")
            status = "🟢 Ativo" if "active" in resultado else "🔴 Inativo"
            texto += f"• *{servico}*: {status}\n"
        except:
            pass
    
    return texto

async def obter_usuarios_sistema() -> str:
    """Obtém informações sobre usuários do sistema"""
    try:
        # Usuários logados
        users = psutil.users()
        
        texto = "👥 *Usuários do Sistema*\n\n"
        
        # Usuários logados
        texto += "*Sessões Ativas*:\n"
        for user in users:
            texto += (
                f"• *{user.name}*\n"
                f"  • Terminal: {user.terminal}\n"
                f"  • Host: {user.host}\n"
                f"  • Iniciado: {datetime.fromtimestamp(user.started).strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )
        
        # Últimos logins
        last_logins = await executar_comando("last -n 5")
        texto += f"\n*Últimos Logins*:\n```\n{last_logins[:500]}```"
        
        return texto
    except Exception as e:
        return f"❌ Erro ao obter informações de usuários: {e}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start - Menu principal"""
    if not await verificar_autorizacao(update):
        return
    
    # Cria o teclado inline
    keyboard = [
        [
            InlineKeyboardButton("📊 Sistema", callback_data=MENU_SISTEMA),
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
    
    # Envia mensagem de boas-vindas
    await update.message.reply_text(
        f"👋 Olá {update.effective_user.first_name}\\!\n\n"
        "🤖 *BOT\\-T\\-Terminal*\n"
        "Controle total do seu servidor\\.\n\n"
        "Escolha uma opção:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN_V2
    )

async def cmd_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /cmd - Executa comandos"""
    if not await verificar_autorizacao(update):
        return
    
    if not context.args:
        await update.message.reply_text(
            "ℹ️ *Como usar*:\n"
            "`/cmd comando`\n\n"
            "*Exemplos*:\n"
            "• `/cmd ls -la`\n"
            "• `/cmd df -h`\n"
            "• `/cmd free -m`\n"
            "• `/cmd ps aux`",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return
    
    comando = ' '.join(context.args)
    resultado = await executar_comando(comando)
    
    # Envia o resultado em partes se for muito grande
    if len(resultado) > 4000:
        partes = [resultado[i:i+4000] for i in range(0, len(resultado), 4000)]
        for parte in partes:
            await update.message.reply_text(
                f"```\n{parte}\n```",
                parse_mode=ParseMode.MARKDOWN_V2
            )
    else:
        await update.message.reply_text(
            f"```\n{resultado}\n```",
            parse_mode=ParseMode.MARKDOWN_V2
        )

def executar_speedtest():
    """Executa um teste de velocidade"""
    try:
        # Verifica se speedtest-cli está instalado
        try:
            import speedtest
        except ImportError:
            return "❌ Speedtest-cli não está instalado. Instale com:\n`pip install speedtest-cli`"
        
        # Executa o teste
        s = speedtest.Speedtest()
        s.get_best_server()
        s.download()
        s.upload()
        
        # Formata o resultado
        resultado = s.results.dict()
        
        # Formata a mensagem
        download = resultado["download"] / 1_000_000  # Mbps
        upload = resultado["upload"] / 1_000_000  # Mbps
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
        
        return texto
    except Exception as e:
        return f"❌ Erro ao executar speedtest: {e}"

# Função para monitoramento em background usando threads
def monitorar_sistema_thread(app: Application):
    """Função que roda em uma thread separada para monitorar o sistema"""
    logger.info("Iniciando monitoramento do sistema em thread separada")
    
    def enviar_alerta_sync(mensagem: str):
        """Versão síncrona da função de enviar alerta"""
        try:
            if IDS_AUTORIZADOS:
                app.bot.send_message(
                    chat_id=IDS_AUTORIZADOS[0],
                    text=mensagem,
                    parse_mode=ParseMode.MARKDOWN_V2
                )
        except Exception as e:
            logger.error(f"Erro ao enviar alerta: {e}")
    
    while True:
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > LIMITE_CPU and not alertas_enviados["cpu"]:
                enviar_alerta_sync(f"⚠️ *Alerta de CPU*\n\nUso de CPU está em {cpu_percent}%!")
                alertas_enviados["cpu"] = True
            elif cpu_percent < LIMITE_CPU:
                alertas_enviados["cpu"] = False
            
            # Memória
            mem = psutil.virtual_memory()
            if mem.percent > LIMITE_RAM and not alertas_enviados["ram"]:
                enviar_alerta_sync(f"⚠️ *Alerta de RAM*\n\nUso de RAM está em {mem.percent}%!")
                alertas_enviados["ram"] = True
            elif mem.percent < LIMITE_RAM:
                alertas_enviados["ram"] = False
            
            # Disco
            disk = psutil.disk_usage('/')
            if disk.percent > LIMITE_DISCO and not alertas_enviados["disco"]:
                enviar_alerta_sync(f"⚠️ *Alerta de Disco*\n\nUso de disco está em {disk.percent}%!")
                alertas_enviados["disco"] = True
            elif disk.percent < LIMITE_DISCO:
                alertas_enviados["disco"] = False
            
            # Processos consumindo muita RAM/CPU
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    pinfo = proc.info
                    if pinfo['cpu_percent'] > 50 or pinfo['memory_percent'] > 50:
                        proc_id = f"{pinfo['pid']}-{pinfo['name']}"
                        if proc_id not in alertas_enviados["processos"]:
                            enviar_alerta_sync(
                                f"⚠️ *Processo com Alto Consumo*\n\n"
                                f"Processo: {pinfo['name']}\n"
                                f"PID: {pinfo['pid']}\n"
                                f"CPU: {pinfo['cpu_percent']}%\n"
                                f"RAM: {pinfo['memory_percent']:.1f}%"
                            )
                            alertas_enviados["processos"].add(proc_id)
                except:
                    pass
            
            # Novos usuários conectados
            users = psutil.users()
            for user in users:
                user_id = f"{user.name}-{user.host}-{user.started}"
                if user_id not in alertas_enviados["usuarios"]:
                    # Obtém localização do IP
                    try:
                        import requests
                        response = requests.get(f"https://ipinfo.io/{user.host}/json")
                        ip_data = response.json()
                        localizacao = f"{ip_data.get('city', 'N/A')}, {ip_data.get('region', 'N/A')}, {ip_data.get('country', 'N/A')}"
                    except:
                        localizacao = "Não disponível"
                    
                    enviar_alerta_sync(
                        f"👤 *Novo Usuário Conectado*\n\n"
                        f"Usuário: {user.name}\n"
                        f"IP: {user.host}\n"
                        f"Localização: {localizacao}\n"
                        f"Terminal: {user.terminal}\n"
                        f"Hora: {datetime.fromtimestamp(user.started).strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    alertas_enviados["usuarios"].add(user_id)
            
            time.sleep(INTERVALO_MONITORAMENTO)
            
        except Exception as e:
            logger.error(f"Erro no monitoramento: {e}")
            time.sleep(INTERVALO_MONITORAMENTO)

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
            "💻 *Menu Sistema*\n"
            "Escolha uma opção:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN_V2
        )
    
    elif query.data == MENU_USUARIOS:
        keyboard = [
            [
                InlineKeyboardButton("👥 Listar Usuários", callback_data="usuarios_listar"),
                InlineKeyboardButton("🔑 Gerenciar SSH", callback_data="usuarios_ssh")
            ],
            [
                InlineKeyboardButton("➕ Adicionar", callback_data="usuarios_add"),
                InlineKeyboardButton("➖ Remover", callback_data="usuarios_del")
            ],
            [
                InlineKeyboardButton("⬅️ Voltar", callback_data=MENU_PRINCIPAL)
            ]
        ]
        await query.edit_message_text(
            "👥 *Menu Usuários*\n"
            "Escolha uma opção:",
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
                InlineKeyboardButton("▶️ Iniciar", callback_data="servicos_start"),
                InlineKeyboardButton("⏹️ Parar", callback_data="servicos_stop")
            ],
            [
                InlineKeyboardButton("⬅️ Voltar", callback_data=MENU_PRINCIPAL)
            ]
        ]
        await query.edit_message_text(
            "🔧 *Menu Serviços*\n"
            "Escolha uma opção:",
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
                InlineKeyboardButton("🔍 Scan", callback_data="seguranca_scan"),
                InlineKeyboardButton("📝 Logs", callback_data="seguranca_logs")
            ],
            [
                InlineKeyboardButton("⬅️ Voltar", callback_data=MENU_PRINCIPAL)
            ]
        ]
        await query.edit_message_text(
            "🔒 *Menu Segurança*\n"
            "Escolha uma opção:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN_V2
        )
    
    elif query.data == MENU_REDE:
        keyboard = [
            [
                InlineKeyboardButton("📊 Status", callback_data="rede_status"),
                InlineKeyboardButton("🔌 Conexões", callback_data="rede_conexoes")
            ],
            [
                InlineKeyboardButton("📡 Interfaces", callback_data="rede_interfaces"),
                InlineKeyboardButton("🚀 Speed Test", callback_data="rede_speedtest")
            ],
            [
                InlineKeyboardButton("⬅️ Voltar", callback_data=MENU_PRINCIPAL)
            ]
        ]
        await query.edit_message_text(
            "🌐 *Menu Rede*\n"
            "Escolha uma opção:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN_V2
        )
    
    elif query.data == MENU_LOGS:
        keyboard = [
            [
                InlineKeyboardButton("📝 Sistema", callback_data="logs_sistema"),
                InlineKeyboardButton("🔒 Segurança", callback_data="logs_seguranca")
            ],
            [
                InlineKeyboardButton("🌐 Apache/Nginx", callback_data="logs_web"),
                InlineKeyboardButton("📊 Aplicação", callback_data="logs_app")
            ],
            [
                InlineKeyboardButton("⬅️ Voltar", callback_data=MENU_PRINCIPAL)
            ]
        ]
        await query.edit_message_text(
            "📝 *Menu Logs*\n"
            "Escolha uma opção:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN_V2
        )
    
    elif query.data == "status":
        status = await obter_status_sistema()
        keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data=MENU_SISTEMA)]]
        await query.edit_message_text(
            status,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN_V2
        )
    
    elif query.data == "processos":
        processos = await obter_processos()
        keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data=MENU_SISTEMA)]]
        await query.edit_message_text(
            processos,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN_V2
        )
    
    elif query.data == "rede_status":
        info_rede = await obter_info_rede()
        keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data=MENU_REDE)]]
        await query.edit_message_text(
            info_rede,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN_V2
        )
    
    elif query.data == "servicos_status":
        servicos = await obter_servicos()
        keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data=MENU_SERVICOS)]]
        await query.edit_message_text(
            servicos,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN_V2
        )
    
    elif query.data == "usuarios_listar":
        usuarios = await obter_usuarios_sistema()
        keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data=MENU_USUARIOS)]]
        await query.edit_message_text(
            usuarios,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN_V2
        )
    
    elif query.data == MENU_PRINCIPAL:
        await start(update, context)
    
    elif query.data == "rede_speedtest":
        await query.edit_message_text(
            "🚀 *Speed Test*\n\n"
            "⏳ Iniciando teste de velocidade...\n"
            "Isso pode levar alguns segundos.",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        
        # Executa o teste
        resultado = executar_speedtest()
        
        # Mostra o resultado
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
                "❌ *Erro*\n"
                "Ocorreu um erro ao processar seu comando\\.\n"
                "O erro foi registrado e será analisado\\.",
                parse_mode=ParseMode.MARKDOWN_V2
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
        app.add_handler(CallbackQueryHandler(button_handler))
        app.add_error_handler(error_handler)
        
        # Iniciar thread de monitoramento
        monitoring_thread = threading.Thread(target=monitorar_sistema_thread, args=(app,), daemon=True)
        monitoring_thread.start()
        
        # Iniciar bot
        logger.info("🚀 Bot iniciado!")
        app.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Erro fatal: {e}")
        exit(1)

if __name__ == "__main__":
    main()