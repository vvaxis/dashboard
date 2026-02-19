# Plano de implementação — EWW Dashboard (redtail)

## Decisões tomadas

| Decisão | Escolha |
|---|---|
| Local de desenvolvimento | `~/Projects/dashboard/`, symlink para `~/.config/eww/` |
| Música — polling vs listen | `deflisten` com `playerctl --follow` (updates instantâneos) |
| Fechar dashboard | Keybind (`Mod+D`) + Escape (via eww event handler). Focus-loss adiado. |
| Escape | Tratado dentro do eww (evento de keypress no widget) |
| Eventos/Agenda | Adiado. Calendário grid funciona standalone. Hook limpo para integrar depois (Google Calendar via khal+vdirsyncer ou gcalcli). |
| Deploy | Symlink: `~/.config/eww → ~/Projects/dashboard/eww` |
| Build order | Faseado — cada módulo testado antes de avançar |

---

## Estrutura final do repo

```
~/Projects/dashboard/
├── PLAN.md                  # Este arquivo
├── eww-dashboard-brief.md   # Brief original
└── eww/                     # <- symlink target para ~/.config/eww/
    ├── eww.yuck             # Widgets e janelas
    ├── eww.scss             # Estilos (paleta redtail v2)
    └── scripts/
        ├── toggle-dashboard.sh   # Toggle open/close
        ├── calendar.py           # JSON do calendário mensal
        └── music.sh              # Controle playerctl (usado por deflisten)
```

---

## Fases

### Fase 0 — Scaffolding e symlink

1. Criar a estrutura de diretórios dentro do repo (`eww/`, `eww/scripts/`)
2. Criar symlink: `~/.config/eww → ~/Projects/dashboard/eww`
3. Criar `eww.yuck` e `eww.scss` vazios (esqueleto mínimo)
4. Garantir que `eww daemon` sobe sem erros
5. **Checkpoint**: `eww ping` retorna pong

### Fase 1 — Calendário

**Scripts:**

1. `scripts/calendar.py`
   - Python3, só stdlib (`json`, `calendar`, `datetime`)
   - Primeiro dia da semana: domingo
   - Meses em português
   - Output JSON: `{"month": "Fevereiro", "year": 2026, "today": 17, "weeks": [[0,0,1,2,3,4,5], ...]}`
   - Dias vazios = 0
   - Testar standalone: `python3 scripts/calendar.py` deve retornar JSON válido

**Widgets (eww.yuck):**

2. `defvar dashboard-open` (default `false`)
3. `defpoll cal-data` — intervalo 3600s, `run-while` ligado a `dashboard-open`, executa `calendar.py`
4. Widget `calendar-header` — mostra "Mês Ano" em âmbar
5. Widget `day-names` — Dom Seg Ter Qua Qui Sex Sáb
6. Widget `calendar-grid` — 6 rows × 7 cols, dia atual destacado (fundo âmbar), dias 0 invisíveis
7. Widget `calendar` — compõe header + day-names + grid

**Janela:**

8. `defwindow dashboard` — anchor center, ~460×520px, stacking overlay, focusable true, namespace `eww-dashboard`
9. Conteúdo da janela: por enquanto só o widget `calendar`

**Estilos (eww.scss):**

10. Variáveis SCSS para toda a paleta redtail v2
11. Fonte base: `Maple Mono NF`, fallback `monospace`
12. Estilos do calendário: grid layout, destaque do dia atual, hover states
13. Background da janela: `#1a1714` com ~94% opacidade, borda 2px `#3d352e`, border-radius 16px

**Toggle:**

14. `scripts/toggle-dashboard.sh`
    - Verifica `dashboard-open`, abre ou fecha seguindo a ordem correta
    - `chmod +x`

**Checkpoint Fase 1:**
- `./scripts/toggle-dashboard.sh` abre o painel com calendário funcional
- Repetir o comando fecha o painel
- `eww get dashboard-open` alterna entre `true`/`false`
- Calendário mostra o mês correto com o dia de hoje destacado

