import json,re,csv,hashlib
from pathlib import Path
from collections import Counter,defaultdict
import argparse
PACKAGE=Path(__file__).resolve().parent.parent
parser=argparse.ArgumentParser(description='Recompute saved semantic judgments; does not run a reviewer or judge.')
parser.add_argument('--inputs',type=Path,default=PACKAGE/'evidence')
parser.add_argument('--output',type=Path,default=PACKAGE/'build/results')
args=parser.parse_args()
INPUT=args.inputs.resolve();OUT=args.output.resolve()
# Never overwrite the published artifacts or frozen evidence.
protected=[PACKAGE/'data',PACKAGE/'evidence',PACKAGE/'reports',PACKAGE/'archive',PACKAGE/'provenance',PACKAGE/'scripts',PACKAGE/'methodology']
if OUT==PACKAGE or any(OUT==x or x in OUT.parents for x in protected):
 parser.error('--output must be a separate build/temp directory')
OUT.mkdir(parents=True,exist_ok=True)
S=json.loads((INPUT/'snapshot.json').read_text()); D=S['cases']
# 单一agent逐根因语义裁决，未经独立人工校准。每行依次对应labels.issues（从0开始）。
# RAW保留96份基线判断；新增判断从additional_judgments.txt读取。
# 分类: T显式信任缺口; O所有权/身份/资源关系; I状态机/不变量; C契约/泛型/边界;
# B构建/工具链/证明可接受性; R运行时/生命周期; G规范复用/放置; H命名/模式/风格; E执行代码保留; W文档。
# F完整根因命中，P部分命中，M未命中，X标签问题已在after修复；冒号后为报告finding编号（1开始）。
RAW='''100-3439712c4524 B/M C/M T/M
104-f3df1ab197d2 R/M
119-0a0ec99c5b50 C/F:1
122-aa2041448069 R/M
127-ac14d35923e4 B/M
136-9483097409b4 T/F:1
143-544fc49e7446 O/M
146-b4c63161c57b T/F:2,3
146-c6ea1a85e164 T/P:1
16-ace524111090 B/M
161-1510b718eb7d I/F:2
17-30beab687be4 B/M
171-6cc1b7bbb99b I/F:1 I/M
171-81a05f39c6ad I/M
175-1be41f76acbd I/M
178-8d5d616a2605 B/F:1
182-16d5d093ac90 T/F:1
183-fb3b9d0681b5 T/F:1 T/F:2
213-7de412d2a90e I/M
213-9d72cec58996 I/F:1
22-97523065e4c0 B/M
220-1c5f850814d9 B/M
220-cfcd9e87ed0d B/F:1
226-84f7a7f07d36 T/F:1 T/F:2 T/F:3
226-8c5c020ff2db B/M
23-56d930eb5a67 B/M
233-9d89be46b390 B/F:1
235-627f20d8afad B/M
236-72a385b929f5 B/F:1
237-24bb220c7879 T/F:1 T/F:2
25-6479bc556a28 T/F:1
250-8224e4aee238 C/F:1
26-2275e7c32b66 T/F:1
26-5474cd472251 T/P:1
296-899421ff5b69 G/M
3-df3e68c119ce T/F:2,3
33-715c00b43894 B/M
337-b6aa265c1a4a R/F:1
35-fa067beadf03 T/M T/F:1,2 T/M T/M T/M
350-5cbda0832ce0 C/M
353-650ed55495ef B/M
355-2a3429fb0b20 B/F:2
382-045fa97a6577 R/F:1 C/F:1 C/F:3
382-6a84ab163da0 O/F:1 W/M
39-8777297fc95c B/M
390-ff234245b17b C/M
392-f30278a5973e O/M
395-6ae195e508a8 R/M
403-a1f2685897f4 O/X
419-e2a32e9a225f O/M
424-2e7051b98235 G/M
424-8d7b6621ed81 R/M
439-b083bbf05f58 O/M B/M
44-a75fa49663cc T/F:2
440-0ba029a82c8d G/M
45-a64f70e4ca48 B/F:1
452-d834e11605c3 G/M
454-1db47ee9a94b C/M
456-6aa8a9b0ede4 R/F:1 R/F:1
473-27c3210449d8 H/M
474-a6fdca3a754f O/M
485-6fac7bc837f6 R/M
487-5170c403b0d7 R/M
492-e7a37a7d7080 H/M B/M
499-2d320cbb55fc I/X
50-5d510a5352a3 B/M
500-5c863f079762 H/M
500-6c26d6c45e16 G/F:1
500-e909aa15bb90 E/M
501-5646c42516b4 R/F:1
505-cb2be5a80af1 R/F:2
505-dffa7b932d72 G/M
511-860ffa221455 G/M
515-378590cc39ac R/F:1
518-4cb9ee7caa9e I/F:1
526-614ad9c3f014 B/M H/M
530-3574febda9d0 C/P:1
532-9200dd2fb210 C/M
534-5ba756b22a68 H/M
546-269c2b583824 C/M
547-4510bdeecf13 O/M
562-581ce53261be H/F:1
577-94715eb8c48e W/M
595-c34b8882f0e1 B/M
612-0886ccdd5411 C/M
614-0f6d3afea7b8 H/M H/M E/M
615-b995aae1ffdb H/F:1
616-bd8357d3afaa E/F:1
617-a00a7b6fa954 O/F:1
626-cef66d9ffb91 H/M
628-096c166e5ce6 H/M
63-742ee43ba12c R/M
632-1be8099780ff O/M
634-64d2718d5a4d H/M
636-b0d5450c6e0c G/M H/M
64-900e41671221 I/M'''
MAP={('pr-'+line.split()[0]):line.split()[1:] for line in RAW.splitlines()}
NOTES={
('pr-136-9483097409b4',0):'同一path对应关系根因：报告定位3个新admit，并明确提及第4个既有admit；不按4个位置拆分标签。',
('pr-146-c6ea1a85e164',0):'H1提及i_pte.wf/root/level/frame level未经证明，但主论点是另一处矛盾；未完整分析Entry::wf缺关系及返回child guard保证。',
('pr-26-5474cd472251',0):'H1命中同根因的positive辅助lemma，但未报告read_unlock其余3个admit；Low只是清理注释，不能算完整转移证明检测。',
('pr-530-3574febda9d0',0):'同类硬编码泛型约束，仅报告已有NR_LEVELS等式；未报告本次新增BASE_PAGE_SIZE及entry ratio。before:146已有该level等式，新增性判断错误。',
('pr-403-a1f2685897f4',0):'标签是before的take/put权限复制，after已改为借用；报告针对新borrow helper闲置，不能匹配旧缺陷，也不能简单归咎漏检。',
('pr-499-2d320cbb55fc',0):'标签全部定位before，PR删除替代模型并恢复production实现；after缺陷检测与历史问题识别任务不一致。',
('pr-35-fa067beadf03',1):'报告H1及M1分别定位inductive与支持lemma，合起来命中一个transition级标签。',
('pr-35-fa067beadf03',0):'报告明确将common.rs既有admit排除在diff之外；基准要求识别快照存量缺陷。',
('pr-35-fa067beadf03',2):'报告明确将write_unlock既有admit排除在diff之外。',
('pr-35-fa067beadf03',3):'报告明确将allocate既有admit排除在diff之外。',
('pr-35-fa067beadf03',4):'报告明确将deallocate既有admit排除在diff之外。',
('pr-39-8777297fc95c',0):'diff仅修改workspace/xtask；标签是证明postcondition内deref的mode错误，与变更路径不重合。',
('pr-452-d834e11605c3',0):'报告要求upstream generic specs，标签要求复用现有is_pow2_exists；同一API不代表同一根因。',
('pr-500-e909aa15bb90',0):'报告是frame_to_index/index_to_frame变spec-only；标签是frame_to_meta/meta_to_frame的exec放置错误，不同API及修复。',
('pr-382-045fa97a6577',0):'H1明确描述None后unwrap并建议恢复retry，虽与callee不实契约合并，实际覆盖caller根因。',
('pr-617-a00a7b6fa954',0):'直接命中getter任意ghost witness未绑定receiver的身份关系。',
}
NAMES={'T':'显式admit/external_body证明缺口','O':'所有权、资源守恒与对象身份','I':'状态机、不变量与模型语义','C':'API契约、泛型与边界','B':'构建、工具链与证明可接受性','R':'运行时行为与生命周期','G':'规范复用、放置与闲置helper','H':'命名、模式、导入与局部风格','E':'执行代码保留/放置','W':'验证文档'}
BASELINE_SAMPLES=set(MAP)
for line in (INPUT/'additional_judgments.txt').read_text().splitlines():
 if not line or line.startswith('#'): continue
 sid,code,reason=(x.strip() for x in line.split('|',2));sid='pr-'+sid
 assert sid not in BASELINE_SAMPLES,sid
 codes=MAP.setdefault(sid,[])
 NOTES[(sid,len(codes))]=reason
 codes.append(code)
