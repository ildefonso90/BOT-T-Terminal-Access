package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"os/exec"
	"runtime"
	"strings"
	"time"

	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
	"github.com/shirou/gopsutil/v3/cpu"
	"github.com/shirou/gopsutil/v3/disk"
	"github.com/shirou/gopsutil/v3/host"
	"github.com/shirou/gopsutil/v3/mem"
	"github.com/shirou/gopsutil/v3/net"
	"github.com/shirou/gopsutil/v3/process"
)

// Configuração
type Config struct {
	Token              string   `json:"token"`
	DonoUsername       string   `json:"dono_username"`
	IdsAutorizados     []int64  `json:"ids_autorizados"`
	UsuariosBloqueados []int64  `json:"usuarios_bloqueados"`
	TentativasMaximas  int      `json:"tentativas_maximas"`
}

var (
	config         Config
	tentativasFalhas = make(map[int64]int)
)

func main() {
	// Carregar configuração
	configFile, err := ioutil.ReadFile("config.json")
	if err != nil {
		log.Fatal("Erro ao ler config.json:", err)
	}

	err = json.Unmarshal(configFile, &config)
	if err != nil {
		log.Fatal("Erro ao parsear config.json:", err)
	}

	// Inicializar bot
	bot, err := tgbotapi.NewBotAPI(config.Token)
	if err != nil {
		log.Fatal("Erro ao inicializar bot:", err)
	}

	log.Printf("🤖 BOT-T-Terminal (Go) iniciado! @%s", bot.Self.UserName)

	u := tgbotapi.NewUpdate(0)
	u.Timeout = 60

	updates := bot.GetUpdatesChan(u)

	for update := range updates {
		if update.Message == nil {
			continue
		}

		msg := update.Message

		// Verificar autorização
		if !verificarAutorizacao(bot, msg) {
			continue
		}

		// Processar comandos
		switch msg.Command() {
		case "start":
			enviarMensagemStart(bot, msg)
		case "cmd":
			executarComando(bot, msg)
		case "status":
			enviarStatus(bot, msg)
		case "processos":
			listarProcessos(bot, msg)
		case "memoria":
			enviarInfoMemoria(bot, msg)
		case "disco":
			enviarInfoDisco(bot, msg)
		case "rede":
			enviarInfoRede(bot, msg)
		case "ajuda":
			enviarMensagemStart(bot, msg)
		}
	}
}

func verificarAutorizacao(bot *tgbotapi.BotAPI, msg *tgbotapi.Message) bool {
	userId := msg.From.ID

	// Verificar se está bloqueado
	for _, id := range config.UsuariosBloqueados {
		if id == userId {
			reply := tgbotapi.NewMessage(msg.Chat.ID, "❌ Você está bloqueado! Contate o administrador.")
			bot.Send(reply)
			return false
		}
	}

	// Verificar se está autorizado
	autorizado := false
	for _, id := range config.IdsAutorizados {
		if id == userId {
			autorizado = true
			break
		}
	}

	if !autorizado {
		tentativasFalhas[userId]++
		if tentativasFalhas[userId] >= config.TentativasMaximas {
			config.UsuariosBloqueados = append(config.UsuariosBloqueados, userId)
			configJson, _ := json.MarshalIndent(config, "", "    ")
			ioutil.WriteFile("config.json", configJson, 0644)
			reply := tgbotapi.NewMessage(msg.Chat.ID, "🚫 Muitas tentativas! Você foi bloqueado.")
			bot.Send(reply)
		} else {
			reply := tgbotapi.NewMessage(msg.Chat.ID, "⚠️ Você não está autorizado!")
			bot.Send(reply)
		}
		return false
	}

	return true
}

