"""Prepare reviewed provider recipes; promotion requires downstream proof."""
from copy import deepcopy
import json
from pathlib import Path


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    module = Path(__file__).resolve().parents[1]
    code = module.parent
    root = module / 'evaluation/2026-10-19_resumed_five_provider_completion'
    ids = ['provider-4e06374e85489c6e', 'provider-5bb54fcb57aa7da9', 'provider-d14fb88cde24ff49',
           'provider-648f0743acabd9c2', 'provider-f10ea7c297cd81a8']
    census = [json.loads(s) for s in (code / 'Module_1/data/output/providers.jsonl').read_text(encoding='utf-8').splitlines()]
    providers = [next(p for p in census if p['provider_id'] == i) for i in ids]
    knowledge = json.loads((root / 'before_discovery_knowledge.json').read_text(encoding='utf-8'))
    endpoints = json.loads((root / 'before_provider_endpoints.json').read_text(encoding='utf-8'))
    doc = 'knowledge/institutions/2026-10-19_resumed_provider_completion.md'
    entries = [
        {'provider_id': ids[0], 'provider_name': providers[0]['name'],
         'investigation_id': '2026-10-19-princeton-blacklight-detail', 'investigation_document': doc,
         'skills': [{'skill_id': 'blacklight-results-to-declared-figgy-manifests',
             'type': 'paginated_json_identifiers_to_manifest_templates',
             'api_url': 'https://dpul.princeton.edu/papyri/catalog.json', 'records_path': 'data',
             'identifier_path': 'links.self', 'identifier_pattern': r'/catalog/(?P<identifier>[^/?#]+)$',
             'query_parameters': {'q': 'papyrus', 'search_field': 'all_fields'},
             'pagination': {'page_parameter': 'page', 'page_size_parameter': 'per_page', 'page_size': 3, 'max_pages': 1000,
                            'has_next_path': 'links.next'}, 'max_identifiers': 10000,
             'identifier_followup': {'url_template': 'https://dpul.princeton.edu/papyri/catalog/{identifier}.json',
                 'records_path': 'response.document', 'identifier_path': 'content_metadata_iiif_manifest_field_ssi',
                 'identifier_pattern': r'/concern/scanned_resources/(?P<identifier>[0-9a-f-]+)/manifest$'},
             'manifest_url_templates': ['https://figgy.princeton.edu/concern/scanned_resources/{identifier}/manifest'],
             'request_delay_seconds': 0.5,
             'coverage_note': 'Validated scope: public papyri search, not every Princeton digital collection.'}]},
        {'provider_id': ids[2], 'provider_name': providers[2]['name'],
         'investigation_id': '2026-10-19-harvard-librarycloud', 'investigation_document': doc,
         'skills': [{'skill_id': 'librarycloud-mods-declared-manifest-links',
             'type': 'paginated_json_manifest_links', 'api_url': 'https://api.lib.harvard.edu/v2/items.json',
             'records_path': 'items.mods', 'manifest_url_path': 'location.*.url.#text',
             'manifest_url_pattern': r'^https://iiif\.lib\.harvard\.edu/manifests/(?:drs|ids):[0-9]+$',
             'query_parameters': {'q': 'iiif.lib.harvard.edu'},
             'pagination': {'page_parameter': 'start', 'page_size_parameter': 'limit', 'page_size': 3,
                            'start_page': 0, 'page_step': 3, 'max_pages': 1000},
             'request_delay_seconds': 1.0,
             'coverage_note': 'MODS location URLs; object-shaped url values. Array-shaped url values use the second recipe.'},
            {'skill_id': 'librarycloud-mods-array-manifest-links',
             'type': 'paginated_json_manifest_links', 'api_url': 'https://api.lib.harvard.edu/v2/items.json',
             'records_path': 'items.mods', 'manifest_url_path': 'location.*.url.*.#text',
             'manifest_url_pattern': r'^https://iiif\.lib\.harvard\.edu/manifests/(?:drs|ids):[0-9]+$',
             'query_parameters': {'q': 'iiif.lib.harvard.edu'},
             'pagination': {'page_parameter': 'start', 'page_size_parameter': 'limit', 'page_size': 3,
                            'start_page': 0, 'page_step': 3, 'max_pages': 1000},
             'request_delay_seconds': 1.0}]},
    ]
    endpoint_entries = [{'provider_id': ids[1], 'provider_name': providers[1]['name'],
                        'entry_points': ['https://digital.library.unt.edu/explore/collections/UNTPC/top',
                                         'https://digital.library.unt.edu/explore/collections/UNTSW/top'],
                        'html_seeds': [], 'investigation_id': '2026-10-19-unt-documented-collection-api',
                        'evidence_directory': 'evaluation/2026-10-19_resumed_five_provider_completion'}]
    for skill in entries[1]['skills']:
        skill['html_migration'] = {'max_hops': 2, 'url_pattern': r'^https://(?:nrs|iiif)\.lib\.harvard\.edu/'}
        skill['pagination']['max_pages'] = 100
    entries.extend([
        {'provider_id': ids[3], 'provider_name': providers[3]['name'],
         'investigation_id': '2026-10-19-stanford-declared-original-manifests', 'investigation_document': doc,
         'skills': [{'skill_id': 'contribution-index-to-original-provider-manifests',
             'type': 'paginated_json_manifest_links', 'api_url': 'https://fromthepage.com/iiif/contributions/stanford.edu',
             'records_path': 'manifests', 'manifest_url_path': 'metadata.*.value',
             'manifest_url_pattern': r'^https://purl\.stanford\.edu/[a-z0-9]+/iiif/manifest$',
             'pagination': {'page_parameter': '', 'page_size_parameter': '', 'page_size': 10000, 'max_pages': 1},
             'request_delay_seconds': 0.6,
             'coverage_note': 'Enumerates only Stanford originals declared in the public FromThePage contribution index. Not the whole Stanford catalogue. Original PURL Manifests, not synthetic manifests, are fetched.'}]},
        {'provider_id': ids[4], 'provider_name': providers[4]['name'],
         'investigation_id': '2026-10-19-biblissima-manifest-catalogue', 'investigation_document': doc,
         'skills': [{'skill_id': 'aggregated-catalogue-to-declared-irht-manifests',
             'type': 'paginated_html_identifiers_to_manifest_templates',
             'api_url': 'https://iiif.biblissima.fr/collections/search',
             'record_url_pattern': r'https://api\.irht\.cnrs\.fr/ark:/63955/(?P<identifier>[^/?#]+)/manifest\.json(?:$|[?#])',
             'manifest_url_templates': ['https://api.irht.cnrs.fr/ark:/63955/{identifier}/manifest.json'],
             'pagination': {'page_parameter': 'from', 'page_size_parameter': '', 'page_size': 20,
                            'start_page': 0, 'page_step': 20, 'max_pages': 1000, 'detect_next_page': True},
             'max_identifiers': 20000, 'request_delay_seconds': 0.6,
             'coverage_note': 'Biblissima is an aggregator. Current executable recipe covers the explicitly linked IRHT Manifest namespace; other repositories are not yet asserted resolved.'}]},
    ])
    # Never replace old provider knowledge while investigating a new source.
    for entry in entries:
        assert not any(p['provider_id'] == entry['provider_id'] for p in knowledge['providers'])
        knowledge['providers'].append(entry)
    for entry in endpoint_entries:
        assert not any(p['provider_id'] == entry['provider_id'] for p in endpoints['providers'])
        endpoints['providers'].append(entry)
    save(root / 'providers.json', providers)
    save(root / 'new_knowledge_entries.json', entries)
    save(root / 'new_endpoint_entries.json', endpoint_entries)
    save(root / 'candidate_discovery_knowledge.json', knowledge)
    save(root / 'candidate_provider_endpoints.json', endpoints)
    checked = [json.loads(s) for s in (code / 'Module_2/data/output/checked_entry_points.jsonl').read_text(encoding='utf-8').splitlines()]
    (root / 'checked_selected.jsonl').write_text(''.join(json.dumps(p, ensure_ascii=False) + '\n' for p in checked if p['provider_id'] in ids), encoding='utf-8')
    network = {'timeout_seconds': 25, 'retries': 0, 'max_response_bytes': 64 * 1024 * 1024}
    config = {'input_jsonl': str(root / 'checked_selected.jsonl'),
              'knowledge_base': str(root / 'candidate_discovery_knowledge.json'), 'curated_endpoints': str(root / 'candidate_provider_endpoints.json'),
              'output_directory': str(root / 'validation/module3/output'), 'log_directory': str(root / 'validation/module3/log'),
              'network': network, 'limits': {'max_stream_pages_per_provider': 5, 'max_collections_per_provider': 10,
                  'max_html_pages_per_provider': 1, 'max_html_depth': 1, 'max_machine_candidates_per_provider': 10, 'max_manifests_per_provider': 6},
              'html_discovery': {'enabled': False}, 'platform_discovery': {'omeka_s_probe_enabled': False}}
    save(root / 'module3_validation.json', config)
    save(root / 'module4_validation.json', {'input_jsonl': str(root / 'validation/module3/output/manifest_urls.jsonl'),
         'raw_manifest_directory': str(root / 'validation/module4/raw_manifests'), 'output_directory': str(root / 'validation/module4/output'),
         'log_directory': str(root / 'validation/module4/log'), 'network': network,
         'run': {'force_refresh': True, 'delay_between_requests_seconds': 0.6}})


if __name__ == '__main__':
    main()