assert set(MAP)=={d['sample'] for d in D},'judgment/sample coverage mismatch'
def findings(txt):
 result=[]; severity=None; current=None
 for line in txt.splitlines():
  if line.startswith('## '):
   severity=line[3:].strip() if line[3:].strip() in ['High','Medium','Low'] else None; current=None
  if severity and line.startswith('### '):
   result.append(dict(severity=severity,title=line[4:],text=line));current=result[-1]
  elif severity and line.startswith('|') and not re.match(r'^\|\s*(Finding\s*\||[- :]+\|)',line):
   if re.match(r'^\|\s*(None|No findings|—)\s*\|',line,re.I): continue
   result.append(dict(severity=severity,title=line.split('|')[1].strip(),text=line));current=None
  elif current:current['text']+='\n'+line
 return result
rows=[]; preds=[]; cases=[]
for d in D:
 sid=d['sample']; F=findings(d['review']); codes=MAP[sid]
 assert len(codes)==len(d['labels']['issues']),(sid,codes)
 for j,f in enumerate(F,1):preds.append(dict(sample=sid,finding=j,**f))
 for idx,(i,code) in enumerate(zip(d['labels']['issues'],codes)):
  group,match=code.split('/'); status,*nums=match.split(':'); ns=[int(x) for x in nums[0].split(',')] if nums else []
  assert all(1<=x<=len(F) for x in ns),(sid,ns,len(F))
  assert status in {'F','P','M','X'} and bool(ns)==(status in {'F','P'}),(sid,code)
  rows.append(dict(sample=sid,label_index=idx,label_id=i['id'],category=i['category'],group=group,group_name=NAMES[group],status=status,finding_ids=ns,finding_titles=[F[n-1]['title'] for n in ns],description=i['description'],rule_ids=i['rule_ids'],locations=i['locations'],reason=NOTES.get((sid,idx), '报告明确指出相同API/证明义务、相同失败机制，修复方向与标签一致。' if status=='F' else '报告未指出此标签的具体根因；其他位置的信任缺口、同文件/同规则问题不计为命中。'),judgment_source='single_agent_semantic_assessment',evaluator_version='20261121-full-v2',batch='baseline_96' if sid in BASELINE_SAMPLES else 'remaining_83'))
 cases.append(dict(sample=sid,pr_number=d['metadata']['pr_number'],labels=len(codes),findings=len(F),full=sum(x.split('/')[1].startswith('F') for x in codes),partial=sum(x.split('/')[1].startswith('P') for x in codes),excluded=sum(x.endswith('/X') for x in codes)))
