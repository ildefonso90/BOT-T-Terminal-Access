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

def print_banner():
    print(f"""{Cores.BLUE}
╔══════════════════════════════════════════╗
║     🤖 BOT-T-Terminal - Instalação       ║ 
║                                          ║
║  Bot do Telegram para controle remoto    ║
║  de servidores Linux via terminal        ║
║                                          ║
║  Autor: JOAC                            ║
║  Versão: 1.0.0                          ║
╚══════════════════════════════════════════╝{Cores.END}
    """)

def verificar_root():
    if os.geteuid() != 0:
        print(f"{Cores.FAIL}❌ Este script precisa ser executado como root (sudo){Cores.END}")
        sys.exit(1)

def verificar_sistema():
    sistema = platform.system().lower()
    if sistema != "linux":
        print(f"{Cores.FAIL}❌ Este bot só funciona em sistemas Linux{Cores.END}")
        sys.exit(1)

def instalar_dependencias_sistema():
    print(f"\n{Cores.HEADER}📦 Instalando dependências do sistema...{Cores.END}")
    
    # Detectar gerenciador de pacotes
    if shutil.which("apt"):
        pkg_manager = "apt"
    elif shutil.which("yum"):
        pkg_manager = "yum"
    elif shutil.which("dnf"):
        pkg_manager = "dnf"
    else:
        print(f"{Cores.WARNING}⚠️ Gerenciador de pacotes não suportado. Tentando continuar...{Cores.END}")
        return

    # Instalar dependências comuns
    deps = ["git", "curl", "python3", "python3-pip", "nodejs", "npm", "golang"]
    
    try:
        if pkg_manager == "apt":
            subprocess.run(["apt", "update"], check=True)
            
        for dep in deps:
            try:
                subprocess.run([pkg_manager, "install", "-y", dep], check=True)
            except:
                print(f"{Cores.WARNING}⚠️ Erro ao instalar {dep}. Continuando...{Cores.END}")
                
    except Exception as e:
        print(f"{Cores.WARNING}⚠️ Erro ao instalar dependências: {e}{Cores.END}")

def instalar_dependencias_python():
    print(f"\n{Cores.HEADER}📦 Instalando dependências Python...{Cores.END}")
    
    try:
        # Atualizar pip
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "setuptools", "wheel"], check=True)
        
        # Instalar dependências do requirements.txt
        if os.path.exists("requirements.txt"):
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        else:
            subprocess.run([sys.executable, "-m", "pip", "install", "python-telegram-bot==20.8", "psutil==5.9.8"], check=True)
            
    except Exception as e:
        print(f"{Cores.WARNING}⚠️ Erro ao instalar dependências Python: {e}{Cores.END}")
        return False
        
    return True

def instalar_dependencias_nodejs():
    print(f"\n{Cores.HEADER}📦 Instalando dependências Node.js...{Cores.END}")
    
    try:
        # Instalar dependências
        subprocess.run(["npm", "install", "node-telegram-bot-api", "systeminformation"], check=True)
        return True
    except Exception as e:
        print(f"{Cores.WARNING}⚠️ Erro ao instalar dependências Node.js: {e}{Cores.END}")
        return False

def instalar_dependencias_go():
    print(f"\n{Cores.HEADER}📦 Instalando dependências Go...{Cores.END}")
    
    try:
        # Instalar dependências
        subprocess.run(["go", "mod", "download"], check=True)
        subprocess.run(["go", "build", "-o", "bot"], check=True)
        return True
    except Exception as e:
        print(f"{Cores.WARNING}⚠️ Erro ao instalar dependências Go: {e}{Cores.END}")
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
    
    if os.path.exists("config.json"):
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
        except:
            pass
    
    # Solicitar token se não existir
    if not config["token"]:
        print(f"\n{Cores.BLUE}Para obter o token do bot:{Cores.END}")
        print("1. Abra o Telegram e procure por @BotFather")
        print("2. Envie /newbot e siga as instruções")
        print("3. Copie o token gerado")
        config["token"] = input("\nToken do bot: ").strip()
    
    # Solicitar username do dono se não existir
    if not config["dono_username"]:
        print(f"\n{Cores.BLUE}Para obter seu ID do Telegram:{Cores.END}")
        print("1. Abra o Telegram e procure por @userinfobot")
        print("2. Envie qualquer mensagem para ver seu ID")
        config["dono_username"] = input("\nSeu username do Telegram (sem @): ").strip()
        dono_id = input("Seu ID do Telegram: ").strip()
        try:
            dono_id = int(dono_id)
            if dono_id not in config["ids_autorizados"]:
                config["ids_autorizados"].append(dono_id)
        except:
            print(f"{Cores.WARNING}⚠️ ID inválido{Cores.END}")
    
    # Salvar configuração
    with open("config.json", "w") as f:
        json.dump(config, f, indent=4)
    
    print(f"\n{Cores.GREEN}✅ Configuração salva!{Cores.END}")

