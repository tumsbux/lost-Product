"""push_lost_product_files.py
Push arbitrary files from F:\\lost-Product\\ to tumsbux/lost-Product via GitHub Contents API.

Usage:
  py push_lost_product_files.py file1 file2 ... [-m "commit message"]

Reads github_token from db_config.json (same lookup as other scripts).
Always pushes to tumsbux/lost-Product repo (not daily-report).
"""

import sys, os, json, base64, argparse
from pathlib import Path
import urllib.request, urllib.error

REPO   = 'tumsbux/lost-Product'
BRANCH = 'main'
API    = 'https://api.github.com'

DB_PATHS = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db_config.json'),
    r'F:\co work dashboard\db_config.json',
]

def load_token():
    for p in DB_PATHS:
        if os.path.exists(p):
            return json.load(open(p, encoding='utf-8'))['github_token']
    raise FileNotFoundError('db_config.json not found')

def api(token, method, path, body=None):
    url = f'{API}{path}'
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json',
        'User-Agent': 'push-lost-product',
    })
    try:
        with urllib.request.urlopen(req) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f'GitHub API {method} {path} -> {e.code}: {e.read().decode()}')

def get_sha(token, filepath_in_repo):
    """Get current SHA of file in repo (needed for update). Returns None if new."""
    try:
        r = api(token, 'GET', f'/repos/{REPO}/contents/{filepath_in_repo}?ref={BRANCH}')
        return r['sha']
    except RuntimeError:
        return None

def push_file(token, local_path, repo_path, message):
    content = Path(local_path).read_bytes()
    b64 = base64.b64encode(content).decode()
    sha = get_sha(token, repo_path)
    body = {'message': message, 'content': b64, 'branch': BRANCH}
    if sha:
        body['sha'] = sha
    r = api(token, 'PUT', f'/repos/{REPO}/contents/{repo_path}', body)
    return r['commit']['sha']

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('files', nargs='+')
    ap.add_argument('-m', '--message', default='chore: update lost-Product files')
    ap.add_argument('-r', '--repo-path', default=None,
                    help='Override repo path for single-file push (e.g. .github/workflows/foo.yml)')
    args = ap.parse_args()

    token = load_token()
    script_dir = Path(os.path.dirname(os.path.abspath(__file__)))

    if args.repo_path and len(args.files) > 1:
        print('ERROR: --repo-path can only be used with a single file'); sys.exit(1)

    for f in args.files:
        p = Path(f)
        if not p.is_absolute():
            p = script_dir / p
        if not p.exists():
            print(f'  SKIP (not found): {f}')
            continue
        repo_path = args.repo_path if args.repo_path else p.name
        print(f'  Uploading {repo_path} ({p.stat().st_size // 1024} KB)...', end=' ')
        sha = push_file(token, p, repo_path, args.message)
        print(f'OK  (commit {sha[:8]})')

    print('Done!')

if __name__ == '__main__':
    main()
