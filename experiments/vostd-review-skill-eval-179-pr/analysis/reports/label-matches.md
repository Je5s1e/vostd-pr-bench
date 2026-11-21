# 逐标签根因匹配表

F=完整命中；P=部分命中；M=未匹配；X=before问题已被after修复。编号采用标签0开始、报告finding 1开始。完整原文及哈希见snapshot.json。单agent语义判断，未人工校准；一项报告含明确不同子声明时可对应多个标签，不代表发现已完整原子化或真伪确认。

## pr-100-3439712c4524

### L0 — M — 构建、工具链与证明可接受性
The refactored cursor path specification reads a nonexistent pa field from an IntermediatePageTableEntryView instead of its frame_pa field.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

### L1 — M — API契约、泛型与边界
map promises that the cursor level is unchanged even though its descent loop lowers the level until frame.map_level().

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

### L2 — M — 显式admit/external_body证明缺口
The new-child map branch assumes that the allocated page-table child is the child represented by the current parent entry and cursor path before appending it.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-104-f3df1ab197d2

### L0 — M — 运行时行为与生命周期
When page-sized cursor progress crosses a page-table-node boundary, move_forward does not ascend to the parent and pop_level would leave the departed child guard in a slot that must be empty at the higher level.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-119-0a0ec99c5b50

### L0 — F — API契约、泛型与边界
replace_with_none identifies the frame-condition exception with the replacement PTE's post-state address instead of the removed PTE's entry-state address.

对应报告：F1 The frame condition exempts the post-state PTE instead of the removed PTE

裁决：报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。

## pr-122-aa2041448069

### L0 — M — 运行时行为与生命周期
try_traverse_and_lock_subtree_root discards PageTableGuard values on two traversal paths without manually releasing their underlying spin locks.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-127-ac14d35923e4

### L0 — M — 构建、工具链与证明可接受性
The Windows bootstrap silently falls back to legacy Windows PowerShell even though that shell has a known module-loading failure for the installer command, leaving users without actionable guidance to use pwsh.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-136-9483097409b4

### L0 — F — 显式admit/external_body证明缺口
`lock_range` uses four `admit()` branches to trust that its lock-model path still corresponds to the requested virtual-address path.

对应报告：F1 H1 — Three new admits trust the central path invariant

裁决：同一path对应关系根因：报告定位3个新admit，并明确提及第4个既有admit；不按4个位置拆分标签。

## pr-143-544fc49e7446

### L0 — M — 所有权、资源守恒与对象身份
A trusted lemma derives a newly allocated child's non-stray state from structural node IDs alone, without tying either guard to the same page-table instance or to the parent's live PTE token.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-146-b4c63161c57b

### L0 — F — 显式admit/external_body证明缺口
alloc_if_none assumes that a newly allocated page is fresh in the SPT frame map and then assumes the entire updated SubPageTable invariant.

对应报告：F2 Allocation freshness is dropped at the wrapper and reintroduced as a caller-local assumption；F3 The state-machine update is bridged to the next verified operation by assuming the whole invariant

裁决：报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。

## pr-146-c6ea1a85e164

### L0 — P — 显式admit/external_body证明缺口
alloc_if_none trusts the parent entry's address, level, root relationship, and resulting child-guard postconditions instead of deriving them from Entry well-formedness.

对应报告：F1 H1 — The proof assumes a fact contradicted by the function precondition

裁决：H1提及i_pte.wf/root/level/frame level未经证明，但主论点是另一处矛盾；未完整分析Entry::wf缺关系及返回child guard保证。

## pr-16-ace524111090

### L0 — M — 构建、工具链与证明可接受性
After the update command starts fetching the current Verus branch, four finite memory-region loops fail the newly enabled execution termination check because they have no decreases clauses.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-161-1510b718eb7d

### L0 — F — 状态机、不变量与模型语义
The stray-to-PTE invariant compares a child PTE's target address with its parent node ID instead of the stray record's physical address.

对应报告：F2 The proof assumes an invariant whose address comparison is shadowed and generally false

裁决：报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。

## pr-17-30beab687be4

### L0 — M — 构建、工具链与证明可接受性
The new FVT13 target omits the execution-termination policy for an intentional spin loop and a consuming queue loop, so the fixed Verus toolchain rejects the target with missing-decreases errors.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-171-6cc1b7bbb99b

### L0 — F — 状态机、不变量与模型语义
`inv_stray_in_node` incorrectly requires every stray entry to retain a live node, excluding the true-stray state created when a node is removed and waits for recycling.

对应报告：F1 The new stray invariant is false after deallocation

裁决：报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。

### L1 — M — 状态机、不变量与模型语义
`wf_cursors` validates only cursor keys that happen to exist and does not require every valid CPU to own a cursor token.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-171-81a05f39c6ad

### L0 — M — 状态机、不变量与模型语义
The non-overlap invariant ignores the nodes already write-locked by a `Locking` cursor, so it cannot establish exclusive ownership when that cursor becomes `Locked`.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-175-1be41f76acbd

### L0 — M — 状态机、不变量与模型语义
`protocol_lock_start` leaves the subtree root in `LockedOutside` and creates an empty `Locking(nid, nid)` range even though execution has already locked that root, so the protocol state does not represent the lock held at the end of traversal.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-178-8d5d616a2605

### L0 — F — 构建、工具链与证明可接受性
The new parallel-verification warning uses `OwoColorize` and `Stream` on every platform while importing them only on Windows.

对应报告：F1 The unconditional warning refers to Windows-only imports

裁决：报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。

## pr-182-16d5d093ac90

### L0 — F — 显式admit/external_body证明缺口
A newly generalized NodeHelper reconstruction lemma grants get_child(get_parent(nid), get_offset(nid)) == nid through admit instead of deriving it from the node trace representation.

对应报告：F1 The new public reconstruction lemma is admitted

裁决：报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。

## pr-183-fb3b9d0681b5

### L0 — F — 显式admit/external_body证明缺口
The rewritten aligned-PTE-index lemma exposes its complete higher-level alignment theorem through admit.

对应报告：F1 H1 — A previously proved alignment lemma is now admitted

裁决：报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。

### L1 — F — 显式admit/external_body证明缺口
The rewritten move_forward proof assumes that adding the current page size preserves every higher-level PTE index after carry propagation.

对应报告：F2 H2 — `move_forward` assumes the core carry-preservation fact

裁决：报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。

## pr-213-7de412d2a90e

### L0 — M — 状态机、不变量与模型语义
The lock-freedom predicate existentially chooses one thread for the entire leads-to relation, so an out-of-set thread makes the property vacuously true even when a real thread waits forever.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-213-9d72cec58996

### L0 — F — 状态机、不变量与模型语义
The abstract-lock invariant equates a held lock with a thread at cs, omitting the reachable unlock program-counter state in which the lock is still held.

对应报告：F1 The admitted `cs` case hides a false invariant used to prove mutual exclusion

裁决：报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。

## pr-22-97523065e4c0

### L0 — M — 构建、工具链与证明可接受性
The selected snapshot's quotient-bound proof uses a division-order lemma whose strict-order precondition already requires the desired `offset < 512` fact, so the fixed verifier rejects the proof as circular.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-220-1c5f850814d9

### L0 — M — 构建、工具链与证明可接受性
Both shell if/then/else blocks in the verification workflow omit their closing fi.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-220-cfcd9e87ed0d

### L0 — F — 构建、工具链与证明可接受性
Both phaseII bootstrap commands suppress failure with || true.

对应报告：F1 Bootstrap failures are suppressed in a promotion gate

裁决：报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。

## pr-226-84f7a7f07d36

### L0 — F — 显式admit/external_body证明缺口
MemoryRegion::view_preserves_inv exposes interval and type-tag validity through admit.

对应报告：F1 The view invariant is admitted

裁决：报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。

### L1 — F — 显式admit/external_body证明缺口
MemoryRegionArray::new is external_body while promising an invariant-valid empty model.

对应报告：F2 The empty constructor is replaced by a trusted body

裁决：报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。

### L2 — F — 显式admit/external_body证明缺口
MemoryRegionArray::push is external_body while promising invariant preservation and success when capacity is available.

对应报告：F3 `push` trusts an incomplete contract that excludes documented behavior

裁决：报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。

## pr-226-8c5c020ff2db

### L0 — M — 构建、工具链与证明可接受性
The memory-region implementations use &self receivers for Inv and InvView methods whose traits require self by value, so the proof-retaining trait implementations do not match their declared interfaces.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-23-56d930eb5a67

### L0 — M — 构建、工具链与证明可接受性
The Windows bootstrap and update paths invoke PowerShell 7 (`pwsh`) unconditionally, so they fail with program-not-found on systems that only have the Windows-bundled `powershell.exe`.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-233-9d89be46b390

### L0 — F — 构建、工具链与证明可接受性
Deleting vstd_extra's public injective_on definition removes the name formerly re-exported through vstd_extra::prelude, but lock-protocol-rcu's unchanged proof still calls injective_on without importing vstd::relations::injective_on.

对应报告：F1 The reused predicate is no longer in scope at an existing caller

裁决：报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。

## pr-235-627f20d8afad

