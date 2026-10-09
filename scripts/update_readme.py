"""Refresh the featured-repos and recent-commits blocks in README.md (public data only)."""
import json, os, re, urllib.request

USER = os.environ.get("GH_USER", "Nisith-Akain")
TOKEN = os.environ.get("GITHUB_TOKEN")
THEME = "hide_border=true&bg_color=0d1117&title_color=22d3ee&text_color=c9d1d9&icon_color=22d3ee"


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}", headers={"Accept": "application/vnd.github+json"})
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def repos_block():
    repos = api(f"/users/{USER}/repos?type=owner&sort=pushed&direction=desc&per_page=50")
    repos = [r for r in repos if not r["private"] and not r["fork"] and not r["archived"]
             and r["name"].lower() != USER.lower()][:4]
    cell = lambda r: (
        f'    <td align="center" width="50%">\n'
        f'      <a href="{r["html_url"]}">\n'
        f'        <img width="100%" alt="{r["name"]}" src="https://github-readme-stats.vercel.app/api/pin/?username={USER}&repo={r["name"]}&{THEME}">\n'
        f'      </a>\n    </td>')
    rows = []
    for i in range(0, len(repos), 2):
        rows.append("  <tr>\n" + "\n".join(cell(r) for r in repos[i:i + 2]) + "\n  </tr>")
    return "<table>\n" + "\n".join(rows) + "\n</table>"


def commits_block():
    repos = api(f"/users/{USER}/repos?type=owner&sort=pushed&direction=desc&per_page=10")
    found = []
    for r in repos:
        if r["private"] or r["fork"]:
            continue
        for c in api(f"/repos/{r['full_name']}/commits?author={USER}&per_page=5"):
            found.append((c["commit"]["author"]["date"], r["name"], r["full_name"], c))
    found.sort(key=lambda x: x[0], reverse=True)
    out = []
    for date, name, full, c in found[:5]:
        msg = c["commit"]["message"].splitlines()[0][:70].replace("<", "&lt;")
        out.append(f'<code>{date[:10]}</code> &nbsp; <a href="{c["html_url"]}">{msg}</a> &nbsp;<sub>{name}</sub><br>')
    return chr(10).join(out) or "<sub>No recent public commits.</sub>"


def swap(text, tag, body):
    pat = re.compile(rf"(<!-- {tag}:START -->).*?(<!-- {tag}:END -->)", re.S)
    return pat.sub(lambda m: f"{m.group(1)}\n{body}\n{m.group(2)}", text)


text = open("README.md", encoding="utf-8").read()
text = swap(text, "REPOS", repos_block())
text = swap(text, "COMMITS", commits_block())
open("README.md", "w", encoding="utf-8", newline="\n").write(text)
