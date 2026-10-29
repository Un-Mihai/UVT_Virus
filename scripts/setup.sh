#!/usr/bin/env bash
# Sets up this project on a new machine. Checks every tool, installs the ones that need no admin
# password or GUI, then prepares the project and starts the local stack.
#
#   bash scripts/setup.sh          install what is missing, create .env, install dependencies,
#                                  start the Docker stack (make setup)
#   bash scripts/setup.sh --check  only report what is installed and what is missing (make doctor)
#
# macOS installs with Homebrew. Linux and WSL install into ~/.local without sudo. It never installs
# Docker, WSL, Homebrew, Git or make and never runs sudo: it prints those steps for a human.
# Exit code 0 means nothing is left for a human to do.
set -euo pipefail
cd "$(dirname "$0")/.."

TERRAFORM_VERSION=1.17.0
POETRY_VERSION=2.5.1
NODE_MAJOR=24
PYTHON_VERSION=3.13
LOCAL_BIN="$HOME/.local/bin"
original_path=$PATH
export PATH="$LOCAL_BIN:$PATH"

case "${1:-}" in
  "") mode=install ;;
  --check) mode=check ;;
  *) echo "usage: bash scripts/setup.sh [--check]" >&2; exit 2 ;;
esac

os=$(uname -s)
arch=$(uname -m)
case "$arch" in x86_64 | amd64) arch=amd64 ;; arm64 | aarch64) arch=arm64 ;; esac
wsl=false
if grep -qi microsoft /proc/version 2>/dev/null; then wsl=true; fi

todo=()     # steps only a human can do, needed for the project to work
optional=() # steps a human may do for extras
notes=()

have() { command -v "$1" >/dev/null 2>&1; }
say() { printf '%s\n' "$*"; }
human() { todo+=("$*"); }
extra() { optional+=("$*"); }
note() { notes+=("$*"); }

# version_ge 24.22.1 22 -> true
version_ge() {
  local IFS=.
  local -a got=($1) want=($2)
  local i g w
  for ((i = 0; i < ${#want[@]}; i++)); do
    g=${got[i]:-0}; w=${want[i]:-0}
    g=${g%%[^0-9]*}; w=${w%%[^0-9]*}
    if ((10#${g:-0} > 10#${w:-0})); then return 0; fi
    if ((10#${g:-0} < 10#${w:-0})); then return 1; fi
  done
  return 0
}

version_of() {
  case "$1" in
    node) node --version 2>/dev/null | sed 's/^v//' ;;
    terraform) terraform version 2>/dev/null | sed -n '1s/^Terraform v//p' ;;
    az) az version --output tsv --query '"azure-cli"' 2>/dev/null ;;
    poetry) poetry --version 2>/dev/null | sed 's/[^0-9.]//g' ;;
    docker) docker compose version --short 2>/dev/null | sed 's/^v//' ;;
    git) git --version 2>/dev/null | awk '{print $3}' ;;
    make) make --version 2>/dev/null | sed -n '1s/[^0-9.]*\([0-9.]*\).*/\1/p' ;;
  esac
}

# tool | minimum version | who installs it | what it is for
TOOLS="git|2|you|clone and commit
docker|2.24|you|Docker Compose runs web, API and database
make|3|you, optional|shortcuts; every target is also a plain command
node|22|this script|editor types, Next.js docs for agents, make check-ui, MCP servers
terraform|1.9|this script|Azure deployment
az|2|this script|Azure login and deployment
poetry|2|this script|running the API outside Docker, editor support"

status_of() { # prints "ok <version>", "old <version>" or "missing"
  local tool=$1 min=$2 version
  if ! have "$tool"; then say missing; return; fi
  version=$(version_of "$tool")
  if [ -z "$version" ]; then
    say missing
  elif version_ge "$version" "$min"; then
    say "ok $version"
  else
    say "old $version"
  fi
}

report() {
  say ""
  printf '%-10s %-14s %-14s %s\n' TOOL STATUS INSTALLED-BY "USED FOR"
  local tool min by purpose
  while IFS='|' read -r tool min by purpose; do
    printf '%-10s %-14s %-14s %s\n' "$tool" "$(status_of "$tool" "$min")" "$by" "$purpose"
  done <<<"$TOOLS"
  if have docker && ! docker info >/dev/null 2>&1; then
    say "docker     installed, but the Docker engine is not running"
  fi
  say ""
}

download() { curl -fsSL --retry 2 -o "$2" "$1"; }

check_sum() { # check_sum <dir> <sums file> <file>
  local line
  line=$(grep " $3\$" "$1/$2") || return 1
  if have sha256sum; then
    (cd "$1" && printf '%s\n' "$line" | sha256sum -c - >/dev/null)
  else
    (cd "$1" && printf '%s\n' "$line" | shasum -a 256 -c - >/dev/null)
  fi
}