### L0 — M — 构建、工具链与证明可接受性
After the Verus update, `lemma_nat_as_parts` no longer proves its nat-valued decomposition because the calc chain does not establish the required intermediate non-overflow/coercion equality.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-236-72a385b929f5

### L0 — F — 构建、工具链与证明可接受性
The root workspace removes verus_builtin and verus_builtin_macros from workspace.dependencies while demo/Cargo.toml still inherits both with workspace = true, so Cargo cannot load the workspace manifest.

对应报告：F1 The workspace dependency cleanup omits the `demo` member

裁决：报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。

## pr-237-24bb220c7879

### L0 — F — 显式admit/external_body证明缺口
The align-up arithmetic theorem and the executable AlignExt::align_up contract are accepted through admit, so callers receive lower-bound, divisibility, least-aligned-value, and nat_align_up equality guarantees that are not checked against the rounding implementation.

对应报告：F1 The align-up model is exported through an admitted theorem

裁决：报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。

### L1 — F — 显式admit/external_body证明缺口
The align-down arithmetic theorem and the executable AlignExt::align_down contract are accepted through admit, so callers receive upper-bound, divisibility, greatest-aligned-value, and nat_align_down equality guarantees without a checked proof for the masking implementation.

对应报告：F2 The align-down model is exported through a separate admitted theorem

裁决：报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。

## pr-25-6479bc556a28

### L0 — F — 显式admit/external_body证明缺口
The callable subtree-bound lemma exports its full guarantee while the essential parent equality is still discharged by a nested `admit()`.

对应报告：F1 The public subtree-bound lemma still depends on an admitted parent fact

裁决：报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。

## pr-250-8224e4aee238

### L0 — F — API契约、泛型与边界
The new proof of entails_not_temp_reverse silently assumes that spec has a satisfying execution, although callers are not required to establish this premise.

对应报告：F1 `entails_not_temp_reverse` assumes the missing condition needed to make its public theorem true

裁决：报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。

## pr-26-2275e7c32b66

### L0 — F — 显式admit/external_body证明缺口
The read-lock induction proof exports cursor/reader-count consistency while its final quantified equality is still discharged with `admit()`.

对应报告：F1 The edited invariant proof still relies on `admit()`

裁决：报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。

## pr-26-5474cd472251

### L0 — P — 显式admit/external_body证明缺口
The read-unlock transition exports cursor/count consistency and positive reader-count guarantees through four related `admit()` calls.

对应报告：F1 Trusted facts are added to ordinary proof modules

裁决：H1命中同根因的positive辅助lemma，但未报告read_unlock其余3个admit；Low只是清理注释，不能算完整转移证明检测。

## pr-296-899421ff5b69

### L0 — M — 规范复用、放置与闲置helper
`remove_rel_children` recursively duplicates information already available through `recursive_trace`, adding an unnecessary parallel specification helper.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-3-df3e68c119ce

### L0 — F — 显式admit/external_body证明缺口
The Rust 1.82 port marks two failing project-local bodies as `external_body`, making their contracts trusted assumptions even though the verifier cannot prove either implementation.

对应报告：F2 A complete recursive-visit proof is replaced by a local axiom；F3 `covers` now trusts its executable/specification correspondence

裁决：报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。

## pr-33-715c00b43894

### L0 — M — 构建、工具链与证明可接受性
The RW test module enables `exec::utils` without including the required `exec/utils.rs` source file, so the crate cannot build.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-337-b6aa265c1a4a

### L0 — F — 运行时行为与生命周期
`PreemptDisabled` is changed from an uninhabited guardian backed by `DisabledPreemptGuard` into a constructible unit struct whose guard constructors return `()`, so taking a lock no longer establishes or retains the advertised preemption-disabled state.

对应报告：F1 H1 — `PreemptDisabled` no longer disables preemption, so the enabled `RwArc` can self-deadlock on a preemptible CPU

裁决：报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。

## pr-35-fa067beadf03

### L0 — M — 显式admit/external_body证明缺口
The public path-order theorem exports strict ordering for every index pair while admitting the case involving the final path element.

对应报告：无

裁决：报告明确将common.rs既有admit排除在diff之外；基准要求识别快照存量缺陷。

### L1 — F — 显式admit/external_body证明缺口
The write-lock transition exports subtree-lock preservation through an admitted inductive step and an admitted supporting subtree theorem.

对应报告：F1 The new write-lock invariant is trusted rather than proved；F2 A new subtree/accounting theorem is introduced with `admit()`

裁决：报告H1及M1分别定位inductive与支持lemma，合起来命中一个transition级标签。

### L2 — M — 显式admit/external_body证明缺口
The write-unlock transition's entire invariant-preservation proof is trusted through `admit()`.

对应报告：无

裁决：报告明确将write_unlock既有admit排除在diff之外。

### L3 — M — 显式admit/external_body证明缺口
The allocate transition's entire inductiveness obligation is trusted through `admit()` even though it can be checked without an assumption.

对应报告：无

裁决：报告明确将allocate既有admit排除在diff之外。

### L4 — M — 显式admit/external_body证明缺口
The deallocate transition's entire inductiveness obligation is trusted through `admit()` even though it can be checked without an assumption.

对应报告：无

裁决：报告明确将deallocate既有admit排除在diff之外。

## pr-350-5cbda0832ce0

### L0 — M — API契约、泛型与边界
`RwArc` exposes locking operations but no spec-level view or equivalent relation to its protected value, so clients cannot state what data a returned guard borrows from the shared wrapper.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-353-650ed55495ef

### L0 — M — 构建、工具链与证明可接受性
The documentation command passes only local and Verus crates to rustdoc, omitting registry dependency --extern mappings and their artifact search directory, so targets importing registry crates cannot resolve those imports.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-355-2a3429fb0b20

### L0 — F — 构建、工具链与证明可接受性
Three lock-guard negative Send implementations contain two consecutive commas in their generic parameter lists, leaving an empty generic parameter and preventing the source from parsing.

对应报告：F2 The rewritten `RwLock` module has invalid `impl` syntax

裁决：报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。

## pr-382-045fa97a6577

### L0 — F — 运行时行为与生命周期
lock_range removes its retry loop and unwraps a traversal result that can be None when a stray node is encountered.

对应报告：F1 The trusted traversal contract excludes an executable `None` result

裁决：H1明确描述None后unwrap并建议恢复retry，虽与callee不实契约合并，实际覆盖caller根因。

### L1 — F — API契约、泛型与边界
The external specification guarantees Some even though the implementation explicitly returns None for stray nodes.

对应报告：F1 The trusted traversal contract excludes an executable `None` result

裁决：报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。

### L2 — F — API契约、泛型与边界
lock_range drops the invariant, in_locked_range, and strict guard-level postconditions required by its callers.

对应报告：F3 `lock_range` no longer exposes the invariant its sole wrapper promises

裁决：报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。

## pr-382-6a84ab163da0

### L0 — F — 所有权、资源守恒与对象身份
placeholder_slot_perm can manufacture initialized, non-unused, unmapped slot facts for any aligned in-range frame even though MetaRegionOwners::inv does not guarantee those facts.

对应报告：F1 `placeholder_slot_perm` manufactures ownership and arbitrary region facts

裁决：报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。

### L1 — M — 验证文档
The map_item_requires documentation omits its new regions argument and the item_not_mapped and item_slot_in_regions obligations.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-39-8777297fc95c

### L0 — M — 构建、工具链与证明可接受性
Three proof postconditions call `Deref::deref` in specification context, which the supported Verus resolves as an illegal exec-mode call.

对应报告：无

裁决：diff仅修改workspace/xtask；标签是证明postcondition内deref的mode错误，与变更路径不重合。

## pr-390-ff234245b17b

### L0 — M — API契约、泛型与边界
The DMA-stream accessor and I/O methods replace the original public `&self` interface with methods that require callers to supply an internal `RwLockReadGuard`, changing the public API/behavior instead of keeping synchronization behind the object boundary.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-392-f30278a5973e

### L0 — M — 所有权、资源守恒与对象身份
The mapping proof manufactures a second initialized metadata-slot permission with an axiom and inserts it into the region map instead of transferring the existing linear permission.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-395-6ae195e508a8

### L0 — M — 运行时行为与生命周期
The successful write-to-upgradeable downgrade returns the new guard without waking waiters that were blocked by the old write lock.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-403-a1f2685897f4

### L0 — X — 所有权、资源守恒与对象身份
The take/put axioms can return linear pointer permissions while leaving an equivalent copy stored in the original PointsTo object, allowing tracked ownership to be duplicated or replaced without a borrow relationship.

对应报告：无

裁决：标签是before的take/put权限复制，after已改为借用；报告针对新borrow helper闲置，不能匹配旧缺陷，也不能简单归咎漏检。

## pr-419-e2a32e9a225f

### L0 — M — 所有权、资源守恒与对象身份
The external seq_tracked_subrange and seq_tracked_map_values helpers return tracked sequences from ordinary ghost sequence inputs without consuming or borrowing the corresponding tracked resources, allowing the same resource model to produce duplicate ownership.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-424-2e7051b98235

### L0 — M — 规范复用、放置与闲置helper
External specifications for slice pointer operations are placed in the generic std_extra module instead of the dedicated vstd_extra::external boundary.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-424-8d7b6621ed81

