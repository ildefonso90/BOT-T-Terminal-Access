# 🤖 BOT-T-Terminal

Bot do Telegram para monitoramento e controle remoto de servidores Linux.

## 📋 Características

### 1. 🖥️ Monitoramento em Tempo Real
* CPU, RAM e Disco com alertas automáticos
* Temperatura do sistema (quando disponível)
* Lista de processos ativos
* Uptime e carga do sistema
* Monitoramento de serviços

### 2. 🌐 Rede
* Status das interfaces
* Velocidade de conexão (Speed Test)
* IP público e interfaces
* Conexões ativas
* Tráfego de rede

### 3. 👥 Gerenciamento de Usuários
* Lista de usuários conectados
* Histórico de logins
* Localização geográfica dos acessos
* Gerenciamento de permissões
* Controle de acesso SSH

### 4. 🔒 Segurança
* Firewall (iptables/ufw)
* Fail2Ban
* Logs de segurança
* Escaneamento de vulnerabilidades
* Monitoramento de tentativas de acesso

### 5. 🔔 Sistema de Alertas
* CPU acima de 80%
* RAM acima de 80%
* Disco acima de 85%
* Processos consumindo muitos recursos
* Novos usuários conectados
* Localização dos IPs de acesso
* Falhas de serviços

### 6. 📊 Logs e Relatórios
* Logs do sistema
* Logs de segurança
* Logs de aplicações web
* Logs personalizados
* Histórico de comandos

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
* ✅ Verificar requisitos do sistema
* 📦 Instalar dependências necessárias
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
    "alertas": {
        "limite_cpu": 80,
        "limite_ram": 80,
        "limite_disco": 85,
        "limite_processo_cpu": 50,
        "limite_processo_ram": 50,
        "intervalo_monitoramento": 60
    },
    "notificacoes": {
        "cpu": true,
        "ram": true,
        "disco": true,
        "processos": true,
        "usuarios": true,
        "servicos": true
    }
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
sudo bot
```

### Comandos do Bot
* `/start` - Menu principal com botões
* `/cmd` - Executa comando no servidor

### Menus Disponíveis
* 📊 **Sistema**: Status, processos, disco, memória
* 👥 **Usuários**: Gerenciamento de usuários e SSH
* 🔧 **Serviços**: Status e controle de serviços
* 🔒 **Segurança**: Firewall, Fail2Ban, scans
* 🌐 **Rede**: Status, conexões, interfaces, speed test
* 📝 **Logs**: Sistema, segurança, web, aplicação

### Speed Test
* Teste de velocidade da conexão
* Download, Upload e Latência
* Resultados formatados

### Sistema de Alertas
* Monitoramento automático
* Alertas em tempo real
* Localização de IPs
* Notificações personalizáveis

## 🔒 Segurança
* 👥 Autenticação por ID do Telegram
* 🔐 Comunicação criptografada
* 📝 Logs detalhados
* 🛡️ Proteção contra comandos maliciosos

## 🛠️ Manutenção

### Comandos Úteis
```bash
# Iniciar/Parar/Reiniciar
sudo systemctl start telegram-terminal-bot
sudo systemctl stop telegram-terminal-bot
sudo systemctl restart telegram-terminal-bot

# Ver Status
sudo systemctl status telegram-terminal-bot

# Ver Logs
sudo journalctl -u telegram-terminal-bot -f
```

### Resolução de Problemas

#### Dependências Python
Se você encontrar erros relacionados a módulos Python faltantes, você pode instalá-los manualmente:

```bash
# Ative o ambiente virtual
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt

# Ou instale individualmente
pip install python-telegram-bot==20.8
pip install psutil==5.9.8
pip install requests==2.31.0
pip install speedtest-cli==2.1.3
pip install aiohttp==3.9.3
pip install asyncio==3.4.3
pip install python-dateutil==2.8.2
```

#### Problemas Comuns

1. **ModuleNotFoundError: No module named 'requests'**
   ```bash
   sudo apt update
   sudo apt install python3-pip
   sudo pip3 install requests
   ```

2. **Erro de Permissão**
   ```bash
   # Certifique-se de que o diretório do bot tem as permissões corretas
   sudo chown -R root:root /root/BOT-T-Terminal-Access
   sudo chmod -R 755 /root/BOT-T-Terminal-Access
   ```

3. **Serviço não Inicia**
   ```bash
   # Verifique os logs do serviço
   sudo journalctl -u telegram-terminal-bot -n 50 --no-pager
   
   # Reinicie o serviço
   sudo systemctl daemon-reload
   sudo systemctl restart telegram-terminal-bot
   ```

4. **Ambiente Virtual não Encontrado**
   ```bash
   # Recrie o ambiente virtual
   sudo python3 install.py
   ```

### Desinstalação
```bash
sudo bot
# Escolha opção 8 (Desinstalar bot)
```

## 📁 Estrutura
```
BOT-T-Terminal-Access/
├── install.py          # Instalador
├── config.json         # Configurações
├── requirements.txt    # Dependências
└── telegram_terminal_bot.py  # Bot principal
```

## 👤 Autor
JOAC (Ildefonso)
* 🌐 GitHub: [@ildefonso90](https://github.com/ildefonso90)
* 📧 Email: ildefonso90@gmail.com

## 📄 Licença
Este projeto está licenciado sob a [MIT License](LICENSE). 