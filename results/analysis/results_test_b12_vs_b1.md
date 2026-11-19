Runs: B12_lam1, B1_lam1 | questions answered by all runs: 152

## Overall

| run | n | correct | correct_ans | correct_unans | refusal | incorrect | rouge_l | f1 | ctx_tokens | sec_per_q |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B12_lam1 | 152 | 0.605 | 0.555 | 0.764 | 0.055 | 0.340 | 0.193 | 0.226 | 11462.292 | 3.129 |
| B1_lam1 | 152 | 0.603 | 0.554 | 0.764 | 0.053 | 0.344 | 0.190 | 0.224 | 11445.368 | 3.239 |

## By question type

| split | group | run | n | correct | incorrect |
| --- | --- | --- | --- | --- | --- |
| question_type | multi-time query | B12_lam1 | 62 | 0.622 | 0.357 |
| question_type | multi-time query | B1_lam1 | 62 | 0.596 | 0.384 |
| question_type | relative-time query | B12_lam1 | 20 | 0.493 | 0.466 |
| question_type | relative-time query | B1_lam1 | 20 | 0.533 | 0.454 |
| question_type | single-time query|multi-companies | B12_lam1 | 33 | 0.540 | 0.298 |
| question_type | single-time query|multi-companies | B1_lam1 | 33 | 0.516 | 0.333 |
| question_type | single-time query|multi-keywords | B12_lam1 | 37 | 0.693 | 0.282 |
| question_type | single-time query|multi-keywords | B1_lam1 | 37 | 0.732 | 0.226 |
| reasoning_type | comparison | B12_lam1 | 46 | 0.402 | 0.531 |
| reasoning_type | comparison | B1_lam1 | 46 | 0.403 | 0.538 |
| reasoning_type | enumeration | B12_lam1 | 70 | 0.656 | 0.269 |
| reasoning_type | enumeration | B1_lam1 | 70 | 0.652 | 0.271 |
| reasoning_type | unanswerable|nonfact | B12_lam1 | 4 | 0.625 | 0.375 |
| reasoning_type | unanswerable|nonfact | B1_lam1 | 4 | 0.625 | 0.375 |
| reasoning_type | unanswerable|out-of-scope | B12_lam1 | 32 | 0.781 | 0.219 |
| reasoning_type | unanswerable|out-of-scope | B1_lam1 | 32 | 0.781 | 0.219 |

## Paired bootstrap on Correct (1,000 resamples)

| run | vs | delta_correct | ci_low | ci_high | p |
| --- | --- | --- | --- | --- | --- |
| B12_lam1 | B1_lam1 | 0.001 | -0.037 | 0.044 | 0.435 |

## Paired bootstrap on Correct, answerable questions only

| run | vs | n | delta_correct | ci_low | ci_high | p |
| --- | --- | --- | --- | --- | --- | --- |
| B12_lam1 | B1_lam1 | 116 | 0.002 | -0.045 | 0.054 | 0.462 |

A gain is significant at 5% when ci_low > 0 (equivalently p < 0.025 one-sided).

CSV files written to results_test_b12_vs_b1/
