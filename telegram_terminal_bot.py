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
        DONO_USERNAME = config['dono_username']
        USUARIOS_AUTORIZADOS = config['usuarios_autorizados']
        TENTATIVAS_FALHAS = config.get('tentativas_falhas', {})
except Exception as e:
    print(f"Erro ao carregar configurações: {e}")
    print("Execute o script de instalação (install.py) primeiro!")
    exit(1)

# Limite de tentativas antes do bloqueio
MAX_TENTATIVAS = 7

def salvar_configuracoes():
    """Salva as configurações atualizadas no arquivo"""
    with open('config.json', 'w') as f:
        json.dump({
            'token': TOKEN,
            'dono_username': DONO_USERNAME,
            'usuarios_autorizados': USUARIOS_AUTORIZADOS,
            'tentativas_falhas': TENTATIVAS_FALHAS
        }, f, indent=4)

def is_authorized(user_id: int, username: str = None) -> bool:
    """Verifica se o usuário está autorizado e não está bloqueado"""
    # Verificar se está bloqueado
    if username and username in TENTATIVAS_FALHAS:
        if TENTATIVAS_FALHAS[username] >= MAX_TENTATIVAS:
            return False
    
    # Verificar se é autorizado
    return user_id in USUARIOS_AUTORIZADOS

def registrar_tentativa_falha(username: str):
    """Registra uma tentativa falha de acesso"""
    if not username:
        return
    
    username = username.lower()
    if username not in TENTATIVAS_FALHAS:
        TENTATIVAS_FALHAS[username] = 1
    else:
        TENTATIVAS_FALHAS[username] += 1
    
    salvar_configuracoes()

def is_owner(username: str) -> bool:
    """Verifica se o usuário é o dono do bot"""
    return username.lower() == DONO_USERNAME.lower()