### L0 — M — 运行时行为与生命周期
The selected PR revision disables the DMA module and replaces the current generic, ownership-tracked DMA stream implementation with an outdated pre-port version.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-439-b083bbf05f58

### L0 — M — 所有权、资源守恒与对象身份
VmReader/VmWriter value operations consume tracked owner permissions on error even when their cursor is restored and the operation produces no value.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

### L1 — M — 构建、工具链与证明可接受性
The final head disables the `mm::dma` module while `ostd::init` still calls `mm::dma::init()`, so the crate cannot resolve that module reference.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-44-a75fa49663cc

### L0 — F — 显式admit/external_body证明缺口
The `allocate` and `lock_range` verification boundaries trust their complete contracts because `allocate` fails a precondition and `lock_range` crashes Verus around `ManuallyDrop`.

对应报告：F2 Production allocation and range locking are promoted with their state transitions wholly trusted

裁决：报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。

## pr-440-0ba029a82c8d

### L0 — M — 规范复用、放置与闲置helper
The migrated frame-mapping loops still spell out the owned iterator’s internal snapshot conversion instead of using the public `it.seq()` specification interface.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-45-a64f70e4ca48

### L0 — F — 构建、工具链与证明可接受性
The FVT6 error migration still imports std::fmt::Error in its VM reader/writer and specification modules while referring to the project-specific InvalidArgs and PageFault variants, so the enabled modules cannot resolve those error values.

对应报告：F1 The error import rewrite breaks the VM I/O module

裁决：报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。

## pr-452-d834e11605c3

### L0 — M — 规范复用、放置与闲置helper
Five new integer is_power_of_two external specifications repeat the existing vstd power-of-two existential model.

对应报告：无

裁决：报告要求upstream generic specs，标签要求复用现有is_pow2_exists；同一API不代表同一根因。

## pr-454-1db47ee9a94b

### L0 — M — API契约、泛型与边界
`cursor_mut_at` requires every non-member frame's slot permission to be in the global region map, excluding valid frames whose permission is owned by another linked list, a `UniqueFrame`, or a page-table node.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-456-6aa8a9b0ede4

### L0 — F — 运行时行为与生命周期
`DmaCoherent::map` accepts non-cache-coherent devices but no longer changes the CPU mapping to uncacheable, so the returned mapping does not provide the advertised coherent CPU/device view.

对应报告：F1 The newly exported DMA mapping is operationally a placeholder

裁决：报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。

### L1 — F — 运行时行为与生命周期
Both DMA backends return a device address without performing their required platform setup: TDX pages remain private on the direct path and the IOMMU path installs no mappings.

对应报告：F1 The newly exported DMA mapping is operationally a placeholder

裁决：报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。

## pr-473-27c3210449d8

### L0 — M — 命名、模式、导入与局部风格
Trusted helpers that produce tracked owners use the legacy verifier::returns(proof) attribute and ordinary return binders instead of declaring tracked return values directly.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-474-a6fdca3a754f

### L0 — M — 所有权、资源守恒与对象身份
KVirtArea::query models page-table guard ownership with a 'static lifetime even though atomic mode is established only by a local preemption guard.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-485-6fac7bc837f6

### L0 — M — 运行时行为与生命周期
Three new executable metadata helpers are called by runtime paths but have unimplemented bodies, so metadata writes or borrows can panic instead of performing the required operation.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-487-5170c403b0d7

### L0 — M — 运行时行为与生命周期
The re-enabled Task::current API always returns Some(CurrentTask {}), contradicting its documented None result in bootstrap context; the original task lookup remains commented out.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-492-e7a37a7d7080

### L0 — M — 命名、模式、导入与局部风格
The generated flags field redundantly combines a `ghost` field marker with the `Ghost<T>` wrapper type.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

### L1 — M — 构建、工具链与证明可接受性
The exported macro's Clone implementation uses an unqualified `Ghost` constructor and unconditionally evaluates a ghost-only specification, breaking downstream or documentation builds where that name or ghost code is unavailable.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-499-2d320cbb55fc

### L0 — X — 状态机、不变量与模型语义
The selected pre-repair snapshot verifies a divergent specification-side x86 PageTableEntry implementation while the production implementation remains commented out, so the proofs do not establish the production PTE encoding behavior.

对应报告：无

裁决：标签全部定位before，PR删除替代模型并恢复production实现；after缺陷检测与历史问题识别任务不一致。

## pr-50-5d510a5352a3

### L0 — M — 构建、工具链与证明可接受性
The blanket paging-constants implementation repeats two trait-owned `when_used_as_spec` mappings, causing the supported Verus to reject `lock-protocol` before verification.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-500-5c863f079762

### L0 — M — 命名、模式、导入与局部风格
Two proof lemmas carry unnecessary per-item `non_snake_case` lint suppressions.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-500-6c26d6c45e16

### L0 — F — 规范复用、放置与闲置helper
The restored executable address conversions use duplicate local spec models while the specification module aliases a second model under the exec names.

对应报告：F1 Reuse the canonical frame/metadata conversion specifications

裁决：报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。

## pr-500-e909aa15bb90

### L0 — M — 执行代码保留/放置
The PR moves the existing executable frame/metadata address conversions out of their implementation module into the specification module.

对应报告：无

裁决：报告是frame_to_index/index_to_frame变spec-only；标签是frame_to_meta/meta_to_frame的exec放置错误，不同API及修复。

## pr-501-5646c42516b4

### L0 — F — 运行时行为与生命周期
The newly exposed `VmSpace::activate` API always panics instead of activating the page table.

对应报告：F1 `VmSpace::activate` is neither callable by its intended clients nor implemented

裁决：报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。

## pr-505-cb2be5a80af1

### L0 — F — 运行时行为与生命周期
The PR publicly enables the heap module while commenting out required allocation APIs and global allocator wiring, leaving downstream heap consumers unable to compile or allocate correctly.

对应报告：F2 Required heap functionality is removed by block comments

裁决：报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。

## pr-505-dffa7b932d72

### L0 — M — 规范复用、放置与闲置helper
Generic external specifications for core allocation types are placed inside the heap implementation module instead of the shared vstd_extra external-spec layer.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-511-860ffa221455

### L0 — M — 规范复用、放置与闲置helper
The now-trivial `view_rec_finite` proof helper is unused and unnecessarily expands the proof API.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-515-378590cc39ac

### L0 — F — 运行时行为与生命周期
The public const `RcuOption::new_none` constructor is deleted even though the type's own example and existing API require it for static empty initialization.

对应报告：F1 Restore the const empty constructor without silently widening the trust boundary

裁决：报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。

## pr-518-4cb9ee7caa9e

### L0 — F — 状态机、不变量与模型语义
The non-optional `Rcu` type exposes a `new_none` constructor that creates a nullable inner value, contradicting the type's non-null read semantics.

对应报告：F1 The nullable constructor was moved onto the non-null RCU type

裁决：报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。

## pr-526-614ad9c3f014

### L0 — M — 构建、工具链与证明可接受性
The ktest TestPtConfig implementation omits two required PageTableConfig proof methods, leaving the trait implementation incomplete when checked with proof members retained.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

### L1 — M — 命名、模式、导入与局部风格
Two new page-table proof bodies import arithmetic helpers that are never referenced in their function scopes.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-530-3574febda9d0

### L0 — P — API契约、泛型与边界
The paging-constants proof newly requires every configuration to use the CPU-global base page size and entry ratio, extending an existing hardcoded level-count restriction.

对应报告：F1 The generic paging-constants lemma promises a property violated by an existing implementation

裁决：同类硬编码泛型约束，仅报告已有NR_LEVELS等式；未报告本次新增BASE_PAGE_SIZE及entry ratio。before:146已有该level等式，新增性判断错误。

## pr-532-9200dd2fb210

### L0 — M — API契约、泛型与边界
The selected revision carries forward CPU-specific paging requirements into newly generic paging proofs, so those proofs still exclude otherwise valid layouts.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-534-5ba756b22a68

### L0 — M — 命名、模式、导入与局部风格
A loop invariant redundantly casts every address and size operand to `int` instead of stating the same equality in their native arithmetic form.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-546-269c2b583824

### L0 — M — API契约、泛型与边界
The segment clone and slice contracts require `rc + 1 < REF_COUNT_MAX`, rejecting the valid boundary `rc = REF_COUNT_MAX - 1` even though the execution saturation guard permits the increment to `REF_COUNT_MAX`.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-547-4510bdeecf13

### L0 — M — 所有权、资源守恒与对象身份
The trusted Entry::new mutable-borrow contract promises that the borrowed PageTableGuard has its original value when the borrow ends, even though the returned Entry exposes that guard through a public mutable node reference.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-562-581ce53261be

### L0 — F — 命名、模式、导入与局部风格
A checked proof function retains an `axiom_` name instead of the required `lemma_` prefix.

对应报告：F1 Rename the proved fact as a lemma

裁决：报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。

## pr-577-94715eb8c48e

### L0 — M — 验证文档
The public `SegmentOwner` verification documentation still describes per-frame permissions and an obligation token that the simplified type no longer contains.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-595-c34b8882f0e1

### L0 — M — 构建、工具链与证明可接受性
The README command described as verifying only ostd omits the focus flag, so it also re-checks dependency proofs instead of limiting verification to the root crate.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-612-0886ccdd5411

