"""Fresh M1-M7 evaluation of the fixed 100 historically validated sources.

Each source gets a separate normal module configuration/output tree. The
orchestrator executes production module APIs, preserves failures and enforces a
small discovery quota. Module 8 is deliberately not called.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone, timedelta
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.parse import urlsplit
import threading

CODE = Path(__file__).resolve().parents[2]
ROOT = CODE.parent
for n in range(1,8):
    sys.path.insert(0,str(CODE/f'Module_{n}'))

def now():
    return datetime.now(timezone(timedelta(hours=1))).isoformat(timespec='seconds')

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def rows(path):
    if not path.exists():return []
    return [json.loads(line) for line in path.read_text(encoding='utf-8-sig').splitlines() if line.strip()]

def write_rows(path,values):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8') as stream:
        for value in values:stream.write(json.dumps(value,ensure_ascii=False)+'\n')

def prepare(run):
    from iiif_provider_census.pipeline import run_pipeline
    historic=CODE/'Module_3/evaluation/2026-10-22_third_seven_provider_completion/cumulative_provider_status.json'
    target={x['provider_id']:x for x in read(historic) if x['status']=='manifest_found_and_basic_structure_validated'}
    census=rows(CODE/'Module_1/data/output/providers.jsonl')
    byid={x['provider_id']:x for x in census}
    assert len(target)==100 and set(target)<=set(byid), 'Cannot reproduce exact requested 100-source cohort'
    providers=[byid[pid] for pid in sorted(target)]
    assert all(p['record_status']=='active' for p in providers)
    write(run/'cohort.json',{'created_at':now(),'providers':providers,'historical_baseline':str(historic),
        'expected_sources':100,'max_manifests_per_source':3,'module_8':'not_run',
        'scope':'Fixed 100 historically validated census entries; current live M1-M7 run, no new sources added.'})
    write(run/'input/providers.json',{'providers':providers})
    cfg={'registry_sources':[],'manual_sources':[str(run/'input/providers.json')],
         'output_directory':str(run/'module_1/output'),'log_directory':str(run/'module_1/log')}
    write(run/'configs/module_1.json',cfg)
    result=run_pipeline(run/'configs/module_1.json',institution_selection=['all'])
    write(run/'module_1/result.json',asdict(result))
    selected=rows(result.selected_providers_jsonl)
    assert len(selected)==100 and {p['provider_id'] for p in selected}==set(target)
    # Run-local caps bound broken catalogue recipes without changing reviewed KB.
    kb=read(CODE/'Module_3/config/discovery_knowledge.json')
    for provider in kb['providers']:
        for skill in provider['skills']:
            if 'max_identifiers' in skill:
                skill['max_identifiers']=min(int(skill['max_identifiers']),30)
            if isinstance(skill.get('pagination'),dict):
                skill['pagination']['max_pages']=min(int(skill['pagination'].get('max_pages',3)),3)
    write(run/'configs/discovery_knowledge.json',kb)
    for provider in selected:
        base=run/'providers'/provider['provider_id']
        write_rows(base/'input.jsonl',[provider])
        configs={}
        for n in range(2,8):
            directory=CODE/f'Module_{n}'
            value=read(directory/'config.example.json')
            assets={3:['curated_endpoints','knowledge_base','learned_knowledge_base'],5:['policy_file'],
                6:['provider_reference_sources'],7:['profile_json','record_schema_json','media_schema_json','ocr_profile_schema_json']}
            for field in assets.get(n,[]):
                if value.get(field):value[field]=str((directory/value[field]).resolve())
            value.update(output_directory=str(base/f'module_{n}/output'),log_directory=str(base/f'module_{n}/log'))
            if n==2:
                value['input_jsonl']=str(base/'input.jsonl')
                value['network'].update(timeout_seconds=20,retries=1,max_response_bytes=64*1024*1024)
                value.setdefault('run',{})['delay_between_requests_seconds']=0.2
            elif n==3:
                value.update(input_jsonl=str(base/'module_2/output/checked_entry_points.jsonl'),
                    knowledge_base=str(run/'configs/discovery_knowledge.json'))
                value.setdefault('llm_discovery',{})['enabled']=False
                value['network'].update(timeout_seconds=20,retries=1,max_response_bytes=64*1024*1024)
                value['limits'].update(max_manifests_per_provider=3,max_stream_pages_per_provider=3,
                    max_collections_per_provider=8,max_html_pages_per_provider=8,max_html_depth=3,
                    max_machine_candidates_per_provider=12)
            elif n==4:
                value.update(input_jsonl=str(base/'module_3/output/manifest_urls.jsonl'),raw_manifest_directory=str(base/'module_4/raw_manifests'))
                value['network'].update(timeout_seconds=25,retries=1,max_response_bytes=64*1024*1024)
                value.setdefault('run',{})['force_refresh']=True
            elif n==5:
                value.update(validated_manifests_jsonl=str(base/'module_4/output/validated_manifests.jsonl'),
                    resource_inventory_jsonl=str(base/'module_4/output/manifest_resource_inventory.jsonl'),
                    module_4_directory=str(base/'configs'))
            elif n==6:
                value.update(research_manifests_jsonl=str(base/'module_5/output/research_manifests.jsonl'),
                    research_resource_inventory_jsonl=str(base/'module_5/output/research_resource_inventory.jsonl'),
                    module_4_directory=str(base/'configs'))
            elif n==7:
                for field,filename in [('normalized_records_jsonl','normalized_records.jsonl'),
                    ('normalized_resources_jsonl','normalized_resources.jsonl'),
                    ('normalized_reference_texts_jsonl','normalized_reference_texts.jsonl')]:
                    value[field]=str(base/'module_6/output'/filename)
            write(base/f'configs/module_{n}.json',value)
            configs[str(n)]=str(base/f'configs/module_{n}.json')
        write(base/'job.json',{'provider_id':provider['provider_id'],'provider_name':provider['name'],
            'host':urlsplit(provider.get('institution_url') or provider['discovery_endpoint']).hostname,'configs':configs})
    return selected

def worker(run,pid):
    from iiif_entry_validator.pipeline import run_pipeline as m2
    from iiif_resource_discovery.pipeline import run_pipeline as m3
    from iiif_manifest_validator.pipeline import run_pipeline as m4
    from iiif_rights_filter.pipeline import run_pipeline as m5
    from iiif_metadata_normalizer.pipeline import run_pipeline as m6
    from iiif_common_exporter.pipeline import run_pipeline as m7
    base=run/'providers'/pid
    job=read(base/'job.json')
    result={'provider_id':pid,'provider_name':job['provider_name'],'started_at':now(),'stages':{},'status':'running'}
    write(base/'result.json',result)
    for n,func in [(2,m2),(3,m3),(4,m4),(5,m5),(6,m6),(7,m7)]:
        result['current_module']=n;write(base/'result.json',result)
        started=time.monotonic()
        try:
            value=func(Path(job['configs'][str(n)]))
            result['stages'][str(n)]={'status':'completed','seconds':round(time.monotonic()-started,3),
                'result':asdict(value) if is_dataclass(value) else value}
        except Exception as exc:
            result['stages'][str(n)]={'status':'failed','seconds':round(time.monotonic()-started,3),
                'error_type':type(exc).__name__,'error':str(exc)}
            result['status']='failed';break
        write(base/'result.json',result)
    else:result['status']='completed'
    result['finished_at']=now();write(base/'result.json',result)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--run-dir',type=Path)
    parser.add_argument('--worker')
    parser.add_argument('--workers',type=int,default=8)
    args=parser.parse_args()
    os.environ['PYTHONIOENCODING']='utf-8';os.environ['PYTHONUTF8']='1'
    run=(args.run_dir or CODE/'Pipeline_Runner/data'/('midterm_100_20261106_'+datetime.now().strftime('%H%M%S'))).resolve()
    if args.worker:
        worker(run,args.worker);return
    if (run/'cohort.json').exists():
        providers=read(run/'cohort.json')['providers']
    else:providers=prepare(run)
    write(CODE/'Pipeline_Runner/data/latest_midterm_100_run.json',{'run_directory':str(run)})
    print('RUN_DIRECTORY='+str(run),flush=True)
    print(f'M1: {len(providers)} sources selected; {sum(len(p["endpoints"]) for p in providers)} endpoints. M8 NOT RUN.',flush=True)
    host_locks={h:threading.Semaphore(2) for h in {
        urlsplit(p.get('institution_url') or p['discovery_endpoint']).hostname for p in providers}}
    def execute(provider):
        pid=provider['provider_id'];base=run/'providers'/pid
        if (base/'result.json').exists() and read(base/'result.json').get('status')=='completed':return read(base/'result.json')
        host=urlsplit(provider.get('institution_url') or provider['discovery_endpoint']).hostname
        with host_locks[host]:
            try:
                cp=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',pid,'--run-dir',str(run)],
                    capture_output=True,timeout=600,env=os.environ.copy())
                (base/'worker_stdout.txt').write_bytes(cp.stdout);(base/'worker_stderr.txt').write_bytes(cp.stderr)
                result=read(base/'result.json') if (base/'result.json').exists() else {'provider_id':pid,'provider_name':provider['name'],'stages':{}}
                if cp.returncode:
                    result.update(status='worker_failed',worker_exit_code=cp.returncode)
            except subprocess.TimeoutExpired:
                result=read(base/'result.json') if (base/'result.json').exists() else {'provider_id':pid,'provider_name':provider['name'],'stages':{}}
                result.update(status='provider_timeout',timeout_seconds=600,finished_at=now())
            write(base/'result.json',result)
            return result
    results=[]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures={pool.submit(execute,p):p for p in providers}
        for future in as_completed(futures):
            result=future.result();results.append(result)
            stages=result.get('stages',{})
            def metric(n,key):return stages.get(str(n),{}).get('result',{}).get(key,0)
            print(f'[{len(results):03d}/100] {result["provider_name"]}: M2 reachable={metric(2,"providers_with_reachable_endpoint")}; '
                f'M3 URLs={metric(3,"unique_manifest_count")}; M4 valid={metric(4,"valid_manifest_count")}; '
                f'M6 research={metric(6,"research_usable_records")}; M7 accepted={metric(7,"valid_records")}; {result["status"]}',flush=True)
            write(run/'progress.json',{'updated_at':now(),'completed_sources':len(results),'expected_sources':100,'results':results,'module_8':'not_run'})
    write(run/'provider_results.json',sorted(results,key=lambda x:x['provider_name']))
    write(run/'finished.json',{'finished_at':now(),'tested_sources':len(results),'module_8':'not_run'})
    print('COMPLETE: '+str(run),flush=True)

if __name__=='__main__':main()
