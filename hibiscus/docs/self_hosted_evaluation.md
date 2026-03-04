<!-- Hibiscus v0.9 — EAZR AI Insurance Intelligence Engine -->
<!-- Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved. -->

# Self-Hosted DeepSeek Evaluation

## Current State (Phase 4)

Hibiscus uses DeepSeek V3 via API as the primary LLM (80% of calls), with DeepSeek R1 for reasoning (15%) and Claude Sonnet as safety net (5%). All calls go through LiteLLM with automatic fallback.

**Current cost**: ₹0.045/conversation average (67× under ₹3 target).

## Self-Hosted Option: When to Consider

Self-hosting makes economic sense when API costs exceed infrastructure costs. The break-even depends on conversation volume.

### Hardware Requirements

| Component | DeepSeek V3 (671B MoE) | DeepSeek R1 (671B MoE) |
|-----------|------------------------|------------------------|
| GPU Memory | 8× A100 80GB or 4× H100 80GB | Same |
| RAM | 256 GB | 256 GB |
| Storage | 1 TB NVMe SSD | 1 TB NVMe SSD |
| Serving Framework | vLLM or TGI | vLLM or TGI |
| Throughput | ~50 tokens/sec (8×A100) | ~30 tokens/sec (8×A100, with CoT) |

### Cost Comparison

| Item | API (DeepSeek) | Self-Hosted (8×A100 cloud) |
|------|----------------|---------------------------|
| Monthly fixed cost | ₹0 | ~₹8,00,000/month (AWS p4d.24xlarge) |
| Per-conversation cost | ₹0.045 | ~₹0 (marginal) |
| Break-even volume | — | ~17,78,000 conversations/month (~59,000/day) |
| At 1,000 conv/day | ₹1,350/month | ₹8,00,000/month |
| At 10,000 conv/day | ₹13,500/month | ₹8,00,000/month |
| At 50,000 conv/day | ₹67,500/month | ₹8,00,000/month |
| At 100,000 conv/day | ₹1,35,000/month | ₹8,00,000/month |

### Break-Even Analysis

```
Break-even = Fixed Monthly Cost / Cost Per Conversation
           = ₹8,00,000 / ₹0.045
           ≈ 1,77,78,000 conversations/month
           ≈ 59,260 conversations/day
```

At current pricing, self-hosting only makes sense at **~60,000 conversations/day** — well beyond Phase 4 targets.

### Alternative: Smaller Models

For specific tasks (extraction, intent classification), smaller fine-tuned models are viable:

| Model | Hardware | Monthly Cost | Use Case |
|-------|----------|-------------|----------|
| Llama 3.1 8B (fine-tuned) | 1× A10G | ~₹30,000/month | Policy extraction |
| Mistral 7B | 1× A10G | ~₹30,000/month | Intent classification |
| DeepSeek V3 0324 (distilled 7B) | 1× A10G | ~₹30,000/month | General chat L1/L2 |

A hybrid approach — small model for L1/L2, API for L3/L4 — could reduce API costs by 60-70% at scale.

## Deployment Options

### vLLM (Recommended)
- Best throughput for large models
- Supports PagedAttention, continuous batching
- Native OpenAI-compatible API server
- `vllm serve deepseek-ai/DeepSeek-V3 --tensor-parallel-size 8`

### Text Generation Inference (TGI)
- HuggingFace's serving framework
- Good for single-GPU smaller models
- Built-in health checks and metrics

### Kubernetes (Production)
- Use NVIDIA GPU Operator for device plugin
- KServe or Triton Inference Server for auto-scaling
- Horizontal pod autoscaling based on GPU utilization

## Recommendation for Phase 4

**Stay on API.** Reasons:

1. **Volume too low**: Even at Phase 3 target (1,000 conv/day), API costs are ₹1,350/month vs ₹8,00,000/month self-hosted.
2. **Cost efficiency**: ₹0.045/conversation is exceptionally low — 67× under budget.
3. **Operational complexity**: Self-hosting adds GPU ops, model updates, failover — significant engineering overhead.
4. **DeepSeek pricing**: DeepSeek's aggressive pricing makes self-hosting uneconomical at any realistic near-term volume.

### When to Revisit

- **50,000+ conversations/day sustained** — approaching break-even
- **Latency requirements tighten** — self-hosted eliminates API RTT (~10-15s → ~2-5s)
- **Data sovereignty requirements** — regulatory need to keep all data on-prem
- **Fine-tuned models needed** — extraction or domain-specific models trained on EAZR data
- **DeepSeek pricing changes** — if API costs increase significantly

### Phase 5 Roadmap (Future)

1. Fine-tune Llama 3.1 8B on EAZR extraction data (Phase 5.1)
2. Deploy as sidecar for policy extraction only (Phase 5.2)
3. Evaluate hybrid: local L1/L2 + API L3/L4 (Phase 5.3)
4. Full self-hosted if volume justifies (Phase 5.4+)
