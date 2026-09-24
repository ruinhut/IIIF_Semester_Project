---
documentclass: extarticle
classoption:
  - 9pt
papersize: a4
geometry:
  - top=1.05cm
  - bottom=1.05cm
  - left=1.25cm
  - right=1.25cm
mainfont: "Arial"
monofont: "Consolas"
colorlinks: true
urlcolor: blue
header-includes:
  - \usepackage{graphicx}
  - \usepackage{fvextra}
  - \fvset{breaklines=true,fontsize=\scriptsize}
  - \usepackage{multicol}
  - \setlength{\columnsep}{0.65cm}
  - \usepackage{enumitem}
  - \setlist{nosep,leftmargin=*}
  - \usepackage{titlesec}
  - \titlespacing*{\section}{0pt}{0.5em}{0.2em}
  - \titlespacing*{\subsection}{0pt}{0.35em}{0.15em}
  - \setlength{\parindent}{0pt}
  - \setlength{\parskip}{0.18em}
  - \setlength{\tabcolsep}{3pt}
  - \renewcommand{\arraystretch}{0.9}
---

\begin{center}
{\Large\bfseries IIIF Document Information Extraction — Weekly Briefing}\\[-0.1em]
Boheng Shang · 22 September 2026
\end{center}
\vspace{-0.35em}

**Meeting:** 11:00–11:20 · **Room:** INN 128 · **Zoom:** <https://epfl.zoom.us/j/2693459226>

## Suggested oral report

Good morning. This week, I studied the main IIIF discovery mechanisms and designed a seven-module harvesting pipeline. I implemented and tested the first three modules: provider census and selection, entry-URL validation, and IIIF resource discovery.

Module 1 currently combines 95 unique candidate records: 69 from the official IIIF Finding Resources guide, 25 from Awesome IIIF, and one from the IIIF Registry. Module 2 checks HTTP status, redirects, response type, elapsed time, JSON parsing, and basic IIIF type. Module 3 discovers resources through Change Discovery streams, IIIF Collections, direct Manifest links, and links declared in HTML pages.

The tested routes produced 21,872 unique Manifest URLs: 21,853 from the Bodleian Change Discovery stream, 18 from Fragmentarium, and one from a Biblissima demonstration. This is a reproducible baseline, not the total available from all 95 candidates.

Testing revealed that the catalogue converter normally retains only the first source-entry link, which is often a homepage. Institutions instead expose IIIF through Change Discovery, Collections, institutional APIs, URL templates, or record-level links. I therefore propose to retain and classify all relevant links in Module 1, validate every candidate endpoint in Module 2, and add Collection pagination plus API/template adapters in Module 3.

## Verified evidence

| Area | Result |
|---|---|
| Module 1 | 95 candidates = 69 official-guide + 25 Awesome IIIF + 1 Registry + 0 manual |
| Module 2 | 1 reachable JSON; 65 reachable non-JSON; 1 too large; 12 restricted; 4 temporary failures; 12 unreachable |
| Module 3 | 21,872 unique Manifest URLs = Bodleian 21,853 + Fragmentarium 18 + Biblissima demo 1 |
| Tests rerun today | Module 1: 13; Module 2: 11; Module 3: 16 — **40/40 passed** |
| Interpretation | Candidates are not confirmed APIs; HTML or one failed URL does not prove that an institution lacks IIIF |

## Problem and correction

IIIF has no mandatory universal discovery endpoint. The Registry is voluntary and incomplete; the official guide mainly explains record-level Manifest discovery; Awesome IIIF mixes providers, viewers, software, Presentation API and Image API implementations. Current coverage therefore measures input and adapter limitations rather than worldwide IIIF availability.

- **Module 1:** preserve the raw entry and every relevant link; classify homepage, Change Discovery, Collection, API documentation/search, Manifest examples and URL templates; distinguish providers from viewers, software and Image-only services.
- **Module 2:** check every candidate link and retain status, redirect, final URL, content type, timing, JSON/type evidence and failures; do not stop after one success.
- **Module 3:** add Presentation 2/3 Collection **next** pagination, API/template adapters, loop detection, checkpoints, caching, limits, rate control, retry/backoff and resumable output.

Use bounded samples before complete harvests. BSB advertised about 3.2 million Collection members; Carnegie exposed about 908 Manifests. An Image API **info.json** must not be counted as a Presentation Manifest.

## Decisions and next actions

**Confirm:** revised architecture; first complete provider; rights allowlist; treatment of Image-only records; common schema and handoff; server resources and rate limits.

**Then:** fix Module 1 multi-link ingestion and tests; extend Module 2; add Collection/API/template support to Module 3; sample BSB and Carnegie; implement Module 4 Manifest validation; continue with rights, metadata and common-schema export.

\newpage

\begin{center}
{\Large\bfseries IIIF Standard APIs — Meaning and Use}
\end{center}
\vspace{-0.3em}

~~~{=latex}
\begin{multicols}{2}
~~~

## General request method

IIIF resources normally use HTTP(S) and JSON or JSON-LD. Follow redirects, set an Accept header, record the final URL/status/content type, and check both context and resource type.

