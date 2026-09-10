#!/usr/bin/env bash
# Creator Dial - Installer
# Installs the ASUS DialPad replacement for Linux
set -euo pipefail

VERSION="1.0.0"
INSTALL_DIR="$HOME/.local/share/creatordial"
CONFIG_DIR="$HOME/.config/creatordial"
SERVICE_DIR="$HOME/.config/systemd/user"
UDEV_DIR="/etc/udev/rules.d"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log()    { echo -e "${GREEN}[+]${NC} $1"; }
warn()   { echo -e "${YELLOW}[!]${NC} $1"; }
error()  { echo -e "${RED}[-]${NC} $1"; }
info()   { echo -e "${BLUE}[i]${NC} $1"; }

check_deps() {
    log "Checking dependencies..."
    local deps=("python3" "python3-pip" "python3-venv")
    local missing=()

    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &>/dev/null && ! dpkg -l "$dep" &>/dev/null 2>&1; then
            missing+=("$dep")
        fi
    done

    if [ ${#missing[@]} -gt 0 ]; then
        error "Missing dependencies: ${missing[*]}"
        info "Install with: sudo apt install ${missing[*]}"
        return 1
    fi

    log "All dependencies found"
}

detect_hardware() {
    log "Detecting hardware..."

    local product
    product=$(cat /sys/devices/virtual/dmi/id/product_name 2>/dev/null || echo "Unknown")
    info "Laptop: $product"

    if grep -q "DialPad" /proc/bus/input/devices 2>/dev/null; then
        log "DialPad device detected"
        return 0
    else
        warn "DialPad virtual device not found in /proc/bus/input/devices"
        warn "It may appear after I2C activation"
        return 0
    fi
}

setup_directories() {
    log "Creating directories..."
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$CONFIG_DIR/profiles"
    mkdir -p "$CONFIG_DIR/themes"
    mkdir -p "$SERVICE_DIR"
}

setup_venv() {
    log "Setting up Python virtual environment..."
    if [ ! -d "$INSTALL_DIR/.venv" ]; then
        python3 -m venv "$INSTALL_DIR/.venv"
    fi

    log "Installing Python packages..."
    "$INSTALL_DIR/.venv/bin/pip" install --upgrade pip
    "$INSTALL_DIR/.venv/bin/pip" install \
        libevdev \
        pyinotify \
        python-periphery \
        PySide6 \
        xkbcommon \
        pygobject

    log "Virtual environment ready"
}

install_files() {
    log "Installing Creator Dial files..."
    local script_dir
    script_dir="$(cd "$(dirname "$0")" && pwd)"

    cp -r "$script_dir/creatordial" "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/creatordial/daemon.py"
    chmod +x "$INSTALL_DIR/creatordial/ui_main.py"
    chmod +x "$INSTALL_DIR/creatordial/debug.py"

    log "Files installed to $INSTALL_DIR"
}

setup_user_groups() {
    log "Setting up user groups..."
    local groups=("input" "i2c" "uinput")
    local current_groups
    current_groups=$(groups)

    for group in "${groups[@]}"; do
        if ! echo "$current_groups" | grep -qw "$group"; then
            if getent group "$group" &>/dev/null; then
                sudo usermod -aG "$group" "$USER" 2>/dev/null || true
                log "Added user to group: $group"
            else
                warn "Group $group does not exist"
            fi
        fi
    done
}

install_udev() {
    log "Installing udev rules..."
    local script_dir
    script_dir="$(cd "$(dirname "$0")" && pwd)"

    if [ -f "$script_dir/udev/99-creatordial.rules" ]; then
        sudo cp "$script_dir/udev/99-creatordial.rules" "$UDEV_DIR/"
        sudo udevadm control --reload-rules
        sudo udevadm trigger
        log "udev rules installed"
    fi
}

install_services() {
    log "Installing systemd services..."
    local script_dir
    script_dir="$(cd "$(dirname "$0")" && pwd)"

    for service in creatordial-daemon.service creatordial-ui.service; do
        if [ -f "$script_dir/systemd/$service" ]; then
            sed "s|%h|$HOME|g; s|%t|/run/user/$(id -u)|g" \
                "$script_dir/systemd/$service" > "$SERVICE_DIR/$service"
            log "Installed service: $service"
        fi
    done

    systemctl --user daemon-reload
    systemctl --user enable creatordial-daemon.service
    systemctl --user enable creatordial-ui.service
    log "Services enabled"
}

setup_config() {
    log "Setting up configuration..."
    if [ ! -f "$CONFIG_DIR/config.json" ]; then
        cat > "$CONFIG_DIR/config.json" << 'CONFIGEOF'
{
  "enabled": false,
  "activation_time": 1.0,
  "rotation_threshold": 90.0,
  "sensitivity": 1.0,
  "inactivity_timeout": 0,
  "coactivator_key": "",
  "touchpad_disables_dialpad": true,
  "layout": {
    "circle_diameter": 1400,
    "center_button_diameter": 250,
    "circle_center_x": 770,
    "circle_center_y": 750,
    "top_right_icon_width": 250,
    "top_right_icon_height": 250
  },
  "plugins": {
    "volume": {"enabled": true, "step": 5},
    "brightness": {"enabled": true, "step": 5},
    "gpu": {"enabled": true},
    "media": {"enabled": true},
    "keyboard": {"enabled": true},
    "screen": {"enabled": true},
    "nightlight": {"enabled": true}
  },
  "theme": "default",
  "debug": false
}
CONFIGEOF
        log "Default config created"
    else
        info "Config already exists, skipping"
    fi
}

uninstall() {
    log "Uninstalling Creator Dial..."

    systemctl --user stop creatordial-daemon.service 2>/dev/null || true
    systemctl --user stop creatordial-ui.service 2>/dev/null || true
    systemctl --user disable creatordial-daemon.service 2>/dev/null || true
    systemctl --user disable creatordial-ui.service 2>/dev/null || true

    rm -f "$SERVICE_DIR/creatordial-daemon.service"
    rm -f "$SERVICE_DIR/creatordial-ui.service"
    systemctl --user daemon-reload

    rm -rf "$INSTALL_DIR"

    sudo rm -f "$UDEV_DIR/99-creatordial.rules"
    sudo udevadm control --reload-rules

    log "Uninstalled. Config preserved at $CONFIG_DIR"
}

print_status() {
    echo ""
    echo "======================================"
    echo "  Creator Dial v$VERSION"
    echo "======================================"
    echo ""
    echo "  Installation: $INSTALL_DIR"
    echo "  Config:       $CONFIG_DIR"
    echo "  Services:     $SERVICE_DIR"
    echo ""
    echo "  Commands:"
    echo "    Start:    systemctl --user start creatordial-daemon creatordial-ui"
    echo "    Stop:     systemctl --user stop creatordial-daemon creatordial-ui"
    echo "    Status:   systemctl --user status creatordial-daemon"
    echo "    Logs:     journalctl --user -u creatordial-daemon -f"
    echo "    Debug:    $INSTALL_DIR/.venv/bin/python3 $INSTALL_DIR/creatordial/debug.py"
    echo "    Uninstall: $0 --uninstall"
    echo ""
    echo "  NOTE: You may need to log out and back in for"
    echo "        group changes to take effect."
    echo ""
}

case "${1:-}" in
    --uninstall)
        uninstall
        ;;
    --status)
        systemctl --user status creatordial-daemon.service 2>/dev/null || echo "Not running"
        ;;
    *)
        echo "Creator Dial v$VERSION Installer"
        echo "================================"
        echo ""
        check_deps
        detect_hardware
        setup_directories
        setup_venv
        install_files
        setup_user_groups
        install_udev
        install_services
        setup_config
        print_status
        ;;
esac
