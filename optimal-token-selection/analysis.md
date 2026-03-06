# Can N/30 Optimally Selected Tokens Match N Random Tokens?

## Short Answer

**Not reliably in practice, but theoretically plausible in narrow settings.** The
best empirical results achieve ~10x data efficiency with quality filtering, and
up to ~20x at small scale with curriculum methods. A full 30x compression ratio
that preserves loss parity remains beyond what has been convincingly demonstrated
for large-scale language model pretraining — and a key negative result (Ayed &
Hayou, 2024) shows fundamental limitations of score-based pruning at high
compression.

---

## Key Results from the Literature

### 1. Beyond Neural Scaling Laws (Sorscher et al., 2022)

The most optimistic paper for the N/30 claim. Sorscher et al. showed that with
optimal data pruning, you can **break power-law scaling** and achieve
**exponential scaling** instead:

- **Power-law regime (no pruning):** Loss ~ N^(-α) where α ≈ 0.4-0.5
- **Exponential regime (with pruning):** Loss ~ exp(-cN) for a curated subset

The theory introduces a **pruning metric quality parameter θ**. With θ near 0 (a
perfect metric), you get exponential scaling and enormous compression. But with
any imperfect metric (θ > 0), there is always a crossover point where
exponential scaling reverts to power law. At θ = 10°, the minimum retainable
fraction is ~24%. At θ = 20°, it is ~46%.

**Empirical results:**
- CIFAR-10: 50% retained with no accuracy loss (2x compression, EL2N metric)
- CIFAR-100: 75% retained (1.3x compression)
- ImageNet: 80% retained (1.25x compression, memorization metric)
- Transfer learning (ImageNet→CIFAR-10): 10% of CIFAR-10 suffices (10x, but
  transfer setting)

**Critical caveat:** Results were primarily on image classification, not
autoregressive language modeling. No existing metric achieves θ near 0 at scale.

### 2. Fundamental Limitations (Ayed & Hayou, 2024)

**"Data Pruning and Neural Scaling Laws: Fundamental Limitations of Score-Based
Algorithms"** (ICML 2024) demonstrates "No Free Lunch" theorems for data
pruning:

- Score-based pruning methods **fail in the high compression regime** (keeping
  <30% of data).
- Random pruning remains a strong baseline and outperforms most existing
  score-based methods when keeping less than ~30% of data.
- **This is a significant negative result for the 30x claim**, since N/30
  means retaining only ~3.3% of data.

### 3. Ask-LLM (Sachdeva et al., 2024)

**"How to Train Data-Efficient LLMs"** — the strongest clean result for
pretraining data selection:

- Uses an instruction-tuned LLM to score training example quality.
- Rejects **90% of data** (keeps 10%) while **outperforming** full-data
  training, converging up to 70% faster.
- **~10x compression** — the best documented ratio for LLM pretraining.

### 4. FineWeb-Edu

Achieves comparable LLM capabilities to full FineWeb with roughly **~10x fewer
tokens** through educational content filtering.

### 5. LFR — Learn, Focus, and Review (2024)

Curriculum-based method using spaced repetition:

- **20x fewer training iterations** for GPT-2 scale models on OpenWebText with
  lower perplexity.
- Caveat: this is curriculum scheduling (spaced repetition), not data selection
  from unique examples.

### 6. DoReMi (Xie et al., 2023)

Optimizes domain weights for pretraining data mixtures using a small proxy model:

- Reaches baseline accuracy with **2.6x fewer training steps**.
- This is domain **reweighting**, not pruning.

### 7. DSIR — Data Selection with Importance Resampling (Xie et al., 2023)

Selects pretraining data to match a target distribution using n-gram features:

- ~2-5x efficiency gains for matching downstream task performance.

### 8. SemDeDup (Abbas et al., 2023)

Semantic deduplication using embeddings:

- Removes 50% of LAION data with minimal performance loss (2x compression).
- Performance degrades at aggressive pruning ratios.

### 9. Phi — "Textbooks Are All You Need" (Gunasekar et al., 2023)

- 1.3B model matches or exceeds models 10x larger on code benchmarks, trained
  on **100x less data** (7B tokens vs. hundreds of billions).
- But: uses **synthetically generated** "textbook quality" data — fundamentally
  different from selecting a subset of existing data.

### 10. When Less is More (Marion et al., 2023)

- Training on **30% of data** selected by perplexity improves over the
  full-data baseline (~3x compression with improvement).

### 11. Rho-1 — Selective Language Modeling

- Performs **token-level** (not document-level) selection, training only on
  "useful" tokens. Up to 30% absolute improvement on math tasks.

---

## Empirical Compression Ratios Summary

