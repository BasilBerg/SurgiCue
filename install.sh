#!/bin/sh

if [ "$(id -u)" != "0" ]; then
    echo "This script must be executed as root. try 'sudo $0'"
    exit 1
fi

#get username
read -p "Enter the user that will run the SurgiCue service:" TARGET_USER
if ! id "$TARGET_USER" >/dev/null 2>&1; then
    echo "User $TARGET_USER does not exist"
    exit 1
fi


USER_HOME=$(eval echo "~$TARGET_USER")
PYFILE_NAME="SurgiCue.py"

#install dependencies
apt update
apt upgrade -y
apt install -y python3 python3-tk python3-pil python3-pil.imagetk xserver-xorg-core xinit openbox

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
PYFILE="$SCRIPT_DIR/$PYFILE_NAME"

# create .xinitrc
echo "#!/bin/sh" > "$USER_HOME/.xinitrc"
echo "cd \"$SCRIPT_DIR\" || exit 1" >> "$USER_HOME/.xinitrc"
echo "python3 \"$PYFILE_NAME\"" >> "$USER_HOME/.xinitrc"
chmod +x "$USER_HOME/.xinitrc"
chown $TARGET_USER:$TARGET_USER "$USER_HOME/.xinitrc"

#create service
SERVICE_NAME="surgicue.service"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME"

cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Start X automatically for $TARGET_USER
After=systemd-user-sessions.service

[Service]
User=$TARGET_USER
WorkingDirectory=$SCRIPT_DIR
ExecStart=/usr/bin/startx
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF


systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl start "$SERVICE_NAME"

