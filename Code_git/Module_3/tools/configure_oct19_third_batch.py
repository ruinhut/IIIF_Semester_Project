"""Prepare five source routes without replacing any existing learned recipe."""
import json
from pathlib import Path


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    module = Path(__file__).resolve().parents[1]
    code = module.parent
    root = module / 'evaluation/2026-10-19_third_five_provider_completion'
    ids = ['provider-f034696f3b1f1c1f', 'provider-4853865a686721d7', 'provider-7781a87376497b5c',
           'provider-a1544ec8d50c2696', 'provider-c94006b2714289d6']
    census = [json.loads(l) for l in (code / 'Module_1/data/output/providers.jsonl').read_text(encoding='utf-8').splitlines()]
    providers = [next(p for p in census if p['provider_id'] == identifier) for identifier in ids]
    doc = 'knowledge/institutions/2026-10-19_third_provider_completion.md'
    knowledge = json.loads((root / 'before_discovery_knowledge.json').read_text(encoding='utf-8'))
    endpoints = json.loads((root / 'before_provider_endpoints.json').read_text(encoding='utf-8'))
    new_knowledge = [
        {'provider_id': ids[1], 'provider_name': providers[1]['name'], 'investigation_id': '2026-10-19-puam-documented-object-api',
         'investigation_document': doc, 'skills': [{
             'skill_id': 'documented-object-api-to-object-manifest', 'type': 'paginated_json_identifiers_to_manifest_templates',
             'api_url': 'https://data.artmuseum.princeton.edu/objects', 'records_path': 'hits.hits',
             'identifier_path': '_source.objectid', 'required_nonempty_paths': ['_source.primaryimage'],
             'query_parameters': {'maker': 5560},
             'pagination': {'page_parameter': 'from', 'page_size_parameter': 'size', 'page_size': 3,
                            'start_page': 0, 'page_step': 3, 'max_pages': 1000},
             'manifest_url_templates': ['https://data.artmuseum.princeton.edu/iiif/objects/{identifier}'],
             'max_identifiers': 10000, 'request_delay_seconds': 0.6,
             'coverage_note': 'Official API requires a supported filter. Validated scope is maker 5560 (Edgar Degas), not the entire museum. Other documented maker/department filters remain configuration.'}]},
        {'provider_id': ids[2], 'provider_name': providers[2]['name'], 'investigation_id': '2026-10-19-ucla-blacklight-ark',
         'investigation_document': doc, 'skills': [{
             'skill_id': 'blacklight-work-arks-to-native-manifests', 'type': 'paginated_json_identifiers_to_manifest_templates',
             'api_url': 'https://digital.library.ucla.edu/catalog.json', 'records_path': 'data', 'identifier_path': 'id',
             'filters': [{'path': 'type', 'equals': 'Work'}], 'query_parameters': {'q': 'map'},
             'pagination': {'page_parameter': 'page', 'page_size_parameter': 'per_page', 'page_size': 3,
                            'start_page': 1, 'max_pages': 1000, 'has_next_path': 'links.next'},
             'manifest_url_templates': ['https://iiif.library.ucla.edu/{identifier}/manifest'],
             'max_identifiers': 10000, 'request_delay_seconds': 0.6,
             'coverage_note': 'URL-encode the complete ARK, including colon and slashes. Scope is the public map query; non-Work catalogue records are skipped.'}]},
        {'provider_id': ids[4], 'provider_name': providers[4]['name'], 'investigation_id': '2026-10-19-smithsonian-official-features',
         'investigation_document': doc, 'skills': [{
             'skill_id': 'official-feature-page-to-declared-manifest-links', 'type': 'paginated_html_identifiers_to_manifest_templates',
             'api_url': 'https://iiif.si.edu/featured/index.html',
             'allow_legacy_shared_canvas': True,
             'record_url_pattern': r'^https://iiif\.si\.edu/manifests/(?P<identifier>[^/?#]+\.json)$',
             'manifest_url_templates': ['https://iiif.si.edu/manifests/{identifier}'],
             'pagination': {'page_parameter': '', 'page_size_parameter': '', 'page_size': 100, 'max_pages': 1},
             'max_identifiers': 100, 'request_delay_seconds': 0.6,
             'coverage_note': 'Official curated featured manifests, not Smithsonian-wide catalogue enumeration or all individual objects.'}]},
    ]
    new_endpoints = [
        {'provider_id': ids[0], 'provider_name': providers[0]['name'],
         'entry_points': ['https://repository.dri.ie/iiif/collection/b564jg065.json'], 'html_seeds': [],
         'investigation_id': '2026-10-19-dri-hingston-collection', 'evidence_directory': 'evaluation/2026-10-19_third_five_provider_completion',
         'coverage_note': 'Hingston nested collection: public scholarly access; no claim of DRI-wide enumeration or publication permission.'},
        {'provider_id': ids[3], 'provider_name': providers[3]['name'],
         'entry_points': ['https://scta.info/iiif/plaoulcommentary/collection', 'https://scta.info/iiif/PetrusGracilis/collection'],
         'html_seeds': [], 'investigation_id': '2026-10-19-scta-text-collections',
         'evidence_directory': 'evaluation/2026-10-19_third_five_provider_completion',
         'coverage_note': 'Public SCTA text collections, with source image-service availability checked separately. Not all SCTA texts.'},
    ]
    for current, additions in [(knowledge, new_knowledge), (endpoints, new_endpoints)]:
        for entry in additions:
            assert not any(p['provider_id'] == entry['provider_id'] for p in current['providers'])
            current['providers'].append(entry)
    for name, value in [('providers.json', providers), ('candidate_discovery_knowledge.json', knowledge),
                        ('candidate_provider_endpoints.json', endpoints), ('new_knowledge_entries.json', new_knowledge),
                        ('new_endpoint_entries.json', new_endpoints)]:
        save(root / name, value)
    checked = [json.loads(l) for l in (code / 'Module_2/data/output/checked_entry_points.jsonl').read_text(encoding='utf-8').splitlines()]
    selected = [p for p in checked if p['provider_id'] in ids]
    assert len(selected) == 5
    (root / 'checked_selected.jsonl').write_text(''.join(json.dumps(p, ensure_ascii=False) + '\n' for p in selected), encoding='utf-8')
    network = {'timeout_seconds': 25, 'retries': 0, 'max_response_bytes': 64 * 1024 * 1024}
    save(root / 'module3_validation.json', {
        'input_jsonl': str(root / 'checked_selected.jsonl'), 'knowledge_base': str(root / 'candidate_discovery_knowledge.json'),
        'curated_endpoints': str(root / 'candidate_provider_endpoints.json'), 'network': network,
        'output_directory': str(root / 'validation/module3/output'), 'log_directory': str(root / 'validation/module3/log'),
        'limits': {'max_stream_pages_per_provider': 10, 'max_collections_per_provider': 30, 'max_html_pages_per_provider': 1,
                   'max_html_depth': 1, 'max_machine_candidates_per_provider': 10, 'max_manifests_per_provider': 6},
        'html_discovery': {'enabled': False}, 'platform_discovery': {'omeka_s_probe_enabled': False}})
    save(root / 'module4_validation.json', {
        'input_jsonl': str(root / 'validation/module3/output/manifest_urls.jsonl'), 'network': network,
        'raw_manifest_directory': str(root / 'validation/module4/raw_manifests'),
        'output_directory': str(root / 'validation/module4/output'), 'log_directory': str(root / 'validation/module4/log'),
        'run': {'force_refresh': True, 'delay_between_requests_seconds': 0.6}})


if __name__ == '__main__':
    main()
