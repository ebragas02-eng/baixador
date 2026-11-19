# Radar de concursos da ICEAD (rotina diária no GitHub Actions, gratuita).
# Lê as páginas públicas das bancas e de agregadores, guarda o que já foi visto em vistos.json e,
# quando aparece concurso novo, grava novos.md e o workflow abre uma issue (o GitHub avisa por e-mail).
# A avaliação "temos condições de preparar?" é feita depois, com o edital em mãos (rotina semanal).
# Diários oficiais: municípios pelo Querido Diário (API pública da Open Knowledge Brasil), União pelo DOU
# (busca pública da Imprensa Nacional); estados e Distrito Federal pelos agregadores de todas as regiões.
import json, os, re, sys, urllib.request, urllib.parse, html, datetime
AQUI = os.path.dirname(os.path.abspath(__file__))
VISTOS = os.path.join(AQUI, 'vistos.json')
FONTES = [
 ('FGV', 'https://conhecimento.fgv.br/concursos', r'href="(/concursos/[a-z0-9-]+)"[^>]*>\s*([^<]{6,160})<'),
 ('FCC', 'https://www.concursosfcc.com.br/concursos/', r'href="(https://www\.concursosfcc\.com\.br/concursos/[a-z0-9]+/index\.html)"[^>]*>\s*(?:<[^>]+>\s*)*([^<]{4,160})<'),
]
# agregadores por região (cobrem os diários oficiais dos estados, do Distrito Federal e dos municípios)
PCI = r'href="(https://www\.pciconcursos\.com\.br/noticias/[a-z0-9-]+)"[^>]*>\s*([^<]{8,200})<'
for reg, nome in [('nacional', 'PCI Nacional'), ('sudeste', 'PCI Sudeste'), ('sul', 'PCI Sul'), ('nordeste', 'PCI Nordeste'), ('norte', 'PCI Norte'), ('centrooeste', 'PCI Centro-Oeste')]:
    FONTES.append((nome, 'https://www.pciconcursos.com.br/concursos/%s/' % reg, PCI))
# grandes concursos de bancos públicos e do INSS também são prioridade
GRANDES = re.compile(r'banco do brasil|caixa econ[oô]mica|\bcaixa\b|banco do nordeste|\bbnb\b|banco da amaz[oô]nia|\bbasa\b|\bbrb\b|banco de bras[ií]lia|banrisul|banestes|banpar[aá]|banese|bndes|banco central|\bbacen\b|\binss\b|instituto nacional do seguro social', re.I)
# grandes concursos de professor têm prioridade: estados, Distrito Federal, capitais e municípios grandes
PROFESSOR = re.compile(r'professor|magist[eé]rio|docente|educa[cç][aã]o b[aá]sica|seduc|secretaria (?:de estado )?da educa', re.I)
CAPITAIS = re.compile(r'S[aã]o Paulo|Rio de Janeiro|Belo Horizonte|Bras[ií]lia|Distrito Federal|Salvador|Fortaleza|Recife|Curitiba|Porto Alegre|Manaus|Bel[eé]m|Goi[aâ]nia|S[aã]o Lu[ií]s|Macei[oó]|Natal|Teresina|Jo[aã]o Pessoa|Aracaju|Campo Grande|Cuiab[aá]|Florian[oó]polis|Vit[oó]ria|Palmas|Porto Velho|Rio Branco|Macap[aá]|Boa Vista|Campinas|Guarulhos|Ribeir[aã]o Preto|Sorocaba|Santos|S[aã]o Jos[eé] dos Campos|Osasco|Santo Andr[eé]|S[aã]o Bernardo|Uberl[aâ]ndia|Contagem|Juiz de Fora|Joinville|Londrina|Niter[oó]i|Duque de Caxias|Nova Igua[cç]u|Feira de Santana|Aparecida de Goi[aâ]nia', re.I)
def querido_diario(desde):
    q = '"concurso público" + edital + (professor | magistério | docente)'
    u = 'https://queridodiario.ok.org.br/api/gazettes?' + urllib.parse.urlencode({'querystring': q, 'published_since': desde, 'size': 100, 'excerpt_size': 300, 'number_of_excerpts': 1, 'sort_by': 'descending_date'})
    for tentativa in range(3):   # a API do Querido Diário às vezes demora
        try: d = json.loads(baixa(u, 120)); break
        except Exception:
            if tentativa == 2: raise
    return [('Diário municipal', '%s/%s · %s · %s' % (g['territory_name'], g['state_code'], g['date'], re.sub(r'\s+', ' ', (g.get('excerpts') or [''])[0])[:160]), g['url']) for g in d.get('gazettes', [])]
