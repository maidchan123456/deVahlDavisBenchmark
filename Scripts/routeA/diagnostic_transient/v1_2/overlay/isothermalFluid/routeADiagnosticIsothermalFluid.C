
// ROUTE_A_OBSERVATION_BEGIN
#include "NativeStageObserver.H"
// ROUTE_A_OBSERVATION_END
/*---------------------------------------------------------------------------*\
  =========                 |
  \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox
   \\    /   O peration     | Website:  https://openfoam.org
    \\  /    A nd           | Copyright (C) 2022-2025 OpenFOAM Foundation
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

\*---------------------------------------------------------------------------*/

#include "routeADiagnosticIsothermalFluid.H"
#include "localEulerDdtScheme.H"
#include "hydrostaticInitialisation.H"
#include "fvcMeshPhi.H"
#include "fvcVolumeIntegrate.H"
#include "fvcReconstruct.H"
#include "fvcDiv.H"
#include "fvcSnGrad.H"
#include "addToRunTimeSelectionTable.H"

// * * * * * * * * * * * * * * Static Data Members * * * * * * * * * * * * * //

namespace Foam
{
namespace solvers
{
    defineTypeNameAndDebug(routeADiagnosticIsothermalFluid, 0);
    addToRunTimeSelectionTable(solver, routeADiagnosticIsothermalFluid, fvMesh);
}
}


// * * * * * * * * * * * * * Private Member Functions  * * * * * * * * * * * //

void Foam::solvers::routeADiagnosticIsothermalFluid::correctCoNum()
{
    fluidSolver::correctCoNum(rho, phi);
}


void Foam::solvers::routeADiagnosticIsothermalFluid::continuityErrors()
{
    fluidSolver::continuityErrors(rho, thermo.rho(), phi);
}


// * * * * * * * * * * * * * Protected Member Functions  * * * * * * * * * * //

Foam::tmp<Foam::volScalarField::Internal>
Foam::solvers::routeADiagnosticIsothermalFluid::pressureWork
(
    const tmp<volScalarField::Internal>& work
) const
{
    if (mesh.moving())
    {
        return
            work
          + fvc::div
            (
                fvc::interpolate(rho)*fvc::meshPhi(rho, U),
                p/rho,
                "div(phi,(p|rho))"
            )();
    }
    else
    {
        return move(work);
    }
}


// * * * * * * * * * * * * * * * * Constructors  * * * * * * * * * * * * * * //

Foam::solvers::routeADiagnosticIsothermalFluid::routeADiagnosticIsothermalFluid
(
    fvMesh& mesh,
    autoPtr<fluidThermo> thermoPtr
)
:
    fluidSolver(mesh),

    thermoPtr_(thermoPtr),
    thermo_(thermoPtr_()),

    p_(thermo_.p()),

    rho_
    (
        IOobject
        (
            "rho",
            runTime.name(),
            mesh,
            IOobject::READ_IF_PRESENT,
            IOobject::AUTO_WRITE
        ),
        thermo_.renameRho()
    ),

    dpdt
    (
        IOobject
        (
            "dpdt",
            runTime.name(),
            mesh
        ),
        mesh,
        dimensionedScalar(p_.dimensions()/dimTime, 0)
    ),

    buoyancy(buoyancy::New(mesh)),

    p_rgh_(buoyancy.valid() ? buoyancy->p_rgh : p_),

    pressureReference
    (
        p_,
        p_rgh_,
        pimple.dict(),
        thermo_.incompressible()
    ),

    U_
    (
        IOobject
        (
            "U",
            runTime.name(),
            mesh,
            IOobject::MUST_READ,
            IOobject::AUTO_WRITE
        ),
        mesh
    ),

    phi_
    (
        IOobject
        (
            "phi",
            runTime.name(),
            mesh,
            IOobject::READ_IF_PRESENT,
            IOobject::AUTO_WRITE
        ),
        linearInterpolate(rho_*U_) & mesh.Sf()
    ),

    K("K", 0.5*magSqr(U_)),

    momentumTransport
    (
        compressible::momentumTransportModel::New
        (
            rho_,
            U_,
            phi_,
            thermo_
        )
    ),

    initialMass(fvc::domainIntegrate(rho_)),

    MRF(mesh),

    thermo(thermo_),
    p(p_),
    p_rgh(p_rgh_),
    rho(rho_),
    U(U_),
    phi(phi_)
{
    mesh.schemes().setFluxRequired(p.name());
    momentumTransport->validate();

    if (buoyancy.valid())
    {
        hydrostaticInitialisation
        (
            p_rgh_,
            p_,
            rho_,
            U,
            buoyancy->gh,
            buoyancy->ghf,
            buoyancy->pRef,
            thermo_,
            pimple.dict()
        );

        netForce = new volVectorField
        (
            IOobject
            (
                "netForce",
                runTime.name(),
                mesh
            ),
            fvc::reconstruct
            (
                (-buoyancy->ghf*fvc::snGrad(rho) - fvc::snGrad(p_rgh))
               *mesh.magSf()
            )
        );
    }

    if (transient())
    {
        correctCoNum();
    }
    else if (LTS)
    {
        Info<< "Using LTS" << endl;

        trDeltaT = tmp<volScalarField>
        (
            new volScalarField
            (
                IOobject
                (
                    fv::localEulerDdt::rDeltaTName,
                    runTime.name(),
                    mesh,
                    IOobject::READ_IF_PRESENT,
                    IOobject::AUTO_WRITE
                ),
                mesh,
                dimensionedScalar(dimless/dimTime, 1),
                extrapolatedCalculatedFvPatchScalarField::typeName
            )
        );
    }
}


