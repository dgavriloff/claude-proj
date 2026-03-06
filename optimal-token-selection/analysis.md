# Can N/30 Optimally Selected Tokens Match N Random Tokens?

## Short Answer

**Not reliably in practice, but theoretically plausible in narrow settings.** The
best empirical results in data pruning show ~2-10x data efficiency gains, with
some results reaching up to ~20x in specific (often classification) settings. A
full 30x compression ratio that preserves loss parity remains beyond what has
been convincingly demonstrated for large-scale language model pretraining.

---

## Key Results from the Literature

### 1. Beyond Neural Scaling Laws (Sorscher et al., 2022)

This is the most optimistic paper for the N/30 claim. Sorscher et al. showed
that with optimal data pruning, you can **break power-law scaling** and achieve
**exponential scaling** instead:

- **Power-law regime (no pruning):** Loss ~ N^(-α) where α ≈ 0.4-0.5
- **Exponential regime (with pruning):** Loss ~ exp(-cN) for a curated subset

Their key theoretical result: if data has redundancy structure and you can
identify a high-quality subset via a good metric (e.g., SL2N — self-supervised
learning to prune), the effective dataset size needed drops dramatically.

**Claimed ratios:** On image classification (ImageNet), they showed ~10x
data reduction with pruning matching unpruned performance. In their most
favorable theoretical analysis, ratios of 10-30x or more are possible
**if the pruning metric is near-optimal**.

**Critical caveat:** These results were primarily on image classification, not
autoregressive language modeling. The structure of redundancy in language data
is different.

### 2. DSIR — Data Selection with Importance Resampling (Xie et al., 2023)

DSIR selects pretraining data to match a target distribution (e.g., Wikipedia)
using importance resampling with n-gram features.

- Achieved performance of training on the full Pile with only **a fraction of
  the data** selected to match a target domain.
- Typical efficiency gains: ~2-5x for matching downstream task performance.
- Far from 30x for general loss matching.

### 3. DoReMi — Domain Reweighting with Minimax Optimization (Xie et al., 2023)

DoReMi optimizes domain weights for pretraining data mixtures using a small
proxy model:

- Improved perplexity on all domains and downstream accuracy.
- Achieved the performance of a 2.5x larger baseline model.
- This is domain **reweighting**, not pruning — it doesn't reduce token count
  but changes the mixture. Effective multiplier: ~2-3x.

### 4. D4 — Data Deduplication and Decontamination

Deduplication (e.g., MinHash, exact substring dedup) is the most practical form
of data selection:

- Removing duplicates from C4/Pile typically removes 30-50% of tokens.
- Training on deduplicated data matches or exceeds random data at the same
  token budget — roughly a 1.5-2x efficiency gain.
- Nowhere near 30x.

### 5. SemDeDup (Abbas et al., 2023)

Semantic deduplication using embeddings:

- Showed up to ~2-4x data efficiency on language and vision tasks.
- Performance degrades at aggressive pruning ratios.

### 6. QuRating / Quality-Based Selection (Various, 2023-2024)

Quality filters (perplexity-based, classifier-based like GPT-3's quality
filter):

- FineWeb, DCLM, and similar efforts show that aggressive quality filtering
  can yield ~3-10x data efficiency for specific benchmarks.
- **But:** Aggressive filtering also narrows the distribution, which can hurt
  generalization and diversity.

---

## Why 30x Is Hard

| Factor | Impact |
|--------|--------|
| **Diminishing returns** | Early pruning removes obvious junk for big gains, but each additional cut yields less improvement |
| **Distribution narrowing** | Heavy pruning biases toward "easy" or "common" patterns, hurting tail performance |
| **Metric imperfection** | No known pruning metric is truly optimal; all introduce noise |
| **Task dependence** | 30x might work for one benchmark but fail on others |
| **Language vs. vision** | Language data has less visual redundancy; each sentence carries more unique information than similar-looking images |
| **Pretraining loss vs. downstream** | Matching pretraining loss is harder than matching downstream benchmark accuracy |

## What Would It Take?

To genuinely achieve N/30 token efficiency, you would need:

1. **Near-perfect data quality scoring** — an oracle that knows exactly which
   tokens are redundant given what the model has already learned.
2. **Curriculum-aware selection** — the optimal subset changes during training
   as the model learns, requiring dynamic re-selection.
3. **No distribution shift penalty** — the subset would need to cover the full
   support of the original distribution.

This is essentially the **active learning** ideal, which has proven difficult to
scale to LLM pretraining.

---

## Realistic Assessment

| Method | Practical data efficiency | Notes |
|--------|--------------------------|-------|
| Deduplication | 1.5-2x | Easy, always worthwhile |
| Quality filtering | 2-5x | Depends on source quality |
| Importance sampling (DSIR) | 2-5x | Domain-dependent |
| Domain reweighting (DoReMi) | 2-3x | Complementary to other methods |
| Neural data pruning (SL2N) | 5-10x (vision), 2-5x (language) | Expensive to compute |
| Combined pipeline | ~5-10x total | Stacking methods helps |
| **Theoretical optimum** | **10-30x possible** | **Unachieved in LLM pretraining** |

## Conclusion

**A 30x reduction (N/30 tokens) matching N random tokens is at the extreme
optimistic edge of theoretical predictions and has not been empirically
demonstrated for LLM pretraining loss.** The best practical systems achieve
roughly 5-10x through stacked approaches (dedup + quality filtering + importance
sampling). Sorscher et al.'s theoretical framework suggests 30x *could* be
achievable with a perfect pruning oracle, but we don't have one.

The claim is best understood as an aspirational upper bound from scaling law
theory, not a practically realized result.

---

## References

- Sorscher, B., Geirhos, R., Shekhar, S., Ganguli, S., & Morcos, A. (2022). Beyond Neural Scaling Laws: Beating Power Law Scaling via Data Pruning. *NeurIPS 2022*.
- Xie, S. M., Santurkar, S., Ma, T., & Liang, P. (2023). Data Selection for Language Models via Importance Resampling (DSIR). *NeurIPS 2023*.
- Xie, S. M., Pham, H., Dong, X., et al. (2023). DoReMi: Optimizing Data Mixtures Speeds Up Language Model Pretraining. *NeurIPS 2023*.
- Abbas, A., Tirumala, K., Simig, D., Ganguli, S., & Morcos, A. (2023). SemDeDup: Data-efficient learning at web-scale through semantic deduplication. *ICLR 2023*.
- Lee, K., Ippolito, D., Nystrom, A., et al. (2022). Deduplicating Training Data Makes Language Models Better. *ACL 2022*.
