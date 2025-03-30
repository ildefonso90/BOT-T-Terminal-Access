# 🤖 BOT-T-Terminal

Bot do Telegram para controle remoto de servidores Linux via terminal.

## 📋 Características

- Execução de comandos remotamente
- Monitoramento de recursos (CPU, memória, disco, rede)
- Lista de processos em execução
- Sistema de autorização e bloqueio de usuários
- Interface amigável com emojis e formatação
- Disponível em múltiplas linguagens:
  - Python 🐍
  - Node.js 💚
  - Go 🦫

## 🚀 Instalação

1. Clone o repositório:
```bash
git clone https://github.com/ildefonso090/BOT-T-Terminal.git
cd BOT-T-Terminal
```

2. Execute o instalador:
```bash
sudo python3 install.py
```

O instalador irá:
- Verificar os requisitos do sistema
- Instalar dependências necessárias
- Tentar instalar o bot em múltiplas linguagens
- Configurar o token e usuários autorizados
- Criar um serviço systemd
- Criar um alias para fácil acesso

## ⚙️ Configuração

O bot usa um arquivo `config.json` com a seguinte estrutura:
```json
{
    "token": "SEU_TOKEN_AQUI",
    "dono_username": "SEU_USERNAME",
    "ids_autorizados": [123456789],
    "usuarios_bloqueados": [],
    "tentativas_maximas": 3
}
```

Para obter o token:
1. Abra o Telegram e procure por @BotFather
2. Envie /newbot e siga as instruções
3. Copie o token gerado

Para obter seu ID:
1. Abra o Telegram e procure por @userinfobot
2. Envie qualquer mensagem para ver seu ID

## 📱 Uso

Após a instalação, você pode:

1. Usar o menu de gerenciamento:
```bash
bot
```

2. Gerenciar o serviço manualmente:
```bash
sudo systemctl start telegram-terminal-bot
sudo systemctl stop telegram-terminal-bot
sudo systemctl restart telegram-terminal-bot
sudo systemctl status telegram-terminal-bot
```

3. Ver logs:
```bash
sudo journalctl -u telegram-terminal-bot -f
```

### Comandos do Bot

- `/start` - Mostra mensagem de boas-vindas
- `/cmd` - Executa comando no servidor
- `/status` - Ver status do servidor
- `/processos` - Listar processos
- `/memoria` - Ver uso de memória
- `/disco` - Ver uso do disco
- `/rede` - Ver informações de rede
- `/ajuda` - Mostra ajuda

## 🔒 Segurança

- Apenas usuários autorizados podem usar o bot
- Sistema de bloqueio após tentativas falhas
- Execução como root para acesso total
- Comunicação criptografada via Telegram
- Token armazenado localmente

## 🔧 Manutenção

- Use o menu de gerenciamento para:
  - Iniciar/parar/reiniciar o bot
  - Ver status e logs
  - Gerenciar usuários autorizados
  - Atualizar configurações

- Faça backups regulares do `config.json`
- Monitore os logs para detectar problemas
- Mantenha o sistema e dependências atualizados

## 📁 Estrutura

```
BOT-T-Terminal/
├── install.py           # Script de instalação
├── config.json          # Configurações do bot
├── requirements.txt     # Dependências Python
├── package.json         # Dependências Node.js
├── go.mod              # Dependências Go
├── telegram_terminal_bot.py   # Versão Python
├── telegram_terminal_bot.js   # Versão Node.js
├── telegram_terminal_bot.go   # Versão Go
└── README.md           # Este arquivo
```

## 👤 Autor

JOAC (Ildefonso)
- GitHub: [@ildefonso090](https://github.com/ildefonso090)
- Email: [ildefonso090@gmail.com](mailto:ildefonso090@gmail.com)

## 📄 Licença

Este projeto está licenciado sob a MIT License. 