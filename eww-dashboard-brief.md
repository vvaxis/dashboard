# EWW Dashboard — redtail

## Contexto

Máquina: notebook `redtail`, Arch Linux com Niri (compositor Wayland scrollable-tiling).
Recursos limitados — economia de RAM e CPU é prioridade.
Dotfiles gerenciados por YADM, configs em `~/.config/`.

### Stack atual do redtail

| Componente     | Programa              |
|----------------|-----------------------|
| Compositor     | Niri                  |
| Terminal       | foot                  |
| Launcher       | fuzzel                |
| Notificações   | dunst                 |
| Barra          | waybar                |
| Wallpaper      | swaybg                |
| Lock           | swaylock-effects      |
| Network menu   | networkmanager-dmenu  |
| File (GUI)     | nautilus              |
| File (TUI)     | yazi                  |
| Fonte          | Maple Mono NF         |

### Paleta redtail v2

| Papel           | Hex       | Uso                          |
|-----------------|-----------|------------------------------|
| Base            | `#1a1714` | Fundo principal              |
| Surface         | `#2a2420` | Painéis, barras              |
| Overlay/Bordas  | `#3d352e` | Bordas, separadores          |
| Texto           | `#e2d5c0` | Texto principal (creme)      |
| Subtexto        | `#b0a48e` | Texto secundário             |
| Âmbar           | `#d4a243` | Acento primário              |
| Terracotta      | `#c46d4d` | Acento secundário            |
| Verde chá       | `#8aab72` | Sucesso, confirmações        |
| Azul discreto   | `#7a9ec2` | CPU, links, info fria        |
| Lavanda         | `#b07ab8` | Áudio, detalhes suaves       |
| Teal            | `#6fa3a0` | Rede, conectividade          |
| Vermelho        | `#c25d5d` | Alertas críticos             |
| Amarelo bright  | `#e0b65b` | Avisos, caps lock, memória   |

---

## Objetivo

Criar um dashboard EWW toggleável (popup central na tela) com dois módulos:

1. **Calendário** — grid visual do mês atual (pt-BR) com dia de hoje destacado + lista dos próximos eventos do Google Calendar via `gcalcli`.
2. **Controle de música** — título, artista, status do player + botões prev/play-pause/next via `playerctl`.

O dashboard abre/fecha com um keybind (`Mod+D`) e consome zero recursos quando fechado (pollers só rodam com o painel aberto).

---

## Arquitetura

### Estrutura de arquivos

```
~/.config/eww/
├── eww.yuck          # Definições de widgets e janela
├── eww.scss          # Estilos (paleta redtail v2, Maple Mono NF)
└── scripts/
    ├── toggle-dashboard.sh   # Toggle open/close + variável run-while
    ├── calendar.py           # Gera JSON do calendário mensal (python3, stdlib)
    ├── gcal-events.sh        # Busca eventos via gcalcli, output JSON
    └── music.sh              # Status do player via playerctl, output JSON
```

### Dependências

- `eww` (AUR) — framework de widgets
- `playerctl` (pacman) — controle MPRIS de players de música
- `gcalcli` (AUR) — CLI para Google Calendar (requer OAuth na primeira vez)
- `python3` (já instalado) — para o script de calendário

### Design da janela

- **Formato**: painel central (anchor center), ~460×520px
- **Stacking**: overlay (acima de tudo)
- **Focusable**: sim
- **Namespace**: `eww-dashboard` (para layer-rules no Niri se necessário)
- **Background**: base (`#1a1714`) com leve transparência (~94%)
- **Borda**: 2px solid overlay (`#3d352e`), border-radius 16px

### Pollers (economia de recursos)

Usar variável `dashboard-open` (defvar, default false) e `run-while` em todos os pollers:

| Poller       | Intervalo | Script                    | Output        |
|--------------|-----------|---------------------------|---------------|
| cal-data     | 3600s     | `scripts/calendar.py`     | JSON (mês, ano, hoje, weeks[][]) |
| gcal-events  | 300s      | `scripts/gcal-events.sh`  | JSON array [{time, name}] |
| music        | 2s        | `scripts/music.sh`        | JSON {title, artist, status} |

### Toggle (scripts/toggle-dashboard.sh)

```
Se dashboard-open == true:
    eww close dashboard
    eww update dashboard-open=false
Senão:
    eww update dashboard-open=true
    eww open dashboard
```

A ordem importa: atualizar a variável ANTES de abrir (para os pollers começarem) e DEPOIS de fechar.

### Calendário (scripts/calendar.py)

- Python3, só stdlib (json, calendar, datetime)
- Primeiro dia da semana: domingo (padrão brasileiro)
- Meses em português
- Output: `{"month": "Fevereiro", "year": 2026, "today": 16, "weeks": [[0,0,0,0,1,2,3], [4,5,...], ...]}`
- Dias vazios = 0

### Eventos Google Calendar (scripts/gcal-events.sh)

- Usa `gcalcli agenda --tsv --nocolor --nodeclined "today" "+3d"`
- Parseia o TSV (tab-separated) com python3 inline
- Output: `[{"time": "14:00", "name": "Reunião CMDJ"}, ...]`
- Máximo 8 eventos
- Se `gcalcli` não estiver instalado, retorna `[]` silenciosamente

### Player de música (scripts/music.sh)

- Usa `playerctl status`, `playerctl metadata title`, `playerctl metadata artist`
- Escapa aspas duplas no JSON
- Se nenhum player ativo: `{"title":"","artist":"","status":"Stopped"}`

---

## Layout dos widgets (de cima pra baixo)

1. **Header do calendário** — "Fevereiro 2026" em âmbar, bold
2. **Nomes dos dias** — Dom Seg Ter Qua Qui Sex Sáb em subtexto, fonte pequena
3. **Grid de dias** — 6 linhas × 7 colunas. Dia atual: fundo âmbar, texto base, bold. Dias vazios: invisíveis.
4. **Separador** — linha 1px overlay
5. **Seção Agenda** — título "󰃭  Agenda" em âmbar. Lista de eventos com horário em terracotta e nome em texto. Se sem eventos: "Sem eventos próximos" em subtexto itálico. Cada evento numa row com background surface translúcido e border-radius 8px.
6. **Separador** — linha 1px overlay
7. **Seção Música** — título "󰎈  Música" em âmbar. Título da música em texto bold. Artista em lavanda. Botões: 󰒮 (prev) 󰏤/󰐊 (play/pause) 󰒭 (next). Botões em subtexto, hover em lavanda. Botão play maior e já em lavanda.

---

## Integração com Niri

Adicionar ao `config.kdl`:

```kdl
// Autostart do daemon EWW
spawn-at-startup "eww" "daemon"

// Toggle do dashboard
Mod+D { spawn-sh "~/.config/eww/scripts/toggle-dashboard.sh"; }
```

Opcionalmente, layer-rule para blur:

```kdl
layer-rule {
    match namespace="^eww-dashboard$"
    // blur se desejado
}
```

---

## Critérios de qualidade

- Todos os scripts devem ter fallback silencioso (sem erros no stderr quando dependência não está instalada)
- JSON output deve ser sempre válido, mesmo em edge cases
- SCSS deve usar variáveis para todas as cores (fácil de trocar paleta)
- Fonte Maple Mono NF em tudo, com fallback monospace
- Código limpo, comentado em português onde ajuda clareza
- Scripts com `#!/bin/bash` ou `#!/usr/bin/env python3` e chmod +x
