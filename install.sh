#!/usr/bin/env bash
# install.sh - install and manage ai-tools skills for AI agents.
# Supports Bash 3.2 (the macOS default shell).

set -euo pipefail

VERSION="2.0.0"
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
SKILLS_ROOT="$REPO_DIR/skills"
MANIFEST="${AI_TOOLS_MANIFEST:-$HOME/.config/ai-tools/manifest}"
BACKUP_DIR="$(dirname "$MANIFEST")/backups/$(date +%Y%m%d-%H%M%S)"

# Format: id|label|user-subdir|project-subdir. Codex reads the cross-provider .agents/skills.
PROVIDERS="
claude|Claude Code|.claude|.claude
agents|Agents (Codex y compatibles)|.agents|.agents
cursor|Cursor|.cursor|.cursor
continue|Continue|.continue|.continue
opencode|OpenCode|.config/opencode|.opencode
"
PROVIDER_IDS="claude agents cursor continue opencode"

# Options

SCOPE=""; PROJECT_DIR=""
WANT_SKILLS=""; WANT_PROVIDERS=""; WITH_EXPERIMENTAL=0
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

Sin opciones es interactivo: pregunta donde instalar, que skills y para que agentes.
Siempre copia; volver a correrlo actualiza lo instalado.

Destino
  --project PATH   PATH/.claude/skills y demas (default: raiz git del cwd)
  --user           ~/.claude/skills y demas

Seleccion
  --skills a,b,c   esas skills (estables o experimentales)
  --all            todas las estables
  --experimental   con --all, suma las experimentales
  --providers a,b  claude, agents, cursor, continue, opencode
                   (default: claude, mas agents si existe .agents/)

Acciones
  --list           lista las skills del repo y sale
  --status         que hay instalado en este proyecto y a nivel usuario
  --uninstall      elimina lo instalado en el destino elegido
                   (acepta --skills para sacar solo algunas)

Otros
  --dry-run        muestra que haria, sin escribir
  --force          pisa las "distintas" (existen con ese nombre y no las instalo este script)
  -y, --yes        no pregunta nada (requiere destino y seleccion; saltea las distintas)
  -h, --help       esta ayuda

Estados
  nueva       no existe en el destino
  al dia      identica al catalogo; no se toca
  actualizar  la instalo este script (o es un symlink viejo al repo) y cambio; se reemplaza
  distinta    existe con ese nombre y no la instalo este script; se pregunta
  Lo que se reemplaza queda en $(tilde "$(dirname "$MANIFEST")")/backups/.

Ejemplos
  ./$SELF                                     interactivo
  ./$SELF --status                            estado actual
  ./$SELF --user --all -y                     estables, global
  ./$SELF --project ~/app --all --experimental --providers claude,agents -y
  cd ~/app && ~/repos/ai-tools/$SELF          instala o actualiza en ~/app
  ./$SELF --project ~/app --uninstall --skills doc-writer
EOF
}

# Arguments

need_arg() {  # $1 option, $2 remaining argument count
  [ "$2" -ge 2 ] || die "falta el valor de $1"
}

while [ $# -gt 0 ]; do
  case "$1" in
    --skills)      need_arg "$1" $#; WANT_SKILLS="$2"; shift 2 ;;
    --skills=*)    WANT_SKILLS="${1#*=}"; shift ;;
    --all)         WANT_SKILLS="__all__"; shift ;;
    --experimental) WITH_EXPERIMENTAL=1; shift ;;
    --providers)   need_arg "$1" $#; WANT_PROVIDERS="$2"; shift 2 ;;
    --providers=*) WANT_PROVIDERS="${1#*=}"; shift ;;
    --project)     need_arg "$1" $#; SCOPE="project"; PROJECT_DIR="$2"; shift 2 ;;
    --project=*)   SCOPE="project"; PROJECT_DIR="${1#*=}"; shift ;;
    --user)        SCOPE="user"; shift ;;
    --copy)        shift ;;  # Kept for compatibility: copying is the only mode.
    --link)        die "--link ya no existe: el instalador solo copia" ;;
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

[ -d "$SKILLS_ROOT/stable" ] || die "no encuentro $SKILLS_ROOT/stable"

# Skills