---

### Fase 2 — Controle de música

**Script + deflisten:**

1. `scripts/music.sh`
   - Usa `playerctl metadata --follow --format '{"title":"{{title}}","artist":"{{artist}}","status":"{{status}}"}'`
   - Escapa caracteres problemáticos para JSON
   - Fallback se nenhum player: `{"title":"","artist":"","status":"Stopped"}`
   - Testar standalone: rodar o script e dar play/pause, verificar output linha a linha

**Widgets (eww.yuck):**

2. `deflisten music-data` — executa `scripts/music.sh` (não é defpoll — é stream contínuo)
3. Widget `music-title` — título da música em texto bold
4. Widget `music-artist` — artista em lavanda
5. Widget `music-controls` — três botões:
   - 󰒮 (prev) → `playerctl previous`
   - 󰏤/󰐊 (play/pause, condicional ao status) → `playerctl play-pause`
   - 󰒭 (next) → `playerctl next`
6. Widget `music-section` — compõe título "󰎈  Música" + title + artist + controls
7. Estado vazio: quando `status == "Stopped"`, mostrar "Nenhum player ativo" em subtexto itálico

**Estilos:**

8. Estilos da seção música: botões com hover em lavanda, play/pause maior
9. Separador entre calendário e música: linha 1px `#3d352e`

**Integração na janela:**

10. Atualizar o conteúdo da `defwindow dashboard`: calendário + separador + música

**Checkpoint Fase 2:**
- Dashboard mostra calendário + player de música
- Botões prev/play-pause/next funcionam
- Título e artista atualizam em tempo real ao trocar de música
- Com nenhum player ativo, mostra estado vazio gracefully

---

### Fase 3 — Escape para fechar + polish

1. Adicionar handler de Escape na janela do dashboard (`:onkeypress` ou mecanismo equivalente no eww) que executa o toggle script
2. Placeholder visual para a futura seção de Agenda:
   - Separador após o calendário
   - Texto "Agenda — em breve" em subtexto, com ícone 󰃭
   - Ou simplesmente omitir (a decidir)
3. Ajustes visuais:
   - Testar tamanho da janela e ajustar se necessário
   - Testar com diferentes quantidades de semanas no mês (28, 30, 31 dias)
   - Verificar que fontes e ícones Nerd Font renderizam corretamente
4. Garantir fallbacks silenciosos:
   - `playerctl` não instalado → música mostra estado vazio
   - `python3` não disponível → eww não crasha (improvável mas verificar)

**Checkpoint Fase 3:**
- Escape fecha o dashboard
- Tudo visualmente polido e coerente com a paleta

---

### Fase 4 — Integração com Niri

1. Fornecer snippet para `~/.config/niri/config.kdl`:
   - `spawn-at-startup "eww" "daemon"`
   - Keybind `Mod+D` → `spawn-sh "~/.config/eww/scripts/toggle-dashboard.sh"`
   - Layer-rule para o namespace `eww-dashboard` (screencast block, blur opcional)
2. **NÃO** modificar o config do Niri automaticamente — apenas fornecer o snippet para o usuário aplicar manualmente

**Checkpoint Fase 4:**
- `Mod+D` abre e fecha o dashboard
- Dashboard aparece como overlay acima das janelas
- `eww daemon` inicia automaticamente com o Niri

---

## Notas

- Todos os scripts com shebangs corretos e `chmod +x`
- Comentários em português onde ajuda clareza
- JSON output sempre válido, mesmo em edge cases
- Zero recursos quando dashboard fechado (`deflisten` é a exceção — roda em background, mas o custo de `playerctl --follow` é negligível)
- A seção de Agenda será integrada numa fase futura quando a fonte de eventos for escolhida (Google Calendar via khal+vdirsyncer ou gcalcli)
