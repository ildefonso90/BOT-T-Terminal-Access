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
    print_status("\n=== Configuração do BOT-T-Terminal ===", "info")
    
    config = {}
    
    # Token do Bot
    print_status("\nPara obter o token do bot:", "info")
    print("1. Abra o Telegram e procure por @BotFather")
    print("2. Envie /newbot e siga as instruções")
    print("3. Copie o token fornecido")
    print()
    config['token'] = input("🔑 Cole o token do seu bot aqui: ").strip()
    
    # Username do dono
    print_status("\nConfiguração do Dono do Bot:", "info")
    print("⚠️ IMPORTANTE: O username deve ser exatamente igual ao do Telegram")
    print("1. Abra seu Telegram")
    print("2. Vá em Configurações -> Username")
    print()
    config['dono_username'] = input("Digite seu username do Telegram (sem @): ").strip().lower()
    
    # IDs autorizados
    print_status("\nAdicionando usuários autorizados:", "info")
    print_status("\nComo conseguir seu ID do Telegram:", "info")
    print("\nMétodo 1 - Usando @userinfobot:")
    print("1. Abra o Telegram")
    print("2. Procure por @userinfobot")
    print("3. Clique no bot")
    print("4. Envie qualquer mensagem")
    print("5. O bot responderá com seu ID")
    
    print("\nMétodo 2 - Usando @RawDataBot:")
    print("1. Procure por @RawDataBot no Telegram")
    print("2. Clique em 'Start'")
    print("3. O bot mostrará todas suas informações, incluindo seu ID")
    
    print("\nMétodo 3 - Usando @getidsbot:")
    print("1. Procure por @getidsbot no Telegram")
    print("2. Envie /start")
    print("3. O bot mostrará seu ID")
    
    print("\nMétodo 4 - Via Navegador:")
    print("1. Acesse web.telegram.org")
    print("2. Faça login")
    print("3. Abra o DevTools (F12)")
    print("4. Procure por 'id' nos dados armazenados")
    
    print(f"\n⚠️ IMPORTANTE: Certifique-se de adicionar seu próprio ID como dono ({config['dono_username']})")
    print("💡 O ID é um número longo (geralmente 9-10 dígitos)")
    print()
    
    ids_autorizados = []
    while True:
        user_id = input("\nDigite o ID do usuário autorizado (ou pressione Enter para terminar): ").strip()
        if not user_id:
            break
        try:
            ids_autorizados.append(int(user_id))
        except ValueError:
            print_status("ID inválido! Digite apenas números.", "error")
    
    config['ids_autorizados'] = ids_autorizados
    config['tentativas_maximas'] = 7
    config['usuarios_bloqueados'] = []
    
    # Salvar configurações
    try:
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        os.chmod('config.json', 0o600)  # Apenas root pode ler/escrever
        print_status("Configurações salvas com sucesso!", "success")
    except Exception as e:
        print_status(f"Erro ao salvar configurações: {str(e)}", "error")
        sys.exit(1)
    
    return config