func enviarMensagemStart(bot *tgbotapi.BotAPI, msg *tgbotapi.Message) {
	mensagem := fmt.Sprintf(`🤖 *Bem-vindo ao BOT-T-Terminal!*

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
- Após %d tentativas falhas, você será bloqueado
- Apenas o dono (@%s) pode desbloquear usuários

*Desenvolvido por:* JOAC
*Versão:* 1.0.0`, config.TentativasMaximas, config.DonoUsername)

	reply := tgbotapi.NewMessage(msg.Chat.ID, mensagem)
	reply.ParseMode = "Markdown"
	bot.Send(reply)
}

func executarComando(bot *tgbotapi.BotAPI, msg *tgbotapi.Message) {
	comando := strings.TrimPrefix(msg.Text, "/cmd ")
	if comando == "" {
		reply := tgbotapi.NewMessage(msg.Chat.ID, "⚠️ Uso: /cmd <comando>")
		bot.Send(reply)
		return
	}

	cmd := exec.Command("bash", "-c", comando)
	output, err := cmd.CombinedOutput()
	
	if err != nil {
		reply := tgbotapi.NewMessage(msg.Chat.ID, fmt.Sprintf("❌ Erro:\n%s", err))
		bot.Send(reply)
		return
	}

	mensagem := fmt.Sprintf("✅ Resultado:\n```\n%s\n```", string(output))
	reply := tgbotapi.NewMessage(msg.Chat.ID, mensagem)
	reply.ParseMode = "Markdown"
	bot.Send(reply)
}

func enviarStatus(bot *tgbotapi.BotAPI, msg *tgbotapi.Message) {
	hostInfo, _ := host.Info()
	cpuInfo, _ := cpu.Info()
	memInfo, _ := mem.VirtualMemory()

	mensagem := fmt.Sprintf(`📊 *Status do Servidor*

*Sistema:*
• OS: %s %s
• Arch: %s
• Uptime: %d horas

*CPU:*
• Modelo: %s
• Cores: %d
• Velocidade: %.2f GHz

*Memória:*
• Total: %.2f GB
• Livre: %.2f GB
• Uso: %.2f%%`,
		hostInfo.Platform, hostInfo.PlatformVersion,
		runtime.GOARCH,
		hostInfo.Uptime/3600,
		cpuInfo[0].ModelName,
		runtime.NumCPU(),
		cpuInfo[0].Mhz/1000,
		float64(memInfo.Total)/(1024*1024*1024),
		float64(memInfo.Free)/(1024*1024*1024),
		memInfo.UsedPercent)

	reply := tgbotapi.NewMessage(msg.Chat.ID, mensagem)
	reply.ParseMode = "Markdown"
	bot.Send(reply)
}

func listarProcessos(bot *tgbotapi.BotAPI, msg *tgbotapi.Message) {
	processes, err := process.Processes()
	if err != nil {
		reply := tgbotapi.NewMessage(msg.Chat.ID, "❌ Erro ao listar processos")
		bot.Send(reply)
		return
	}

	mensagem := "📋 *Top 10 Processos:*\n\n"
	
	type ProcessInfo struct {
		pid   int32
		name  string
		cpu   float64
		mem   float32
	}

	processInfos := make([]ProcessInfo, 0)
	
	for _, p := range processes {
		name, _ := p.Name()
		cpu, _ := p.CPUPercent()
		mem, _ := p.MemoryPercent()
		
		processInfos = append(processInfos, ProcessInfo{
			pid:  p.Pid,
			name: name,
			cpu:  cpu,
			mem:  mem,
		})
	}

	// Ordenar por CPU
	for i := 0; i < len(processInfos)-1; i++ {
		for j := i + 1; j < len(processInfos); j++ {
			if processInfos[j].cpu > processInfos[i].cpu {
				processInfos[i], processInfos[j] = processInfos[j], processInfos[i]
			}
		}
	}

	// Pegar top 10
	count := 0
	for _, p := range processInfos {
		if count >= 10 {
			break
		}
		mensagem += fmt.Sprintf("• %s (PID: %d)\n", p.name, p.pid)
		mensagem += fmt.Sprintf("  CPU: %.1f%% | RAM: %.1f MB\n\n", p.cpu, float64(p.mem)*1024/100)
		count++
	}

	reply := tgbotapi.NewMessage(msg.Chat.ID, mensagem)
	reply.ParseMode = "Markdown"
	bot.Send(reply)
}

