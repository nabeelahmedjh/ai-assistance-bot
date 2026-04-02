#!/usr/bin/env node

import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..");

const API_BASE = (process.env.API_BASE_URL || "http://127.0.0.1:8000/api").replace(/\/$/, "");
const WS_BASE = (process.env.WS_BASE_URL || "ws://127.0.0.1:8001").replace(/\/$/, "");
const LEAD_ID = process.env.E2E_LEAD_ID || `e2e-lead-${Date.now()}`;
const CHAT_MESSAGE = process.env.E2E_CHAT_MESSAGE || "How much is a 40ft container and do you deliver to Texas?";
const SAMPLE_DIR = path.join(repoRoot, "Backend", "sample_documents");

function logStep(message) {
  console.log(`\n[STEP] ${message}`);
}

function logOk(message) {
  console.log(`[OK] ${message}`);
}

function fail(message, details) {
  console.error(`\n[FAIL] ${message}`);
  if (details) {
    console.error(details);
  }
  process.exit(1);
}

async function parseJsonSafe(response) {
  const text = await response.text();
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

async function uploadDocuments() {
  const files = (await fs.readdir(SAMPLE_DIR))
    .filter((name) => name.endsWith(".md"))
    .sort();

  if (files.length === 0) {
    fail("No sample markdown files found", `Checked: ${SAMPLE_DIR}`);
  }

  const payload = [];
  for (const fileName of files) {
    const filePath = path.join(SAMPLE_DIR, fileName);
    const content = await fs.readFile(filePath, "utf-8");
    payload.push({
      title: fileName.replace(/\.md$/, ""),
      content,
      source_type: "seed",
      file_url: "",
    });
  }

  const response = await fetch(`${API_BASE}/documents/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await parseJsonSafe(response);
  if (!response.ok || !Array.isArray(data) || data.length === 0) {
    fail("Document upload failed", JSON.stringify(data, null, 2));
  }

  const ids = data.map((row) => row.id).filter(Boolean);
  if (ids.length === 0) {
    fail("Upload succeeded but no document IDs were returned", JSON.stringify(data, null, 2));
  }

  logOk(`Uploaded ${ids.length} document(s)`);
  return ids;
}

async function ingestDocuments(documentIds) {
  for (const id of documentIds) {
    const response = await fetch(`${API_BASE}/documents/${id}/ingest/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });

    const data = await parseJsonSafe(response);
    if (!response.ok) {
      fail(`Ingestion failed for document ${id}`, JSON.stringify(data, null, 2));
    }

    if (!data.processed) {
      fail(`Ingestion endpoint returned unprocessed status for document ${id}`, JSON.stringify(data, null, 2));
    }
  }

  logOk(`Ingested ${documentIds.length} document(s)`);
}

async function runRestChat() {
  const response = await fetch(`${API_BASE}/ai/chat/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      lead_id: LEAD_ID,
      message: CHAT_MESSAGE,
    }),
  });

  const data = await parseJsonSafe(response);
  if (!response.ok) {
    fail("REST chat request failed", JSON.stringify(data, null, 2));
  }

  const answer = data?.response?.answer;
  if (!answer || typeof answer !== "string") {
    fail("REST chat response missing structured answer", JSON.stringify(data, null, 2));
  }

  logOk("REST chat returned structured response");
}

async function verifyHistory() {
  const response = await fetch(`${API_BASE}/ai/chat/history/${encodeURIComponent(LEAD_ID)}/`);
  const data = await parseJsonSafe(response);

  if (!response.ok || !Array.isArray(data)) {
    fail("Chat history fetch failed", JSON.stringify(data, null, 2));
  }

  if (data.length < 2) {
    fail("Chat history does not contain expected turns", JSON.stringify(data, null, 2));
  }

  logOk(`History contains ${data.length} turn(s)`);
}

async function runWebSocketChat() {
  const wsUrl = `${WS_BASE}/ws/chat/${encodeURIComponent(LEAD_ID)}/`;

  const outcome = await new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl);
    const timeout = setTimeout(() => {
      ws.close();
      reject(new Error("Timed out waiting for websocket assistant reply"));
    }, 10000);

    ws.addEventListener("open", () => {
      ws.send(JSON.stringify({ type: "typing", is_typing: true }));
      ws.send(JSON.stringify({ type: "message", message: "Can I place an order today?" }));
    });

    ws.addEventListener("message", (event) => {
      let data;
      try {
        data = JSON.parse(event.data);
      } catch {
        return;
      }

      if (data.type === "error") {
        clearTimeout(timeout);
        ws.close();
        reject(new Error(`WebSocket error event: ${data.error || "unknown"}`));
        return;
      }

      if (data.type === "message" && data.response?.answer) {
        clearTimeout(timeout);
        ws.close();
        resolve(data.response.answer);
      }
    });

    ws.addEventListener("error", () => {
      clearTimeout(timeout);
      reject(new Error("WebSocket connection error"));
    });
  });

  if (!outcome || typeof outcome !== "string") {
    fail("WebSocket response did not include assistant answer");
  }

  logOk("WebSocket chat returned assistant response");
}

async function main() {
  console.log("=== E2E Sanity Test ===");
  console.log(`API_BASE_URL: ${API_BASE}`);
  console.log(`WS_BASE_URL: ${WS_BASE}`);
  console.log(`LEAD_ID: ${LEAD_ID}`);

  logStep("Uploading sample documents");
  const docIds = await uploadDocuments();

  logStep("Ingesting uploaded documents");
  await ingestDocuments(docIds);

  logStep("Testing REST chat endpoint");
  await runRestChat();

  logStep("Verifying chat history endpoint");
  await verifyHistory();

  logStep("Testing WebSocket chat endpoint");
  await runWebSocketChat();

  console.log("\n[SUCCESS] End-to-end sanity test passed.");
}

main().catch((error) => {
  fail("Unhandled error in E2E sanity test", error instanceof Error ? error.stack : String(error));
});
