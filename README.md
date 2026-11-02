# Issue Dedup RAG

## 1. What is it?

When any issue is issued, it can be duplicated of any other issue. This system finds likely duplicate issues for a new GitHub issue.

## 2. Data

For now, I am using issues from the `microsoft/vscode` repository. The data starts from January 1, 2024, and the current file has 89,030 issues.

## 3. Answer key

I am going to find the original issue by reading duplicate comments, such as “duplicate of #number”, and matching that issue number. The pair count and the 30-pair manual error rate are not done yet.

## 4. Split

The pool, dev, and test issues are separated by date so that newer issues do not leak into the older issue search. I am going to use the dev issues for decisions and the test issues only for the final evaluation.

## 5. Methods

- **BM25:** Finds issues with similar words and keywords.
- **Dense embeddings:** Embeds issues in FAISS so issues with similar meaning can be found.
- **Hybrid RRF:** Combines the BM25 and dense search rankings using Reciprocal Rank Fusion.

## 6. Results

The evaluation is not done yet.

| Method | Recall@1 | Recall@5 | Recall@10 | MRR | Test queries |
|---|---:|---:|---:|---:|---:|
| BM25 | Not measured | Not measured | Not measured | Not measured | Not measured |
| Dense embeddings | Not measured | Not measured | Not measured | Not measured | Not measured |
| Hybrid RRF | Not measured | Not measured | Not measured | Not measured | Not measured |

## 7. Limits

The labels and issue text can be noisy, and this project uses only one repository. The answer key and evaluation are also still being made.

## 8. How to run it

```bash
git clone https://github.com/MohitSingh-2335/issue_dedup_rag.git
cd issue_dedup_rag
python -m venv .venv
source .venv/bin/activate && pip install -r requirements.txt
python scripts/fetch_issues.py
```
