%% Compiler: pdfLaTeX; bibliography backend: Biber.
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{aerodynamics}[2026/11/16 v0.4 Aerodynamics textbook class (pdfLaTeX)]

% ------------------------------------------------------------------
% 1. Language options and base class
% ------------------------------------------------------------------
\newif\ifAero@english
\Aero@englishfalse
\DeclareOption{portuguese}{\Aero@englishfalse}
\DeclareOption{brazil}{\Aero@englishfalse}
\DeclareOption{english}{\Aero@englishtrue}
% Forward additional options to the standard book class.
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{book}}
\ProcessOptions\relax
\LoadClass[11pt,a4paper,oneside,openany]{book}

\RequirePackage{iftex}
\RequirePackage{amsmath}
\RequirePackage{amssymb}
\RequirePackage{mathtools}
\RequirePackage{amsthm}

% ------------------------------------------------------------------
% 2. Language and typography
% ------------------------------------------------------------------
\ifAero@english
  \RequirePackage[english]{babel}
  \def\aero@toclabel{In this chapter}
  \def\aero@reflabel{References}
  \def\aero@examplelabel{Example}
  \def\aero@exerciselabel{Exercise}
  \def\aero@remarklabel{Remark}
\else
  \RequirePackage[brazil]{babel}
  \def\aero@toclabel{Neste capítulo}
  \def\aero@reflabel{Referências bibliográficas}
  \def\aero@examplelabel{Exemplo}
  \def\aero@exerciselabel{Exercício}
  \def\aero@remarklabel{Observação}
\fi

% pdfLaTeX requires Type 1 fonts; fontspec/unicode-math are not supported.
\ifPDFTeX\else
  \ClassError{aerodynamics}
    {This class requires pdfLaTeX}
    {Compile using pdflatex or latexmk -pdf.}
