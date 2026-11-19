Runs: B12_lam1, B1QI_lam1_alpha1 | questions answered by all runs: 152

## Overall

| run | n | correct | correct_ans | correct_unans | refusal | incorrect | rouge_l | f1 | ctx_tokens | sec_per_q |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B12_lam1 | 152 | 0.605 | 0.555 | 0.764 | 0.055 | 0.340 | 0.193 | 0.226 | 11462.292 | 3.129 |
| B1QI_lam1_alpha1 | 152 | 0.605 | 0.547 | 0.792 | 0.060 | 0.335 | 0.193 | 0.225 | 11461.382 | 3.431 |

## By question type

| split | group | run | n | correct | incorrect |
| --- | --- | --- | --- | --- | --- |
| question_type | multi-time query | B12_lam1 | 62 | 0.622 | 0.357 |
| question_type | multi-time query | B1QI_lam1_alpha1 | 62 | 0.617 | 0.360 |
| question_type | relative-time query | B12_lam1 | 20 | 0.493 | 0.466 |
| question_type | relative-time query | B1QI_lam1_alpha1 | 20 | 0.546 | 0.415 |
| question_type | single-time query|multi-companies | B12_lam1 | 33 | 0.540 | 0.298 |
| question_type | single-time query|multi-companies | B1QI_lam1_alpha1 | 33 | 0.548 | 0.284 |
| question_type | single-time query|multi-keywords | B12_lam1 | 37 | 0.693 | 0.282 |
| question_type | single-time query|multi-keywords | B1QI_lam1_alpha1 | 37 | 0.667 | 0.298 |
| reasoning_type | comparison | B12_lam1 | 46 | 0.402 | 0.531 |
| reasoning_type | comparison | B1QI_lam1_alpha1 | 46 | 0.418 | 0.522 |
| reasoning_type | enumeration | B12_lam1 | 70 | 0.656 | 0.269 |
| reasoning_type | enumeration | B1QI_lam1_alpha1 | 70 | 0.632 | 0.279 |
| reasoning_type | unanswerable|nonfact | B12_lam1 | 4 | 0.625 | 0.375 |
| reasoning_type | unanswerable|nonfact | B1QI_lam1_alpha1 | 4 | 0.875 | 0.125 |
| reasoning_type | unanswerable|out-of-scope | B12_lam1 | 32 | 0.781 | 0.219 |
| reasoning_type | unanswerable|out-of-scope | B1QI_lam1_alpha1 | 32 | 0.781 | 0.219 |

## Paired bootstrap on Correct (1,000 resamples)

| run | vs | delta_correct | ci_low | ci_high | p |
| --- | --- | --- | --- | --- | --- |
| B12_lam1 | B1QI_lam1_alpha1 | -0.000 | -0.036 | 0.039 | 0.461 |

## Paired bootstrap on Correct, answerable questions only

| run | vs | n | delta_correct | ci_low | ci_high | p |
| --- | --- | --- | --- | --- | --- | --- |
| B12_lam1 | B1QI_lam1_alpha1 | 116 | 0.008 | -0.043 | 0.058 | 0.368 |

A gain is significant at 5% when ci_low > 0 (equivalently p < 0.025 one-sided).

CSV files written to results_test_b12_vs_b1qi/
