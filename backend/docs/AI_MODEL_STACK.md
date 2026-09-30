# BidGuard AI — Hugging Face AI Model Stack Specification

This document defines the production Hugging Face model stack, architecture, hardware considerations, and agent responsibilities for BidGuard AI's document understanding, RAG retrieval, and AI assistant layers.

---

## 1. Selected Model Stack Summary

| Layer | Model | Hugging Face ID | Version/Revision | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Document AI** | LayoutLMv3 Base | `microsoft/layoutlmv3-base` | `main` | Document layout understanding, clause/heading segmentation, table extraction |
| **OCR** | TrOCR Small (Printed) | `microsoft/trocr-small-printed` | `main` | Optical character recognition on scanned PDFs, stamp seals, and images |
| **Embedding** | BGE Small English v1.5 | `BAAI/bge-small-en-v1.5` | `main` | Dense vector embedding generation for tender clauses and bidder evidence |
| **Reranker** | MS MARCO MiniLM L-6 v2 | `cross-encoder/ms-marco-MiniLM-L-6-v2` | `main` | Cross-encoder contextual reranking of retrieved evidence chunks |
| **LLM** | Qwen2.5-1.5B-Instruct | `Qwen/Qwen2.5-1.5B-Instruct` | `main` | Core reasoning, RAG synthesis, document analysis, and AI assistant |

---

## 2. Detailed Model Evaluation & Selection Rationale

### A. Document Understanding Model: `microsoft/layoutlmv3-base`

* **Hugging Face Model ID**: `microsoft/layoutlmv3-base`
* **Version / Revision**: `main`
* **Model Size**: ~501 MB (125 Million parameters)
* **Context Length**: 512 tokens per window (multi-modal: text + 2D bounding boxes + image patches)
* **Input Types**: Text tokens, 2D coordinates `[x0, y0, x1, y1]`, document page images (PNG/JPEG)
* **Output Types**: Token-level classification logits, layout region boundaries (Headers, Questions, Answers, Tables, Clauses)
* **License**: MIT
* **Inference Requirements**: CPU-compatible (peak memory ~600 MB RAM) or Hugging Face Serverless / Inference API.
* **Why Selected**:
  1. Integrates text content, visual cues, and spatial layouts (bounding boxes), which is critical for complex public procurement documents (GeM bid documents, GCC/SCC clauses, bid schedules).
  2. Extremely lightweight (125M params) compared to massive vision-language models, making it feasible on CPU without GPU hardware bottlenecks.
  3. Pretrained with masked vision-language modeling across extensive multilingual business and administrative documents.
* **Why Alternatives Were Rejected**:
  * *`naver-clova-ix/donut-base`*: End-to-end OCR-free transformer is prone to hallucination when transcribing complex numeric criteria (e.g. `INR 357 Lakhs`, `68 bar(g)`).
  * *`Qwen/Qwen2-VL-7B-Instruct`*: Superior multimodal capability, but requires 16+ GB VRAM or heavy cloud GPU clusters, which exceeds local development hardware.
* **Limitations**: Maximum sequence length of 512 tokens per window requires sliding-window chunking for multi-page documents.

---

### B. OCR Model: `microsoft/trocr-small-printed`

* **Hugging Face Model ID**: `microsoft/trocr-small-printed`
* **Version / Revision**: `main`
* **Model Size**: ~246 MB (62 Million parameters)
* **Input Types**: Cropped line/region image or rendered PDF page snippet
* **Output Types**: Decoded UTF-8 text strings
* **License**: MIT
* **Inference Requirements**: Very low memory footprint (~300 MB RAM), runs fast on CPU.
* **Why Selected**:
  * High-accuracy transformer-based encoder-decoder model specialized for printed text in administrative certificates, Udyam certificates, and scanned bid annexures.
  * Native Hugging Face transformers integration without external system binary requirements (such as Tesseract C++ binaries).
* **Why Alternatives Were Rejected**:
  * *`tesseract`*: Requires external OS package installation (`tesseract-ocr`) and native DLLs, leading to brittle cross-platform deployment.
  * *`microsoft/trocr-large-printed`*: 334M params (~1.3 GB) provides marginal accuracy gains on clear scans at 4x the latency and memory overhead.
* **Limitations**: Optimized for single-line or block-level text; whole-page documents benefit from preliminary layout segmentation via LayoutLM before OCR transcription.

---

### C. Embedding Model: `BAAI/bge-small-en-v1.5`

* **Hugging Face Model ID**: `BAAI/bge-small-en-v1.5`
* **Version / Revision**: `main`
* **Model Size**: ~133 MB (33.4 Million parameters)
* **Embedding Dimension**: 384
* **Context Length**: 512 tokens
* **License**: MIT
* **Inference Requirements**: Ultra-low memory (<200 MB RAM), ~5ms per embedding inference on CPU.
* **Why Selected**:
  * Top-ranking model on the Massive Text Embedding Benchmark (MTEB) in the compact model category.
  * 384-dimensional vectors keep database vector storage and memory usage minimal while outperforming older 768-dim models (e.g. `all-mpnet-base-v2`).
  * Supports asymmetric query instruction formatting (`"Represent this sentence for searching relevant passages:"`) which dramatically increases retrieval recall for legal and procurement queries.
