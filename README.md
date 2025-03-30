# 🤖 BOT-T-Terminal-Access

Um bot do Telegram poderoso para controlar seu servidor Linux remotamente com privilégios root, desenvolvido em Python.

## ✨ Características

- 🔐 Sistema de autenticação baseado em username e ID do Telegram
- 👑 Sistema de dono único com privilégios especiais
- 🛡️ Sistema de bloqueio após tentativas falhas
- 📊 Interface interativa com botões e menus
- 🔄 Inicialização automática com o servidor
- 📝 Logs detalhados de todas as ações
- ⚡ Comandos rápidos pré-configurados
- 🖥️ Monitoramento do sistema em tempo real

## 📋 Pré-requisitos

- Python 3.7+
- Sistema Linux (testado em Ubuntu/Debian)
- Privilégios root
- Conexão com internet
- Bot do Telegram criado via @BotFather

## 🚀 Instalação

1. **Clone o repositório:**
```bash
git clone https://github.com/ildefonso90/BOT-T-Terminal-Access.git
cd BOT-T-Terminal-Access
```

2. **Execute o instalador:**
```bash
sudo python3 install.py
```

3. **Durante a instalação, você precisará:**
   - Token do bot do Telegram
   - Seu username do Telegram
   - ID do Telegram dos usuários autorizados

## 📱 Uso

1. **Iniciar o bot:**
   - O bot inicia automaticamente após a instalação
   - Reinicia automaticamente se o servidor for reiniciado

2. **Comandos básicos:**
   - `/start` - Inicia o bot e mostra o menu principal
   - `/help` - Mostra ajuda detalhada
   - `/status` - Mostra status do sistema
   - `/cmd <comando>` - Executa comando personalizado

3. **Comandos rápidos disponíveis:**
   - 📂 Listar arquivos
   - 💾 Uso do disco
   - 🔄 Uso da memória
   - ⚡ Uso da CPU
   - 📡 Conexões de rede
   - 🔍 Processos ativos
   - 👤 Usuário atual
   - 📅 Data e hora
   - 🌡️ Temperatura CPU
   - 🔒 Últimos logins

## ⚙️ Gerenciamento do Serviço

```bash
# Verificar status
sudo systemctl status telegram-terminal-bot

# Ver logs
sudo journalctl -u telegram-terminal-bot -f

# Reiniciar bot
sudo systemctl restart telegram-terminal-bot

# Parar bot
sudo systemctl stop telegram-terminal-bot
```

## 🔒 Segurança

- Apenas usuários autorizados podem usar o bot
- Sistema de bloqueio após 7 tentativas falhas
- Apenas o dono pode desbloquear usuários
- Todas as ações são registradas nos logs do sistema
- Permissões restritas nos arquivos de configuração
- Timeout em comandos longos (60 segundos)

## 📁 Estrutura do Projeto

```
BOT-T-Terminal-Access/
├── install.py           # Script de instalação
├── telegram_terminal_bot.py  # Código principal do bot
├── requirements.txt     # Dependências Python
├── config.json         # Configurações (gerado na instalação)
└── README.md           # Esta documentação
```

## ⚠️ Avisos Importantes

1. **Segurança:**
   - O bot tem acesso root ao servidor
   - Mantenha o arquivo config.json seguro
   - Monitore os logs regularmente
   - Use apenas em redes confiáveis

2. **Backup:**
   - Faça backup do arquivo config.json
   - Guarde o token do bot e IDs autorizados
   - Mantenha registro do username do dono

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 👤 Autor

JOAC (Ildefonso)
- GitHub: [@ildefonso90](https://github.com/ildefonso90)
- Email: ildefonso90@gmail.com 
