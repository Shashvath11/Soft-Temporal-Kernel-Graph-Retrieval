| Shifted timestamps | TG-RAG Correct (all) | B1 Correct (all) | Δ (all) [95% CI] | TG-RAG Correct (answerable) | B1 Correct (answerable) | Δ (answerable) [95% CI] |
|---|---|---|---|---|---|---|
| 0% | 0.599 | 0.603 | +0.004 [−0.049, +0.059], p = 0.445 | 0.540 | 0.554 | +0.014 [−0.049, +0.083], p = 0.334 |
| 10% | 0.600 | 0.582 | −0.018 [−0.081, +0.043], p = 0.719 | 0.570 | 0.521 | −0.049 [−0.123, +0.025], p = 0.904 |
| 20% | 0.575 | 0.606 | +0.031 [−0.027, +0.096], p = 0.155 | 0.534 | 0.547 | +0.013 [−0.059, +0.092], p = 0.351 |
| 30% | 0.566 | 0.627 | +0.061 [+0.005, +0.120], p = 0.019 * | 0.526 | 0.585 | +0.059 [−0.004, +0.126], p = 0.036 |

- Noise: each stored timestamp is shifted by ± one quarter with the given probability (deterministic hash, seed 13).
- Six tests (3 rates × 2 splits); with a Bonferroni correction the threshold would be p < 0.025/6 ≈ 0.004, which none meets.
- B1 at 30 % noise scores above clean B1, so part of the gap is run-to-run variation.
