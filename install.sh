#!/usr/bin/env bash
# install.sh - install and manage ai-tools skills for AI agents.
# Supports Bash 3.2 (the macOS default shell).

set -euo pipefail

VERSION="1.1.0"
SELF="$(basename "$0")"
NL="$(printf '\nx')"; NL="${NL%x}"

# Repository source

# Resolve the real script directory, including symlinked invocations.
resolve_dir() {
  local src="$1" dir
  while [ -L "$src" ]; do
    dir="$(cd -P "$(dirname "$src")" && pwd)"
    src="$(readlink "$src")"
    case "$src" in /*) ;; *) src="$dir/$src" ;; esac
  done
  cd -P "$(dirname "$src")" && pwd
}

REPO_DIR="$(resolve_dir "${BASH_SOURCE[0]}")"
SKILLS_SRC="$REPO_DIR/skills/generic-skills"
MANIFEST="${AI_TOOLS_MANIFEST:-$HOME/.config/ai-tools/manifest}"

# Format: id|label|user-subdir|project-subdir. Codex is excluded because it has no skill mechanism.
PROVIDERS="
claude|Claude Code|.claude|.claude
cursor|Cursor|.cursor|.cursor
continue|Continue|.continue|.continue
opencode|OpenCode|.config/opencode|.opencode
agents|Agents (cross-provider)|.agents|.agents
"
PROVIDER_IDS="claude cursor continue opencode agents"

# Options

MODE=""; SCOPE=""; PROJECT_DIR=""
WANT_SKILLS=""; WANT_PROVIDERS=""
ASSUME_YES=0; DRY_RUN=0; FORCE=0
ACTION="install"

# Output

if [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; then
  C_DIM=$'\033[2m'; C_B=$'\033[1m'; C_OK=$'\033[32m'
  C_WARN=$'\033[33m'; C_ERR=$'\033[31m'; C_OFF=$'\033[0m'
else
  C_DIM=""; C_B=""; C_OK=""; C_WARN=""; C_ERR=""; C_OFF=""
fi

info() { printf '%s\n' "$*"; }
dim()  { printf '%s%s%s\n' "$C_DIM" "$*" "$C_OFF"; }
ok()   { printf '%s  ok%s  %s\n' "$C_OK" "$C_OFF" "$*"; }
warn() { printf '%swarn%s  %s\n' "$C_WARN" "$C_OFF" "$*" >&2; }
die()  { printf '%serror%s %s\n' "$C_ERR" "$C_OFF" "$*" >&2; exit 1; }

# Route writes through this wrapper so --dry-run remains side-effect free.
run() {
  if [ "$DRY_RUN" -eq 1 ]; then
    printf '%s  dry%s  %s\n' "$C_DIM" "$C_OFF" "$*"
  else
    "$@"
  fi
}

# Shorten paths in output.
tilde() {
  case "$1" in
    "$HOME")   printf '~' ;;
    "$HOME"/*) printf '~/%s' "${1#$HOME/}" ;;
    *)         printf '%s' "$1" ;;
  esac
}

usage() {
  cat <<EOF
$SELF $VERSION - instalador de skills de ai-tools

  $SELF [opciones]

Sin opciones es interactivo: pregunta donde instalar, que skills, que agentes
y si linkear o copiar.

Destino
  --project PATH   PATH/.claude/skills y demas (default: raiz git del cwd)
  --user           ~/.claude/skills y demas

Seleccion
  --skills a,b,c   solo esas skills          --all         todas
  --providers a,b  solo esos agentes

Modo
  --link           symlink al repo (default no-interactivo)
  --copy           copia, independiente del repo

Acciones
  --list           lista las skills del repo y sale
  --status         que hay instalado en este proyecto y a nivel usuario
  --uninstall      elimina lo instalado en el destino elegido
                   (acepta --skills para sacar solo algunas)

Otros
  --dry-run        muestra que haria, sin escribir
  --force          pisa entradas que no haya creado este script
  -y, --yes        no pregunta nada (requiere destino y seleccion)
  -h, --help       esta ayuda

Ejemplos
  ./$SELF                                     interactivo
  ./$SELF --status                            estado actual
  ./$SELF --user --all -y                     todo, global
  cd ~/app && ~/repos/ai-tools/$SELF          instala en ~/app
  ./$SELF --project ~/app --uninstall --skills grill-me
EOF
}

# Arguments

while [ $# -gt 0 ]; do
  case "$1" in
    --skills)      WANT_SKILLS="${2:-}"; shift 2 ;;
    --skills=*)    WANT_SKILLS="${1#*=}"; shift ;;
    --all)         WANT_SKILLS="__all__"; shift ;;
    --providers)   WANT_PROVIDERS="${2:-}"; shift 2 ;;
    --providers=*) WANT_PROVIDERS="${1#*=}"; shift ;;
    --project)     SCOPE="project"; PROJECT_DIR="${2:-}"; shift 2 ;;
    --project=*)   SCOPE="project"; PROJECT_DIR="${1#*=}"; shift ;;
    --user)        SCOPE="user"; shift ;;
    --link)        MODE="link"; shift ;;
    --copy)        MODE="copy"; shift ;;
    --dry-run)     DRY_RUN=1; shift ;;
    --uninstall)   ACTION="uninstall"; shift ;;
    --status)      ACTION="status"; shift ;;
    --list)        ACTION="list"; shift ;;
    --force)       FORCE=1; shift ;;
    -y|--yes)      ASSUME_YES=1; shift ;;
    -h|--help)     usage; exit 0 ;;
    *)             die "opcion desconocida: $1 (proba --help)" ;;
  esac
done

[ -d "$SKILLS_SRC" ] || die "no encuentro $SKILLS_SRC"

# Skills

# A skill is a directory containing SKILL.md; runtime scratch and scaffolding are excluded.
list_skills() {
  local dir name
  for dir in "$SKILLS_SRC"/*/; do
    [ -d "$dir" ] || continue
    name="$(basename "$dir")"
    case "$name" in _*|.*|*-workspace) continue ;; esac
    [ -f "$dir/SKILL.md" ] || continue
    printf '%s\n' "$name"
  done
}