### L0 — M — API契约、泛型与边界
The page-table item contract guarantees raw-value recovery after converting a raw value to an item, but does not guarantee recovery of the original item after converting it to raw form, despite the documented round-trip requirement.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-614-0f6d3afea7b8

### L0 — M — 命名、模式、导入与局部风格
Two proof helpers that construct tracked resources use the `lemma_` prefix instead of the ownership-role prefix `tracked_`.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

### L1 — M — 命名、模式、导入与局部风格
Three reusable proof facts are missing the required `lemma_` prefix.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

### L2 — M — 执行代码保留/放置
Proof work rewrites the executable `NR_LEVELS()` method instead of preserving its original direct return shape.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-615-b995aae1ffdb

### L0 — F — 命名、模式、导入与局部风格
Two proof helpers that construct tracked entries are named with the `lemma_` prefix instead of the repository's `tracked_` prefix for tracked-value helpers.

对应报告：F1 The new tracked constructors are single-use public helpers with the wrong proof-role name

裁决：报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。

## pr-616-bd8357d3afaa

### L0 — F — 执行代码保留/放置
The proof removes `external_body` by decomposing the original one-line `page_size` execution into new executable locals and a temporary result instead of keeping all proof scaffolding in proof mode.

对应报告：F1 Proof work rewrites the executable implementation without retaining its original form

裁决：报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。

## pr-617-a00a7b6fa954

### L0 — F — 所有权、资源守恒与对象身份
The DMA accessors expose values through fresh ghost snapshots that are only required to satisfy the inner invariant and are never related to this `DmaStream` or to a tracked observation of its current `RwArc` state, so the contracts do not establish that returned values describe the receiver being queried.

对应报告：F1 The getter snapshots are not tied to the receiver

裁决：直接命中getter任意ghost witness未绑定receiver的身份关系。

## pr-626-cef66d9ffb91

### L0 — M — 命名、模式、导入与局部风格
New Metadata specification import is added as another standalone same-crate import.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-628-096c166e5ce6

### L0 — M — 命名、模式、导入与局部风格
The embedded linked-list ownership helpers mutate tracked owners and transfer frame permissions but lack the tracked_ resource-role prefix.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-63-742ee43ba12c

### L0 — M — 运行时行为与生命周期
`PHYS_ADDR_MASK` includes the x86 NO_EXECUTE flag bit, so extracting the physical address from an NX page-table entry returns bit 63 as address data.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-632-1be8099780ff

### L0 — M — 所有权、资源守恒与对象身份
The ghost frame_obligations ledger can be cleared without consuming outstanding tracked DropObligation tokens, undermining the clean-boundary accounting.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-634-64d2718d5a4d

### L0 — M — 命名、模式、导入与局部风格
A reusable checked proof fact is named `segment_drop_embedded` instead of using the required `lemma_` prefix.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-636-b0d5450c6e0c

### L0 — M — 规范复用、放置与闲置helper
The tracked frame constructor repeats the physical-address alignment and upper-bound conjunction already provided by has_safe_slot.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

### L1 — M — 命名、模式、导入与局部风格
The tracked frame constructor splits the contiguous parent-level bound into separate clauses instead of the chained comparison 1 <= parent_level < NR_LEVELS.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-64-900e41671221

### L0 — M — 状态机、不变量与模型语义
`PageTableEntryPerms::wf` guards every per-entry invariant with `len < 512` while also requiring `len == 512`, making all 512 PTE well-formedness obligations vacuous.

对应报告：无

裁决：报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。

## pr-646-5053290d119e

### L0 — M — 规范复用、放置与闲置helper
The local broadcast block repeats three TreePath facts already activated by the module-level group_ghost_tree_lemmas.

对应报告：无

裁决：报告无finding；未检查局部broadcast与模块group已激活事实的重复。

## pr-65-625495f69559

### L0 — M — API契约、泛型与边界
Both PageFlags::RW implementations map specification calls to X_spec, so proofs observe execute-only bits 4 instead of the executable read/write bits 3.

对应报告：无

裁决：F1/F2讨论allocate_pt输入与层级契约，未识别两个RW的when_used_as_spec错误指向X_spec。

## pr-651-4fe5602573ae

### L0 — M — 规范复用、放置与闲置helper
The single-use `tracked_pop_level_owner` proof helper unnecessarily expands the cursor-owner proof API instead of keeping the tracked state transition at its only call site.

对应报告：无

裁决：唯一意见是segment文档引用已删除raw_count；不是单调用tracked_pop_level_owner的抽象边界问题。

## pr-656-ffafeb7a696a

### L0 — M — 命名、模式、导入与局部风格
`CursorKind` is a proof-only model enum but is declared as an ordinary enum instead of a ghost type.

对应报告：无

裁决：报告检查了CursorEntry字段模式，但未指出CursorKind枚举本身缺ghost分类。

## pr-658-4f0076d7cb29

### L0 — M — 运行时行为与生命周期
The custom `ManuallyDrop<T>` stores its payload as an ordinary `T`, so Rust's automatic field drop glue still destroys `T` when the wrapper is dropped instead of preserving manual-drop semantics.

对应报告：无

裁决：F1是into_inner恢复账本权限问题，未指出包装器value:T会执行自动drop；同属ManuallyDrop不等于同根因。

## pr-659-77c06f3ce196

### L0 — M — 规范复用、放置与闲置helper
The single-use lemma_vm_writer_fill_zeros_embedded helper has an empty body and only forwards unchanged owner facts, adding a redundant proof boundary.

对应报告：无

裁决：F3要求修改同一helper的命名前缀，未指出其空体、单调用和冗余边界；F1/F2为其他契约问题。

## pr-668-12d847140254

### L0 — M — 所有权、资源守恒与对象身份
The public tracked_from_unused_owner axiom constructs a metadata owner and asserts the entire region invariant without any precondition, even while guaranteeing that the region slot map is unchanged.

对应报告：无

裁决：报告聚焦运行时unimplemented和Repr布局，未识别tracked_from_unused_owner无前提保持slots却断言regions.inv的矛盾。

## pr-674-fc2045c29e48

### L0 — F — 规范复用、放置与闲置helper
The generic AtomicUsize::from_ptr external specification is declared inside the page-table implementation instead of the shared external-specification layer.

对应报告：F3 The generic `AtomicUsize::from_ptr` specification belongs in the reusable specification layer

裁决：F3明确要求将同一个AtomicUsize::from_ptr通用外部规格迁至共享层，根因与位置一致。

### L1 — M — API契约、泛型与边界
The as_mut_ptr contract has no postcondition relating its returned pointer to the tracked array element, so callers cannot derive that pointer-to-element correspondence from the modular specification.

对应报告：无

裁决：F1讨论E布局、atomic对齐及写入关系；提到as_mut_ptr缺布局保证，但未指出返回指针与tracked数组元素之间缺后置关系。

## pr-675-6d0431e7ba0c

### L0 — M — 所有权、资源守恒与对象身份
The trusted drop_meta_in_place contract checks reference-count and list-membership values from an owner that is not required to describe the receiver, so those checks do not establish exclusive access to the metadata being destroyed.

对应报告：无

裁决：F1是into_raw忘记抑制原Frame析构，未指出drop_meta_in_place用另一slot owner证明receiver独占性。

## pr-677-1de689b269f2

### L0 — M — 命名、模式、导入与局部风格
Adjacent verus! blocks split contiguous verified items without an intervening executable Rust item.

对应报告：无

裁决：唯一意见是enqueue新增运行时clone；未指出相邻verus块可合并。

## pr-679-f7dfb8525a55

### L0 — M — 命名、模式、导入与局部风格
The reusable insert_before_slot_distinct proof fact lacks the required lemma_ naming prefix.

对应报告：无

裁决：报告定位同一helper但只要求去掉nn参数，未指出insert_before_slot_distinct缺lemma_前缀。

## pr-69-931cc78db2e3

### L0 — M — API契约、泛型与边界
The PTE physical-address mask retains bits 52 through 62, so reserved or software bits above the x86-64 physical-address field are returned as address bits.

对应报告：无

裁决：报告讨论new_pt执行表达式重排，未指出PHYS_ADDR_MASK保留52至62位的错误。

## pr-692-1c768aa6f173

### L0 — M — 命名、模式、导入与局部风格
The new Jiffies::from_spec body repeats the fully qualified duration_new_spec path instead of importing the free specification helper.

对应报告：无

裁决：报告关注timer执行代码删除和Duration规格上游化，未指出from_spec重复全限定路径。

## pr-699-6f1ed3a06cce

### L0 — M — 命名、模式、导入与局部风格
Adjacent verification imports from one crate are unnecessarily split.

对应报告：无

裁决：未指出同crate验证imports拆分；其他意见是状态不变量、前置条件和执行代码变化。

### L1 — M — 命名、模式、导入与局部风格
A contiguous four-endpoint bound is split into three clauses.

对应报告：无

裁决：F2批评范围前提过强，未要求将四端点写为链式比较；语义限制与表达规范不同。

## pr-70-ca8ef69001b0

### L0 — M — 显式admit/external_body证明缺口
`lemma_va_range_get_guard_level` exports the guard-level bound used for path indexing and loop invariants while its entire proof body is `admit()`.

对应报告：无

