"""Allow running jupyterhub_manager as a module: python -m jupyterhub_manager"""

import os
import sys
from dotenv import load_dotenv

from src.jupyterhub_manager.start_server import start_server
from src.jupyterhub_manager.ssh_tunnel import setup_ssh_tunnel


# Configuration constants
HUB_URL = 'https://jupyterhub.domain.com'
PORT = 2022


def main():
    """Main entry point"""
    # Load environment variables
    load_dotenv()

    token = os.getenv('JUPYTERHUB_TOKEN', '').strip()
    if not token:
        print("✗ No JUPYTERHUB_TOKEN configured")
        sys.exit(1)

    username = os.getenv('JUPYTERHUB_USERNAME', '').strip()
    if not username:
        print("✗ No JUPYTERHUB_USERNAME configured")
        sys.exit(1)

    profile = os.getenv('JUPYTERHUB_PROFILE', '').strip()
    if not profile:
        print("✗ No JUPYTERHUB_PROFILE configured")
        sys.exit(1)

    print("=" * 70)
    print("JupyterHub SSH Connection Setup")
    print("=" * 70)
    print()

    # Start server
    print(f"⏳ Starting server for {username}...")
    try:
        start_server(HUB_URL, token, username, profile)
    except Exception as e:
        print(f"\n✗ Setup failed: {e}")
        sys.exit(1)

    # Setup SSH tunnel
    print("\nSetting up SSH tunnel on remote server...")
    try:
        setup_ssh_tunnel(HUB_URL, token, username, PORT)
    except Exception as e:
        print(f"\n✗ Setup failed during SSH tunnel setup: {e}")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("SSH Ready")
    print("=" * 70)
    print()
    print("Connect using:")
    print(f"  ssh user@jupyterhub")
    print()


if __name__ == "__main__":
    main()