def criar_servico():
    print(f"\n{Cores.HEADER}🔧 Criando serviço...{Cores.END}")
    
    # Detectar qual versão do bot está disponível
    if os.path.exists("telegram_terminal_bot.py"):
        bot_cmd = f"{sys.executable} {os.path.abspath('telegram_terminal_bot.py')}"
        print(f"{Cores.BLUE}ℹ️ Usando versão Python{Cores.END}")
    elif os.path.exists("telegram_terminal_bot.js"):
        bot_cmd = f"node {os.path.abspath('telegram_terminal_bot.js')}"
        print(f"{Cores.BLUE}ℹ️ Usando versão Node.js{Cores.END}")
    elif os.path.exists("bot"):
        bot_cmd = os.path.abspath("bot")
        print(f"{Cores.BLUE}ℹ️ Usando versão Go{Cores.END}")
    else:
        print(f"{Cores.FAIL}❌ Nenhuma versão do bot encontrada{Cores.END}")
        return False
    
    service = f"""[Unit]
Description=BOT-T-Terminal - Bot do Telegram para controle remoto
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={os.getcwd()}
ExecStart={bot_cmd}
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""

    # Criar arquivo do serviço
    service_path = "/etc/systemd/system/telegram-terminal-bot.service"
    with open(service_path, "w") as f:
        f.write(service)

    # Recarregar daemon e habilitar serviço
    try:
        subprocess.run(["systemctl", "daemon-reload"], check=True)
        subprocess.run(["systemctl", "enable", "telegram-terminal-bot"], check=True)
        subprocess.run(["systemctl", "start", "telegram-terminal-bot"], check=True)
        print(f"{Cores.GREEN}✅ Serviço criado e iniciado!{Cores.END}")
        return True
    except Exception as e:
        print(f"{Cores.FAIL}❌ Erro ao criar serviço: {e}{Cores.END}")
        return False

def criar_alias():
    print(f"\n{Cores.HEADER}🔧 Criando alias...{Cores.END}")
    
    try:
        # Obter caminho absoluto do script
        script_path = os.path.abspath(__file__)
        
        # Obter caminho do .bashrc do usuário que executou com sudo
        sudo_user = os.environ.get("SUDO_USER", os.environ.get("USER"))
        bashrc_path = os.path.expanduser(f"~{sudo_user}/.bashrc")
        
        # Verificar se o alias já existe
        with open(bashrc_path, "r") as f:
            if f"alias bot=" in f.read():
                print(f"{Cores.BLUE}ℹ️ Alias 'bot' já existe{Cores.END}")
                return True
        
        # Adicionar alias
        with open(bashrc_path, "a") as f:
            f.write(f'\nalias bot="sudo python3 {script_path} menu"\n')
        
        # Tentar carregar o alias
        try:
            os.system(f"su - {sudo_user} -c 'source {bashrc_path}'")
        except:
            pass
            
        print(f"{Cores.GREEN}✅ Alias 'bot' criado! Use 'source ~/.bashrc' para ativar.{Cores.END}")
        return True
        
    except Exception as e:
        print(f"{Cores.WARNING}⚠️ Erro ao criar alias: {e}{Cores.END}")
        print(f"{Cores.BLUE}ℹ️ Você pode criar manualmente adicionando a seguinte linha ao seu .bashrc:{Cores.END}")
        print(f"alias bot=\"sudo python3 {os.path.abspath(__file__)} menu\"")
        return False

def mostrar_menu():
    while True:
        print(f"""\n{Cores.HEADER}🤖 BOT-T-Terminal - Menu{Cores.END}

{Cores.BLUE}1. 🚀 Iniciar bot
2. 🛑 Parar bot
3. 🔄 Reiniciar bot
4. 📊 Status do bot
5. 📝 Ver logs
6. 👥 Gerenciar usuários
7. ⚙️ Configurações
8. ❌ Sair{Cores.END}
""")
        
        opcao = input("Escolha uma opção: ").strip()
        
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
            print(f"{Cores.BLUE}ℹ️ Reinicie o bot para aplicar as alterações{Cores.END}")
            
        elif opcao == "8":
            print(f"{Cores.GREEN}👋 Até mais!{Cores.END}")
            break
            
        else:
            print(f"{Cores.WARNING}⚠️ Opção inválida{Cores.END}")

def gerenciar_usuarios():
    while True:
        # Carregar configuração atual
        with open("config.json", "r") as f:
            config = json.load(f)
        
        print(f"""\n{Cores.HEADER}👥 Gerenciar Usuários{Cores.END}