def dou():
    u = 'https://www.in.gov.br/consulta/-/buscar/dou?' + urllib.parse.urlencode({'q': 'concurso público edital abertura', 's': 'todos', 'exactDate': 'semana', 'sortType': '0'})
    m = re.search(r'BuscaDouPortlet_params"[^>]*>(.*?)</script>', baixa(u), re.S)
    arr = json.loads(m.group(1)).get('jsonArray', []) if m else []
    return [('DOU', '%s · %s · %s' % (x.get('pubDate', ''), x.get('title', ''), x.get('hierarchyStr', '')[:80]), 'https://www.in.gov.br/web/dou/-/' + x.get('urlTitle', '')) for x in arr]
BASE = {'FGV': 'https://conhecimento.fgv.br', 'FCC': 'https://www.concursosfcc.com.br'}
# o que interessa à ICEAD (áreas em que já temos material ou base): educação, direito, contabilidade, finanças, administração pública, nível médio geral
INTERESSE = re.compile(r'banco|caixa|inss|seguro social|professor|educa|seduc|secretaria da educa|pedag|direito|procurador|defensor|advog|contab|contador|fiscal|auditor|tribunal|câmara|camara|assembleia|prefeitura|banco|anbima|cfc|oab|tecnico|técnico|analista|agente|escriturário|escriturario', re.I)
def baixa(u, espera=40):
    r = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36', 'Accept': 'text/html,application/json;q=0.9,*/*;q=0.8', 'Accept-Language': 'pt-BR,pt;q=0.9'})
    with urllib.request.urlopen(r, timeout=espera) as f: b = f.read()
    try: return b.decode('utf-8')
    except UnicodeDecodeError: return b.decode('latin-1')
def main():
    vistos = json.load(open(VISTOS)) if os.path.exists(VISTOS) else {}
    primeira = not vistos
    fontes_vistas = {v.get('fonte') for v in vistos.values()}
    novos, erros = [], []
    achados = []
    for nome, url, rx in FONTES:
        try: pag = baixa(url)
        except Exception as e: erros.append(f'{nome}: {e}'); continue
        for href, titulo in re.findall(rx, pag, re.I):
            t = re.sub(r'\s+', ' ', html.unescape(titulo)).strip()
            achados.append((nome, t, BASE.get(nome, '') + href if href.startswith('/') else href))
    desde = (datetime.date.today() - datetime.timedelta(days=4)).isoformat()
    for nome, fn in [('Diário municipal', lambda: querido_diario(desde)), ('DOU', dou)]:
        try: achados += fn()
        except Exception as e: erros.append(f'{nome}: {e}')
    for nome, t, link in achados:
        if link in vistos: continue
        vistos[link] = {'fonte': nome, 'titulo': t[:200], 'visto': datetime.date.today().isoformat()}
        if nome not in fontes_vistas: continue   # fonte nova: a primeira leitura só forma a base
        if nome in ('Diário municipal', 'DOU') or INTERESSE.search(t + ' ' + link): novos.append((nome, t, link))
    json.dump(vistos, open(VISTOS, 'w'), ensure_ascii=False, indent=0)
    saida = os.path.join(AQUI, 'novos.md')
    if primeira:
        open(saida, 'w').write(''); print('primeira execução: %d itens guardados como base' % len(vistos)); return
    if novos:   # fonte fora do ar sozinha não abre aviso; fica no registro da execução
        linhas = ['Concursos novos encontrados pelo radar da ICEAD em %s:' % datetime.date.today().strftime('%d/%m/%Y'), '']
        eprof = lambda n: n[0] == 'Diário municipal' or PROFESSOR.search(n[1] + n[2])   # a busca nos diários municipais já é só de professor
        prio = [n for n in novos if GRANDES.search(n[1] + ' ' + n[2])] + [n for n in novos if eprof(n) and not GRANDES.search(n[1] + ' ' + n[2]) and (CAPITAIS.search(n[1]) or re.search(r'estado|estadual|governo|seduc|distrito federal', n[1], re.I))]
        prof = [n for n in novos if eprof(n) and n not in prio]
        outros = [n for n in novos if n not in prio and n not in prof]
        for tit, grupo in [('Prioridade: bancos públicos, INSS e professor em estado, Distrito Federal, capital ou município grande', prio), ('Professor (demais municípios)', prof), ('Outras áreas', outros)]:
            if grupo: linhas += ['## ' + tit, ''] + ['- **%s** · %s · %s' % (f, t, l) for f, t, l in grupo[:60]] + ['']
        if erros: linhas += ['', 'Fontes que não responderam hoje: ' + '; '.join(erros)]
        linhas += ['', 'Próximo passo: ler o edital e avaliar se a ICEAD tem condições de preparar o material (rotina semanal).']
        open(saida, 'w').write('\n'.join(linhas))
    else:
        open(saida, 'w').write('')
    print(len(novos), 'novos;', len(erros), 'erros', erros)
if __name__ == '__main__': main()