for p in preds:
 p['full_label_ids']=[r['label_id'] for r in rows if r['sample']==p['sample'] and p['finding'] in r['finding_ids'] and r['status']=='F']
 p['partial_label_ids']=[r['label_id'] for r in rows if r['sample']==p['sample'] and p['finding'] in r['finding_ids'] and r['status']=='P']
 p['benchmark_status']='full_match' if p['full_label_ids'] else 'partial_match' if p['partial_label_ids'] else 'unmatched_not_adjudicated_false'
def stats(rr):
 c=Counter(r['status'] for r in rr); n=len(rr)
 return dict(n=n,full=c['F'],partial=c['P'],miss=c['M'],fixed_in_after=c['X'],strict_recall=c['F']/n if n else None,lenient_recall=(c['F']+c['P'])/n if n else None)
summary=dict(captured_at=S['captured_at'],sample_count=len(D),distinct_pr_count=len(set(c['pr_number'] for c in cases)),total_samples=len(S['all_samples']),completed_rate=len(D)/len(S['all_samples']),issue_stats=stats(rows),by_category={k:stats([r for r in rows if r['category']==k]) for k in ['semantic','guideline']},by_group={NAMES[k]:stats([r for r in rows if r['group']==k]) for k in NAMES},after_only_sensitivity=stats([r for r in rows if r['status']!='X']),findings=len(preds),finding_status=dict(Counter(p['benchmark_status'] for p in preds)),severity=dict(Counter(p['severity'] for p in preds)),cases_any_full=sum(c['full']>0 for c in cases),cases_all_full=sum(c['full']==c['labels'] for c in cases),cases_no_full=sum(c['full']==0 for c in cases),cases_no_findings=sum(c['findings']==0 for c in cases),diff_equal=all(d['diff_equal'] for d in D))
def ratio(n,d):return n/d if d else None
pr_recalls=defaultdict(list)
for c in cases:
 if c['labels']:pr_recalls[c['pr_number']].append(c['full']/c['labels'])