裁决：唯一意见是PTE地址掩码后的可信roundtrip矛盾，未指出guard-level lemma的admit。

### L1 — M — 显式admit/external_body证明缺口
`lemma_va_range_get_tree_path` exports valid NodeIds and the exact guard-path length while its entire proof body is `admit()`.

对应报告：无

裁决：未指出va_range_get_tree_path的路径有效性及长度保证由admit导出。

### L2 — M — 显式admit/external_body证明缺口
`NodeHelper::lemma_is_child_level_relation` exports the one-level parent/child relationship while its entire proof body is `admit()`.

对应报告：无

裁决：未指出lemma_is_child_level_relation的父子层级证明缺口。

### L3 — M — 显式admit/external_body证明缺口
`lemma_va_level_to_nid_inc` exports the correspondence between virtual-address traces and the next child NodeId while its entire proof body is `admit()`.

对应报告：无

裁决：未指出lemma_va_level_to_nid_inc的地址轨迹与child关系证明缺口。

## pr-701-a6a2b2dbee26

### L0 — M — 构建、工具链与证明可接受性
The DV submodule is advanced to a newer Verus toolchain without regenerating the root `Cargo.lock`, leaving the committed dependency versions inconsistent with the toolchain used by verification.

对应报告：无

裁决：报告无finding且只核对DV参数传播，未检查子模块升级与根Cargo.lock同步。

## pr-702-6288e960b7a1

### L0 — M — 命名、模式、导入与局部风格
Tracked fields redundantly repeat their enclosing struct mode.

对应报告：无

裁决：报告关注WaitQueue计数溢出assume，未指出tracked struct重复字段mode。

## pr-703-9481481143aa

### L0 — M — 命名、模式、导入与局部风格
The fields of a `ghost struct` redundantly repeat the `ghost` mode marker.

对应报告：无

裁决：F1引用了ghost字段声明，但未将重复ghost标记作为问题。

### L1 — M — 规范复用、放置与闲置helper
The allocator range is modeled with a custom ghost struct instead of the canonical `Range<int>` model.

对应报告：无

裁决：F1要求扩展状态模型，未指出两端点自定义模型可复用Range<int>。

## pr-704-0ae594a446f7

### L0 — M — 规范复用、放置与闲置helper
The unchanged-cursor branch repeats equality for every CursorMutModel field instead of stating equality of the whole cursor model.

对应报告：无

裁决：两条意见针对借用键比较与cursor.wf，不是None分支逐字段相等可合并为整体相等。

## pr-706-3d7ea1276689

### L0 — M — 命名、模式、导入与局部风格
The allocator proof splits the lower and upper bounds on the same index into separate comparisons instead of a chained comparison.

对应报告：无

裁决：未指出allocator索引上下界应使用链式比较。

### L1 — M — 命名、模式、导入与局部风格
New ghost contracts repeatedly use the fully qualified crate::arch::io::MAX_IO_PORT constant instead of importing it.

对应报告：无

裁决：未指出MAX_IO_PORT在新契约中反复使用全限定路径。

## pr-71-ddd2e78f5931

### L0 — M — 所有权、资源守恒与对象身份
`cur_entry` does not expose that its returned `Entry.node` is the current path node, so the map caller cannot prove the returned PTE address relative to `cur_entry.node`.

对应报告：无

裁决：报告把assume换assert视为改进且无finding，未发现Entry::new_at/cur_entry缺node身份后置关系。

## pr-710-81e3abfc0815

### L0 — M — 构建、工具链与证明可接受性
The build-selected architecture interface unconditionally exports the x86 model and aliases CurrentArch to X86Arch without target_arch guards, so it does not select the model according to the target architecture.

对应报告：无

裁决：F1是泛型trait无条件获取CPU常量，未指出CurrentArch/x86导出缺target_arch条件。

### L1 — M — 规范复用、放置与闲置helper
The spec helper bypasses the public dual-mode paging-constant methods and calls their generated _spec implementation names directly.

对应报告：无

裁决：未指出spec helper绕过公共双模式API直接调用生成的_spec名称。

## pr-718-80dcb9bc16eb

### L0 — M — 命名、模式、导入与局部风格
The sequence-union membership contract spells out an indexed existential instead of using the equivalent Seq::any predicate.

对应报告：无

裁决：未指出序列存在量词可使用Seq::any。

### L1 — M — 命名、模式、导入与局部风格
The nonempty-range postcondition spells out an indexed universal instead of using Seq::all for that element-wise property.

对应报告：无

裁决：未指出非空range的逐元素全称量词可使用Seq::all；不将其他iterator契约意见算命中。

### L2 — M — 规范复用、放置与闲置helper
The private lemma_seq_range_union_small helper has only one caller and can be kept local to that proof instead of expanding the module proof API.

对应报告：无

裁决：未指出lemma_seq_range_union_small只有一个调用者、应局部化。

## pr-723-d90d548c92ae

### L0 — M — 命名、模式、导入与局部风格
The proof helper borrow returns a tracked resource reference but lacks the required tracked_ ownership-role prefix.

对应报告：无

裁决：F1是wf改Inv，F2是辅助lemma布局；未指出borrow应有tracked_前缀。

## pr-728-7e0d60333942

### L0 — M — 命名、模式、导入与局部风格
New proof-only constant and invariant marker use ordinary struct mode.

对应报告：无

裁决：报告讨论分配资源的真实性，未指出FreelistConstant/FreelistInvariant应为ghost模型类型。

### L1 — M — 命名、模式、导入与局部风格
Several facts repeatedly guard and project the same Option payload.

对应报告：无

裁决：未指出target_node的Some载荷重复投影可绑定一次。

## pr-738-b759e2fe2adc

### L0 — F — 执行代码保留/放置
The as_ptr implementation replaces self.val.get() with a cast of a pointer to the enclosing PCell, but preserves only the old expression in a comment without explaining the executable divergence.

对应报告：F1 The returned pointer is derived from the `PCell` wrapper, not its stored value

裁决：F1明确指出同一as_ptr执行替换缺表示依据，并要求使用实际cell accessor、保留原get行为；计入原保存/解释根因，不据此确认其条件性运行时后果。

## pr-739-c6323145118d

### L0 — M — 执行代码保留/放置
The patch inserts an inline Verus `returns` clause into the signature of an already-verified executable getter instead of attaching the new contract with `#[verus_spec]`.

对应报告：无

裁决：报告明确肯定inline returns；未识别既有exec getter应以verus_spec附加契约的约定。

## pr-74-519268844721

### L0 — M — 显式admit/external_body证明缺口
`pte_index` exports the less-than-512 `valid_pte_offset` guarantee while its decisive low-nine-bit range proof ends in `admit()`.

对应报告：无

裁决：报告是MetaSlotPerm全局归属变弱，未指出pte_index九位掩码界限仍由admit证明。

## pr-742-32f28ee1260b

### L0 — M — 规范复用、放置与闲置helper
The ghost old_store binding is unused in its function after the proof merge.

对应报告：无

裁决：未指出embedding函数内old_store未使用。

### L1 — M — 命名、模式、导入与局部风格
The patch moves the original BitVec import above core and mixes it with verification-added imports instead of preserving the executable import grouping.

对应报告：无

裁决：未指出BitVec原始import分组被改变。

### L2 — M — 规范复用、放置与闲置helper
The private lemma_first_zero_seq_ext_equal helper has no caller outside its own recursive proof.

对应报告：无

裁决：未指出lemma_first_zero_seq_ext_equal除自身递归外无调用。

## pr-75-0ff02a61dc17

### L0 — M — 所有权、资源守恒与对象身份
The intermediate Child::None allocation path assumes that the current PTE address owns an unused-PTE token immediately before consuming that linear token.

对应报告：无

裁决：唯一意见是旧prototype删除后留下imports；未指出map路径假设unused-PTE token存在再消费。

## pr-76-58c6aac4274b

### L0 — M — 状态机、不变量与模型语义
recursive_trace duplicates reached children instead of including the starting node, while the admitted trace length theorem is false even for an empty path.

对应报告：无

裁决：报告仅讨论执行表示/API变化，未指出recursive_trace重复child及空路径长度定理错误。

### L1 — M — API契约、泛型与边界
seek_trace_next exports an admitted child/trace equality without requiring a resolvable path, present child, valid depth, or in-range child index.

对应报告：无

裁决：未指出seek_trace_next缺路径、child、深度与索引前提。

### L2 — M — 状态机、不变量与模型语义
The admitted removal lemmas claim a removed child is absent from the entire subtree even though the tree invariant permits the same child value at another key or path.

对应报告：无

裁决：未指出允许重复child值时删除后全子树不存在定理不成立。

## pr-763-027c97275075

### L0 — M — 执行代码保留/放置
The cursor proof migration deletes preserved original Rust debug assertions and path-update expressions, losing the source context for the adapted executable code.

对应报告：无

裁决：报告认为删除的原始debug_assert/路径更新注释无问题，未识别迁移来源记录丢失；before定位是被删除证据，不是已修复标签。

## pr-770-28ec70b8e3f2

### L0 — M — 命名、模式、导入与局部风格
The zero-initialized CpuSet contract spells out an indexed universal instead of the equivalent Seq::all predicate.

对应报告：无

