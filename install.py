#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import platform
import shutil
from pathlib import Path

# Cores para output
class Cores:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Adiciona variável global no início do arquivo, após as importações
python_executable = "/usr/bin/python3"

def imprimir_banner():
    banner = f"""{Cores.BLUE}
╔══════════════════════════════════════════╗
║     🤖 BOT-T-Terminal - Instalação       ║ 
║                                          ║
║  Bot do Telegram para controle remoto    ║
║  de servidores Linux via terminal        ║
║                                          ║
║  Autor: JOAC                            ║
║  Versão: 1.0.0                          ║
╚══════════════════════════════════════════╝{Cores.END}
    """
    print(banner)

def verificar_root():
    if os.geteuid() != 0:
        print(f"{Cores.FAIL}❌ Este script precisa ser executado como root (sudo){Cores.END}")
        sys.exit(1)

def verificar_sistema():
    print(f"{Cores.HEADER}✨ Verificando sistema...{Cores.END}")
    
    # Verifica se é Linux
    if sys.platform != "linux":
        print(f"{Cores.FAIL}❌ Este bot só funciona em sistemas Linux{Cores.END}")
        sys.exit(1)
    
    # Verifica Python 3.8+
    if sys.version_info < (3, 8):
        print(f"{Cores.FAIL}❌ Python 3.8 ou superior é necessário{Cores.END}")
        sys.exit(1)

def is_debian_based():
    """Verifica se é um sistema baseado em Debian"""
    return os.path.exists("/etc/debian_version")

def configurar_bot():
    config = {
        "token": "",
        "dono_username": "",
        "ids_autorizados": []
    }
    
    print(f"\n{Cores.BLUE}=== Configuração do Bot ==={Cores.END}")
    
    # Token do Bot
    while True:
        token = input("\nDigite o token do bot (obtido do @BotFather): ").strip()
        if token:
            config["token"] = token
            break
        print(f"{Cores.FAIL}Token inválido! Tente novamente.{Cores.END}")
    
    # Username do dono
    while True:
        username = input("\nDigite seu username do Telegram (sem @): ").strip()
        if username:
            config["dono_username"] = username.lower()
            break
        print(f"{Cores.FAIL}Username inválido! Tente novamente.{Cores.END}")
    
    # ID do Telegram
    while True:
        try:
            telegram_id = int(input("\nDigite seu ID do Telegram (obtido do @userinfobot): "))
            config["ids_autorizados"].append(telegram_id)
            break
        except ValueError:
            print(f"{Cores.FAIL}ID inválido! Digite apenas números.{Cores.END}")
    
    # Salva a configuração
    with open("config.json", "w") as f:
        json.dump(config, f, indent=4)
    
    print(f"\n{Cores.GREEN}✅ Configuração salva com sucesso!{Cores.END}")
    return True

def instalar_dependencias():
    try:
        print(f"\n{Cores.BLUE}=== Instalando Dependências ==={Cores.END}")
        
        # Instala as dependências Python
        os.system("pip3 install python-telegram-bot==20.8")
        os.system("pip3 install psutil==5.9.8")
        
        print(f"\n{Cores.GREEN}✅ Dependências instaladas com sucesso!{Cores.END}")
        return True
    except Exception as e:
        print(f"{Cores.FAIL}❌ Erro ao instalar dependências: {str(e)}{Cores.END}")
        return False

