// Verification-only diagnostics. No mutation of the live pressure matrix/fields.
#include "PCG.H"
#include <fstream>
#include <iomanip>
#include <vector>
#include <algorithm>

class ContinuityAuditMatrix : public Foam::fvScalarMatrix
{
public:
    explicit ContinuityAuditMatrix(const Foam::fvScalarMatrix& original)
    : Foam::fvScalarMatrix(original)
    {
        addBoundaryDiag(diag(), 0);
        addBoundarySource(source(), false);
    }

    Foam::scalarField trueResidual() const
    {
        Foam::scalarField Ap(psi().size());
        Amul(Ap, psi().primitiveField(), const_cast<ContinuityAuditMatrix&>(*this).boundaryCoeffs(),
             psi().boundaryField().scalarInterfaces(), 0);
        return source() - Ap;
    }

    Foam::scalar normalization() const
    {
        Foam::scalarField Ap(psi().size()), scratch(psi().size());
        Amul(Ap, psi().primitiveField(), const_cast<ContinuityAuditMatrix&>(*this).boundaryCoeffs(),
             psi().boundaryField().scalarInterfaces(), 0);
        Foam::dictionary controls;
        controls.add("tolerance", 1e-10);
        controls.add("relTol", 0.0);
        // Call the installed PCG's actual normFactor, without calling solve.
        Foam::PCG linear(psi().name(), *this, const_cast<ContinuityAuditMatrix&>(*this).boundaryCoeffs(), const_cast<ContinuityAuditMatrix&>(*this).internalCoeffs(),
                        psi().boundaryField().scalarInterfaces(), controls);
        return linear.normFactor(psi().primitiveField(), source(), Ap, scratch);
    }
};

Foam::scalar auditPercentile(std::vector<Foam::scalar> values, double fraction)
{
    std::sort(values.begin(), values.end());
    double position = fraction*(values.size()-1);
    std::size_t i = static_cast<std::size_t>(position);
    std::size_t j = std::min(i+1, values.size()-1);
    return values[i] + (position-i)*(values[j]-values[i]);
}

void writeContinuityAudit
(
    std::ostream& out, const Foam::Time& runTime, const Foam::fvMesh& mesh,
    const Foam::surfaceScalarField& phi, const Foam::volVectorField& U,
    Foam::label reference, Foam::scalar normFactor,
    const Foam::solverPerformance& performance,
    const Foam::scalarField& trueResidual,
    const Foam::scalarField& physicalResidual
)
{
    using namespace Foam;
    scalarField q(mesh.nCells(), 0.0);
    const labelUList& owner = mesh.owner();
    const labelUList& neighbour = mesh.neighbour();
    forAll(owner, f)
    {
        q[owner[f]] += phi[f];
        q[neighbour[f]] -= phi[f];
    }
    scalar boundaryNet = 0;
    forAll(mesh.boundary(), patch)
    {
        if (mesh.boundary()[patch].type() == "empty") continue;
        const labelUList& cells = mesh.boundary()[patch].faceCells();
        const scalarField& pf = phi.boundaryField()[patch];
        forAll(pf, f)
        {
            q[cells[f]] += pf[f];
            boundaryNet += pf[f];
        }
    }
    scalarField d(q/mesh.V());
    scalar volume = gSum(mesh.V());
    scalar mean = gSum(mag(q))/volume;
    scalar up = gMax(mag(U.primitiveField()));
    scalar maximum = 0;
    label maxCell = 0;
    std::vector<scalar> absolute;
    forAll(d, i)
    {
        absolute.push_back(mag(d[i]));
        if (mag(d[i]) > maximum) { maximum = mag(d[i]); maxCell = i; }
    }
    scalar trueL1 = gSum(mag(trueResidual));
    scalar recursiveL1 = performance.finalResidual()*normFactor;
    scalar nonRef = trueL1-mag(trueResidual[reference]);
    scalar kp = 0.01*normFactor/(up*volume);
    scalar epsilon = 0.01/up*mean;
    scalar Rtrue = trueL1/normFactor;
    scalar signedMean = gSum(q)/volume;
    // Native metric computed through the actual OpenFOAM operator.
    tmp<volScalarField> nativeDiv = fvc::div(phi);
    scalar nativeLocal = runTime.deltaTValue()*mag(nativeDiv())().weightedAverage(mesh.V()).value();
    scalar nativeGlobal = runTime.deltaTValue()*nativeDiv().weightedAverage(mesh.V()).value();
    const vector& centre = mesh.C()[maxCell];
    out << std::setprecision(17)
        << runTime.value() << ',' << mesh.nCells() << ',' << normFactor << ','
        << performance.initialResidual() << ',' << performance.finalResidual() << ','
        << performance.nIterations() << ',' << performance.converged() << ','
        << trueL1 << ',' << Rtrue << ',' << recursiveL1 << ',' << mag(trueL1-recursiveL1) << ','
        << nonRef << ',' << trueResidual[reference] << ',' << physicalResidual[reference] << ','
        << q[reference] << ',' << gSum(mag(q-physicalResidual)) << ','
        << gMax(mag(q-physicalResidual)) << ',' << gSum(mag(q)) << ',' << gMax(mag(q)) << ','
        << mean << ',' << maximum << ',' << auditPercentile(absolute, .95) << ','
        << auditPercentile(absolute, .99) << ',' << signedMean << ',' << boundaryNet << ','
        << up << ',' << kp << ',' << epsilon << ',' << 0.01/up*maximum << ','
        << epsilon/(kp*performance.finalResidual()) << ',' << epsilon/(kp*Rtrue) << ','
        << nativeLocal << ',' << nativeGlobal << ',' << reference << ',' << maxCell << ','
        << centre.x() << ',' << centre.y() << ',' << centre.z() << '\n';
    out.flush();
}
