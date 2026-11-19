# Results summary: every number and the command behind it

All commands are run from `C:\Research\Temporal-GraphRAG` with `C:\Users\shash\miniconda3\envs\tgrag\python.exe` (written `python` below).
Model calls use temperature 0 and TG-RAG's response cache. Seeds: data split 42, timestamp noise 13, bootstrap 0, hand-check sampling 42.
Settings locked on dev and used for every test run: λ = 1, κ_min = 0.05, top_k = 20, 12,000 context tokens.
Each run file stores its exact retrieval settings in the `settings` field of every record.

## 1. Data and graph (done before 18 Nov 2026; never rebuilt)
| Result | Command |
|---|---|
| Subset: 6 companies, 96 transcripts; 37 dev / 152 test questions (stratified by question type, seed 42) | `python scripts/make_subset.py --companies 6` |
| Graph: 96 docs, 378 chunks in `graph_subset/` (gemini-2.5-flash-lite) | built once with TG-RAG's `build_graph.py`. **Do not rebuild**: it costs money and changes every result |
| Graph statistics, 824 / 8,476 relation stamps unparseable (9.7 %) | `python scripts/graph_stats.py graph_subset` |

## 2. Dev set (37 questions): `results_dev/`, `results/dev_table.md`
Run files: `runs/dev_<run>.jsonl`. The commands follow the same pattern as the test runs, with `--questions ect-qa/subset/dev.jsonl` (variant and λ as recorded in each file's `settings`):
```
python scripts/run_ectqa.py --working_dir graph_subset --questions ect-qa/subset/dev.jsonl --variant original --out runs/dev_original.jsonl
python scripts/run_ectqa.py --working_dir graph_subset --questions ect-qa/subset/dev.jsonl --variant tgrag --out runs/dev_tgrag.jsonl
python scripts/run_ectqa.py --working_dir graph_subset --questions ect-qa/subset/dev.jsonl --variant naive --out runs/dev_naive.jsonl
python scripts/run_ectqa.py --working_dir graph_subset --questions ect-qa/subset/dev.jsonl --variant B1 --lam <0.25|0.5|1|2|4|1000> --out runs/dev_B1_lam<λ>.jsonl
python scripts/run_ectqa.py --working_dir graph_subset --questions ect-qa/subset/dev.jsonl --variant B12 --lam 1 --out runs/dev_B12_lam1.jsonl
python scripts/run_ectqa.py --working_dir graph_subset --questions ect-qa/subset/dev.jsonl --variant B1QI --lam 1 --alpha 1 --out runs/dev_B1QI_lam1_alpha1.jsonl
python scripts/run_ectqa.py --working_dir graph_subset --questions ect-qa/subset/dev.jsonl --variant C --out runs/dev_C.jsonl
python scripts/run_ectqa.py --working_dir graph_subset --questions ect-qa/subset/dev.jsonl --variant BC --lam 1 --out runs/dev_BC_lam1.jsonl
python scripts/judge.py runs/dev_*.jsonl
python scripts/analyze.py runs/dev_*.judged.jsonl --reference tgrag --out results_dev
```
| Result | Value | Source |
|---|---|---|
| tgrag matches TG-RAG's original retrieval | 36 / 37 questions (97 %) | `python scripts/compare_retrieval.py runs/dev_original.jsonl runs/dev_tgrag.jsonl` |
| λ = 1000 vs tgrag | 0.447 vs 0.445 Correct (95 % identical evidence) | `results_dev/overall.csv` |
| B1 λ = 1 vs tgrag | 0.522 vs 0.445, Δ +0.077 [−0.050, 0.208], p = 0.113 | `results_dev/significance.csv` |
| λ sweep | 0.25: 0.519, 0.5: 0.482, 1: 0.522, 2: 0.481, 4: 0.456, 1000: 0.447 | `paper/figures/lambda_sweep_dev.csv` |

## 3. Test set (152 questions), run once on 18 Nov 2026: `results_test*/`
All 13 runs (the commands in `scripts/run_test_suite.bat`) finished with 152 answers each and 0 errors.
```
python scripts/run_ectqa.py --working_dir graph_subset --questions ect-qa/subset/test.jsonl --variant <v> [--lam 1] [--alpha 1] [--noise <0.1|0.2|0.3>] --out runs/test_<run>.jsonl
python scripts/judge.py runs/test_*.jsonl
python scripts/analyze.py runs/test_tgrag.judged.jsonl runs/test_naive.judged.jsonl runs/test_B1_lam1.judged.jsonl runs/test_B12_lam1.judged.jsonl runs/test_B1QI_lam1_alpha1.judged.jsonl runs/test_C.judged.jsonl runs/test_BC_lam1.judged.jsonl --reference tgrag --out results_test > results_test_main.md
python scripts/analyze.py runs/test_tgrag_noise<N>.judged.jsonl runs/test_B1_lam1_noise<N>.judged.jsonl --reference tgrag_noise<N> --out results_test_noise<N> > results_test_noise<N>.md
python scripts/analyze.py runs/test_B12_lam1.judged.jsonl runs/test_B1QI_lam1_alpha1.judged.jsonl --reference B1QI_lam1_alpha1 --out results_test_b12_vs_b1qi > results_test_b12_vs_b1qi.md
python scripts/analyze.py runs/test_B12_lam1.judged.jsonl runs/test_B1_lam1.judged.jsonl --reference B1_lam1 --out results_test_b12_vs_b1 > results_test_b12_vs_b1.md
```
| Pre-registered claim | Result | Verdict |
|---|---|---|
| B1 vs tgrag, overall Correct | 0.603 vs 0.599, Δ +0.004 [−0.049, +0.059], p = 0.445 | not supported |
| B1 vs tgrag, answerable | 0.554 vs 0.540, Δ +0.014 [−0.049, +0.083], p = 0.334 | not supported |
| B12 vs B1QI | Δ −0.000 [−0.036, +0.039], p = 0.461 | not supported |
| B12 vs B1 | Δ +0.001 [−0.037, +0.044], p = 0.435 | not supported |
| C vs tgrag | Δ −0.038 [−0.094, +0.020], p = 0.896; answerable −0.071 [−0.136, −0.003] | not supported; C is worse on answerable questions |
| Robustness, 10 % noise (B1 − tgrag) | Δ −0.018 [−0.081, +0.043], p = 0.719 | not supported |
| Robustness, 20 % | Δ +0.031 [−0.027, +0.096], p = 0.155 | not supported |
| Robustness, 30 % | Δ +0.061 [+0.005, +0.120], p = 0.019; answerable +0.059 [−0.004, +0.126], p = 0.036 | overall significant (95 % CI above 0); does not survive Bonferroni over 6 tests (p < 0.004) |

Tables and figures, rebuilt from the files above (no API calls):
```
python scripts/make_tables.py    # results/main_table, ablation_table (+ ablation_pairs.csv), robustness_table, dev_table (.md + .csv)
python scripts/make_figures.py   # paper/figures/lambda_sweep_dev, robustness_test, per_type_test (.png 300 dpi + .pdf + .csv)
python scripts/make_diagrams.py  # paper/figures/architecture, workflow (.png 300 dpi + .pdf)
python scripts/make_review2_deck.py  # thesis/ppt-slides/Review-2.pptx from Review-2_template.pptx (numbers read from results_test*/ and results_dev/)
```


Exploratory per-question analysis (not pre-registered; used in the paper's Section 5.5):
```
python scripts/seed_analysis.py   # results/seed_analysis.md
```
On the 116 answerable test questions, B1 changes the retrieved context on 110. It is better than TG-RAG on 35, worse on 28 and tied on 53 (net +1.63 Correct points summed). TG-RAG had zero seed facts on 2 questions, where B1 scored 0.458 vs 0.000.

## 4. Hand checks: `docs/hand_checks/`
| Result | Command |
|---|---|
| 8,408 stored facts; 832 (9.9 %) with a timestamp outside YYYY / YYYY-QN / YYYY-MM / YYYY-MM-DD, 223 distinct strings | `python scripts/make_hand_checks.py facts` |
| 100 facts to check by hand (`fact_dates_100.csv`) | same command |
| 50 judged answers, blind sheet + key (`judge_check_50.csv`) | `python scripts/make_hand_checks.py answers` |
| Judge-vs-owner agreement, share of correct dates | `python scripts/score_hand_checks.py answers` / `facts`. **Pending: the owner fills the sheets** |

(The graph_stats count, 824 / 8,476, counts relation records. The hand-check count, 832 / 8,408, counts (entity pair, timestamp) facts with a description. They are different units, so both are reported.)

## 5. Cost
| Item | USD |
|---|---|
| Spent before 18 Nov 2026 (owner's figure: graph build, dev runs) | about 1.6 |
| Dev judging (audit) and PoC demo | about 0.03 |
| Test suite: 13 runs + judging (planned estimate; the exact figure is on the OpenRouter activity page) | about 4.5–5.5 |
