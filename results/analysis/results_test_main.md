Runs: tgrag, naive, B1_lam1, B12_lam1, B1QI_lam1_alpha1, C, BC_lam1 | questions answered by all runs: 152

## Overall

| run | n | correct | correct_ans | correct_unans | refusal | incorrect | rouge_l | f1 | ctx_tokens | sec_per_q |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tgrag | 152 | 0.599 | 0.540 | 0.792 | 0.070 | 0.331 | 0.185 | 0.218 | 11321.007 | 5.936 |
| naive | 152 | 0.548 | 0.426 | 0.944 | 0.092 | 0.360 | 0.195 | 0.228 | nan | 3.738 |
| B1_lam1 | 152 | 0.603 | 0.554 | 0.764 | 0.053 | 0.344 | 0.190 | 0.224 | 11445.368 | 3.239 |
| B12_lam1 | 152 | 0.605 | 0.555 | 0.764 | 0.055 | 0.340 | 0.193 | 0.226 | 11462.292 | 3.129 |
| B1QI_lam1_alpha1 | 152 | 0.605 | 0.547 | 0.792 | 0.060 | 0.335 | 0.193 | 0.225 | 11461.382 | 3.431 |
| C | 152 | 0.561 | 0.468 | 0.861 | 0.070 | 0.368 | 0.179 | 0.210 | 11039.162 | 3.242 |
| BC_lam1 | 152 | 0.626 | 0.522 | 0.958 | 0.050 | 0.324 | 0.189 | 0.219 | 11389.743 | 3.971 |

## By question type

| split | group | run | n | correct | incorrect |
| --- | --- | --- | --- | --- | --- |
| question_type | multi-time query | tgrag | 62 | 0.522 | 0.407 |
| question_type | multi-time query | naive | 62 | 0.483 | 0.499 |
| question_type | multi-time query | B1_lam1 | 62 | 0.596 | 0.384 |
| question_type | multi-time query | B12_lam1 | 62 | 0.622 | 0.357 |
| question_type | multi-time query | B1QI_lam1_alpha1 | 62 | 0.617 | 0.360 |
| question_type | multi-time query | C | 62 | 0.514 | 0.413 |
| question_type | multi-time query | BC_lam1 | 62 | 0.605 | 0.371 |
| question_type | relative-time query | tgrag | 20 | 0.590 | 0.361 |
| question_type | relative-time query | naive | 20 | 0.666 | 0.306 |
| question_type | relative-time query | B1_lam1 | 20 | 0.533 | 0.454 |
| question_type | relative-time query | B12_lam1 | 20 | 0.493 | 0.466 |
| question_type | relative-time query | B1QI_lam1_alpha1 | 20 | 0.546 | 0.415 |
| question_type | relative-time query | C | 20 | 0.362 | 0.548 |
| question_type | relative-time query | BC_lam1 | 20 | 0.515 | 0.446 |
| question_type | single-time query|multi-companies | tgrag | 33 | 0.697 | 0.253 |
| question_type | single-time query|multi-companies | naive | 33 | 0.508 | 0.136 |
| question_type | single-time query|multi-companies | B1_lam1 | 33 | 0.516 | 0.333 |
| question_type | single-time query|multi-companies | B12_lam1 | 33 | 0.540 | 0.298 |
| question_type | single-time query|multi-companies | B1QI_lam1_alpha1 | 33 | 0.548 | 0.284 |
| question_type | single-time query|multi-companies | C | 33 | 0.719 | 0.249 |
| question_type | single-time query|multi-companies | BC_lam1 | 33 | 0.631 | 0.265 |
| question_type | single-time query|multi-keywords | tgrag | 37 | 0.647 | 0.257 |
| question_type | single-time query|multi-keywords | naive | 37 | 0.631 | 0.355 |
| question_type | single-time query|multi-keywords | B1_lam1 | 37 | 0.732 | 0.226 |
| question_type | single-time query|multi-keywords | B12_lam1 | 37 | 0.693 | 0.282 |
| question_type | single-time query|multi-keywords | B1QI_lam1_alpha1 | 37 | 0.667 | 0.298 |
| question_type | single-time query|multi-keywords | C | 37 | 0.607 | 0.302 |
| question_type | single-time query|multi-keywords | BC_lam1 | 37 | 0.715 | 0.232 |
| reasoning_type | comparison | tgrag | 46 | 0.379 | 0.563 |
| reasoning_type | comparison | naive | 46 | 0.400 | 0.435 |
| reasoning_type | comparison | B1_lam1 | 46 | 0.403 | 0.538 |
| reasoning_type | comparison | B12_lam1 | 46 | 0.402 | 0.531 |
| reasoning_type | comparison | B1QI_lam1_alpha1 | 46 | 0.418 | 0.522 |
| reasoning_type | comparison | C | 46 | 0.312 | 0.654 |
| reasoning_type | comparison | BC_lam1 | 46 | 0.315 | 0.634 |
| reasoning_type | enumeration | tgrag | 70 | 0.645 | 0.241 |
| reasoning_type | enumeration | naive | 70 | 0.442 | 0.467 |
| reasoning_type | enumeration | B1_lam1 | 70 | 0.652 | 0.271 |
| reasoning_type | enumeration | B12_lam1 | 70 | 0.656 | 0.269 |
| reasoning_type | enumeration | B1QI_lam1_alpha1 | 70 | 0.632 | 0.279 |
| reasoning_type | enumeration | C | 70 | 0.571 | 0.299 |
| reasoning_type | enumeration | BC_lam1 | 70 | 0.659 | 0.266 |
| reasoning_type | unanswerable|nonfact | tgrag | 4 | 0.875 | 0.125 |
| reasoning_type | unanswerable|nonfact | naive | 4 | 1.000 | 0.000 |
| reasoning_type | unanswerable|nonfact | B1_lam1 | 4 | 0.625 | 0.375 |
| reasoning_type | unanswerable|nonfact | B12_lam1 | 4 | 0.625 | 0.375 |
| reasoning_type | unanswerable|nonfact | B1QI_lam1_alpha1 | 4 | 0.875 | 0.125 |
| reasoning_type | unanswerable|nonfact | C | 4 | 0.750 | 0.250 |
| reasoning_type | unanswerable|nonfact | BC_lam1 | 4 | 0.875 | 0.125 |
| reasoning_type | unanswerable|out-of-scope | tgrag | 32 | 0.781 | 0.219 |
| reasoning_type | unanswerable|out-of-scope | naive | 32 | 0.938 | 0.062 |
| reasoning_type | unanswerable|out-of-scope | B1_lam1 | 32 | 0.781 | 0.219 |
| reasoning_type | unanswerable|out-of-scope | B12_lam1 | 32 | 0.781 | 0.219 |
| reasoning_type | unanswerable|out-of-scope | B1QI_lam1_alpha1 | 32 | 0.781 | 0.219 |
| reasoning_type | unanswerable|out-of-scope | C | 32 | 0.875 | 0.125 |
| reasoning_type | unanswerable|out-of-scope | BC_lam1 | 32 | 0.969 | 0.031 |

