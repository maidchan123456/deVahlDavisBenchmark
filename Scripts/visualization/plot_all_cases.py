#!/usr/bin/env python3
"""Generate a new, read-only visualization publication from existing CFD results.

Run with python3 -B. Existing output directories are never overwritten.
"""
from __future__ import annotations
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import sys
import traceback
from zoneinfo import ZoneInfo

sys.dont_write_bytecode=True
os.environ.setdefault('MPLCONFIGDIR','/tmp/deVahlDavis-visualization-matplotlib')
from common import (ROOT,DEFAULT_OUTPUT,A_REVIEW,RAS,QOIS,INPUTS,CHECKS,np,plt,
                    read_csv,read_json,write_csv,sha,check,load_all,protected_snapshot,git_evidence)
from plot_case import plot_case
from plot_comparisons import (montage,plot_grid_and_paper,gate_f,ab_comparison,gate_h,
                              diagnostics,auxiliary,table_figure)


def validate_comparisons(cases,paper):
    byid={c.case_id:c for c in cases}
    for r in read_csv(A_REVIEW/'RouteA_AB_Ra_trend.csv'):
        a,b=byid[r['A_case_id']],byid[r['B_case_id']];q=r['quantity']
        if q in a.metrics and q in b.metrics and isinstance(a.metrics[q],(float,int)):
            check(a.case_id,'AB CSV A:'+q,a.metrics[q],float(r['A']))
            check(b.case_id,'AB CSV B:'+q,b.metrics[q],float(r['B']))
        if r['relative_difference']:
            check(a.case_id,'AB CSV relative:'+q,float(r['relative_difference']),abs(float(r['A'])-float(r['B']))/abs(float(r['B'])))
    hbase=byid['A-Ra1e6-fine'];hp=byid['A-H-Ra1e6-fine-beta1e-4']
    for r in read_csv(ROOT/'results/routeA/attempts/attempt_008/GateH_comparison.csv'):
        q=r['quantity']
        if q in hbase.metrics and isinstance(hbase.metrics[q],(int,float)):
            check(hbase.case_id,'H CSV baseline:'+q,hbase.metrics[q],float(r['baseline']))
            check(hp.case_id,'H CSV perturbed:'+q,hp.metrics[q],float(r['perturbed']))
        if q in QOIS:
            check(hp.case_id,'H CSV relative:'+q,abs(hbase.metrics[q]-hp.metrics[q])/abs(hbase.metrics[q]),float(r['relative_difference']))
    hd=read_json(ROOT/'results/routeA/attempts/attempt_008/GateH_diagnostics.json')
    for c,key in [(hbase,'baseline'),(hp,'perturbed')]:
        for k,sk in [('rho_min','rho_min'),('rho_max','rho_max'),('max_relative_density_deviation','max_abs_rho_over_rho0_minus_1'),
                     ('temperature_symmetry','temperature_symmetry'),('velocity_symmetry','velocity_symmetry')]:
            check(c.case_id,'H diagnostic:'+k,c.summary[sk],hd[key][k])
    # Compare reference differences wherever prior metrics store the same definition.
    for c in cases:
        if c.ra not in paper: continue
        comparison=c.metrics.get('paper_comparison_like_for_like') or {}
        for q in QOIS:
            if q in comparison:
                ref=float(paper[c.ra][q]);record=comparison[q]
                check(c.case_id,'paper reference:'+q,ref,record['reference'])
                if 'absolute_relative_error' in record:
                    check(c.case_id,'paper error:'+q,abs(c.metrics[q]-ref)/abs(ref),record['absolute_relative_error'])