# Extract and truncate the first useful frontmatter description line.
skill_desc() {
  awk -v w="${2:-64}" '
    NR==1 && $0 != "---" { exit }
    /^---[[:space:]]*$/  { if (++d == 2) exit; next }
    d == 1 && /^description:/ {
      sub(/^description:[[:space:]]*\|?[[:space:]]*/, "")
      gsub(/^"|"$/, "")
      if (length($0) == 0 && (getline) > 0) sub(/^[[:space:]]+/, "")
      if (length($0) <= w) { print; exit }
      s = substr($0, 1, w)
      i = length(s)
      while (i > 0 && substr(s, i, 1) != " ") i--
      if (i > w / 2) s = substr(s, 1, i - 1)
      printf "%s...\n", s
      exit
    }
  ' "$1" 2>/dev/null
}

SKILLS_ALL="$(list_skills)"
[ -n "$SKILLS_ALL" ] || die "no hay skills con SKILL.md en $SKILLS_SRC"

if [ "$ACTION" = "list" ]; then
  info "${C_B}Skills disponibles${C_OFF}  $(tilde "$SKILLS_SRC")"
  for s in $SKILLS_ALL; do
    printf '  %-26s %s\n' "$s" "$(skill_desc "$SKILLS_SRC/$s/SKILL.md")"
  done
  exit 0
fi

# Manifest: <skill> TAB <absolute path> TAB <mode>.

MANIFEST_DATA=""
[ -f "$MANIFEST" ] && MANIFEST_DATA="$(cat "$MANIFEST")"

manifest_has() {  # $1 path
  case "$NL$MANIFEST_DATA$NL" in
    *"$NL"*"	$1	"*"$NL"*) return 0 ;;
    *) return 1 ;;
  esac
}

manifest_add() {  # $1 skill, $2 path, $3 mode
  local line="$1	$2	$3"
  MANIFEST_DATA="${MANIFEST_DATA:+$MANIFEST_DATA$NL}$line"
  [ "$DRY_RUN" -eq 1 ] && return 0
  mkdir -p "$(dirname "$MANIFEST")"
  printf '%s\n' "$line" >> "$MANIFEST"
  awk '!seen[$0]++' "$MANIFEST" > "$MANIFEST.tmp" && mv "$MANIFEST.tmp" "$MANIFEST"
  return 0
}

