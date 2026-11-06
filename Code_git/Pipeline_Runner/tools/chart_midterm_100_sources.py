"""Summarize the fresh fixed-100-source M1-M7 run; publish PNGs only.

Provider progress always uses the full fixed 100-source denominator. Separate
record/endpoint metrics state their own denominators. Module 8 is not run.
"""
from pathlib import Path
from collections import Counter
import csv
import json
import math
import shutil

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from PIL import Image, ImageOps, ImageDraw

CODE=Path(__file__).resolve().parents[2]
ROOT=CODE.parent
RUN=Path(json.loads((CODE/'Pipeline_Runner/data/latest_midterm_100_run.json').read_text())['run_directory'])
DEST=ROOT/'Work_flow/工作流v1/中期汇报/中期汇报/Fig'
STAGE=RUN/'figures_png'
STAGE.mkdir(exist_ok=True)

def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def rows(path):
    if not path.exists():return []
    return [json.loads(s) for s in path.read_text(encoding='utf-8-sig').splitlines() if s.strip()]

cohort=read(RUN/'cohort.json')['providers']
assert len(cohort)==100 and (RUN/'finished.json').exists(),'Wait until all 100 sources finish'
results=read(RUN/'provider_results.json')
assert {p['provider_id'] for p in cohort}=={r['provider_id'] for r in results}
jobs={r['provider_id']:r for r in results}
S=[];endpoint_rows=[];rights=Counter();qualities=Counter();missing=Counter()
total=Counter();unique_urls=set();unique_valid_urls=set();unique_image_urls=set();unique_resource_ids=set()
categories_by_record={};extraction_availability=Counter();provider_refs=0
for p in sorted(cohort,key=lambda p:p['name'].casefold()):
    base=RUN/'providers'/p['provider_id']
    rr=lambda n,name:rows(base/f'module_{n}/output'/name)
    checks=rr(2,'checked_entry_points.jsonl');endpoint_rows.extend(checks)
    found=rr(3,'manifest_urls.jsonl');discovery=rr(3,'provider_discovery.jsonl')
    valid=rr(4,'validated_manifests.jsonl');inventory=rr(4,'manifest_resource_inventory.jsonl')
    research=rr(5,'research_manifests.jsonl');reuse=rr(5,'reuse_eligible_manifests.jsonl')
    normalized=rr(6,'normalized_records.jsonl');images6=rr(6,'normalized_resources.jsonl');refs6=rr(6,'normalized_reference_texts.jsonl')
    records7=rr(7,'common_records.jsonl');images7=rr(7,'common_media.jsonl');profiles=rr(7,'ocr_document_profiles.jsonl');refs7=rr(7,'institution_reference_texts.jsonl')
    assert all(x['quality'].get('research_usable') is True for x in records7)
    usable=[x for x in normalized if x['quality'].get('research_usable') is True]
    stages=jobs[p['provider_id']].get('stages',{})
    reachable=sum(c['endpoint_check']['check_result'] in {'reachable_json','reachable_non_json','invalid_json'} for c in checks)
    json_count=sum(c['endpoint_check'].get('json_parseable') is True for c in checks)
    row={'provider_id':p['provider_id'],'provider_name':p['name'],'worker_status':jobs[p['provider_id']]['status'],
        'input_endpoints':len(p['endpoints']),'checked_endpoints':len(checks),'reachable_endpoints':reachable,
        'json_endpoints':json_count,'discovered_urls':len(found),'valid_manifests':len(valid),'research_records':len(research),
        'research_usable_records':len(usable),'exported_records':len(records7),'exported_images':len(images7),
        'reference_descriptors':len(refs7),'completed_modules':[int(k) for k,v in stages.items() if v['status']=='completed']}
    S.append(row)
    for key,n in [('discovered_observations',len(found)),('valid_records',len(valid)),('m4_images',len(inventory)),
        ('research_records',len(research)),('reuse_records',len(reuse)),('normalized_records',len(normalized)),
        ('research_usable_records',len(usable)),('m6_images',len(images6)),('m6_refs',len(refs6)),
        ('exported_records',len(records7)),('exported_images',len(images7)),('profiles',len(profiles)),('refs',len(refs7))]:total[key]+=n
    unique_urls.update(x['manifest_url'] for x in found)
    unique_valid_urls.update(x['manifest_url'] for x in valid)
    unique_image_urls.update(x['image'].get('download_url') or x['image'].get('id') for x in images7)
    unique_resource_ids.update(x['resource_id'] for x in images7)
    for x in research:
        a=x['rights_assessment'];rights[a['category']]+=1
        total['research_only_records']+=a.get('public_reuse_eligible') is not True
        total['unknown_records']+=a['category']=='unknown'
    research_by_id={x['manifest_id']:x for x in research}
    for x in normalized:
        q=x['quality'];m=x['normalized_metadata'];qualities[q['status']]+=1;missing.update(q['missing_fields'])
        assert 'rights' not in q['missing_fields'],'Rights assessment incorrectly marked missing'
        assert x['quality']['research_usable'] is True,'New research usability policy not applied'
        assert m['rights']['decision']==research_by_id[x['manifest_id']]['rights_assessment']['decision']
        for key,present in [('Title',bool(m['title']['preferred'])),('Date string',bool(m['dates'])),
            ('Parsed date',any(d['normalization']['normalized'] for d in m['dates'])),
            ('Place string',any(d.get('normalized') for d in m['places'])),
            ('Language',bool(m['languages'])),('Rights assessment',bool(m['rights']['category']))]:
            extraction_availability[key]+=bool(present)
    # Source-specific observations keep aliases/aggregators from creating fake
    # unique totals. Distinct URL counts are reported separately above.
    ref_record_ids={x['record_id'] for x in refs7};ref_image_ids={x['resource_id'] for x in refs7 if x.get('resource_id')}
    total['documents_with_refs']+=len(ref_record_ids)
    total['images_with_refs']+=len(ref_image_ids)
    total['page_refs']+=sum(bool(x.get('resource_id')) for x in refs7)
    provider_refs+=bool(refs7)
    for d in discovery:
        for a in d['resource_discovery'].get('knowledge_application',[]):
            if a.get('manifest_requests') is not None and a.get('manifests_validated') is not None:
                total['template_requests']+=a['manifest_requests'];total['template_verified']+=a['manifests_validated']

