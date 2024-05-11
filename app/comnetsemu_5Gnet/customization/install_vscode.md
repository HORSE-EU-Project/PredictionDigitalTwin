Installa VSCode server: curl -fsSL https://code-server.dev/install.sh | sh
	- **To start/stop the service:** sudo systemctl start code-server@$USER
	- **To enable the service:** sudo systemctl enable --now code-server@$USER
	- **To configure the service:** nano ~/.config/code-server/config.yaml
