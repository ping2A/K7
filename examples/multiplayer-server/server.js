#!/usr/bin/env node
// K7 multiplayer WebSocket server: broadcasts every message to all connected clients.
// Run: npm install && npm start
// Then open two browser tabs to editor.html and use the multiplayer example (connect to ws://localhost:8081).

const WebSocket = require('ws');
const PORT = Number(process.env.PORT) || 8081;

const wss = new WebSocket.Server({ port: PORT });

wss.on('connection', (ws, req) => {
  const addr = req.socket.remoteAddress;
  console.log('Client connected:', addr);
  ws.on('message', (data) => {
    const text = data.toString();
    console.log('Broadcast:', text);
    wss.clients.forEach((client) => {
      if (client !== ws && client.readyState === WebSocket.OPEN) {
        client.send(text);
      }
    });
  });
  ws.on('close', () => console.log('Client disconnected:', addr));
});

console.log('K7 multiplayer server on ws://localhost:' + PORT);