progress={'M1':100,'M2':sum(x['reachable_endpoints']>0 for x in S),
    'M3':sum(x['discovered_urls']>0 for x in S),'M4':sum(x['valid_manifests']>0 for x in S),
    'M5':sum(x['research_records']>0 for x in S),'M6':sum(x['research_usable_records']>0 for x in S),
    'M7':sum(x['exported_records']>0 for x in S)}
assert total['valid_records']==total['research_records']==total['normalized_records']==total['research_usable_records']==total['exported_records']
assert total['m4_images']==total['m6_images']==total['exported_images']
assert total['m6_refs']==total['refs']

with (RUN/'provider_stage_counts.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(S[0]));writer.writeheader();writer.writerows(S)

NAVY='#193650';TEXT='#40566C';GRID='#DCE5EC';BLUE='#3976B8';GREEN='#4D9A73';ORANGE='#E9832E';RED='#C94C4C';GRAY='#8393A2';PURPLE='#8064A2'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':16,'axes.labelcolor':TEXT,
    'xtick.color':TEXT,'ytick.color':TEXT,'axes.edgecolor':TEXT,'axes.unicode_minus':False})
PROVENANCE={'date':'2026-11-06','cohort_size':100,'scope':'Fixed 100 historically validated census entries; fresh M1-M7 run',
    'run_directory':str(RUN.relative_to(ROOT)),'module_8':'not_run','max_manifests_per_source':3}
plots=[]
SUB='Live evaluation: 100 fixed sources | 2026-11-06 | Up to 3 Manifests per source'
FOOT='Source-level progress uses all 100 inputs. Record/endpoint ratios use their explicitly labelled denominators.\nThis is a bounded rerun of known sources, not an unseen-source generalization or full-catalogue harvest.'

def frame(title,subtitle=SUB,foot=FOOT,height=9,left=.36):
    fig=plt.figure(figsize=(16,height),facecolor='white')
    fig.text(.035,.953,title,ha='left',va='top',fontsize=26,fontweight='bold',color=NAVY)
    fig.text(.035,.895,subtitle,ha='left',va='top',fontsize=13,color=TEXT)
    fig.text(.035,.035,foot,ha='left',va='bottom',fontsize=10.8,color=TEXT,linespacing=1.5)
    ax=fig.add_axes([left,.20,.96-left,.61]);ax.spines[['top','right','left']].set_visible(False)
    ax.tick_params(axis='y',length=0,pad=12);ax.grid(axis='x',color=GRID);ax.set_axisbelow(True)
    return fig,ax

