# training_log.md
# Training run summaries and architecture experiment results.

## Architecture Experiments

### Structure-Aware vs Raster Ordering (Phase 4)
- Date:
- Raster order validation pass rate:
- Structure-aware order validation pass rate:
- Decision:

### Sequence Length Risk Evaluation (Phase 4)
- Date:
- Pass rate for sequences < 1,500 tokens:
- Pass rate for sequences > 1,500 tokens:
- Decision (proceed / implement hierarchical generation):

### DNA Conditioning Consistency (Phase 4)
- Date:
- Top-half average DNA consistency score:
- Bottom-half average DNA consistency score:
- Delta:
- Decision (proceed / flag for cross-attention upgrade in Phase 6):

## Training Runs

| Date | Phase | Steps | Train Loss | Val Loss | Notes |
|------|-------|-------|------------|----------|-------|

## Training run 2026-07-01T21:39:07 — VALIDATION RUN (tier 0)
- corpus: data/validation_corpus/indexed (271 train / 29 val)
- model: small (889,860 params), device cpu
- steps 700, batch 8, lr 0.0003
- step 50: train_loss 2.6650 | val_loss 2.4965 | val_token_acc 55.1% | 93s
