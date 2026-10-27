"""Explicit, resumable research runs through the shared pipeline and four metrics.

Usage: venv/bin/python -m testing.evals.precision_study manifest.json output-dir
The manifest captures model/prompt/snapshot and source-validated held-out questions.
This is a paid evaluation operation, never imported by the offline pytest suite.
"""
import hashlib
import json
import sys
import time
from types import SimpleNamespace
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from deepeval.test_case import LLMTestCase
from langsmith import trace

from app.admin import store
from app.dependencies import initialize_rag_system, get_rag_chain
from testing.evals.metrics import single_turn_metrics, judge_settings, STEP_DEADLINE
from testing.evals.runner import _metric_results


def run_case(manifest, phase, row, folder):
    path = folder / f"{phase['name']}-{row['id']}.json"
    fingerprint = hashlib.sha256(json.dumps([manifest, phase, row], sort_keys=True).encode()).hexdigest()
    if path.exists():
        saved = json.loads(path.read_text())
        if saved.get('fingerprint') != fingerprint:
            raise ValueError('Existing case belongs to a different frozen experiment.')
        return saved
    config = manifest['configuration']
    with trace('precision-study-case', inputs={'case_id': row['id'], 'question': row['input']},
               metadata={'study': manifest['name'], 'phase': phase['name'], 'knowledge_version': phase['knowledge_version']}) as parent:
        if phase.get('reuse_saved_answers'):
            saved = row['baseline_record']
            response = SimpleNamespace(answer=saved['answer'], error=saved.get('error'),
                retrieval_context=saved['retrieval_context'], usage=saved.get('usage', {}))
        else:
            response = get_rag_chain().run(question=row['input'],
                session_id=f"study-{fingerprint[:24]}", channel='evaluation',
                namespace=phase['namespace'], model=config['model'], top_k=config['top_k'],
                model_provider=config.get('model_provider', 'openrouter'),
                intent_model=config['intent_model'], prompt_config=config['prompt_snapshot'], history_turns=[])
        result = {'fingerprint': fingerprint, 'id': row['id'], 'phase': phase,
                  'input': row['input'], 'expected_output': row['expected_output'],
                  'answer': response.answer, 'error': response.error,
                  'retrieval_context': response.retrieval_context,
                  'usage': response.usage, 'metrics': [], 'trace_url': parent.get_url(),
                  'judge_settings': judge_settings(config['judge'])}
        retained = {}
        if phase.get('reuse_retrieval_metrics_from'):
            source = json.loads((Path(phase['reuse_retrieval_metrics_from']) /
                                f"{phase['reuse_phase_name']}-{row['id']}.json").read_text())
            if (source['input'] == row['input'] and source['expected_output'] == row['expected_output']
                    and [p['text'] for p in source['retrieval_context']] == [p['text'] for p in response.retrieval_context]):
                retained = {m['name']: {**m, 'retained_from': source['trace_url']}
                            for m in source['metrics'] if m['name'] in ('Contextual Recall', 'Contextual Precision')
                            and m.get('score') is not None and not m.get('error')}
        if not response.error:
            case = LLMTestCase(input=row['input'], actual_output=response.answer,
                expected_output=row['expected_output'],
                retrieval_context=[p['text'] for p in response.retrieval_context])
            for metric in single_turn_metrics(judge_model=config['judge']):
                if metric.__name__ in retained:
                    result['metrics'].append(retained[metric.__name__])
                    continue
                token = STEP_DEADLINE.set(time.monotonic() + 180)
                try:
                    result['metrics'].extend(_metric_results(case, [metric]))
                finally:
                    STEP_DEADLINE.reset(token)
        parent.end(outputs={'scores': {m['name']:m.get('score') for m in result['metrics']},
                            'scoring_errors':sum(bool(m.get('error')) for m in result['metrics'])})
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(phase['name'], row['id'], [(m['name'],m.get('score'),m.get('error')) for m in result['metrics']], flush=True)
    return result


def main():
    manifest = json.loads(Path(sys.argv[1]).read_text())
    folder = Path(sys.argv[2]);folder.mkdir(parents=True, exist_ok=True)
    initialize_rag_system()
    jobs = [(phase, row) for phase in manifest['phases'] for row in manifest['cases']]
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(run_case, manifest, phase, row, folder) for phase,row in jobs]
        results = [future.result() for future in futures]
    (folder/'results.json').write_text(json.dumps(results, indent=2, ensure_ascii=False))
    store.close_pool()


if __name__ == '__main__':
    main()
