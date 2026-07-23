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

print(json.dumps(results, indent=2))
