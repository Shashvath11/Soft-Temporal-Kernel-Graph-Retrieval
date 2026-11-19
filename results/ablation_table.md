| Method | Correct (all) | Correct (answerable) | Correct (unanswerable) | ROUGE-L | F1 | Δ Correct vs TG-RAG (all) [95% CI] | Δ Correct vs TG-RAG (answerable) [95% CI] |
|---|---|---|---|---|---|---|---|
| B1: soft time kernel, λ = 1 (ours) | 0.603 | 0.554 | 0.764 | 0.190 | 0.224 | +0.004 [−0.049, +0.059], p = 0.445 | +0.014 [−0.049, +0.083], p = 0.334 |
| B12: B1 + κ in PageRank walk | 0.605 | 0.555 | 0.764 | 0.193 | 0.226 | +0.005 [−0.050, +0.069], p = 0.411 | +0.016 [−0.051, +0.091], p = 0.313 |
| B1QI: question-independent decay | 0.605 | 0.547 | 0.792 | 0.193 | 0.225 | +0.006 [−0.049, +0.064], p = 0.416 | +0.007 [−0.059, +0.085], p = 0.418 |
| C: hard filter + hybrid BM25 + dense seeding | 0.561 | 0.468 | 0.861 | 0.179 | 0.210 | −0.038 [−0.094, +0.020], p = 0.896 | −0.071 [−0.136, −0.003], p = 0.979 |
| BC: B12 + hybrid seeding | 0.626 | 0.522 | 0.958 | 0.189 | 0.219 | +0.026 [−0.039, +0.094], p = 0.215 | −0.017 [−0.084, +0.055], p = 0.683 |

- Test set: 152 questions (116 answerable, 36 unanswerable), 6 companies of ECT-QA, run once with settings locked on dev (λ = 1, κ_min = 0.05, top_k = 20, 12,000 context tokens).
- Correct = LLM judge (gpt-4o-mini), 0–1 per question. ROUGE-L and F1 are on answerable questions only.
- Δ: paired bootstrap, 1,000 resamples, seed 0; p is one-sided (share of resamples with Δ ≤ 0); * = 95% CI above 0 (one-sided p < 0.025).

Secondary pre-registered pairs (paired bootstrap, same settings):

| Pair | Δ Correct (all) [95% CI] | Δ Correct (answerable) [95% CI] |
|---|---|---|
| B12 vs B1QI | −0.000 [−0.036, +0.039], p = 0.461 | +0.008 [−0.043, +0.058], p = 0.368 |
| B12 vs B1 | +0.001 [−0.037, +0.044], p = 0.435 | +0.002 [−0.045, +0.054], p = 0.462 |