# A skill is a directory containing SKILL.md; runtime scratch and scaffolding are excluded.
list_skills() {  # $1 tier directory
  local dir name
  for dir in "$SKILLS_ROOT/$1"/*/; do
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

# Stable skills win: an experimental skill with the same name is not offered.
SKILLS_STABLE="$(list_skills stable)"
SKILLS_EXP=""
for s in $(list_skills experimental); do
  printf '%s\n' "$SKILLS_STABLE" | grep -qxF "$s" || SKILLS_EXP="${SKILLS_EXP:+$SKILLS_EXP$NL}$s"
done
SKILLS_ALL="$SKILLS_STABLE${SKILLS_EXP:+$NL$SKILLS_EXP}"
[ -n "$SKILLS_STABLE" ] || die "no hay skills con SKILL.md en $SKILLS_ROOT/stable"

is_experimental() { printf '%s\n' "$SKILLS_EXP" | grep -qxF "$1"; }

skill_src() {  # $1 skill
  if is_experimental "$1"; then printf '%s' "$SKILLS_ROOT/experimental/$1"
  else printf '%s' "$SKILLS_ROOT/stable/$1"; fi
}

EXP_NOTE="experimentales: en desarrollo, sin validar"

if [ "$ACTION" = "list" ]; then
  info "${C_B}Skills estables${C_OFF}  $(tilde "$SKILLS_ROOT/stable")"
  for s in $SKILLS_STABLE; do
    printf '  %-26s %s\n' "$s" "$(skill_desc "$(skill_src "$s")/SKILL.md")"
  done
  if [ -n "$SKILLS_EXP" ]; then
    info ""
    info "${C_B}Skills ${EXP_NOTE}${C_OFF}  $(tilde "$SKILLS_ROOT/experimental")"
    for s in $SKILLS_EXP; do
      printf '  %-26s %s\n' "$s" "$(skill_desc "$(skill_src "$s")/SKILL.md")"
    done
    dim "  (se instalan con --skills o con --all --experimental)"
  fi
  exit 0
fi

# Manifest: <skill> TAB <absolute path> TAB <mode>. Mode is always "copy" now;
# "link" entries may remain from earlier versions.

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
  MANIFEST_DATA="$(printf '%s\n' "$MANIFEST_DATA" | awk -F'\t' -v p="$2" 'NF && $2 != p')"
  MANIFEST_DATA="${MANIFEST_DATA:+$MANIFEST_DATA$NL}$line"
  [ "$DRY_RUN" -eq 1 ] && return 0
  mkdir -p "$(dirname "$MANIFEST")"
  # One line per path: a reinstall replaces the previous entry.
  touch "$MANIFEST"
  awk -F'\t' -v p="$2" '$2 != p' "$MANIFEST" > "$MANIFEST.tmp"
  printf '%s\n' "$line" >> "$MANIFEST.tmp"
  mv "$MANIFEST.tmp" "$MANIFEST"
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
# $1 title, $2 default, $3 newline-delimited id|mark|hint items, $4 optional footer.
# Items whose id starts with "--" are unnumbered, unselectable header rows.
choose() {
  local title="$1" dflt="$2" items="$3" footer="${4:-}"
  local n=0 it reply out="" ids="" i tok lo hi id rest mark hint oldifs
  {
    printf '\n%s%s%s\n' "$C_B" "$title" "$C_OFF"
    oldifs="$IFS"; IFS="$NL"
    for it in $items; do
      id="${it%%|*}"; rest="${it#*|}"; mark="${rest%%|*}"; hint="${rest#*|}"
      case "$id" in
        --*) printf '     %s── %s ──%s\n' "$C_DIM" "$hint" "$C_OFF"; continue ;;
      esac
      n=$((n + 1))
      ids="${ids:+$ids$NL}$id"
      printf ' %1s %2d) %-26s %s%s%s\n' "$mark" "$n" "$id" "$C_DIM" "$hint" "$C_OFF"
    done
    IFS="$oldifs"
    [ -n "$footer" ] && printf '%s%s%s\n' "$C_DIM" "$footer" "$C_OFF"
  } > /dev/tty
  reply="$(ask '> ')"
  case "$reply" in
    "")            printf '%s' "$dflt"; return ;;
    all|ALL|todas) printf '%s' "$ids" | tr '\n' ' '; return ;;
    none|NONE)     printf ''; return ;;
  esac
  for tok in $reply; do
    case "$tok" in
      *-*) lo="${tok%%-*}"; hi="${tok##*-}"
           case "$lo$hi" in ""|*[!0-9]*) warn "ignoro '$tok'"; continue ;; esac
           i="$lo" ;;
      *[!0-9]*) warn "ignoro '$tok'"; continue ;;
      *)   lo="$tok"; hi="$tok"; i="$tok" ;;
    esac
    while [ "$i" -le "$hi" ]; do
      id="$(printf '%s\n' "$ids" | sed -n "${i}p")"
      if [ -z "$id" ]; then
        warn "fuera de rango: $i"
      else
        case " $out " in *" $id "*) ;; *) out="$out $id" ;; esac
      fi
      i=$((i + 1))
    done
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

# A provider is detected when its base directory exists (.claude, .agents, ...).
provider_detected() {  # $1 id, $2 scope, $3 base
  [ -d "$(dirname "$(provider_dest_for "$1" "$2" "$3")")" ]
}

# Project destination: the Git root of the working directory, or the working directory itself.
# Physical paths (pwd -P) keep manifest entries stable across symlinked paths.

if [ -z "$PROJECT_DIR" ]; then
  PROJECT_DIR="$(git -C "$PWD" rev-parse --show-toplevel 2>/dev/null || pwd -P)"
else
  [ -d "$PROJECT_DIR" ] || die "no existe el proyecto: $PROJECT_DIR"
  PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd -P)"
fi

IS_SELF=0
[ "$PROJECT_DIR" = "$REPO_DIR" ] && IS_SELF=1

# ------------------------------------------------------- installed state ----

# evals/ and *-workspace are authoring material, not runtime: they are neither copied nor compared.
same_as_catalog() {  # $1 catalog source, $2 installed copy
  diff -rq -x evals -x '*-workspace' -x .DS_Store "$1" "$2" >/dev/null 2>&1
}

copy_skill() {  # $1 source, $2 destination (must not exist)
  cp -R "$1" "$2" \
    && find "$2" \( -name evals -o -name '*-workspace' -o -name .DS_Store \) -prune -exec rm -rf {} +
}

is_catalog_link() {  # $1 path; symlinks created by earlier versions of this script
  [ -L "$1" ] || return 1
  case "$(readlink "$1")" in "$REPO_DIR"/skills/*) return 0 ;; esac
  return 1
}

# State of a skill at one destination path:
#   nueva       nothing there
#   al-dia      identical to the catalog
#   actualizar  installed by this script (or a symlink to this repo) and different from the catalog
#   distinta    something else with the same name that this script did not install
skill_state() {  # $1 skill, $2 destination path
  if [ -L "$2" ]; then
    if is_catalog_link "$2" || manifest_has "$2"; then printf 'actualizar'; else printf 'distinta'; fi
  elif [ ! -e "$2" ]; then
    printf 'nueva'
  elif [ -d "$2" ] && same_as_catalog "$(skill_src "$1")" "$2"; then
    printf 'al-dia'
  elif manifest_has "$2"; then
    printf 'actualizar'
  else
    printf 'distinta'
  fi
}

state_label() {
  case "$1" in
    al-dia)     printf 'al dia' ;;
    actualizar) printf 'actualizar' ;;
    distinta)   printf '%sdistinta%s' "$C_WARN" "$C_OFF" ;;
    falta)      printf 'falta en disco' ;;
    *)          printf '%s' "$1" ;;
  esac
}

# Per-provider states of a skill in a scope, as "provider:state" words. Includes providers where
# something exists on disk or the manifest records an entry ("falta" when it is gone).
skill_presence() {  # $1 skill, $2 scope, $3 base
  local id dest out=""
  for id in $PROVIDER_IDS; do
    dest="$(provider_dest_for "$id" "$2" "$3")/$1"
    if [ -e "$dest" ] || [ -L "$dest" ]; then
      out="$out $id:$(skill_state "$1" "$dest")"
    elif manifest_has "$dest"; then
      out="$out $id:falta"
    fi
  done
  printf '%s' "${out# }"
}

# Menu mark, worst state first: ~ distinta, * actualizable, ! falta en disco, = al dia.
MARK_LEGEND="= al dia · * hay actualizacion · ~ distinta (no la instalo este script) · ! falta en disco"
presence_mark() {  # $1 output of skill_presence
  case " $1 " in
    *:distinta\ *)   printf '~' ;;
    *:actualizar\ *) printf '*' ;;
    *:falta\ *)      printf '!' ;;
    *:al-dia\ *)     printf '=' ;;
  esac
}

# "state: providers" groups, e.g. "al dia: claude, agents · actualizar: cursor".
presence_summary() {  # $1 output of skill_presence
  local st w ids out=""
  for st in al-dia actualizar distinta falta nueva; do
    ids=""
    for w in $1; do [ "${w#*:}" = "$st" ] && ids="${ids:+$ids, }${w%%:*}"; done
    [ -n "$ids" ] && out="${out:+$out · }$(state_label "$st"): $ids"
  done
  printf '%s' "$out"
}

print_scope_status() {  # $1 label, $2 scope, $3 base
  local s pr tag n=0
  info "${C_B}$1${C_OFF}  $(tilde "$3")"
  for s in $SKILLS_ALL; do
    pr="$(skill_presence "$s" "$2" "$3")"
    [ -n "$pr" ] || continue
    tag=""; is_experimental "$s" && tag="exp"
    printf '  %-26s %-4s %s\n' "$s" "$tag" "$(presence_summary "$pr")"
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
  dim "distinta = existe con ese nombre y no la instalo este script"
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
  [ -n "$KEEP" ] && dim "Quedan otras entradas registradas: $SELF --status"
  exit 0
fi

# Skill selection: Enter and --all mean stable skills; experimental ones are opt-in.

add_word() {  # $1 list, $2 word; appends without duplicates
  case " $1 " in *" $2 "*) printf '%s' "$1" ;; *) printf '%s' "${1:+$1 }$2" ;; esac
}

if [ "$WANT_SKILLS" = "__all__" ]; then
  SEL_SKILLS="$SKILLS_STABLE"
  [ "$WITH_EXPERIMENTAL" -eq 1 ] && SEL_SKILLS="$SKILLS_ALL"
elif [ -n "$WANT_SKILLS" ]; then
  SEL_SKILLS=""
  for s in $(printf '%s' "$WANT_SKILLS" | tr ',' ' '); do
    printf '%s\n' "$SKILLS_ALL" | grep -qxF "$s" || die "skill inexistente: $s (proba --list)"
    SEL_SKILLS="$(add_word "$SEL_SKILLS" "$s")"
  done
elif [ "$INTERACTIVE" -eq 1 ]; then
  MENU=""; ANY_MARK=0; HEADER_DONE=0
  for s in $SKILLS_ALL; do
    if [ "$HEADER_DONE" -eq 0 ] && is_experimental "$s"; then
      MENU="$MENU$NL--||$EXP_NOTE"; HEADER_DONE=1
    fi
    pr="$(skill_presence "$s" "$SCOPE" "$BASE")"
    desc="$(skill_desc "$(skill_src "$s")/SKILL.md" 60)"
    if [ -n "$pr" ]; then
      ANY_MARK=1
      provs="$(printf '%s' "$pr" | sed 's/:[a-z-]*//g; s/ /,/g')"
      MENU="${MENU:+$MENU$NL}$s|$(presence_mark "$pr")|[$provs] $(skill_desc "$(skill_src "$s")/SKILL.md" 48)"
    else
      MENU="${MENU:+$MENU$NL}$s||$desc"
    fi
  done
  FOOTER="  Enter = estables · all = todas · varias: \"1 3\" o \"1-4\" · none"
  [ "$ANY_MARK" -eq 1 ] && FOOTER="  $MARK_LEGEND$NL$FOOTER"
  SEL_SKILLS="$(choose "Que skills instalar en $(tilde "$BASE")?" "$SKILLS_STABLE" "$MENU" "$FOOTER")"
else
  die "sin tty: usa --skills o --all"
fi
[ -n "$(printf '%s' "$SEL_SKILLS" | tr -d '[:space:]')" ] || { info "ninguna skill seleccionada"; exit 0; }

# Provider selection: Claude and Agents are always offered; the rest only when detected.
# Default: Claude, plus Agents when its directory already exists.

PROV_MENU_IDS=""
for p in $PROVIDER_IDS; do
  case "$p" in claude|agents) ;; *) provider_detected "$p" "$SCOPE" "$BASE" || continue ;; esac
  PROV_MENU_IDS="$(add_word "$PROV_MENU_IDS" "$p")"
