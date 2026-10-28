"""One bounded recovery for incomplete answer text, with cumulative usage."""

import logging
import time

from langchain_core.messages import SystemMessage
from langsmith import traceable

logger = logging.getLogger(__name__)
INCOMPLETE = 'Maaf, Kak, jawaban lengkapnya belum berhasil disiapkan. Silakan coba pertanyaannya lagi atau konfirmasi ke admin toko.'


@traceable(name='answer-generation', process_inputs=lambda inputs: {
    'messages': inputs.get('messages'), 'recovery_available': inputs.get('recovery_available', True),
})
def generate(llm, messages, *, recovery_available=True):
    from app.integrations.waha import plain_text

    usage = {'prompt_tokens': 0, 'completion_tokens': 0, 'requests': 0, 'cost_usd': None}
    deadline = time.monotonic() + 65
    recovery, finish_reason = 'not_needed', None
    for attempt in range(2 if recovery_available else 1):
        usage['requests'] += 1
        try:
            if attempt:
                remaining = min(20, deadline - time.monotonic())
                if remaining <= 0:
                    raise TimeoutError('Answer recovery deadline expired')
                retry_messages = [*messages[:-1], SystemMessage(content=(
                    'Buat ulang jawaban lengkap dan ringkas dari KONTEKS KNOWLEDGE. '
                    'Jawab setiap bagian pertanyaan yang didukung bukti. Jika satu detail pesanan '
                    'belum jelas, tanyakan satu klarifikasi. Jangan melanjutkan fragmen jawaban sebelumnya.'
                )), *messages[-1:]]
                response = llm.bind(max_tokens=8192, timeout=remaining).invoke(retry_messages)
            else:
                response = llm.invoke(messages)
        except Exception as error:
            if not attempt:
                raise
            logger.warning('Answer recovery failed error_type=%s', type(error).__name__)
            return {'answer': INCOMPLETE, 'usage': usage, 'finish_reason': finish_reason, 'recovery': 'failed'}
        metadata = getattr(response, 'response_metadata', {}) or {}
        reported = metadata.get('token_usage') or {}
        tokens = getattr(response, 'usage_metadata', None) or {}
        usage['prompt_tokens'] += tokens.get('input_tokens', reported.get('prompt_tokens', 0))
        usage['completion_tokens'] += tokens.get('output_tokens', reported.get('completion_tokens', 0))
        if isinstance(reported.get('cost'), (int, float)):
            usage['cost_usd'] = (usage['cost_usd'] or 0) + reported['cost']
        finish_reason = metadata.get('finish_reason')
        content = getattr(response, 'content', '')
        answer = plain_text(content) if isinstance(content, str) else ''
        if answer.strip() and finish_reason != 'length':
            return {'answer': answer, 'usage': usage, 'finish_reason': finish_reason,
                    'recovery': 'regenerated' if attempt else recovery}
        recovery = 'incomplete'
    return {'answer': INCOMPLETE, 'usage': usage, 'finish_reason': finish_reason, 'recovery': recovery}
