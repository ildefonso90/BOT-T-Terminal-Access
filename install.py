#!/usr/bin/env python3
import os
import sys
import subprocess
import json
from pathlib import Path
import time

def print_banner():
    banner = """
\033[1;36m██████╗  ██████╗ ████████╗   ████████╗    ████████╗███████╗██████╗ ███╗   ███╗██╗███╗   ██╗ █████╗ ██╗     
██╔══██╗██╔═══██╗╚══██╔══╝   ╚══██╔══╝    ╚══██╔══╝██╔════╝██╔══██╗████╗ ████║██║████╗  ██║██╔══██╗██║     
██████╔╝██║   ██║   ██║         ██║          ██║   █████╗  ██████╔╝██╔████╔██║██║██╔██╗ ██║███████║██║     
██╔══██╗██║   ██║   ██║         ██║          ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║██║██║╚██╗██║██╔══██║██║     
██████╔╝╚██████╔╝   ██║         ██║          ██║   ███████╗██║  ██║██║ ╚═╝ ██║██║██║ ╚████║██║  ██║███████╗
╚═════╝  ╚═════╝    ╚═╝         ╚═╝          ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝\033[0m
                                                                                                    
\033[1;33m╔══════════════════════════════════════════════════════════════════════════════╗
║                     Controle Remoto via Telegram Bot                        ║
║                        Desenvolvido por: \033[1;32mJOAC\033[1;33m                              ║
║                          Versão: 1.0.0                                     ║
╚══════════════════════════════════════════════════════════════════════════════╝\033[0m
"""
    # Efeito de digitação para o banner
    for line in banner.split('\n'):
        print(line)
        time.sleep(0.1)  # Pequeno delay entre cada linha

def print_status(message, status="info"):
    """Imprime mensagens estilizadas"""
    colors = {
        "info": "\033[1;34m",    # Azul
        "success": "\033[1;32m",  # Verde
        "warning": "\033[1;33m",  # Amarelo
        "error": "\033[1;31m",    # Vermelho
        "reset": "\033[0m"        # Reset
    }
    
    prefix = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌"
    }
    
    print(f"{colors[status]}{prefix[status]} {message}{colors['reset']}")

def executar_comando(comando):
    try:
        return subprocess.run(comando, shell=True, capture_output=True, text=True)
    except Exception as e:
        print_status(f"Erro ao executar comando: {e}", "error")
        return None

def criar_servico_systemd():
    service_content = """[Unit]
Description=BOT-T-Terminal - Telegram Bot para Controle Remoto
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory={work_dir}
ExecStart=/usr/bin/python3 {work_dir}/telegram_terminal_bot.py
Restart=always
RestartSec=10
StartLimitInterval=0
Environment="PYTHONUNBUFFERED=1"

# Garantir privilégios necessários
AmbientCapabilities=CAP_NET_BIND_SERVICE
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
SecureBits=keep-caps
NoNewPrivileges=no

# Configurações de segurança
ProtectSystem=full
ReadWritePaths={work_dir}
PrivateTmp=true

[Install]
WantedBy=multi-user.target
"""
    work_dir = os.getcwd()
    service_content = service_content.format(work_dir=work_dir)
    
    service_path = '/etc/systemd/system/telegram-terminal-bot.service'
    with open(service_path, 'w') as f:
        f.write(service_content)
    
    # Ajustar permissões
    os.chmod(service_path, 0o644)
    os.chmod('telegram_terminal_bot.py', 0o755)

