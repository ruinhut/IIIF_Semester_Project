"""Freeze an isolated baseline and probe the next unresolved source group."""
import json
from pathlib import Path


def main():
    module = Path(__file__).resolve().parents[1]
    root = module / 'evaluation/2026-10-19_third_five_provider_completion'
    root.mkdir(parents=True, exist_ok=True)
    for name in ['discovery_knowledge.json', 'provider_endpoints.json']:
        path = root / ('before_' + name)
        if not path.exists():
            path.write_bytes((module / 'config' / name).read_bytes())
    targets = [
        ('Digital Repository of Ireland', 'Public search JSON', 'https://repository.dri.ie/catalog.json?q=photograph&per_page=5'),
        ('Digital Repository of Ireland', 'Published IIIF collection example', 'https://repository.dri.ie/iiif/collection/b564jg065.json'),
        ('Illinois', 'Public collection JSON', 'https://digital.library.illinois.edu/collections.json'),
        ('Illinois', 'API documentation', 'https://digital.library.illinois.edu/api'),
        ('Folger', 'Current collection homepage', 'https://collections.folger.edu/'),
        ('Folger', 'Public digital collections homepage', 'https://digitalcollections.folger.edu/'),
        ('Princeton Art Museum', 'Official API documentation', 'https://raw.githubusercontent.com/Princeton-University-Art-Museum/puam-api-docs/main/README.md'),
        ('Princeton Art Museum', 'Public object enumeration', 'https://data.artmuseum.princeton.edu/objects?limit=5&page=1'),
        ('UCLA', 'Public catalogue JSON', 'https://digital.library.ucla.edu/catalog.json?q=map&per_page=5'),
        ('UCLA', 'Official IIIF guide', 'https://guides.library.ucla.edu/digital-collections/iiif'),
        ('Getty', 'Public linked-data collection', 'https://data.getty.edu/museum/collection/'),
        ('Folger', 'Official IIIF guide', 'https://guides.iiif.io/guides/collections.folger.edu/'),
    ]
    (root / 'round1_requests.json').write_text(json.dumps([dict(provider_name=n, purpose=p, url=u) for n,p,u in targets], indent=2), encoding='utf-8')
    print(root)


if __name__ == '__main__':
    main()