unzip_to() { # unzip_to <zip> <member> <dir>
  if have unzip; then
    unzip -oq "$1" "$2" -d "$3"
  elif have python3; then
    python3 -c 'import sys, zipfile; zipfile.ZipFile(sys.argv[1]).extract(sys.argv[2], sys.argv[3])' "$1" "$2" "$3"
  else
    return 1
  fi
}

# --- installers ----------------------------------------------------------------------------

brew_install() { brew install --quiet "$@"; }

install_node() {
  if [ "$os" = Darwin ]; then brew_install node; return; fi
  local base="https://nodejs.org/dist/latest-v${NODE_MAJOR}.x" tmp file bin platform=x64
  [ "$arch" = arm64 ] && platform=arm64
  tmp=$(mktemp -d)
  download "$base/SHASUMS256.txt" "$tmp/SHASUMS256.txt" || return 1
  file=$(grep -o "node-v[0-9.]*-linux-$platform\.tar\.gz" "$tmp/SHASUMS256.txt" | head -1)
  download "$base/$file" "$tmp/$file" || return 1
  check_sum "$tmp" SHASUMS256.txt "$file" || return 1
  rm -rf "$HOME/.local/share/node"
  mkdir -p "$HOME/.local/share/node" "$LOCAL_BIN"
  tar -xzf "$tmp/$file" -C "$HOME/.local/share/node" --strip-components 1 || return 1
  for bin in node npm npx; do ln -sf "$HOME/.local/share/node/bin/$bin" "$LOCAL_BIN/$bin"; done
  rm -rf "$tmp"
}

install_terraform() {
  if [ "$os" = Darwin ]; then brew_install hashicorp/tap/terraform; return; fi
  local base="https://releases.hashicorp.com/terraform/$TERRAFORM_VERSION" tmp
  local file="terraform_${TERRAFORM_VERSION}_linux_${arch}.zip"
  local sums="terraform_${TERRAFORM_VERSION}_SHA256SUMS"
  tmp=$(mktemp -d)
  download "$base/$file" "$tmp/$file" || return 1
  download "$base/$sums" "$tmp/$sums" || return 1
  check_sum "$tmp" "$sums" "$file" || return 1
  mkdir -p "$LOCAL_BIN"
  unzip_to "$tmp/$file" terraform "$LOCAL_BIN" || return 1
  chmod +x "$LOCAL_BIN/terraform"
  rm -rf "$tmp"
}

# On Linux, uv installs Python tools and Python itself without sudo.
ensure_uv() {
  have uv && return
  mkdir -p "$LOCAL_BIN"
  curl -fsSL https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="$LOCAL_BIN" UV_NO_MODIFY_PATH=1 sh >/dev/null
}

install_az() {
  if [ "$os" = Darwin ]; then brew_install azure-cli; return; fi
  ensure_uv && uv tool install --quiet azure-cli
}

install_poetry() {
  if [ "$os" = Darwin ]; then brew_install poetry; return; fi
  ensure_uv && uv tool install --quiet "poetry==$POETRY_VERSION"
}

# --- platform checks that need a human --------------------------------------------------------

case "$os" in
  Darwin)
    if ! have brew; then
      human 'Install Homebrew (asks for your password), then run this script again: /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    fi
    ;;
  Linux) ;;
  *)
    say "On Windows, run this script inside WSL (Ubuntu): wsl --install, then clone the repo in the WSL file system."
    say "Native Windows alternative, in PowerShell: winget install Git.Git Docker.DockerDesktop OpenJS.NodeJS.LTS Hashicorp.Terraform Microsoft.AzureCLI Python.Python.3.13"
    exit 1
    ;;
esac

if ! have curl; then human "Install curl (Ubuntu: sudo apt install curl)."; fi
if ! have git; then
  if [ "$os" = Darwin ]; then human "Install Git: xcode-select --install"; else human "Install Git: sudo apt install git"; fi
fi
if ! have make; then
  if [ "$os" = Darwin ]; then extra "make: xcode-select --install"; else extra "make: sudo apt install make"; fi
fi
if ! have docker; then
  if $wsl; then
    human "Install Docker Desktop on Windows (https://docs.docker.com/desktop/setup/install/windows-install/), then enable Settings > Resources > WSL integration for this distro."
  elif [ "$os" = Darwin ]; then
    human "Install Docker Desktop (https://docs.docker.com/desktop/setup/install/mac-install/) and start it once."
  else
    human "Install Docker Engine (https://docs.docker.com/engine/install/) and add yourself to the docker group."
  fi
elif ! docker info >/dev/null 2>&1; then
  human "Start Docker Desktop (or the Docker engine), then run this script again."
elif ! version_ge "$(version_of docker)" 2.24; then
  human "Update Docker: Compose 2.24 or newer is required."