manifest_rewrite() {  # $1 replacement content
  [ "$DRY_RUN" -eq 1 ] && return 0
  if [ -z "$1" ]; then
    rm -f "$MANIFEST"
  else
    mkdir -p "$(dirname "$MANIFEST")"
    printf '%s\n' "$1" > "$MANIFEST"
  fi
  return 0
}

# TTY input is required for prompts when stdin contains the script (for example, curl | bash).

TTY_OK=0
[ -r /dev/tty ] && [ -t 2 ] && TTY_OK=1
INTERACTIVE=0
[ "$TTY_OK" -eq 1 ] && [ "$ASSUME_YES" -eq 0 ] && INTERACTIVE=1

ask() {
  local reply=""
  printf '%s' "$1" > /dev/tty
  IFS= read -r reply < /dev/tty || reply=""
  printf '%s' "$reply"
}

confirm() {  # $1 prompt; the script's only confirmation point.
  [ "$ASSUME_YES" -eq 1 ] && return 0
  [ "$TTY_OK" -eq 1 ] || die "sin tty: agrega -y para confirmar"
  local r; r="$(ask "$1 [S/n] ")"
  case "$r" in ""|s|S|y|Y|si|SI|yes|YES) return 0 ;; *) return 1 ;; esac
}

# Numbered menu supporting lists, ranges, all, none, and a default on Enter.
# $1 title, $2 default, $3 newline-delimited id|mark|hint items.
choose() {
  local title="$1" dflt="$2" items="$3"
  local n=0 it reply out="" i tok lo hi id rest mark hint oldifs
  {
    printf '\n%s%s%s\n' "$C_B" "$title" "$C_OFF"
    oldifs="$IFS"; IFS="$NL"
    for it in $items; do
      n=$((n + 1))
      id="${it%%|*}"; rest="${it#*|}"; mark="${rest%%|*}"; hint="${rest#*|}"
      printf ' %1s %2d) %-26s %s%s%s\n' "$mark" "$n" "$id" "$C_DIM" "$hint" "$C_OFF"
    done
    IFS="$oldifs"
  } > /dev/tty
  reply="$(ask '> ')"
  case "$reply" in
    "")            printf '%s' "$dflt"; return ;;
    all|ALL|todas) printf '%s\n' "$items" | awk -F'|' 'NF{printf "%s ", $1}'; return ;;
    none|NONE)     printf ''; return ;;
  esac
  for tok in $reply; do
    case "$tok" in
      *-*) lo="${tok%%-*}"; hi="${tok##*-}"
           case "$lo$hi" in *[!0-9]*) warn "ignoro '$tok'"; continue ;; esac
           i="$lo"
           while [ "$i" -le "$hi" ]; do
             it="$(printf '%s\n' "$items" | sed -n "${i}p")"
             [ -n "$it" ] && out="$out ${it%%|*}"
             i=$((i + 1))
           done ;;
      *[!0-9]*) warn "ignoro '$tok'" ;;
      *)   it="$(printf '%s\n' "$items" | sed -n "${tok}p")"
           if [ -n "$it" ]; then out="$out ${it%%|*}"; else warn "fuera de rango: $tok"; fi ;;
    esac
  done
  printf '%s' "${out# }"
}

# ------------------------------------------------------------- providers ----

provider_label() {
  printf '%s\n' "$PROVIDERS" | awk -F'|' -v i="$1" '$1==i{print $2;exit}'
}
# $1 id, $2 scope, $3 base
provider_dest_for() {
  local col=3; [ "$2" = "project" ] && col=4
  local sub; sub="$(printf '%s\n' "$PROVIDERS" | awk -F'|' -v i="$1" -v c="$col" '$1==i{print $c;exit}')"
  [ -n "$sub" ] || return 1
  printf '%s/%s/skills' "$3" "$sub"
}
provider_dest() { provider_dest_for "$1" "$SCOPE" "$BASE"; }

# A provider is detected when its marker directory exists; .claude is the project default.
detected_providers() {  # $1 scope, $2 base
  local id dest marker
  for id in $PROVIDER_IDS; do
    dest="$(provider_dest_for "$id" "$1" "$2")"
    marker="$(dirname "$dest")"
    if [ -d "$marker" ]; then
      printf '%s\n' "$id"
    elif [ "$1" = "project" ] && [ "$id" = "claude" ]; then
      printf '%s\n' "$id"
    fi
  done
}

# Project destination: the Git root of the working directory, or the working directory itself.