func enviarInfoMemoria(bot *tgbotapi.BotAPI, msg *tgbotapi.Message) {
	v, _ := mem.VirtualMemory()
	s, _ := mem.SwapMemory()

	mensagem := fmt.Sprintf(`💾 *Uso de Memória*

*RAM:*
• Total: %.2f GB
• Usado: %.2f GB
• Livre: %.2f GB
• Uso: %.2f%%

*Swap:*
• Total: %.2f GB
• Usado: %.2f GB
• Livre: %.2f GB
• Uso: %.2f%%`,
		float64(v.Total)/(1024*1024*1024),
		float64(v.Used)/(1024*1024*1024),
		float64(v.Free)/(1024*1024*1024),
		v.UsedPercent,
		float64(s.Total)/(1024*1024*1024),
		float64(s.Used)/(1024*1024*1024),
		float64(s.Free)/(1024*1024*1024),
		s.UsedPercent)

	reply := tgbotapi.NewMessage(msg.Chat.ID, mensagem)
	reply.ParseMode = "Markdown"
	bot.Send(reply)
}

func enviarInfoDisco(bot *tgbotapi.BotAPI, msg *tgbotapi.Message) {
	partitions, err := disk.Partitions(false)
	if err != nil {
		reply := tgbotapi.NewMessage(msg.Chat.ID, "❌ Erro ao obter informações do disco")
		bot.Send(reply)
		return
	}

	mensagem := "💽 *Uso de Disco*\n\n"

	for _, partition := range partitions {
		usage, err := disk.Usage(partition.Mountpoint)
		if err != nil {
			continue
		}

		mensagem += fmt.Sprintf("*%s:*\n", partition.Mountpoint)
		mensagem += fmt.Sprintf("• Total: %.2f GB\n", float64(usage.Total)/(1024*1024*1024))
		mensagem += fmt.Sprintf("• Usado: %.2f GB\n", float64(usage.Used)/(1024*1024*1024))
		mensagem += fmt.Sprintf("• Livre: %.2f GB\n", float64(usage.Free)/(1024*1024*1024))
		mensagem += fmt.Sprintf("• Uso: %.2f%%\n\n", usage.UsedPercent)
	}

	reply := tgbotapi.NewMessage(msg.Chat.ID, mensagem)
	reply.ParseMode = "Markdown"
	bot.Send(reply)
}

func enviarInfoRede(bot *tgbotapi.BotAPI, msg *tgbotapi.Message) {
	interfaces, err := net.Interfaces()
	if err != nil {
		reply := tgbotapi.NewMessage(msg.Chat.ID, "❌ Erro ao obter informações de rede")
		bot.Send(reply)
		return
	}

	stats, _ := net.IOCounters(true)
	
	mensagem := "🌐 *Informações de Rede*\n\n"

	for _, iface := range interfaces {
		if len(iface.Addrs) > 0 {
			mensagem += fmt.Sprintf("*%s:*\n", iface.Name)
			for _, addr := range iface.Addrs {
				mensagem += fmt.Sprintf("• IP: %s\n", addr.Addr)
			}
			mensagem += fmt.Sprintf("• MAC: %s\n", iface.HardwareAddr)
			mensagem += fmt.Sprintf("• MTU: %d\n\n", iface.MTU)
		}
	}

	for _, stat := range stats {
		mensagem += fmt.Sprintf("*%s (Stats):*\n", stat.Name)
		mensagem += fmt.Sprintf("• RX: %.2f MB\n", float64(stat.BytesRecv)/(1024*1024))
		mensagem += fmt.Sprintf("• TX: %.2f MB\n\n", float64(stat.BytesSent)/(1024*1024))
	}

	reply := tgbotapi.NewMessage(msg.Chat.ID, mensagem)
	reply.ParseMode = "Markdown"
	bot.Send(reply)
} 