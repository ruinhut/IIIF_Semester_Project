# Module 3 Generalisation Evaluation — 2026-09-25

## Purpose

This experiment measures whether Module 3's generic discovery strategies transfer
to institutions that were not used while the strategies were developed.

The current 94-provider census is split into:

- 75 development providers;
- 19 held-out test providers.

Providers sharing the same institutional base domain, together with all of their
endpoint candidates, remain in the same split. The split uses only Module 1
domains and endpoint roles. It does not use live network outcomes or Module 3
results.

Module 3 is deterministic and rule-based. The development set therefore does
not train model weights. It inventories endpoint classes and verifies reusable
strategies. The same implementation and limits are frozen before the held-out
run; no test-provider-specific code or curated endpoints are added.

## Bounded-run settings

- Module 2 timeout: 8 seconds; no retries.
- Module 3 timeout: 10 seconds; no retries.
- At most 2 HTML pages and depth 1 per provider.
- At most 5 Change Discovery pages and 20 Collections per provider.
- At most 20 machine-discovered candidates and 100 Manifests per provider.

A negative result means that no Manifest was found within these common limits.
It does not prove that an institution has no IIIF resources.

## Reproduction

Run the following commands in order.

From this evaluation directory:

~~~powershell
python prepare_split.py
~~~

From Code_git/Module_2:

~~~powershell
python -m iiif_entry_validator run --config ..\Module_3\evaluation\2026-09-25\configs\module2_development.json
python -m iiif_entry_validator run --config ..\Module_3\evaluation\2026-09-25\configs\module2_test.json
~~~

From Code_git/Module_3:

~~~powershell
python -m iiif_resource_discovery run --config evaluation\2026-09-25\configs\module3_development.json
python -m iiif_resource_discovery run --config evaluation\2026-09-25\configs\module3_test.json
python evaluation\2026-09-25\analyze_results.py
~~~

## Result

- Development set: 9/75 providers resolved; 306 unique Manifest URLs.
- Held-out test set: 2/19 providers resolved (10.5%); 19 unique Manifest URLs.
- Held-out successes: Digital Commonwealth (1) and Fragmentarium (18).

See results/generalisation_evaluation.md for interpretation,
results/held_out_provider_results.csv for every held-out institution, and the
two PNG/PDF charts for the requested visual summaries.