if [ -z "$PROJECT_DIR" ]; then
  PROJECT_DIR="$(git -C "$PWD" rev-parse --show-toplevel 2>/dev/null || printf '%s' "$PWD")"
else
  [ -d "$PROJECT_DIR" ] || die "no existe el proyecto: $PROJECT_DIR"
  PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd)"
fi

IS_SELF=0
[ "$PROJECT_DIR" = "$REPO_DIR" ] && IS_SELF=1

# Return "mode|providers" for a skill in a scope, or an empty string.

status_of() {  # $1 skill, $2 scope, $3 base
  local id dest line found_mode="" provs="" oldifs
  for id in $PROVIDER_IDS; do
    dest="$(provider_dest_for "$id" "$2" "$3")/$1"
    oldifs="$IFS"; IFS="$NL"
    for line in $MANIFEST_DATA; do
      case "$line" in
        *"	$dest	"*)
          found_mode="${line##*	}"
          provs="${provs:+$provs,}$id"
          break ;;
      esac
    done
    IFS="$oldifs"
  done
  [ -n "$found_mode" ] && printf '%s|%s' "$found_mode" "$provs"
  return 0
}

print_scope_status() {  # $1 label, $2 scope, $3 base
  local s st mode provs n=0
  info "${C_B}$1${C_OFF}  $(tilde "$3")"
  for s in $SKILLS_ALL; do
    st="$(status_of "$s" "$2" "$3")"
    [ -n "$st" ] || continue
    mode="${st%%|*}"; provs="${st#*|}"
    [ "$mode" = "copy" ] && mode="copia"
    printf '  %-26s %-8s %s\n' "$s" "$mode" "$provs"
    n=$((n + 1))
  done
  [ "$n" -eq 0 ] && dim "  (nada instalado)"
  return 0
}

if [ "$ACTION" = "status" ]; then
  print_scope_status "Proyecto" "project" "$PROJECT_DIR"
  info ""
  print_scope_status "Usuario" "user" "$HOME"
  info ""
  dim "Manifest $(tilde "$MANIFEST")"
  exit 0
fi

# User or project destination

if [ -z "$SCOPE" ]; then
  if [ "$INTERACTIVE" -eq 1 ]; then
    if [ "$IS_SELF" -eq 1 ]; then
      SCOPE_DFLT="user"
      MENU="project||$(tilde "$PROJECT_DIR")  <- es el propio repo de skills${NL}user||$(tilde "$HOME")/... agentes detectados  (default)"
    else
      SCOPE_DFLT="project"
      MENU="project||$(tilde "$PROJECT_DIR")  (default)${NL}user||$(tilde "$HOME")/... agentes detectados"
    fi
    SCOPE="$(choose "Donde instalar?" "$SCOPE_DFLT" "$MENU")"
  else
    die "sin tty: elegi el destino con --user o --project PATH"
  fi
fi
case "$SCOPE" in project|user) ;; *) die "destino invalido: $SCOPE" ;; esac

if [ "$SCOPE" = "project" ]; then BASE="$PROJECT_DIR"; else BASE="$HOME"; fi

# Resolve destination directories once for this scope.
SCOPE_DIRS=""
for p in $PROVIDER_IDS; do
  SCOPE_DIRS="${SCOPE_DIRS:+$SCOPE_DIRS$NL}$(provider_dest_for "$p" "$SCOPE" "$BASE")"
done

# Uninstall only entries recorded for this destination.