COMANDOS_COMUNS = {
    "📂 Listar arquivos": "ls -la",
    "💾 Uso do disco": "df -h",
    "🔄 Uso da memória": "free -h",
    "⚡ Uso da CPU": "top -bn1 | head -n 5",
    "📡 Conexões de rede": "netstat -tuln",
    "🔍 Processos ativos": "ps aux | head -n 5",
    "👤 Usuário atual": "whoami && id",
    "📅 Data e hora": "date",
    "🌡️ Temperatura CPU": "cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null || echo 'Não disponível'",
    "🔒 Últimos logins": "last | head -n 5"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start - Envia mensagem de boas-vindas com menu principal"""
    user_id = update.effective_user.id
    username = update.effective_user.username

    if not username:
        await update.message.reply_text(
            "❌ Você precisa ter um username configurado no Telegram para usar este bot."
        )
        return

    # Verificar se é o dono
    if is_owner(username):
        # Resetar tentativas de falha se o dono acessar
        TENTATIVAS_FALHAS.clear()
        salvar_configuracoes()
    elif not is_authorized(user_id, username):
        # Registrar tentativa falha
        registrar_tentativa_falha(username)
        tentativas = TENTATIVAS_FALHAS.get(username, 0)
        
        if tentativas >= MAX_TENTATIVAS:
            await update.message.reply_text(
                "🚫 Acesso bloqueado devido a múltiplas tentativas não autorizadas.\n"
                "Entre em contato com o administrador do sistema."
            )
        else:
            await update.message.reply_text(
                f"❌ Acesso não autorizado!\n"
                f"Tentativas restantes: {MAX_TENTATIVAS - tentativas}"
            )
        return

    # Mensagem de boas-vindas detalhada
    welcome_message = f"""
🤖 *Bem-vindo ao Terminal Bot!*

Este bot permite controlar seu servidor via Telegram com privilégios root.

*Informações do Sistema:*
• Sistema: {platform.system()} {platform.release()}
• Hostname: {platform.node()}
• Python: {platform.python_version()}
• Bot Version: 1.0

*Comandos Disponíveis:*
📌 *Básicos:*
• /start - Mostra esta mensagem
• /help - Mostra ajuda detalhada
• /status - Status do sistema

🛠️ *Terminal:*
• /cmd <comando> - Executa comando
Exemplo: `/cmd ls -la`

⚡ *Comandos Rápidos:*
• Use o menu abaixo para acessar

⚠️ *Segurança:*
• Todos os comandos são executados como root
• Todas as ações são registradas
• {MAX_TENTATIVAS} tentativas falhas = bloqueio
• Apenas o dono pode desbloquear usuários

*Status do Usuário:*
• Nome: {update.effective_user.first_name}
• Username: @{username}
• ID: `{user_id}`
• Nível: {"👑 Dono" if is_owner(username) else "👤 Autorizado"}

Use os botões abaixo para começar:
"""

    keyboard = [
        [InlineKeyboardButton("📊 Status do Sistema", callback_data='status')],
        [InlineKeyboardButton("⚡ Comandos Rápidos", callback_data='quick_commands')],
        [InlineKeyboardButton("❓ Ajuda Detalhada", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /help - Mostra todos os comandos disponíveis"""
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("❌ Desculpe, você não está autorizado a usar este bot.")
        return
    
    help_text = """
🤖 *Comandos Disponíveis*

Básicos:
/start - Inicia o bot e mostra o menu principal
/help - Mostra esta mensagem de ajuda
/status - Mostra status do sistema

Comandos do Terminal:
/cmd <comando> - Executa um comando no terminal
Exemplo: `/cmd ls -la`

Comandos Rápidos:
/disk - Mostra uso do disco
/mem - Mostra uso da memória
/cpu - Mostra uso da CPU
/net - Mostra conexões de rede
/ps - Lista processos ativos

⚠️ *Observações*:
- Apenas usuários autorizados podem usar o bot
- Alguns comandos podem levar alguns segundos para responder
- Use com responsabilidade!
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /status - Mostra informações do sistema"""
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("❌ Desculpe, você não está autorizado a usar este bot.")
        return
    
    # Coleta informações do sistema
    cpu_percent = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    boot_time = datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
    
    status_text = f"""
🖥️ *Status do Sistema*

*Sistema:*
OS: {platform.system()} {platform.release()}
Uptime desde: {boot_time}

*Recursos:*
CPU: {cpu_percent}%
RAM: {mem.percent}% usado
Disco: {disk.percent}% usado

*Memória:*
Total: {bytes_to_human(mem.total)}
Usado: {bytes_to_human(mem.used)}
Livre: {bytes_to_human(mem.free)}

*Disco:*
Total: {bytes_to_human(disk.total)}
Usado: {bytes_to_human(disk.used)}
Livre: {bytes_to_human(disk.free)}
"""
    await update.message.reply_text(status_text, parse_mode='Markdown')

async def quick_commands_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra menu de comandos rápidos"""
    keyboard = []
    for comando_nome in COMANDOS_COMUNS.keys():
        keyboard.append([InlineKeyboardButton(comando_nome, callback_data=f'cmd_{comando_nome}')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "📝 Selecione um comando rápido:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manipula callbacks dos botões"""
    query = update.callback_query
    await query.answer()
    
    if not is_authorized(query.from_user.id):
        await query.message.reply_text("❌ Desculpe, você não está autorizado a usar este bot.")
        return
    
    if query.data == 'status':
        await status_command(query, context)
    elif query.data == 'quick_commands':
        await quick_commands_menu(query, context)
    elif query.data == 'help':
        await help_command(query, context)
    elif query.data.startswith('cmd_'):
        comando_nome = query.data[4:]
        comando = COMANDOS_COMUNS.get(comando_nome)
        if comando:
            context.user_data['command'] = comando
            await execute_command(query, context)

async def execute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Executa o comando recebido no terminal com privilégios root"""
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("❌ Desculpe, você não está autorizado a usar este bot.")
        return

    # Obtém o comando
    if isinstance(update, Update):
        command = update.message.text[5:].strip()  # Remove '/cmd '
    else:
        command = context.user_data.get('command', '')

    if not command:
        await update.message.reply_text("❌ Por favor, especifique um comando para executar.")
        return

    try:
        # Garantir que o comando seja executado como root
        if os.geteuid() != 0:
            command = f"sudo {command}"

        # Registrar comando no log do sistema
        log_command = f"Comando executado via Telegram Bot por ID {update.effective_user.id}: {command}"
        subprocess.run(['logger', '-t', 'telegram-bot', log_command])

        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid  # Criar novo grupo de processo
        )
        
        try:
            stdout, stderr = process.communicate(timeout=60)  # Timeout de 60 segundos
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            await update.message.reply_text("⚠️ Comando cancelado: tempo limite excedido (60s)")
            return

        response = f"🔧 *Comando executado como root:* `{command}`\n\n"
        if stdout:
            response += f"📤 *Saída:*\n```\n{stdout[:1500]}```\n"  # Limitar saída
            if len(stdout) > 1500:
                response += "\n... (saída truncada) ...\n"
        if stderr:
            response += f"⚠️ *Erro:*\n```\n{stderr[:500]}```\n"  # Limitar erros
            if len(stderr) > 500:
                response += "\n... (mensagem de erro truncada) ...\n"
        if not stdout and not stderr:
            response += "✅ Comando executado sem saída."

        # Divide a resposta se for muito longa
        if len(response) > 4000:
            for i in range(0, len(response), 4000):
                await update.message.reply_text(
                    response[i:i+4000],
                    parse_mode='Markdown'
                )
        else:
            await update.message.reply_text(response, parse_mode='Markdown')

    except Exception as e:
        error_msg = f"❌ Erro ao executar o comando: {str(e)}"
        await update.message.reply_text(error_msg)
        # Registrar erro no log do sistema
        subprocess.run(['logger', '-t', 'telegram-bot', f"Erro: {error_msg}"])

def bytes_to_human(bytes_value):
    """Converte bytes para formato legível"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024
    return f"{bytes_value:.2f} PB"

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manipula erros do bot"""
    print(f"Erro: {context.error}")
    await update.message.reply_text("❌ Ocorreu um erro ao processar sua solicitação.")

def main():
    """Função principal"""
    if not USUARIOS_AUTORIZADOS:
        print("⚠️ AVISO: Nenhum usuário autorizado configurado!")
        print("Execute o script de instalação (install.py) para configurar o bot.")
        return

    # Cria o aplicativo
    app = Application.builder().token(TOKEN).build()

    # Adiciona os handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("cmd", execute_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_error_handler(error_handler)

    # Inicia o bot
    print("🤖 Bot iniciado! Pressione Ctrl+C para parar.")
    app.run_polling(poll_interval=1)

if __name__ == "__main__":
    main() 