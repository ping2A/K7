# K7 Multiplayer WebSocket Server (Node.js)

Simple broadcast server: every text message received is sent to all other connected clients. A Rust version is available: `cargo run -p k7-multiplayer-server`.

## Run

```bash
npm install
npm start
```

Listens on `ws://localhost:8081` (override with `PORT=9999 npm start`).

## Usage with K7

1. Start this server.
2. In the browser, open the K7 Python page (`editor.html`), click **Load multiplayer example**, then **Run**.
3. Open a second tab to the same page and click **Run**. Both clients will see each other’s position.

Messages are plain text (e.g. `x,y` for the demo). Implement your own protocol in your game.
