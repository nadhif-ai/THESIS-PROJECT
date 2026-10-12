---
status: accepted
date: 2026-10-12
---

# Use LangSmith for traces and evaluation reports

The user selected LangSmith as the shared destination for chatbot traces and evaluation results, using the `chatbot-avg` project. DeepEval will calculate quality metrics, and the application will attach those scores and explanations to LangSmith evaluation runs. This keeps the selected metric framework while placing operational traces and experiment comparisons in the user's preferred service.

Confident AI was considered as DeepEval's native hosted reporting option. LangSmith was chosen to simplify use of the existing LangChain pipeline and the user's configured account. It introduces a small integration layer that maps DeepEval results to LangSmith feedback. Local evaluation artifacts remain available for thesis reproducibility and for recovering from reporting failures.
