# TG-RAG vs B1 (λ = 1) on the 116 answerable test questions (exploratory)

Command: `python scripts/seed_analysis.py` (reads runs/test_tgrag.judged.jsonl and runs/test_B1_lam1.judged.jsonl)

- Zero seed facts: TG-RAG 2, B1 0
- On the 2 questions where TG-RAG had zero seeds, B1 found seeds for 2; mean Correct TG-RAG 0.000 vs B1 0.458
- Per question: B1 better on 35, worse on 28, tied on 53 (sum of gains +12.90, sum of losses -11.27, net +1.63 of 116 questions)
- Identical retrieved context (same chunks, same order): 6 of 116 questions

| Question type | n | TG-RAG zero seeds | B1 better | B1 worse | tied | net Δ (sum) |
|---|---|---|---|---|---|---|
| multi-time query | 50 | 1 | 18 | 7 | 25 | +4.58 |
| single-time query|multi-keywords | 30 | 1 | 12 | 6 | 12 | +2.15 |
| single-time query|multi-companies | 22 | 0 | 3 | 13 | 6 | -4.97 |
| relative-time query | 14 | 0 | 2 | 2 | 10 | -0.13 |
