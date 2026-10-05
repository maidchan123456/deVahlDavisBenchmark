#!/usr/bin/env python3
"""Reproduce isolated serial v6 microcases; no benchmark solver access."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from common import HERE, ROOT, RESULTS, WORK, L, WIDTH, read_case, parser
import numpy as np

FOAM = Path('/home/mirai/OpenFOAM/OpenFOAM-6')
AUDIT = HERE/'auditSolver/bin/buoyantBoussinesqSimpleFoamContinuityAudit'
MANIFEST = RESULTS/'run_manifest.json'


def header(name, cls='dictionary'):
    return f'FoamFile {{ version 2.0; format ascii; class {cls}; object {name}; }}\n'


def make_template():
    template = HERE/'microcase_template'
    def put(relative, text):
        p=template/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
    put('system/controlDict', header('controlDict')+'''application buoyantBoussinesqSimpleFoam;
startFrom startTime;
startTime 0;
stopAt endTime;
endTime 10;
deltaT 1;
writeControl timeStep;
writeInterval 1;
purgeWrite 0;
writeFormat ascii;
writePrecision 16;
writeCompression off;
timeFormat general;
timePrecision 10;
runTimeModifiable false;
''')
    put('system/blockMeshDict',header('blockMeshDict')+'''convertToMeters 1;
vertices ((0 0 0) (0.01 0 0) (0.01 0.01 0) (0 0.01 0)
          (0 0 0.001) (0.01 0 0.001) (0.01 0.01 0.001) (0 0.01 0.001));
blocks (hex (0 1 2 3 4 5 6 7) (@N@ @N@ 1) simpleGrading (1 1 1));
edges ();
boundary
(
 hotWall { type wall; faces ((0 4 7 3)); }
 coldWall { type wall; faces ((1 2 6 5)); }
 bottomWall { type wall; faces ((0 1 5 4)); }
 topWall { type wall; faces ((3 7 6 2)); }
 front { type empty; faces ((0 3 2 1)); }
 back { type empty; faces ((4 5 6 7)); }
);
mergePatchPairs ();
''')
    put('system/fvSchemes',header('fvSchemes')+'''ddtSchemes { default steadyState; }
gradSchemes { default Gauss linear; }
divSchemes { default none; div(phi,U) Gauss linear; div(phi,T) Gauss linear;
             div((nuEff*dev2(T(grad(U))))) Gauss linear; }
laplacianSchemes { default Gauss linear corrected; }
interpolationSchemes { default linear; }
snGradSchemes { default corrected; }
fluxRequired { default no; p_rgh; }
''')
    put('system/fvSolution',header('fvSolution')+'''solvers
{
 p_rgh { solver PCG; preconditioner DIC; tolerance @TOL@; relTol 0; maxIter 10000; }
 U { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-12; relTol 0; }
 T { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-12; relTol 0; }
}
SIMPLE { nNonOrthogonalCorrectors 0; pRefCell @REF@; pRefValue 0; }
relaxationFactors { fields { p_rgh 0.3; } equations { U 0.7; T 0.7; } }
''')
    beta=3e4*1e-12/(.71*9.81*L**3)
    put('constant/transportProperties',header('transportProperties')+f'''transportModel Newtonian;
nu [0 2 -1 0 0 0 0] 1e-6;
beta [0 0 0 -1 0 0 0] {beta:.17g};
TRef [0 0 0 1 0 0 0] 300.5;
Pr [0 0 0 0 0 0 0] 0.71;
Prt [0 0 0 0 0 0 0] 0.85;
rhoRef [1 -3 0 0 0 0 0] 1;
CpRef [0 2 -2 -1 0 0 0] 1000;
''')
    put('constant/turbulenceProperties',header('turbulenceProperties')+'simulationType laminar;\n')
    put('constant/radiationProperties',header('radiationProperties')+'radiationModel none;\n')
    put('constant/g',header('g','uniformDimensionedVectorField')+'dimensions [0 1 -2 0 0 0 0];\nvalue (0 -9.81 0);\n')
    fields={'U':('volVectorField','[0 1 -1 0 0 0 0]','(0 0 0)'),
            'T':('volScalarField','[0 0 0 1 0 0 0]','300.5'),
            'p_rgh':('volScalarField','[0 2 -2 0 0 0 0]','0'),
            'alphat':('volScalarField','[0 2 -1 0 0 0 0]','0')}
    for name,(cls,dim,value) in fields.items():
        text=header(name,cls)+f'dimensions {dim};\ninternalField uniform {value};\nboundaryField\n{{\n'
        for patch in ('hotWall','coldWall','bottomWall','topWall'):
            if name=='T':
                bc=f'type fixedValue; value uniform {301 if patch=="hotWall" else 300};' if patch in ('hotWall','coldWall') else 'type zeroGradient;'
            elif name=='p_rgh':bc='type fixedFluxPressure; value uniform 0;'
            elif name=='U':bc='type fixedValue; value uniform (0 0 0);'
            else:bc='type fixedValue; value uniform 0;'
            text+=patch+' { '+bc+' }\n'
        text+='front { type empty; }\nback { type empty; }\n}\n'
        put('0/'+name,text)
    return template


def foam_env():
    command=['bash','-c','source "$1" >/dev/null; env -0','verification-env',str(FOAM/'etc/bashrc')]
    raw=subprocess.check_output(command)
    return dict(item.decode().split('=',1) for item in raw.split(b'\0') if b'=' in item)


def execute(argv, log, environment, cwd=None):
    arguments=[str(a) for a in argv]
    if '-case' in arguments:
        case_path=Path(arguments[arguments.index('-case')+1]).resolve()
        if not case_path.is_relative_to((WORK/'microcases').resolve()):
            raise RuntimeError('STOP: solver/mesh execution outside verification microcase allowlist')
    with log.open('w') as stream:
        completed=subprocess.run([str(a) for a in argv],cwd=cwd,env=environment,stdout=stream,stderr=subprocess.STDOUT)
    text=log.read_text()
    if completed.returncode or 'FOAM FATAL' in text or 'nan' in text.lower().split():
        raise RuntimeError(f'STOP: independent microcase failed; inspect {log}')


def make_case(template, name, n, tolerance, environment, reference=None):
    case=WORK/'microcases'/name
    if case.exists():raise RuntimeError(f'Refusing to overwrite existing independent case: {case}')
    shutil.copytree(template,case)
    ref=reference if reference is not None else (n//2)*n+n//2
    for f in ('system/blockMeshDict','system/fvSolution'):
        p=case/f;p.write_text(p.read_text().replace('@N@',str(n)).replace('@TOL@',str(tolerance)).replace('@REF@',str(ref)))
    execute(['blockMesh','-case',case],case/'log.blockMesh',environment)
    return case


def equivalence(stock,audit,n):
    comparisons={}
    for field in ('U','T','p_rgh','phi'):
        a=stock/'10'/field;b=audit/'10'/field
        same=hashlib.sha256(a.read_bytes()).hexdigest()==hashlib.sha256(b.read_bytes()).hexdigest()
        count=2*n*(n-1) if field=='phi' else n*n
        reader=parser.read_vector if field=='U' else parser.read_scalar
        x=reader(a,count);y=reader(b,count)
        comparisons[field]={'file_sha256_equal':same,'stock_sha256':hashlib.sha256(a.read_bytes()).hexdigest(),
                            'audit_sha256':hashlib.sha256(b.read_bytes()).hexdigest(),
                            'internal_max_absolute_difference':float(np.max(abs(x-y))),
                            'internal_relative_max_difference':float(np.max(abs(x-y))/max(np.max(abs(x)),np.finfo(float).tiny))}
    # Same paths inside headers; the full-file hash includes all patch values.
    if not all(d['file_sha256_equal'] for d in comparisons.values()):
        raise RuntimeError('STOP: audit/stock full field hashes differ; do not use audit evidence')
    return comparisons


def run():
    RESULTS.mkdir(parents=True,exist_ok=True);WORK.mkdir(parents=True,exist_ok=True)
    from synthetic_operator_tests import run as synthetic
    synthetic()  # Mandatory PASS gate before solver execution.
    template=make_template();environment=foam_env()
    execute(['wmake'],WORK/'log.build',environment,cwd=HERE/'auditSolver')
    state={'Ra_test':3e4,'Pr':.71,'L_m':L,'width_m':WIDTH,'serial':True,'iterations':10,
           'write_precision':16,'write_format':'ascii','relTol':0,'benchmark_cases_executed':False,
           'cases':[],'audit_equivalence':None}
    def save():MANIFEST.write_text(json.dumps(state,indent=2)+'\n')
    save()
    representative=make_case(template,'audit_n20_tol1e-8',20,1e-8,environment)
    stock=make_case(template,'stock_n20_tol1e-8',20,1e-8,environment)
    execute(['buoyantBoussinesqSimpleFoam','-case',stock],stock/'log.stock',environment)
    execute([AUDIT,'-case',representative],representative/'log.audit',environment)
    state['audit_equivalence']=equivalence(stock,representative,20)
    state['cases'].append({'id':representative.name,'n':20,'tolerance':1e-8,'path':str(representative),'role':'sweep'})
    save()
    for n in (20,40,80):
        for tolerance in (1e-6,1e-8,1e-10):
            if n==20 and tolerance==1e-8:continue
            name=f'audit_n{n}_tol{tolerance:g}'
            case=make_case(template,name,n,tolerance,environment)
            execute([AUDIT,'-case',case],case/'log.audit',environment)
            state['cases'].append({'id':name,'n':n,'tolerance':tolerance,'path':str(case),'role':'sweep'})
            save()
            print('Completed',name,flush=True)
    restart=make_case(template,'restart_n20_tol1e-8',20,1e-8,environment)
    p=restart/'system/controlDict';p.write_text(p.read_text().replace('endTime 10;','endTime 5;'))
    execute([AUDIT,'-case',restart],restart/'log.audit_first5',environment)
    shutil.copy2(restart/'continuityAudit.csv',restart/'continuityAudit_first5.csv')
    p.write_text(p.read_text().replace('endTime 5;','endTime 10;').replace('startFrom startTime;','startFrom latestTime;'))
    execute([AUDIT,'-case',restart],restart/'log.audit_restart',environment)
    state['cases'].append({'id':restart.name,'n':20,'tolerance':1e-8,'path':str(restart),'role':'restart'})
    save()
    # One low-cost reference-location check, no changes to the sweep setup.
    refcase=make_case(template,'reference_corner_n20_tol1e-8',20,1e-8,environment,reference=0)
    execute([AUDIT,'-case',refcase],refcase/'log.audit',environment)
    state['cases'].append({'id':refcase.name,'n':20,'tolerance':1e-8,'path':str(refcase),'role':'reference_location'})
    save()
    print('Independent solver suite complete; stock/audit hashes all match.',flush=True)


if __name__=='__main__':
    try:
        run()
    except Exception as exc:
        RESULTS.mkdir(parents=True,exist_ok=True)
        (RESULTS/'STOP.json').write_text(json.dumps({'status':'STOP','reason':str(exc)},indent=2)+'\n')
        stage=json.loads((RESULTS/'operator_stage_summary.json').read_text()) if (RESULTS/'operator_stage_summary.json').exists() else {'status':'NOT_RUN'}
        (RESULTS/'STOP_review.md').write_text(
            '# Route B Case C partial verification — STOP\n\n'
            +f'Reason: {exc}\n\nOperator stage: {stage["status"]}. '
            +'Existing stage CSVs, logs and run manifest are retained. Further solver work stopped.\n\n'
            +'No benchmark results were used for threshold derivation. Production files and criteria were not changed. '
            +'tau_phi remains UNRESOLVED and Candidate B remains PROVISIONAL.\n')
        raise
