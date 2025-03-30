# 🤖 BOT-T-Terminal-Access

Bot do Telegram para controle remoto de servidores Linux via terminal.

## 📋 Características

* 🔐 Sistema de autorização e bloqueio de usuários
* 💻 Execução de comandos remotamente com timeout de 30 segundos
* 📊 Monitoramento em tempo real:
  * CPU e processos
  * Memória RAM e Swap
  * Uso de disco
  * Interfaces de rede
* 🎯 Interface amigável com botões e emojis
* 🔄 Disponível em múltiplas linguagens:
  * Python 🐍
  * Node.js 💚
  * Go 🦫

## 🚀 Instalação

1. Clone o repositório:
```bash
git clone https://github.com/ildefonso90/BOT-T-Terminal-Access.git
cd BOT-T-Terminal-Access
```

2. Execute o instalador:
```bash
sudo python3 install.py
```

O instalador irá:
* ✅ Verificar os requisitos do sistema
* 📦 Instalar dependências necessárias
* 🔄 Tentar instalar em múltiplas linguagens
* ⚙️ Configurar token e usuários
* 🛠️ Criar serviço systemd
* 🔗 Criar alias para fácil acesso

## ⚙️ Configuração

O bot usa um arquivo `config.json`:

```json
{
    "token": "SEU_TOKEN_AQUI",
    "dono_username": "SEU_USERNAME",
    "ids_autorizados": [123456789],
    "usuarios_bloqueados": [],
    "tentativas_maximas": 3
}
```

### 🔑 Obtendo o Token

1. Abra o Telegram e procure por @BotFather
2. Envie `/newbot` e siga as instruções
3. Copie o token gerado

### 🆔 Obtendo seu ID

1. Abra o Telegram e procure por @userinfobot
2. Envie qualquer mensagem para ver seu ID

## 📱 Uso

### Menu de Gerenciamento

```bash
bot
```

### Comandos Systemd

```bash
sudo systemctl start telegram-terminal-bot
sudo systemctl stop telegram-terminal-bot
sudo systemctl restart telegram-terminal-bot
sudo systemctl status telegram-terminal-bot
```

### Logs

```bash
sudo journalctl -u telegram-terminal-bot -f
```

### 🤖 Comandos do Bot

* `/start` - Menu principal com botões
* `/cmd` - Executa comando no servidor
* `/status` - Status detalhado do sistema
* `/processos` - Lista top 10 processos
* `/memoria` - Informações de RAM e Swap
* `/disco` - Uso de todas partições
* `/rede` - Status das interfaces
* `/ajuda` - Lista todos comandos

## 🔒 Segurança

* 👥 Sistema de autorização por ID
* 🚫 Bloqueio após tentativas falhas
* 🔑 Execução como root (sudo)
* 🔐 Comunicação criptografada
* ⏱️ Timeout em comandos longos
* 📝 Logs detalhados

## 🛠️ Manutenção

### Menu de Gerenciamento
* ▶️ Iniciar/parar/reiniciar bot
* 📊 Ver status e logs
* 👥 Gerenciar usuários
* ⚙️ Atualizar configurações

### Boas Práticas
* 💾 Backup regular do `config.json`
* 📋 Monitoramento de logs
* 🔄 Atualizações do sistema
* ⚡ Verificação de performance

## 📁 Estrutura

```
BOT-T-Terminal-Access/
├── install.py                # Instalador
├── config.json               # Configurações
├── requirements.txt          # Deps Python
├── package.json              # Deps Node.js
├── go.mod                    # Deps Go
├── telegram_terminal_bot.py  # Bot Python
├── telegram_terminal_bot.js  # Bot Node.js
├── telegram_terminal_bot.go  # Bot Go
└── README.md                # Documentação
```

## 👤 Autor

JOAC (Ildefonso)
* 🌐 GitHub: [@ildefonso90](https://github.com/ildefonso90)
* 📧 Email: ildefonso90@gmail.com

## 📄 Licença

Este projeto está licenciado sob a [MIT License](LICENSE). 