#ifndef routeA_NativeMatrixObserver_H
#define routeA_NativeMatrixObserver_H

// Observation adapter only. No solve(), relax(), constrain(), field assignment,
// timestep change, or equation replacement is performed by this header.
#include "fvMatrices.H"
#include "volFields.H"
#include "surfaceFields.H"
#include <cmath>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace routeADiagnostic
{
struct StageId
{
    int timeIndex, outer, pressure, energySolve;
    double time, dt, dtPrevious;
    std::string stage;
    std::vector<std::string> oldTimeIds;
    void validate() const
    {
        if (timeIndex < 0 || outer < 0 || pressure < 0 || energySolve < 0
         || stage.empty() || oldTimeIds.empty() || !std::isfinite(time)
         || !std::isfinite(dt) || dt <= 0 || !std::isfinite(dtPrevious)
         || dtPrevious <= 0)
            throw std::runtime_error("STAGE_IDENTITY_FAILURE");
    }
    std::string key() const
    {
        return std::to_string(timeIndex) + ":" + std::to_string(outer)
             + ":" + std::to_string(pressure) + ":"
             + std::to_string(energySolve) + ":" + stage;
    }
};

struct IntegratedAction
{
    double signedSum, absoluteSum, localL1, localLinf;
    double summationRoundoffBound;
    Foam::dimensionSet dimensions;
};

// Integrated matrix cells are already in kg/s or W. Divide by V for local
// densities only. Accumulate in extended precision; never multiply by V again.
inline IntegratedAction summarizeIntegrated
(
    const Foam::scalarField& cells,
    const Foam::scalarField& volumes,
    const Foam::dimensionSet& dimensions
)
{
    if (cells.size() != volumes.size() || !cells.size())
        throw std::runtime_error("EVALUATOR_SIZE_FAILURE");
    long double sum=0, correction=0, absolute=0, volume=0;
    double linf=0;
    for (Foam::label i=0; i<cells.size(); ++i)
    {
        if (!std::isfinite(cells[i]) || !std::isfinite(volumes[i])
         || volumes[i]<=0) throw std::runtime_error("EVALUATOR_NONFINITE_OR_VOLUME");
        const long double x=cells[i], next=sum+x;
        correction += std::fabs(sum)>=std::fabs(x) ? (sum-next)+x : (x-next)+sum;
        sum=next; absolute += std::fabs(x); volume += volumes[i];
        linf=std::max(linf, std::fabs(cells[i]/volumes[i]));
    }
    const long double eps=std::numeric_limits<double>::epsilon();
    const long double gamma=(cells.size()+2)*eps/(1-(cells.size()+2)*eps);
    return {double(sum+correction), double(absolute), double(absolute/volume),
            linf, double(gamma*absolute), dimensions};
}

class ScalarMatrixSnapshot
{
    // Deep coefficient/source/boundary copy; psi reference deliberately stays
    // attached to the original solved field. Evaluate before its BC epoch moves.
    Foam::fvScalarMatrix matrix_;
    StageId id_;
    Foam::dimensionSet expected_;
public:
    ScalarMatrixSnapshot(const Foam::fvScalarMatrix& matrix,
                         const StageId& id, const Foam::dimensionSet& expected)
      : matrix_(matrix), id_(id), expected_(expected)
    {
        id_.validate();
        if (matrix_.dimensions()!=expected_)
            throw std::runtime_error("MATRIX_UNITS_FAILURE");
        for (const auto& patch : matrix_.psi().boundaryField())
            if (patch.coupled()) throw std::runtime_error("SERIAL_UNCOUPLED_ONLY");
    }
    Foam::scalarField lhsMinusRhs() const
    {
        // Native lduMatrix::residual requires an allocated upper/lower array,
        // even for a diagonal matrix. Density/storage matrices can lack both.
        // Normalize ONLY a private scratch copy to zero off-diagonals, with
        // identical mathematical action. Never allocate/change the live matrix.
        if (matrix_.diagonal())
        {
            Foam::fvScalarMatrix scratch(matrix_);
            scratch.upper()=0;
            scratch.lower()=0;
            return -scratch.residual()();
        }
        return -matrix_.residual()(); // native b-Apsi -> our Apsi-b
    }
    IntegratedAction evaluate() const
    {
        return summarizeIntegrated(lhsMinusRhs(),
                 matrix_.psi().mesh().V().primitiveField(), expected_);
    }
    double matrixActionRoundoffBound()
    {
        // Bound matvec/source/boundary arithmetic on the stored FLOATING
        // matrix. This does not bound error in assembling its coefficients.
        const auto& psi=matrix_.psi().primitiveField();
        std::vector<long double> scales(psi.size());
        std::vector<unsigned> counts(psi.size(),3);
        for(Foam::label i=0;i<psi.size();++i)
            scales[i]=std::fabs((long double)matrix_.diag()[i]*psi[i])
                      +std::fabs((long double)matrix_.source()[i]);
        if (!matrix_.diagonal())
        {
            const auto& lo=matrix_.lduAddr().lowerAddr();
            const auto& up=matrix_.lduAddr().upperAddr();
            for(Foam::label f=0;f<lo.size();++f)
            {
                scales[lo[f]]+=std::fabs((long double)matrix_.upper()[f]*psi[up[f]]);
                scales[up[f]]+=std::fabs((long double)matrix_.lower()[f]*psi[lo[f]]);
                counts[lo[f]]+=3;counts[up[f]]+=3;
            }
        }
        for(Foam::label patch=0;patch<matrix_.internalCoeffs().size();++patch)
        {
            const auto& cells=matrix_.psi().mesh().boundary()[patch].faceCells();
            for(Foam::label f=0;f<cells.size();++f)
            {
                scales[cells[f]]+=std::fabs((long double)matrix_.internalCoeffs()[patch][f]*psi[cells[f]])
                                 +std::fabs((long double)matrix_.boundaryCoeffs()[patch][f]);
                counts[cells[f]]+=6;
            }
        }
        const long double eps=std::numeric_limits<double>::epsilon();
        long double bound=0;
        for(Foam::label i=0;i<psi.size();++i)
            bound+=counts[i]*eps/(1-counts[i]*eps)*scales[i];
        return double(bound)+evaluate().summationRoundoffBound;
    }
    const StageId& id() const { return id_; }
    const Foam::fvScalarMatrix& coefficients() const { return matrix_; }
};

inline Foam::scalarField integrateExplicit
(
    const Foam::volScalarField& field,
    const Foam::dimensionSet& integratedDimensions
)
{
    if (field.dimensions()*Foam::dimVolume != integratedDimensions)
        throw std::runtime_error("EXPLICIT_UNITS_FAILURE");
    return field.primitiveField()*field.mesh().V().primitiveField();
}

inline double outwardBoundarySum(const Foam::surfaceScalarField& phi)
{
    if (phi.dimensions()!=Foam::dimMass/Foam::dimTime)
        throw std::runtime_error("NATIVE_PHI_UNITS_FAILURE");
    long double total=0;
    for (const auto& patch : phi.boundaryField())
        for (const auto& value : patch)
        {
            if (!std::isfinite(value)) throw std::runtime_error("NATIVE_PHI_NONFINITE");
            total+=value;
        }
    return double(total);
}
}
#endif
