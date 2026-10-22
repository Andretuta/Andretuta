"""Card de contribuições em pixel art, no estilo do banner. Gera assets/stats.svg.

Uso: GH_TOKEN=... python tools/stats.py [usuario]   (ou --from arquivo.json com a resposta da GraphQL)
Sem dependências: só a biblioteca padrão.
"""
import json, os, sys, urllib.request

USER = next((a for a in sys.argv[1:] if not a.startswith('--') and not a.endswith('.json')), 'Andretuta')
OUT = os.path.join(os.path.dirname(__file__), '..', 'assets', 'stats.svg')
QUERY = ('query($u:String!){user(login:$u){contributionsCollection{totalCommitContributions '
         'totalPullRequestContributions contributionCalendar{totalContributions weeks{contributionDays{contributionCount}}}}}}')

def fetch():
    if '--from' in sys.argv:
        return json.load(open(sys.argv[sys.argv.index('--from') + 1], encoding='utf-8'))
    req = urllib.request.Request('https://api.github.com/graphql', method='POST',
                                 data=json.dumps({'query': QUERY, 'variables': {'u': USER}}).encode(),
                                 headers={'Authorization': 'bearer ' + os.environ['GH_TOKEN'], 'User-Agent': 'stats-card'})
    return json.load(urllib.request.urlopen(req, timeout=30))

c = fetch()['data']['user']['contributionsCollection']
cal = c['contributionCalendar']
weeks = [sum(d['contributionCount'] for d in w['contributionDays']) for w in cal['weeks']][-26:]
stats = [(cal['totalContributions'], 'CONTRIBUIÇÕES', '#fbbbad'),
         (c['totalCommitContributions'], 'COMMITS', '#ee8695'),
         (c['totalPullRequestContributions'], 'PULL REQUESTS', '#9ff0e0')]

# fonte pixel 3x5 (M e N mais largos); linhas negativas/extras são acentos
F = {
    '0': '111 101 101 101 111', '1': '010 110 010 010 111', '2': '111 001 111 100 111', '3': '111 001 011 001 111',
    '4': '101 101 111 001 001', '5': '111 100 111 001 111', '6': '111 100 111 101 111', '7': '111 001 010 010 010',
    '8': '111 101 111 101 111', '9': '111 101 111 001 111', '.': '0 0 0 0 1', ' ': '00 00 00 00 00',
    'A': '010 101 111 101 101', 'B': '110 101 110 101 110', 'C': '011 100 100 100 011', 'E': '111 100 110 100 111',
    'I': '111 010 010 010 111', 'L': '100 100 100 100 111', 'M': '10001 11011 10101 10001 10001',
    'N': '1001 1101 1011 1001 1001', 'O': '010 101 101 101 010', 'P': '110 101 110 100 100', 'Q': '010 101 101 110 011',
    'R': '110 101 110 101 101', 'S': '011 100 010 001 110', 'T': '111 010 010 010 010', 'U': '101 101 101 101 111',
    'F': '111 100 110 100 100', 'H': '101 101 111 101 101', 'Y': '101 101 010 010 010', 'G': '011 100 101 101 011',
    '/': '001 001 010 100 100', '_': '000 000 000 000 111', '>': '100 110 111 110 100',
}
TIL = [(0, -1), (1, -2), (2, -1)]
ACC = {'Ç': ('C', [(1, 5)]), 'Õ': ('O', TIL), 'Ã': ('A', TIL), 'Ú': ('U', [(1, -1), (2, -2)])}

def glyph_px(ch):
    base, extra = ACC.get(ch, (ch, []))
    rows = F[base].split()
    pts = [(i, j) for j, r in enumerate(rows) for i, b in enumerate(r) if b == '1']
    return pts + extra, len(rows[0])

def text(s, x0, y0, color, scale=1):
    out, x = [], x0
    for ch in s:
        pts, w = glyph_px(ch)
        out += [f'<rect x="{x + i * scale}" y="{y0 + j * scale}" width="{scale}" height="{scale}" fill="{color}"/>' for i, j in pts]
        x += (w + 1) * scale
    return out, x - x0 - scale

def num(n):
    return f'{n:,}'.replace(',', '.')

BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
RAMP = ['#4a7a96', '#7f7395', '#c9809a', '#ee8695', '#fbbbad']
def ramp(v, x, y):
    v = max(0.0, min(len(RAMP) - 1.0, v)); b = int(v)
    return RAMP[min(b + (1 if v - b > (BAYER[y % 4][x % 4] + .5) / 16 else 0), len(RAMP) - 1)]

W, H = 200, 44
o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="1000" height="{H * 5}" shape-rendering="crispEdges" role="img" '
     f'aria-label="{num(stats[0][0])} contribuições no último ano, {stats[1][0]} commits, {stats[2][0]} pull requests; gráfico das últimas 26 semanas">',
     f'<rect width="{W}" height="{H}" fill="#1c1b26"/>',
     f'<rect x="0" y="0" width="{W}" height="1" fill="#2a2d3a"/><rect x="0" y="{H - 1}" width="{W}" height="1" fill="#2a2d3a"/>',
     f'<rect x="0" y="0" width="1" height="{H}" fill="#2a2d3a"/><rect x="{W - 1}" y="0" width="1" height="{H}" fill="#2a2d3a"/>']

