from types import SimpleNamespace

from langchain_core.messages import HumanMessage

from app.backend.answer_generation import generate


def response(text, finish='stop', tokens=10):
    return SimpleNamespace(content=text, usage_metadata={'input_tokens': 100, 'output_tokens': tokens},
        response_metadata={'finish_reason': finish, 'token_usage': {'cost': .01}})


class Model:
    def __init__(self, *responses):
        self.responses = iter(responses)
        self.calls, self.options = [], []

    def bind(self, **options):
        self.options.append(options)
        return self

    def invoke(self, messages):
        self.calls.append(messages)
        result = next(self.responses)
        if isinstance(result, Exception):
            raise result
        return result


def test_truncation_regenerates_once_and_counts_both_requests():
    llm = Model(response('Harga mulai Rp', 'length', 2048), response('Totalnya Rp 100.000.'))
    messages = [HumanMessage(content='Berapa harganya?')]
    result = generate(llm, messages)
    assert result['answer'] == 'Totalnya Rp 100.000.'
    assert result['usage']['requests'] == 2
    assert result['usage']['completion_tokens'] == 2058
    assert result['usage']['cost_usd'] == .02
    assert len(llm.calls) == 2 and 'Harga mulai Rp' not in str(llm.calls[1])
    assert messages == [HumanMessage(content='Berapa harganya?')]


def test_empty_reasoning_only_response_is_recoverable():
    result = generate(Model(response('', 'length'), response('Linen bertekstur kain.')), [])
    assert result['answer'] == 'Linen bertekstur kain.'


def test_exhausted_budget_or_second_truncation_never_publishes_a_fragment():
    for available in (True, False):
        llm = Model(response('Harga mulai Rp', 'length'), response('Harga Rp', 'length'))
        result = generate(llm, [], recovery_available=available)
        assert 'Harga mulai Rp' not in result['answer']
        assert result['recovery'] == 'incomplete'
        assert len(llm.calls) == (2 if available else 1)


def test_recovery_failure_is_bounded_and_retains_usage():
    llm = Model(response('Terpotong', 'length'), TimeoutError())
    result = generate(llm, [])
    assert result['recovery'] == 'failed'
    assert result['usage']['requests'] == 2
    assert result['usage']['completion_tokens'] == 10
