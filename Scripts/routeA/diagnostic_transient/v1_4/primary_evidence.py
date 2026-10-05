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
    # Native geometric arithmetic may differ by a few ulps within one grid line.
    # Group only within64eps*L, then interpolate using each actual bracket coordinate.
    tol=64*np.finfo(float).eps*L
    def groups(axis):
        ordered=np.sort(axis);out=[]
        for value in ordered:
            if not out or value-out[-1][-1]>tol:out.append([value])
            else:out[-1].append(value)
        return np.asarray([np.mean(g) for g in out])
    xs=groups(points[:,0]);ys=groups(points[:,1]);nx=len(xs);ny=len(ys);need(nx*ny==len(T) and nx>=2 and ny>=2,'PRIMARY_RECTANGULAR_GRID')
    ixcell=np.argmin(abs(points[:,0,None]-xs[None,:]),axis=1);iycell=np.argmin(abs(points[:,1,None]-ys[None,:]),axis=1)
    order=np.argsort(iycell*nx+ixcell);need(np.array_equal((iycell*nx+ixcell)[order],np.arange(len(T))),'PRIMARY_CELL_ADDRESSING')
    ux=U[order].reshape(ny,nx,3);temp=T[order].reshape(ny,nx);xy=points[order].reshape(ny,nx,3)
    need(np.max(abs(xy[:,:,0]-xs[None,:]))<=tol and np.max(abs(xy[:,:,1]-ys[:,None]))<=tol,'PRIMARY_NONUNIFORM_LINES')
    ix=np.searchsorted(xs,L/2);iy=np.searchsorted(ys,L/2);need(0<ix<nx and 0<iy<ny,'PRIMARY_CENTRELINE_BRACKETS')
    wx=(L/2-xy[:,ix-1,0])/(xy[:,ix,0]-xy[:,ix-1,0]);wy=(L/2-xy[iy-1,:,1])/(xy[iy,:,1]-xy[iy-1,:,1])
    uline=(1-wx)*ux[:,ix-1,0]+wx*ux[:,ix,0];wline=(1-wy)*ux[iy-1,:,1]+wy*ux[iy,:,1]
    uy=(1-wx)*xy[:,ix-1,1]+wx*xy[:,ix,1];wxcoord=(1-wy)*xy[iy-1,:,0]+wy*xy[iy,:,0]
    q=np.linspace(0,L,4097);uq=np.interp(q,np.r_[0,uy,L],np.r_[0,uline,0])*L/alpha;wq=np.interp(q,np.r_[0,wxcoord,L],np.r_[0,wline,0])*L/alpha
    ui=int(np.argmax(uq));wi=int(np.argmax(wq));theta=(T-tc)/dt
    cavity=1+float(np.sum(V*(L/alpha)*U[:,0]*theta)/np.sum(V))
    hot_local=L*(th-temp[:,0])/(xy[:,0,0]*dt)
    rho=np.asarray(state['rho']['cells']);rhoT=np.asarray(state['rhoFluidThermo:rho']['cells']);mass=float(np.sum(V*rho))
    return {'Nu_bar_cavity':cavity,'Nu_bar_0':float(np.mean(hot_local)),'Umax':float(uq[ui]),'Umax_Z':float(q[ui]/L),'Wmax':float(wq[wi]),'Wmax_X':float(q[wi]/L),'total_mass':mass,'rho_min':float(rho.min()),'rho_max':float(rho.max()),'rho_mean':float(np.sum(V*rho)/np.sum(V)),'thermo_rho_min':float(rhoT.min()),'thermo_rho_max':float(rhoT.max()),'thermo_rho_mean':float(np.sum(V*rhoT)/np.sum(V))}

def required_columns(values,contract):
    required=set(contract['sampling']['required_primary_and_stage_columns'])
    need(required<=set(values),'PRIMARY_REQUIRED_COLUMNS_MISSING: '+','.join(sorted(required-set(values))))
    need(values.get('validity') is True,'PRIMARY_VALIDITY')
    return values