def configurar_servico():
    try:
        print(f"\n{Cores.BLUE}=== Configurando Serviço ==={Cores.END}")
        
        # Cria o arquivo de serviço
        service_content = f"""[Unit]
Description=Telegram Terminal Bot
After=network.target

[Service]
Type=simple
WorkingDirectory={os.getcwd()}
ExecStart=/usr/bin/python3 {os.getcwd()}/telegram_terminal_bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""
        
        # Salva o arquivo de serviço
        service_path = "/etc/systemd/system/telegram-terminal-bot.service"
        with open(service_path, "w") as f:
            f.write(service_content)
        
        # Configura o serviço
        os.system("sudo systemctl daemon-reload")
        os.system("sudo systemctl enable telegram-terminal-bot")
        os.system("sudo systemctl start telegram-terminal-bot")
        
        print(f"\n{Cores.GREEN}✅ Serviço configurado com sucesso!{Cores.END}")
        return True
    except Exception as e:
        print(f"{Cores.FAIL}❌ Erro ao configurar serviço: {str(e)}{Cores.END}")
        return False

def desinstalar_bot():
    try:
        print(f"\n{Cores.BLUE}=== Desinstalando Bot ==={Cores.END}")
        
        # Para e remove o serviço
        if os.path.exists("/etc/systemd/system/telegram-terminal-bot.service"):
            os.system("sudo systemctl stop telegram-terminal-bot")
            os.system("sudo systemctl disable telegram-terminal-bot")
            os.system("sudo rm -rf /etc/systemd/system/telegram-terminal-bot.service")
            os.system("sudo systemctl daemon-reload")
            print(f"{Cores.GREEN}✅ Serviço do bot removido{Cores.END}")
        
        # Remove as dependências Python
        os.system("pip3 uninstall -y python-telegram-bot psutil")
        print(f"{Cores.GREEN}✅ Dependências removidas{Cores.END}")
        
        # Remove os arquivos do bot
        bot_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(os.path.dirname(bot_dir))
        if os.path.exists("BOT-T-Terminal-Access"):
            shutil.rmtree("BOT-T-Terminal-Access")
            print(f"{Cores.GREEN}✅ Arquivos do bot removidos{Cores.END}")
        
        print(f"\n{Cores.GREEN}🎉 Bot desinstalado completamente!{Cores.END}")
        return True
    except Exception as e:
        print(f"{Cores.FAIL}❌ Erro ao desinstalar bot: {str(e)}{Cores.END}")
        return False

def instalar_bot():
    print(f"\n{Cores.BLUE}=== Instalando BOT-T-Terminal ==={Cores.END}")
    
    if not configurar_bot():
        return False
    
    if not instalar_dependencias():
        return False
    
    if not configurar_servico():
        return False
    
    print(f"\n{Cores.GREEN}🎉 Bot instalado com sucesso!{Cores.END}")
    print(f"\n{Cores.BLUE}Para ver os logs do bot:{Cores.END}")
    print("sudo journalctl -u telegram-terminal-bot -f")
    return True

def menu_principal():
    while True:
        print(f"\n{Cores.BOLD}=== BOT-T-Terminal ==={Cores.END}")
        print("1. Instalar Bot")
        print("2. Desinstalar Bot")
        print("3. Sair")
        
        opcao = input("\nEscolha uma opção (1-3): ").strip()
        
        if opcao == "1":
            if instalar_bot():
                input("\nPressione ENTER para continuar...")
        elif opcao == "2":
            if desinstalar_bot():
                input("\nPressione ENTER para continuar...")
        elif opcao == "3":
            print(f"\n{Cores.GREEN}Até logo!{Cores.END}")
            sys.exit(0)
        else:
            print(f"\n{Cores.FAIL}❌ Opção inválida! Escolha 1, 2 ou 3.{Cores.END}")

def main():
    try:
        # Se for chamado com argumento 'menu', abre o menu
        if len(sys.argv) > 1 and sys.argv[1] == "menu":
            verificar_root()
            menu_principal()
            return
        
        # Instalação normal
        imprimir_banner()
        verificar_root()
        verificar_sistema()
        
        menu_principal()
    except KeyboardInterrupt:
        print(f"\n{Cores.WARNING}⚠️ Instalação cancelada{Cores.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Cores.FAIL}❌ Erro: {e}{Cores.END}")
        sys.exit(1)

if __name__ == "__main__":
    main() 