if [ "$ACTION" = "uninstall" ]; then
  [ -n "$MANIFEST_DATA" ] || die "no hay nada registrado en $(tilde "$MANIFEST")"

  FILTER_SKILLS=""
  if [ -n "$WANT_SKILLS" ] && [ "$WANT_SKILLS" != "__all__" ]; then
    FILTER_SKILLS="$(printf '%s' "$WANT_SKILLS" | tr ',' ' ')"
  fi

  TARGETS=""; KEEP=""
  oldifs="$IFS"; IFS="$NL"
  for line in $MANIFEST_DATA; do
    IFS="$oldifs"
    [ -n "$line" ] || continue
    lpath="${line#*	}"; lpath="${lpath%%	*}"
    lskill="${line%%	*}"
    ldir="$(dirname "$lpath")"
    match=0
    case "$NL$SCOPE_DIRS$NL" in *"$NL$ldir$NL"*) match=1 ;; esac
    if [ "$match" -eq 1 ] && [ -n "$FILTER_SKILLS" ]; then
      match=0
      for f in $FILTER_SKILLS; do [ "$f" = "$lskill" ] && match=1; done
    fi
    if [ "$match" -eq 1 ]; then
      TARGETS="${TARGETS:+$TARGETS$NL}$line"
    else
      KEEP="${KEEP:+$KEEP$NL}$line"
    fi
    IFS="$NL"
  done
  IFS="$oldifs"

  [ -n "$TARGETS" ] || die "nada instalado por este script en $(tilde "$BASE")${FILTER_SKILLS:+ para: $FILTER_SKILLS}"

  info "${C_B}Se van a eliminar de $(tilde "$BASE")${C_OFF}"
  IFS="$NL"; for line in $TARGETS; do IFS="$oldifs"
    lpath="${line#*	}"; lpath="${lpath%%	*}"
    printf '  %s\n' "$(tilde "$lpath")"
    IFS="$NL"
  done; IFS="$oldifs"
  confirm "Confirmas?" || { info "cancelado"; exit 0; }

  IFS="$NL"; for line in $TARGETS; do IFS="$oldifs"
    lpath="${line#*	}"; lpath="${lpath%%	*}"
    lmode="${line##*	}"
    if [ -L "$lpath" ]; then
      run rm -f "$lpath"; ok "removido $(tilde "$lpath")"
    elif [ -d "$lpath" ] && [ "$lmode" = "copy" ]; then
      run rm -rf "$lpath"; ok "removido $(tilde "$lpath")"
    else
      warn "no existe o cambio de tipo, lo dejo: $(tilde "$lpath")"
    fi
    IFS="$NL"
  done; IFS="$oldifs"

  manifest_rewrite "$KEEP"
  info "listo"
  [ -n "$KEEP" ] && dim "Quedan entradas en otros destinos: $SELF --status"
  exit 0
fi

# Selection

if [ "$WANT_SKILLS" = "__all__" ]; then
  SEL_SKILLS="$SKILLS_ALL"
elif [ -n "$WANT_SKILLS" ]; then
  SEL_SKILLS="$(printf '%s' "$WANT_SKILLS" | tr ',' ' ')"
  for s in $SEL_SKILLS; do
    printf '%s\n' "$SKILLS_ALL" | grep -qx "$s" || die "skill inexistente: $s"
  done
elif [ "$INTERACTIVE" -eq 1 ]; then
  MENU=""
  for s in $SKILLS_ALL; do
    st="$(status_of "$s" "$SCOPE" "$BASE")"
    if [ -n "$st" ]; then
      m="${st%%|*}"; [ "$m" = "copy" ] && m="copia"
      MENU="${MENU:+$MENU$NL}$s|*|[$m] $(skill_desc "$SKILLS_SRC/$s/SKILL.md" 52)"
    else
      MENU="${MENU:+$MENU$NL}$s||$(skill_desc "$SKILLS_SRC/$s/SKILL.md" 60)"
    fi
  done
  SEL_SKILLS="$(choose \
    "Que skills instalar en $(tilde "$BASE")?  ${C_DIM}(* = ya instalada; Enter=todas, \"1 3 5\", \"1-4\", none)${C_OFF}" \
    "$SKILLS_ALL" "$MENU")"
else
  die "sin tty: usa --skills o --all"
fi
[ -n "$(printf '%s' "$SEL_SKILLS" | tr -d '[:space:]')" ] || { info "ninguna skill seleccionada"; exit 0; }

DETECTED="$(detected_providers "$SCOPE" "$BASE")"
if [ -n "$WANT_PROVIDERS" ]; then
  SEL_PROVIDERS="$(printf '%s' "$WANT_PROVIDERS" | tr ',' ' ')"
  for p in $SEL_PROVIDERS; do
    [ -n "$(provider_label "$p")" ] || die "provider desconocido: $p"
    printf '%s\n' "$DETECTED" | grep -qx "$p" \
      || warn "$p no parece instalado; lo instalo igual porque lo pediste"
  done
elif [ -z "$DETECTED" ]; then
  die "no detecte ningun agente de IA en $(tilde "$BASE")"
