"""Gera o site e o blog da Souvrin em /conteudo/ a partir de _blog/posts/*.md.

Uso (na raiz do repositório):  python3 _blog/build.py
Páginas fixas: _blog/paginas/*.html (cabeçalho titulo/descricao/url) usam o mesmo molde.
Só usa a biblioteca padrão do Python.

Formato do post (_blog/posts/AAAA-MM-DD-slug.md):
---
titulo: Título do artigo (até ~55 caracteres, vira o <title> com " | SOUVRIN")
descricao: Meta description entre 120 e 158 caracteres.
data: 2026-11-20
atualizado: 2026-11-20            (opcional)
categoria: home-equity            (home-equity, consorcio, financiamento, construcao,
                                   capital-de-giro, consorcio-empresarial, imovel-comercial, geral)
formato: artigo                   (artigo ou duvida)
palavra_chave: empréstimo com garantia de imóvel
resumo: Texto curto do card no índice (opcional; usa a descrição se faltar).
rascunho: nao                     (sim = não publica)
---
Corpo em Markdown: ## e ### para títulos, parágrafos, listas (- e 1.), > para destaque,
tabelas com |, **negrito**, *itálico* e [link](/caminho/). Uma seção "## Perguntas frequentes"
com perguntas em ### vira schema FAQPage.
"""
import datetime, html, json, pathlib, re, sys

SITE = 'https://www.souvrin.com.br'
ROOT = pathlib.Path(__file__).resolve().parent.parent
BLOG = ROOT / '_blog'
OUT = ROOT / 'conteudo'
MOLDE = (BLOG / 'molde.html').read_text()
E = lambda s: html.escape(s, quote=True)
MESES = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro',
         'outubro', 'novembro', 'dezembro']

CAT = {
    'home-equity': ('Crédito com garantia de imóvel', 'simulador'),
    'consorcio': ('Consórcio e cartas contempladas', 'simulador'),
    'financiamento': ('Financiamento imobiliário', 'simulador'),
    'construcao': ('Crédito para construção', 'simulador'),
    'capital-de-giro': ('Capital de giro com garantia de imóvel', 'simulador'),
    'consorcio-empresarial': ('Consórcio empresarial', 'simulador'),
    'imovel-comercial': ('Financiamento de imóvel comercial', 'simulador'),
    'geral': ('Crédito em geral', 'simulador'),
}
FORMATO = {'artigo': 'Artigo', 'duvida': 'Dúvida respondida'}

CSS = """
.post{max-width:760px;margin:0 auto}
.post .meta{display:flex;flex-wrap:wrap;gap:8px 16px;margin-top:18px;font-size:14px;color:var(--aco)}
.post .body{margin-top:32px}
.post .body h2{font-size:clamp(24px,2.6vw,32px);margin:44px 0 14px}
.post .body h3{font-size:20px;margin:28px 0 10px}
.post .body p,.post .body li{font-size:17.5px;line-height:1.7}
.post .body ul,.post .body ol{padding-left:22px;margin:0 0 1.2em;color:var(--body)}
.post .body li{margin-bottom:8px;max-width:66ch}
.post .body a{color:var(--cob);font-weight:600}
.post .body strong{color:var(--navy)}
.post .body blockquote{margin:24px 0;padding:18px 22px;background:var(--card);border-left:5px solid var(--cob);border-radius:0 16px 16px 0}
.post .body blockquote p{margin:0}
.post .tbl{overflow-x:auto;margin:20px 0 28px}
.post table{border-collapse:collapse;width:100%;font-size:15.5px;min-width:480px}
.post th,.post td{text-align:left;padding:12px 10px;border-bottom:1px solid var(--line);vertical-align:top;color:var(--body)}
.post th{color:var(--navy);font-weight:700;background:var(--card)}
.post .box{margin-top:44px;background:var(--navy);border-radius:24px;padding:clamp(22px,3vw,34px)}
.post .box h2{color:var(--ala);font-size:26px}.post .box p{color:#C9D1DB;margin-top:10px}
.post .disc{font-size:13.5px;color:var(--aco);margin-top:28px}
.tag{display:inline-block;font-size:12.5px;font-weight:700;padding:4px 10px;border-radius:999px;background:#F3ECDD;color:var(--cob);letter-spacing:.06em}
.card .tag{align-self:flex-start}
.card time{font-size:13.5px;color:var(--aco)}
"""