Foam::solvers::routeADiagnosticIsothermalFluid::routeADiagnosticIsothermalFluid(fvMesh& mesh)
:
    routeADiagnosticIsothermalFluid(mesh, fluidThermo::New(mesh))
{}


// * * * * * * * * * * * * * * * * Destructor  * * * * * * * * * * * * * * * //

Foam::solvers::routeADiagnosticIsothermalFluid::~routeADiagnosticIsothermalFluid()
{}


// * * * * * * * * * * * * * * Member Functions  * * * * * * * * * * * * * * //

void Foam::solvers::routeADiagnosticIsothermalFluid::preSolve()
{
    if ((mesh.dynamic() || MRF.size()) && !rhoUf.valid())
    {
        Info<< "Constructing face momentum rhoUf" << endl;

        // Ensure the U BCs are up-to-date before constructing Uf
        U_.correctBoundaryConditions();

        rhoUf = new surfaceVectorField
        (
            IOobject
            (
                "rhoUf",
                runTime.name(),
                mesh,
                IOobject::READ_IF_PRESENT,
                IOobject::AUTO_WRITE
            ),
            fvc::interpolate(rho*U)
        );
    }

    if (transient())
    {
        correctCoNum();
    }
    else if (LTS)
    {
        setRDeltaT();
    }

    // Store divrhoU from the previous mesh so that it can be mapped
    // and used in correctPhi to ensure the corrected phi has the
    // same divergence
    if (correctPhi || mesh.topoChanging())
    {
        divrhoU = new volScalarField
        (
            "divrhoU",
            fvc::div(fvc::absolute(phi, rho, U))
        );
    }

    fvModels().preUpdateMesh();

    // Store momentum to set rhoUf for introduced faces
    if (mesh.topoChanging())
    {
        rhoU = new volVectorField("rhoU", rho*U);

        for (label i = 1; i <= rhoUf().nOldTimes(false); ++ i)
        {
            rhoU().oldTimeRef(i) == rho.oldTime(i)*U.oldTime(i);
        }
    }

    // Update the mesh for topology change, mesh to mesh mapping
    mesh_.update();
}


void Foam::solvers::routeADiagnosticIsothermalFluid::prePredictor()
{
    if
    (
        !mesh.schemes().steady()
     && !pimple.simpleRho()
     && pimple.firstIter()
    )
    {
        correctDensity();
    }
}


void Foam::solvers::routeADiagnosticIsothermalFluid::momentumTransportPredictor()
{
    momentumTransport->predict();
}


void Foam::solvers::routeADiagnosticIsothermalFluid::thermophysicalTransportPredictor()
{}


void Foam::solvers::routeADiagnosticIsothermalFluid::thermophysicalPredictor()
{
    thermo_.correct();
}


void Foam::solvers::routeADiagnosticIsothermalFluid::pressureCorrector()
{
    while (pimple.correct())
    {
// ROUTE_A_OBSERVATION_BEGIN
routeAU04::stage("pressure_start", mesh);
// ROUTE_A_OBSERVATION_END

        if (buoyancy.valid())
        {
            correctBuoyantPressure();
        }
        else
        {
            correctPressure();
        }
    }

    tUEqn.clear();
}


void Foam::solvers::routeADiagnosticIsothermalFluid::momentumTransportCorrector()
{
    momentumTransport->correct();
}


void Foam::solvers::routeADiagnosticIsothermalFluid::thermophysicalTransportCorrector()
{}


void Foam::solvers::routeADiagnosticIsothermalFluid::postSolve()
{
    divrhoU.clear();

    if (!mesh.schemes().steady())
    {

// ROUTE_A_OBSERVATION_BEGIN
routeAU04::stage("before_postSolve_EOS_copy", mesh);
// ROUTE_A_OBSERVATION_END
        rho_ = thermo.rho();
// ROUTE_A_OBSERVATION_BEGIN
routeAU04::stage("after_postSolve_EOS_copy", mesh);
// ROUTE_A_OBSERVATION_END


        // Correct rhoUf with the updated density if the mesh is moving
        fvc::correctRhoUf(rhoUf, rho, U, phi, MRF);
    }
}


// ************************************************************************* //
