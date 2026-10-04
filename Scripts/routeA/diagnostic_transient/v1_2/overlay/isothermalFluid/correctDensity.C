
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

#include "routeADiagnosticIsothermalFluid.H"
#include "fvcDiv.H"

// * * * * * * * * * * * * * * Member Functions  * * * * * * * * * * * * * * //

void Foam::solvers::routeADiagnosticIsothermalFluid::correctDensity()
{
    volScalarField& rho(rho_);
// ROUTE_A_OBSERVATION_BEGIN
routeAU04::stage("before_correctDensity", mesh);
// ROUTE_A_OBSERVATION_END


    fvScalarMatrix rhoEqn
    (
        routeAU04::tap("D_B_rho", fvm::ddt(rho)) + routeAU04::tap("div_phi", fvc::div(phi))
      ==
        routeAU04::tap("mass_models", fvModels().source(rho))
    );

    
// ROUTE_A_OBSERVATION_BEGIN
routeAU04::total("mass_unrelaxed_assembly", rhoEqn);
// ROUTE_A_OBSERVATION_END
fvConstraints().constrain(rhoEqn);

    rhoEqn.solve();
// ROUTE_A_OBSERVATION_BEGIN
routeAU04::solved("mass_after_solve", rhoEqn);
// ROUTE_A_OBSERVATION_END


    fvConstraints().constrain(rho);
// ROUTE_A_OBSERVATION_BEGIN
routeAU04::stage("after_correctDensity", mesh);
// ROUTE_A_OBSERVATION_END

}


// ************************************************************************* //
