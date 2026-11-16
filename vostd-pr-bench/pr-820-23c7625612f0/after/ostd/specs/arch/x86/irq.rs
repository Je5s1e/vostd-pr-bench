// SPDX-License-Identifier: MPL-2.0
use vstd::prelude::*;

verus! {

pub(crate) type IsaOverrideMapping = (u8, u32);

/// A decoded MADT override's bus, source and target, or a different entry kind.
pub(crate) type MadtOverrideEntry = Option<(u8, u8, u32)>;

/// The first override for an ISA source wins; an absent source maps to itself.
pub(crate) open spec fn isa_mapping_correct(
    overrides: Seq<IsaOverrideMapping>,
    isa: u8,
    gsi: u32,
) -> bool {
    &&& (forall|i: int| 0 <= i < overrides.len() ==> #[trigger] overrides[i].0 != isa) ==> gsi
        == isa as u32
    &&& (exists|i: int| 0 <= i < overrides.len() && #[trigger] overrides[i].0 == isa) ==> (exists|
        i: int,
    |
        0 <= i < overrides.len() && #[trigger] overrides[i].0 == isa && (forall|j: int|
            0 <= j < i ==> #[trigger] overrides[j].0 != isa) && gsi == overrides[i].1)
}

/// Retain the source and target of an ISA interrupt-source override.
pub(crate) open spec fn isa_override_entry(entry: MadtOverrideEntry) -> Option<IsaOverrideMapping> {
    match entry {
        Some((bus, source, target)) if bus == 0 => Some((source, target)),
        _ => None,
    }
}

/// Collect ISA overrides in MADT traversal order, preserving duplicates.
pub(crate) open spec fn collect_isa_overrides(entries: Seq<MadtOverrideEntry>) -> Seq<
    IsaOverrideMapping,
> {
    entries.filter_map(|entry: MadtOverrideEntry| isa_override_entry(entry))
}

/// Insert the PIT override only if the whole collected list is empty.
pub(crate) open spec fn isa_overrides_with_fallback(overrides: Seq<IsaOverrideMapping>) -> Seq<
    IsaOverrideMapping,
> {
    if overrides.len() == 0 {
        seq![(0u8, 2u32)]
    } else {
        overrides
    }
}

/// Later duplicates cannot change the target of the first matching source.
pub(crate) proof fn lemma_isa_first_match(
    overrides: Seq<IsaOverrideMapping>,
    isa: u8,
    gsi: u32,
    i: int,
)
    requires
        isa_mapping_correct(overrides, isa, gsi),
        0 <= i < overrides.len(),
        overrides[i].0 == isa,
        forall|j: int| 0 <= j < i ==> #[trigger] overrides[j].0 != isa,
    ensures
        gsi == overrides[i].1,
{
    let k = choose|k: int|
        0 <= k < overrides.len() && #[trigger] overrides[k].0 == isa && (forall|j: int|
            0 <= j < k ==> #[trigger] overrides[j].0 != isa) && gsi == overrides[k].1;
}

/// With the empty-list fallback, only IRQ 0 maps to a different GSI.
pub(crate) proof fn lemma_empty_isa_overrides(isa: u8, gsi: u32)
    requires
        isa_mapping_correct(isa_overrides_with_fallback(Seq::empty()), isa, gsi),
    ensures
        gsi == if isa == 0 {
            2u32
        } else {
            isa as u32
        },
{
    if isa == 0 {
        lemma_isa_first_match(isa_overrides_with_fallback(Seq::empty()), isa, gsi, 0);
    }
}

/// A nonempty override list without IRQ 0 keeps its identity mapping.
pub(crate) proof fn lemma_nonempty_isa_overrides_without_timer(
    overrides: Seq<IsaOverrideMapping>,
    gsi: u32,
)
    requires
        overrides.len() > 0,
        forall|i: int| 0 <= i < overrides.len() ==> #[trigger] overrides[i].0 != 0,
        isa_mapping_correct(isa_overrides_with_fallback(overrides), 0, gsi),
    ensures
        gsi == 0,
{
}

/// Every collected mapping originates from an ISA entry in the decoded sequence.
pub(crate) proof fn lemma_isa_override_origin(
    entries: Seq<MadtOverrideEntry>,
    mapping: IsaOverrideMapping,
)
    requires
        collect_isa_overrides(entries).contains(mapping),
    ensures
        exists|i: int|
            0 <= i < entries.len() && #[trigger] isa_override_entry(entries[i]) == Some(mapping),
{
    let f = |entry: MadtOverrideEntry| isa_override_entry(entry);
    entries.lemma_filter_map_contains(f, mapping);
    let entry = choose|entry: MadtOverrideEntry|
        entries.contains(entry) && f(entry) == Some(mapping);
    let i = choose|i: int| 0 <= i < entries.len() && entries[i] == entry;
}

/// Processing one more entry appends exactly its ISA mapping, if it has one.
pub(crate) proof fn lemma_collect_isa_override_push(
    entries: Seq<MadtOverrideEntry>,
    entry: MadtOverrideEntry,
)
    ensures
        collect_isa_overrides(entries.push(entry)) == match isa_override_entry(entry) {
            Some(mapping) => collect_isa_overrides(entries).push(mapping),
            None => collect_isa_overrides(entries),
        },
{
    let next = entries.push(entry);
    assert(next[..entries.len()] == entries);
    next.lemma_filter_map_take_succ(
        |e: MadtOverrideEntry| isa_override_entry(e),
        entries.len() as int,
    );
}

} // verus!
