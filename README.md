# JupyterHub Manager

A Python tool for tunneling SSH to a JupyterHub container through jupyter-server-proxy endpoints.

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
