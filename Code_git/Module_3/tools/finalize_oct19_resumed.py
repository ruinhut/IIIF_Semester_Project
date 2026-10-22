"""Reconcile the 19 October resumed investigation and promote verified recipes."""
import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def rows(path):
    return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s.strip()]


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def table(path, values):
    with path.open('w', encoding='utf-8-sig', newline='') as output:
        writer = csv.DictWriter(output, fieldnames=list(values[0]))
        writer.writeheader()
        writer.writerows(values)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evaluation-root', type=Path, required=True)
    parser.add_argument('--previous-status', type=Path, required=True)
    parser.add_argument('--promote', action='store_true')
    parser.add_argument('--metrics-only', action='store_true', help='Write reconciled metrics without the original run-specific prose')
    args = parser.parse_args()
    root = args.evaluation_root.resolve()
    module = Path(__file__).resolve().parents[1]
    code = module.parent
    providers = read(root / 'providers.json')
    expected = {p['provider_id'] for p in providers}
    bundles = read(root / 'bundle_verification.json')
    pixels = read(root / 'image_decode_verification.json')
    tests = read(root / 'test_results.json')
    assert expected == set(bundles['provider_ids']) and not bundles['errors']
    assert pixels['decoded_images'] == len(expected) and not pixels['decode_errors']
    assert len(tests) == 6 and all(t['exit_code'] == 0 for t in tests)
    manifests = rows(root / 'validation/module3/output/manifest_urls.jsonl')
    validated = rows(root / 'combined_validated_manifests.jsonl')
    records = rows(root / 'downstream/module7/output/common_records.jsonl')
    media = rows(root / 'downstream/module7/output/common_media.jsonl')
    references = rows(root / 'downstream/module7/output/institution_reference_texts.jsonl')
    by_record = {r['record_id']: r for r in records}
    sample_root = root / 'download_examples/module8/output'
    downloads = rows(sample_root / 'all/download_index.jsonl')
    pixel_by_resource = {r['resource_id']: r for r in pixels['images']}
    sample_by_provider, sample_locations = {}, []
    for item in downloads:
        directory = sample_root / item['bundle_directory']
        document = read(directory / 'common_record.json')
        for provider in document['source']['providers']:
            sample_by_provider[provider['provider_id']] = item
        sample_locations.append({
            'provider_name': document['source']['providers'][0]['provider_name'],
            'manifest_url': document['source']['manifest_url'],
            'image_path': str((sample_root / item['image_path']).resolve()),
            **{name: str((directory / (name + '.json')).resolve())
               for name in ['common_record', 'common_media', 'ocr_document_profile']},
        })
    assert set(sample_by_provider) == expected and len(downloads) == len(expected)
    counts = []
    for provider in providers:
        identifier = provider['provider_id']
        associated = [m for m in media if any(p['provider_id'] == identifier for p in by_record[m['record_id']]['source']['providers'])]
        sample = sample_by_provider[identifier]
        pixel = pixel_by_resource[sample['resource_id']]
        counts.append({
            'provider_id': identifier, 'provider_name': provider['name'],
            'discovered_manifest_urls': sum(any(p['provider_id'] == identifier for p in m['providers']) for m in manifests),
            'validated_manifests': sum(any(p['provider_id'] == identifier for p in m['providers']) for m in validated),
            'exported_image_associations': len(associated),
            'distinct_image_urls': len({m['image']['download_url'] for m in associated}),
            'actual_sample_images': 1, 'actual_width': pixel['width'], 'actual_height': pixel['height'],
            'canvas_width': pixel['declared_dimensions'][0], 'canvas_height': pixel['declared_dimensions'][1],
            'matches_declared_dimensions': pixel['dimensions_match'],
        })
    assert all(p['validated_manifests'] > 0 and p['exported_image_associations'] > 0 for p in counts)
    save(root / 'provider_results.json', counts)
    table(root / 'provider_results.csv', counts)
    table(root / 'sample_downloads.csv', sample_locations)
    prior = read(args.previous_status)
    old_ids = {p['provider_id'] for p in prior if p['status'] == 'manifest_found_and_basic_structure_validated'}
    assert not (old_ids & expected), 'These entries were already counted in the previous run'
    all_ids = old_ids | expected
    census = rows(code / 'Module_1/data/output/providers.jsonl')
    statuses = [{'provider_id': p['provider_id'], 'provider_name': p['name'],
                 'institution_url': p['institution_url'],
                 'status': 'manifest_found_and_basic_structure_validated' if p['provider_id'] in all_ids else 'unresolved_in_cumulative_evidence'} for p in census]
    remaining = [p for p in statuses if p['provider_id'] not in all_ids]
    for filename, values in [('cumulative_provider_status', statuses), ('remaining_unresolved_entries', remaining)]:
        save(root / (filename + '.json'), values)
        table(root / (filename + '.csv'), values)
    preservation = {}
    for filename, addition in [('discovery_knowledge.json', 'new_knowledge_entries.json'),
                               ('provider_endpoints.json', 'new_endpoint_entries.json')]:
        baseline = read(root / ('before_' + filename))
        current = read(module / 'config' / filename)
        existing = {p['provider_id']: p for p in current['providers']}
        assert all(existing.get(p['provider_id']) == p for p in baseline['providers']), 'Existing recipe changed'
        for entry in read(root / addition):
            assert entry['provider_id'] in expected
            if entry['provider_id'] in existing:
                assert existing[entry['provider_id']] == entry
            elif args.promote:
                current['providers'].append(entry)
        if args.promote:
            save(module / 'config' / filename, current)
        preservation[filename] = {'before_entries': len(baseline['providers']), 'after_entries': len(current['providers']), 'old_entries_unchanged': True}
    save(root / 'knowledge_preservation_check.json', preservation)
    summary = {
        'generated_at': datetime.now(timezone.utc).isoformat(), 'new_resolved_source_entries': len(expected),
        'discovered_manifest_urls': len({m['manifest_url'] for m in manifests}), 'validated_manifests': len(validated),
        'exported_documents': len(records), 'exported_image_associations': len(media),
        'distinct_image_urls': len({m['image']['download_url'] for m in media}),
        'actual_downloaded_sample_images': len(downloads), 'actual_sample_image_bytes': sum(d['bytes'] for d in downloads),
        'ocr_reference_descriptors': len(references), 'schema_validated_sample_json_files': bundles['schema_validated_json_files'],
        'decoded_images': pixels['decoded_images'], 'smaller_than_canvas_declaration': len(pixels['dimension_mismatches']),
        'tests_passed': sum(t['passed'] for t in tests), 'previous_resolved_census_entries': len(old_ids),
        'cumulative_resolved_census_entries': len(all_ids), 'census_entries': len(census),
        'remaining_unresolved_census_entries': len(remaining), 'configuration_promoted': args.promote,
        'scope': 'Bounded samples; source entries include an aggregator. Historical successes were not all re-fetched today.',
        'unresolved_investigation': {'provider_name': 'Villanova University', 'observed_status': 'HTTP 403', 'counted_as_new_success': False},
    }
    save(root / 'summary.json', summary)
    if args.metrics_only:
        summary['unresolved_investigation'] = read(root / 'unresolved_investigations.json') if (root / 'unresolved_investigations.json').exists() else []
        summary['legacy_shared_canvas_manifests'] = sum(m.get('structural_validation', {}).get('source_format') == 'legacy_shared_canvas' for m in validated)
        summary['summed_per_manifest_distinct_image_body_count'] = sum(m.get('structural_validation', {}).get('image_body_count', 0) for m in validated)
        save(root / 'summary.json', summary)
        print(json.dumps(summary, ensure_ascii=True))
        return
    lines = ['# 本轮五个新增来源的验证结果', '', '日期：2026-10-19。先前 18:05 截止记录保留，本轮是在新的“继续跑”指令后执行。', '',
             '## 实际完成', '', '| 来源 | 有效 Manifest | 图片关联记录 | 实际下载图片 | 样例像素 |', '|---|---:|---:|---:|---|']
    lines += [f"| {p['provider_name']} | {p['validated_manifests']} | {p['exported_image_associations']:,} | 1 | {p['actual_width']} × {p['actual_height']} |" for p in counts]
    lines += ['', f"合计 **{len(validated)} 个 Manifest、{len(media):,} 条图片关联、5 张真实图片及 15 份配套 JSON**。这是样本验证，2,103 条链接没有全部下载，不能作为全馆总量。", '',
              '## 已保存的方法', '',
              '- Princeton：分页目录 JSON → 条目详情 JSON → 详情声明的 Figgy Manifest。',
              '- UNT：馆藏 API 页面 → 原生 Collection 的 first / next 分页。',
              '- Harvard：LibraryCloud 的 MODS 目录 → 明确 Manifest 链接 → 有界跟随 HTML 迁移声明及 HTTP 重定向。',
              '- Stanford：公开 FromThePage 贡献索引 → dc:source 声明的 Stanford 原馆 PURL Manifest。范围限于该索引。',
              '- Biblissima：聚合目录分页 → 结果页明确链接的 IRHT Manifest。当前配置不涵盖其他全部原馆。', '',
              '新增的是可执行配置及可复用的处理方法；没有接入运行时 LLM API。Villanova 的公开入口返回 403，未计入成功，用 Biblissima 补足本轮 5 个来源。',
              '[详细调查过程与官方来源](../../knowledge/institutions/2026-10-19_resumed_provider_completion.md)。', '',
              '## 测试和输出限制', '',
              f"- Module 4 独立联网校验 30/30 通过，没有使用旧 Manifest 缓存冒充本次下载；M5–7 导出 30 个文献和 2,103 个媒体记录。",
              f"- M3–8 自动测试 **{summary['tests_passed']} 项全部通过**，另有 7 个子测试。5 张图均实际解码成功，15 份 JSON 通过 schema 与关联检查。",
              '- Princeton 样例链接明确请求宽 1000 像素；Harvard 与 Biblissima 实际图片也小于 Canvas 声明。本轮没有把缩放样例称为原始分辨率，详情见 image_decode_verification.json；像素/坐标用于 OCR 前仍需核对。',
              '- 本轮没有确认可直接交给 Arsha 的图片—机构 OCR 配对。UNT 的 12 个描述性元数据 XML 链接已从 OCR reference 输出中排除，原始链接仍保留在原 Manifest；ALTO、hOCR 与明确转录继续支持。',
              '- Biblissima 样例图片下载成功，但对其 info.json 的额外检查超时；不据此否认图片成功，也不声称该附加请求已成功。', '',
              '## 累计与文件', '',
              f"累计 **{len(old_ids)} → {len(all_ids)} / {len(census)} 个来源条目**；未解决 **{len(census)-len(old_ids)} → {len(remaining)}**。Biblissima 是聚合平台，这不是新增 5 家独立收藏机构。累计沿用已保存的历史验证证据，不是今天重新检查了全部 94 条。",
              '- provider_results.csv：逐来源 Manifest、图片数量和实际像素。',
              '- sample_downloads.csv：5 张图片及每张对应的三个 JSON 的完整路径。',
              '- downstream/module7/output：本轮完整 JSONL 输出。',
              '- download_examples/module8/output/all/without_reference：实际图片及 JSON 文件包。',
              '- 运行命令.txt：可复制的 PowerShell 命令。',
              '- cleanup_manifest.json：临时文件清理记录。保留正式代码、知识库、配置、日志、原始 Manifest 及样例。', '']
    (root / '本轮五来源验证结果.md').write_text('\n'.join(lines), encoding='utf-8')
    commands = [
        "$CodeRoot = 'E:\\exchange-epfl\\Semester_Project\\Code_git'",
        "$PipelinePython = Join-Path $CodeRoot '.venv\\Scripts\\python.exe'",
        "$EvaluationRoot = Join-Path $CodeRoot 'Module_3\\evaluation\\2026-10-19_resumed_five_provider_completion'",
        "$env:PYTHONIOENCODING = 'utf-8'",
        "# This computer's valid CA bundle; use an installed valid CA file if moving to another machine.",
        "$env:SSL_CERT_FILE = 'C:\\Users\\43057\\AppData\\Local\\Programs\\Python\\Python310\\lib\\site-packages\\certifi\\cacert.pem'",
        'Set-Location -LiteralPath $CodeRoot', '',
        '& $PipelinePython Module_3\\tools\\run_discovery_with_evidence.py --config "$EvaluationRoot\\module3_validation.json"',
        'if ($LASTEXITCODE -ne 0) { throw "Module 3 failed" }',
        '& $PipelinePython -m iiif_manifest_validator run --config "$EvaluationRoot\\module4_validation.json"',
        'if ($LASTEXITCODE -ne 0) { throw "Module 4 failed" }',
        '& $PipelinePython Module_3\\tools\\complete_oct19_provider_completion.py --evaluation-root $EvaluationRoot',
        'if ($LASTEXITCODE -ne 0) { throw "Module 5-8 failed" }',
        '& $PipelinePython Module_3\\tools\\verify_linked_download_bundles.py --output-root "$EvaluationRoot\\download_examples\\module8\\output" --report "$EvaluationRoot\\bundle_verification.json"', '',
        '# Open image/JSON paths in sample_downloads.csv; full Module 7 JSONL files are in downstream/module7/output.',
        'Import-Csv -LiteralPath "$EvaluationRoot\\provider_results.csv" | Format-Table -AutoSize',
        'Import-Csv -LiteralPath "$EvaluationRoot\\sample_downloads.csv" | Format-List', '',
    ]
    (root / '运行命令.txt').write_text('\n'.join(commands), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=True))


if __name__ == '__main__':
    main()