def verificar_instalacao():
    """Verifica se todas as dependências estão instaladas"""
    print_status("\nVerificando requisitos do sistema...", "info")
    
    # Verificar Python3
    python_version = executar_comando("python3 --version")
    if not python_version or python_version.returncode != 0:
        print_status("Python3 não encontrado! Tentando instalar...", "warning")
        # Tentar instalar Python3
        methods = [
            "apt-get update && apt-get install -y python3",
            "apt update && apt install -y python3",
            "yum install -y python3",
            "dnf install -y python3"
        ]
        for method in methods:
            result = executar_comando(method)
            if result and result.returncode == 0:
                print_status("Python3 instalado com sucesso!", "success")
                break
    else:
        print_status(f"Python3 encontrado: {python_version.stdout.strip()}", "success")
    
    # Verificar Node.js como alternativa
    node_version = executar_comando("node --version")
    if node_version and node_version.returncode == 0:
        print_status(f"Node.js encontrado: {node_version.stdout.strip()}", "success")
        return "node"
    
    # Verificar Go como alternativa
    go_version = executar_comando("go version")
    if go_version and go_version.returncode == 0:
        print_status(f"Go encontrado: {go_version.stdout.strip()}", "success")
        return "go"
    
    # Tentar diferentes métodos para gerenciador de pacotes Python
    print_status("Verificando/Instalando gerenciador de pacotes...", "info")
    
    package_managers = [
        ("pip3", "pip3 install"),
        ("pip", "pip install"),
        ("python3 -m pip", "python3 -m pip install"),
        ("python -m pip", "python -m pip install")
    ]
    
    for cmd, install_cmd in package_managers:
        result = executar_comando(f"{cmd} --version")
        if result and result.returncode == 0:
            print_status(f"Usando {cmd} para instalação", "success")
            return install_cmd
    
    # Se não encontrou pip, tentar instalar
    print_status("Tentando instalar gerenciadores de pacotes...", "info")
    
    # Tentar instalar pip
    pip_methods = [
        "apt-get update && apt-get install -y python3-pip",
        "apt update && apt install -y python3-pip",
        "yum install -y python3-pip",
        "dnf install -y python3-pip",
        "curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python3 get-pip.py"
    ]
    
    # Tentar instalar Node.js
    node_methods = [
        "curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && apt-get install -y nodejs",
        "dnf module install -y nodejs:18/common",
        "yum install -y nodejs npm"
    ]
    
    # Tentar instalar Go
    go_methods = [
        "apt-get update && apt-get install -y golang-go",
        "yum install -y golang",
        "dnf install -y golang"
    ]
    
    # Tentar todos os métodos
    for method in pip_methods + node_methods + go_methods:
        print_status(f"Tentando: {method}", "info")
        result = executar_comando(method)
        if result and result.returncode == 0:
            # Verificar qual foi instalado
            for cmd, install_cmd in package_managers:
                if executar_comando(f"{cmd} --version").returncode == 0:
                    return install_cmd
            if executar_comando("node --version").returncode == 0:
                return "node"
            if executar_comando("go version").returncode == 0:
                return "go"
    
    print_status("Não foi possível instalar nenhum gerenciador de pacotes!", "error")
    print_status("Por favor, instale manualmente um dos seguintes:", "info")
    print("1. Python: apt-get update && apt-get install -y python3-pip")
    print("2. Node.js: curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && apt-get install -y nodejs")
    print("3. Go: apt-get update && apt-get install -y golang-go")
    sys.exit(1)

