"""Registered QoIs from current state, never disk fields; frozen policy functions."""
import importlib.util,math
from pathlib import Path
import numpy as np
from packed import need
H=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('frozen_contract_policy',H.parent/'v1_1/contract_policy.py');policy=importlib.util.module_from_spec(spec);spec.loader.exec_module(policy)

def primary(state,centres,physical):
    L=physical['geometry_m']['L'];p=physical['properties'];alpha=p['alpha0_m2_s'];tc=p['Tc_K'];dt=p['DeltaT_K'];th=p['Th_K']
    points=np.asarray(centres,dtype=np.float64);U=np.asarray(state['U']['cells'],dtype=np.float64);T=np.asarray(state['T']['cells'],dtype=np.float64);V=np.asarray(state['volumes'],dtype=np.float64)
    need(len(points)==len(T)==len(U)==len(V) and np.all(V>0),'PRIMARY_SIZE')
    xs=np.unique(points[:,0]);ys=np.unique(points[:,1]);nx=len(xs);ny=len(ys);need(nx*ny==len(T) and nx>=2 and ny>=2,'PRIMARY_RECTANGULAR_GRID')
    order=np.lexsort((points[:,0],points[:,1]));ux=U[order].reshape(ny,nx,3);temp=T[order].reshape(ny,nx)
    need(np.allclose(points[order,0].reshape(ny,nx),xs[None,:],rtol=0,atol=0) and np.allclose(points[order,1].reshape(ny,nx),ys[:,None],rtol=0,atol=0),'PRIMARY_CELL_ADDRESSING')
    ix=np.searchsorted(xs,L/2);iy=np.searchsorted(ys,L/2);need(0<ix<nx and 0<iy<ny,'PRIMARY_CENTRELINE_BRACKETS')
    wx=(L/2-xs[ix-1])/(xs[ix]-xs[ix-1]);wy=(L/2-ys[iy-1])/(ys[iy]-ys[iy-1])
    uline=(1-wx)*ux[:,ix-1,0]+wx*ux[:,ix,0];wline=(1-wy)*ux[iy-1,:,1]+wy*ux[iy,:,1]
    q=np.linspace(0,L,4097);uq=np.interp(q,np.r_[0,ys,L],np.r_[0,uline,0])*L/alpha;wq=np.interp(q,np.r_[0,xs,L],np.r_[0,wline,0])*L/alpha
    ui=int(np.argmax(uq));wi=int(np.argmax(wq));theta=(T-tc)/dt
    cavity=1+float(np.sum(V*(L/alpha)*U[:,0]*theta)/np.sum(V))
    hot_local=L*(th-temp[:,0])/(xs[0]*dt)
    rho=np.asarray(state['rho']['cells']);rhoT=np.asarray(state['rhoFluidThermo:rho']['cells']);mass=float(np.sum(V*rho))
    return {'Nu_bar_cavity':cavity,'Nu_bar_0':float(np.mean(hot_local)),'Umax':float(uq[ui]),'Umax_Z':float(q[ui]/L),'Wmax':float(wq[wi]),'Wmax_X':float(q[wi]/L),'total_mass':mass,'rho_min':float(rho.min()),'rho_max':float(rho.max()),'rho_mean':float(np.sum(V*rho)/np.sum(V)),'thermo_rho_min':float(rhoT.min()),'thermo_rho_max':float(rhoT.max()),'thermo_rho_mean':float(np.sum(V*rhoT)/np.sum(V))}

def required_columns(values,contract):
    required=set(contract['sampling']['required_primary_and_stage_columns'])
    need(required<=set(values),'PRIMARY_REQUIRED_COLUMNS_MISSING: '+','.join(sorted(required-set(values))))
    need(values.get('validity') is True,'PRIMARY_VALIDITY')
    return values
