Runs: tgrag_noise0.1, B1_lam1_noise0.1 | questions answered by all runs: 152

## Overall

| run | n | correct | correct_ans | correct_unans | refusal | incorrect | rouge_l | f1 | ctx_tokens | sec_per_q |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tgrag_noise0.1 | 152 | 0.600 | 0.570 | 0.694 | 0.058 | 0.343 | 0.191 | 0.221 | 11447.855 | 4.580 |
| B1_lam1_noise0.1 | 152 | 0.582 | 0.521 | 0.778 | 0.066 | 0.352 | 0.194 | 0.229 | 11446.867 | 4.977 |

## By question type

| split | group | run | n | correct | incorrect |
| --- | --- | --- | --- | --- | --- |
| question_type | multi-time query | tgrag_noise0.1 | 62 | 0.556 | 0.398 |
| question_type | multi-time query | B1_lam1_noise0.1 | 62 | 0.573 | 0.395 |
| question_type | relative-time query | tgrag_noise0.1 | 20 | 0.579 | 0.386 |
| question_type | relative-time query | B1_lam1_noise0.1 | 20 | 0.551 | 0.362 |
| question_type | single-time query|multi-companies | tgrag_noise0.1 | 33 | 0.680 | 0.248 |
| question_type | single-time query|multi-companies | B1_lam1_noise0.1 | 33 | 0.506 | 0.343 |
| question_type | single-time query|multi-keywords | tgrag_noise0.1 | 37 | 0.613 | 0.310 |
| question_type | single-time query|multi-keywords | B1_lam1_noise0.1 | 37 | 0.682 | 0.283 |
| reasoning_type | comparison | tgrag_noise0.1 | 46 | 0.432 | 0.524 |
| reasoning_type | comparison | B1_lam1_noise0.1 | 46 | 0.371 | 0.565 |
| reasoning_type | enumeration | tgrag_noise0.1 | 70 | 0.661 | 0.243 |
| reasoning_type | enumeration | B1_lam1_noise0.1 | 70 | 0.620 | 0.279 |
| reasoning_type | unanswerable|nonfact | tgrag_noise0.1 | 4 | 0.500 | 0.500 |
| reasoning_type | unanswerable|nonfact | B1_lam1_noise0.1 | 4 | 0.750 | 0.250 |
| reasoning_type | unanswerable|out-of-scope | tgrag_noise0.1 | 32 | 0.719 | 0.281 |
| reasoning_type | unanswerable|out-of-scope | B1_lam1_noise0.1 | 32 | 0.781 | 0.219 |

## Paired bootstrap on Correct (1,000 resamples)

| run | vs | delta_correct | ci_low | ci_high | p |
| --- | --- | --- | --- | --- | --- |
| B1_lam1_noise0.1 | tgrag_noise0.1 | -0.018 | -0.081 | 0.043 | 0.719 |

## Paired bootstrap on Correct, answerable questions only

| run | vs | n | delta_correct | ci_low | ci_high | p |
| --- | --- | --- | --- | --- | --- | --- |
| B1_lam1_noise0.1 | tgrag_noise0.1 | 116 | -0.049 | -0.123 | 0.025 | 0.904 |

A gain is significant at 5% when ci_low > 0 (equivalently p < 0.025 one-sided).

CSV files written to results_test_noise0.1/