def save(fig,name,data):
    fig.canvas.draw();renderer=fig.canvas.get_renderer();artists=list(fig.texts)
    for ax in fig.axes:
        artists.extend(ax.texts)
        xmin,xmax=sorted(ax.get_xlim());ymin,ymax=sorted(ax.get_ylim())
        artists.extend(t for t,p in zip(ax.get_xticklabels(),ax.get_xticks()) if xmin<=p<=xmax)
        artists.extend(t for t,p in zip(ax.get_yticklabels(),ax.get_yticks()) if ymin<=p<=ymax)
    for a in artists:
        if not a.get_visible() or not a.get_text():continue
        b=a.get_window_extent(renderer)
        assert b.x0>=-1 and b.y0>=-1 and b.x1<=fig.bbox.width+1 and b.y1<=fig.bbox.height+1,(name,a.get_text())
    fig.savefig(STAGE/name,dpi=200,metadata={'Title':name,'Description':json.dumps({**PROVENANCE,'statistics':data})})
    plt.close(fig);plots.append(name)

def rate(name,title,data,subtitle=SUB,foot=FOOT,height=9):
    fig,ax=frame(title,subtitle,foot,height)
    for i,(label,n,d,color) in enumerate(data):
        assert d>=n>=0,(label,n,d)
        if d:
            v=100*n/d;ax.barh(i,v,height=.65,color=color)
            ax.text(v+1.2,i,f'{v:.1f}% ({n:,}/{d:,})',va='center',fontsize=16,fontweight='bold',color='#101010')
        else:ax.text(1,i,'N/A (no inputs)',va='center',fontsize=16,color=GRAY)
    ax.set_yticks(range(len(data)),[r[0] for r in data],fontsize=16);ax.invert_yaxis()
    ax.set_xlim(0,138);ax.set_xticks([0,20,40,60,80,100]);ax.set_xlabel('Rate (%)',labelpad=12)
    save(fig,name,[{'metric':a,'numerator':b,'denominator':c,'rate':100*b/c if c else None} for a,b,c,_ in data])

def count(name,title,data,subtitle=SUB,foot=FOOT,height=9,left=.36):
    fig,ax=frame(title,subtitle,foot,height,left);maximum=max(x[1] for x in data) or 1
    for i,(label,n,color) in enumerate(data):
        ax.barh(i,n,height=.65,color=color);ax.text(n+maximum*.018,i,f'{n:,}',va='center',fontsize=18,fontweight='bold',color='#101010')
    ax.set_yticks(range(len(data)),[x[0] for x in data],fontsize=15);ax.invert_yaxis();ax.set_xlim(0,maximum*1.22)
    ax.xaxis.set_major_locator(MaxNLocator(nbins=6,integer=True));ax.set_xlabel('Count (row units shown)',labelpad=12)
    save(fig,name,[{'metric':a,'count':b} for a,b,_ in data])

rate('00_Pipeline_Success_and_Retention.png','Module 1-7 progress across all 100 sources',[
    ('M1 | Sources selected',progress['M1'],100,BLUE),('M2 | Sources with reachable entries',progress['M2'],100,ORANGE),
    ('M3 | Sources with Manifest URLs',progress['M3'],100,GREEN),('M4 | Sources with image Manifests',progress['M4'],100,GREEN),
    ('M5 | Sources retained for research',progress['M5'],100,GREEN),('M6 | Sources normalized for research',progress['M6'],100,GREEN),
    ('M7 | Sources exported',progress['M7'],100,GREEN)],
    foot='All bars use the SAME 100-source denominator. M3 may succeed via a known API even if initial M2 entries fail.\nUnknown/reuse-excluded resources remain research-usable. Module 8 was not run; no download success is claimed.')

E=sum(len(p['endpoints']) for p in cohort)
count('01_Module1_Census_and_Selection.png','Module 1 | Fixed-cohort selection',[
    ('Frozen input sources',100,BLUE),('Sources exported by M1',100,GREEN),
    ('Sources selected for this run',100,GREEN),('Candidate endpoints preserved',E,ORANGE)],
    foot='The exact 100 historically validated census entries were frozen before testing; all their candidate endpoints were retained.\nNo new sources were added. The other 27 entries in the 127-entry census are outside this requested cohort.')

