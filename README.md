# Protector-of-Earth-3DS
Independent research and development project focused on porting Ben 10: Protector of Earth (PSP) to Nintendo 3DS.
# Protector of Earth 3DS

**Projeto de pesquisa e desenvolvimento de um port de _Ben 10: Protector of Earth_ (versão PSP) para Nintendo 3DS.**

> Projeto comunitário e experimental, ainda em fase de engenharia reversa e levantamento de formatos. Não é um port jogável neste momento e não inclui arquivos comerciais do jogo.

## Objetivo

Investigar a estrutura da versão PSP, documentar executáveis, módulos, níveis e recursos, e desenvolver ferramentas que ajudem a avaliar uma implementação compatível com o Nintendo 3DS.

O objetivo final é uma adaptação nativa para o hardware do 3DS. Binários PSP (MIPS/Allegrex) não são executáveis diretamente no 3DS (ARM); será necessário reimplementar sistemas do jogo, traduzir componentes ou desenvolver camadas de compatibilidade, além de adaptar renderização, áudio, controles e gerenciamento de memória.

## Estado atual

- [x] Scanner inicial de arquivos e assinaturas.
- [x] Inventário de arquivos, extensões, tamanhos e hashes SHA-256.
- [x] Leitura preliminar de cabeçalhos ELF32 little-endian e segmentos/seções.
- [x] Identificação preliminar de vídeos PSMF e módulos PRX por assinatura.
- [x] Registro de configurações e catálogo de níveis fornecidos durante a análise.
- [x] Builder de relatórios com agrupamento de arquivos `.r4s`/`.r4m` por nome-base.
- [ ] Confirmar a estrutura interna dos formatos `.r4s` e `.r4m`.
- [ ] Investigar tabelas de recursos, texturas, modelos, animações e áudio.
- [ ] Mapear chamadas e dependências relevantes do executável PSP.
- [ ] Definir arquitetura de gameplay, renderização e áudio para o 3DS.
- [ ] Implementar protótipo nativo para Nintendo 3DS.

## Inventário de referência

O levantamento inicial fornecido para a pasta do jogo encontrou **487 arquivos**, totalizando aproximadamente **731,4 MB**. Entre as extensões mais frequentes:

| Extensão | Quantidade | Observação |
|---|---:|---|
| `.r4s` | 177 | Dados proprietários ainda não identificados |
| `.r4m` | 175 | Dados proprietários ainda não identificados |
| `.pmf` | 77 | Candidatos a vídeo PSP; assinatura PSMF reconhecida |
| `.prx` | 41 | Módulos PSP |
| `.png` | 6 | Imagens PNG |
| `.bin` | 4 | Binários variados |

Os nomes-base coincidentes entre arquivos `.r4s` e `.r4m` foram agrupados pelo builder para facilitar a investigação. **Isso não prova que os dois formatos sejam um par funcional nem revela seu conteúdo.**

O relatório ELF de referência identificou `SYSDIR/BOOT.BIN` como ELF32 little-endian, máquina MIPS. O `EBOOT.BIN` principal foi reconhecido pela assinatura `PSP_SCE_PRX`; isso não significa que esteja descriptografado ou pronto para análise estática comum.

## Ferramenta: POE3DS Builder

O builder usa somente a biblioteca padrão do Python e não altera os arquivos de origem.

### Requisitos

- Python 3.9 ou superior.
- Cópia local dos arquivos do jogo extraídos de uma mídia que você possui.

### Uso

```bash
python poe3ds_builder.py "/caminho/para/PSP_GAME" --out poe3ds_report
```

Para pular o cálculo dos hashes e acelerar o inventário:

```bash
python poe3ds_builder.py "/caminho/para/PSP_GAME" --out poe3ds_report --no-hash
```

### Relatórios gerados

- `game_manifest.json` — resumo geral e inventário de arquivos.
- `asset_summary.json` — contagens por extensão/assinatura e candidatos a recursos.
- `executable_report.json` — análise preliminar de ELF e reconhecimento de executáveis.
- `r4_pair_report.json` — agrupamento de `.r4s` e `.r4m` por nome-base.
- `text_file_report.json` — estatísticas básicas de arquivos `.txt`.
- `scan_errors.json` — arquivos que não puderam ser lidos.

## Estrutura sugerida do repositório

```text
Protector-of-Earth-3DS/
├── README.md
├── poe3ds_builder.py
├── docs/
│   ├── research-notes.md
│   ├── file-formats.md
│   └── porting-roadmap.md
├── tools/
└── .gitignore
```

Não publique dumps, ISOs, executáveis originais, vídeos, músicas, texturas ou outros recursos protegidos por direitos autorais. Publique ferramentas próprias, documentação, metadados não sensíveis e código original. Cada colaborador deve obter legalmente sua própria cópia do jogo.

## Direção técnica

1. **Formato dos dados:** documentar os contêineres `.r4s` e `.r4m` antes de tentar extrair ou converter recursos.
2. **Executáveis e APIs:** mapear o fluxo de inicialização e as dependências PSP sem assumir que o binário PSP possa ser reutilizado diretamente.
3. **Recursos:** identificar modelos, texturas, animações, áudio, vídeos e dados de fase; criar conversores apenas quando os formatos forem compreendidos.
4. **Nintendo 3DS:** planejar renderização via citro3d/libctru, entrada, áudio, memória, salvamento e interface.
5. **Protótipo:** começar por uma cena pequena e isolada antes de tentar portar uma fase completa.

## Aviso

Este repositório é um projeto independente, sem afiliação ou endosso da Nintendo, da desenvolvedora ou da publicadora de _Ben 10: Protector of Earth_. Marcas e direitos sobre o jogo permanecem com seus respectivos titulares.