def configurar_bot():
    config = {
        "token": "",
        "dono_username": "",
        "usuarios_autorizados": [],
        "tentativas_falhas": {}
    }
    
    print_status("\n=== Configuração do BOT-T-Terminal ===", "info")
    
    # Token do Bot
    print_status("\nPara obter o token do bot:", "info")
    print("1. Abra o Telegram e procure por @BotFather")
    print("2. Envie /newbot e siga as instruções")
    print("3. Copie o token fornecido")
    token = input("\n🔑 Cole o token do seu bot aqui: ").strip()
    config["token"] = token

    # Username do dono
    print_status("\nConfiguração do Dono do Bot:", "info")
    print("⚠️ IMPORTANTE: O username deve ser exatamente igual ao do Telegram")
    print("1. Abra seu Telegram")
    print("2. Vá em Configurações -> Username")
    dono_username = input("\nDigite seu username do Telegram (sem @): ").strip().lower()
    config["dono_username"] = dono_username

    # IDs dos usuários
    print_status("\nAdicionando usuários autorizados:", "info")
    print("1. Envie uma mensagem para @userinfobot no Telegram")
    print("2. Ele responderá com seu ID")
    print(f"3. Certifique-se de adicionar seu próprio ID como dono ({dono_username})")
    while True:
        user_id = input("\nDigite o ID do usuário autorizado (ou pressione Enter para terminar): ").strip()
        if not user_id:
            break
        try:
            config["usuarios_autorizados"].append(int(user_id))
        except ValueError:
            print_status("ID inválido! Digite apenas números.", "error")

    # Salvar configuração
    config_path = 'config.json'
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)
    
    # Ajustar permissões do arquivo de configuração
    os.chmod(config_path, 0o600)
    print_status("Configurações salvas com sucesso!", "success")

def verificar_instalacao():
    """Verifica se todas as dependências estão instaladas"""
    print_status("\nVerificando requisitos do sistema...", "info")
    
    # Verificar Python3
    python_version = executar_comando("python3 --version")
    if not python_version or python_version.returncode != 0:
        print_status("Python3 não encontrado! Por favor, instale o Python3.", "error")
        sys.exit(1)
    else:
        print_status(f"Python3 encontrado: {python_version.stdout.strip()}", "success")
    
    # Tentar diferentes métodos para garantir que temos um gerenciador de pacotes
    print_status("Verificando/Instalando gerenciador de pacotes...", "info")
    
    # Lista de possíveis comandos para instalar pacotes
    package_managers = [
        ("pip3", "pip3 install"),
        ("pip", "pip install"),
        ("python3 -m pip", "python3 -m pip install"),
        ("python -m pip", "python -m pip install")
    ]
    
    install_command = None
    for cmd, install_cmd in package_managers:
        result = executar_comando(f"{cmd} --version")
        if result and result.returncode == 0:
            install_command = install_cmd
            print_status(f"Usando {cmd} para instalação", "success")
            break
    
    if not install_command:
        print_status("Tentando instalar pip...", "info")
        # Tentar instalar pip usando diferentes métodos
        methods = [
            "apt-get update && apt-get install -y python3-pip",
            "apt update && apt install -y python3-pip",
            "yum install -y python3-pip",
            "dnf install -y python3-pip",
            "curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python3 get-pip.py"
        ]
        
        for method in methods:
            print_status(f"Tentando: {method}", "info")
            result = executar_comando(method)
            if result and result.returncode == 0:
                # Verificar se pip foi instalado
                for cmd, install_cmd in package_managers:
                    result = executar_comando(f"{cmd} --version")
                    if result and result.returncode == 0:
                        install_command = install_cmd
                        print_status(f"Instalação bem sucedida! Usando {cmd}", "success")
                        break
                if install_command:
                    break
        
        if not install_command:
            print_status("Não foi possível instalar um gerenciador de pacotes!", "error")
            print_status("Por favor, instale manualmente o pip usando um dos comandos:", "info")
            print("1. apt-get update && apt-get install -y python3-pip")
            print("2. curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python3 get-pip.py")
            sys.exit(1)
    
    return install_command

