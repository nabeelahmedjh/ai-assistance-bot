# Memox.io – AI Engineering Technical Test

**Level:** Intermediate (2–4 years)  
**Time:** 3–4 hours

---

## How We Evaluate

- **Show your work:** Commit history matters. 15+ commits + a `DECISIONS.md` tells us everything. One squashed commit tells us nothing.
- **Go beyond the requirements:** The spec is a floor, not a ceiling. Add a feature that wasn't asked for, improve UX, or polish a detail others skip. We're hiring for product instinct, not just technical competence.
- **Creativity > completeness:** A half-finished submission with one genuinely clever idea beats a fully working but generic one.

---

## Background

Memox builds white-label AI sales assistants for B2B companies. Clients embed a chat widget on their website to answer prospect questions, qualify leads, and drive conversions — grounded in the company's own docs.

**Client for this test:** A shipping container company fielding hundreds of repetitive daily questions (sizes, pricing, delivery, customization, bulk discounts).

**Stack:** Django + DRF (backend), Next.js + TypeScript (frontend), WebSockets (real-time), any vector store / embedding approach.

---

## The Scenario

Build a proof-of-concept AI sales assistant for a container company. The bot should answer questions like:
- *"How much is a 40ft container?"*
- *"Do you deliver to Texas?"*
- *"What's the difference between new and one-trip?"*

Answers must be grounded in the company's actual product documentation.

**Create 5–10 sample documents yourself** (product specs, pricing pages, FAQ, delivery policies, customization options — make them realistic). The system should ingest them, chunk them, and let prospects ask questions with answers that drive toward a sale.

---

## Requirements

### 1. Document Ingestion Pipeline — 25 pts

Build a pipeline that takes raw documents and makes them searchable.

**Django Models:**
- `Document` — `title`, `content`, `source_type`, `file_url`, `uploaded_at`, `processed`
- `Chunk` — `document` (FK), `content`, `embedding`, `chunk_index`, `metadata`

**Ingestion Service:**
- `ingest_document(document_id)` — chunks content, generates embeddings (sentence-transformers or any approach), stores results
- Use ~500 char chunks with overlap
- Justify your chunking strategy in a comment or doc

---

### 2. Retrieval + LLM Response — 25 pts

**Context Retrieval:**
- `retrieve_context(query, top_k=3)` — embed the query, find most similar chunks, return them with source attribution

**Prompt Construction:**
- `build_prompt(query, context)` — assemble a system message + retrieved context + user query
- Prompt should instruct the LLM to: cite sources, answer like a knowledgeable sales rep, and guide prospects toward conversion

**Chat Endpoint:**
- `POST /api/ai/chat/` — accepts `{ lead_id, message }`, retrieves context, builds prompt, calls LLM (mock or real), saves the conversation turn
- Return a **structured response** — not just a string

---

### 3. API + Real-time — 20 pts

**REST Endpoints:**
- `GET /api/documents/`
- `POST /api/documents/`
- `POST /api/documents/<id>/ingest/`
- `GET /api/documents/<id>/chunks/`
- `POST /api/ai/chat/`
- `GET /api/ai/chat/history/<lead_id>/`

**WebSocket:**
- `/ws/chat/<lead_id>/` — bidirectional chat with typing indicators

---

### 4. Frontend — 20 pts

**Chat Widget (TypeScript):**
- Props: `leadId`, `apiUrl`, `wsUrl`
- Scrollable message history, input field, WebSocket connection, typing indicator
- Should feel like a product, not a homework assignment

**Admin Page (Next.js):**
- List documents with processing status
- Button to trigger ingestion

---

### 5. Bonus: Agent Behavior — 10 pts

- `classify_intent(message)` — categorize as `pricing | availability | general | conversion`
- `handle_message(message, lead_id)` — route based on intent:
  - `pricing` intents → include product comparisons
  - `conversion` intents (e.g., "I want to buy", "Can I place an order?") → trigger a sales handoff signal

---

## Tests We Expect

```python
# test_ingestion.py

def test_chunk_creation():
    doc = Document.objects.create(
        title="Pricing", content="40ft standard container: $3,850. 20ft: $2,100..."
    )
    chunks = chunk_document(doc, chunk_size=500)
    assert len(chunks) > 0
    assert all(c.document_id == doc.id for c in chunks)

def test_embedding_similarity():
    emb1 = generate_embedding("shipping container prices")
    emb2 = generate_embedding("container pricing information")
    assert cosine_similarity(emb1, emb2) > 0.5


# test_agent.py

def test_intent_classification():
    assert classify_intent("How much is a 40ft container?") == "pricing"
    assert classify_intent("Do you deliver to Texas?") == "availability"
    assert classify_intent("I want to place an order") == "conversion"
```

---

## What to Submit

1. **GitHub repo** — Django backend + Next.js frontend + widget, with real commit history (not one squashed commit)
2. **README** — setup instructions (Docker preferred but not required)
3. **DECISIONS.md** — a short log of key decisions: what you chose, what you rejected, what AI helped with and where you overrode it. 5–10 bullet points is plenty.

---

## "Going Beyond" — Ideas That Have Impressed Before

- A response format that returns **structured components** (data cards, source citations) instead of plain text
- **Streaming responses** over WebSocket so the user sees tokens arrive in real time
- A **smarter chunking strategy** (e.g., respecting paragraph boundaries, handling tables differently)
- An **eval script** that tests answer quality, not just that the endpoint returns 200
- Thoughtful **error states in the UI** (what happens when the LLM is slow? when there's no relevant context?)
- Anything that makes us say *"we didn't ask for that, but it's obviously better"*

> Note: We won't hint at what "going beyond" should be — that's yours to decide.