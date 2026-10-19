"""Freeze the resumed investigation baseline and record primary-source probes."""
import json
from pathlib import Path


def main():
    module = Path(__file__).resolve().parents[1]
    root = module / 'evaluation/2026-10-19_resumed_five_provider_completion'
    root.mkdir(parents=True, exist_ok=True)
    for name in ('discovery_knowledge.json', 'provider_endpoints.json'):
        target = root / ('before_' + name)
        if not target.exists():
            target.write_bytes((module / 'config' / name).read_bytes())
    targets = [
        ('Princeton University Libraries', 'Blacklight catalogue JSON', 'https://dpul.princeton.edu/papyri/catalog.json?per_page=5&page=1'),
        ('Princeton University Libraries', 'Collection record', 'https://dpul.princeton.edu/papyri/catalog/k930c1539'),
        ('University of North Texas Libraries', 'Official API documentation', 'https://digital.library.unt.edu/api/'),
        ('University of North Texas Libraries', 'Documented collection manifest', 'https://digital.library.unt.edu/collection/manifest/'),
        ('Villanova University', 'Public VuFind API root', 'https://digital.library.villanova.edu/api/v1/'),
        ('Villanova University', 'Official guide', 'https://guides.iiif.io/guides/digital.library.villanova.edu/'),
        ('Stanford University', 'Blacklight structured results', 'https://searchworks.stanford.edu/catalog.json?f%5Biiif_resources%5D%5B%5D=available&per_page=5'),
        ('Stanford University', 'Official IIIF documentation', 'https://api.library.stanford.edu/docs/iiif/api/'),
        ('Harvard University Digital Collections', 'Official IIIF documentation', 'https://library.harvard.edu/services-tools/iiif-manifests-digital-objects'),
        ('Harvard University Digital Collections', 'CURIOSity catalogue JSON', 'https://curiosity.lib.harvard.edu/chinese-rare-books/catalog.json?per_page=5&page=1'),
    ]
    (root / 'round1_requests.json').write_text(json.dumps([dict(provider_name=n, purpose=p, url=u) for n,p,u in targets], indent=2) + '\n', encoding='utf-8')
    print(root)


if __name__ == '__main__':
    main()