* **Why Alternatives Were Rejected**:
  * *`intfloat/e5-large-v2`*: 1.34 GB model size and 1024-dim vectors are unnecessarily heavy for local CPU deployment.
  * *`sentence-transformers/all-MiniLM-L6-v2`*: BGE-small-v1.5 systematically outperforms MiniLM-L6-v2 across retrieval benchmarks (MTEB Retrieval score 51.68 vs 41.95).
* **Limitations**: English-focused; multilingual tenders requiring Indic language scripts (Hindi, Tamil, etc.) would require switching to `BAAI/bge-m3` in future phases.

---

### D. Reranker: `cross-encoder/ms-marco-MiniLM-L-6-v2`

* **Hugging Face Model ID**: `cross-encoder/ms-marco-MiniLM-L-6-v2`
* **Version / Revision**: `main`
* **Model Size**: ~87 MB (22.7 Million parameters)
* **Input Types**: Pairs of `(query, document_passage)`
* **Output Types**: Calibrated relevance logit / score
* **License**: Apache 2.0
* **Inference Requirements**: Extremely fast CPU inference (<15ms for a batch of 10 passages).
* **Why Selected**:
  * Bi-encoder embeddings match queries based on semantic proximity, which can miss exact numeric conditions (e.g., distinguishing between `Turnover >= 10 Cr` and `Turnover >= 50 Cr`).
  * Cross-encoders jointly attend across both query and passage simultaneously via cross-attention, providing high-precision ranking of candidate evidence before passing to the LLM.
* **Why Alternatives Were Rejected**:
  * *`BAAI/bge-reranker-large`*: 2.2 GB model size is too heavy for rapid per-query inference on local CPU.
* **Limitations**: Compute cost scales as `O(N)` with the number of candidate documents; therefore, the reranker is applied strictly to the top 10–20 candidates retrieved by the embedding vector search.

---

### E. LLM / Chat Model: `Qwen/Qwen2.5-1.5B-Instruct`

* **Hugging Face Model ID**: `Qwen/Qwen2.5-1.5B-Instruct`
* **Version / Revision**: `main`
* **Model Size**: 1.54 Billion parameters (~3.1 GB FP16, ~1.0 GB in 4-bit / GGUF)
* **Context Window**: 32,768 tokens native (expandable to 128k)
* **License**: Apache 2.0
* **Minimum Hardware Requirement**: 4 GB RAM on CPU or 2 GB VRAM on GPU; or Hugging Face Serverless Inference API.
* **Why Selected**:
  * State-of-the-art instruction-following and structured JSON extraction among sub-2B parameter models.
  * Large 32k context window easily accommodates multiple full tender clauses, bidder evidence excerpts, and statutory rules in a single prompt.
  * Permissive Apache 2.0 license permits commercial procurement deployment.
  * Perfectly sized for local CPU inference on systems with 16 GB RAM and 2–4 GB available memory.
* **Why Alternatives Were Rejected**:
  * *`meta-llama/Llama-3.2-1B-Instruct`*: Good lightweight model, but Qwen2.5-1.5B-Instruct scores higher on reasoning, structured extraction, and complex tabular comprehension benchmarks.
  * *`mistralai/Mistral-7B-Instruct-v0.3`*: 14 GB unquantized footprint causes memory swapping and sluggish CPU response times in environments with limited free RAM.
* **Limitations**: Complex multi-hop legal analysis on hundred-page contracts should be partitioned by the RAG agent into focused evidence chunks rather than fed raw.

---

## 3. Architecture & Data Flow

```text
                  +--------------------------------+
                  |          USER QUESTION         |
                  +--------------------------------+
                                  |
                                  v
                  +--------------------------------+
                  |          AGENT ROUTER          |
                  +--------------------------------+
                                  |
        +-------------------------+-------------------------+
        |                         |                         |
        v                         v                         v
+----------------+       +------------------+       +----------------+
| DOCUMENT AGENT |       |    RAG AGENT     |       | ANALYSIS AGENT |
| (LayoutLMv3)   |       | (BGE Embedding   |       | (Shared LLM)   |
| - Layout/OCR   |       |  + Cross-Encoder |       | - Comparison   |
| - Clauses/Tabs |       |  Reranker)       |       | - Discrepancy  |
| - Summary      |       | - Dense Vector   |       | - Officer Risk |
+----------------+       | - Evidence Rank  |       +----------------+
        |                +------------------+               |
        |                         |                         |
        +-------------------------+-------------------------+
                                  |
                                  v
                  +--------------------------------+
                  |         SHARED LLM             |
                  |     (Qwen2.5-1.5B-Instruct)    |
                  +--------------------------------+
                                  |
                                  v
                  +--------------------------------+
                  |        SYNTHESIZED ANSWER      |
                  |    with Citations & Guardrail  |
                  +--------------------------------+
```

---

## 4. Hardware Awareness & Fallback Strategy

1. **Local CPU Execution**: Models are sized to run comfortably within 2–4 GB RAM on standard CPU hardware without GPU acceleration.
2. **Hugging Face Hub API Integration**: When `HUGGINGFACE_API_KEY` is provided in `.env`, the provider layer can route inference to Hugging Face Serverless Inference Endpoints with zero local memory consumption.
3. **Resilient Offline Fallback**: In offline, CI/CD, or constrained environments where weights cannot be downloaded from Hugging Face Hub, the provider layer provides deterministic, rule-informed local fallbacks ensuring 100% test reliability and zero downtime.
