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

def instalar_dependencias():
    print(f"\n{Cores.HEADER}📦 Instalando dependências...{Cores.END}")
    
    try:
        # Instala python3-venv e python3-pip
        print(f"{Cores.BLUE}📌 Instalando requisitos básicos...{Cores.END}")
        subprocess.run(["apt", "update"], check=True)
        subprocess.run(["apt", "install", "-y", "python3-venv", "python3-pip", "python3-psutil"], check=True)
        
        # Cria e ativa ambiente virtual
        venv_path = os.path.join(os.getcwd(), "venv")
        print(f"{Cores.BLUE}📌 Criando ambiente virtual em {venv_path}...{Cores.END}")
        subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)
        
        # Paths do ambiente virtual
        pip_path = os.path.join(venv_path, "bin", "pip")
        python_path = os.path.join(venv_path, "bin", "python")
        
        # Atualiza pip no ambiente virtual
        print(f"{Cores.BLUE}📌 Atualizando pip...{Cores.END}")
        subprocess.run([pip_path, "install", "--upgrade", "pip"], check=True)
        
        # Instala as dependências no ambiente virtual
        print(f"{Cores.BLUE}📌 Instalando dependências Python...{Cores.END}")
        subprocess.run([
            pip_path, "install",
            "python-telegram-bot==20.8"
        ], check=True)
        
        # Atualiza o serviço para usar o Python do ambiente virtual
        global python_executable
        python_executable = python_path
        
        print(f"{Cores.GREEN}✅ Dependências instaladas com sucesso!{Cores.END}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"{Cores.FAIL}❌ Erro ao instalar dependências: {e}{Cores.END}")
        return False

def configurar_bot():
    print(f"\n{Cores.HEADER}⚙️ Configurando o bot...{Cores.END}")
    
    config = {
        "token": "",
        "dono_username": "",
        "ids_autorizados": [],
        "usuarios_bloqueados": [],
        "tentativas_maximas": 3
    }
    
    # Solicita o token
    while not config["token"]:
        print(f"{Cores.BLUE}🔑 Digite o token do bot (obtido do @BotFather): {Cores.END}")
        token = input().strip()
        if token:
            config["token"] = token
        else:
            print(f"{Cores.FAIL}❌ Token inválido!{Cores.END}")
    
    # Solicita o username
    while not config["dono_username"]:
        print(f"{Cores.BLUE}👤 Digite seu username do Telegram (sem @): {Cores.END}")
        username = input().strip()
        if username:
            config["dono_username"] = username.lower()
        else:
            print(f"{Cores.FAIL}❌ Username inválido!{Cores.END}")
    
    # Solicita o ID
    while not config["ids_autorizados"]:
        try:
            print(f"{Cores.BLUE}🆔 Digite seu ID do Telegram (use @userinfobot para descobrir): {Cores.END}")
            id_telegram = int(input().strip())
            config["ids_autorizados"].append(id_telegram)
        except ValueError:
            print(f"{Cores.FAIL}❌ ID inválido! Digite apenas números.{Cores.END}")
    
    # Salva a configuração
    with open("config.json", "w") as f:
        json.dump(config, f, indent=4)
    
    print(f"{Cores.GREEN}✅ Configuração salva com sucesso!{Cores.END}")

def criar_servico():
    print(f"\n{Cores.HEADER}🛠️ Criando serviço systemd...{Cores.END}")
    
    servico = f"""[Unit]
Description=BOT-T-Terminal - Bot do Telegram para controle remoto
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={os.getcwd()}
Environment="PYTHONPATH={os.getcwd()}/venv/lib/python3.*/site-packages"
ExecStart={python_executable} {os.path.join(os.getcwd(), "telegram_terminal_bot.py")}
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    # Salva o arquivo do serviço
    service_path = "/etc/systemd/system/telegram-terminal-bot.service"
    with open(service_path, "w") as f:
        f.write(servico)
    
    # Recarrega o systemd e habilita o serviço
    subprocess.run(["systemctl", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "enable", "telegram-terminal-bot"], check=True)
    
    print(f"{Cores.GREEN}✅ Serviço criado com sucesso!{Cores.END}")

def criar_alias():
    print(f"\n{Cores.HEADER}🔗 Criando alias para o menu...{Cores.END}")
    
    try:
        # Obtém o caminho absoluto do script
        script_path = os.path.abspath("install.py")
        
        # Obtém o caminho do .bashrc do usuário que executou o sudo
        sudo_user = os.environ.get("SUDO_USER", os.environ.get("USER"))
        bashrc_path = os.path.expanduser(f"~{sudo_user}/.bashrc")
        
        # Verifica se o alias já existe
        with open(bashrc_path, "r") as f:
            if f'alias bot="sudo python3 {script_path} menu"' in f.read():
                print(f"{Cores.BLUE}ℹ️ Alias 'bot' já existe!{Cores.END}")
                return
        
        # Adiciona o alias ao .bashrc
        with open(bashrc_path, "a") as f:
            f.write(f'\nalias bot="sudo python3 {script_path} menu"\n')
        
        # Tenta carregar o alias imediatamente
        try:
            os.system(f"su - {sudo_user} -c 'source {bashrc_path}'")
            print(f"{Cores.GREEN}✅ Alias 'bot' criado com sucesso!{Cores.END}")
            print(f"{Cores.BLUE}ℹ️ Use o comando 'bot' para abrir o menu{Cores.END}")
        except:
            print(f"{Cores.WARNING}⚠️ Alias criado, mas será necessário reiniciar o terminal{Cores.END}")
            
    except Exception as e:
        print(f"{Cores.FAIL}❌ Erro ao criar alias: {e}{Cores.END}")
        print(f"{Cores.BLUE}ℹ️ Você pode criar manualmente adicionando a linha abaixo ao seu .bashrc:{Cores.END}")
        print(f'alias bot="sudo python3 {script_path} menu"')

def desinstalar_bot():
    print(f"\n{Cores.HEADER}🗑️ Desinstalando BOT-T-Terminal...{Cores.END}")
    
    try:
        # Para o serviço
        print(f"{Cores.BLUE}📌 Parando serviço...{Cores.END}")
        subprocess.run(["systemctl", "stop", "telegram-terminal-bot"], check=False)
        
        # Remove o serviço
        print(f"{Cores.BLUE}📌 Removendo serviço...{Cores.END}")
        service_path = "/etc/systemd/system/telegram-terminal-bot.service"
        if os.path.exists(service_path):
            os.remove(service_path)
            subprocess.run(["systemctl", "daemon-reload"], check=False)
        
        # Remove ambiente virtual
        print(f"{Cores.BLUE}📌 Removendo ambiente virtual...{Cores.END}")
        venv_path = os.path.join(os.getcwd(), "venv")
        if os.path.exists(venv_path):
            shutil.rmtree(venv_path)
        
        # Remove arquivos de configuração
        print(f"{Cores.BLUE}📌 Removendo configurações...{Cores.END}")
        config_files = ["config.json"]
        for file in config_files:
            if os.path.exists(file):
                os.remove(file)
        
        # Remove alias do .bashrc
        print(f"{Cores.BLUE}📌 Removendo alias...{Cores.END}")
        sudo_user = os.environ.get("SUDO_USER", os.environ.get("USER"))
        bashrc_path = os.path.expanduser(f"~{sudo_user}/.bashrc")
        if os.path.exists(bashrc_path):
            with open(bashrc_path, "r") as f:
                lines = f.readlines()
            with open(bashrc_path, "w") as f:
                for line in lines:
                    if "alias bot=" not in line:
                        f.write(line)
        
        print(f"{Cores.GREEN}✅ Bot desinstalado com sucesso!{Cores.END}")
        print(f"{Cores.BLUE}ℹ️ Para remover completamente, delete a pasta do bot:{Cores.END}")
        print(f"{Cores.BLUE}   rm -rf {os.getcwd()}{Cores.END}")
        
        return True
    except Exception as e:
        print(f"{Cores.FAIL}❌ Erro ao desinstalar: {e}{Cores.END}")
        return False

def menu_interativo():
    # Verifica se é root
    if os.geteuid() != 0:
        print(f"{Cores.FAIL}❌ Execute o menu como root (sudo bot){Cores.END}")
        return

    while True:
        print(f"""\n{Cores.HEADER}🤖 BOT-T-Terminal - Menu{Cores.END}

{Cores.BLUE}1. 🚀 Iniciar bot
2. 🛑 Parar bot
3. 🔄 Reiniciar bot
4. 📊 Status do bot
5. 📝 Ver logs
6. 👥 Gerenciar usuários
7. ⚙️ Configurações
8. 🗑️ Desinstalar bot
9. ❌ Sair{Cores.END}
""")
        
        try:
            opcao = input(f"{Cores.BLUE}Escolha uma opção: {Cores.END}").strip()
            
            if opcao == "1":
                subprocess.run(["systemctl", "start", "telegram-terminal-bot"])
                print(f"{Cores.GREEN}✅ Bot iniciado!{Cores.END}")
            
            elif opcao == "2":
                subprocess.run(["systemctl", "stop", "telegram-terminal-bot"])
                print(f"{Cores.GREEN}✅ Bot parado!{Cores.END}")
            
            elif opcao == "3":
                subprocess.run(["systemctl", "restart", "telegram-terminal-bot"])
                print(f"{Cores.GREEN}✅ Bot reiniciado!{Cores.END}")
            
            elif opcao == "4":
                subprocess.run(["systemctl", "status", "telegram-terminal-bot"])
            
            elif opcao == "5":
                subprocess.run(["journalctl", "-u", "telegram-terminal-bot", "-f"])
            
            elif opcao == "6":
                gerenciar_usuarios()
            
            elif opcao == "7":
                configurar_bot()
            
            elif opcao == "8":
                confirmacao = input(f"{Cores.WARNING}⚠️ Tem certeza que deseja desinstalar o bot? (s/N): {Cores.END}").strip().lower()
                if confirmacao == "s":
                    if desinstalar_bot():
                        return
            
            elif opcao == "9":
                print(f"{Cores.GREEN}👋 Até logo!{Cores.END}")
                break
            
            else:
                print(f"{Cores.FAIL}❌ Opção inválida!{Cores.END}")
                
        except KeyboardInterrupt:
            print(f"\n{Cores.GREEN}👋 Até logo!{Cores.END}")
            break
        except Exception as e:
            print(f"{Cores.FAIL}❌ Erro: {e}{Cores.END}")

def gerenciar_usuarios():
    while True:
        print(f"""\n{Cores.HEADER}👥 Gerenciamento de Usuários{Cores.END}

{Cores.BLUE}1. 📋 Listar usuários autorizados
2. ➕ Adicionar usuário
3. ➖ Remover usuário
4. 🔙 Voltar{Cores.END}
""")
        
        try:
            opcao = input(f"{Cores.BLUE}Escolha uma opção: {Cores.END}").strip()
            
            if opcao == "1":
                with open("config.json", "r") as f:
                    config = json.load(f)
                print(f"\n{Cores.BLUE}📋 Usuários autorizados:{Cores.END}")
                for id_user in config["ids_autorizados"]:
                    print(f"  • {id_user}")
            
            elif opcao == "2":
                try:
                    id_novo = int(input(f"{Cores.BLUE}Digite o ID do usuário: {Cores.END}"))
                    with open("config.json", "r") as f:
                        config = json.load(f)
                    if id_novo not in config["ids_autorizados"]:
                        config["ids_autorizados"].append(id_novo)
                        with open("config.json", "w") as f:
                            json.dump(config, f, indent=4)
                        print(f"{Cores.GREEN}✅ Usuário adicionado!{Cores.END}")
                    else:
                        print(f"{Cores.WARNING}⚠️ Usuário já autorizado!{Cores.END}")
                except ValueError:
                    print(f"{Cores.FAIL}❌ ID inválido!{Cores.END}")
            
            elif opcao == "3":
                try:
                    id_remover = int(input(f"{Cores.BLUE}Digite o ID do usuário: {Cores.END}"))
                    with open("config.json", "r") as f:
                        config = json.load(f)
                    if id_remover in config["ids_autorizados"]:
                        config["ids_autorizados"].remove(id_remover)
                        with open("config.json", "w") as f:
                            json.dump(config, f, indent=4)
                        print(f"{Cores.GREEN}✅ Usuário removido!{Cores.END}")
                    else:
                        print(f"{Cores.WARNING}⚠️ Usuário não encontrado!{Cores.END}")
                except ValueError:
                    print(f"{Cores.FAIL}❌ ID inválido!{Cores.END}")
            
            elif opcao == "4":
                break
            
            else:
                print(f"{Cores.FAIL}❌ Opção inválida!{Cores.END}")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"{Cores.FAIL}❌ Erro: {e}{Cores.END}")

def main():
    try:
        # Se for chamado com argumento 'menu', abre o menu
        if len(sys.argv) > 1 and sys.argv[1] == "menu":
            verificar_root()
            menu_interativo()
            return
        
        # Instalação normal
        imprimir_banner()
        verificar_root()
        verificar_sistema()
        
        if not instalar_dependencias():
            print(f"{Cores.FAIL}❌ Falha ao instalar dependências!{Cores.END}")
            sys.exit(1)
        
        configurar_bot()
        criar_servico()
        criar_alias()
        
        # Inicia o bot
        print(f"\n{Cores.GREEN}🚀 Iniciando o bot...{Cores.END}")
        subprocess.run(["systemctl", "start", "telegram-terminal-bot"], check=True)
        
        print(f"""
{Cores.GREEN}✅ Instalação concluída com sucesso!

Para gerenciar o bot, use:
• {Cores.BOLD}bot{Cores.END}{Cores.GREEN} - Menu de gerenciamento
• {Cores.BOLD}systemctl status telegram-terminal-bot{Cores.END}{Cores.GREEN} - Ver status
• {Cores.BOLD}journalctl -u telegram-terminal-bot -f{Cores.END}{Cores.GREEN} - Ver logs

Não se esqueça de:
1. Executar 'source ~/.bashrc' para ativar o alias
2. Iniciar uma conversa com o bot no Telegram
3. Verificar os logs para garantir que está funcionando

Divirta-se! 🚀{Cores.END}""")
    except KeyboardInterrupt:
        print(f"\n{Cores.WARNING}⚠️ Instalação cancelada{Cores.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Cores.FAIL}❌ Erro: {e}{Cores.END}")
        sys.exit(1)

if __name__ == "__main__":
    main() 