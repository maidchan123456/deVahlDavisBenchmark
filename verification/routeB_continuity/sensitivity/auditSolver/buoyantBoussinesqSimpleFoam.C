/*---------------------------------------------------------------------------*\
  =========                 |
  \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox
   \\    /   O peration     | Website:  https://openfoam.org
    \\  /    A nd           | Copyright (C) 2011-2018 OpenFOAM Foundation
     \\/     M anipulation  |
-------------------------------------------------------------------------------
License
    This file is part of OpenFOAM.

    OpenFOAM is free software: you can redistribute it and/or modify it
    under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    OpenFOAM is distributed in the hope that it will be useful, but WITHOUT
    ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
    FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
    for more details.

    You should have received a copy of the GNU General Public License
    along with OpenFOAM.  If not, see <http://www.gnu.org/licenses/>.

Application
    buoyantBoussinesqSimpleFoam

Description
    Steady-state solver for buoyant, turbulent flow of incompressible fluids.

    Uses the Boussinesq approximation:
    \f[
        rho_{k} = 1 - beta(T - T_{ref})
    \f]

    where:
        \f$ rho_{k} \f$ = the effective (driving) density
        beta = thermal expansion coefficient [1/K]
        T = temperature [K]
        \f$ T_{ref} \f$ = reference temperature [K]

    Valid when:
    \f[
        \frac{beta(T - T_{ref})}{rho_{ref}} << 1
    \f]

\*---------------------------------------------------------------------------*/

#include "fvCFD.H"
#include "singlePhaseTransportModel.H"
#include "turbulentTransportModel.H"
#include "noRadiation.H"
#include "fvOptions.H"
#include "simpleControl.H"
#include "continuityAudit.H"
#include "steadyMonitor.H"

// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

int main(int argc, char *argv[])
{
    #include "postProcess.H"

    #include "setRootCaseLists.H"
    #include "createTime.H"
    #include "createMesh.H"
    #include "createControl.H"
    #include "createFields.H"
    #include "initContinuityErrs.H"

    turbulence->validate();
    volScalarField continuitySource(IOobject("continuitySource",runTime.constant(),mesh,
        IOobject::MUST_READ,IOobject::NO_WRITE),mesh);
    if(continuitySource.dimensions()!=dimless/dimTime)
        FatalErrorInFunction<<"continuitySource must have units 1/s"<<exit(FatalError);
    const bool monitorEnabled=runTime.controlDict().lookupOrDefault<bool>("steadyMonitorEnabled",true);
    const scalar pressureTolerance=runTime.controlDict().lookupOrDefault<scalar>("auditPressureTolerance",1e-10);
    SensitivityMonitor sensitivityMonitor(runTime);
    scalarField lastForcedResidual(mesh.nCells(),0.),lastPhysicalResidual(mesh.nCells(),0.);
    std::ofstream auditOut((runTime.path()/"continuityAudit.csv").c_str());
    auditOut<<"iteration,cell_count,Np,R_initial,R_recursive,linear_iterations,converged,true_residual_L1,R_true,recursive_residual_L1,abs_L1_norm_drift,true_nonreference_L1,true_reference_residual,physical_reference_residual,q_reference,mapping_defect_L1,mapping_defect_max,sum_abs_q,max_abs_q,mean_abs_div_phi,max_abs_div_phi,P95_abs_div_phi,P99_abs_div_phi,signed_volume_mean_div_phi,net_boundary_flux,Up,Kp,epsilon_phi_mean,epsilon_phi_max,ratio_recursive,ratio_true,native_sum_local,native_global,reference_cell,max_cell_id,max_cell_x,max_cell_y,max_cell_z\n";

    // * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

    Info<< "\nStarting time loop\n" << endl;

    while (simple.loop(runTime))
    {
        Info<< "Time = " << runTime.timeName() << nl << endl;

        // Pressure-velocity SIMPLE corrector
        {
            #include "UEqn.H"
            #include "TEqn.H"
            #include "pEqn.H"
        }

        laminarTransport.correct();
        turbulence->correct();

        if(monitorEnabled && sensitivityMonitor.check(runTime,mesh,U,T,phi,pressureTolerance))
        {
            Info<<"SENSITIVITY_STEADY_CONFIRMED"<<nl;
            runTime.writeAndEnd();
        }
        runTime.write();

        Info<< "ExecutionTime = " << runTime.elapsedCpuTime() << " s"
            << "  ClockTime = " << runTime.elapsedClockTime() << " s"
            << nl << endl;
    }

    std::ofstream cells((runTime.path()/"sourceCells.csv").c_str());
    cells<<"cell,g,V,physical_residual,forced_residual,X,Z\n";
    forAll(mesh.V(),i) cells<<std::setprecision(17)<<i<<','
        <<mesh.V()[i]*continuitySource[i]<<','<<mesh.V()[i]<<','
        <<lastPhysicalResidual[i]<<','<<lastForcedResidual[i]<<','
        <<mesh.C()[i].x()/.01<<','<<mesh.C()[i].y()/.01<<'\n';
    Info<<"SENSITIVITY_STATUS "<<(sensitivityMonitor.steady ? "STEADY" : "NOT_CONVERGED")<<nl;
    Info<< "End\n" << endl;

    return 0;
}


// ************************************************************************* //