fi
case "$PWD" in
  /mnt/[a-z]/*) $wsl && human "Move the repo into the WSL file system (for example ~/code): under /mnt/c, file watching and builds are slow." ;;
esac

# --- check mode -------------------------------------------------------------------------------

finish() {
  local line
  for line in ${notes[@]+"${notes[@]}"}; do say "Done: $line"; done
  for line in ${optional[@]+"${optional[@]}"}; do say "Optional: $line"; done
  for line in ${todo[@]+"${todo[@]}"}; do say "Needs you: $line"; done
}

if [ "$mode" = check ]; then
  report
  missing=0
  while IFS='|' read -r tool min by _; do
    if [ "$by" = "this script" ]; then
      case "$(status_of "$tool" "$min")" in ok*) ;; *) missing=1 ;; esac
    fi
  done <<<"$TOOLS"
  finish
  if [ "$missing" = 1 ]; then say "Run 'bash scripts/setup.sh' (make setup) to install the missing tools."; fi
  if [ "$missing" = 1 ] || [ ${#todo[@]} -gt 0 ]; then exit 1; fi
  say "Everything needed is installed."
  exit 0
fi

# --- install mode -----------------------------------------------------------------------------

if [ "$os" = Darwin ] && ! have brew; then
  say "Homebrew is required on macOS to install the tools."
  finish
  exit 1
fi

for tool in node terraform az poetry; do
  min=$(printf '%s\n' "$TOOLS" | awk -F'|' -v t="$tool" '$1 == t {print $2}')
  case "$(status_of "$tool" "$min")" in
    ok*) continue ;;
  esac
  say "Installing $tool..."
  "install_$tool" || true
  case "$(status_of "$tool" "$min")" in
    ok*) note "installed $tool $(version_of "$tool")" ;;
    *) human "Install $tool by hand: see the Tools table in README.md." ;;
  esac
done

if [ ! -f .env ]; then
  : > .env
  note "created an empty .env: add an AI key (docs/ai-providers.md)"
fi

# npm writes node_modules/.package-lock.json on install; skip when the lock file has not changed.
if have npm && { [ ! -f web/node_modules/.package-lock.json ] || [ web/package-lock.json -nt web/node_modules/.package-lock.json ]; }; then
  say "Installing web dependencies..."
  (cd web && npm ci --no-audit --no-fund --no-update-notifier --loglevel=error) && note "installed web dependencies (editor types, Next.js docs in web/node_modules/next/dist/docs)"
fi

if have poetry; then
  say "Creating api/.venv..."
  python=""
  if [ "$os" = Darwin ]; then
    have "python$PYTHON_VERSION" || brew_install "python@$PYTHON_VERSION" || true
    python=$(command -v "python$PYTHON_VERSION" || true)
  elif ensure_uv && uv python install --quiet "$PYTHON_VERSION"; then
    python=$(uv python find "$PYTHON_VERSION")
  fi
  if [ -n "$python" ] && (cd api && export POETRY_VIRTUALENVS_IN_PROJECT=true && poetry env use "$python" >/dev/null && poetry install --no-root --quiet); then
    note "created api/.venv (Python $PYTHON_VERSION) for editors and running the API outside Docker"
  else
    note "skipped api/.venv: Poetry could not create it (the API still runs in Docker)"
  fi
fi

# Impeccable's detector downloads its engine on first use; do it now rather than mid-task.
sh .agents/skills/impeccable/scripts/impeccable engine-probe >/dev/null 2>&1 && note "fetched impeccable's design detector" || true

web_port=$(sed -n 's/^WEB_PORT=//p' .env | tail -1)
web_port=${web_port:-3000}
if have docker && docker info >/dev/null 2>&1; then
  say "Starting the stack (the first build takes a few minutes)..."
  # A fresh web container, so node_modules matches the image (see make up in the Makefile).
  docker compose rm --stop --force --volumes web >/dev/null 2>&1 || true
  if docker compose up --build -d; then
    # Ready when the sign-in page answers: the web app and Keycloak are both up.
    sign_in="http://localhost:$web_port/auth/login"
    for _ in $(seq 1 90); do
      curl -fsSL -o /dev/null "$sign_in" 2>/dev/null && break
      sleep 2
    done
    if curl -fsSL -o /dev/null "$sign_in" 2>/dev/null; then
      note "stack running: http://localhost:$web_port (sign in as reviewer, password demo)"
    else
      human "The stack started but its sign-in page does not answer yet: check docker compose logs web keycloak."
    fi
  else
    human "docker compose up failed. If a port is taken, set WEB_PORT, API_PORT, DB_PORT or KEYCLOAK_PORT in .env and run this script again."
  fi
fi

report
finish
case ":$original_path:" in
  *":$LOCAL_BIN:"*) ;;
  *)
    if [ -d "$LOCAL_BIN" ]; then
      say "Tools were installed into $LOCAL_BIN, which is not on your PATH yet. Add it with:"
      say "  echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc"
    fi
    ;;
esac
if [ ${#todo[@]} -gt 0 ]; then exit 1; fi
say "Setup complete."