elif [ "$(printf '%s\n' "$DETECTED" | wc -l | tr -d ' ')" = "1" ]; then
  # No provider choice is needed when exactly one is detected.
  SEL_PROVIDERS="$DETECTED"
  [ "$INTERACTIVE" -eq 1 ] && dim "Agente: $(provider_label "$DETECTED") (unico detectado en $(tilde "$BASE"))"
elif [ "$INTERACTIVE" -eq 1 ]; then
  MENU=""
  for p in $DETECTED; do
    MENU="${MENU:+$MENU$NL}$p||$(provider_label "$p") - $(tilde "$(provider_dest "$p")")"
  done
  SEL_PROVIDERS="$(choose "Para que agentes?  ${C_DIM}(detectados; Enter=todos)${C_OFF}" \
                          "$DETECTED" "$MENU")"
else
  SEL_PROVIDERS="$DETECTED"
fi
[ -n "$(printf '%s' "$SEL_PROVIDERS" | tr -d '[:space:]')" ] || { info "ningun agente seleccionado"; exit 0; }

if [ -z "$MODE" ]; then
  if [ "$INTERACTIVE" -eq 1 ]; then
    if [ "$SCOPE" = "project" ]; then
      COPY_HINT="copia independiente; se puede commitear"
      LINK_HINT="editas el repo y se ve al instante; no sirve para tus companeros"
    else
      COPY_HINT="copia independiente del repo"
      LINK_HINT="editas el repo y se ve al instante  (default)"
    fi
    MODE="$(choose "Como instalar?" "link" "link||$LINK_HINT${NL}copy||$COPY_HINT")"
  else
    MODE="link"
  fi
fi
case "$MODE" in link|copy) ;; *) die "modo invalido: $MODE" ;; esac

# Plan

fmt_list() { printf '%s' "$1" | tr '\n' ' ' | tr -s ' ' | sed 's/^ //;s/ $//'; }

info ""
info "${C_B}Plan${C_OFF}"
info "  origen    $(tilde "$SKILLS_SRC")"
info "  destino   $(tilde "$BASE")  ${C_DIM}($SCOPE)${C_OFF}"
info "  modo      $MODE"
info "  skills    $(fmt_list "$SEL_SKILLS")"
info "  agentes   $(fmt_list "$SEL_PROVIDERS")"
[ "$DRY_RUN" -eq 1 ] && dim "  (dry-run: no se escribe nada)"
info ""
confirm "Procedo?" || { info "cancelado"; exit 0; }
info ""

# Installation

SEL_DESTS=""
for p in $SEL_PROVIDERS; do
  SEL_DESTS="${SEL_DESTS:+$SEL_DESTS$NL}$(provider_dest "$p")"
done

install_one() {  # $1 skill, $2 destination directory
  local name="$1" dir="$2" dest="$2/$1" src="$SKILLS_SRC/$1"
  if [ -e "$dest" ] || [ -L "$dest" ]; then
    if manifest_has "$dest" || [ "$FORCE" -eq 1 ]; then
      run rm -rf "$dest"
    else
      warn "$(tilde "$dest") ya existe y no lo creo este script; lo salteo (--force para pisar)"
      return 1
    fi
  fi
  run mkdir -p "$dir"
  if [ "$MODE" = "copy" ]; then run cp -R "$src" "$dest"; else run ln -sfn "$src" "$dest"; fi
  manifest_add "$name" "$dest" "$MODE"
  return 0
}

COUNT=0
for s in $SEL_SKILLS; do
  DONE_ONE=0
  oldifs="$IFS"; IFS="$NL"
  for d in $SEL_DESTS; do
    IFS="$oldifs"
    if install_one "$s" "$d"; then ok "$s -> $(tilde "$d/$s")"; DONE_ONE=1; fi
    IFS="$NL"
  done
  IFS="$oldifs"
  [ "$DONE_ONE" -eq 1 ] && COUNT=$((COUNT + 1))
done

info ""
info "${C_B}Listo${C_OFF}  $COUNT skill(s) instalada(s)."
if [ "$MODE" = "link" ]; then
  dim "Symlinks a $(tilde "$SKILLS_SRC")"
  dim "No muevas ni borres ese directorio, o las skills dejan de aparecer."
  [ "$SCOPE" = "project" ] && dim "Son links a un path local: tus companeros no los van a resolver."
fi
dim "Estado: $SELF --status  ·  revertir: $SELF --uninstall"
