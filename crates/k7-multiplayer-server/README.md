# K7 Multiplayer Server (Rust)

WebSocket server that broadcasts every text message to all other connected clients. Same behavior as the Node.js server in `examples/multiplayer-server/`.

## Run

```bash
# From repo root
cargo run -p k7-multiplayer-server
```

Listens on `ws://localhost:8081`. Override port with:

```bash
PORT=9999 cargo run -p k7-multiplayer-server
```

## Usage with K7

1. Start this server.
2. Open the K7 Python page (`editor.html`), click **Load multiplayer example**, then **Run**.
3. Open a second browser tab and click **Run**. Both clients will see each other’s position.

Messages are plain text (e.g. `x,y` in the demo). Use any protocol you like in your game.