| Method | Compression | Setting |
|--------|------------|---------|
| Ask-LLM | ~10x | LLM pretraining |
| FineWeb-Edu | ~10x | LLM pretraining |
| LFR pedagogy | ~20x | GPT-2 scale (curriculum) |
| Phi (synthetic) | ~100x | Code tasks, synthetic data |
| Sorscher (theory, perfect metric) | Unbounded | Vision, theoretical |
| Sorscher (empirical, ImageNet) | 1.25x | Vision |
| DoReMi | 2.6x | LLM pretraining |
| "When Less is More" | ~3x | LLM pretraining |
| SemDeDup | ~2x | Vision/language |
| DSIR | 2-5x | Domain-dependent |
| Deduplication | 1.5-2x | Universal |

---

## Why 30x Is Hard

| Factor | Impact |
|--------|--------|
| **No Free Lunch (Ayed & Hayou)** | Score-based pruning provably fails below ~30% retention |
| **Diminishing returns** | Early pruning removes obvious junk for big gains; each additional cut yields less |
| **Distribution narrowing** | Heavy pruning biases toward "easy" patterns, hurting tail performance |
| **Metric imperfection** | No known pruning metric is truly optimal; all introduce noise |
| **Task dependence** | 30x might work for one benchmark but fail on others |
| **Language vs. vision** | Language data has less redundancy per example than images |
| **Pretraining loss vs. downstream** | Matching pretraining loss is harder than matching benchmark accuracy |
| **Scale dependence** | Many results are at small scale (GPT-2, ResNets); unclear if they hold at frontier scale |

## What Would It Take?

To genuinely achieve N/30 token efficiency, you would likely need to combine:

1. **Near-perfect data quality scoring** — an oracle that knows exactly which
   tokens are redundant given what the model has already learned.
2. **Curriculum-aware dynamic selection** — re-selecting as the model learns.
3. **Token-level selection** (Rho-1 style) — not just document-level.
4. **No distribution shift penalty** — the subset covering the full support.
5. **Possibly synthetic data augmentation** — replacing low-quality examples
   with high-quality synthetic ones.

---

## Conclusion

**A 30x reduction (N/30 tokens) matching N random tokens is at the extreme
optimistic edge of theoretical predictions and has not been empirically
demonstrated for general LLM pretraining loss.**

- **~10x** is achievable with strong quality-based filtering (Ask-LLM, FineWeb-Edu)
- **~20x** has been shown at small scale with curriculum methods (LFR)
- **30x** sits in a regime where fundamental limitations of score-based pruning
  kick in (Ayed & Hayou, 2024), requiring only ~3.3% data retention
- **~100x** is possible with synthetic data (Phi), but that's a different paradigm

The claim is best understood as an aspirational upper bound from scaling law
theory. Getting there for real LLM pretraining would likely require breakthroughs
in pruning metric quality, combining quality filtering, deduplication, domain
reweighting, token-level selection, and curriculum design simultaneously.

---

## References

- Sorscher, B., Geirhos, R., Shekhar, S., Ganguli, S., & Morcos, A. (2022). Beyond Neural Scaling Laws: Beating Power Law Scaling via Data Pruning. *NeurIPS 2022*. https://arxiv.org/abs/2206.14486
- Ayed, F. & Hayou, S. (2024). Data Pruning and Neural Scaling Laws: Fundamental Limitations of Score-Based Algorithms. *ICML 2024*. https://arxiv.org/abs/2302.06960
- Sachdeva, N., et al. (2024). How to Train Data-Efficient LLMs (Ask-LLM). https://arxiv.org/abs/2402.09668
- Xie, S. M., Pham, H., Dong, X., et al. (2023). DoReMi: Optimizing Data Mixtures Speeds Up Language Model Pretraining. *NeurIPS 2023*. https://arxiv.org/abs/2305.10429
- Xie, S. M., Santurkar, S., Ma, T., & Liang, P. (2023). Data Selection for Language Models via Importance Resampling (DSIR). *NeurIPS 2023*. https://arxiv.org/abs/2302.03169
- Tirumala, K., et al. (2023). D4: Improving LLM Pretraining via Document De-Duplication and Diversification. https://arxiv.org/abs/2308.12284
- Abbas, A., Tirumala, K., Simig, D., Ganguli, S., & Morcos, A. (2023). SemDeDup: Data-efficient learning at web-scale through semantic deduplication. *ICLR 2023*. https://arxiv.org/abs/2303.09540
- Gunasekar, S., et al. (2023). Textbooks Are All You Need (Phi). https://arxiv.org/abs/2306.11644
- Marion, M., et al. (2023). When Less is More: Investigating Data Pruning for Pretraining LLMs at Scale. https://arxiv.org/abs/2309.04564
- Rho-1: Not All Tokens Are What You Need. https://openreview.net/forum?id=0NMzBwqaAJ
- LFR: Learn, Focus, and Review. https://arxiv.org/html/2409.06131v1
- Lee, K., Ippolito, D., Nystrom, A., et al. (2022). Deduplicating Training Data Makes Language Models Better. *ACL 2022*.
