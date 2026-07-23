#!/usr/bin/env python3
import urllib.request, urllib.parse, json, time

queries = [
    '"agent orchestration" python framework stars:>800',
    '"multi-agent" open source stars:>1000',
    'microsoft agent-framework stars:>1000',
    'haystack RAG agents stars:>1000',
    'llama.cpp stars:>10000',
    '"local LLM" inference serving stars:>800',
    '"retrieval augmented generation" framework stars:>1000',
    'cognita RAG stars:>1000',
    '"vector database" open source stars:>2000',
    '"browser automation" playwright alternative stars:>1000',
    '"AI security" assessment stars:>1000',
    '"agent governance" open source stars:>500',
    'AutoRAG stars:>1000',
]

headers = [
    'Accept: application/vnd.github+json',
    'User-Agent: Hermes-Research/1.0',
    'X-GitHub-Api-Version: 2022-11-28',
]

results = []
for i, q in enumerate(queries):
    encoded = urllib.parse.quote(q, safe='')
    url = f'https://api.github.com/search/repositories?q={encoded}&sort=stars&per_page=5'
    if i > 0:
        time.sleep(2.5)
    req = urllib.request.Request(url)
    for h in headers:
        k, v = h.split(': ', 1)
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        results.append({'query': q, 'error': str(e)})
        continue
    for it in data.get('items', []):
        results.append({
            'query': q,
            'full_name': it.get('full_name'),
            'stars': it.get('stargazers_count'),
            'forks': it.get('forks_count'),
            'open_issues': it.get('open_issues_count'),
            'language': it.get('language'),
            'license': ((it.get('license') or {}) or {}).get('spdx_id', ''),
            'updated_at': it.get('updated_at'),
            'pushed_at': it.get('pushed_at'),
            'description': (it.get('description') or '')[:120],
            'archived': int(it.get('archived', 0)),
        })

print(json.dumps(results, indent=2))
