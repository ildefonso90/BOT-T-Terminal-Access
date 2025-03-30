const TelegramBot = require('node-telegram-bot-api');
const si = require('systeminformation');
const fs = require('fs');
const { exec } = require('child_process');
const { promisify } = require('util');

const execAsync = promisify(exec);

// Carregar configuração
let config;
try {
    config = JSON.parse(fs.readFileSync('config.json', 'utf8'));
} catch (err) {
    console.error('❌ Erro ao carregar config.json:', err);
    process.exit(1);
}

// Inicializar bot
const bot = new TelegramBot(config.token, { polling: true });

// Mapa para armazenar tentativas de acesso
const tentativasFalhas = new Map();

// Verificar autorização
function verificarAutorizacao(msg) {
    const userId = msg.from.id;

    // Verificar se está bloqueado
    if (config.usuarios_bloqueados.includes(userId)) {
        bot.sendMessage(msg.chat.id, '❌ Você está bloqueado! Contate o administrador.');
        return false;
    }

    // Verificar se está autorizado
    if (!config.ids_autorizados.includes(userId)) {
        tentativasFalhas.set(userId, (tentativasFalhas.get(userId) || 0) + 1);
        
        if (tentativasFalhas.get(userId) >= config.tentativas_maximas) {
            config.usuarios_bloqueados.push(userId);
            fs.writeFileSync('config.json', JSON.stringify(config, null, 4));
            bot.sendMessage(msg.chat.id, '🚫 Muitas tentativas! Você foi bloqueado.');
        } else {
            bot.sendMessage(msg.chat.id, '⚠️ Você não está autorizado!');
        }
        return false;
    }

    return true;
}

// Comando /start
bot.onText(/\/start/, async (msg) => {
    if (!verificarAutorizacao(msg)) return;

    const mensagem = `🤖 *Bem-vindo ao BOT-T-Terminal!*

Este bot permite controlar seu servidor via Telegram.

*Comandos disponíveis:*
/cmd - Executar comando no servidor
/status - Ver status do servidor
/processos - Listar processos
/memoria - Ver uso de memória
/disco - Ver uso do disco
/rede - Ver informações de rede
/ajuda - Mostrar esta mensagem

*Observações:*
- Apenas usuários autorizados podem usar o bot
- Após ${config.tentativas_maximas} tentativas falhas, você será bloqueado
- Apenas o dono (@${config.dono_username}) pode desbloquear usuários

*Desenvolvido por:* JOAC
*Versão:* 1.0.0`;

    bot.sendMessage(msg.chat.id, mensagem, { parse_mode: 'Markdown' });
});

// Comando /cmd
bot.onText(/\/cmd (.+)/, async (msg, match) => {
    if (!verificarAutorizacao(msg)) return;

    const comando = match[1];
    
    try {
        const { stdout, stderr } = await execAsync(comando);
        const output = stdout || stderr;
        bot.sendMessage(msg.chat.id, `✅ Resultado:\n\`\`\`\n${output}\n\`\`\``, { parse_mode: 'Markdown' });
    } catch (err) {
        bot.sendMessage(msg.chat.id, `❌ Erro:\n${err.message}`);
    }
});

// Comando /status
bot.onText(/\/status/, async (msg) => {
    if (!verificarAutorizacao(msg)) return;

    try {
        const [cpu, mem, os] = await Promise.all([
            si.cpu(),
            si.mem(),
            si.osInfo()
        ]);

        const uptime = Math.floor(os.uptime / 3600);
        const mensagem = `📊 *Status do Servidor*

*Sistema:*
• OS: ${os.distro} ${os.release}
• Arch: ${os.arch}
• Uptime: ${uptime} horas

*CPU:*
• Modelo: ${cpu.manufacturer} ${cpu.brand}
• Cores: ${cpu.cores}
• Velocidade: ${cpu.speed} GHz

*Memória:*
• Total: ${(mem.total / (1024 * 1024 * 1024)).toFixed(2)} GB
• Livre: ${(mem.free / (1024 * 1024 * 1024)).toFixed(2)} GB
• Uso: ${((mem.used / mem.total) * 100).toFixed(2)}%`;

        bot.sendMessage(msg.chat.id, mensagem, { parse_mode: 'Markdown' });
    } catch (err) {
        bot.sendMessage(msg.chat.id, `❌ Erro ao obter status: ${err.message}`);
    }
});

