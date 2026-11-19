Runs: tgrag_noise0.2, B1_lam1_noise0.2 | questions answered by all runs: 152

## Overall

| run | n | correct | correct_ans | correct_unans | refusal | incorrect | rouge_l | f1 | ctx_tokens | sec_per_q |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tgrag_noise0.2 | 152 | 0.575 | 0.534 | 0.708 | 0.071 | 0.354 | 0.182 | 0.211 | 11422.080 | 2.983 |
| B1_lam1_noise0.2 | 152 | 0.606 | 0.547 | 0.796 | 0.061 | 0.333 | 0.190 | 0.221 | 11433.951 | 2.823 |

## By question type

| split | group | run | n | correct | incorrect |
| --- | --- | --- | --- | --- | --- |
| question_type | multi-time query | tgrag_noise0.2 | 62 | 0.548 | 0.396 |
| question_type | multi-time query | B1_lam1_noise0.2 | 62 | 0.604 | 0.378 |
| question_type | relative-time query | tgrag_noise0.2 | 20 | 0.546 | 0.426 |
| question_type | relative-time query | B1_lam1_noise0.2 | 20 | 0.559 | 0.408 |
| question_type | single-time query|multi-companies | tgrag_noise0.2 | 33 | 0.628 | 0.257 |
| question_type | single-time query|multi-companies | B1_lam1_noise0.2 | 33 | 0.481 | 0.320 |
| question_type | single-time query|multi-keywords | tgrag_noise0.2 | 37 | 0.588 | 0.330 |
| question_type | single-time query|multi-keywords | B1_lam1_noise0.2 | 37 | 0.747 | 0.230 |
| reasoning_type | comparison | tgrag_noise0.2 | 46 | 0.400 | 0.534 |
| reasoning_type | comparison | B1_lam1_noise0.2 | 46 | 0.357 | 0.556 |
| reasoning_type | enumeration | tgrag_noise0.2 | 70 | 0.621 | 0.267 |
| reasoning_type | enumeration | B1_lam1_noise0.2 | 70 | 0.672 | 0.253 |
| reasoning_type | unanswerable|nonfact | tgrag_noise0.2 | 4 | 0.625 | 0.375 |
| reasoning_type | unanswerable|nonfact | B1_lam1_noise0.2 | 4 | 0.667 | 0.333 |
| reasoning_type | unanswerable|out-of-scope | tgrag_noise0.2 | 32 | 0.719 | 0.281 |
| reasoning_type | unanswerable|out-of-scope | B1_lam1_noise0.2 | 32 | 0.812 | 0.188 |

## Paired bootstrap on Correct (1,000 resamples)

| run | vs | delta_correct | ci_low | ci_high | p |
| --- | --- | --- | --- | --- | --- |
| B1_lam1_noise0.2 | tgrag_noise0.2 | 0.031 | -0.027 | 0.096 | 0.155 |

## Paired bootstrap on Correct, answerable questions only

| run | vs | n | delta_correct | ci_low | ci_high | p |
| --- | --- | --- | --- | --- | --- | --- |
| B1_lam1_noise0.2 | tgrag_noise0.2 | 116 | 0.013 | -0.059 | 0.092 | 0.351 |

A gain is significant at 5% when ci_low > 0 (equivalently p < 0.025 one-sided).

CSV files written to results_test_noise0.2/
