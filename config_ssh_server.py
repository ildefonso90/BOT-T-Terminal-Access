#!/usr/bin/env python3
import os
import subprocess
import sys
import time
from typing import Optional

def verificar_privilegios_root():
    """Verifica se o script está sendo executado com privilégios de root."""
    if os.geteuid() != 0:
        print("Este script precisa ser executado como root (sudo)")
        sys.exit(1)

def executar_comando(comando: str) -> tuple[bool, str]:
    """Executa um comando e retorna o resultado."""
    try:
        resultado = subprocess.run(comando, shell=True, capture_output=True, text=True)
        return resultado.returncode == 0, resultado.stdout
    except Exception as e:
        return False, str(e)

def configurar_ssh():
    """Configura o servidor SSH para aceitar autenticação por senha e login root."""
    print("Iniciando configuração do servidor SSH...")
    
    # Backup do arquivo de configuração SSH
    backup_cmd = "cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup"
    sucesso, output = executar_comando(backup_cmd)
    if not sucesso:
        print(f"Erro ao fazer backup: {output}")
        return False
    
    # Configurações para permitir autenticação por senha
    configs = [
        "PermitRootLogin yes",
        "PasswordAuthentication yes",
        "PermitEmptyPasswords no",
        "X11Forwarding yes",
        "UsePAM yes"
    ]
    
    # Aplicar configurações
    for config in configs:
        comando = f"sed -i 's/#{config}/{config}/g' /etc/ssh/sshd_config"
        sucesso, output = executar_comando(comando)
        if not sucesso:
            print(f"Erro ao configurar {config}: {output}")
            return False
    
    # Reiniciar o serviço SSH
    print("Reiniciando o serviço SSH...")
    sucesso, output = executar_comando("systemctl restart sshd")
    if not sucesso:
        print(f"Erro ao reiniciar o serviço SSH: {output}")
        return False
    
    return True

def configurar_senha_root(senha: Optional[str] = None):
    """Configura a senha do usuário root."""
    if not senha:
        senha = input("Digite a nova senha para o usuário root: ")
    
    comando = f"echo 'root:{senha}' | chpasswd"
    sucesso, output = executar_comando(comando)
    
    if sucesso:
        print("Senha do root configurada com sucesso!")
    else:
        print(f"Erro ao configurar senha do root: {output}")

def main():
    """Função principal do script."""
    print("=== Configurador de Servidor SSH ===")
    
    # Verificar privilégios de root
    verificar_privilegios_root()
    
    # Configurar SSH
    if configurar_ssh():
        print("Configuração do SSH concluída com sucesso!")
    else:
        print("Erro ao configurar o SSH")
        return
    
    # Configurar senha do root
    configurar_senha_root()
    
    print("\nConfiguração concluída! O servidor SSH está pronto para:")
    print("- Aceitar conexões com autenticação por senha")
    print("- Permitir login do usuário root")
    print("- Usar autenticação PAM")
    print("- Permitir forwarding X11")
    
    print("\nIMPORTANTE: Mantenha o arquivo de backup em /etc/ssh/sshd_config.backup")

if __name__ == "__main__":
    main() 