done
DEFAULT_PROVIDERS="claude"
provider_detected agents "$SCOPE" "$BASE" && DEFAULT_PROVIDERS="claude agents"

if [ -n "$WANT_PROVIDERS" ]; then
  SEL_PROVIDERS=""
  for p in $(printf '%s' "$WANT_PROVIDERS" | tr ',' ' '); do
    [ -n "$(provider_label "$p")" ] || die "agente desconocido: $p (opciones: $PROVIDER_IDS)"
    SEL_PROVIDERS="$(add_word "$SEL_PROVIDERS" "$p")"
  done
elif [ "$INTERACTIVE" -eq 1 ]; then
  MENU=""
  for p in $PROV_MENU_IDS; do
    mk=""; provider_detected "$p" "$SCOPE" "$BASE" && mk="*"
    MENU="${MENU:+$MENU$NL}$p|$mk|$(provider_label "$p")  $(tilde "$(provider_dest "$p")")"
  done
  SEL_PROVIDERS="$(choose "Para que agentes?" "$DEFAULT_PROVIDERS" "$MENU" \
    "  * = detectado · Enter = $(printf '%s' "$DEFAULT_PROVIDERS" | sed 's/ / + /') · varias: \"1 2\" o \"1-2\"")"
else
  SEL_PROVIDERS="$DEFAULT_PROVIDERS"
