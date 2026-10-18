"""Bound complete user/assistant pairs without cutting order specifications mid-answer."""

from langchain_core.messages import AIMessage, HumanMessage

MAX_HISTORY_PAIRS = 8
HISTORY_TOKEN_BUDGET = 8000


def bounded_history(turns):
    messages, used = [], 0
    for question, answer in reversed(list(turns)[-MAX_HISTORY_PAIRS:]):
        if not question or not answer:
            continue
        # UTF-8 bytes conservatively bound text tokens across the configured providers.
        cost = len(question.encode("utf-8")) + len(answer.encode("utf-8")) + 64
        if used + cost > HISTORY_TOKEN_BUDGET:
            break
        messages[0:0] = [HumanMessage(content=question), AIMessage(content=answer)]
        used += cost
    return messages


def retrieval_question(question, history):
    # Short replies often supply just a material or quantity; retrieve the original product too.
    if len(question) > 160 or not history:
        return question
    previous, used = [], 0
    for message in reversed(history):
        if message.type != "human":
            continue
        cost = len(message.content.encode("utf-8"))
        if used + cost > 1200 or len(previous) == 3:
            break
        previous.insert(0, message.content)
        used += cost
    return question + ("\nKonteks pelanggan sebelumnya:\n" + "\n".join(previous) if previous else "")
