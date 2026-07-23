import urllib.request, urllib.parse, json, time, os

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "Hermes-Research/1.0",
    "X-GitHub-Api-Version": "2022-11-28",
}

QUERIES = [
    '"agent orchestration" python framework stars:>800',
    '"local LLM" inference serving stars:>800',
    '"retrieval augmented generation" framework stars:>1000',
    '"vector database" open source stars:>2000',
    '"multi-agent" open source stars:>1000',
    '"GGUF" inference stars:>500',
    '"AI security" assessment stars:>1000',
    '"self-hosted" AI assistant windows stars:>500',
    'microsoft agent-framework stars:>1000',
    '"RAG" agents stars:>1000',
]

out = {}
for q in QUERIES:
    url = "https://api.github.com/search/repositories?q=" + urllib.parse.quote(q, safe='') + "&sort=stars&order=desc&per_page=5"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode())
            items = []
            for item in data.get("items", []):
                items.append({
                    "full_name": item.get("full_name"),
                    "description": item.get("description"),
                    "stars": item.get("stargazers_count"),
                    "forks": item.get("forks_count"),
                    "open_issues": item.get("open_issues_count"),
                    "updated": item.get("updated_at"),
                    "pushed": item.get("pushed_at"),
                    "license": item.get("license", {}).get("spdx_id") if item.get("license") else None,
                    "language": item.get("language"),
                    "archived": item.get("archived"),
                    "url": item.get("html_url"),
                })
            out[q] = {"total": data.get("total_count", 0), "items": items}
    except Exception as e:
        out[q] = {"error": str(e)}
    time.sleep(2)

print(json.dumps(out, indent=2))