fi
[ -n "$(printf '%s' "$SEL_PROVIDERS" | tr -d '[:space:]')" ] || { info "ningun agente seleccionado"; exit 0; }

# Plan: classify every skill x provider before asking anything.

PLAN=""; N_ACT=0; N_DIFF=0
for s in $SEL_SKILLS; do
  for p in $SEL_PROVIDERS; do
    st="$(skill_state "$s" "$(provider_dest "$p")/$s")"
    PLAN="${PLAN:+$PLAN$NL}$s|$p|$st"
    case "$st" in
      nueva|actualizar) N_ACT=$((N_ACT + 1)) ;;
      distinta)         N_DIFF=$((N_DIFF + 1)) ;;
    esac
  done
done

plan_state() {  # $1 skill, $2 provider
  printf '%s\n' "$PLAN" | awk -F'|' -v s="$1" -v p="$2" '$1==s && $2==p {print $3; exit}'
}

fmt_list() { printf '%s' "$1" | tr '\n' ' ' | tr -s ' ' | sed 's/^ //;s/ $//'; }

info ""
info "${C_B}Plan${C_OFF}  $(tilde "$BASE") ($SCOPE) · $(fmt_list "$SEL_PROVIDERS" | sed 's/ /, /g')"
for s in $SEL_SKILLS; do
  words=""
  for p in $SEL_PROVIDERS; do words="$words $p:$(plan_state "$s" "$p")"; done
  words="${words# }"
  first="${words%% *}"; first="${first#*:}"
  same=1
  for w in $words; do [ "${w#*:}" = "$first" ] || same=0; done
  if [ "$same" -eq 1 ]; then line="$(state_label "$first")"; else line="$(presence_summary "$words")"; fi
  tag=""; is_experimental "$s" && tag="exp"
  printf '  %-26s %-4s %s\n' "$s" "$tag" "$line"
