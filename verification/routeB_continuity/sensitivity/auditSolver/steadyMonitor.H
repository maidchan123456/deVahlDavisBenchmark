// Verification-only convergence monitor; no mutation of equation/solution fields.
#include <array>
#include <deque>

class SensitivityMonitor
{
    Foam::vectorField previousU;
    Foam::scalarField previousT;
    std::deque<std::array<double, 13>> history;
    Foam::label candidateIteration;
    std::ofstream out;
public:
    bool steady;
    explicit SensitivityMonitor(const Foam::Time& t)
    : candidateIteration(-1), out((t.path()/"steadyMonitor.csv").c_str()), steady(false)
    {
        out << "iteration,Nu_bar_cavity,Nu_bar_0,Nu_bar_half,Umax,Wmax,Umax_Z,Wmax_X,U_change,T_change,epsilon_phi_mean,epsilon_phi_max,heat_imbalance,Up,window_value_range,window_position_range,window_heat_range,qualified\n";
    }
    bool check(const Foam::Time& time, const Foam::fvMesh& mesh,
        const Foam::volVectorField& U, const Foam::volScalarField& T,
        const Foam::surfaceScalarField& phi, double pressureTolerance)
    {
        using namespace Foam;
        label iteration = label(time.value());
        if (iteration % 20) return false;
        label n = label(std::sqrt(double(mesh.nCells())) + .5);
        const double L=.01, alpha=1e-6/.71;
        double up=gMax(mag(U.primitiveField()));
        if (!(up>0)) return false;
        double cold=T.boundaryField()[mesh.boundaryMesh().findPatchID("coldWall")][0];
        double hot=T.boundaryField()[mesh.boundaryMesh().findPatchID("hotWall")][0];
        std::array<double,13> v{};
        v[0]=1.; double coldNu=0.;
        for (label i=0;i<n*n;++i)
        {
            v[0]+=(L/alpha)*U[i].x()*(T[i]-cold)/(n*n);
            if (i%n==0) v[1]+=2*n*(hot-T[i])/n;
            if (i%n==n-1) coldNu+=2*n*(T[i]-cold)/n;
        }
        const labelUList& owner=mesh.owner();
        const labelUList& neighbour=mesh.neighbour();
        scalarField q(n*n,0.);
        forAll(owner,f)
        {
            q[owner[f]]+=phi[f]; q[neighbour[f]]-=phi[f];
            if (neighbour[f]-owner[f]==1 && owner[f]%n==n/2-1)
                v[2]+=phi[f]*(.5*(T[owner[f]]+T[neighbour[f]])-cold)/(alpha*.001)
                    -(T[neighbour[f]]-T[owner[f]]);
        }
        forAll(mesh.boundary(),p)
        {
            if (mesh.boundary()[p].type()=="empty") continue;
            const labelUList& cells=mesh.boundary()[p].faceCells();
            forAll(cells,f) q[cells[f]]+=phi.boundaryField()[p][f];
        }
        // Exactly the production piecewise-linear 4097-point centreline rule.
        v[3]=v[4]=-GREAT;
        for (label k=0;k<=4096;++k)
        {
            double x=double(k)/4096.;
            double cell=x*n-.5;
            label a=label(std::floor(cell)), b=a+1;
            double w=cell-a;
            if (a<0) { a=-1;b=0;w=2*n*x; }
            if (b>=n) { a=n-1;b=n;w=2*n*(x-(1.-.5/n)); }
            double ua= a<0 ? 0. : .5*(U[a*n+n/2-1].x()+U[a*n+n/2].x());
            double ub= b>=n ? 0. : .5*(U[b*n+n/2-1].x()+U[b*n+n/2].x());
            double va= a<0 ? 0. : .5*(U[(n/2-1)*n+a].y()+U[(n/2)*n+a].y());
            double vb= b>=n ? 0. : .5*(U[(n/2-1)*n+b].y()+U[(n/2)*n+b].y());
            double u=((1-w)*ua+w*ub)*L/alpha, z=((1-w)*va+w*vb)*L/alpha;
            if(u>v[3]) {v[3]=u;v[5]=x;}
            if(z>v[4]) {v[4]=z;v[6]=x;}
        }
        v[7]=previousU.size() ? gMax(mag(U.primitiveField()-previousU))/up : GREAT;
        v[8]=previousT.size() ? gMax(mag(T.primitiveField()-previousT)) : GREAT;
        previousU=U.primitiveField();previousT=T.primitiveField();
        v[9]=L/up*gSum(mag(q))/gSum(mesh.V());
        v[10]=L/up*gMax(mag(q/mesh.V()));
        v[11]=mag(v[1]-coldNu)/(.5*(mag(v[1])+mag(coldNu)));
        v[12]=up;
        history.push_back(v); if(history.size()>11) history.pop_front();
        double rv=0.,rp=0.,rh=0.; bool qualified=history.size()==11 && iteration>=400;
        for(label j=0;j<12;++j)
        {
            double lo=GREAT, hi=-GREAT;
            for(const auto& row:history) {lo=std::min(lo,row[j]);hi=std::max(hi,row[j]);}
            double range=hi-lo;
            if(j<5) rv=std::max(rv,range/std::max(mag(v[j]),1.));
            if(j==5 || j==6) rp=std::max(rp,range);
            if(j==7 || j==8) qualified=qualified && hi<=1e-8;
            // Capacity-scaled continuity stability, not an acceptance quota.
            if(j==9) qualified=qualified && range<=2*pressureTolerance*100;
            if(j==10) qualified=qualified && range<=2*pressureTolerance*100*n*n;
            if(j==11) rh=range;
        }
        qualified=qualified && rv<=1e-8 && rp<=1./4096 && rh<=1e-8;
        if(!qualified) candidateIteration=-1;
        else if(candidateIteration<0) candidateIteration=iteration;
        steady=qualified && iteration-candidateIteration>=200;
        out<<std::setprecision(17)<<iteration;
        for(const auto& value:v) out<<','<<value;
        out<<','<<rv<<','<<rp<<','<<rh<<','<<qualified<<'\n';out.flush();
        return steady;
    }
};