\begin{Verbatim}[fontsize=\scriptsize,breaklines=true]
curl.exe -L -H "Accept: application/ld+json, application/json" URL -o out.json
python -m json.tool out.json > pretty.json
\end{Verbatim}

## Presentation API 3.0

**Purpose:** describes how a compound digital object should be presented. A **Manifest** normally represents one object; its **Canvases** represent ordered views, pages, surfaces or time spans. A **Collection** groups Manifests and child Collections.

**How to use it:**

1. Request a known Manifest or Collection URL.
2. Verify the IIIF context and **type**.
3. For Presentation 3, read Collection/Manifest **items**. In Presentation 2, Collections commonly use **manifests/collections**, while Manifests commonly use **sequences**.
4. Follow Collection **next** pagination and nested Collections.
5. Preserve **id**, label, metadata, rights, requiredStatement, provider and source URL. Human-readable metadata is not guaranteed to be semantically normalized.

\begin{Verbatim}[fontsize=\scriptsize,breaklines=true]
curl.exe -L "MANIFEST_OR_COLLECTION_URL" -o presentation.json
\end{Verbatim}

Official specification: <https://iiif.io/api/presentation/3.0/>

## Image API 3.0

**Purpose:** delivers image information and derivatives. It can crop, resize, rotate and select quality/format. It does not describe the complete cultural object.

**How to use it:**

\begin{Verbatim}[fontsize=\scriptsize,breaklines=true]
GET {image-service-id}/info.json
GET {image-service-id}/{region}/{size}/{rotation}/{quality}.{format}

# Example
GET https://example.org/image-service/id/full/max/0/default.jpg
\end{Verbatim}

Read **info.json** to learn dimensions, profile and supported features. Construct image requests in the required order: region, size, rotation, quality and format. Do not count info.json as a Manifest.

Official specification: <https://iiif.io/api/image/3.0/>

## Change Discovery API 1.0

**Purpose:** publishes additions, updates, deletions and moves of IIIF resources so a client can synchronize incrementally.

**How to use it:**

1. Fetch the provider's **OrderedCollection**.
2. Open its first/last page and follow **next/prev** as appropriate.
3. Read every page's **orderedItems**.
4. For each Activity, inspect **type**, **object.id**, **object.type** and **endTime**.
5. Retrieve current Manifest/Collection objects for Create/Update; preserve or remove state for Delete/Remove/Move.
6. Store the last processed activity/time for later incremental runs.

\begin{Verbatim}[fontsize=\scriptsize,breaklines=true]
curl.exe -L "https://iiif.bodleian.ox.ac.uk/iiif/activity/all-changes" -o activity.json
\end{Verbatim}

The Activity reports that a resource changed; it does not necessarily contain a field-level diff.

Official specification: <https://iiif.io/api/discovery/1.0/>

## Content Search API 2.0

**Purpose:** searches annotations associated with a Manifest or Collection, commonly OCR/transcription text. It is search **inside known IIIF resources**, not a universal provider-discovery API.

**How to use it:**

1. Find a declared SearchService2 in the Presentation resource.
2. send its search endpoint a URL-encoded **q** parameter;
3. read the returned AnnotationPage/AnnotationCollection and **items**;
4. follow **next** pages and use Annotation targets to locate the matching Canvas or region.

\begin{Verbatim}[fontsize=\scriptsize,breaklines=true]
GET https://example.org/service/manifest/search?q=bird
\end{Verbatim}

Official specification: <https://iiif.io/api/search/2.0/>

## Registry, Collections and templates

The Registry is a directory of voluntarily registered streams, not a complete IIIF census:

\begin{Verbatim}[fontsize=\scriptsize,breaklines=true]
curl.exe -L "https://registry.iiif.io/index.json" -o registry.json
\end{Verbatim}

Verified Collection examples:

\begin{Verbatim}[fontsize=\scriptsize,breaklines=true]
curl.exe -L "https://api.digitale-sammlungen.de/iiif/presentation/v2/collection/top" -o bsb.json
curl.exe -L "https://cmoa-records-images.s3.amazonaws.com/collection/top.json" -o cmoa.json
\end{Verbatim}

Some providers require non-IIIF enumeration before Manifest retrieval: Europeana and Harvard use keyed institutional APIs; Gallica and Internet Archive expose search identifiers that can be inserted into deterministic Manifest URL templates. These adapters belong in Module 3. Credentials must stay outside Git.

~~~{=latex}
\end{multicols}
~~~

\newpage

\begin{center}
{\Large\bfseries Pipeline Diagrams}
\end{center}
\vspace{0.2em}

\begin{center}
\includegraphics[width=0.98\linewidth,height=10.6cm,keepaspectratio]{fig1_pipeline.png}\\[-0.1em]
{\small Figure 1. Seven-module IIIF harvesting pipeline}
\end{center}

\vspace{0.5em}

\begin{center}
\includegraphics[width=0.98\linewidth,height=10.6cm,keepaspectratio]{fig2_module1.png}\\[-0.1em]
{\small Figure 2. Module 1 inputs, control and outputs}
\end{center}
