"""SSH tunnel setup for JupyterHub"""

from .terminal_manager import JupyterTerminal


def setup_ssh_tunnel(hub_url, token, username, port):
    """Setup SSH service and websocat tunnel on the remote server"""
    commands = [
        "sudo service ssh start",
        f"./websocat --binary -E ws-l:0.0.0.0:{port} tcp:localhost:22 &",
    ]

    terminal = JupyterTerminal(hub_url, token, username)
    print(f"💻 Executing on Server:")
    try:
        for command in commands:
            terminal.execute(command, timeout=15)
    finally:
        terminal.close()
    print("\n📋 Execution done")
