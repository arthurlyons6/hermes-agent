import urllib.request, json, time, sys

headers = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "Hermes-Research/1.0",
    "X-GitHub-Api-Version": "2022-11-28",
}

queries = sys.argv[1:]
results = {}

for q in queries:
    url = "https://api.github.com/search/repositories?q=" + urllib.parse.quote(q, safe='') + "&sort=stars&order=desc&per_page=5"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            results[q] = data.get("items", [])
    except urllib.error.HTTPError as e:
        results[q] = {"error": str(e.code), "msg": str(e)}
    time.sleep(2)

# Compact output: full_name, stars, language, license, pushed_at, open_issues
out = {}
for q, items in results.items():
    out[q] = []
    for repo in items:
        if "full_name" not in repo:
            out[q].append(repo)
            continue
        lic = repo.get("license", {}).get("spdx_id", "none")
        out[q].append({
            "name": repo["full_name"],
            "stars": repo["stargazers_count"],
            "lang": repo.get("language"),
            "license": lic,
            "pushed_at": repo.get("pushed_at"),
            "updated_at": repo.get("updated_at"),
            "open_issues": repo.get("open_issues_count", 0),
            "description": repo.get("description", "")[:120],
        })

print(json.dumps(out, indent=2))
