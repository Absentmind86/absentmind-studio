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
- step 100: train_loss 1.2189 | val_loss 0.7593 | val_token_acc 82.2% | 191s
- step 150: train_loss 1.0956 | val_loss 0.5289 | val_token_acc 84.7% | 284s
- step 200: train_loss 0.9245 | val_loss 0.4764 | val_token_acc 85.7% | 382s
- step 250: train_loss 0.8640 | val_loss 0.4432 | val_token_acc 86.7% | 475s
- step 300: train_loss 0.8548 | val_loss 0.4239 | val_token_acc 87.5% | 564s
- step 350: train_loss 0.8641 | val_loss 0.4111 | val_token_acc 87.6% | 661s
- step 400: train_loss 0.8631 | val_loss 0.4068 | val_token_acc 87.7% | 758s
- step 450: train_loss 0.8333 | val_loss 0.4038 | val_token_acc 87.6% | 855s
- step 500: train_loss 0.8338 | val_loss 0.3975 | val_token_acc 87.8% | 949s
- step 550: train_loss 0.7913 | val_loss 0.3941 | val_token_acc 87.9% | 1048s
- step 600: train_loss 0.7970 | val_loss 0.3914 | val_token_acc 87.9% | 1146s
- step 650: train_loss 0.7992 | val_loss 0.3908 | val_token_acc 87.9% | 1238s
- step 700: train_loss 0.8076 | val_loss 0.3888 | val_token_acc 88.0% | 1335s
- finished: best val_loss 0.3888; checkpoint /home/user/absentmind-studio/am-pixel/model/checkpoints/validation/latest.pt
- sample batch (held-out palettes): 5/8 automated-gate passes, mean 77.5/85 — logs/validation_run_samples/