done
[ "$N_DIFF" -gt 0 ] && dim "  distinta = ya existe con ese nombre y no la instalo este script"
[ "$DRY_RUN" -eq 1 ] && dim "  (dry-run: no se escribe nada)"
info ""

OVERWRITE="$FORCE"
if [ "$N_ACT" -eq 0 ] && [ "$N_DIFF" -eq 0 ]; then
  # Nothing to copy; record identical copies that were not installed by this script.
  for s in $SEL_SKILLS; do
    for p in $SEL_PROVIDERS; do
      d="$(provider_dest "$p")/$s"
      manifest_has "$d" || manifest_add "$s" "$d" "copy"
    done
  done
  info "Todo al dia."
  exit 0
elif [ "$N_DIFF" -gt 0 ] && [ "$FORCE" -eq 0 ] && [ "$ASSUME_YES" -eq 0 ]; then
  [ "$TTY_OK" -eq 1 ] || die "sin tty: agrega -y para confirmar"
  r="$(ask "Procedo? [S]i, salteando distintas · [p]isar · [n]o ")"
  case "$r" in
    ""|s|S|y|Y|si|SI|yes|YES) ;;
    p|P|pisar) OVERWRITE=1 ;;
    *) info "cancelado"; exit 0 ;;
  esac
  info ""
