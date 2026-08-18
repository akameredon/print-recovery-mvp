# Days 91–98 — Pilot and public-beta readiness pack

This document records the operational artifacts for Days 91–98. It is a readiness pack and template set; it does not claim that a named shop, target printer/RIP, seven-day pilot or physical seam measurement has occurred without attached field evidence.

## Day 91 — Named pilot-shop onboarding checklist

The tester records the shop name, operator and technician contacts, printer model, RIP version, media dimensions, power-protection behavior, workspace owner, backup location, support contact and pilot start/end dates. Before the first job, the tester confirms local login, workspace isolation, encrypted-key backup, offline capture, interruption event recording, evidence review and restore-tested backup status.

## Day 92 — Operator training material

The operator workflow is: create or upload a job; confirm printer, RIP and media dimensions; capture checkpoints; record the interruption reason; inspect the checkpoint and recovery-safety report; review the continuation preview; generate a test-first continuation; inspect the registration strip; record the operator review; and retain the evidence bundle. Operators must not treat a software recommendation as proof of physical alignment and must escalate missing or changed source files.

## Day 93 — Technician adapter-conformance checklist

For each adapter, the technician records the adapter name and version, printer/RIP model, observed queue or trace source, event timestamp behavior, interruption mapping, checkpoint mapping, duplicate-event behavior, reconnect behavior, workspace scope, secret handling, failure mode and evidence capture. Conformance requires observation-only behavior, no printer-control commands, deterministic event replay and a documented unsupported case.

## Day 94 — Repeated interruption-test archive

The test archive must include the exact printer/RIP/media configuration, test identifier, interruption trigger, checkpoint before interruption, source hash, recovery output name, registration-strip review, operator decision, observed seam result and raw event export. Repeated tests must include power loss and protection-trip scenarios where safely available. A report without target-device evidence is a planned test, not a completed field result.

## Day 95 — Seam, alignment and material measurement report

The measurement record includes job dimensions, checkpoint coordinate, continuation coordinate, overlap, observed seam offset, alignment result, material used, material saved estimate, waste estimate, measurement method, instrument or ruler resolution, operator and timestamp. Software estimates must remain labeled as estimates until physical measurements are entered.

## Day 96 — Customer-visible confidence explanation

The customer-facing wording is: “This assistant records where the software believes the interruption occurred and prepares a continuation for operator review. The confidence indicator reflects the completeness and consistency of recorded evidence; it does not guarantee physical alignment, print quality or material recovery. Inspect the preview and test strip before continuing.”

## Day 97 — Supported and unsupported model messaging

Supported messaging must name the exact tested printer/RIP workflow and adapter version. Unsupported messaging must state that the assistant may capture local job evidence but cannot claim device-specific position accuracy without a validated adapter and field test. Mimaki, Roland and other brands must not be described as supported merely because an image file can be uploaded.

## Day 98 — Beta release notes and known limitations

The beta includes multi-user workspaces, encrypted local secrets, audit records, integrity checks, offline capture state, verified backups, structured crash reports, signed continuation metadata, upload validation and operational reports. Known limitations are that the system is software-only, does not control printers or RIPs, does not measure physical media position, requires printer/RIP-specific validation, and cannot claim a seven-day pilot or seam-quality result without field evidence.

| Evidence status | Meaning |
|---|---|
| Planned | Artifact or test procedure exists; field execution has not occurred |
| Recorded | Software event or operator note exists |
| Verified | The supplied artifact passed its deterministic check |
| Field-validated | A named printer/RIP/shop produced reviewed physical evidence |

> These artifacts support disciplined beta preparation. They must not be presented to a customer as proof of field validation until the named shop, target device and physical test records are attached.
