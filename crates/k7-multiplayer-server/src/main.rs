//! K7 multiplayer WebSocket server: room-based matchmaking + LLM proxy.
//! First message: "create" (get new room code) or "join:CODE" (join room).
//! Then every message is broadcast to all peers in the same room (including the sender).
//! Special: "LLM_REQ:{json}" is not broadcast; server POSTs to LLM at 127.0.0.1:1234 and
//! sends "LLM_RESP:content" or "LLM_ERR:message" back to that client only.
//!
//! Run: cargo run -p k7-multiplayer-server
//! LLM: run an OpenAI-compatible API on http://127.0.0.1:1234 (e.g. Ollama + proxy, LiteLLM).

use futures_util::{SinkExt, StreamExt};
use std::collections::{HashMap, HashSet};
use std::net::SocketAddr;
use std::sync::atomic::{AtomicU32, Ordering};
use std::sync::Arc;
use tokio::net::TcpListener;
use tokio::sync::{mpsc, Mutex};
use tokio_tungstenite::accept_async;
use tokio_tungstenite::tungstenite::Message;

const LLM_URL: &str = "http://127.0.0.1:1234/v1/chat/completions";

#[derive(serde::Deserialize)]
struct LlmRequest {
    prompt: String,
    #[serde(default)]
    system_prompt: String,
    #[serde(default = "default_model")]
    model: String,
}

fn default_model() -> String {
    "gpt-4o-mini".to_string()
}

static NEXT_PEER_ID: AtomicU32 = AtomicU32::new(0);

const ROOM_CODE_LEN: usize = 6;
const ROOM_CODE_CHARS: &[u8] = b"ABCDEFGHJKLMNPQRSTUVWXYZ23456789";

fn random_room_code() -> String {
    use std::time::{SystemTime, UNIX_EPOCH};
    let t = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos();
    let mut s = String::with_capacity(ROOM_CODE_LEN);
    let n = ROOM_CODE_CHARS.len();
    for i in 0..ROOM_CODE_LEN {
        let idx = ((t >> (i * 5)) as usize) % n;
        s.push(ROOM_CODE_CHARS[idx] as char);
    }
    s
}

type PeerId = u32;
type RoomCode = String;
type Sender = mpsc::UnboundedSender<String>;

/// Single shared state so we take one lock per operation instead of three.
struct SharedState {
    peers: HashMap<PeerId, Sender>,
    room_to_peers: HashMap<RoomCode, HashSet<PeerId>>,
    peer_to_room: HashMap<PeerId, RoomCode>,
}

type State = Arc<Mutex<SharedState>>;

async fn handle_llm_request(payload: &str) -> Result<String, String> {
    let req: LlmRequest = serde_json::from_str(payload).map_err(|e| e.to_string())?;
    let mut messages = Vec::new();
    if !req.system_prompt.is_empty() {
        messages.push(serde_json::json!({ "role": "system", "content": req.system_prompt }));
    }
    let user_content = if req.prompt.trim().is_empty() {
        "Hi"
    } else {
        req.prompt.trim()
    };
    messages.push(serde_json::json!({ "role": "user", "content": user_content }));
    let body = serde_json::json!({
        "model": req.model,
        "messages": messages
    });
    let client = reqwest::Client::new();
    let res = client
        .post(LLM_URL)
        .json(&body)
        .send()
        .await
        .map_err(|e| e.to_string())?;
    let status = res.status();
    let data: serde_json::Value = res.json().await.map_err(|e| e.to_string())?;
    if !status.is_success() {
        let msg = data
            .get("error")
            .and_then(|e| e.get("message"))
            .and_then(|m| m.as_str())
            .unwrap_or("HTTP error");
        return Err(msg.to_string());
    }
    let content = data
        .get("choices")
        .and_then(|c| c.get(0))
        .and_then(|c| c.get("message"))
        .and_then(|m| m.get("content"))
        .and_then(|c| c.as_str())
        .ok_or_else(|| "missing choices[0].message.content".to_string())?;
    Ok(content.to_string())
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let port = std::env::var("PORT").unwrap_or_else(|_| "8081".into());
    let addr: SocketAddr = format!("0.0.0.0:{}", port).parse()?;
    let listener = TcpListener::bind(addr).await?;
    println!("K7 multiplayer server on ws://localhost:{}", addr.port());

    let state: State = Arc::new(Mutex::new(SharedState {
        peers: HashMap::new(),
        room_to_peers: HashMap::new(),
        peer_to_room: HashMap::new(),
    }));

    while let Ok((stream, peer_addr)) = listener.accept().await {
        let state = state.clone();
        tokio::spawn(async move {
            if let Err(e) = handle_client(stream, peer_addr, state).await {
                eprintln!("client error: {}", e);
            }
        });
    }
    Ok(())
}