elif [ "$ASSUME_YES" -eq 0 ]; then
  confirm "Procedo?" || { info "cancelado"; exit 0; }
  info ""
fi

# Installation: copy to a temporary sibling, back up what gets replaced, then swap.

BACKED_UP=0
install_one() {  # $1 skill, $2 provider
  local name="$1" dir dest src tmp bak=""
  dir="$(provider_dest "$2")"; dest="$dir/$name"; src="$(skill_src "$name")"
  tmp="$dir/.$name.ai-tools-tmp"
  if [ -e "$dest" ] && [ ! -L "$dest" ]; then bak="$BACKUP_DIR/$2/$name"; fi
  if [ "$DRY_RUN" -eq 1 ]; then
    printf '%s  dry%s  copia %s -> %s%s\n' "$C_DIM" "$C_OFF" "$(tilde "$src")" "$(tilde "$dest")" \
      "${bak:+  (backup en $(tilde "$bak"))}"
    manifest_add "$name" "$dest" "copy"
    return 0
  fi
  mkdir -p "$dir" || return 1
  rm -rf "$tmp"
  copy_skill "$src" "$tmp" || { rm -rf "$tmp"; return 1; }
  if [ -L "$dest" ]; then
    rm -f "$dest" || { rm -rf "$tmp"; return 1; }
  elif [ -n "$bak" ]; then
    { mkdir -p "$(dirname "$bak")" && mv "$dest" "$bak"; } || { rm -rf "$tmp"; return 1; }
    BACKED_UP=1
  fi
  mv "$tmp" "$dest" || return 1
  manifest_add "$name" "$dest" "copy"
}

INSTALLED=0; UPTODATE=0; FAILED=0; SKIPPED=""
for s in $SEL_SKILLS; do
  done_one=0; all_current=1
  for p in $SEL_PROVIDERS; do
    st="$(plan_state "$s" "$p")"; d="$(provider_dest "$p")/$s"
    case "$st" in
      al-dia)
        manifest_has "$d" || manifest_add "$s" "$d" "copy"
        continue ;;
      distinta)
        all_current=0
        if [ "$OVERWRITE" -ne 1 ]; then SKIPPED="${SKIPPED:+$SKIPPED, }$s ($p)"; continue; fi ;;
      *) all_current=0 ;;
    esac
    if install_one "$s" "$p"; then
      [ "$DRY_RUN" -eq 1 ] || ok "$s -> $(tilde "$d")"
      done_one=1
    else
      warn "no pude instalar $s en $(tilde "$d")"; FAILED=$((FAILED + 1))
    fi
  done
  [ "$done_one" -eq 1 ] && INSTALLED=$((INSTALLED + 1))
  [ "$all_current" -eq 1 ] && UPTODATE=$((UPTODATE + 1))
done

SUMMARY="$INSTALLED instalada(s) o actualizada(s)"
[ "$UPTODATE" -gt 0 ] && SUMMARY="$SUMMARY · $UPTODATE al dia"
info ""
if [ "$DRY_RUN" -eq 1 ]; then
  info "${C_B}Dry-run${C_OFF}  $SUMMARY  ${C_DIM}(nada escrito)${C_OFF}"
else
  info "${C_B}Listo${C_OFF}  $SUMMARY"
fi
[ -n "$SKIPPED" ] && warn "salteadas por distintas: $SKIPPED  (--force para pisarlas)"
[ "$BACKED_UP" -eq 1 ] && dim "Lo reemplazado quedo en $(tilde "$BACKUP_DIR")"
dim "Estado: $SELF --status  ·  revertir: $SELF --uninstall"
if [ "$INSTALLED" -eq 0 ] && { [ -n "$SKIPPED" ] || [ "$FAILED" -gt 0 ]; }; then exit 1; fi
exit 0