{Cores.BLUE}Usuários autorizados:{Cores.END}""")
        for id in config["ids_autorizados"]:
            print(f"• {id}")
            
        print(f"\n{Cores.BLUE}Usuários bloqueados:{Cores.END}")
        for id in config["usuarios_bloqueados"]:
            print(f"• {id}")
            
        print(f"""\n{Cores.BLUE}1. ➕ Adicionar usuário
2. ➖ Remover usuário
3. 🔒 Bloquear usuário
4. 🔓 Desbloquear usuário
5. ↩️ Voltar{Cores.END}
""")
        
        opcao = input("Escolha uma opção: ").strip()
        
        if opcao == "1":
            id = input("ID do usuário: ").strip()
            try:
                id = int(id)
                if id not in config["ids_autorizados"]:
                    config["ids_autorizados"].append(id)
                    with open("config.json", "w") as f:
                        json.dump(config, f, indent=4)
                    print(f"{Cores.GREEN}✅ Usuário adicionado!{Cores.END}")
                else:
                    print(f"{Cores.WARNING}⚠️ Usuário já autorizado{Cores.END}")
            except:
                print(f"{Cores.FAIL}❌ ID inválido{Cores.END}")
                
        elif opcao == "2":
            id = input("ID do usuário: ").strip()
            try:
                id = int(id)
                if id in config["ids_autorizados"]:
                    config["ids_autorizados"].remove(id)
                    with open("config.json", "w") as f:
                        json.dump(config, f, indent=4)
                    print(f"{Cores.GREEN}✅ Usuário removido!{Cores.END}")
                else:
                    print(f"{Cores.WARNING}⚠️ Usuário não encontrado{Cores.END}")
            except:
                print(f"{Cores.FAIL}❌ ID inválido{Cores.END}")
                
        elif opcao == "3":
            id = input("ID do usuário: ").strip()
            try:
                id = int(id)
                if id not in config["usuarios_bloqueados"]:
                    config["usuarios_bloqueados"].append(id)
                    with open("config.json", "w") as f:
                        json.dump(config, f, indent=4)
                    print(f"{Cores.GREEN}✅ Usuário bloqueado!{Cores.END}")
                else:
                    print(f"{Cores.WARNING}⚠️ Usuário já bloqueado{Cores.END}")
            except:
                print(f"{Cores.FAIL}❌ ID inválido{Cores.END}")
                
        elif opcao == "4":
            id = input("ID do usuário: ").strip()
            try:
                id = int(id)
                if id in config["usuarios_bloqueados"]:
                    config["usuarios_bloqueados"].remove(id)
                    with open("config.json", "w") as f:
                        json.dump(config, f, indent=4)
                    print(f"{Cores.GREEN}✅ Usuário desbloqueado!{Cores.END}")
                else:
                    print(f"{Cores.WARNING}⚠️ Usuário não encontrado{Cores.END}")
            except:
                print(f"{Cores.FAIL}❌ ID inválido{Cores.END}")
                
        elif opcao == "5":
            break
            
        else:
            print(f"{Cores.WARNING}⚠️ Opção inválida{Cores.END}")

def main():
    # Se o argumento for "menu", mostrar menu de gerenciamento
    if len(sys.argv) > 1 and sys.argv[1] == "menu":
        verificar_root()
        mostrar_menu()
        return

    print_banner()
    verificar_root()
    verificar_sistema()
    
    # Instalar dependências do sistema
    instalar_dependencias_sistema()
    
    # Tentar instalar em cada linguagem
    python_ok = instalar_dependencias_python()
    nodejs_ok = instalar_dependencias_nodejs()
    go_ok = instalar_dependencias_go()
    
    if not (python_ok or nodejs_ok or go_ok):
        print(f"{Cores.FAIL}❌ Nenhuma versão do bot pôde ser instalada{Cores.END}")
        sys.exit(1)
    
    # Configurar bot
    configurar_bot()
    
    # Criar serviço
    if criar_servico():
        # Criar alias
        criar_alias()
        
        print(f"""
{Cores.GREEN}✅ Instalação concluída!

Para gerenciar o bot, use:
• {Cores.BOLD}bot{Cores.END}{Cores.GREEN} - Menu de gerenciamento
• {Cores.BOLD}systemctl status telegram-terminal-bot{Cores.END}{Cores.GREEN} - Ver status
• {Cores.BOLD}journalctl -u telegram-terminal-bot -f{Cores.END}{Cores.GREEN} - Ver logs

Não se esqueça de:
1. Executar 'source ~/.bashrc' para ativar o alias
2. Iniciar uma conversa com o bot no Telegram
3. Verificar os logs para garantir que está funcionando

Divirta-se! 🚀{Cores.END}""")
    else:
        print(f"{Cores.FAIL}❌ Erro ao finalizar instalação{Cores.END}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Cores.WARNING}⚠️ Instalação cancelada{Cores.END}")
        sys.exit(1) 