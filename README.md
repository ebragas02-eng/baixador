# baixador

Robô de downloads de documentos públicos oficiais e radar de concursos da ICEAD.

## Para que serve

- **Downloads (`.github/workflows/baixa.yml`):** cada linha de `urls.txt` tem o formato `caminho/nome.ext URL`. Um push que altera `urls.txt` faz o GitHub Actions baixar os arquivos para `saida/` e gravá-los com o commit `baixado`.
- **Radar de concursos (`.github/workflows/radar_concursos.yml`):** todo dia às 7h23 (horário de Brasília) o `radar/radar.py` lê páginas públicas de bancas, agregadores e diários oficiais (Querido Diário e DOU) e, quando encontra concurso novo, abre uma issue com o rótulo `radar` neste repositório.

## Regras de conteúdo

- O robô só baixa **documentos públicos oficiais**: leis, editais, normas e páginas de órgãos públicos.
- **Provas de bancas e materiais de terceiros não ficam guardados neste repositório.** Quem baixar um arquivo desse tipo deve apagá-lo de `saida/` logo depois do uso.
- Todo arquivo em `saida/` com mais de 7 dias é apagado automaticamente (a cada execução e numa limpeza diária).
- Nenhum segredo, dado pessoal ou código de produto é guardado aqui. O radar usa apenas o `GITHUB_TOKEN` do próprio repositório.