http=sum(200<=(c['endpoint_check'].get('status_code') or 0)<300 for c in endpoint_rows)
json_sources=sum(x['json_endpoints']>0 for x in S)
rate('02_Module2_Endpoint_Checks.png','Module 2 | All-cohort endpoint checks',[
    ('Candidate endpoints checked',len(endpoint_rows),E,GREEN),('Endpoint HTTP success',http,len(endpoint_rows),ORANGE),
    ('Sources with reachable entries',progress['M2'],100,ORANGE),('Sources with initial JSON',json_sources,100,BLUE)],
    subtitle=f'All 100 sources | {E} supplied endpoints | Initial HTTP/format checks only',
    foot='HTTP success is per endpoint; provider reachability/JSON availability are per source, each out of 100.\nXML and HTML may still support discovery. Known M3 catalogue routes can work when a supplied homepage fails.')

rate('03_Module3_Manifest_Discovery.png','Module 3 | Fresh discovery over 100 sources',[
    ('Sources with Manifest URLs',progress['M3'],100,GREEN),
    ('Template candidate checks',total['template_verified'],total['template_requests'],ORANGE)],
    subtitle=f'100 fixed inputs | {total["discovered_observations"]:,} source-Manifest observations | {len(unique_urls):,} unique Manifest URLs',
    foot='Source success requires at least one discovered URL, not an entire catalogue. Template checks cover only logged template candidates.\nKnown-source evaluation with reviewed recipes; all unresolved and failed cases remain in the denominator.')

rate('04_Module4_Manifest_Validation.png','Module 4 | Fresh Manifest validation',[
    ('Sources with accepted image Manifests',progress['M4'],100,GREEN),
    ('Manifest observations accepted',total['valid_records'],total['discovered_observations'],ORANGE)],
    subtitle=f'{total["discovered_observations"]:,} source-Manifest inputs | {total["valid_records"]:,} valid observations | {len(unique_valid_urls):,} unique valid URLs',
    foot='Force refresh was enabled. Acceptance requires basic structure and image bodies for the downstream OCR workflow.\nA valid IIIF video/audio Manifest can fall outside this image pipeline; actual image downloads are not tested here.')

rate('05_Module5_Rights_and_Retention.png','Module 5 | Research retention under the current policy',[
    ('Sources retained for research',progress['M5'],100,GREEN),
    ('Validated records retained',total['research_records'],total['valid_records'],GREEN),
    ('Research-only records retained',total['research_only_records'],total['research_only_records'],GREEN),
    ('Public-reuse eligible (separate)',total['reuse_records'],total['research_records'],BLUE)],
    subtitle=f'{total["research_records"]:,} research records | Unknown and public-reuse-excluded records included',
    foot='Research usability does NOT require public-reuse permission. Original rights categories and restrictions remain attached.\nPublic distribution/commercial flags are separate; the eligibility fraction is not a research rejection rate.')

rate('06_Module6_Normalization_and_Completeness.png','Module 6 | Research usability and normalization',[
    ('Sources normalized for research',progress['M6'],100,GREEN),
    ('Research-usable normalized records',total['research_usable_records'],total['research_records'],GREEN),
    ('Image associations normalized',total['m6_images'],total['m4_images'],GREEN)],
    subtitle=f'{total["normalized_records"]:,} documents | {total["m6_images"]:,} image associations | {total["m6_refs"]:,} text references',
    foot='NEW RULE: unknown/reuse-excluded rights do not make a record unusable or a rights field missing.\nDate/place gaps remain metadata annotations, not research rejection. Descriptive field availability is plotted separately.')

rate('07_Module7_Common_Schema_Export.png','Module 7 | Common-schema export',[
    ('Sources with exported records',progress['M7'],100,GREEN),
    ('Document observations accepted',total['exported_records'],total['normalized_records'],GREEN),
    ('Image associations accepted',total['exported_images'],total['m6_images'],GREEN),
    ('Reference descriptors accepted',total['refs'],total['m6_refs'],GREEN)],
    subtitle=f'{total["exported_records"]:,} document observations | {total["exported_images"]:,} image associations | {total["profiles"]:,} OCR profiles',
    foot='A shared Manifest may appear under more than one source; observation counts are not claimed to be unique objects.\nThe current common schema accepts research-retained records without requiring public-reuse permission.')

fig=plt.figure(figsize=(16,9),facecolor='white')
fig.text(.055,.89,'Module 8 | Not run in this evaluation',fontsize=30,fontweight='bold',color=NAVY)
fig.text(.055,.63,'Requested scope: 100 sources, Modules 1-7',fontsize=25,color=TEXT)
fig.text(.055,.45,'No image download test was executed.\nNo download success percentage is reported.',fontsize=24,color=GRAY,linespacing=1.7)
fig.text(.055,.14,'Manifest-declared image links and reference descriptors were exported by M7.\nThey are not counted as downloaded files.',fontsize=16,color=TEXT,linespacing=1.6)
save(fig,'08_Module8_Not_Run.png',{'status':'not_run','reason':'Explicit user instruction'})

