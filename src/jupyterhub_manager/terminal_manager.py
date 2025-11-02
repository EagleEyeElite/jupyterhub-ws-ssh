import json
import requests
import websocket
import time
import ssl
import truststore


class JupyterTerminal:
    def __init__(self, hub_url, token, username):
        self.hub_url = hub_url
        self.token = token
        self.username = username

        # Configure SSL
        truststore.inject_into_ssl()

        self.session = requests.Session()
        self.session.headers.update({'Authorization': f'token {self.token}'})

        self.server_url = None
        self.terminal_name = None
        self.ws = None
        self.output = []

    def connect(self):
        """One-step connection setup"""
        # Get server URL
        response = self.session.get(f"{self.hub_url}/hub/api/users/{self.username}")
        response.raise_for_status()

        user_data = response.json()
        if 'servers' not in user_data or '' not in user_data['servers']:
            raise Exception("No running server found. Please start your server first.")

        self.server_url = user_data['servers']['']['url']

        # Create terminal
        terminal_url = f"{self.hub_url}{self.server_url}api/terminals"
        response = self.session.post(terminal_url)
        response.raise_for_status()
        self.terminal_name = response.json()['name']

        # Connect WebSocket
        # Convert https:// to wss://
        ws_base = self.hub_url.replace('https://', 'wss://').replace('http://', 'ws://')
        ws_url = f"{ws_base}{self.server_url}terminals/websocket/{self.terminal_name}"

        self.ws = websocket.create_connection(
            ws_url,
            header={"Authorization": f"token {self.token}"},
            sslopt={"ssl_context": truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)}
        )

        time.sleep(1)  # Wait for initial prompt

    def execute(self, command, timeout=10):
        """Execute command and return output"""
        if not self.ws:
            self.connect()

        # Clear output buffer
        self.output = []

        # Send command
        self.ws.send(json.dumps(["stdin", f"{command}\n"]))

        # Collect output with simple timeout
        start_time = time.time()
        last_output_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # Check for new messages (non-blocking with short timeout)
                self.ws.settimeout(0.5)
                message = self.ws.recv()

                data = json.loads(message)
                if data[0] == "stdout":
                    output_text = data[1]
                    self.output.append(output_text)
                    print(output_text, end='', flush=True)
                    last_output_time = time.time()

                    # Simple completion check: look for common prompt patterns
                    if any(pattern in output_text for pattern in ['$ ', '# ', '> ']):
                        if time.time() - start_time > 1:  # Avoid immediate prompt detection
                            break

            except websocket.WebSocketTimeoutException:
                # No new output - check if we should stop waiting
                if time.time() - last_output_time > 2:  # 2 seconds of silence
                    break
            except Exception as e:
                print(f"Error reading output: {e}")
                break

        result = ''.join(self.output)
        return result

    def close(self):
        """Clean up connection"""
        if self.ws:
            self.ws.close()
