#!/bin/sh

if [ "$(id -u)" != "0" ]; then
    echo "This script must be executed as root. try 'sudo $0'"
    exit 1
fi

TARGET_USER="surgicue"
USER_HOME="/home/$TARGET_USER"
PYFILE_NAME="SurgiCue.py"
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
INSTALL_DIR="/usr/local/share/surgicue"

#create user
if ! id "$TARGET_USER" >/dev/null 2>&1; then
    adduser --disabled-password --gecos "" "$TARGET_USER"
    echo "created user $TARGET_USER"
else
    echo "user $TARGET_USER already exists"
fi
deluser "$TARGET_USER" sudo >/dev/null

#install dependencies
apt update
apt upgrade -y
apt install -y python3 python3-tk python3-pil python3-pil.imagetk xserver-xorg-core xinit openbox

mkdir -p "$INSTALL_DIR"
cp -r "$SCRIPT_DIR"/* "$INSTALL_DIR"/

#log directory
mkdir -p /var/log/surgicue
chown $TARGET_USER:$TARGET_USER /var/log/surgicue

# .xinitrc
cat > "$USER_HOME/.xinitrc" <<EOF
#!/bin/sh
cd "$INSTALL_DIR" || exit 1
python3 "$PYFILE_NAME"
EOF
chmod +x "$USER_HOME/.xinitrc"
chown $TARGET_USER:$TARGET_USER "$USER_HOME/.xinitrc"

# auto login
AUTOLOGIN_DIR="/etc/systemd/system/getty@tty1.service.d"
mkdir -p "$AUTOLOGIN_DIR"
cat > "$AUTOLOGIN_DIR/override.conf" <<EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin $TARGET_USER --noclear %I \$TERM
EOF

# startx when user logs in
PROFILE_FILE="$USER_HOME/.profile"
grep -qxF '# Auto-start X11' "$PROFILE_FILE" 2>/dev/null || {
    echo "" >> "$PROFILE_FILE"
    echo "# Auto-start X11" >> "$PROFILE_FILE"
    echo 'if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then' >> "$PROFILE_FILE"
    echo "    startx" >> "$PROFILE_FILE"
    echo "fi" >> "$PROFILE_FILE"
    chown $TARGET_USER:$TARGET_USER "$PROFILE_FILE"
}

systemctl daemon-reexec
systemctl restart getty@tty1
