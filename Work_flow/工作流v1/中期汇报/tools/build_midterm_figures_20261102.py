"""Build editable, evidence-scoped workflow figures for the midterm report."""
from pathlib import Path
import shutil
import subprocess

base = Path(__file__).resolve().parents[1]
figures = base / "figures/2026-11-02"
figures.mkdir(parents=True, exist_ok=True)
header = '''digraph G {
graph [rankdir=TB, bgcolor="white", pad="0.18", nodesep="0.28", ranksep="0.40", fontname="Arial"];
node [shape=box, style="rounded,filled", fillcolor="#EAF2FA", color="#8CA8C0", fontname="Arial", fontsize=12, margin="0.14,0.09"];
edge [color="#45627A", arrowsize=0.7, fontname="Arial", fontsize=10];
'''
diagrams = {
"01_pipeline_overview": header + '''
sources [label="Registry | IIIF guides | Community lists | Maintained entries", fillcolor="#F5F7F9"];
{rank=same; m1; m2; m3; m4;}
{rank=same; m8; m7; m6; m5;}
m1 [label="M1: Provider census\\nKeep endpoints; select"];
m2 [label="M2: Endpoint checks\\nHTTP + content type"];
m3 [label="M3: Manifest discovery\\nSkills + recipes", fillcolor="#FFE8CE"];
m4 [label="M4: Fetch and validate\\nRaw JSON + inventory"];
m5 [label="M5: Rights classification\\nRetention + reuse"];
m6 [label="M6: Normalize and link\\nMetadata + references"];
m7 [label="M7: Common-schema export\\nRecords + links"];
m8 [label="M8: Download bundles\\nImage + JSON + text"];
output [label="Downstream OCR work: linked, traceable samples", fillcolor="#E5F2E9"];
sources -> m1; m1 -> m2 -> m3 -> m4; m4 -> m5;
m8 -> m7 -> m6 -> m5 [dir=back]; m8 -> output;
}''',
"02_module3_current_design": header + '''
input [label="M2: all checked endpoints\\nGroup by provider_id"];
subgraph cluster_methods {
label=""; color="#C5D5E3"; fontname="Arial";
direct [label="Native IIIF routes\\nManifest / Collection /\\nChange Discovery"];
recipe [label="Saved catalogue recipes\\nJSON / XML / RSS / HTML\\nPagination; IDs; URL templates"];
html [label="Bounded HTML discovery\\nDeclared links; embedded data;\\ndetail pages"];
{rank=same; direct; recipe; html;}
urls [label="Deduplicated Manifest URLs\\nProvider + discovery evidence", fillcolor="#E5F2E9"];
direct -> urls; recipe -> urls; html -> urls;
}
input -> direct; input -> recipe; input -> html;
knowledge [label="Reusable skill code + provider configuration\\nVerified facts stored in the knowledge base", fillcolor="#FFE8CE"];
knowledge -> recipe [style=dashed, label="configuration"];
investigation [label="AI-assisted investigation outside runtime\\nRead guides; inspect platform; test route", shape=note, fillcolor="#F5F7F9", fontsize=10];
investigation -> knowledge [style=dashed, label="save after verification"];
audit [label="Audit: failures; unresolved routes; truncation", shape=note, fillcolor="#F5F7F9", fontsize=10];
urls -> audit [style=dashed, arrowhead=none];
m4 [label="M4: fresh retrieval + basic structure validation\\nIndependent downstream acceptance", fillcolor="#EAF2FA"];
urls -> m4;
}''',
"03_linked_output_contract": header + '''
records [label="common_records\\nrecord_id\\nManifest; provider; metadata; rights", fillcolor="#DCEBF7"];
media [label="common_media\\nresource_id + record_id\\nCanvas ID; image URL; Image service"];
profile [label="ocr_document_profiles\\nrecord_id\\nLanguage; dates; production; evidence"];
reference [label="institution_reference_texts\\nrecord_id + alignment_scope\\nresource_id for a known page\\nReference URL / inline text; provenance", fillcolor="#FFE8CE"];
{rank=same; media; profile;}
records -> media [label="1 : many"];
records -> profile [label="1 : 1"];
records -> reference [label="1 : 0..many"];
media -> reference [label="exact page association\\nwhen resource_id is known"];
document_text [label="Document-level reference: resource_id = null\\nDo not fabricate page labels", shape=note, fillcolor="#F5F7F9", fontsize=10];
reference -> document_text [style=dashed, arrowhead=none];
}''',
"04_rights_and_reference_delivery": header + '''
graph [newrank=true];
subgraph cluster_rights {
label="Rights classification"; color="#C5D5E3"; fontname="Arial";
valid [label="M4-valid document"];
rights [label="M5: assess rights\\nPreserve evidence"];
research [label="Research-retained\\nIncludes unknown /\\nreuse-excluded", fillcolor="#E5F2E9"];
reuse [label="Reuse-eligible subset\\nCurrent policy", fillcolor="#F5F7F9"];
valid -> rights; rights -> research; rights -> reuse;
}
subgraph cluster_reference {
label="Reference availability (successful image downloads)"; color="#C5D5E3"; fontname="Arial";
export [label="M6-M7: normalize\\nand associate data"];
declared [label="Page reference\\ndeclared?", shape=diamond, fillcolor="#FFF1DF"];
attempt [label="M8: try reference\\ndownload"];
with [label="with_reference\\nImage + 3 JSON\\n+ text + provenance", fillcolor="#E5F2E9"];
failed [label="reference_failed\\nImage + 3 JSON\\nFailure recorded", fillcolor="#FBE8E5"];
without [label="without_reference\\nImage + 3 JSON"];
export -> declared;
declared -> without [label="No"]; declared -> attempt [label="Yes"];
attempt -> with [label="Success"]; attempt -> failed [label="Failed"];
}
{rank=same;valid;export;}
{rank=same;rights;declared;}
{rank=same;research;reuse;attempt;}
{rank=same;with;failed;without;}
research -> export [constraint=false, label="research handoff"];
}'''
}
dot = shutil.which("dot")
if not dot:
    raise RuntimeError("Graphviz dot is required")
for name, source in diagrams.items():
    path = figures / (name + ".dot")
    path.write_text(source, encoding="utf-8")
    for extension in ("svg", "png"):
        subprocess.run([dot, "-T" + extension, "-Gdpi=170", str(path), "-o", str(path.with_suffix("." + extension))], check=True)
    print(path.with_suffix(".png"))