def fail(msg):
    print('ERRO:', msg)
    sys.exit(1)


def parse(path):
    raw = path.read_text()
    m = re.match(r'---\n(.*?)\n---\n(.*)', raw, re.S)
    if not m:
        fail(f'{path.name}: falta o cabeçalho entre ---')
    meta = {}
    for line in m.group(1).splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            meta[k.strip()] = v.strip()
    for k in ('titulo', 'descricao', 'data', 'categoria'):
        if not meta.get(k):
            fail(f'{path.name}: falta "{k}"')
    if meta['categoria'] not in CAT:
        fail(f'{path.name}: categoria "{meta["categoria"]}" não existe ({", ".join(CAT)})')
    fm = re.match(r'(\d{4}-\d{2}-\d{2})-(.+)\.md$', path.name)
    if not fm:
        fail(f'{path.name}: nome deve ser AAAA-MM-DD-slug.md')
    meta['slug'] = fm.group(2)
    meta['data'] = datetime.date.fromisoformat(meta['data'])
    meta['atualizado'] = datetime.date.fromisoformat(meta['atualizado']) if meta.get('atualizado') else meta['data']
    meta['formato'] = meta.get('formato', 'artigo')
    meta['md'] = m.group(2).strip()
    return meta


def inline(t):
    t = E(t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])', r'<em>\1</em>', t)

    def link(m):
        txt, url = m.group(1), m.group(2)
        ext = url.startswith('http') and not url.startswith(SITE)
        extra = ' target="_blank" rel="noopener"' if ext else ''
        return f'<a href="{url}"{extra}>{txt}</a>'
    return re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', link, t)


def md_to_html(md):
    """Converte o subconjunto de Markdown usado nos posts. Devolve (html, faq)."""
    out, faq = [], []
    blocks = re.split(r'\n\s*\n', md)
    in_faq, cur_q = False, None
    for b in blocks:
        lines = b.strip('\n').split('\n')
        first = lines[0]
        if first.startswith('### '):
            q = first[4:].strip()
            out.append(f'<h3>{inline(q)}</h3>')
            rest = '\n'.join(lines[1:]).strip()
            if in_faq:
                cur_q = [q, '']
                faq.append(cur_q)
            if rest:
                out.append(f'<p>{inline(" ".join(rest.split()))}</p>')
                if cur_q:
                    cur_q[1] += rest + ' '
            continue
        if first.startswith('## '):
            t = first[3:].strip()
            in_faq = t.lower().startswith('perguntas frequentes')
            cur_q = None
            out.append(f'<h2>{inline(t)}</h2>')
            rest = '\n'.join(lines[1:]).strip()
            if rest:
                out.append(f'<p>{inline(" ".join(rest.split()))}</p>')
            continue
        if all(re.match(r'\s*[-*] ', l) for l in lines):
            out.append('<ul>' + ''.join('<li>%s</li>' % inline(re.sub(r'^\s*[-*] ', '', l)) for l in lines) + '</ul>')
        elif all(re.match(r'\s*\d+[.)] ', l) for l in lines):
            out.append('<ol>' + ''.join('<li>%s</li>' % inline(re.sub(r'^\s*\d+[.)] ', '', l)) for l in lines) + '</ol>')
        elif all(l.startswith('>') for l in lines):
            txt = ' '.join(l.lstrip('> ').strip() for l in lines)
            out.append(f'<blockquote><p>{inline(txt)}</p></blockquote>')
        elif all(l.strip().startswith('|') for l in lines) and len(lines) >= 3:
            rows = [[c.strip() for c in l.strip().strip('|').split('|')] for l in lines]
            head, body = rows[0], [r for r in rows[2:]]
            t = '<div class="tbl"><table><thead><tr>' + ''.join(f'<th>{inline(c)}</th>' for c in head) + '</tr></thead><tbody>'
            t += ''.join('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>' for r in body)
            out.append(t + '</tbody></table></div>')
        else:
            txt = ' '.join(b.split())
            out.append(f'<p>{inline(txt)}</p>')
            if cur_q is not None:
                cur_q[1] += txt + ' '
    faq = [[q, re.sub(r'\*\*|\[([^\]]+)\]\([^)]+\)', lambda m: m.group(1) or '', a).strip()] for q, a in faq if a.strip()]
    return '\n'.join(out), faq