count('09_100_Source_Cohort_and_Scope.png','Fixed cohort and current discovery outcome',[
    ('Full census (entries)',127,GRAY),('Fixed cohort tested',100,BLUE),
    ('Outside the requested cohort',27,GRAY),('Manifest found in current cohort',progress['M3'],GREEN),
    ('Unresolved in current cohort',100-progress['M3'],RED)],
    foot='100/127 describes cohort selection from historical evidence, not today\'s discovery success.\nToday\'s source discovery rate is shown against all 100 tested inputs; existing aliases/projects remain in this census.')

formats=Counter()
for c in endpoint_rows:
    e=c['endpoint_check'];kind=str(e.get('content_type') or '').lower()
    if e.get('check_result') not in {'reachable_json','reachable_non_json','invalid_json'}:label='Unavailable / restricted / bounded'
    elif e.get('json_parseable') is True:label='Reachable JSON'
    elif 'xml' in kind:label='Reachable XML'
    elif 'html' in kind:label='Reachable HTML'
    else:label='Other reachable response'
    formats[label]+=1
count('10_Module2_Response_Types.png','Module 2 | Endpoint response categories',[
    (k,formats[k],c) for k,c in [('Reachable JSON',BLUE),('Reachable XML',ORANGE),('Reachable HTML',GREEN),
        ('Other reachable response',PURPLE),('Unavailable / restricted / bounded',RED)]],
    subtitle=f'All {len(endpoint_rows)} checked endpoint rows across the fixed 100 sources',
    foot='Categories describe initial endpoint checks, including bounded-response or access failures.\nThey do not by themselves determine whether M3 can use a different documented catalogue route.')

count('11_Module5_Rights_Categories.png','Module 5 | Rights evidence retained for research',[
    (k.replace('_',' ').title(),n,ORANGE if k=='unknown' else BLUE) for k,n in rights.most_common()],
    subtitle=f'{total["research_records"]:,} research-retained source-Manifest observations',
    foot='Every category is retained for the project\'s research handoff, including unknown and public-reuse-excluded categories.\nOriginal evidence and public-use restrictions are preserved; category counts are not research rejection counts.',height=max(9,len(rights)*.55+3))

ranked=sorted(S,key=lambda x:x['exported_images'],reverse=True)[:20]
count('12_Image_Yield_by_Source.png','Image associations | Top 20 of the 100 tested sources',[
    (x['provider_name'] if len(x['provider_name'])<45 else x['provider_name'][:42]+'...',x['exported_images'],BLUE) for x in ranked],
    subtitle=f'All-source total: {total["exported_images"]:,} associations | {len(unique_image_urls):,} distinct download URLs | No images downloaded',
    foot='Ranking is computed from all 100 sources. Only the top 20 labels are displayed; full per-source outcomes are included separately.\nCounts describe the up-to-3-Manifest samples, not entire catalogues or guaranteed downloadable images.',height=14,left=.41)

rate('13_OCR_Reference_Availability.png','Reference-text declarations and page linkage',[
    ('Sources with reference declarations',provider_refs,100,BLUE),
    ('Documents with text references',total['documents_with_refs'],total['exported_records'],BLUE),
    ('Images with declared page references',total['images_with_refs'],total['exported_images'],BLUE),
    ('Descriptors linked to a page',total['page_refs'],total['refs'],GREEN)],
    subtitle=f'All 100 source inputs | {total["refs"]:,} declared reference observations',
    foot='These are declared references/ID linkages, not M8 downloads or certified correct transcription labels.\nDocument-level references are kept without invented page alignment. Module 8 was not run.')

rate('14_Metadata_Field_Availability.png','M6 descriptive fields | Separate from research usability',[
    (label,n,total['normalized_records'],BLUE) for label,n in extraction_availability.items()],
    subtitle=f'{total["normalized_records"]:,} normalized document observations | Current field extraction rules',
    foot='This measures non-empty extracted fields, not a gate for research usage or a semantic accuracy score.\nUnknown rights are a recorded assessment; missing dates/places remain explicit and do not discard records.')

