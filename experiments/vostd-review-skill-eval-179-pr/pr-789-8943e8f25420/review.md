# Review: `diff.patch` with captured before/after context

> Fast, non-exhaustive VOSTD review of the changes captured in `diff.patch` and the corresponding `before/` and `after/` trees.
> Scope: ACPI/DMAR verification changes, the new `vstd_extra` external specifications, related dependency changes, and the module-enablement edits present in the patch.

**Bottom line:** The parsing proof is not yet usable as a public contract. Callers cannot unfold the predicate they must establish, and successful parsing exposes only the decoded header rather than the device scopes that are the parser's principal output. The remaining findings are low-severity trust-boundary and upstream-reuse readiness issues.

## High

No high-severity findings.

## Medium

### Make the caller-facing validity predicate unfoldable

- **Guideline:** `keep-internal-spec-helpers-closed`
- **Location:** `ostd/src/arch/x86/kernel/acpi/remapping.rs:317`
- **Evidence:** `pub closed spec fn valid_device_scopes(bytes: Seq<u8>, start: int, end: int) -> bool`, while the generated public `from_bytes` contract requires `valid_device_scopes(bytes@, size_of::<$header_struct>() as int, bytes@.len() as int)` at lines 369-377.
- **Problem:** This is not an internal helper: it is a precondition that external callers of each public parser must prove. Because it is `closed`, callers cannot unfold its recursive definition to establish that a concrete byte sequence consists of valid device-scope entries.
- **Suggestion:** Change it to `pub open spec fn valid_device_scopes(...)` (or export sufficient public introduction/decomposition lemmas) so callers can discharge the public precondition without depending on module-private unfolding.

### Specify the parsed device scopes, not only the header

- **Guideline:** `api-postconditions`
- **Location:** `ostd/src/arch/x86/kernel/acpi/remapping.rs:369`
- **Evidence:** The generated parser constructs `device_scopes` in the loop at lines 387-404, but its only postcondition is `ret.header_spec() == decode_pod::<$header_struct>(...)` at lines 378-381. The affected result types contain `device_scopes: Vec<DeviceScope>` (for example `Drhd` at line 37), and `DeviceScope::from_bytes_prefix` already provides a `path_spec` result at lines 434-442.
- **Problem:** A caller can prove which header was decoded but nothing about the sequence of device scopes produced from the remaining bytes. That omits the main semantic result of these parsing APIs and prevents downstream verification from relating parsed IOMMU scopes to the input table.
- **Suggestion:** Add a model for each result's `device_scopes` (or one generated shared accessor) and strengthen `from_bytes` to relate it to the recursively parsed suffix of `bytes@`; preserve table order and use the existing `DeviceScope` header/path models for each element.

## Low

| Finding | Guideline | Detail |
|---|---|---|
| The newly verified public constructor is entirely trusted without documenting that boundary. | `document-verified-apis` | At `ostd/src/arch/x86/kernel/acpi/dmar.rs:90-92`, `pub fn new() -> Option<Self>` is introduced under `#[verus_verify(external_body)]`, but its rustdoc only says “Creates a instance from ACPI table.” Add a concise verified-properties/Safety note stating that ACPI discovery and DMAR parsing performed by `new` remain an external-body trust boundary; do not imply those operations were proved by this change. |
| The generic `core::str::from_utf8` model is reusable beyond OSTD but is added as a local trust source. | `upstream-reusable-specs` | `verified_libs/vstd_extra/src/external/str.rs:23-32` adds an `assume_specification` for a standard `core` API, with success bytes and UTF-8 validity plus the invalid-input error direction. Propose this specification upstream to Verus/vstd (and retire the local copy once available) so projects do not accumulate competing trusted models of the same `core` function. |

## Evidence check record

- Read all 798 lines of `diff.patch` and inspected the cited files in both captured trees for surrounding executable and specification context.
- Checked all additions matching `rlimit`, `assume`, `external_body`, and external-specification constructs. No added or changed `#[verifier::rlimit(...)]` was present, so there is no `rlimit > 200` finding.
- Searched the captured `after/` tree for uses of `valid_device_scopes`, `device_scopes`, `path_pairs_spec`, `header_spec`, and the new UTF-8 specification. The validity predicate is used as a public parser precondition; no parser postcondition relates the constructed `device_scopes` vector to the input bytes.
- Compared the new `core::str::from_utf8` contract with its documented success/error split as represented in the patch. No contradictory direction was found statically; the concern is placement and reuse, not an asserted semantic mismatch.
- The manual `Pod` implementations were inspected for field composition and layout-sensitive risk. No strong evidence-backed defect was retained from that check.
- The commented module/import blocks were compared with the before snapshot. They preserve the original text directly while enabling the ACPI target, so no `preserve-exec-code` finding was retained.
- No duplicate existing `from_utf8` specification was found in the captured tree; the new file itself states that vstd does not currently specify this API.

**No-verification disclosure:** Per the requested fast-review override, no Verus run, build, test, isolated caller experiment, git-history analysis, or exhaustive guideline checklist was performed. Findings are based on static inspection of the supplied patch and before/after context only.
