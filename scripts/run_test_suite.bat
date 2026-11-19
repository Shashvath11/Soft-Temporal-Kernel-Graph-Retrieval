@echo off
REM Final test-set runs (152 questions). Settings were fixed on the dev set: lambda = 1, kappa_min = 0.05.
REM Safe to stop and start again: finished questions are skipped.
REM Run from C:\Research\Temporal-GraphRAG with the tgrag environment active:  scripts\run_test_suite.bat
set Q=ect-qa/subset/test.jsonl
set G=graph_subset
set R=python scripts/run_ectqa.py --working_dir %G% --questions %Q%

echo ===== 1/3 Main runs =====
%R% --variant tgrag --out runs/test_tgrag.jsonl
%R% --variant naive --out runs/test_naive.jsonl
%R% --variant B1 --lam 1 --out runs/test_B1_lam1.jsonl
%R% --variant B12 --lam 1 --out runs/test_B12_lam1.jsonl
%R% --variant B1QI --lam 1 --alpha 1 --out runs/test_B1QI_lam1_alpha1.jsonl
%R% --variant C --out runs/test_C.jsonl
%R% --variant BC --lam 1 --out runs/test_BC_lam1.jsonl

echo ===== 2/3 Noisy-date runs (novelty 3) =====
for %%N in (0.1 0.2 0.3) do (
  %R% --variant tgrag --noise %%N --out runs/test_tgrag_noise%%N.jsonl
  %R% --variant B1 --lam 1 --noise %%N --out runs/test_B1_lam1_noise%%N.jsonl
)

echo ===== 3/3 Scoring and tables =====
python scripts/judge.py runs/test_*.jsonl
python scripts/analyze.py runs/test_tgrag.judged.jsonl runs/test_naive.judged.jsonl runs/test_B1_lam1.judged.jsonl runs/test_B12_lam1.judged.jsonl runs/test_B1QI_lam1_alpha1.judged.jsonl runs/test_C.judged.jsonl runs/test_BC_lam1.judged.jsonl --reference tgrag --out results_test > results_test_main.md
for %%N in (0.1 0.2 0.3) do (
  python scripts/analyze.py runs/test_tgrag_noise%%N.judged.jsonl runs/test_B1_lam1_noise%%N.judged.jsonl --reference tgrag_noise%%N --out results_test_noise%%N > results_test_noise%%N.md
)
echo.
echo Done. Send Claude these 4 files: results_test_main.md, results_test_noise0.1.md, results_test_noise0.2.md, results_test_noise0.3.md
