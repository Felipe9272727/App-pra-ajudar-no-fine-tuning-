"""Pure checkpoint validation for independent evaluation shards."""
def merge_shards(parts,expected_ids):
    if not parts:raise ValueError('Missing shards')
    reference=parts[0]
    fields=['variant','data_sha256','patch_sha256','frozen_selection_sha256',
            'inference_code_sha256','protocol','loaded_parameters','shards']
    if any(any(k not in p for k in fields) for p in parts):raise ValueError('Missing evaluation metadata')
    if len(parts)!=reference['shards']:raise ValueError('Incomplete shard count')
    if {p['shard'] for p in parts}!=set(range(reference['shards'])):raise ValueError('Duplicate/missing shard')
    seen={}
    for p in parts:
        if p['status']!='complete':raise ValueError('Incomplete shard')
        if any(p.get(k)!=reference.get(k) for k in fields):raise ValueError('Incompatible evaluation metadata')
        for row in p['rows']:
            if row['id'] in seen:raise ValueError('Repeated test question')
            seen[row['id']]=row
    if set(seen)!=set(expected_ids):raise ValueError('Test partition mismatch')
    merged={k:v for k,v in reference.items() if k not in ['shard','rows','correct','total']}
    merged['rows']=[seen[key] for key in expected_ids]
    merged.update(status='complete',exact_correct=sum(r['exact_correct'] for r in merged['rows']),
        content_correct=sum(r['content_correct'] for r in merged['rows']),total=len(expected_ids),
        peak_rss_mib=max(p['peak_rss_mib'] for p in parts))
    return merged
