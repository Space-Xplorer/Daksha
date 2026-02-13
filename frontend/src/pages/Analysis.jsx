import React, { useState, useEffect } from 'react';
import { useShield } from '../context/ShieldContext';
import { Network, Loader2 } from 'lucide-react';
import GlassCard from '../components/GlassCard';
import AgentStatus from '../components/AgentStatus';

const Analysis = () => {
  const { setView } = useShield();
  const [step, setStep] = useState(0);

  const steps = [
    "Identity Agent: Anchoring Aadhaar Hash...",
    "Extraction Agent: Parsing PDF Features...",
    "EBM Engine: Calculating Interactions...",
    "Advisor Agent: Generating Reasoning Trace..."
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setStep(prev => {
        if (prev === steps.length - 1) {
          clearInterval(timer);
          setTimeout(() => setView('result'), 1000);
          return prev;
        }
        return prev + 1;
      });
    }, 2000);
    return () => clearInterval(timer);
  }, [setView, steps.length]);

  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center px-6 text-center">
      <div className="relative w-32 h-32 mb-12">
        <div className="absolute inset-0 border-8 border-[#4B0082]/5 rounded-full" />
        <div className="absolute inset-0 border-8 border-[#F4C2C2] border-t-transparent rounded-full animate-spin" />
        <div className="absolute inset-0 flex items-center justify-center text-[#4B0082]"><Network size={40} /></div>
      </div>
      <h2 className="text-2xl font-black text-[#4B0082] italic uppercase tracking-[0.2em] mb-4">Agentic Orchestration</h2>
      <div className="bg-white p-6 rounded-[2rem] shadow-sm border border-slate-100 min-w-[320px]">
        <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Active Task</p>
        <p className="text-sm font-black text-[#4B0082] animate-pulse">{steps[step]}</p>
      </div>
      // Inside Analysis.jsx
<GlassCard className="p-12 max-w-md mx-auto">
  <h4 className="text-center font-black text-[#4B0082] mb-8 uppercase italic tracking-widest">
    Orchestration Pulse
  </h4>
  <div className="space-y-4">
    <AgentStatus name="Identity Agent" status="complete" />
    <AgentStatus name="Extraction Agent" status="loading" />
    <AgentStatus name="EBM Logic Engine" status="waiting" />
  </div>
</GlassCard>
    </div>
  );
};

export default Analysis;