# números à esquerda
for k, (n, label, color) in enumerate(stats):
    y = 5 + k * 13
    r, w = text(num(n), 8, y, color, scale=2); o += r
    r, _ = text(label, 8 + w + 5, y + 3, '#8f8aa8'); o += r

# gráfico à direita: barras de pixel com degradê lo-fi, revelado de baixo para cima
X0, BASE, TOP, STEP, BAR = 114, 39, 12, 3, 2
r, _ = text('ÚLTIMAS 26 SEMANAS', X0, 4, '#8f8aa8'); o += r
o.append(f'<rect x="{X0 - 2}" y="{BASE + 1}" width="{len(weeks) * STEP + 3}" height="1" fill="#2a2d3a"/>')
o.append(f'<defs><clipPath id="sobe"><rect x="0" y="{BASE + 1}" width="{W}" height="0">'
         f'<animate attributeName="y" from="{BASE + 1}" to="{TOP - 1}" dur="1.2s" fill="freeze"/>'
         f'<animate attributeName="height" from="0" to="{BASE - TOP + 2}" dur="1.2s" fill="freeze"/></rect></clipPath></defs>')
o.append('<g clip-path="url(#sobe)">')
peak = max(weeks) or 1
for i, v in enumerate(weeks):
    x = X0 + i * STEP
    h = round(v / peak * (BASE - TOP + 1))
    if v and h == 0: h = 1
    for j in range(h):
        y = BASE - j
        for dx in range(BAR):
            o.append(f'<rect x="{x + dx}" y="{y}" width="1" height="1" fill="{ramp(j / (BASE - TOP) * (len(RAMP) - 1), x + dx, y)}"/>')
o.append('</g>')
o.append('</svg>')
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, 'w', encoding='utf-8').write('\n'.join(o))
print('stats.svg:', num(stats[0][0]), 'contribuições,', stats[1][0], 'commits,', stats[2][0], 'PRs; pico semanal', peak)

# ---------- cartão "contribuição mais famosa" (assets/fame.svg) ----------
FAME_REPO = 'HayatoG/iss_pc'

def stars():
    if '--stars' in sys.argv:
        return int(sys.argv[sys.argv.index('--stars') + 1])
    h = {'User-Agent': 'stats-card'}
    if os.environ.get('GH_TOKEN'):
        h['Authorization'] = 'bearer ' + os.environ['GH_TOKEN']
    req = urllib.request.Request(f'https://api.github.com/repos/{FAME_REPO}', headers=h)
    return json.load(urllib.request.urlopen(req, timeout=30))['stargazers_count']

STAR = ['0001000', '0001000', '1111111', '0111110', '0011100', '0110110', '0100010']
n_stars = stars()
FW, FH = 200, 30
f = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {FW} {FH}" width="1000" height="{FH * 5}" shape-rendering="crispEdges" role="img" '
     f'aria-label="Contribuição mais famosa: {FAME_REPO}, {num(n_stars)} estrelas">',
     f'<rect width="{FW}" height="{FH}" fill="#1c1b26"/>',
     f'<rect width="{FW}" height="1" fill="#2a2d3a"/><rect y="{FH - 1}" width="{FW}" height="1" fill="#2a2d3a"/>',
     f'<rect width="1" height="{FH}" fill="#2a2d3a"/><rect x="{FW - 1}" width="1" height="{FH}" fill="#2a2d3a"/>']
f += text('CONTRIBUIÇÃO MAIS FAMOSA', 8, 6, '#8f8aa8')[0]
f.append(f'<rect x="8" y="13" width="{FW - 16}" height="1" fill="#2a2d3a"/>')
cursor = text('>', 8, 17, '#ee8695', scale=2)[0]  # cursor de menu de jogo, piscando
f.append('<g>' + ''.join(cursor) + '<animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite" calcMode="discrete"/></g>')
f += text(FAME_REPO.upper(), 18, 17, '#fbbbad', scale=2)[0]
num_w = text(num(n_stars), 0, 0, '#ffe58f', scale=2)[1]
nx = FW - 8 - num_w
f += text(num(n_stars), nx, 17, '#ffe58f', scale=2)[0]
sx = nx - 11
for j, row in enumerate(STAR):
    for i, b in enumerate(row):
        if b == '1':
            f.append(f'<rect x="{sx + i}" y="{18 + j}" width="1" height="1" fill="{"#ffe58f" if j < 4 else "#fab47e"}"/>')
f.append('</svg>')
open(os.path.join(os.path.dirname(OUT), 'fame.svg'), 'w', encoding='utf-8').write('\n'.join(f))
print('fame.svg:', FAME_REPO, num(n_stars), 'estrelas')