async fn handle_client(
    stream: tokio::net::TcpStream,
    peer_addr: SocketAddr,
    state: State,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let ws = accept_async(stream).await?;
    let peer_id = NEXT_PEER_ID.fetch_add(1, Ordering::Relaxed);
    println!("Client connected: {} (id={})", peer_addr, peer_id);

    let (mut ws_tx, mut ws_rx) = ws.split();
    let (tx, mut rx) = mpsc::unbounded_channel::<String>();
    {
        let mut st = state.lock().await;
        st.peers.insert(peer_id, tx);
    }

    let outgoing = tokio::spawn(async move {
        while let Some(s) = rx.recv().await {
            if ws_tx.send(Message::Text(s)).await.is_err() {
                break;
            }
        }
    });

    let mut my_room: Option<String> = None;
    let mut logged_waiting_for_join = false;

    while let Some(msg) = ws_rx.next().await {
        let text = match msg {
            Ok(Message::Text(t)) => t,
            Ok(Message::Close(_)) => {
                println!("[{}] received Close", peer_id);
                break;
            }
            Ok(_) => continue,
            Err(e) => {
                println!("[{}] ws error: {}", peer_id, e);
                break;
            }
        };

        if text.starts_with("LLM_REQ:") {
            let payload = text["LLM_REQ:".len()..].to_string();
            let preview = if payload.len() > 60 {
                format!("{}...", &payload[..60])
            } else {
                payload.clone()
            };
            let pid = peer_id;
            println!("[{}] LLM request (len={}): {}", pid, payload.len(), preview);
            let tx = {
                let st = state.lock().await;
                st.peers.get(&pid).cloned()
            };
            if let Some(tx) = tx {
                tokio::spawn(async move {
                    match handle_llm_request(&payload).await {
                        Ok(content) => {
                            let out_preview = if content.len() > 60 {
                                format!("{}...", &content[..60])
                            } else {
                                content.clone()
                            };
                            println!("[{}] LLM response (len={}): {}", pid, content.len(), out_preview);
                            let _ = tx.send(format!("LLM_RESP:{}", content));
                        }
                        Err(e) => {
                            eprintln!("[{}] LLM error: {}", pid, e);
                            let _ = tx.send(format!("LLM_ERR:{}", e));
                        }
                    }
                });
            }
            continue;
        }

        if my_room.is_none() {
            let trimmed = text.trim();
            if trimmed == "create" {
                let code = random_room_code();
                let to_self = {
                    let mut st = state.lock().await;
                    st.room_to_peers.entry(code.clone()).or_default().insert(peer_id);
                    st.peer_to_room.insert(peer_id, code.clone());
                    st.peers.get(&peer_id).cloned()
                };
                my_room = Some(code.clone());
                if let Some(s) = to_self {
                    let _ = s.send(format!("created:{}", code));
                }
                println!("[{}] room created: {} (size=1)", peer_id, code);
            } else if let Some(code) = trimmed.strip_prefix("join:") {
                let code = code.trim().to_uppercase();
                if code.len() >= 4 {
                    let (to_self, to_others) = {
                        let mut st = state.lock().await;
                        let (other_ids, size_after) = {
                            let entry = st.room_to_peers.entry(code.clone()).or_default();
                            entry.insert(peer_id);
                            (entry.iter().filter(|&&id| id != peer_id).copied().collect::<Vec<PeerId>>(), entry.len())
                        };
                        st.peer_to_room.insert(peer_id, code.clone());
                        let to_self = st.peers.get(&peer_id).cloned();
                        let to_others: Vec<Sender> = other_ids.iter().filter_map(|id| st.peers.get(id).cloned()).collect();
                        (to_self, (to_others, size_after))
                    };
                    my_room = Some(code.clone());
                    if let Some(s) = to_self {
                        let _ = s.send("joined".to_string());
                    }
                    for s in to_others.0 {
                        let _ = s.send("peer_joined".to_string());
                    }
                    println!("[{}] joined room {} (peers now: {})", peer_id, code, to_others.1);
                } else {
                    println!("[{}] join rejected: code too short (len={})", peer_id, code.len());
                    if let Some(s) = state.lock().await.peers.get(&peer_id) {
                        let _ = s.send("error:invalid_code".to_string());
                    }
                }
            } else {
                if !logged_waiting_for_join {
                    logged_waiting_for_join = true;
                    let preview = if trimmed.len() > 60 { format!("{}...", &trimmed[..60]) } else { trimmed.to_string() };
                    println!("[{}] waiting for create/join, ignoring: {:?} (len={})", peer_id, preview, trimmed.len());
                    if let Some(s) = state.lock().await.peers.get(&peer_id) {
                        let _ = s.send("error:send_create_or_join".to_string());
                    }
                }
            }
            continue;
        }

        let room = my_room.as_ref().unwrap();
        let senders: Vec<Sender> = {
            let st = state.lock().await;
            st.room_to_peers
                .get(room)
                .map(|ids| ids.iter().filter_map(|id| st.peers.get(id).cloned()).collect())
                .unwrap_or_default()
        };
        let n = senders.len();
        for s in &senders {
            let _ = s.send(text.clone());
        }
        if n > 0 && (n > 1 || !text.starts_with("d,")) {
            let preview = if text.len() > 50 { format!("{}...", &text[..50]) } else { text.clone() };
            println!("[{}] broadcast room={} to {} peer(s): {}", peer_id, room, n, preview);
        }
    }

    if let Some(room) = my_room.take() {
        let mut st = state.lock().await;
        if let Some(peers_in_room) = st.room_to_peers.get_mut(&room) {
            peers_in_room.remove(&peer_id);
            let left = peers_in_room.len();
            if peers_in_room.is_empty() {
                st.room_to_peers.remove(&room);
                println!("[{}] disconnected from room {} (room closed, was last)", peer_id, room);
            } else {
                println!("[{}] disconnected from room {} ({} peer(s) left)", peer_id, room, left);
            }
        }
        st.peer_to_room.remove(&peer_id);
    } else {
        println!("[{}] disconnected (never joined a room)", peer_id);
    }
    outgoing.abort();
    state.lock().await.peers.remove(&peer_id);
    println!("[{}] client gone: {}", peer_id, peer_addr);
    Ok(())
}