裁决：未指出zero构造后置条件的forall可用Seq::all。

### L1 — M — 规范复用、放置与闲置helper
Private CpuSet representation and bounds lemmas interrupt the public model and API section instead of residing in the trailing auxiliary section.

对应报告：无

裁决：未指出private CpuSet辅助证明插入公共模型/API区。

## pr-775-d3b5ea030112

### L0 — M — 规范复用、放置与闲置helper
A private recursive construction helper unnecessarily expands the associated proof API.

对应报告：无

裁决：报告明确将private single-purpose helper视为合理，未指出单外部调用的递归构造helper应局部化。

## pr-778-994b5b0a00cf

### L0 — M — 规范复用、放置与闲置helper
New contains helper has no current consumer.

对应报告：无

裁决：唯一意见是as_aligned排除短range，未指出contains helper无消费者。

### L1 — M — 规范复用、放置与闲置helper
New overlaps helper has no current consumer.

对应报告：无

裁决：未指出overlaps helper无消费者；不因同一模型文件而匹配。

## pr-78-6082813ffdda

### L0 — F — 构建、工具链与证明可接受性
The partial GuardInPath rename removes variant None but leaves six cursor predicates and invariants referring to it, so the Verus target no longer compiles or verifies.

对应报告：F1 The removed `None` variant remains in cursor invariants

裁决：F1准确枚举6处GuardInPath::None残留，并区分合法Option::None；与标签根因和修复一致。

## pr-782-0195dc456673

### L0 — F — 规范复用、放置与闲置helper
`MemoryRegionArray` keeps an `Inv` implementation for the same `count <= LEN` predicate already enforced by its new type invariant.

对应报告：F1 Preserve the invariant of elements returned by `Deref`

裁决：F1除元素有效性主论点外，明确指出type_inv与Inv重复count谓词、存在漂移并要求唯一规范定义；匹配此子声明，不为额外元素论点背书。

## pr-782-1a8ec593d670

### L0 — M — 规范复用、放置与闲置helper
The replacement public `inv()` spec helper only forwards to `type_inv()` and has no justified consumer after the type-invariant migration.

对应报告：无

裁决：报告明确保留inv兼容别名且无finding；未指出其无必要消费者。

## pr-782-4f44ff343670

### L0 — M — 命名、模式、导入与局部风格
The `Deref` contract spells sequence-view equality as a length clause plus a triggered pointwise quantifier instead of one direct model equality.

对应报告：无

裁决：报告是push排除满数组Err输入，未指出Deref逐点等式可改model整体等式。

## pr-789-8943e8f25420

### L0 — M — 规范复用、放置与闲置helper
Identical per-header length accessors are hand-copied.

对应报告：无

裁决：未指出重复header length accessor应生成；F2建议生成共享device_scopes accessor不是同一根因。

### L1 — F — API契约、泛型与边界
A public parser precondition has no externally usable introduction rule.

对应报告：F1 Make the caller-facing validity predicate unfoldable

裁决：F1准确识别valid_device_scopes为public closed且无引入lemma，调用者无法证明输入前提。

## pr-797-07c694bbca2a

### L0 — M — API契约、泛型与边界
The public normalization model is opaque to external contract consumers.

对应报告：无

裁决：F1引用aligned_regions作参数，但未指出其自身闭合造成输入归一化模型不透明；不能用泛称predicates覆盖未点出的模型。

### L1 — F — API契约、泛型与边界
A public partition guarantee has no exported elimination rule.

对应报告：F1 The normalization result is specified through predicates that callers cannot use

裁决：F1明确指出closed is_partition无法导出contiguous/aligned事实，建议公开characterization。

### L2 — M — 规范复用、放置与闲置helper
Private sweep-boundary scaffolding interrupts the public model/API section.

对应报告：无

裁决：未指出region_boundaries私有证明辅助项打断公共API区。

### L3 — F — API契约、泛型与边界
Public coalescing guarantee is closed without an exported characterization.

对应报告：F1 The normalization result is specified through predicates that callers cannot use

裁决：F1明确指出closed coalesced无法导出相邻类型不同，并提出对应公开lemma。

### L4 — F — API契约、泛型与边界
The public type-preservation guarantee has no usable external meaning.

对应报告：F1 The normalization result is specified through predicates that callers cannot use

裁决：F1明确指出preserves_types及selected_type不透明，无法得到覆盖地址类型；与另两条子声明分别匹配。

## pr-802-2d0e9d0e7c27

### L0 — M — 命名、模式、导入与局部风格
The Layout external specifications use a generic self_ receiver and explicit dereferencing instead of a role-specific receiver name and method-call auto-dereferencing.

对应报告：无

裁决：未指出Layout规格receiver应使用角色名及自动解引用；上游化建议不等于命名规范命中。

## pr-809-9d1b88dd7b02

### L0 — M — 规范复用、放置与闲置helper
Already correctly typed ranges are repeatedly reconstructed field-for-field.

对应报告：无

裁决：未指出同类型Range逐字段重建冗余。

### L1 — M — 命名、模式、导入与局部风格
Internal resource fields unnecessarily expose representation to the parent module.

对应报告：无

裁决：未指出FreelistResource字段不必要的父模块可见性。

### L2 — M — 命名、模式、导入与局部风格
The changed contract binds the same Ok payload in separate implication blocks.

对应报告：无

裁决：未指出同一Ok载荷在多个implication中重复绑定。

## pr-812-4121eb1c32b0

### L0 — M — 命名、模式、导入与局部风格
Contract queries Result shape through is_ok rather than the prescribed spec form.

对应报告：无

裁决：F2批评Ok/Err语义方向缺失，但未指出is_ok应改为spec的is Ok；两者不是同一义务。

## pr-819-15e19d347120

### L0 — F — 命名、模式、导入与局部风格
Volatile-read address constraints access the pointer view representation.

对应报告：F3 Use the established pointer-address model

裁决：F3明确覆盖ptr.rs115-143的ptr@.addr，要求使用addr()，包含volatile read。

### L1 — F — 命名、模式、导入与局部风格
Volatile-write address constraints access the pointer view representation.

对应报告：F3 Use the established pointer-address model

裁决：F3明确覆盖同一区域的指针address accessor，包含独立volatile write；共享报告项记录两个具体操作位置。

## pr-82-7861acbd2ab1

### L0 — F — API契约、泛型与边界
The external specification for unsigned `ilog2` accepts zero even though every unsigned primitive `0.ilog2()` panics, so the public wrapper contract omits the operation's required nonzero domain.

对应报告：F1 The trusted `ilog2` specification omits its required nonzero precondition

裁决：F1准确指出unsigned ilog2(0) panic与缺nonzero前置条件，并给出x>0修复。

## pr-820-23c7625612f0

### L0 — M — 规范复用、放置与闲置helper
The newly added lemma_nonempty_isa_overrides_without_timer proof helper has no caller.

对应报告：无

裁决：唯一意见是map_isa_pin_to未导出映射性质，未指出lemma_nonempty_isa_overrides_without_timer无调用。

### L1 — M — 规范复用、放置与闲置helper
The newly added lemma_empty_isa_overrides proof helper has no caller.

对应报告：无

裁决：未指出lemma_empty_isa_overrides无调用。

### L2 — M — 规范复用、放置与闲置helper
The newly added lemma_isa_override_origin proof helper has no caller.

对应报告：无

裁决：未指出lemma_isa_override_origin无调用。

## pr-847-deb42343023f

### L0 — M — 运行时行为与生命周期
The RISC-V set_prop implementation turns an absent PTE into a present entry, so the shared trait contract was weakened for one architecture instead of preserving its documented no-op behavior.

对应报告：无

裁决：报告讨论架构执行模块删除及satp状态模型，未指出set_prop给absent PTE置VALID。

## pr-855-5c9e493bb78b

### L0 — F — API契约、泛型与边界
The PR moves CPU-layout equalities from a temporary trusted helper into mandatory PagingConstsTrait requirements, preventing a valid three-level IOMMU configuration from satisfying the trait.

对应报告：F1 The generic paging-constants contract is false for an existing implementation

裁决：F1准确对比CPU四级与IOMMU三级，识别将全局等式移入泛型trait义务的限制；不据匹配额外确认所有不健全性措辞。

## pr-856-619ad58877f8

### L0 — F — 命名、模式、导入与局部风格
The unconditional vstd arithmetic and prelude imports are split into separate declarations instead of one grouped import.

对应报告：F1 Keep the new `vstd` proof import in the existing crate-level import.

裁决：F1定位同一两条vstd import并提出分组合并，明确保留cfg import独立。

## pr-857-51bb973322ec

### L0 — M — 执行代码保留/放置
The verification patch rewrites `unmap`'s executable overflow check locally instead of first fixing and adopting the upstream Asterinas implementation.

对应报告：无

裁决：报告没有指出unmap先改本地overflow检查而未先修upstream的流程问题。

### L1 — M — 执行代码保留/放置
`wait_until_or_cancelled` rewrites executable Option control flow without removing the proof cheat or otherwise benefiting the verification.

对应报告：无

裁决：F1指出残留admit及closure状态差异，但未将无收益的Option执行重写作为问题；不因同一分支而匹配。

## pr-860-a4749f699922

### L0 — M — 命名、模式、导入与局部风格
New spec imports precede the vstd group and lack the prescribed stacking.

