# JupyterHub Manager

A Python tool for tunneling SSH to a JupyterHub container through jupyter-server-proxy endpoints.

### How it works

```mermaid
%%{init: {'themeVariables': {'background': 'transparent'}}}%%
flowchart LR
    user["💻 User<br/>ssh → websocket"]
    proxy["🌐 JupyterHub Proxy<br/>http"]
    n1["🖥️ Node 1"]
    n2["🖥️ Node 2<br/>websocket → ssh"]
    n3["🖥️ Node 3"]

    user --> proxy
    proxy -.- n1
    proxy --> n2
    proxy -.- n3

    classDef base fill:transparent,stroke:#64748b,stroke-width:2px
    classDef active fill:transparent,stroke:#3b82f6,stroke-width:3px
    classDef idle fill:transparent,stroke:#9ca3af,stroke-dasharray:4 3
    class user,proxy base
    class n2 active
    class n1,n3 idle
    linkStyle 0,2 stroke:#3b82f6,stroke-width:2px
    linkStyle 1,3 stroke:#9ca3af
```

1. `ssh` doesn't open a TCP connection itself; its `ProxyCommand` runs `websocat`,
   which wraps the SSH byte stream in a WebSocket (`wss://`, port 443).
2. The JupyterHub proxy checks the API token and routes the request by its
   path `/user/<name>/` to the node running that user's server.
3. On that node, `jupyter-server-proxy` forwards `/proxy/2022` to local port 2022,
   where `websocat` (started by `python -m src.jupyterhub_manager`) unwraps the
   WebSocket back into raw TCP and hands it to `sshd` on port 22.

### Prerequisites:
- Request a [Jupyterhub API Token](https://jupyterhub.domain.com/hub/token)
- Create .env file and update info: `cp .env.example .env`
- Setup ssh keys:
  - Get your public key (on client): `cat ~/.ssh/id_ed25519.pub`
  - Add public key to jupyterhub container (on server) `nano ~/.ssh/authorized_keys`
- Install `websocat` on server:
  - `wget https://github.com/vi/websocat/releases/latest/download/websocat.x86_64-unknown-linux-musl -O ~/websocat`
  - `chmod +x ~/websocat`
- Install `websocat` on client (for example):
    - `cargo install websocat`
- Add this (on client) to `~/.ssh/config`:
```
Host jupyterhub
    HostName dummy
    ProxyCommand websocat --binary -H='Authorization: token 123456789abcdef123456789abcdef12' - wss://jupyterhub.domain.com/user/user@email.com/proxy/2022
```


### Usage
Run on your client:
- Start server: `uv run python3 -m src.jupyterhub_manager`
- Connect via ssh: `ssh user@jupyterhub`

### Manual server setup (for debugging):

- Server:
    - start ssh: `sudo service ssh start`
    - start ws tunnel: `~/websocat --binary -E ws-l:0.0.0.0:2022 tcp:localhost:22`
- Client:
```
ssh -o ProxyCommand="websocat \
    --binary \
    -H='Authorization: token 123456789abcdef123456789abcdef12' \
    - wss://jupyterhub.domain.com/user/user@email.com/proxy/2022" \
    user@dummy
```
