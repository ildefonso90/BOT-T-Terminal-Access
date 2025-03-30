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
        config = json.load(f)
        TOKEN = config['token']
        DONO_USERNAME = config['dono_username'].lower()
        IDS_AUTORIZADOS = config['ids_autorizados']
        USUARIOS_BLOQUEADOS = config.get('usuarios_bloqueados', [])
        TENTATIVAS_MAXIMAS = config.get('tentativas_maximas', 3)
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

def verificar_autorizacao(user_id: int, username: str = None) -> bool:
    """Verifica se o usuário está autorizado"""
    # Verificar se está bloqueado
    if user_id in USUARIOS_BLOQUEADOS:
        return False
    
    # Verificar se é o dono
    if username and username.lower() == DONO_USERNAME:
        return True
    
    # Verificar se está autorizado
    return user_id in IDS_AUTORIZADOS

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

def executar_comando(comando: str) -> tuple:
    """Executa um comando e retorna (sucesso, saída)"""
    try:
        processo = subprocess.Popen(
            comando,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        try:
            stdout, stderr = processo.communicate(timeout=30)
            sucesso = processo.returncode == 0
            saida = stdout if sucesso else stderr
            return sucesso, saida.strip()
        except subprocess.TimeoutExpired:
            processo.kill()
            return False, "⚠️ Comando excedeu o tempo limite de 30 segundos"
            
    except Exception as e:
        return False, f"❌ Erro ao executar comando: {str(e)}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start - Mostra menu principal"""
    user = update.effective_user
    user_id = user.id
    username = user.username

    if not username:
        await update.message.reply_text(
            "❌ Você precisa ter um username configurado no Telegram para usar este bot."
        )
        return

    # Verificar autorização
    if not verificar_autorizacao(user_id, username):
        registrar_tentativa_falha(user_id)
        
        if user_id in USUARIOS_BLOQUEADOS:
            await update.message.reply_text(
                "🚫 Você está bloqueado! Entre em contato com o administrador."
            )
        else:
            tentativas = tentativas_falhas.get(user_id, 0)
            await update.message.reply_text(
                f"❌ Acesso não autorizado!\n"
                f"Tentativas restantes: {TENTATIVAS_MAXIMAS - tentativas}"
            )
        return

    # Obter informações do sistema
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        status = f"""
🤖 *BOT-T-Terminal*

*Sistema:*
• OS: {platform.system()} {platform.release()}
• CPU: {cpu_percent}%
• RAM: {mem.percent}%
• Disco: {disk.percent}%
• Uptime: {datetime.now() - datetime.fromtimestamp(psutil.boot_time())}

*Usuário:*
• Nome: {user.first_name}
• Username: @{username}
• ID: `{user_id}`
• Tipo: {"👑 Dono" if username.lower() == DONO_USERNAME else "👤 Autorizado"}

*Comandos:*
/cmd - Executar comando
/status - Ver status detalhado
/processos - Listar processos
/memoria - Ver uso de memória
/disco - Ver uso do disco
/rede - Ver informações de rede
/ajuda - Mostrar ajuda

⚠️ Este bot tem acesso root ao servidor.
Use com responsabilidade!
"""
        
        # Botões inline
        keyboard = [
            [
                InlineKeyboardButton("📊 Status", callback_data="status"),
                InlineKeyboardButton("💾 Memória", callback_data="memoria")
            ],
            [
                InlineKeyboardButton("💽 Disco", callback_data="disco"),
                InlineKeyboardButton("🌐 Rede", callback_data="rede")
            ],
            [
                InlineKeyboardButton("📋 Processos", callback_data="processos"),
                InlineKeyboardButton("❓ Ajuda", callback_data="ajuda")
            ]
        ]
        
        await update.message.reply_text(
            status,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Erro ao obter status: {e}")

async def cmd_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Executa comandos enviados via /cmd"""
    user = update.effective_user
    
    if not verificar_autorizacao(user.id, user.username):
        await update.message.reply_text("❌ Você não está autorizado!")
        return
    
    # Obter comando após /cmd
    comando = update.message.text.split(' ', 1)
    if len(comando) < 2:
        await update.message.reply_text("⚠️ Use: /cmd <comando>")
        return
        
    comando = comando[1]
    
    # Executar comando
    sucesso, saida = executar_comando(comando)
    
    if not saida:
        saida = "✅ Comando executado (sem saída)"
    
    # Formatar resposta
    resposta = f"✅ Resultado:" if sucesso else "❌ Erro:"
    resposta += f"\n```\n{saida[:3900]}\n```"  # Limite Telegram
    
    await update.message.reply_text(
        resposta,
        parse_mode='Markdown'
    )

async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra status detalhado do sistema"""
    if not verificar_autorizacao(update.effective_user.id):
        await update.message.reply_text("❌ Você não está autorizado!")
        return
        
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
        
        # Sistema
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        
        status = f"""
📊 *Status do Sistema*

*CPU:*
• Uso: {cpu_percent}%
• Cores: {cpu_count}
• Freq: {cpu_freq.current:.1f} MHz
• Min: {cpu_freq.min:.1f} MHz
• Max: {cpu_freq.max:.1f} MHz

*Memória RAM:*
• Total: {mem.total / (1024**3):.1f} GB
• Usada: {mem.used / (1024**3):.1f} GB
• Livre: {mem.free / (1024**3):.1f} GB
• Uso: {mem.percent}%

*Swap:*
• Total: {swap.total / (1024**3):.1f} GB
• Usada: {swap.used / (1024**3):.1f} GB
• Livre: {swap.free / (1024**3):.1f} GB
• Uso: {swap.percent}%

*Disco:*
• Total: {disk.total / (1024**3):.1f} GB
• Usado: {disk.used / (1024**3):.1f} GB
• Livre: {disk.free / (1024**3):.1f} GB
• Uso: {disk.percent}%

*Sistema:*
• OS: {platform.system()} {platform.release()}
• Python: {platform.python_version()}
• Boot: {boot_time.strftime('%Y-%m-%d %H:%M:%S')}
• Uptime: {uptime}
"""
        
        await update.message.reply_text(
            status,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Erro ao obter status: {e}")

async def processos_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lista os processos do sistema"""
    if not verificar_autorizacao(update.effective_user.id):
        await update.message.reply_text("❌ Você não está autorizado!")
        return
        
    try:
        processos = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                pinfo = proc.info
                processos.append((
                    pinfo['cpu_percent'],
                    pinfo['memory_percent'],
                    pinfo['pid'],
                    pinfo['name']
                ))
            except:
                pass
                
        # Ordenar por CPU
        processos.sort(reverse=True)
        
        # Pegar top 10
        resposta = "📋 *Top 10 Processos:*\n\n"
        for cpu, mem, pid, name in processos[:10]:
            resposta += f"• {name} (PID: {pid})\n"
            resposta += f"  CPU: {cpu:.1f}% | RAM: {mem:.1f}%\n\n"
            
        await update.message.reply_text(
            resposta,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Erro ao listar processos: {e}")

async def memoria_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra uso detalhado de memória"""
    if not verificar_autorizacao(update.effective_user.id):
        await update.message.reply_text("❌ Você não está autorizado!")
        return
        
    try:
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        resposta = f"""
💾 *Uso de Memória*

*RAM:*
• Total: {mem.total / (1024**3):.1f} GB
• Disponível: {mem.available / (1024**3):.1f} GB
• Usada: {mem.used / (1024**3):.1f} GB
• Livre: {mem.free / (1024**3):.1f} GB
• Buffers: {mem.buffers / (1024**3):.1f} GB
• Cache: {mem.cached / (1024**3):.1f} GB
• Uso: {mem.percent}%

*Swap:*
• Total: {swap.total / (1024**3):.1f} GB
• Usada: {swap.used / (1024**3):.1f} GB
• Livre: {swap.free / (1024**3):.1f} GB
• Uso: {swap.percent}%
"""
        
        await update.message.reply_text(
            resposta,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Erro ao obter informações de memória: {e}")

async def disco_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra uso detalhado do disco"""
    if not verificar_autorizacao(update.effective_user.id):
        await update.message.reply_text("❌ Você não está autorizado!")
        return
        
    try:
        resposta = "💽 *Uso de Disco*\n\n"
        
        for particao in psutil.disk_partitions():
            try:
                uso = psutil.disk_usage(particao.mountpoint)
                resposta += f"*{particao.mountpoint}:*\n"
                resposta += f"• Device: {particao.device}\n"
                resposta += f"• Total: {uso.total / (1024**3):.1f} GB\n"
                resposta += f"• Usado: {uso.used / (1024**3):.1f} GB\n"
                resposta += f"• Livre: {uso.free / (1024**3):.1f} GB\n"
                resposta += f"• Uso: {uso.percent}%\n"
                resposta += f"• Tipo: {particao.fstype}\n\n"
            except:
                pass
                
        await update.message.reply_text(
            resposta,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Erro ao obter informações de disco: {e}")

async def rede_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra informações de rede"""
    if not verificar_autorizacao(update.effective_user.id):
        await update.message.reply_text("❌ Você não está autorizado!")
        return
        
    try:
        # Interfaces
        interfaces = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        io = psutil.net_io_counters(pernic=True)
        
        resposta = "🌐 *Informações de Rede*\n\n"
        
        for interface, addrs in interfaces.items():
            if interface in stats:
                stat = stats[interface]
                resposta += f"*{interface}:*\n"
                
                # Endereços
                for addr in addrs:
                    familia = {
                        psutil.AF_INET: "IPv4",
                        psutil.AF_INET6: "IPv6",
                        psutil.AF_PACKET: "MAC"
                    }.get(addr.family, addr.family)
                    
                    resposta += f"• {familia}: {addr.address}\n"
                
                # Status
                resposta += f"• Ativo: {'✅' if stat.isup else '❌'}\n"
                resposta += f"• MTU: {stat.mtu}\n"
                
                # I/O
                if interface in io:
                    net_io = io[interface]
                    resposta += f"• Download: {net_io.bytes_recv / (1024**2):.1f} MB\n"
                    resposta += f"• Upload: {net_io.bytes_sent / (1024**2):.1f} MB\n"
                    
                resposta += "\n"
                
        await update.message.reply_text(
            resposta,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Erro ao obter informações de rede: {e}")

async def ajuda_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra mensagem de ajuda"""
    if not verificar_autorizacao(update.effective_user.id):
        await update.message.reply_text("❌ Você não está autorizado!")
        return
        
    ajuda = """
❓ *Ajuda do BOT-T-Terminal*

*Comandos Disponíveis:*

📌 *Básicos:*
• /start - Menu principal
• /ajuda - Mostra esta mensagem
• /status - Status detalhado

🛠️ *Sistema:*
• /cmd <comando> - Executa comando
• /processos - Lista processos
• /memoria - Uso de memória
• /disco - Uso do disco
• /rede - Info de rede

⚠️ *Observações:*
• Todos os comandos são executados como root
• Comandos têm timeout de 30 segundos
• Use com responsabilidade!

*Exemplos:*
• Ver arquivos: `/cmd ls -la`
• Processos: `/cmd ps aux`
• Memória: `/cmd free -h`
• Rede: `/cmd netstat -tuln`
• Sistema: `/cmd uname -a`

*Segurança:*
• Apenas usuários autorizados têm acesso
• {TENTATIVAS_MAXIMAS} tentativas = bloqueio
• Somente o dono pode desbloquear
"""
    
    await update.message.reply_text(
        ajuda,
        parse_mode='Markdown'
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa botões inline"""
    query = update.callback_query
    await query.answer()
    
    if not verificar_autorizacao(query.from_user.id):
        await query.message.reply_text("❌ Você não está autorizado!")
        return
        
    comando = query.data
    
    if comando == "status":
        await status_handler(update, context)
    elif comando == "processos":
        await processos_handler(update, context)
    elif comando == "memoria":
        await memoria_handler(update, context)
    elif comando == "disco":
        await disco_handler(update, context)
    elif comando == "rede":
        await rede_handler(update, context)
    elif comando == "ajuda":
        await ajuda_handler(update, context)

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
        app.add_handler(CommandHandler("status", status_handler))
        app.add_handler(CommandHandler("processos", processos_handler))
        app.add_handler(CommandHandler("memoria", memoria_handler))
        app.add_handler(CommandHandler("disco", disco_handler))
        app.add_handler(CommandHandler("rede", rede_handler))
        app.add_handler(CommandHandler("ajuda", ajuda_handler))
        
        # Handler para botões
        app.add_handler(CallbackQueryHandler(button_handler))
        
        # Handler de erros
        app.add_error_handler(error_handler)
        
        # Iniciar bot
        print("🤖 BOT-T-Terminal iniciado!")
        app.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        exit(1)

if __name__ == "__main__":
    main() 