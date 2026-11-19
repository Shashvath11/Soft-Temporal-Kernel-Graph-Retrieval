| Method | Correct (all) | Correct (answerable) | Correct (unanswerable) | ROUGE-L | F1 | Δ Correct vs TG-RAG (all) [95% CI] | Δ Correct vs TG-RAG (answerable) [95% CI] |
|---|---|---|---|---|---|---|---|
| TG-RAG (reproduced, hard filter) | 0.599 | 0.540 | 0.792 | 0.185 | 0.218 | – | – |
| Naive RAG (chunks only) | 0.548 | 0.426 | 0.944 | 0.195 | 0.228 | −0.051 [−0.126, +0.025], p = 0.901 | −0.114 [−0.211, −0.022], p = 0.992 |
| B1: soft time kernel, λ = 1 (ours) | 0.603 | 0.554 | 0.764 | 0.190 | 0.224 | +0.004 [−0.049, +0.059], p = 0.445 | +0.014 [−0.049, +0.083], p = 0.334 |
| B1QI: question-independent decay | 0.605 | 0.547 | 0.792 | 0.193 | 0.225 | +0.006 [−0.049, +0.064], p = 0.416 | +0.007 [−0.059, +0.085], p = 0.418 |

- Test set: 152 questions (116 answerable, 36 unanswerable), 6 companies of ECT-QA, run once with settings locked on dev (λ = 1, κ_min = 0.05, top_k = 20, 12,000 context tokens).
- Correct = LLM judge (gpt-4o-mini), 0–1 per question. ROUGE-L and F1 are on answerable questions only.
- Δ: paired bootstrap, 1,000 resamples, seed 0; p is one-sided (share of resamples with Δ ≤ 0); * = 95% CI above 0 (one-sided p < 0.025).
- TG-RAG's paper reports Correct = 0.599 on the full ECT-QA benchmark with its own models and judge prompts. Our reproduced TG-RAG also scores 0.599 here, by coincidence; the numbers are not comparable (different subset, judge wording and models).
- Naive RAG scores high on unanswerable questions mainly because it refuses often; see the answerable column.