summary.update(evaluator_version='20261121-full-v2',judgment_source='single_agent_semantic_assessment',
 sample_macro_recall=ratio(sum(c['full']/c['labels'] for c in cases if c['labels']),sum(c['labels']>0 for c in cases)),
 pr_balanced_macro_recall=ratio(sum(sum(v)/len(v) for v in pr_recalls.values()),len(pr_recalls)),
 pr_macro_definition='先对每PR的有标签快照recall取均值，再对PR等权平均；未做跨快照根因去重',
 zero_label_samples=sum(c['labels']==0 for c in cases),
 by_batch={b:dict(samples=sum((c['sample'] in BASELINE_SAMPLES)==(b=='baseline_96') for c in cases),issues=stats([r for r in rows if r['batch']==b]),by_category={k:stats([r for r in rows if r['batch']==b and r['category']==k]) for k in ['semantic','guideline']},findings=sum((p['sample'] in BASELINE_SAMPLES)==(b=='baseline_96') for p in preds)) for b in ['baseline_96','remaining_83']},
 by_rule={k:stats([r for r in rows if k in r['rule_ids']]) for k in sorted({k for r in rows for k in r['rule_ids']})},
 unmatched_raw_finding_rate=ratio(sum(p['benchmark_status']=='unmatched_not_adjudicated_false' for p in preds),len(preds)),
 full_aligned_raw_finding_rate=ratio(sum(p['benchmark_status']=='full_match' for p in preds),len(preds)),
 known_prior_exposure_prs=[628,632,770,856,886,931],
 not_measured={'finding_precision':None,'confirmed_false_positives_per_pr':None,'unresolved_atomic_rate':None,'atomic_duplicate_rate':None,'recall_at_k':None,'executable_oracle_recall':None,'tokens':None,'tool_calls':None,'latency':None},
 limitations=['标签匹配是单agent判断，未人工校准','finding为原始报告项，未完整原子化或独立真伪裁决','未匹配不等于误报','全快照汇总，未跨快照根因去重或依赖组隔离','fast静态配置，缺runner原始prompt/trace与成本','未运行历史Verus/编译/测试','before/after不是bug/fix配对','目录名pr-test不代表封存测试划分'])
summary['declared_prior_exposure_sensitivity']=stats([r for r in rows if int(r['sample'].split('-')[1]) not in summary['known_prior_exposure_prs']])
reported_rules=set(summary['by_rule']) | {'upstream-reusable-specs','complete-external-contracts','restrict-generic-trusted-models','document-real-proof-debt'}
for p in preds:
 p['reported_rule_ids']=[k for k in sorted(reported_rules) if k in p['text']]
summary['finding_rule_mentions']={k:dict(raw_findings=sum(k in p['reported_rule_ids'] for p in preds),unmatched=sum(k in p['reported_rule_ids'] and p['benchmark_status']=='unmatched_not_adjudicated_false' for p in preds)) for k in sorted(reported_rules) if any(k in p['reported_rule_ids'] for p in preds)}
summary['finding_rule_mentions_definition']='按报告原文出现的规则ID计数，非互斥，未出现ID的同类意见不推断归类；不是规则执行率或问题真伪裁决'
for c in cases:
 c['batch']='baseline_96' if c['sample'] in BASELINE_SAMPLES else 'remaining_83'
 c['strict_recall']=ratio(c['full'],c['labels'])
assert len({r['label_id'] for r in rows})==len(rows)
for name,obj in [('label_matches',rows),('findings',preds),('cases',cases),('metrics',summary)]:
 (OUT/(name+'.json')).write_text(json.dumps(obj,ensure_ascii=False,indent=2))
 if isinstance(obj,list):
  with (OUT/(name+'.csv')).open('w',newline='',encoding='utf-8-sig') as f:
   w=csv.DictWriter(f,fieldnames=list(obj[0]));w.writeheader();w.writerows([{k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in x.items()} for x in obj])
md=['# 逐标签根因匹配表','\nF=完整命中；P=部分命中；M=未匹配；X=before问题已被after修复。编号采用标签0开始、报告finding 1开始。完整原文及哈希见snapshot.json。单agent语义判断，未人工校准；一项报告含明确不同子声明时可对应多个标签，不代表发现已完整原子化或真伪确认。']
for d in D:
 sid=d['sample'];md+=['\n## '+sid]
 for r in [r for r in rows if r['sample']==sid]:
  md+=['\n### L'+str(r['label_index'])+' — '+r['status']+' — '+r['group_name'],r['description'],'\n对应报告：'+('；'.join(f"F{n} {t}" for n,t in zip(r['finding_ids'],r['finding_titles'])) or '无'),'\n裁决：'+r['reason']]
(OUT/'逐条匹配.md').write_text('\n'.join(md))
with (OUT/'rule_metrics.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.DictWriter(f,fieldnames=['rule_id']+list(stats([])))
 w.writeheader();w.writerows(dict(rule_id=k,**v) for k,v in summary['by_rule'].items())
print(json.dumps(summary,ensure_ascii=False,indent=2))