def readme(out,cases,inventory,protection,gategroups,ab,hprimary,gf):
    matrix=[c for c in cases if c.category=='matrix']
    lines=['# 既存 CFD 結果の統一可視化（Route A / Route B）','',
        '本成果物は保存済み結果のみを読み込んだ可視化・比較です。solver、mesh 生成、OpenFOAM postProcess は実行していません。既存の判定・契約・場・metrics を更新していません。',
        '', '## 正式判定と対象','',
        '- Route A：computed **12/12**、accepted **12/12**、Gate D PASS **12/12**。各 Ra の fine practical paper comparison と Gate G は既存 PASS。Gate F は全4 Raで FAIL、needs_320=YES を保持。',
        '- Route B：computed **12/12**、accepted **9/12**。Ra=10³～10⁵は全格子 accepted。Ra=10⁶は全格子 Gate D FAIL / accepted NO の **diagnostic-only**。',
        '- B-Ra1e4-coarse は独立したケースを作らず、正式 matrix が再利用を認めた **B-SMOKE** の field/result を使用。`case_id` と `source_case_id` を各表で分離。補助 B-SMOKE は同じ solver result の別表示であり、独立した追加計算ではありません。',
        '- A-Ra1e3-coarse の metrics は attempt_004 の `accepted_reuse/metrics.json` と付属 CSV を使用。',
        '- 正式24表示条件、補助 A/B-COND・A/B-SMOKE の4表示ケース、Gate H 1ケースの計29表示ケース（独立した solver result は28）。補助図・感度図は `comparison/auxiliary/`・`comparison/sensitivity/` に分離。',
        '', '## 入力ケース・結果の一覧','',
        '|表示 case ID|source case ID|分類|Ra|grid|accepted|最終反復|入力ケース|metrics|',
        '|---|---|---|---:|---|---|---:|---|---|']
    for c in cases:
        lines.append(f'|{c.case_id}|{c.source_case_id}|{c.category}|{c.ra}|{c.n}x{c.n}x1|{c.status.get("accepted","正式 matrix 外")}|{c.metrics["final_iteration"]}|{c.case_path}|{c.metrics_path}|')
    lines += ['', '## 無次元化・座標・描画','',
        r'`X=x/L`, `Z=z/L`, `theta=(T-Tc)/(Th-Tc)`, `(U,W)=(L/alpha0)*(ux,uz)`。`alpha0` は各 manifest の既存 benchmark 値を使用。実 mesh は OpenFOAM `(x,y,z)` の第2成分が鉛直なので、論文 `Z` と `W` は OpenFOAM `y` と `U[:, :, 1]` に対応します。第3成分は厚み方向で、流線には用いません。保存 C または保存 mesh の points/faces/owner/neighbour から cell 配置と並び順を検証しています。',
        '', '中心線速度は既存 B extractor を A にも適用し、A の同一の式と照合。2本の隣接 cell-centre line の平均で正確な X=0.5 / Z=0.5 を取り、壁 no-slip のゼロ endpoint を加えて線形補間した **4097点**です。正の Umax/Wmax と位置を保存 metrics と照合。局所 Nu 極値は既存の5点 quartic 法をそのまま呼び出します。Route A の quartic に渡す座標は既存 analyzer と同じ有次元座標/L の計算順序を保持します。Table V の星印は参照極値と位置で、参照の全プロファイルは捏造していません。',
        '', '温度は contourf、共通 0≤theta≤1、aspect=1。セル値をクリップしません。overshoot は `data/all_case_summary.csv` と `data/temperature_overshoot.csv` の範囲・セル数に保存し、色範囲外は extend に表示します。温度・速度絶対値・密度図は表示のためだけに既知の壁温度/no-slip・断熱境界を付加します。元の CSV field は cell centre の値を保持。流線は均一 cell-centre grid 上の streamplot を使用し、壁から半セル以内は描画補外しません。',
        '', '流線の色は in-plane の U/W で運ばれる3成分速度絶対値 |U*|（厚み成分の最大値も CSV に記録）。各 Ra 内では両 Route・3格子の最大速度を共通上限に使用。異なる Ra は別の上限で、montage では各行の colorbar を確認してください。温度は coolwarm、速度は magma、密度偏差は RdBu_r。',
        '', '線図は Route A=青、Route B=朱、paper=黒の点線・星、Gate H perturbed=緑。accepted は実線/塗りつぶし marker、B Ra=10⁶ は破線/中抜き marker。field は各パネルタイトルに accepted / diagnostic-only を記載。補助ケースは outside formal matrix と記載。',
        '', '## Nu の定義と比較範囲','',
        r'原論文熱輸送密度は `Q=U*theta-dtheta/dX`。`Nu_bar_0` は高温壁、`Nu_bar_half` は中央 X=0.5 断面、`Nu_bar_1` は低温壁、`Nu_bar_cavity = 1 + volume_mean(U*theta)` は領域積分です。断面曲線の台形積分は独立診断であり、primary cavity 値を置き換えません。`local Nu(Z)` は壁 face の局所値であり、平均 Nu と区別します。',
        '', '- Route A：壁は直交 patch gradient A1、内部断面は linear cell-U/theta face interpolation + 2-cell 温度勾配。物理熱収支は保存 wallHeatFlux Q による A2 を使用。',
        '- Route B：正式壁値 B1 は fixedValue patch snGrad、内部断面の移流は **保存済み volume flux phi** × linear theta。B2 は壁温度と第1/第2セル温度から独立二次再構成した診断値で、点線で表示。B2 で正式 B1 を置き換えません。',
        '- A/B の Nu_bar_half・section consistency は演算子が異なり、**NOT_LIKE_FOR_LIKE**。これらは同じ比較誤差曲線へ入れません。既存 AB CSV の comparison_class・diagnostic_only 等は保持し、Nu_bar_cavity、Nu_bar_0、Umax、Wmax、局所 Nu max/min の6量だけを AB 相対差図に使用。',
        '- 原論文対 A は practical benchmark difference、A対Bは model/formulation difference。Aの差を純粋な数値誤差と解釈しません。paper 相対差は 100|computed-reference|/|reference|、AB は 100|A-B|/|B|。',
        '', '## 密度・保存則・Gate H の注意','',
        r'Route A は温度依存 Boussinesq EOS `rho=rho0[1-beta(T-T0)]`, `psi=0`。密度偏差図は圧力依存 compressibility を示しません。`rho_min`, `rho_max`, `max|rho/rho0-1|` は cell-centre 値として表に記録し、壁での振幅 beta DeltaT/2 を別表示。',
        '', 'Route B rhok は `1-beta(T-TRef)` を保存 T から再構成した **buoyancy / hydrostatic factor**。v6 createFields.H / TEqn.H / pEqn.H と docs/routeB_design.md を確認しました。浮力と静水圧分離 `p=p_rgh+rhok*gh` に使用され、慣性・温度輸送・連続式に温度依存の質量密度として入る場ではありません。A rho と B rhok の単純差分は作成していません。',
        '', 'A native phi は mass flux [kg/s]、B native phi は volume flux [m³/s]。normalized native continuity indicator は Route 別の図・operator metadata に分離。速度再構成 divergence は native face flux divergence と別量です。既存 epsilon 値を転記して判定は変えません。温度・速度対称性は保存場の180度回転対応セルから算出し、保存済み定義・値がある場合に照合しています。ゼロ値は対数図で 0 と明記し、未保存値は not stored と表示します。',
        '', 'Gate H は共通160²で beta/10, g×10、Ra/Pr を固定した感度比較。**grid independence、Route A=Route B、格子とモデルの影響の完全分離の証明ではありません。** 密度偏差の左右比較は共通±0.0005で、個別 H 図では小さい密度振幅も確認できます。',
        '', '|Gate H primary QoI|相対差 [%]|', '|---|---:|']
    for r in hprimary: lines.append(f'|{r["quantity"]}|{100*float(r["relative_difference"]):.8f}|')
    lines += ['', '## 図から確認できる観察・解釈・未解決事項','',
        '**観察：** Ra増加に伴って Nu・速度極値が増加し、高Raでは壁近くの温度変化と鉛直流れが集中します。正式3格子の Nu_bar_cavity は両 Route の全Raで格子細分化とともに低下。速度極値の一部は非単調で、Gate F の未定義 p/GCI を「未定義」と保持。A Ra=10⁶ の Nu fine-medium 差は約1.3402%。',
        '', '|Ra|A fine Nu|B fine Nu|A fine Umax|B fine Umax|A fine Wmax|B fine Wmax|B区分|', '|---:|---:|---:|---:|---:|---:|---:|---|']
    for ra in RAS:
        a=next(c for c in matrix if c.route=='A' and c.ra==ra and c.n==160)
        b=next(c for c in matrix if c.route=='B' and c.ra==ra and c.n==160)
        lines.append(f'|{ra}|{a.metrics["Nu_bar_cavity"]:.9f}|{b.metrics["Nu_bar_cavity"]:.9f}|{a.metrics["Umax"]:.7f}|{b.metrics["Umax"]:.7f}|{a.metrics["Wmax"]:.7f}|{b.metrics["Wmax"]:.7f}|{b.label}|')
    maxab=max(100*float(r['relative_difference']) for r in ab if r['quantity'] in QOIS)
    lines += ['', f'**観察：** fine の3主要量 Nu_cavity/Umax/Wmax では既存 AB CSV の相対差の最大値は {maxab:.6f}%（B Ra=10⁶を含む診断比較）。Gate H の3量は既存値約0.0392/0.0239/0.0111%と一致し、密度振幅は約1/10。温度 overshoot の有無は次の表で判定可能です。',
        '', f'全29表示ケースのセル温度範囲は theta={min(c.summary["theta_min"] for c in cases):.9g}～{max(c.summary["theta_max"] for c in cases):.9g}。範囲外セル総数は {sum(c.summary["theta_below_0_count"]+c.summary["theta_above_1_count"] for c in cases)}。',
        '', '**推論：** 小さい fine 主要量差と密度振幅の低下は、今回の共通格子・固定条件での感度が小さいことを支持します。原論文・Route B との物理方程式差、格子誤差、離散 operator 差の寄与はこの図だけで分離できません。',
        '', '**未解決：** A Gate F 全4Ra FAIL/needs_320 YES、B Ra=10⁶ Gate D FAIL、B Gate F 非単調/未評価、B Gate G の正式 FAIL/未評価・閾値未解決は既存結論を維持。図生成・fineの参照一致だけで Verification 完了や grid independent と結論しません。',
        '', '## 数値照合と read-only 保護','',
        f'全 {len(CHECKS)} 照合項目 PASS。保存場→既存 analyzer の純粋関数による再計算→metrics/中心線/局所Nu/断面Nu CSV→正式 matrix/AB/Gate H の順に整合を確認。既存値は上書きしません。rtol=atol=5e-12（geometry coordinate のみ atol=5e-10 m）。検出した不一致は例外 STOP で終了し、その原因を logs/STOP.json に記録する実装です。',
        '', '開発時、A-Ra1e6-medium の quartic 最小値に7.2759576e-11の差が出て停止しました。原因は等価な座標式の浮動小数点計算順序。Route A analyzer と同じ座標式に修正後、許容差を緩和せず一致。既存 metrics は変更していません。',
        '', f'実行前後で protected roots と外部 v6 Route B cases の全 {protection["protected_file_count"]} ファイルの size/mtime_ns/ctime_ns を比較し、変更・追加・削除はゼロ。実入力 {protection["hashed_input_count"]} ファイルの SHA-256 も不変。git diff/status は開始時と一致。入力全量をhashしたわけではなく、全領域 metadata inventory と実入力 content hashes の組合せです。',
        '', '`logs/protection.json` に範囲・件数・git比較結果、`logs/input_sha256.csv` に実入力 hash、`logs/numerical_checks.csv` に照合差、`logs/run_summary.json` に件数を保存。solver 実行は0回、mesh生成0回、既存 analyzer main() 呼出し0回。',
        '', '## 図一覧（PNG 300 dpi + PDF）','',
        '各行の PNG と PDF は同じ図です。PDF の field/線はベクトル出力で、論文掲載時の拡大に適します。',
        '', '|図|説明|ケース|', '|---|---|---|']
    for r in inventory:
        lines.append(f'|[PNG]({r["png"]}) / [PDF]({r["pdf"]})|{r["description"]}|{r["case_ids"]}|')
    lines += ['', '## CSV一覧','',
        '- `data/all_case_summary.csv`：ケース対応・正式状態・主要量・温度範囲・密度振幅。',
        '- `data/paper_comparison_fine.csv`：fine の3量と Table V 絶対相対差[%]。',
        '- `data/routeA_vs_routeB_fine.csv`：既存 AB 比較CSVを分類・原精度付きで保存（NOT_LIKE_FOR_LIKE含む；図の対象からは除外）。',
        '- `data/grid_convergence.csv`：全正式ケースの格子依存・参照差。',
        '- `data/gate_F_detail.csv`：既存 fine-medium差[%]・p_obs・GCI[%]・判定。未定義/未評価を文字列のまま保存。',
        '- `data/convergence_conservation.csv`：residual、Rwin、熱収支、section偏差、native/再構成divergence、対称性。',
        '- `data/routeA_density_summary.csv` / `data/GateH_density_diagnostics.csv`：EOS密度範囲・感度。',
        '- `data/GateH_comparison.csv`：既存 Gate H 比較と分類。',
        '- `data/temperature_overshoot.csv`：温度範囲と範囲外セル数。',
        '- `data/centreline_<case>.csv`：4097点 U/W。',
        '- `data/local_Nu_<case>.csv`：壁局所Nu；B2診断値を別列。',
        '- `data/section_Nu_<case>.csv`：断面 Nu と cavity 水平線値・operator。',
        '- `data/temperature_centreline_<case>.csv`：4097点温度線（追加の表示用定義；原論文硬判定には使用しない）。',
        '- `data/field_<case>.csv`：実セルの X/Z/theta/U*/W*/速度絶対値・密度偏差または rhok。',
        '- `tables/figure_inventory.csv`, `tables/csv_inventory.csv`, `tables/case_status.csv`, `tables/gate_summary.csv`：全ファイル対応表・既存判定一覧。',
        '', '完全な CSV ファイル一覧：','']
    for p in sorted(out.rglob('*.csv')): lines.append(f'- [{p.relative_to(out)}]({p.relative_to(out)})')
    lines += ['', '## 再生成','',
        'Python 3 / numpy / matplotlib を使用。既存 field readers/analyzer をread-only importし、main()は呼びません。既存出力を上書きしないため、未使用の出力ディレクトリを指定してください。書込み先は `results/visualization_all_cases/` 内に制限しています。',
        '', '```bash',f'cd {ROOT}',
        'OPENBLAS_NUM_THREADS=1 python3 -B Scripts/visualization/plot_all_cases.py --output results/visualization_all_cases/regenerated_001',
        '```', '',
        '`--case CASE_ID` で対象ケースの個別図だけを生成できます。その場合も正式状態・全ケース入力・比較sourceの検証と read-only 保護を実施し、`--output` に未使用パスを指定します。全図の一覧は本 full run の inventory を参照してください。']
    (out/'README.md').write_text('\n'.join(lines)+'\n')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=DEFAULT_OUTPUT)
    p.add_argument('--case',help='Optional single-case individual plots; still validate every authoritative source')
    args=p.parse_args();out=args.output.resolve()
    if out!=DEFAULT_OUTPUT and DEFAULT_OUTPUT not in out.parents: p.error('Output must lie within results/visualization_all_cases/')
    if out.exists() and any(out.iterdir()): p.error('Refusing to overwrite existing output; choose a new --output path')
    out.mkdir(parents=True,exist_ok=True)
    for sub in ('individual','comparison','montage','tables','data','logs'): (out/sub).mkdir(exist_ok=True)
    print('Snapshot of protected artifacts...',flush=True)
    before=protected_snapshot();git_before=git_evidence()
    import hashlib
    before_digest=hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest()
    (out/'logs/protected_before_inventory.json').write_text(json.dumps(dict(file_count=len(before),metadata_inventory_sha256=before_digest,git_head=git_before[2].strip()),indent=2)+'\n')
    (out/'logs/git_before.diff').write_text(git_before[0]);(out/'logs/git_before.status').write_text(git_before[1])
    try:
        cases,groups=load_all()
        paper={int(r['Ra']):r for r in read_csv(ROOT/'reference/de_vahl_davis_table_v.csv')}
        validate_comparisons(cases,paper)
        # Includes all figure inputs and attribution documents before plotting.
        import common
        for f in [ROOT/'docs/benchmark_spec.md',ROOT/'docs/routeB_design.md',
                  Path('/home/mirai/OpenFOAM/OpenFOAM-6/applications/solvers/heatTransfer/buoyantBoussinesqSimpleFoam')/'createFields.H',
                  Path('/home/mirai/OpenFOAM/OpenFOAM-6/applications/solvers/heatTransfer/buoyantBoussinesqSimpleFoam')/'TEqn.H',
                  Path('/home/mirai/OpenFOAM/OpenFOAM-6/applications/solvers/heatTransfer/buoyantBoussinesqSimpleFoam')/'pEqn.H']:
            common.track(f).read_text()
        input_hashes={str(path):sha(path) for path in INPUTS}
        write_csv(out/'logs/input_sha256.csv',[dict(path=k,sha256=v) for k,v in sorted(input_hashes.items())])
        print(f'Pre-plot verification: {len(cases)} display cases; {len(CHECKS)} checks PASS',flush=True)
        write_csv(out/'data/all_case_summary.csv',[c.summary for c in cases])
        write_csv(out/'data/temperature_overshoot.csv',[{k:c.summary[k] for k in ('case_id','theta_min','theta_max','theta_below_0_count','theta_above_1_count')} for c in cases])
        scales={ra:max(float(c.speed.max()) for c in cases if c.category=='matrix' and c.ra==ra) for ra in RAS}
        inventory=[]
        selected=[c for c in cases if not args.case or c.case_id==args.case]
        if not selected: raise ValueError('Unknown --case '+str(args.case))
        for i,c in enumerate(selected):
            print(f'Individual {i+1}/{len(selected)}: {c.case_id}',flush=True)
            plot_case(c,out,inventory,paper.get(c.ra),scales.get(c.ra,float(c.speed.max()) or 1))
        if not args.case:
            print('Montages and fine A/B fields...',flush=True);montage(cases,out,inventory,scales)
            print('Grid and paper comparisons...',flush=True);plot_grid_and_paper(cases,paper,out,inventory)
            gf=gate_f(out,inventory)
            print('A/B source comparisons...',flush=True);ab=ab_comparison(cases,out,inventory)
            print('Gate H and conservation diagnostics...',flush=True);hp=gate_h(cases,out,inventory,paper)
            diagnostics(cases,out,inventory);auxiliary(cases,out,inventory,paper)
        else: gf=[];ab=[];hp=[]
        a,b,_=common.audit_status()
        status=[]
        for c in cases:
            if c.category=='matrix': status.append({**c.status,'case_id':c.case_id,'source_case_id':c.source_case_id,'route':c.route,'Ra':c.ra,'N':c.n})
        write_csv(out/'tables/case_status.csv',status)
        write_csv(out/'tables/gate_summary.csv',[dict(route='A',**r) for r in groups]+[dict(route='B',case_id=r['case_id'],Ra=r['Ra'],Gate_D=r['Gate_D'],Gate_E=r['Gate_E_status'],Gate_F=r['Gate_F_status_Ra_scope'],Gate_G=r['Gate_G_formal_status'],needs_320=r['needs_320_Ra_scope']) for r in b])
        table_figure([dict(case_id=c.case_id,route=c.route,Ra=c.ra,N=c.n,computed=c.status['computed'],accepted=c.status['accepted'],Gate_D=c.status['Gate_D']) for c in cases if c.category=='matrix'],
            ['case_id','Ra','N','computed','accepted','Gate_D'],['Matrix case','Ra','N','computed','accepted','Gate D'],out,Path('tables/formal_matrix_status'),inventory,'Existing matrix statuses (no reclassification)')
        write_csv(out/'tables/figure_inventory.csv',inventory)
        write_csv(out/'logs/numerical_checks.csv',CHECKS)
        after=protected_snapshot();git_after=git_evidence()
        changes=[p for p in set(before)|set(after) if before.get(p)!=after.get(p)]
        hash_changes=[p for p,h in input_hashes.items() if sha(p)!=h]
        if changes or hash_changes or git_after!=git_before:
            raise ValueError(f'STOP: protected artifact changed: metadata {changes[:5]}, hashes {hash_changes[:5]}, git identical {git_after==git_before}')
        protection=dict(protected_file_count=len(before),protected_roots=['results/routeA/','results/routeB/','cases/','docs/','reference/','Scripts/routeA/','Scripts/routeB/','external v6 cases/routeB/'],
            full_metadata_inventory_unchanged=True,changed_count=len(changes),hashed_input_count=len(input_hashes),input_hashes_unchanged=True,
            git_diff_before_after_identical=True,git_existing_diff_empty=not git_after[0],git_head=git_after[2].strip(),solver_executions=0,mesh_generations=0,analyzer_main_invocations=0)
        (out/'logs/protection.json').write_text(json.dumps(protection,indent=2)+'\n')
        (out/'logs/git_after.diff').write_text(git_after[0]);(out/'logs/git_after.status').write_text(git_after[1])
        write_csv(out/'logs/input_sha256.csv',[dict(path=k,sha256=v) for k,v in sorted(input_hashes.items())])
        write_csv(out/'tables/csv_inventory.csv',[dict(path=str(f.relative_to(out)),rows=sum(1 for _ in f.open())-1) for f in sorted(out.rglob('*.csv'))])
        summary=dict(completed_at=datetime.now(ZoneInfo('Asia/Tokyo')).isoformat(),display_cases=len(cases),formal_conditions=24,
            RouteA_computed=12,RouteA_accepted=12,RouteB_computed=12,RouteB_accepted=9,logical_figures=len(inventory),png_files=len(inventory),pdf_files=len(inventory),
            csv_files=len(list(out.rglob('*.csv'))),numerical_checks=len(CHECKS),all_checks_pass=all(r['status']=='PASS' for r in CHECKS),solver_executions=0)
        (out/'logs/run_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
        if not args.case: readme(out,cases,inventory,protection,groups,ab,hp,gf)
        else: (out/'README.md').write_text(f'# Individual visualization: {args.case}\n\nAll source checks PASS; see logs/ and tables/figure_inventory.csv.\n')
        print(json.dumps(summary,indent=2),flush=True)
    except Exception as error:
        failed_after=protected_snapshot()
        failed_changes=[p for p in set(before)|set(failed_after) if before.get(p)!=failed_after.get(p)]
        (out/'logs/protection_on_failure.json').write_text(json.dumps(dict(protected_file_count=len(before),changed_count=len(failed_changes),changed_paths=failed_changes[:30],git_before_after_identical=git_evidence()==git_before,solver_executions=0),indent=2)+'\n')
        (out/'logs/STOP.json').write_text(json.dumps(dict(error=str(error),traceback=traceback.format_exc(),last_checks=CHECKS[-5:],solver_executed=False),indent=2)+'\n')
        write_csv(out/'logs/numerical_checks.csv',CHECKS)
        raise


if __name__=='__main__': main()
