# Project context and authoritative facts

## Student and status

- Student: Boheng Shang.
- Status: Bachelor exchange student in Computer Science at EPFL for Autumn 2026.
- Home-university major: Artificial Intelligence.
- The DHLAB project has been accepted on the project side. Kaplan wrote that the project was available and invited Boheng to the kickoff; the group invitation welcomed students who were taking on semester or master's projects.
- “Kick-off” means the project launch meeting, not a selection or elimination meeting.
- Administrative registration remains separate from project-side acceptance.

## Authoritative local sources

- Teacher project PDF: `E:\exchange-epfl\Semester_Project\Work_flow\工作目标与工作流程.pdf`
  - Boheng's individual sheet is pages 59–60.
  - Its title is “One door to a scattered heritage.”
- Teacher email: `E:\exchange-epfl\Semester_Project\Work_flow\教授的信.txt`
- Maintained project guide:
  - `E:\exchange-epfl\Semester_Project\Work_flow\IIIF项目内容与工作流程.md`
  - `E:\exchange-epfl\Semester_Project\Work_flow\IIIF项目内容与工作流程.pdf`
- Broad public project page: `https://www.epfl.ch/labs/dhlab/index-html/student-projects/`
- IIIF official site: `https://iiif.io/`
- Time Atlas: `https://timeatlas.eu/`

If these sources conflict, use the latest supervisor communication first, then the individual sheet. The broad public page describes the whole group project and is not the final definition of Boheng's personal contribution.

## Personal assignment

The individual goal is to identify institutions publishing heritage through IIIF and build a unified, rights-filtered harvest across providers. Records must enter the team's common schema so scattered heritage can be accessed through one consistent entry point.

Boheng owns the front half of the pipeline:

1. Census institutions and IIIF providers.
2. Record their discovery endpoints, estimated scale, and rights situation.
3. Discover and retrieve manifests through common IIIF mechanisms.
4. Filter records according to confirmed rights rules.
5. Normalize at least identifier, date, place, rights, and source.
6. Deliver a schema-conformant dataset slice for downstream work and Time Atlas.

“Front” means the front half of the data pipeline. It does not mean web front-end development.

## Team relationships

- Frédéric Kaplan: main supervisor.
- Ziyi Liu: co-supervisor. Ziyi's PhD work is an OCR-free search engine for IIIF resources and is an anchor for the project.
- Hafidz Arsha: downstream teammate responsible for extracting content from what Boheng harvests.
- Kaile: provides or coordinates the common schema into which Boheng's records land.
- Boheng's harvest and Hafidz's extraction form one pipeline but remain separately gradable. Hafidz can start on a public sample before Boheng's harvest is complete.

## Teacher-stated sources

Start with aggregators because they expose many providers:

- Europeana, including its Change Discovery interface.
- IIIF Registry of Activity Streams.
- Biblissima for manuscripts and rare books.

Then consider major reservoirs and open museums:

- Internet Archive.
- Gallica.
- Library of Congress.
- David Rumsey Map Collection.
- Other open museums and libraries.

Filter on rights before performing expensive downstream harvesting or content processing.

## Registration

- IS-Academia subject: Specific project for exchange/visiting student.
- Project title: `IIIF Document Information Extraction`.
- Main supervisor: Frédéric Kaplan.
- Co-supervisor: Ziyi Liu.
- ECTS value was to be confirmed with the supervisor; do not invent it.
- Administrative comments can normally remain blank unless the supervisor or administration asks for content.

## Fixed events and deadlines

- Time Atlas introduction:
  - Wednesday 16 September 2026, 13:00–15:00, CM1100.
  - Thursday 17 September 2026, 10:00–12:00, BC03.
  - Optional laboratory: Thursday 17 September 2026, 13:00–15:00, BC04.
- Weekly IIIF supervision:
  - First session: Tuesday 22 September 2026.
  - Every Tuesday, 11:00–11:20, INN 128.
  - Remote link: `https://epfl.zoom.us/j/2693459226`.
  - Attend only the IIIF group's slot.
  - A previous calendar update cancelled the 27 October session; follow the latest calendar invitation if this changes.
- Mid-term presentation: Monday 9 November 2026, all day.
- Report deadline: Friday 8 January 2027.
- Final presentation: Monday 18 January 2027.
- Kaplan travels from 14–21 September 2026, so replies may be slow. Urgent matters can go to Alicia Foucart at `alicia.foucart@epfl.ch`.

## Scope and expectations

A ten-manifest script is only the first working baseline. A semester-level result should add meaningful coverage, rights handling, metadata normalization, reliability, evaluation, reproducibility, and team integration.

The assignment is mainly data engineering and digital-humanities infrastructure. It is not primarily a computer-vision project. If Boheng wants more machine-learning content, the safest route is to complete the core pipeline and ask whether a related extension—such as metadata quality assessment or assisted normalization—can be added without duplicating Hafidz's contribution.