def instalar_dependencias(install_type):
    print_status("\nInstalando dependências...", "info")
    
    if install_type == "node":
        # Criar package.json
        package_json = {
            "name": "bot-t-terminal",
            "version": "1.0.0",
            "dependencies": {
                "node-telegram-bot-api": "^0.61.0",
                "systeminformation": "^5.21.7"
            }
        }
        with open('package.json', 'w') as f:
            json.dump(package_json, f, indent=2)
        
        # Instalar dependências Node.js
        methods = [
            "npm install",
            "npm install --no-package-lock",
            "npm install --force"
        ]
        
        for method in methods:
            print_status(f"Tentando: {method}", "info")
            result = executar_comando(method)
            if result and result.returncode == 0:
                print_status("Dependências Node.js instaladas com sucesso!", "success")
                return True
        
    elif install_type == "go":
        # Criar go.mod
        executar_comando("go mod init bot-t-terminal")
        
        # Instalar dependências Go
        go_deps = [
            "go get -u github.com/go-telegram-bot-api/telegram-bot-api/v5",
            "go get -u github.com/shirou/gopsutil/v3"
        ]
        
        success = True
        for dep in go_deps:
            print_status(f"Instalando: {dep}", "info")
            result = executar_comando(dep)
            if not result or result.returncode != 0:
                success = False
        
        if success:
            print_status("Dependências Go instaladas com sucesso!", "success")
            return True
            
    else:  # Python
        # Lista de dependências Python
        dependencies = [
            "python-telegram-bot==20.8",
            "psutil==5.9.8"
        ]
        
        # Primeiro, atualizar o pip
        executar_comando(f"{install_type} --upgrade pip")
        
        # Instalar cada dependência
        success = True
        for dep in dependencies:
            methods = [
                f"{install_type} {dep}",
                f"{install_type} --no-cache-dir {dep}",
                f"{install_type} --ignore-installed {dep}",
                f"{install_type} --user {dep}"
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
                success = False
        
        if success:
            print_status("Todas as dependências Python instaladas com sucesso!", "success")
            return True
    
    print_status("Falha ao instalar dependências.", "error")
    return False

def mostrar_menu():
    """Mostra o menu interativo do BOT-T-Terminal"""
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        print("""\033[1;36m
╔══════════════════════════════════════════════════╗
║             BOT-T-Terminal - Menu               ║
╠══════════════════════════════════════════════════╣
║                                                 ║
║  [1] 🟢 Iniciar Bot                            ║
║  [2] 🔴 Parar Bot                              ║
║  [3] 🔄 Reiniciar Bot                          ║
║  [4] 📊 Status do Bot                          ║
║  [5] 📝 Ver Logs                               ║
║  [6] 👥 Gerenciar Usuários                     ║
║  [7] ⚙️  Configurações                          ║
║  [8] ℹ️  Sobre                                  ║
║  [0] 🚪 Sair                                   ║
║                                                 ║
╚══════════════════════════════════════════════════╝\033[0m
""")
        opcao = input("\nEscolha uma opção: ").strip()
        
        if opcao == "1":
            print_status("\nIniciando o BOT-T-Terminal...", "info")
            resultado = executar_comando("systemctl start telegram-terminal-bot")
            if resultado and resultado.returncode == 0:
                print_status("Bot iniciado com sucesso!", "success")
            else:
                print_status("Erro ao iniciar o bot!", "error")
        
        elif opcao == "2":
            print_status("\nParando o BOT-T-Terminal...", "info")
            resultado = executar_comando("systemctl stop telegram-terminal-bot")
            if resultado and resultado.returncode == 0:
                print_status("Bot parado com sucesso!", "success")
            else:
                print_status("Erro ao parar o bot!", "error")
        
        elif opcao == "3":
            print_status("\nReiniciando o BOT-T-Terminal...", "info")
            resultado = executar_comando("systemctl restart telegram-terminal-bot")
            if resultado and resultado.returncode == 0:
                print_status("Bot reiniciado com sucesso!", "success")
            else:
                print_status("Erro ao reiniciar o bot!", "error")
        
        elif opcao == "4":
            print_status("\nStatus do BOT-T-Terminal:", "info")
            status = executar_comando("systemctl status telegram-terminal-bot")
            if status:
                print("\n" + status.stdout)
            input("\nPressione Enter para continuar...")
        
        elif opcao == "5":
            print_status("\nÚltimas 50 linhas do log:", "info")
            logs = executar_comando("journalctl -u telegram-terminal-bot -n 50 --no-pager")
            if logs:
                print("\n" + logs.stdout)
            input("\nPressione Enter para continuar...")
        
        elif opcao == "6":
            while True:
                os.system('clear' if os.name == 'posix' else 'cls')
                print("""\033[1;33m
╔══════════════════════════════════════════════════╗
║           Gerenciamento de Usuários             ║
╠══════════════════════════════════════════════════╣
║                                                 ║
║  [1] 📋 Listar Usuários Autorizados            ║
║  [2] ➕ Adicionar Usuário                       ║
║  [3] ➖ Remover Usuário                         ║
║  [4] 🔓 Desbloquear Usuário                    ║
║  [0] 🔙 Voltar                                 ║
║                                                 ║
╚══════════════════════════════════════════════════╝\033[0m
""")
                sub_opcao = input("\nEscolha uma opção: ").strip()
                
                if sub_opcao == "1":
                    try:
                        with open('config.json', 'r') as f:
                            config = json.load(f)
                        print("\nUsuários Autorizados:")
                        for user_id in config['ids_autorizados']:
                            print(f"- ID: {user_id}")
                        print("\nUsuários Bloqueados:")
                        for user_id in config.get('usuarios_bloqueados', []):
                            print(f"- ID: {user_id}")
                    except Exception as e:
                        print_status(f"Erro ao ler configurações: {e}", "error")
                    input("\nPressione Enter para continuar...")
                
                elif sub_opcao == "2":
                    try:
                        user_id = input("\nDigite o ID do usuário para adicionar: ").strip()
                        with open('config.json', 'r') as f:
                            config = json.load(f)
                        if int(user_id) not in config['ids_autorizados']:
                            config['ids_autorizados'].append(int(user_id))
                            with open('config.json', 'w') as f:
                                json.dump(config, f, indent=4)
                            print_status("Usuário adicionado com sucesso!", "success")
                        else:
                            print_status("Usuário já está autorizado!", "warning")
                    except Exception as e:
                        print_status(f"Erro ao adicionar usuário: {e}", "error")
                    input("\nPressione Enter para continuar...")
                
                elif sub_opcao == "3":
                    try:
                        user_id = input("\nDigite o ID do usuário para remover: ").strip()
                        with open('config.json', 'r') as f:
                            config = json.load(f)
                        if int(user_id) in config['ids_autorizados']:
                            config['ids_autorizados'].remove(int(user_id))
                            with open('config.json', 'w') as f:
                                json.dump(config, f, indent=4)
                            print_status("Usuário removido com sucesso!", "success")
                        else:
                            print_status("Usuário não encontrado!", "error")
                    except Exception as e:
                        print_status(f"Erro ao remover usuário: {e}", "error")
                    input("\nPressione Enter para continuar...")
                
                elif sub_opcao == "4":
                    try:
                        user_id = input("\nDigite o ID do usuário para desbloquear: ").strip()
                        with open('config.json', 'r') as f:
                            config = json.load(f)
                        if int(user_id) in config.get('usuarios_bloqueados', []):
                            config['usuarios_bloqueados'].remove(int(user_id))
                            with open('config.json', 'w') as f:
                                json.dump(config, f, indent=4)
                            print_status("Usuário desbloqueado com sucesso!", "success")
                        else:
                            print_status("Usuário não está bloqueado!", "warning")
                    except Exception as e:
                        print_status(f"Erro ao desbloquear usuário: {e}", "error")
                    input("\nPressione Enter para continuar...")
                
                elif sub_opcao == "0":
                    break
        
        elif opcao == "7":
            print_status("\nAbrindo configurações...", "info")
            try:
                with open('config.json', 'r') as f:
                    config = json.load(f)
                print("\nConfigurações atuais:")
                print(json.dumps(config, indent=4))
            except Exception as e:
                print_status(f"Erro ao ler configurações: {e}", "error")
            input("\nPressione Enter para continuar...")
        
        elif opcao == "8":
            print("""\033[1;32m
╔══════════════════════════════════════════════════╗
║               Sobre BOT-T-Terminal               ║
╠══════════════════════════════════════════════════╣
║                                                 ║
║  Versão: 1.0.0                                 ║
║  Desenvolvido por: JOAC                        ║
║  GitHub: https://github.com/ildefonso090       ║
║                                                ║
║  Bot do Telegram para controle remoto de       ║
║  servidores Linux via terminal.                ║
║                                                ║
╚══════════════════════════════════════════════════╝\033[0m
""")
            input("\nPressione Enter para continuar...")
        
        elif opcao == "0":
            print_status("\nSaindo do BOT-T-Terminal...", "info")
            break
        
        else:
            print_status("Opção inválida!", "error")
            time.sleep(1)

def criar_alias():
    """Cria um alias 'bot' para acessar o menu facilmente"""
    try:
        # Obter o caminho absoluto do script
        script_path = os.path.abspath(__file__)
        
        # Obter o caminho do .bashrc do usuário que executou o sudo
        sudo_user = os.environ.get('SUDO_USER', os.environ.get('USER'))
        bashrc_path = os.path.expanduser(f'~{sudo_user}/.bashrc')
        
        # Criar o comando do alias
        alias_cmd = f'\n# BOT-T-Terminal alias\nalias bot="sudo python3 {script_path} menu"\n'
        
        # Verificar se o alias já existe
        if os.path.exists(bashrc_path):
            with open(bashrc_path, 'r') as f:
                if 'alias bot="sudo python3' in f.read():
                    return
        
        # Adicionar o alias ao .bashrc
        with open(bashrc_path, 'a') as f:
            f.write(alias_cmd)
        
        # Tentar carregar o alias imediatamente
        os.system(f'su - {sudo_user} -c "source {bashrc_path}"')
        
        print_status("\nAlias 'bot' criado com sucesso!", "success")
        print("Agora você pode usar o comando 'bot' para abrir o menu.")
        print("Se o comando não funcionar imediatamente, feche e abra o terminal")
        print("ou execute: source ~/.bashrc")
    except Exception as e:
        print_status(f"\nNão foi possível criar o alias: {e}", "warning")
        print("Você pode criar manualmente com o comando:")
        print(f'echo \'alias bot="sudo python3 {script_path} menu"\' >> ~/.bashrc')
        print("E depois execute: source ~/.bashrc")

def main():
    if os.geteuid() != 0:
        print_status("Este script precisa ser executado como root (sudo)!", "error")
        sys.exit(1)

    # Limpar a tela
    os.system('clear' if os.name == 'posix' else 'cls')
    
    print_banner()
    print_status("\nIniciando instalação do BOT-T-Terminal...", "info")
    
    # Verificar instalação e obter tipo de instalação
    install_type = verificar_instalacao()
    
    # Instalar dependências
    if not instalar_dependencias(install_type):
        print_status("Tentando métodos alternativos...", "warning")
        # Se Python falhar, tentar Node.js
        if install_type.endswith("install"):  # É um comando pip
            print_status("Tentando com Node.js...", "info")
            if executar_comando("curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && apt-get install -y nodejs").returncode == 0:
                if instalar_dependencias("node"):
                    install_type = "node"
        
        # Se ainda falhar, tentar Go
        if install_type != "node":
            print_status("Tentando com Go...", "info")
            if executar_comando("apt-get update && apt-get install -y golang-go").returncode == 0:
                if instalar_dependencias("go"):
                    install_type = "go"
    
    # Configurar bot
    config = configurar_bot()
    
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
    
    # Criar alias para o comando bot
    criar_alias()
    
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
    print("4. Digite 'bot' no terminal para abrir o menu de gerenciamento")
    
    print_status("\nGerenciamento do serviço:", "info")
    print("- Use o comando 'bot' para acessar todas as funções")
    print("- Ou use os comandos tradicionais:")
    print("  • Verificar status: sudo systemctl status telegram-terminal-bot")
    print("  • Ver logs: sudo journalctl -u telegram-terminal-bot -f")
    print("  • Reiniciar: sudo systemctl restart telegram-terminal-bot")
    print("  • Parar: sudo systemctl stop telegram-terminal-bot")
    
    print_status("\nIMPORTANTE:", "warning")
    print("- O bot está configurado para iniciar automaticamente com o servidor")
    print("- Todos os comandos serão executados com privilégios root")
    print("- Mantenha o arquivo config.json seguro e com permissões restritas")
    print(f"- Após {config['tentativas_maximas']} tentativas falhas, usuários serão bloqueados")
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
    if len(sys.argv) > 1 and sys.argv[1] == "menu":
        if os.geteuid() != 0:
            print_status("Este comando precisa ser executado como root (sudo)!", "error")
            sys.exit(1)
        mostrar_menu()
    else:
        main() 