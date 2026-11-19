Runs: tgrag_noise0.3, B1_lam1_noise0.3 | questions answered by all runs: 152

## Overall

| run | n | correct | correct_ans | correct_unans | refusal | incorrect | rouge_l | f1 | ctx_tokens | sec_per_q |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tgrag_noise0.3 | 152 | 0.566 | 0.526 | 0.694 | 0.071 | 0.363 | 0.187 | 0.215 | 11460.619 | 2.952 |
| B1_lam1_noise0.3 | 152 | 0.627 | 0.585 | 0.764 | 0.062 | 0.311 | 0.188 | 0.218 | 11434.771 | 2.724 |

## By question type

| split | group | run | n | correct | incorrect |
| --- | --- | --- | --- | --- | --- |
| question_type | multi-time query | tgrag_noise0.3 | 62 | 0.556 | 0.396 |
| question_type | multi-time query | B1_lam1_noise0.3 | 62 | 0.641 | 0.339 |
| question_type | relative-time query | tgrag_noise0.3 | 20 | 0.546 | 0.411 |
| question_type | relative-time query | B1_lam1_noise0.3 | 20 | 0.688 | 0.254 |
| question_type | single-time query|multi-companies | tgrag_noise0.3 | 33 | 0.563 | 0.333 |
| question_type | single-time query|multi-companies | B1_lam1_noise0.3 | 33 | 0.490 | 0.314 |
| question_type | single-time query|multi-keywords | tgrag_noise0.3 | 37 | 0.597 | 0.310 |
| question_type | single-time query|multi-keywords | B1_lam1_noise0.3 | 37 | 0.695 | 0.291 |
| reasoning_type | comparison | tgrag_noise0.3 | 46 | 0.364 | 0.578 |
| reasoning_type | comparison | B1_lam1_noise0.3 | 46 | 0.505 | 0.428 |
| reasoning_type | enumeration | tgrag_noise0.3 | 70 | 0.633 | 0.252 |
| reasoning_type | enumeration | B1_lam1_noise0.3 | 70 | 0.638 | 0.272 |
| reasoning_type | unanswerable|nonfact | tgrag_noise0.3 | 4 | 0.500 | 0.500 |
| reasoning_type | unanswerable|nonfact | B1_lam1_noise0.3 | 4 | 0.375 | 0.625 |
| reasoning_type | unanswerable|out-of-scope | tgrag_noise0.3 | 32 | 0.719 | 0.281 |
| reasoning_type | unanswerable|out-of-scope | B1_lam1_noise0.3 | 32 | 0.812 | 0.188 |

## Paired bootstrap on Correct (1,000 resamples)

| run | vs | delta_correct | ci_low | ci_high | p |
| --- | --- | --- | --- | --- | --- |
| B1_lam1_noise0.3 | tgrag_noise0.3 | 0.061 | 0.005 | 0.120 | 0.019 |

## Paired bootstrap on Correct, answerable questions only

| run | vs | n | delta_correct | ci_low | ci_high | p |
| --- | --- | --- | --- | --- | --- | --- |
| B1_lam1_noise0.3 | tgrag_noise0.3 | 116 | 0.059 | -0.004 | 0.126 | 0.036 |

A gain is significant at 5% when ci_low > 0 (equivalently p < 0.025 one-sided).

CSV files written to results_test_noise0.3/