for page in range(5):
    subset=S[page*20:(page+1)*20]
    fig=plt.figure(figsize=(18,11),facecolor='white')
    fig.text(.035,.95,f'All-source stage results | {page*20+1}-{page*20+len(subset)} of 100',fontsize=25,fontweight='bold',color=NAVY)
    fig.text(.035,.90,'Fresh 2026-11-06 run | Counts are successful outputs, not merely process exit codes',fontsize=13,color=TEXT)
    ax=fig.add_axes([.035,.16,.93,.69]);ax.axis('off')
    table_data=[];colors=[]
    fields=['reachable_endpoints','discovered_urls','valid_manifests','research_records','research_usable_records','exported_records']
    for row in subset:
        vals=[row[k] if module in row['completed_modules'] else None for module,k in zip(range(2,8),fields)]
        table_data.append([row['provider_name']]+[str(n) if n is not None else 'Not completed' for n in vals])
        colors.append(['white']+[('#D9EFE3' if n else '#F7DAD8') if n is not None else '#E2E6EA' for n in vals])
    table=ax.table(cellText=table_data,cellColours=colors,
        colLabels=['Source','M2 reachable\nendpoints','M3 Manifest\nURLs','M4 valid\nManifests','M5 research\nrecords','M6 research\nusable','M7 exported\nrecords'],
        colWidths=[.43]+[.095]*6,cellLoc='center',loc='center',bbox=[0,0,1,1])
    table.auto_set_font_size(False);table.set_fontsize(11.5)
    for (r,c),cell in table.get_celld().items():
        cell.set_edgecolor('#D7DFE7');cell.set_linewidth(.6)
        if r==0:cell.set_facecolor(NAVY);cell.set_text_props(color='white',weight='bold')
        elif c==0:cell.set_text_props(ha='left',color=TEXT)
    fig.text(.035,.055,'Green: at least one output | Red: zero | Gray: stage did not finish. M8 excluded.\nA known M3 API route can succeed even when the initial M2 endpoint is unavailable.',fontsize=12,color=TEXT,linespacing=1.5)
    save(fig,f'15_Source_Stage_Results_{page+1:02d}_of_05.png',subset)

outcome={'provenance':PROVENANCE,'provider_progress':progress,'counts':dict(total),
    'unique_manifest_urls_discovered':len(unique_urls),'unique_manifest_urls_validated':len(unique_valid_urls),
    'distinct_image_download_urls':len(unique_image_urls),'distinct_resource_ids':len(unique_resource_ids),
    'endpoint_checks':len(endpoint_rows),'supplied_endpoints':E,'http_successes':http,'json_sources':json_sources,
    'rights_categories':dict(rights),'metadata_quality':dict(qualities),'metadata_missing_fields':dict(missing),
    'field_availability':dict(extraction_availability),'module_8':'not_run',
    'source_failures':[x for x in S if x['exported_records']==0],'png_files':plots}
(RUN/'evaluation_summary.json').write_text(json.dumps(outcome,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

# Replace only figures made by the previous statistics job; preserve unrelated
# user images. Old seven-source results must not remain as the current summary.
DEST.mkdir(parents=True,exist_ok=True)
for old in DEST.glob('*.png'):
    try:
        with Image.open(old) as im:meta=json.loads(im.info.get('Description','{}'))
    except (ValueError,OSError):continue
    managed=('2026-10-22_third_seven_provider_completion' in str(meta.get('source_directory',''))
        or str(meta.get('run_directory','')).startswith('Code_git'))
    if managed and old.name not in plots:old.unlink()
for name in plots:shutil.copy2(STAGE/name,DEST/name)
assert all(p.suffix.lower() in {'.png','.jpg','.jpeg'} for p in DEST.iterdir() if p.is_file())

for start in range(0,len(plots),6):
    subset=plots[start:start+6];sheet=Image.new('RGB',(1440,450*math.ceil(len(subset)/3)),'#dddddd');draw=ImageDraw.Draw(sheet)
    for i,name in enumerate(subset):
        with Image.open(STAGE/name) as source:thumb=ImageOps.contain(source.convert('RGB'),(460,410))
        x=(i%3)*480+(480-thumb.width)//2;y=(i//3)*450+30
        sheet.paste(thumb,(x,y));draw.text(((i%3)*480+8,(i//3)*450+8),name,fill='black')
    sheet.save(RUN/f'chart_review_{start//6+1}.png')
print(json.dumps({k:v for k,v in outcome.items() if k not in {'png_files','source_failures'}},ensure_ascii=False,indent=2))
print('PNGs published:',len(plots),'in',DEST)
