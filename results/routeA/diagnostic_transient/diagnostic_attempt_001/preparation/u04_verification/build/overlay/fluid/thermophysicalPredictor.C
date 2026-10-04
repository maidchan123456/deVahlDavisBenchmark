
// ROUTE_A_OBSERVATION_BEGIN
#include "NativeStageObserver.H"
// ROUTE_A_OBSERVATION_END
/*---------------------------------------------------------------------------*\
  =========                 |
  \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox
   \\    /   O peration     | Website:  https://openfoam.org
    \\  /    A nd           | Copyright (C) 2022-2023 OpenFOAM Foundation
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

#include "routeADiagnosticFluid.H"
#include "fvcDdt.H"
#include "fvmDiv.H"

// * * * * * * * * * * * * * * Member Functions  * * * * * * * * * * * * * * //

void Foam::solvers::routeADiagnosticFluid::thermophysicalPredictor()
{
    volScalarField& he = thermo_.he();
// ROUTE_A_OBSERVATION_BEGIN
routeAU04::stage("energy_begin", mesh);
routeAU04::history("S_K", K);
if (buoyancy.valid()) routeAU04::thermal(thermo_.Cpv()(), buoyancy->g);
// ROUTE_A_OBSERVATION_END


    fvScalarMatrix EEqn
    (
        routeAU04::tap("S_e", fvm::ddt(rho, he)) + routeAU04::tap("F_e", fvm::div(phi, he))
      + routeAU04::tap("S_K", fvc::ddt(rho, K)) + routeAU04::tap("F_K", fvc::div(phi, K))
      + routeAU04::tap("W_p", pressureWork
        (
            he.name() == "e"
          ? fvc::div(phi, p/rho)()
          : -dpdt
        ))
      + routeAU04::tap("H_out", thermophysicalTransport->divq(he))
     ==
        (
            buoyancy.valid()
          ? routeAU04::tap("S_models", fvModels().source(rho, he)) + routeAU04::tap("W_g", rho*(U & buoyancy->g))
          : routeAU04::tap("S_models", fvModels().source(rho, he))
        )
    );

    
// ROUTE_A_OBSERVATION_BEGIN
routeAU04::total("energy_unrelaxed_assembly", EEqn);
// ROUTE_A_OBSERVATION_END
EEqn.relax();
// ROUTE_A_OBSERVATION_BEGIN
routeAU04::total("energy_after_relax", EEqn);
// ROUTE_A_OBSERVATION_END


    fvConstraints().constrain(EEqn);

    EEqn.solve();
// ROUTE_A_OBSERVATION_BEGIN
routeAU04::solved("energy_after_solve", EEqn);
// ROUTE_A_OBSERVATION_END


    fvConstraints().constrain(he);

    
// ROUTE_A_OBSERVATION_BEGIN
routeAU04::stage("before_thermo_correct", mesh);
// ROUTE_A_OBSERVATION_END
thermo_.correct();
// ROUTE_A_OBSERVATION_BEGIN
routeAU04::stage("after_thermo_correct", mesh);
// ROUTE_A_OBSERVATION_END

}


// ************************************************************************* //
