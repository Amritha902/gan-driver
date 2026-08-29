"""
emi_check.py -- does pull-up strength matter for quantities the cost ignores?

The paper claims drive-strength scheduling is worth 0.00%. That claim is only
honest if drive strength also fails to move the things the cost function
leaves out - EMI and dV/dt - which is exactly what active gate drivers are
usually scheduled for.

Note the window: pull-up governs TURN-ON, so the oscillation energy must be
measured there. The project's standard E_osc metric windows the turn-off
event and cannot detect a pull-up effect at all.
"""
import sys, numpy as np
sys.path.insert(0, __file__.rsplit('/',1)[0])
import gansim
from multiprocessing import Pool

def job(npu):
    d,p = gansim.run_raw(cir="ideal", NPU_LS=npu, NPD_LS=8, NPD_HS=8,
                         CLKEN=1, VNEG=0, DT="15n")
    t=d[:,0]; sw=d[:,1]; vds=d[:,3]
    T4=2e-6+15e-9
    w=(t>=T4)&(t<=T4+300e-9)
    y=vds[w]-vds[w].mean(); ts=t[w]
    yu=np.interp(np.linspace(ts[0],ts[-1],4096),ts,y)
    fs=4095.0/(ts[-1]-ts[0]); Y=np.abs(np.fft.rfft(yu))**2
    fr=np.fft.rfftfreq(4096,1.0/fs)
    eosc=float(Y[(fr>=30e6)&(fr<=500e6)].sum()/len(yu)**2)
    k=(t>=T4)&(t<=T4+40e-9)
    return npu, eosc, np.abs(np.gradient(sw[k],t[k])).max()/1e9

if __name__ == "__main__":
    print("  N_PU   turn-on E_osc   peak dV/dt (V/ns)")
    with Pool(4) as p: res=sorted(p.map(job,[1,2,3,4,6,8]))
    for n,e,d in res: print("   %d        %8.1f        %8.1f"%(n,e,d))
    e=[r[1] for r in res]; dv=[r[2] for r in res]
    print("\n  E_osc spans %.0f%%, dV/dt spans %.0f%% across the pull-up range"
          % (100*(max(e)-min(e))/min(e), 100*(max(dv)-min(dv))/min(dv)))
    print("  Both are absent from the cost function. The 0.00%% scheduling")
    print("  value of pull-up is therefore scoped to a loss-and-overshoot")
    print("  objective and must be stated that way.")