\fi
\RequirePackage[T1]{fontenc}
\RequirePackage[utf8]{inputenc}
\RequirePackage{lmodern}          % Latin Modern monospaced font
\RequirePackage[default,defaultsans]{lato} % Main text: Lato
\RequirePackage{newtxmath}        % Serif mathematics, compatible with pdfLaTeX
% Compatibility alias for math expressions using \symbfit.
\providecommand{\symbfit}[1]{\boldsymbol{#1}}
\RequirePackage{microtype}
\linespread{1.14}

% ------------------------------------------------------------------
% 3. Page layout, palette, and general settings
% ------------------------------------------------------------------
\RequirePackage[
  a4paper,
  top=28mm, bottom=28mm,
  inner=30mm, outer=27mm,
  headheight=15pt, headsep=8mm, footskip=13mm
]{geometry}
\RequirePackage{graphicx}
\RequirePackage{xcolor}
\RequirePackage{tikz}
\RequirePackage{fancyhdr}
\RequirePackage{titlesec}
\RequirePackage{etoc}
\RequirePackage{csquotes}
\RequirePackage{enumitem}
\RequirePackage{subcaption}

\definecolor{AeroBlack}{gray}{0.10}
\definecolor{AeroGray}{gray}{0.91}
\definecolor{AeroMidGray}{gray}{0.45}
\color{AeroBlack}
\setlength{\parindent}{1.2em}
\setlength{\parskip}{0.1em}
\setlength{\emergencystretch}{2em}
\setlist{itemsep=0.3em,topsep=0.4em}

% Chapter and section headings: understated sans-serif hierarchy.
\titleformat{\chapter}[display]
  {\normalfont\sffamily\bfseries\color{AeroBlack}}
  {\normalfont\small\sffamily\color{AeroMidGray}\chaptername~\thechapter}
  {10pt}
  {\fontsize{25}{30}\selectfont}
\titlespacing*{\chapter}{0pt}{8pt}{25pt}
\titleformat{\section}{\Large\sffamily\bfseries\color{AeroBlack}}{\thesection}{0.85em}{}
\titleformat{\subsection}{\large\sffamily\bfseries\color{AeroBlack}}{\thesubsection}{0.8em}{}
\titleformat{\subsubsection}{\normalsize\sffamily\bfseries\color{AeroBlack}}{\thesubsubsection}{0.8em}{}
\setcounter{secnumdepth}{3}
\setcounter{tocdepth}{1} % Global TOC: chapters and sections.

% Headers and page numbers.
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\footnotesize\sffamily\nouppercase{\leftmark}}
\fancyfoot[R]{\footnotesize\thepage}
\renewcommand{\headrulewidth}{0.35pt}
\renewcommand{\footrulewidth}{0pt}
\fancypagestyle{plain}{%
  \fancyhf{}%
  \fancyfoot[R]{\footnotesize\thepage}%
  \renewcommand{\headrulewidth}{0pt}%
}

% ------------------------------------------------------------------
% 4. Metadata defined ONLY in each language-specific main.tex
% ------------------------------------------------------------------
\newcommand{\subtitle}[1]{\gdef\aero@subtitle{#1}}
\newcommand{\institution}[1]{\gdef\aero@institution{#1}}
\newcommand{\city}[1]{\gdef\aero@city{#1}}
\def\aero@subtitle{}
\def\aero@institution{}
\def\aero@city{}

% Monochrome A4 cover, with a left-aligned title
% positioned approximately at the vertical center of the page.
\renewcommand{\maketitle}{%
  \hypersetup{pageanchor=false}% Prevents duplicate PDF page anchors in front matter.
  \begin{titlepage}%
    \thispagestyle{empty}%
    \begin{tikzpicture}[remember picture,overlay]
      % Dark left-hand strip.
      \fill[AeroBlack] (current page.north west) rectangle
        ([xshift=10mm]current page.south west);
      % University at the top.
      \node[anchor=north west,inner sep=0pt,text width=165mm,align=left]
        at ([xshift=28mm,yshift=-20mm]current page.north west)
        {{\sffamily\fontsize{14}{18}\selectfont\bfseries\aero@institution}};
      \draw[AeroBlack,line width=0.85pt]
        ([xshift=28mm,yshift=-32mm]current page.north west) --
        ([xshift=72mm,yshift=-32mm]current page.north west);
      % Gray horizontal band behind the title.
      \fill[AeroGray]
        ([xshift=10mm,yshift=-117mm]current page.north west) rectangle
        ([yshift=-148mm]current page.north east);
      \node[anchor=west,inner sep=0pt,text width=165mm,align=left]
        at ([xshift=28mm,yshift=-132.5mm]current page.north west)
        {{\sffamily\bfseries\fontsize{25}{30}\selectfont\@title}};
      % Subtitle.
      \node[anchor=north west,inner sep=0pt,text width=165mm,align=left]
        at ([xshift=28mm,yshift=-153mm]current page.north west)
        {{\sffamily\fontsize{16}{20}\selectfont\aero@subtitle}};
      % Authors and imprint.
      \draw[AeroBlack,line width=0.9pt]
        ([xshift=28mm,yshift=58mm]current page.south west) --
        ([xshift=72mm,yshift=58mm]current page.south west);
      \node[anchor=north west,inner sep=0pt,text width=160mm,align=left]
        at ([xshift=28mm,yshift=51mm]current page.south west)
        {{\begingroup\sffamily\fontsize{12.5}{17}\selectfont\bfseries
          \def\and{\par}% Author entries supplied using \author{A \and B}.
          \@author\par\endgroup}};
      \node[anchor=south west,inner sep=0pt,text width=165mm,align=left]
        at ([xshift=28mm,yshift=17mm]current page.south west)
        {{\sffamily\fontsize{11}{15}\selectfont
          \space\@date}};
    \end{tikzpicture}%
    \null\vfill
  \end{titlepage}%
  \hypersetup{pageanchor=true}%
  \cleardoublepage
}

% ------------------------------------------------------------------
% 5. Chapter table of contents (etoc)
% ------------------------------------------------------------------
\newcommand{\ChapterTOC}{%
  \begingroup
    \etocarticlestylenomarks
    \etocsetnexttocdepth{section}%
    \etocsettocstyle{%
      \par\bigskip\noindent
      {\large\sffamily\bfseries\aero@toclabel\par}%
      \vspace{5pt}\hrule height 0.4pt\vspace{7pt}%
    }{\par\medskip}%
    \localtableofcontents
  \endgroup
}

% ------------------------------------------------------------------
% 6. Numeric citations and chapter-specific references
% ------------------------------------------------------------------
\RequirePackage[
  backend=biber,
  style=numeric,
  sorting=none,
  refsection=chapter,
  giveninits=true,
  maxbibnames=99
]{biblatex}

\newcommand{\ChapterReferences}{%
  \printbibliography[heading=subbibliography,title={\aero@reflabel}]%
}

% ------------------------------------------------------------------
% 7. Teaching environments
% ------------------------------------------------------------------
\theoremstyle{definition}
\newtheorem{example}{\aero@examplelabel}[chapter]
\newtheorem{exercise}{\aero@exerciselabel}[chapter]
\theoremstyle{remark}
\newtheorem*{remark}{\aero@remarklabel}

% ------------------------------------------------------------------
% 8. PDF links and metadata
% ------------------------------------------------------------------
\RequirePackage[unicode=true,hidelinks,pdfencoding=auto]{hyperref}
\AtBeginDocument{%
  \hypersetup{pdftitle={\@title}}%
}

\endinput