## Paired bootstrap on Correct (1,000 resamples)

| run | vs | delta_correct | ci_low | ci_high | p |
| --- | --- | --- | --- | --- | --- |
| naive | tgrag | -0.051 | -0.126 | 0.025 | 0.901 |
| B1_lam1 | tgrag | 0.004 | -0.049 | 0.059 | 0.445 |
| B12_lam1 | tgrag | 0.005 | -0.050 | 0.069 | 0.411 |
| B1QI_lam1_alpha1 | tgrag | 0.006 | -0.049 | 0.064 | 0.416 |
| C | tgrag | -0.038 | -0.094 | 0.020 | 0.896 |
| BC_lam1 | tgrag | 0.026 | -0.039 | 0.094 | 0.215 |

## Paired bootstrap on Correct, answerable questions only

| run | vs | n | delta_correct | ci_low | ci_high | p |
| --- | --- | --- | --- | --- | --- | --- |
| naive | tgrag | 116 | -0.114 | -0.211 | -0.022 | 0.992 |
| B1_lam1 | tgrag | 116 | 0.014 | -0.049 | 0.083 | 0.334 |
| B12_lam1 | tgrag | 116 | 0.016 | -0.051 | 0.091 | 0.313 |
| B1QI_lam1_alpha1 | tgrag | 116 | 0.007 | -0.059 | 0.085 | 0.418 |
| C | tgrag | 116 | -0.071 | -0.136 | -0.003 | 0.979 |
| BC_lam1 | tgrag | 116 | -0.017 | -0.084 | 0.055 | 0.683 |

A gain is significant at 5% when ci_low > 0 (equivalently p < 0.025 one-sided).

CSV files written to results_test/
