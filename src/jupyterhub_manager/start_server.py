import json
import time
import requests


def event_stream(session, url):
    """Generator yielding events from a JSON event stream"""
    r = session.get(url, stream=True)
    r.raise_for_status()
    for line in r.iter_lines():
        line = line.decode('utf8', 'replace')
        if line.startswith('data:'):
            yield json.loads(line.split(':', 1)[1])


def _request_start_server(session, hub_url, username, profile, max_retries=5):
    """Try to start server with retry logic for 'pending stop' errors"""
    for attempt in range(max_retries):
        try:
            r = session.post(f"{hub_url}/hub/api/users/{username}/server",
                             json={"profile": profile})
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Cannot reach JupyterHub {hub_url}. Are you connected to VPN?")

        # Check if we got a "pending stop" error and should retry
        if r.status_code == 400:
            try:
                error_data = r.json()
                if "pending stop" in error_data.get("message", "").lower():
                    if attempt < max_retries - 1:
                        print(f"⏳ Server is shutting down, waiting... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(1)
                        continue
                    else:
                        raise RuntimeError(f"Server is still shutting down after {max_retries} attempts. Please try again later.")
            except (ValueError, KeyError):
                pass  # Not a JSON response or missing message field

        # If we didn't continue, return the response
        return r

    # If we exhausted all retries, raise an error
    raise RuntimeError(f"Failed to start server after {max_retries} attempts")


def _process_start_response(session, hub_url, username, profile):
    """Request server start and process the response to return server URL"""
    # Request server start with retry logic
    r = _request_start_server(session, hub_url, username, profile)

    server_url = None

    match r.status_code:
        case 201:
            print("✅ Server ready")
            # Get server URL from user info
            user_r = session.get(f"{hub_url}/hub/api/users/{username}")
            user_r.raise_for_status()
            server_url = user_r.json()['servers']['']['url']

        case 202:
            # Monitor progress using the progress API
            progress_url = f"{hub_url}/hub/api/users/{username}/server/progress"
            for event in event_stream(session, progress_url):
                progress = event.get('progress', 0)
                message = event.get('message', '')
                print(f"[{progress}%] {message}")

                if event.get('ready'):
                    server_url = event.get('url', '')
                    break

        case 400:
            # Server already running or other error
            error_msg = r.json().get('message', 'Unknown error')
            if "already running" in error_msg.lower():
                raise RuntimeError(f"Cannot start server: {error_msg}\n\nStop the server here: {hub_url}/hub/home")
            else:
                raise RuntimeError(f"Cannot start server: {error_msg}")

        case _:  # Default case
            print(f"❌ Status: {r.json()}")

    # Exit if server is not ready
    if server_url is None:
        raise RuntimeError("Server not available")

    return server_url


def start_server(hub_url, token, username, profile):
    """Start JupyterHub server"""
    session = requests.Session()
    session.headers.update({
        'Authorization': f'token {token}',
        'Content-Type': 'application/json'
    })

    # Request server start and process response
    server_url = _process_start_response(session, hub_url, username, profile)

    print(f"✅ Server ready at: {hub_url}{server_url}")