def data_br(d):
    return f'{d.day} de {MESES[d.month - 1]} de {d.year}'


def render(head, ld, main, depth, aria=True):
    r = '../' * depth
    h = MOLDE.replace('{{HEAD}}', head).replace('{{LD}}', f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>')
    h = h.replace('{{CSS}}', re.sub(r'\s*\n\s*', '', CSS)).replace('{{MAIN}}', main).replace('{{R}}', r)
    if not aria:
        h = h.replace(' aria-current="page"', '', 1)
    return h


def head(title, desc, url, typ='website', extra=''):
    return (f'<title>{E(title)}</title>\n<meta name="description" content="{E(desc)}">\n'
            f'<link rel="canonical" href="{url}">\n<meta name="robots" content="index, follow, max-image-preview:large">\n'
            f'<meta name="theme-color" content="#0B1B33">\n'
            f'<meta property="og:type" content="{typ}"><meta property="og:locale" content="pt_BR"><meta property="og:site_name" content="SOUVRIN Soluções Financeiras">\n'
            f'<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{url}">\n'
            f'<meta property="og:image" content="{SITE}/assets/og.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">\n'
            f'<meta name="twitter:card" content="summary_large_image">\n'
            f'<link rel="alternate" type="application/rss+xml" title="Souvrin: crédito com garantia de imóvel, explicado" href="{SITE}/conteudo/feed.xml">{extra}')


ORG = {"@type": ["FinancialService", "Organization"], "@id": SITE + "/#org", "name": "SOUVRIN Soluções Financeiras",
       "url": SITE + "/", "email": "contato@souvrin.com.br", "telephone": "+55-12-99134-6990",
       "areaServed": {"@type": "Country", "name": "Brasil"},
       "description": "Consultoria em crédito com garantia de imóvel (home equity) para pessoas e empresas."}


def paginas():
    """Gera as páginas fixas a partir de _blog/paginas/*.html. Devolve as URLs para o sitemap."""
    urls = []
    for f in sorted((BLOG / 'paginas').glob('*.html')):
        m = re.match(r'---\n(.*?)\n---\n(.*)', f.read_text(), re.S)
        meta = dict(l.split(':', 1) for l in m.group(1).splitlines() if ':' in l)
        meta = {k.strip(): v.strip() for k, v in meta.items()}
        u = meta['url']
        depth = 0 if u in ('/', '/404.html') else u.strip('/').count('/') + 1
        h = head(meta['titulo'], meta['descricao'], SITE + u)
        if meta.get('robots'):
            h = h.replace('index, follow, max-image-preview:large', meta['robots'])
        ld = {"@context": "https://schema.org", "@graph": [ORG, {"@type": "WebPage", "url": SITE + u, "name": meta['titulo'],
              "description": meta['descricao'], "inLanguage": "pt-BR", "publisher": {"@id": SITE + "/#org"}}]}
        page = render(h, ld, m.group(2), depth).replace(' class="on" aria-current="page"', '')
        if u == '/404.html':
            page = page.replace('href="assets/', 'href="/assets/').replace('href=""', 'href="/"').replace('href="#', 'href="/#').replace('href="conteudo/', 'href="/conteudo/').replace('href="privacidade/', 'href="/privacidade/')
            (ROOT / '404.html').write_text(page)
            continue
        dest = ROOT / u.strip('/') / 'index.html' if u != '/' else ROOT / 'index.html'
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(page)
        urls.append(u)
    return urls


def card(p, r):
    return (f'<a class="card" href="{r}conteudo/{p["slug"]}/"><span class="tag">{E(FORMATO.get(p["formato"], "Artigo"))}</span>'
            f'<h2 style="font-size:21px;letter-spacing:-.01em">{E(p["titulo"])}</h2><p>{E(p.get("resumo") or p["descricao"])}</p>'
            f'<time datetime="{p["data"]}">{data_br(p["data"])}</time><span class="go">Ler →</span></a>')


def build():
    fixas = paginas()
    posts = [parse(f) for f in sorted((BLOG / 'posts').glob('*.md'))]
    posts = [p for p in posts if p.get('rascunho', 'nao').lower() not in ('sim', 'true')]
    slugs = [p['slug'] for p in posts]
    if len(slugs) != len(set(slugs)):
        fail('slug repetido')
    posts.sort(key=lambda p: (p['data'], p['slug']), reverse=True)
    avisos = []

    # limpa páginas de posts antigas (só pastas geradas por este script)
    OUT.mkdir(exist_ok=True)
    for d in OUT.iterdir():
        if d.is_dir() and (d / '.gerado').exists() and d.name not in slugs:
            for f in d.iterdir():
                f.unlink()
            d.rmdir()

    for p in posts:
        body, faq = md_to_html(p['md'])
        p['faq'] = faq
        words = len(re.sub(r'<[^>]+>', ' ', body).split())
        p['min'] = max(1, round(words / 200))
        url = f'{SITE}/conteudo/{p["slug"]}/'
        title = f'{p["titulo"]} | SOUVRIN'
        if len(title) > 65:
            avisos.append(f'{p["slug"]}: título com {len(title)} caracteres (ideal até 60)')
        if not 110 <= len(p['descricao']) <= 160:
            avisos.append(f'{p["slug"]}: descrição com {len(p["descricao"])} caracteres (ideal 120–158)')
        minimo = 700 if p['formato'] == 'artigo' else 400
        if words < minimo:
            avisos.append(f'{p["slug"]}: só {words} palavras (mínimo sugerido {minimo})')
        for link in re.findall(r'href="(/[^"#?]+)', body):
            alvo = ROOT / link.strip('/') / 'index.html' if link.strip('/') else ROOT / 'index.html'
            if not alvo.exists() and not (link.startswith('/conteudo/') and link.strip('/').split('/')[-1] in slugs):
                avisos.append(f'{p["slug"]}: link interno quebrado {link}')
        cat_nome, cat_slug = CAT[p['categoria']]
        rel = [q for q in posts if q is not p and q['categoria'] == p['categoria']][:3]
        rel += [q for q in posts if q is not p and q not in rel][:3 - len(rel)]
        ld = {"@context": "https://schema.org", "@graph": [
            {"@type": "BlogPosting", "@id": url + "#post", "headline": p['titulo'], "description": p['descricao'],
             "datePublished": str(p['data']), "dateModified": str(p['atualizado']), "inLanguage": "pt-BR",
             "mainEntityOfPage": url, "url": url, "image": SITE + "/assets/og.png", "wordCount": words,
             "keywords": p.get('palavra_chave', ''), "articleSection": cat_nome,
             "author": {"@type": "Organization", "name": "Equipe Souvrin", "url": SITE + "/"},
             "publisher": {"@id": SITE + "/#org"}},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Início", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Conteúdo", "item": SITE + "/conteudo/"},
                {"@type": "ListItem", "position": 3, "name": p['titulo'], "item": url}]}]}
        if faq:
            ld['@graph'].append({"@type": "FAQPage", "mainEntity": [
                {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]})
        upd = f' · Atualizado em {data_br(p["atualizado"])}' if p['atualizado'] != p['data'] else ''
        cta_prod = (f'<a class="btn" href="../../{cat_slug}/" style="border-color:var(--ala);color:var(--ala)">Ver {E(cat_nome.lower())}</a>'
                    if cat_slug != 'simulador' else '')
        main = f'''<div class="band"><article class="post">
  <nav class="crumb" aria-label="Você está em"><a href="../../">Início</a> / <a href="../">Conteúdo</a> / {E(cat_nome)}</nav>
  <span class="tag">{E(FORMATO.get(p['formato'], 'Artigo'))}</span>
  <h1 style="margin-top:14px;font-size:clamp(32px,4.4vw,50px)">{E(p['titulo'])}</h1>
  <div class="meta"><span>Por Equipe Souvrin</span><time datetime="{p['data']}">{data_br(p['data'])}</time><span>{p['min']} min de leitura</span></div>
  <div class="body">
{body}
  </div>
  <div class="box"><h2>Quer ver a conta do seu caso?</h2><p>Um consultor da Souvrin responde pelo WhatsApp com as opções e o custo total, antes de qualquer assinatura.</p>
   <div class="row" style="margin-top:18px"><a class="btn cta" href="../../#simulador">Simular agora</a>{cta_prod}</div></div>
  <p class="disc">Publicado em {data_br(p['data'])}{upd}. Conteúdo informativo. Taxas, prazos e limites são referências e dependem da análise de crédito e das regras de cada instituição. A Souvrin não é instituição financeira: atua na consultoria e intermediação de operações de instituições parceiras.</p>
 </article></div>
 <div class="band" style="padding-top:0"><div class="wrap">
  <span class="mi">Continue lendo</span>
  <div class="cards">{"".join(card(q, "../../") for q in rel)}</div>
 </div></div>'''
        extra = f'\n<meta property="article:published_time" content="{p["data"]}"><meta property="article:modified_time" content="{p["atualizado"]}">'
        d = OUT / p['slug']
        d.mkdir(parents=True, exist_ok=True)
        (d / 'index.html').write_text(render(head(title, p['descricao'], url, 'article', extra), ld, main, 2, aria=False))
        (d / '.gerado').write_text('')

    # índice /conteudo/
    title = 'Crédito com garantia de imóvel, explicado | SOUVRIN'
    desc = 'Guias e respostas diretas sobre crédito com garantia de imóvel (home equity): custos, documentos, riscos e como usar o patrimônio a seu favor.'
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "Blog", "@id": SITE + "/conteudo/#blog", "url": SITE + "/conteudo/", "name": title, "description": desc,
         "inLanguage": "pt-BR", "publisher": {"@id": SITE + "/#org"},
         "blogPost": [{"@type": "BlogPosting", "headline": p['titulo'], "url": f'{SITE}/conteudo/{p["slug"]}/', "datePublished": str(p['data'])} for p in posts[:20]]},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Início", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Conteúdo", "item": SITE + "/conteudo/"}]}]}
    main = f'''<div class="band"><div class="wrap">
  <span class="mi">Conteúdo</span>
  <h1 style="margin-top:14px;max-width:20ch">Crédito com garantia de imóvel, explicado.</h1>
  <p class="lead" style="margin-top:18px">Guias e respostas diretas sobre crédito com garantia de imóvel, escritos por quem estrutura essas operações todos os dias.</p>
  <div class="cards">{"".join(card(p, "../") for p in posts) or "<p>Os primeiros guias saem nos próximos dias.</p>"}</div>
 </div></div>'''
    (OUT / 'index.html').write_text(render(head(title, desc, SITE + '/conteudo/'), ld, main, 1))

    # feed RSS
    rfc = lambda d: datetime.datetime(d.year, d.month, d.day, 8, 0).strftime('%a, %d %b %Y %H:%M:%S -0300')
    items = ''.join(f'<item><title>{E(p["titulo"])}</title><link>{SITE}/conteudo/{p["slug"]}/</link>'
                    f'<guid>{SITE}/conteudo/{p["slug"]}/</guid><pubDate>{rfc(p["data"])}</pubDate>'
                    f'<description>{E(p["descricao"])}</description></item>' for p in posts[:30])
    (OUT / 'feed.xml').write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>Souvrin: crédito com garantia de imóvel, explicado</title>'
                                  f'<link>{SITE}/conteudo/</link><description>{E(desc)}</description><language>pt-BR</language>{items}</channel></rss>\n')

    # sitemap gerado do zero: páginas fixas + índice do blog + posts
    hoje = datetime.date.today()
    ult = max([p['atualizado'] for p in posts], default=hoje)
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sm += ''.join(f'  <url><loc>{SITE}{u}</loc><lastmod>{hoje}</lastmod><priority>{"1.0" if u == "/" else "0.5"}</priority></url>\n' for u in fixas)
    sm += f'  <url><loc>{SITE}/conteudo/</loc><lastmod>{ult}</lastmod><priority>0.8</priority></url>\n'
    sm += ''.join(f'  <url><loc>{SITE}/conteudo/{p["slug"]}/</loc><lastmod>{p["atualizado"]}</lastmod><priority>0.7</priority></url>\n' for p in posts)
    (ROOT / 'sitemap.xml').write_text(sm + '</urlset>\n')

    print(f'ok: {len(posts)} posts em /conteudo/')
    for a in avisos:
        print('  aviso:', a)
    return avisos


if __name__ == '__main__':
    build()