对应报告：无

裁决：未指出weak_monitor验证imports分组顺序。

### L1 — M — 命名、模式、导入与局部风格
The same required Option payload is projected repeatedly.

对应报告：无

裁决：未指出parent.info的重复Some载荷投影。

### L2 — M — 命名、模式、导入与局部风格
An exact boolean return is expressed through a named ensures equality.

对应报告：无

裁决：未指出complete的精确布尔结果应使用returns。

### L3 — M — 规范复用、放置与闲置helper
Private singleton-choice scaffolding interrupts the API section.

对应报告：无

裁决：未指出singleton choice私有lemma应后置。

### L4 — M — 命名、模式、导入与局部风格
A free spec function is imported but unused in this module.

对应报告：无

裁决：未指出report_covers为未使用的free predicate import。

### L5 — M — 规范复用、放置与闲置helper
Two independently maintained predicates encode the same record-observation relation.

对应报告：无

裁决：未指出cpu/retirement重复record-observation谓词。

### L6 — M — 规范复用、放置与闲置helper
Compare-exchange repeats its root's existing acceptance predicate.

对应报告：无

裁决：F1讨论compare_exchange失败返回缺接受关系，未指出前提应复用self.root.accepts(value)。

## pr-862-637c0417fccd

### L0 — X — 状态机、不变量与模型语义
`is_partition` places pairwise disjointness and full-union coverage inside a per-part implication, so an empty `parts` set vacuously partitions every set, including a non-empty `s`.

对应报告：无

裁决：标签只定位before；diff把pairwise_disjoint和union equality移出forall，after已排除空parts划分非空s。报告在Evidence中正确解释修复，不应要求其作为after缺陷报告。

## pr-865-f93f960594be

### L0 — M — 命名、模式、导入与局部风格
**Type:** group-imports-by-crate
**Problem:** The exec import header interleaves verification-added imports with inherited ones in one pile: `crate::specs` facade at :2 sits above `alloc`/`core` while the `vstd`/`vstd_extra` group (:5-6) sits below them, with no blank-line group separation; the canonical sibling shape (ostd/src/arch/riscv/mm/mod.rs:1-17) blank-separates vstd/vstd_extra, the `crate::specs` facade, alloc, core, and the crate exec group. Fix: regroup this header to that shape — blank-line-separated verification-added groups above the inherited imports.

对应报告：无

裁决：未指出LoongArch exec header验证imports与原imports混杂。

### L1 — M — 命名、模式、导入与局部风格
The newly added vaddr_range_proofs module import is never referenced in the LoongArch specification module.

对应报告：无

裁决：未指出vaddr_range_proofs模块import无引用。

### L2 — M — 命名、模式、导入与局部风格
**Type:** organize-proof-imports
**Problem:** `vstd::arithmetic::power2::lemma2_to64()` is fully qualified at :97 and :111 although the lemma is imported unqualified at :2 and called unqualified at :81-82 in the same file. Fix: use the unqualified call form.

对应报告：无

裁决：未指出lemma2_to64已导入却仍用全限定路径。

### L3 — M — 规范复用、放置与闲置helper
Two public cross-module paging lemmas are placed in an unlabeled trailing proof block with private helpers instead of separating the public proof API from auxiliary scaffolding.

对应报告：无

裁决：未指出公共跨模块lemma与私有尾部辅助证明混排。

### L4 — M — API契约、泛型与边界
**Type:** complete-external-contracts
**Problem:** `set_prop_req`'s present-branch imposes raw-word byte-level obligations unpublished on the shared surface this PR edited: bit 12 / `GLOBAL_IN_HUGE` (PPN bit 0, inside `PHYS_ADDR_MASK`) must be clear (:475) and the property must not be `GLOBAL` (:474), because exec `set_prop` (:532) and `raw_set_prop_spec` (:733) clear IS_BASIC without restoring it. The crate's own `new_page` produces exactly the excluded entries (odd frames keep bit 12 via `paddr & PHYS_ADDR_MASK` at :365, then re-OR IS_BASIC at :370; `lemma_new_page` :961 has no parity qualifier), the arch-neutral caller bridges the predicate through the pre-existing `assume(pte.set_prop_req(new_prop))` at ostd/src/mm/page_table/node/entry.rs:1294, and the trait doc updated in this PR (ostd/src/mm/page_table/mod.rs:1521) states only that absent-entry behavior is implementation-specific. Fix: either preserve IS_BASIC across `set_prop` (root cause — then both guards can go) or document these present-entry restrictions on the shared trait doc, beside `set_prop_ensures` (ostd/specs/arch/loongarch/mod.rs:29), and in `lemma_new_page`'s doc.

对应报告：无

裁决：唯一意见是架构执行模块删除，未检查set_prop清IS_BASIC造成bit12/GLOBAL限制。

## pr-868-c4d83ca80c61

### L0 — M — 所有权、资源守恒与对象身份
The LinkedList pop_front and pop_back contracts consume the tracked list owner by value but return only the removed frame owner, leaving callers without the permissions needed to keep using the remaining list.

对应报告：无

裁决：报告无真实finding（Low表格None只是占位）；未指出pop消费list owner却未返回剩余list权限。

## pr-870-d808e2c9c911

### L0 — M — 规范复用、放置与闲置helper
The CalleeRegs zero constructor duplicates its struct literal in the return contract and executable body instead of sharing a dual-mode model.

对应报告：无

裁决：报告要求还原构造体执行排版，未指出同一literal在spec/exec重复、应使用dual_spec。

## pr-871-61c301b7f35d

### L0 — M — 构建、工具链与证明可接受性
The verification-statistics CI job disables Verus bootstrap but then builds line_count from the untracked tools/verus source tree, so a clean runner has no Cargo manifest to build.

对应报告：无

裁决：报告识别统计脚本及workflow其他问题，但未指出verus:false使干净runner缺line_count源码manifest。

## pr-879-902b28e19560

### L0 — M — 规范复用、放置与闲置helper
A newly added private roundtrip lemma has no consumer.

对应报告：无

裁决：报告无finding，并检查了嵌套恢复lemma的内容；未发现lemma_nested_restore没有消费者。

## pr-886-fe5eb7f3e6aa

### L0 — M — 命名、模式、导入与局部风格
The None equivalence repeats a direction already implied by the Some contract.

对应报告：无

裁决：未指出Some保证已蕴含None等价式的一个方向；意见为信任边界和import。

## pr-887-431e3c7c0000

### L0 — M — 执行代码保留/放置
Executable bitflags implementation/API changes lack their own adjacent divergence marker.

对应报告：无

裁决：F1是删除生产执行路径，未识别bitflags实现替换缺独立Origin标记。

### L1 — M — 命名、模式、导入与局部风格
New getter contracts express exact results using named ensures equalities.

对应报告：无

裁决：未指出四个getter应以returns表达精确结果。

## pr-890-5b1e96c2ec18

### L0 — P — 构建、工具链与证明可接受性
The newly added lemma_filter_laws helper lacks its opening verus! block while retaining the closing delimiter, so util/ops.rs cannot parse; its signature also omits the iter parameter used by its contract and three-argument call.

对应报告：F1 `lemma_filter_laws` has an inconsistent signature and call

裁决：F1命中lemma_filter_laws缺iter形参与调用arity不一致，但漏掉更早的verus!开块缺失/孤立闭括号；标签组合两个helper引入缺陷，仅部分覆盖。

## pr-892-34407c0508d2

### L0 — M — 规范复用、放置与闲置helper
The Frame::from_raw_spec model retains an unused paddr parameter even though the constructed frame is determined entirely by slot_perm and metadata_perm.

对应报告：无

裁决：报告无finding；未指出from_raw_spec的paddr参数未使用。

## pr-895-910070850974

### L0 — M — 命名、模式、导入与局部风格
The `set_bit` helper redundantly stacks bare `#[verus_verify]` on top of `#[verus_verify(dual_spec)]`.

对应报告：无

裁决：报告讨论PCI执行代码删除，未指出verus_verify与dual_spec属性重复。

## pr-897-657bce05372e

### L0 — M — 规范复用、放置与闲置helper
**Type:** defer-auxiliary-proof-functions
**Problem:** The `FrameRawPermsRef` model block — struct (:295), `View` (:300-312), `Inv` (:314-318) — is defined below the `NonNullPtr for Frame` impl (:143-293) that binds it (`type RefPermission<'a> = FrameRawPermsRef<'a>` at :150) and below the proof fns that construct it (`borrow_ref_perm`/`borrow_perm_as_ref_perm`, :229-237), while the guideline puts types, public `spec fn`s, and `View`/`Inv` impls in the upper part of the file. Fix pointer: move the block above the impl — same layout as `BoxRef`/`ArcRef` preceding their impls (`non_null/mod.rs:161→:206, :333→:367`) and as this file already leads with `FrameRef` (:33-69).

对应报告：无

裁决：未指出FrameRawPermsRef与View/Inv定义在使用它的公共impl之后。

