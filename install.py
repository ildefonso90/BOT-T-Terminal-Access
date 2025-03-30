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
    
    if is_debian_based():
        print(f"{Cores.GREEN}📌 Sistema baseado em Debian detectado, usando apt...{Cores.END}")
        try:
            # Atualiza os repositórios
            subprocess.run(["apt", "update"], check=True)
            
            # Instala as dependências via apt
            subprocess.run([
                "apt", "install", "-y",
                "python3-psutil",
                "python3-telegram-bot"
            ], check=True)
            
            print(f"{Cores.GREEN}✅ Dependências instaladas com sucesso via apt{Cores.END}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"{Cores.FAIL}❌ Erro ao instalar dependências via apt: {e}{Cores.END}")
            return False
    else:
        print(f"{Cores.GREEN}📌 Usando pip para instalar dependências...{Cores.END}")
        try:
            # Atualiza pip
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)
            
            # Instala as dependências via pip
            subprocess.run([
                sys.executable, "-m", "pip", "install",
                "python-telegram-bot==20.8",
                "psutil==5.9.8"
            ], check=True)
            
            print(f"{Cores.GREEN}✅ Dependências instaladas com sucesso via pip{Cores.END}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"{Cores.FAIL}❌ Erro ao instalar dependências via pip: {e}{Cores.END}")
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
ExecStart=/usr/bin/python3 {os.path.join(os.getcwd(), "telegram_terminal_bot.py")}
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

def menu_interativo():
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
        
        try:
            opcao = input("Escolha uma opção: ").strip()
            
            if opcao == "1":
                subprocess.run(["systemctl", "start", "telegram-terminal-bot"])
            elif opcao == "2":
                subprocess.run(["systemctl", "stop", "telegram-terminal-bot"])
            elif opcao == "3":
                subprocess.run(["systemctl", "restart", "telegram-terminal-bot"])
            elif opcao == "4":
                subprocess.run(["systemctl", "status", "telegram-terminal-bot"])
            elif opcao == "5":
                subprocess.run(["journalctl", "-u", "telegram-terminal-bot", "-f"])
            elif opcao == "6":
                gerenciar_usuarios()
            elif opcao == "7":
                configurar_bot()
                subprocess.run(["systemctl", "restart", "telegram-terminal-bot"])
            elif opcao == "8":
                print(f"{Cores.GREEN}👋 Até logo!{Cores.END}")
                break
            else:
                print(f"{Cores.WARNING}⚠️ Opção inválida{Cores.END}")
                
        except KeyboardInterrupt:
            print(f"\n{Cores.WARNING}⚠️ Instalação cancelada{Cores.END}")
            break
        except Exception as e:
            print(f"\n{Cores.FAIL}❌ Erro: {e}{Cores.END}")

def gerenciar_usuarios():
    try:
        # Carrega a configuração atual
        with open("config.json", "r") as f:
            config = json.load(f)
        
        while True:
            print(f"""\n{Cores.HEADER}👥 Gerenciar Usuários{Cores.END}

{Cores.BLUE}1. 📃 Listar usuários autorizados{Cores.END}
2. ➕ Adicionar usuário
3. ➖ Remover usuário
4. 🔒 Ver usuários bloqueados
5. 🔄 Desbloquear usuário
6. ↩️ Voltar{Cores.END}
""")
            
            opcao = input("Escolha uma opção: ").strip()
            
            if opcao == "1":
                print(f"\n{Cores.BLUE}📃 Usuários autorizados:{Cores.END}")
                for id_user in config["ids_autorizados"]:
                    print(f"- {id_user}")
                    
            elif opcao == "2":
                try:
                    novo_id = int(input(f"{Cores.BLUE}🆔 Digite o ID do usuário: {Cores.END}").strip())
                    if novo_id not in config["ids_autorizados"]:
                        config["ids_autorizados"].append(novo_id)
                        print(f"{Cores.GREEN}✅ Usuário adicionado!{Cores.END}")
                    else:
                        print(f"{Cores.WARNING}⚠️ Usuário já autorizado!{Cores.END}")
                except ValueError:
                    print(f"{Cores.FAIL}❌ ID inválido!{Cores.END}")
                    
            elif opcao == "3":
                try:
                    remover_id = int(input(f"{Cores.BLUE}🆔 Digite o ID do usuário: {Cores.END}").strip())
                    if remover_id in config["ids_autorizados"]:
                        config["ids_autorizados"].remove(remover_id)
                        print(f"{Cores.GREEN}✅ Usuário removido!{Cores.END}")
                    else:
                        print(f"{Cores.WARNING}⚠️ Usuário não encontrado!{Cores.END}")
                except ValueError:
                    print(f"{Cores.FAIL}❌ ID inválido!{Cores.END}")
                    
            elif opcao == "4":
                print(f"\n{Cores.BLUE}🔒 Usuários bloqueados:{Cores.END}")
                for id_user in config["usuarios_bloqueados"]:
                    print(f"- {id_user}")
                    
            elif opcao == "5":
                try:
                    desbloquear_id = int(input(f"{Cores.BLUE}🆔 Digite o ID do usuário: {Cores.END}").strip())
                    if desbloquear_id in config["usuarios_bloqueados"]:
                        config["usuarios_bloqueados"].remove(desbloquear_id)
                        print(f"{Cores.GREEN}✅ Usuário desbloqueado!{Cores.END}")
                    else:
                        print(f"{Cores.WARNING}⚠️ Usuário não está bloqueado!{Cores.END}")
                except ValueError:
                    print(f"{Cores.FAIL}❌ ID inválido!{Cores.END}")
                    
            elif opcao == "6":
                break
                
            else:
                print(f"{Cores.WARNING}⚠️ Opção inválida{Cores.END}")
            
            # Salva as alterações
            with open("config.json", "w") as f:
                json.dump(config, f, indent=4)
            
    except FileNotFoundError:
        print(f"{Cores.FAIL}❌ Arquivo config.json não encontrado!{Cores.END}")
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