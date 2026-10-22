"""Prepare isolated Module 2-4 tests for reviewed 20 October discovery routes."""
import json
from pathlib import Path

module = Path(__file__).resolve().parents[1]
code = module.parent
root = module / 'evaluation/2026-10-20_five_provider_completion'
root.mkdir(parents=True, exist_ok=True)


def save(name, value):
    path = root / name
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


selected_ids = ['provider-47cf886a2e6017f1', 'provider-47ee4f79e1a60cac',
                'provider-8798d72493175a05', 'provider-665981fb2cfa68fa',
                'provider-116ce327597310c6']
census = [json.loads(line) for line in (code / 'Module_1/data/output/providers.jsonl').read_text(encoding='utf8').splitlines() if line.strip()]
providers = [next(p for p in census if p['provider_id'] == identifier) for identifier in selected_ids]
save('providers.json', providers)
(root / 'selected_providers.jsonl').write_text(''.join(json.dumps(p, ensure_ascii=False) + '\n' for p in providers), encoding='utf8')

entries = []
for provider in providers:
    pid = provider['provider_id']
    common = {'provider_id': pid, 'provider_name': provider['name'],
              'investigation_id': '2026-10-20-five-provider-discovery',
              'investigation_document': 'knowledge/institutions/2026-10-20_five_provider_completion.md'}
    if pid == selected_ids[0]:
        recipe = {'skill_id': 'aggregator-data-manifest-to-ghent-originals',
                  'type': 'paginated_html_identifiers_to_manifest_templates',
                  'api_url': 'https://iiif.biblissima.fr/collections/search',
                  'query_parameters': {'collection': 'Ghent University Library'},
                  'record_url_attributes': ['href', 'data-manifest'],
                  'record_url_pattern': r'^https://adore\.ugent\.be/IIIF/manifests/archive\.ugent\.be(?:%3A|:)(?P<identifier>[A-Fa-f0-9-]+)$',
                  'manifest_url_templates': ['https://adore.ugent.be/IIIF/manifests/archive.ugent.be%3A{identifier}'],
                  'pagination': {'page_parameter': 'from', 'page_size_parameter': '', 'page_size': 20,
                                 'start_page': 0, 'page_step': 20, 'max_pages': 1000, 'detect_next_page': True},
                  'max_identifiers': 20000, 'request_delay_seconds': 0.6,
                  'coverage_note': 'Biblissima-indexed Ghent manuscripts only; delivery remains at the Ghent source host.'}
    elif pid == selected_ids[1]:
        recipe = {'skill_id': 'funnelback-index-to-standrews-manifests',
                  'type': 'paginated_json_identifiers_to_manifest_templates',
                  'api_url': 'https://standrews-search.funnelback.squiz.cloud/s/search.json',
                  'query_parameters': {'collection': 'standrews~sp-web-sc-photo', 'profile': '_default',
                                       'form': 'grid', 'query': 'photograph'},
                  'records_path': 'response.resultPacket.results', 'identifier_path': 'listMetadata.IRN.0',
                  'required_nonempty_paths': ['listMetadata.MultimediaIdentifier.0'],
                  'filters': [{'path': 'listMetadata.MultimediaPublish.0', 'equals': 'Yes'},
                              {'path': 'listMetadata.MultimediaType.0', 'equals': 'image'}],
                  'manifest_url_templates': ['https://collections.st-andrews.ac.uk/{identifier}/manifest'],
                  'pagination': {'page_parameter': 'start_rank', 'page_size_parameter': 'num_ranks',
                                 'page_size': 10, 'start_page': 1, 'page_step': 10, 'max_pages': 10000,
                                 'total_path': 'response.resultPacket.resultsSummary.totalMatching'},
                  'max_identifiers': 50000, 'request_delay_seconds': 2.0,
                  'coverage_note': 'Public photographic search results with published image metadata; catalogue text is not assumed OCR.'}
    else:
        name = provider['name']
        namespace = {'provider-8798d72493175a05': 'ycba/obj',
                     'provider-665981fb2cfa68fa': 'ypm/nat',
                     'provider-116ce327597310c6': 'yuag/obj'}[pid]
        query = {'AND': [{'hasDigitalImage': 1}, {'memberOf': {'name': name}}]}
        recipe = {'skill_id': 'linked-art-search-detail-to-' + namespace.split('/')[0] + '-manifests',
                  'type': 'paginated_json_identifiers_to_manifest_templates',
                  'api_url': 'https://lux.collections.yale.edu/api/search/item',
                  'query_parameters': {'q': json.dumps(query, separators=(',', ':'))},
                  'records_path': 'orderedItems', 'identifier_path': 'id',
                  'identifier_pattern': r'/data/object/(?P<identifier>[a-f0-9-]+)$',
                  'identifier_followup': {
                      'url_template': 'https://lux.collections.yale.edu/data/object/{identifier}',
                      'records_path': '$',
                      'identifier_path': 'subject_of.*.digitally_carried_by.*.access_point.*.id',
                      'identifier_pattern': r'^https://manifests\.collections\.yale\.edu/' + namespace + r'/(?P<identifier>\d+)$'},
                  'manifest_url_templates': ['https://manifests.collections.yale.edu/' + namespace + '/{identifier}'],
                  'pagination': {'page_parameter': 'page', 'page_size_parameter': 'pageLength',
                                 'page_size': 3, 'max_pages': 10000, 'total_path': 'partOf.0.totalItems'},
                  'max_identifiers': 100000, 'request_delay_seconds': 0.6,
                  'coverage_note': 'LUX memberOf institutional search with digital images; only explicit native Manifest links in the institution-specific namespace are accepted.'}
    entries.append({**common, 'skills': [recipe]})
save('new_knowledge_entries.json', entries)
save('new_endpoint_entries.json', [])
save('candidate_discovery_knowledge.json', {'knowledge_base_version': '1.0', 'providers': entries})
save('candidate_provider_endpoints.json', {'providers': []})
network = {'timeout_seconds': 30, 'retries': 1, 'backoff_seconds': 0.5, 'max_response_bytes': 67108864}
save('module2_validation.json', {'input_jsonl': str(root / 'selected_providers.jsonl'),
     'output_directory': str(root / 'validation/module2/output'), 'log_directory': str(root / 'validation/module2/log'),
     'network': network, 'run': {'delay_between_requests_seconds': 0.2}})
save('module3_validation.json', {'input_jsonl': str(root / 'validation/module2/output/checked_entry_points.jsonl'),
     'knowledge_base': str(root / 'candidate_discovery_knowledge.json'), 'curated_endpoints': str(root / 'candidate_provider_endpoints.json'),
     'output_directory': str(root / 'validation/module3/output'), 'log_directory': str(root / 'validation/module3/log'),
     'network': network, 'limits': {'max_stream_pages_per_provider': 3, 'max_collections_per_provider': 6,
                                  'max_html_pages_per_provider': 1, 'max_html_depth': 1,
                                  'max_machine_candidates_per_provider': 6, 'max_manifests_per_provider': 6},
     'html_discovery': {'enabled': False}, 'platform_discovery': {'omeka_s_probe_enabled': False}})
save('module4_validation.json', {'input_jsonl': str(root / 'validation/module3/output/manifest_urls.jsonl'),
     'raw_manifest_directory': str(root / 'validation/module4/raw_manifests'),
     'output_directory': str(root / 'validation/module4/output'), 'log_directory': str(root / 'validation/module4/log'),
     'network': network, 'run': {'force_refresh': True, 'delay_between_requests_seconds': 0.6}})
print('Prepared five providers and candidate-only discovery knowledge:', root)
