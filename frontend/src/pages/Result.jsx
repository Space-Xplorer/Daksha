import React from 'react';
import { useShield } from '../context/ShieldContext';
import { ShieldCheck, BrainCircuit, Sparkles, Activity } from 'lucide-react';

const Result = () => {
  const { setView, service, workflowResult, workflowStatus } = useShield();
  const isInsurance = service === 'insurance';
  const rejected = workflowStatus?.rejected || false;
  const rejectionReason = workflowStatus?.rejection_reason;
  const loanPrediction = workflowResult?.loan?.prediction;
  const insurancePrediction = workflowResult?.insurance?.prediction;
  const explanation = isInsurance
    ? workflowResult?.insurance?.explanation
    : workflowResult?.loan?.explanation;
  const description = isInsurance
    ? workflowResult?.insurance?.description
    : workflowResult?.loan?.description;

  const decisionLabel = rejected
    ? 'Rejected'
    : (isInsurance ? 'Approved' : (loanPrediction?.approved ? 'Approved' : 'Review'));
  const amountLabel = isInsurance ? 'Estimated Premium' : 'Approval Probability';
  const amountValue = isInsurance
    ? insurancePrediction?.premium
    : loanPrediction?.probability;

  return (
    <div className="max-w-4xl mx-auto py-10 px-6 animate-in zoom-in-95">
      <div className="glass-card rounded-[4rem] p-16 border-b-24 border-[#F4C2C2]">
        <div className="flex justify-center mb-10">
          <div className="bg-[#4B0082] text-[#F4C2C2] px-8 py-3 rounded-full text-xs font-black uppercase tracking-[0.3em] flex items-center gap-3 shadow-lg">
            <ShieldCheck size={20} /> Daksha Verified
          </div>
        </div>

        <div className="text-center mb-12">
          <h2 className="text-9xl font-black text-[#4B0082] tracking-tighter italic mb-2 uppercase">{decisionLabel}</h2>
          <p className="text-xs font-black uppercase tracking-[0.6em] text-slate-400">Total Shield Level: Optimal</p>
        </div>

        <div className="grid lg:grid-cols-2 gap-10">
          <div className="bg-white/50 p-10 rounded-[3rem] border border-white">
            <h5 className="font-black text-[#4B0082] flex items-center gap-3 mb-8 italic"><BrainCircuit size={20} /> EBM Reasoning Trace</h5>
            <div className="space-y-6">
              {[
                {l: "Identity Integrity", v: "100%", c: "#4B0082"},
                {l: "Income Interaction", v: "88%", c: "#F4C2C2"},
                {l: "Risk Buffer", v: "15%", c: "#800080"}
              ].map((it, i) => (
                <div key={i}>
                  <div className="flex justify-between text-[9px] font-black uppercase text-slate-400 mb-2"><span>{it.l}</span><span>{it.v}</span></div>
                  <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full transition-all duration-1000" style={{width: it.v, backgroundColor: it.c}} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-6">
            <div className="p-8 bg-white/80 rounded-[3rem] border border-white">
              <div className="flex items-center gap-3 mb-4"><Activity className="text-[#4B0082]" /><h6 className="font-black text-[#4B0082] italic">Daksha Advisor</h6></div>
              <p className="text-sm text-slate-500 font-medium leading-relaxed italic">
                {explanation || 'Decision explanation will appear here once the workflow completes.'}
              </p>
            </div>
            <div className="p-8 bg-white/80 rounded-[3rem] border border-white">
              <div className="flex items-center gap-3 mb-4"><Sparkles className="text-[#4B0082]" /><h6 className="font-black text-[#4B0082] italic">Decision Description</h6></div>
              <p className="text-sm text-slate-500 font-medium leading-relaxed italic">
                {description || 'Decision description will appear here once the workflow completes.'}
              </p>
            </div>
            <div className="p-8 bg-[#4B0082] text-white rounded-[3rem] shadow-xl">
              <p className="text-[10px] font-black uppercase tracking-widest opacity-60">
                 {amountLabel}
              </p>
               <p className="text-5xl font-black italic">
                 {amountValue
                   ? (isInsurance ? `₹ ${Number(amountValue).toFixed(0)}` : `${Math.round(Number(amountValue) * 100)}%`)
                   : 'Pending'}
               </p>
            </div>
          </div>
        </div>

        {rejected && rejectionReason ? (
          <div className="mt-10 bg-red-50 border border-red-100 text-red-600 rounded-4xl p-6 text-xs font-bold uppercase tracking-widest text-center">
            {rejectionReason}
          </div>
        ) : null}

        <button onClick={() => setView('landing')} className="w-full mt-12 py-8 bg-[#FAF9F6] border-2 border-[#4B0082]/10 text-[#4B0082] rounded-[2.5rem] font-black uppercase tracking-widest text-xs hover:bg-white transition-all">Return to Lobby</button>
      </div>
    </div>
  );
};

export default Result;