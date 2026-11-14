"""Before learning, retain full tool evidence but teach its concise relevant view."""
import copy, hashlib, json
from pathlib import Path
H=Path(__file__).resolve().parent


def main():
    path=H/'data/train_tools.json';raw=path.read_bytes()
    archive=H/'data/train_tools_full_context.json';assert not archive.exists()
    archive.write_bytes(raw);rows=json.loads(raw)
    for row in rows:
        if row['id']=='N028U/repaired_final':
            # Successful final observation suffices; the separate repair example
            # still contains the original failed call and real error.
            row['messages']=row['messages'][:2]+row['messages'][-2:]
        for message in row['messages']:
            if message['role']!='tool':continue
            original=json.loads(message['content'])
            message['content']=json.dumps({k:original[k] for k in ['tool','ok','stdout','error'] if k in original})
    assert [(r['id'],r['solution'],r['plan']) for r in rows]==[(r['id'],r['solution'],r['plan']) for r in json.loads(raw)]
    path.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    report={'before_any_optimizer_updates':True,'teacher_targets_and_gold_cases_changed':False,
        'full_original_tool_context_retained':str(archive),
        'full_context_sha256':hashlib.sha256(raw).hexdigest(),
        'original_long_context_backward_preflight_already_passed':True,
        'reason':'Reduce activation memory by omitting runtime metadata and obsolete failed round from successful-final teaching; retain real error in the repair example and all raw observations.',
        'replayed_model_or_teacher_collection':False}
    (H/'reports/context_projection.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
