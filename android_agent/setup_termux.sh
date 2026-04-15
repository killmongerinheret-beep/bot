#!/data/data/com.termux/files/usr/bin/bash
# Vatican Agent — Termux Setup Script
# Run this once in Termux to install everything

echo "Setting up Vatican Browser Agent on Android..."

# Update packages
pkg update -y && pkg upgrade -y

# Install Python and required tools
pkg install -y python git termux-api

# Install Python dependencies
pip install requests

# Install Termux:API (needed to open Chrome)
# You also need to install "Termux:API" app from F-Droid
echo ""
echo "IMPORTANT: Install 'Termux:API' from F-Droid for Chrome opening to work"
echo ""

# Create autostart (runs agent when Termux opens)
mkdir -p ~/.termux/boot
cat > ~/.termux/boot/start_agent.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd ~/vatican_agent
python main.py --agent android-1 &
EOF
chmod +x ~/.termux/boot/start_agent.sh

# Copy agent files
mkdir -p ~/vatican_agent
cp main.py ~/vatican_agent/
cp agent_config.json ~/vatican_agent/

echo ""
echo "✅ Setup complete!"
echo ""
echo "Edit ~/vatican_agent/agent_config.json to set your agent_id"
echo ""
echo "To run now:"
echo "  cd ~/vatican_agent && python main.py --agent android-1"
echo ""
echo "Agent will auto-start when Termux opens (after installing Termux:Boot from F-Droid)"