### L1 — F — 所有权、资源守恒与对象身份
**Type:** implement-inv-for-models; api-postconditions
**Problem:** With the `Permission: Inv`/`RefPermission: Inv` bounds dropped, Box/Arc export permission validity unconditionally (`non_null/mod.rs:260, 276, 409, 424`; `either.rs` inherits via delegation), but Frame's compensation never exports it forward: `ptr_perm_match` (:205-209) is slot-only, `rel_perm` (:211-216) makes validity an antecedent only, and `ref_rel_perm` (:222-227) guards every conjunct under `r.inv()` — so the trait's sole postcondition (`raw_as_ref`'s `ensures Self::ref_rel_perm(ret, perm@)`, `non_null/mod.rs:135-143`) is vacuously satisfiable for Frame and no chain guard re-derives permission validity anymore (`rcu/mod.rs:88, 207, 363, 386, 462, 513, 1108`; the merge base carried `perm.resource().inv()` in the guard's `type_inv`). Fix pointer: lift onto the contract the implication `raw_as_ref`'s body already proves (extra ensures :243-244) — add `&&& perm.inv() ==> r.inv()` beside today's guard in `ref_rel_perm`.

对应报告：F1 The consolidated trait no longer guarantees valid permissions or references

裁决：F1明确定位Frame ref_rel_perm的反向implication，指出泛型raw_as_ref不能导出reference inv；匹配机制，不要求采用报告较宽的修复。

## pr-900-d5d5a579f00c

### L0 — M — 运行时行为与生命周期
Preemption guard is changed into an IRQ-masking RAII guard.

对应报告：无

裁决：F1是IRQ guard非LIFO析构导致提前开中断；虽提及preempt包装IRQ guard，未把禁抢占改禁中断的执行语义变化作为问题。

### L1 — M — 规范复用、放置与闲置helper
An identity tracked move is wrapped in a dedicated transfer API.

对应报告：无

裁决：未指出tracked_transfer原样返回self，是多余identity move API。

## pr-905-b62614ee989e

### L0 — M — 执行代码保留/放置
The proof migration rewrites existing CPUID leaf-description and frequency-formula comments instead of preserving the original source comments.

对应报告：无

裁决：F1是checked_mul引入None，未指出CPUID叶说明及频率公式注释被改写；建议恢复rustdoc不足以匹配具体注释根因。

## pr-906-f6e33f374ccc

### L0 — F — 执行代码保留/放置
Existing executable parser functions are moved to a new sibling module for verification isolation.

对应报告：F1 Keep the parser in its original module

裁决：F1准确指出parser迁至stack_size新模块、扩大可见性并改变call path，要求原位验证。

## pr-909-a2d5bf577533

### L0 — M — 规范复用、放置与闲置helper
The NonNull equality boundary duplicates raw-pointer equality semantics instead of reusing the existing *mut T PartialEq specification.

对应报告：无

裁决：F3仅建议NonNull::eq上游化，没有发现已存在raw-pointer PartialEq规格可复用。

## pr-915-7a42b67bb385

### L0 — P — API契约、泛型与边界
Both address-conversion contracts unnecessarily make their exact result guarantees conditional even though their bodies assume the same range conditions.

对应报告：F1 Unrestricted values reach unconditional trusted range assumptions

裁决：F1注意到结果为条件式并要求成功时精确后置，但主张改变构造域、删除assume；没有识别标签在既有信任政策下可直接导出无条件等式，只记相关子义务。

## pr-916-d7cdf470b297

### L0 — M — 规范复用、放置与闲置helper
The zero-valued data-directory constructor duplicates a spec-compatible struct literal instead of exposing the executable helper through dual_spec.

对应报告：无

裁决：未指出零data-directory构造literal重复及dual_spec复用。

### L1 — P — API契约、泛型与边界
The crate-visible PE-header API exposes closed precondition and result models without caller-visible characterization, preventing callers outside the defining module from establishing the input obligation or interpreting the returned bytes.

对应报告：F1 Make the exported precondition caller-provable

裁决：F1完整指出valid_setup_elf前提不透明，但未指出pe_coff_bytes_spec结果模型同样closed；此标签包含输入和输出两项义务。

## pr-92-8fe6908fea09

### L0 — M — 状态机、不变量与模型语义
The present-entry unmap branch assumes that the current PTE is absent from the SPT and calls `Entry::replace` under the same impossible precondition, even though `is_present` has just established that the PTE is present.

对应报告：无

裁决：唯一意见是from_raw_paddr地址界限，未指出present分支假设absent及replace相反前提形成矛盾。

## pr-920-1358fc9ae842

### L0 — M — 执行代码保留/放置
The verification patch rewrites the existing CPUID imports, calls, and adjacent executable comments to use a different wrapper instead of specifying the original core intrinsics at the centralized external boundary.

对应报告：无

裁决：报告肯定已有Origin记录与wrapper，未指出应保留core intrinsic调用及原注释、为原API加规格。

## pr-920-d5764dad33a5

### L0 — M — 命名、模式、导入与局部风格
The feature-specific ghost model is named the overly broad `CpuModel`, even though it contains only the maximum basic leaf and AVX/AVX-512F capability bits.

对应报告：无

裁决：唯一意见是CPUID规格上游化，未指出CpuModel名称过宽。

## pr-921-26e8809aa407

### L0 — M — 执行代码保留/放置
The environment-dependent verification boundary is partly presented as public rustdoc instead of being kept inside the adjacent Origin Rust block.

对应报告：无

裁决：未指出verification说明拆在公共rustdoc和Origin块两处；F2是另一组import注释问题。

## pr-923-1f20b6eda2bb

### L0 — M — 执行代码保留/放置
The newly verified executable heap APIs keep legacy Verus signature/body syntax inside `verus!` instead of attaching contracts with `#[verus_spec]` attribute-mode macros.

对应报告：无

裁决：未指出exec heap APIs应迁至verus_spec attribute模式；执行模块删除意见不是该历史迁移约定。

## pr-923-229645379886

### L0 — M — 执行代码保留/放置
The proof migration widens all three `HeapSlot` fields to `pub(super)` even though closed specification accessors can expose the required proof facts without changing executable visibility.

对应报告：无

裁决：唯一意见是core import树保存，未指出HeapSlot三字段pub(super)扩大可见性。

## pr-924-fa4046a6b4ba

### L0 — P — 执行代码保留/放置
Executable rewrites and removals in the migrated MM tests are not preserved in the required reasoned `Origin Rust:` blocks.

对应报告：F1 M1 — Preserve the value-level assertions when converting the I/O tests

裁决：F1指出多个原运行时值断言被删除并要求保留，覆盖标签一部分；未识别构造/调用改写使用无理由的Origin标记，故不记完整命中。

### L1 — M — 执行代码保留/放置
The disabled vmspace test module adds migration rationale inside the block wrapper instead of preserving the unchanged code verbatim.

对应报告：无

裁决：未指出未改变的vmspace模块应直接包裹，而非插入迁移说明。

## pr-927-cd548f6f2503

### L0 — M — API契约、泛型与边界
Fallible VM value and collection APIs omit success postconditions needed to establish their documented cursor and result-length behavior.

对应报告：无

裁决：未指出read_val/write_val/collect成功后置条件缺失；Pod问题为不同根因。

### L1 — M — API契约、泛型与边界
The trusted generic Vec::index_mut specification omits the SliceIndex bounds-admissibility condition.

对应报告：无

裁决：F3只建议Vec::index_mut规格上游化，未指出缺SliceIndex bounds-admissibility。

## pr-93-7fd1bdf5bd01

### L0 — F — 构建、工具链与证明可接受性
The ManuallyDrop specification migration removes ex_manually_drop_value_axiom but leaves an enabled FVT5 proof broadcasting that deleted item, so the proof-retaining target refers to a nonexistent symbol.

对应报告：F1 Deleting a live exported proof API leaves an unresolved in-tree use

裁决：F1准确指出被删ManuallyDrop axiom仍由FVT5 broadcast use引用，构建/证明名称解析断裂。

## pr-931-79810bc1eeb5

### L0 — M — 执行代码保留/放置
The verification change rewrites an existing to_flat_binary comment instead of preserving the original source documentation.

对应报告：无

裁决：唯一意见是slice/Vec规格上游化，未指出原zero-fill注释被改写。

## pr-96-d6659b1d4f5f

### L0 — M — 构建、工具链与证明可接受性
The shared tool locator gives environment paths precedence over fixed repository hints, allowing stale external Verus or Z3 binaries to displace the repository toolchain; the selected problem commit broadens, but does not introduce, this behavior.

对应报告：无

裁决：报告质疑root路径推断，未指出环境路径优先级应低于仓库工具；共享locator不等于同根因。

## pr-97-d67afbc9e914

### L0 — M — 运行时行为与生命周期
take_next compensates for a no-op move_forward with one-byte increments, so absent page-table regions are traversed at unaligned byte addresses instead of advancing to the next PTE.

对应报告：无

裁决：F1是level>1提前结束、F2是replace返回值契约，未指出move_forward空操作及三处逐字节补偿。

## pr-99-08de0794bf8f

### L0 — M — 所有权、资源守恒与对象身份
SubPageTable initialization creates a root frame but leaves its executable permission resource absent and relies on an invariant that inconsistently treats the same key as both a frame index and a physical address.

对应报告：无

裁决：F2关注mutation中的perms/invariant assume，未识别初始化根frame未插入permission以及frame index/paddr键混用；相关资源问题不算具体初始化根因命中。