// Comando /processos
bot.onText(/\/processos/, async (msg) => {
    if (!verificarAutorizacao(msg)) return;

    try {
        const processos = await si.processes();
        
        let mensagem = '📋 *Top 10 Processos:*\n\n';
        
        // Ordenar por CPU
        const top10 = processos.list
            .sort((a, b) => b.cpu - a.cpu)
            .slice(0, 10);
            
        for (const proc of top10) {
            mensagem += `• ${proc.name} (PID: ${proc.pid})\n`;
            mensagem += `  CPU: ${proc.cpu.toFixed(1)}% | RAM: ${(proc.memRss / 1024 / 1024).toFixed(1)} MB\n\n`;
        }

        bot.sendMessage(msg.chat.id, mensagem, { parse_mode: 'Markdown' });
    } catch (err) {
        bot.sendMessage(msg.chat.id, `❌ Erro ao listar processos: ${err.message}`);
    }
});

// Comando /memoria
bot.onText(/\/memoria/, async (msg) => {
    if (!verificarAutorizacao(msg)) return;

    try {
        const [mem, swap] = await Promise.all([
            si.mem(),
            si.memLayout()
        ]);

        const mensagem = `💾 *Uso de Memória*

*RAM:*
• Total: ${(mem.total / (1024 * 1024 * 1024)).toFixed(2)} GB
• Usado: ${(mem.used / (1024 * 1024 * 1024)).toFixed(2)} GB
• Livre: ${(mem.free / (1024 * 1024 * 1024)).toFixed(2)} GB
• Uso: ${((mem.used / mem.total) * 100).toFixed(2)}%

*Swap:*
• Total: ${(mem.swaptotal / (1024 * 1024 * 1024)).toFixed(2)} GB
• Usado: ${(mem.swapused / (1024 * 1024 * 1024)).toFixed(2)} GB
• Livre: ${((mem.swaptotal - mem.swapused) / (1024 * 1024 * 1024)).toFixed(2)} GB
• Uso: ${((mem.swapused / mem.swaptotal) * 100).toFixed(2)}%`;

        bot.sendMessage(msg.chat.id, mensagem, { parse_mode: 'Markdown' });
    } catch (err) {
        bot.sendMessage(msg.chat.id, `❌ Erro ao obter informações de memória: ${err.message}`);
    }
});

// Comando /disco
bot.onText(/\/disco/, async (msg) => {
    if (!verificarAutorizacao(msg)) return;

    try {
        const discos = await si.fsSize();
        
        let mensagem = '💽 *Uso de Disco*\n\n';
        
        for (const disco of discos) {
            mensagem += `*${disco.mount}:*\n`;
            mensagem += `• Total: ${(disco.size / (1024 * 1024 * 1024)).toFixed(2)} GB\n`;
            mensagem += `• Usado: ${(disco.used / (1024 * 1024 * 1024)).toFixed(2)} GB\n`;
            mensagem += `• Livre: ${((disco.size - disco.used) / (1024 * 1024 * 1024)).toFixed(2)} GB\n`;
            mensagem += `• Uso: ${disco.use.toFixed(2)}%\n\n`;
        }

        bot.sendMessage(msg.chat.id, mensagem, { parse_mode: 'Markdown' });
    } catch (err) {
        bot.sendMessage(msg.chat.id, `❌ Erro ao obter informações de disco: ${err.message}`);
    }
});

// Comando /rede
bot.onText(/\/rede/, async (msg) => {
    if (!verificarAutorizacao(msg)) return;

    try {
        const [interfaces, stats] = await Promise.all([
            si.networkInterfaces(),
            si.networkStats()
        ]);
        
        let mensagem = '🌐 *Informações de Rede*\n\n';
        
        // Interfaces
        for (const iface of interfaces) {
            if (iface.ip4) {
                mensagem += `*${iface.iface}:*\n`;
                mensagem += `• IP: ${iface.ip4}\n`;
                if (iface.ip6) mensagem += `• IPv6: ${iface.ip6}\n`;
                mensagem += `• MAC: ${iface.mac}\n`;
                mensagem += `• MTU: ${iface.mtu}\n\n`;
            }
        }
        
        // Estatísticas
        for (const stat of stats) {
            mensagem += `*${stat.iface} (Stats):*\n`;
            mensagem += `• RX: ${(stat.rx_bytes / (1024 * 1024)).toFixed(2)} MB\n`;
            mensagem += `• TX: ${(stat.tx_bytes / (1024 * 1024)).toFixed(2)} MB\n\n`;
        }

        bot.sendMessage(msg.chat.id, mensagem, { parse_mode: 'Markdown' });
    } catch (err) {
        bot.sendMessage(msg.chat.id, `❌ Erro ao obter informações de rede: ${err.message}`);
    }
});

// Comando /ajuda
bot.onText(/\/ajuda/, (msg) => {
    if (!verificarAutorizacao(msg)) return;
    bot.emit('message', msg, ['/start']);
});

// Inicialização
console.log('🤖 BOT-T-Terminal (Node.js) iniciado!'); 