def instalar_dependencias(install_command):
    print_status("\nInstalando dependências...", "info")
    
    # Lista de dependências necessárias
    dependencies = [
        "python-telegram-bot==20.8",
        "psutil==5.9.8"
    ]
    
    # Primeiro, atualizar o próprio pip
    print_status("Atualizando gerenciador de pacotes...", "info")
    executar_comando(f"{install_command} --upgrade pip")
    
    # Instalar cada dependência individualmente
    success = True
    for dep in dependencies:
        print_status(f"Instalando {dep}...", "info")
        
        # Tentar diferentes métodos de instalação
        methods = [
            f"{install_command} {dep}",
            f"{install_command} --no-cache-dir {dep}",
            f"{install_command} --ignore-installed {dep}",
            f"{install_command} --user {dep}"
        ]
        
        installed = False
        for method in methods:
            print_status(f"Tentando: {method}", "info")
            result = executar_comando(method)
            if result and result.returncode == 0:
                installed = True
                print_status(f"{dep} instalado com sucesso!", "success")
                break
        
        if not installed:
            print_status(f"Falha ao instalar {dep}", "error")
            success = False
    
    if not success:
        print_status("Algumas dependências não puderam ser instaladas.", "error")
        print_status("Por favor, tente instalar manualmente:", "info")
        for dep in dependencies:
            print(f"{install_command} {dep}")
        sys.exit(1)
    else:
        print_status("Todas as dependências foram instaladas com sucesso!", "success")

def main():
    if os.geteuid() != 0:
        print_status("Este script precisa ser executado como root (sudo)!", "error")
        sys.exit(1)

    # Limpar a tela
    os.system('clear' if os.name == 'posix' else 'cls')
    
    print_banner()
    print_status("\nIniciando instalação do BOT-T-Terminal...", "info")
    
    # Verificar instalação e obter comando de instalação
    install_command = verificar_instalacao()
    
    # Instalar dependências
    instalar_dependencias(install_command)
    
    # Configurar bot
    configurar_bot()
    
    # Criar e ativar serviço systemd
    print_status("\nConfigurando inicialização automática...", "info")
    criar_servico_systemd()
    
    # Recarregar e ativar serviço
    comandos = [
        "systemctl daemon-reload",
        "systemctl enable telegram-terminal-bot",
        "systemctl restart telegram-terminal-bot"
    ]
    
    for cmd in comandos:
        resultado = executar_comando(cmd)
        if not resultado or resultado.returncode != 0:
            print_status(f"Erro ao executar: {cmd}", "error")
            print("Verifique os logs com: journalctl -u telegram-terminal-bot")
            sys.exit(1)
    
    # Verificar status do serviço
    status = executar_comando("systemctl is-active telegram-terminal-bot")
    if status and status.stdout.strip() == "active":
        print_status("\nBOT-T-Terminal instalado e em execução!", "success")
    else:
        print_status("\nBOT-T-Terminal instalado, mas pode haver problemas na execução.", "warning")
        print("Verifique os logs com: journalctl -u telegram-terminal-bot")
    
    print_status("\nComo usar seu bot:", "info")
    print("1. Abra o Telegram e procure pelo seu bot")
    print("2. Envie /start para iniciar e ver as instruções completas")
    print("3. Apenas o dono pode autorizar novos usuários")
    
    print_status("\nGerenciamento do serviço:", "info")
    print("- Verificar status: sudo systemctl status telegram-terminal-bot")
    print("- Ver logs: sudo journalctl -u telegram-terminal-bot -f")
    print("- Reiniciar: sudo systemctl restart telegram-terminal-bot")
    print("- Parar: sudo systemctl stop telegram-terminal-bot")
    
    print_status("\nIMPORTANTE:", "warning")
    print("- O bot está configurado para iniciar automaticamente com o servidor")
    print("- Todos os comandos serão executados com privilégios root")
    print("- Mantenha o arquivo config.json seguro e com permissões restritas")
    print("- Após 7 tentativas falhas, usuários serão bloqueados")
    print(f"- Apenas o dono ({config['dono_username']}) pode desbloquear usuários")
    
    # Banner de conclusão
    print("""
\033[1;32m
╔══════════════════════════════════════════════════╗
║      BOT-T-Terminal Instalado com Sucesso!       ║
║          Desenvolvido com ❤️ por JOAC            ║
╚══════════════════════════════════════════════════╝\033[0m
""")

if __name__ == "__main__":
    main() 