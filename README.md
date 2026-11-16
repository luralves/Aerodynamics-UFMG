# Coleção Aerodinâmica — UFMG

Projeto de livros didáticos de Aerodinâmica.

## Estrutura principal

Os livros estão disponíveis na pasta `books/` e os arquivos finais estão disponíveis em `build/`.

## Como gerar os arquivos

Execute os comandos abaixo no terminal, a partir da raíz do projeto.

Reúne os PDFs existentes e compila os ausentes quando necessário:
```bash
python3 -m publishing pdf
```

Força a recompilação de todos os livros em PDF:
```bash
python3 -m publishing pdf --force
```

Preserva os arquivos auxiliares da compilação:
```bash
python3 -m publishing pdf --keep-aux
```

Requisitos para PDF
-------------------
- Python 3
- Distribuição LaTeX com pdfLaTeX, latexmk e Biber
- Pacotes LaTeX exigidos por `aerodynamics.cls`

Formatos planejados
-------------------
    python -m publishing epub
    python -m publishing site
    python -m publishing all
