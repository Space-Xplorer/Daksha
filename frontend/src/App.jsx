import React, { useState, useEffect } from 'react';
import { 
  Shield, UserCheck, FileText, Activity, Landmark, Upload, 
  CheckCircle, AlertCircle, ChevronRight, Fingerprint, 
  Search, Info, ArrowLeft, Clock, Zap, ArrowRight, Eye, ShieldCheck, 
  TrendingUp, Building2, BarChart3, Rocket, Star, Trophy, Target,
  ZapOff, ShieldAlert, PieChart, Layers, Network
} from 'lucide-react';

const App = () => {
  const [view, setView] = useState('landing'); 
  const [step, setStep] = useState(1);
  const [shieldType, setShieldType] = useState(null);
  const [aadhaar, setAadhaar] = useState("");
  const [isVerifying, setIsVerifying] = useState(false);
  const [formData, setFormData] = useState({ income: "", debt: "", bmi: "", smoker: "No" });

  const startPlatform = () => { setView('platform'); setStep(1); window.scrollTo(0,0); };
  const viewPartner = () => { setView('partner'); window.scrollTo(0,0); };
  const goHome = () => { setView('landing'); setStep(1); setShieldType(null); window.scrollTo(0,0); };

  // --- VIEW 1: LANDING PAGE (Enhanced Information) ---
  if (view === 'landing') {
    return (
      <div className="min-h-screen bg-[#F8FAFF] text-slate-800 font-sans selection:bg-blue-200">
        <nav className="fixed top-0 w-full z-50 bg-white/90 backdrop-blur-md border-b border-blue-100 px-8 h-20 flex items-center justify-between">
          <div className="flex items-center gap-2 cursor-pointer" onClick={goHome}>
            <div className="p-2 bg-blue-500 rounded-2xl rotate-3 shadow-lg shadow-blue-200">
              <Shield className="text-white w-6 h-6" fill="currentColor" />
            </div>
            <span className="text-2xl font-black tracking-tight text-blue-600 italic">KAVACH</span>
          </div>
          <div className="flex items-center gap-8 font-black text-[10px] uppercase tracking-widest">
            <button onClick={() => document.getElementById('how-it-works').scrollIntoView({behavior:'smooth'})} className="text-slate-400 hover:text-blue-500">How It Works</button>
            <button onClick={viewPartner} className="text-slate-400 hover:text-blue-500">For Partners</button>
            <button onClick={startPlatform} className="bg-blue-500 hover:bg-blue-600 text-white px-8 py-3 rounded-full shadow-xl shadow-blue-200 transition-all">Start Quest</button>
          </div>
        </nav>

        {/* Hero */}
        <section className="pt-48 pb-20 px-8 text-center relative overflow-hidden">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[500px] bg-blue-400/5 rounded-full blur-[120px] -z-10" />
          <div className="max-w-4xl mx-auto">
            <div className="inline-flex items-center gap-2 bg-yellow-100 text-yellow-700 px-4 py-2 rounded-full mb-8 font-bold text-[10px] uppercase tracking-widest shadow-sm">
              <Zap size={14} fill="currentColor" /> The World's First Glass-Box Underwriting Shield
            </div>
            <h1 className="text-7xl md:text-9xl font-black text-slate-900 mb-8 leading-[0.85] tracking-tighter">
              Fair Risk. <br />
              <span className="text-blue-500 italic">Zero Secrets.</span>
            </h1>
            <p className="text-slate-500 text-xl md:text-2xl mb-12 max-w-2xl mx-auto font-medium leading-relaxed">
              We've replaced the "Black Box" of banking with <strong>Agentic Intelligence</strong>. Get verified, see your math, and unlock your true potential.
            </p>
            <div className="flex justify-center gap-4">
               <button onClick={startPlatform} className="bg-blue-500 text-white px-12 py-6 rounded-[2.5rem] font-black text-xs uppercase tracking-widest flex items-center gap-4 shadow-2xl shadow-blue-300 hover:-translate-y-1 transition-all">
                  Initialize My Shield <Rocket size={20} />
               </button>
            </div>
          </div>
        </section>

        {/* The Problem Section */}
        <section id="how-it-works" className="py-24 px-8 bg-white rounded-[4rem] mx-4 shadow-xl border border-blue-50">
           <div className="max-w-6xl mx-auto grid md:grid-cols-2 gap-20 items-center">
              <div className="space-y-8">
                 <h2 className="text-4xl font-black text-slate-900 italic tracking-tighter leading-tight">Why Kavach? <br /> Because "Computer Says No" isn't an answer.</h2>
                 <p className="text-slate-500 text-lg leading-relaxed font-medium">
                    Traditional insurance and loans are a black hole. You give your data, and a mysterious algorithm rejects you without a reason.
                 </p>
                 <div className="grid grid-cols-1 gap-6">
                    <div className="flex items-start gap-4 p-6 bg-rose-50 rounded-3xl border border-rose-100">
                       <ZapOff className="text-rose-500 mt-1" />
                       <div>
                          <h4 className="font-black text-rose-900">The Black Box Problem</h4>
                          <p className="text-xs text-rose-700 font-medium">Legacy AI uses deep layers that even bankers can't explain. We use <strong>EBMs</strong> for 100% clarity.</p>
                       </div>
                    </div>
                    <div className="flex items-start gap-4 p-6 bg-emerald-50 rounded-3xl border border-emerald-100">
                       <ShieldCheck className="text-emerald-500 mt-1" />
                       <div>
                          <h4 className="font-black text-emerald-900">Verified Identity</h4>
                          <p className="text-xs text-emerald-700 font-medium">Our <strong>Identity Agents</strong> pull directly from Aadhaar and CIBIL. No manual entry, no fraud, no errors.</p>
                       </div>
                    </div>
                 </div>
              </div>
              <div className="relative">
                 <div className="bg-slate-50 border-8 border-white rounded-[3.5rem] p-10 shadow-2xl overflow-hidden">
                    <div className="flex items-center justify-between mb-8">
                       <span className="font-black text-[10px] tracking-widest uppercase text-slate-400">Live Agent Dashboard</span>
                       <div className="h-2 w-2 bg-emerald-500 rounded-full animate-pulse" />
                    </div>
                    <div className="space-y-4">
                       {[
                         {l: "OCR Agent: Extracting CIBIL...", p: "100%"},
                         {l: "Compliance Agent: Verifying DTI...", p: "100%"},
                         {l: "EBM Engine: Calculating Interactions...", p: "85%"},
                         {l: "Transparency Agent: Framing Logic...", p: "10%"}
                       ].map((step, i) => (
                         <div key={i} className="bg-white p-4 rounded-2xl flex items-center justify-between shadow-sm border border-slate-100">
                            <span className="text-[10px] font-black">{step.l}</span>
                            <div className="w-12 h-1 bg-slate-100 rounded-full"><div className="bg-blue-500 h-full rounded-full" style={{width: step.p}} /></div>
                         </div>
                       ))}
                    </div>
                 </div>
              </div>
           </div>
        </section>
      </div>
    );
  }

  // --- VIEW 2: B2B PARTNER PAGE (Detailed) ---
  if (view === 'partner') {
    return (
      <div className="min-h-screen bg-white text-slate-800 font-sans">
        <nav className="h-20 border-b border-slate-100 px-8 flex items-center justify-between sticky top-0 bg-white/90 backdrop-blur-md z-50">
          <div onClick={goHome} className="flex items-center gap-2 cursor-pointer font-black text-blue-600 italic tracking-tighter text-xl">KAVACH B2B</div>
          <button onClick={startPlatform} className="bg-slate-900 text-white px-6 py-2 rounded-full font-black text-[10px] uppercase tracking-widest">Interactive Demo</button>
        </nav>

        <section className="max-w-7xl mx-auto py-24 px-8 grid lg:grid-cols-12 gap-20">
           <div className="lg:col-span-5 space-y-8">
              <span className="text-[10px] font-black text-blue-500 uppercase tracking-[0.3em]">For Financial Institutions</span>
              <h2 className="text-5xl font-black text-slate-900 leading-tight tracking-tighter">Underwriting, <br /> Re-imagined for Scale.</h2>
              <p className="text-slate-500 text-lg leading-relaxed font-medium">
                Our Agentic Ecosystem allows insurance providers to automate 90% of manual auditing while staying 100% compliant with "Right to Explanation" laws.
              </p>
              
              <div className="grid grid-cols-1 gap-4">
                 {[
                   {i: <Network />, t: "API-First Orchestration", d: "Integrate our Agents into your existing CRM in minutes."},
                   {i: <Layers />, t: "Multi-Source Verification", d: "Automatically cross-verify Aadhaar, GST, and Health data."},
                   {i: <PieChart />, t: "Bias Detection", d: "EBMs identify and alert you if the model is showing unfair bias."}
                 ].map((feat, idx) => (
                   <div key={idx} className="flex gap-4 p-6 bg-slate-50 rounded-3xl border border-slate-100 transition-all hover:bg-blue-50">
                      <div className="p-3 bg-white rounded-xl text-blue-500 shadow-sm">{feat.i}</div>
                      <div>
                         <h4 className="font-black text-sm">{feat.t}</h4>
                         <p className="text-xs text-slate-500 mt-1">{feat.d}</p>
                      </div>
                   </div>
                 ))}
              </div>
           </div>

           <div className="lg:col-span-7 bg-[#0F172A] rounded-[4rem] p-12 text-white shadow-3xl overflow-hidden relative">
              <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/20 rounded-full blur-[100px]" />
              <h3 className="text-xl font-black mb-12 flex items-center gap-3 italic"><BarChart3 className="text-blue-400" /> System Metrics (2026)</h3>
              
              <div className="grid grid-cols-2 gap-8 mb-12">
                 <div className="bg-white/5 p-8 rounded-3xl border border-white/10">
                    <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Manual Work Saved</p>
                    <p className="text-4xl font-black text-white italic tracking-tighter">84.2%</p>
                 </div>
                 <div className="bg-white/5 p-8 rounded-3xl border border-white/10">
                    <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Customer Trust Score</p>
                    <p className="text-4xl font-black text-white italic tracking-tighter">+2x</p>
                 </div>
              </div>

              <div className="space-y-8">
                 <h4 className="text-[10px] font-black uppercase tracking-widest text-slate-500">Agentic Throughput</h4>
                 <div className="space-y-4">
                    <div className="flex justify-between text-xs font-bold uppercase"><span>OCR Accuracy</span><span>99.8%</span></div>
                    <div className="h-2 w-full bg-white/5 rounded-full"><div className="h-full bg-blue-500 rounded-full" style={{width: '99%'}} /></div>
                    <div className="flex justify-between text-xs font-bold uppercase mt-4"><span>Compliance Sync</span><span>Real-time</span></div>
                    <div className="h-2 w-full bg-white/5 rounded-full"><div className="h-full bg-emerald-500 rounded-full" style={{width: '100%'}} /></div>
                 </div>
              </div>
           </div>
        </section>
      </div>
    );
  }

  // --- VIEW 3: THE GAME PLATFORM (Improved UX) ---
  return (
    <div className="min-h-screen bg-[#F8F9FF] text-slate-800 font-sans">
      <nav className="h-20 bg-white border-b border-slate-100 px-8 flex items-center justify-between sticky top-0 z-50">
        <div onClick={goHome} className="flex items-center gap-2 cursor-pointer">
          <div className="p-1.5 bg-blue-500 rounded-xl shadow-lg shadow-blue-100"><Shield className="text-white w-4 h-4" /></div>
          <span className="font-black text-blue-600 italic tracking-tighter">KAVACH PLAY</span>
        </div>
        <div className="hidden md:flex gap-2">
           {[1, 2, 3, 4, 5, 6].map(i => (
             <div key={i} className={`h-2 w-10 rounded-full transition-all duration-500 ${step >= i ? 'bg-blue-500' : 'bg-slate-100'}`} />
           ))}
        </div>
      </nav>

      <main className="max-w-3xl mx-auto py-12 px-6">
        
        {/* Step 1: KYC (Identity Key) */}
        {step === 1 && (
          <div className="bg-white rounded-[4rem] p-16 shadow-2xl text-center animate-in fade-in slide-in-from-bottom-8 border border-blue-50">
            <div className="w-24 h-24 bg-blue-50 rounded-[2.5rem] flex items-center justify-center mx-auto mb-8 border border-blue-100 shadow-inner">
               <Fingerprint className="text-blue-500" size={48} />
            </div>
            <h2 className="text-4xl font-black mb-4 tracking-tighter italic">Identity Quest</h2>
            <p className="text-slate-400 font-medium mb-12">Login with your Aadhaar ID to summon your verified profile.</p>
            <input 
              type="text" 
              placeholder="0000 0000 0000" 
              maxLength="12"
              className="w-full bg-slate-50 border-4 border-slate-100 p-8 rounded-[2.5rem] text-center text-4xl font-black tracking-[0.2em] focus:border-blue-400 focus:bg-white outline-none transition-all shadow-inner"
              onChange={(e) => setAadhaar(e.target.value)}
            />
            <button 
              onClick={() => { setIsVerifying(true); setTimeout(() => { setIsVerifying(false); setStep(2); }, 1500); }}
              disabled={aadhaar.length < 12}
              className="w-full mt-10 py-8 bg-blue-500 text-white font-black text-xs uppercase tracking-widest rounded-[2.5rem] shadow-2xl shadow-blue-200 hover:scale-[1.02] transition-all disabled:opacity-20"
            >
              {isVerifying ? "CONNECTING TO IDENTITY AGENT..." : "UNLOCK SHIELD"}
            </button>
          </div>
        )}

        {/* Step 2: Product Pick */}
        {step === 2 && (
          <div className="space-y-8 animate-in fade-in zoom-in-95">
             <div className="text-center">
                <h2 className="text-4xl font-black mb-2 italic tracking-tighter">Hi, Spoorthy!</h2>
                <p className="text-slate-400 font-bold uppercase tracking-widest text-[10px]">What is your mission today?</p>
             </div>
             <div className="grid md:grid-cols-2 gap-8">
                <button onClick={() => { setShieldType('loan'); setStep(3); }} className="group p-12 bg-white border-4 border-transparent hover:border-blue-400 rounded-[4rem] shadow-2xl transition-all text-left">
                   <div className="p-6 bg-blue-50 text-blue-500 rounded-3xl w-fit mb-8 group-hover:scale-110 transition shadow-sm"><Landmark size={40} /></div>
                   <h4 className="text-2xl font-black">LOAN SHIELD</h4>
                   <p className="text-sm text-slate-400 mt-4 font-medium leading-relaxed">Verify your credit and get an instant approval roadmap.</p>
                </button>
                <button onClick={() => { setShieldType('health'); setStep(3); }} className="group p-12 bg-white border-4 border-transparent hover:border-emerald-400 rounded-[4rem] shadow-2xl transition-all text-left">
                   <div className="p-6 bg-emerald-50 text-emerald-500 rounded-3xl w-fit mb-8 group-hover:scale-110 transition shadow-sm"><Activity size={40} /></div>
                   <h4 className="text-2xl font-black">HEALTH SHIELD</h4>
                   <p className="text-sm text-slate-400 mt-4 font-medium leading-relaxed">Assess your health biomarkers and unlock custom premiums.</p>
                </button>
             </div>
          </div>
        )}

        {/* Step 3: Interactive Form */}
        {step === 3 && (
          <div className="bg-white rounded-[4rem] p-12 shadow-2xl animate-in fade-in slide-in-from-right-8">
            <h2 className="text-3xl font-black mb-10 italic tracking-tighter text-center">Base Configuration</h2>
            <div className="space-y-8">
               {shieldType === 'loan' ? (
                 <>
                   <div className="space-y-4">
                      <label className="text-[10px] font-black uppercase text-slate-400 tracking-widest">Annual Income (INR)</label>
                      <input type="number" placeholder="e.g. 15,00,000" className="w-full bg-slate-50 border-2 border-slate-100 p-6 rounded-3xl focus:border-blue-300 outline-none font-bold" />
                   </div>
                   <div className="space-y-4">
                      <label className="text-[10px] font-black uppercase text-slate-400 tracking-widest">Requested Amount</label>
                      <input type="number" placeholder="e.g. 50,00,000" className="w-full bg-slate-50 border-2 border-slate-100 p-6 rounded-3xl focus:border-blue-300 outline-none font-bold" />
                   </div>
                 </>
               ) : (
                 <>
                   <div className="space-y-4">
                      <label className="text-[10px] font-black uppercase text-slate-400 tracking-widest">Height (CM)</label>
                      <input type="number" placeholder="e.g. 175" className="w-full bg-slate-50 border-2 border-slate-100 p-6 rounded-3xl focus:border-emerald-300 outline-none font-bold" />
                   </div>
                   <div className="space-y-4">
                      <label className="text-[10px] font-black uppercase text-slate-400 tracking-widest">Weight (KG)</label>
                      <input type="number" placeholder="e.g. 70" className="w-full bg-slate-50 border-2 border-slate-100 p-6 rounded-3xl focus:border-emerald-300 outline-none font-bold" />
                   </div>
                 </>
               )}
               <button onClick={() => setStep(4)} className={`w-full py-6 text-white font-black rounded-3xl shadow-xl transition-all ${shieldType === 'loan' ? 'bg-blue-500 shadow-blue-200' : 'bg-emerald-500 shadow-emerald-200'}`}>NEXT STAGE: DOCUMENT SCAN</button>
            </div>
          </div>
        )}

        {/* Step 4: Doc Upload */}
        {step === 4 && (
          <div className="bg-white rounded-[4rem] p-16 shadow-2xl text-center animate-in fade-in">
             <div className="w-24 h-24 bg-slate-50 rounded-[2.5rem] flex items-center justify-center mx-auto mb-8 border border-slate-100 shadow-inner">
                <Upload className="text-slate-300" size={40} />
             </div>
             <h2 className="text-3xl font-black mb-4 italic tracking-tighter uppercase">{shieldType === 'loan' ? "Bank Statements" : "Health Reports"}</h2>
             <p className="text-slate-400 font-medium mb-12 italic text-sm">Upload your verified PDF. Our OCR Agent will auto-extract the features.</p>
             <div className="border-4 border-dashed border-slate-100 rounded-[3rem] p-20 hover:border-blue-300 transition-all cursor-pointer bg-slate-50/50">
                <p className="text-xs font-black uppercase text-slate-400 tracking-widest">Drop PDF Here</p>
             </div>
             <button onClick={() => setStep(5)} className={`w-full mt-10 py-6 text-white font-black rounded-3xl ${shieldType === 'loan' ? 'bg-blue-500 shadow-blue-200' : 'bg-emerald-500 shadow-emerald-200'}`}>START AGENTIC ANALYSIS</button>
          </div>
        )}

        {/* Step 5: Multi-Agent Processing */}
        {step === 5 && (
          <div className="bg-white rounded-[4rem] p-20 shadow-2xl text-center flex flex-col items-center">
             <div className={`w-20 h-20 border-8 ${shieldType === 'loan' ? 'border-blue-500' : 'border-emerald-500'} border-t-transparent rounded-full animate-spin mb-10`} />
             <h2 className="text-2xl font-black mb-4 uppercase tracking-[0.2em] italic">Orchestrating...</h2>
             <div className="space-y-4 w-full">
                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Compliance Agent Running Preliminary Analysis...</p>
                <div className="h-2 w-full bg-slate-100 rounded-full"><div className="h-full bg-blue-500 rounded-full animate-[loading_3s_ease-in-out]" /></div>
             </div>
             <button onClick={() => setStep(6)} className="mt-20 text-[10px] font-black uppercase tracking-widest text-slate-300 hover:text-blue-500">Fast Forward (Debug)</button>
          </div>
        )}

        {/* Step 6: Final Verdict */}
        {step === 6 && (
          <div className="bg-white rounded-[4rem] p-16 shadow-2xl text-center animate-in zoom-in-95 duration-1000 border-b-[16px] border-blue-50">
             <div className="inline-flex items-center gap-2 bg-emerald-100 text-emerald-600 px-8 py-3 rounded-full font-black text-[10px] uppercase tracking-widest mb-12 shadow-sm">
                <CheckCircle size={16} /> Verified by Kavach AI
             </div>
             <h2 className="text-8xl font-black text-slate-900 mb-2 italic tracking-tighter uppercase">{shieldType === 'loan' ? 'APPROVED' : '₹ 14,200'}</h2>
             <p className="text-slate-400 font-bold text-xs uppercase tracking-[0.4em] mb-12">Total Shield Level</p>

             <div className="bg-[#F8FBFF] rounded-[3rem] p-12 text-left border border-blue-50 shadow-inner">
                <h5 className="font-black text-xl flex items-center gap-4 mb-10 italic tracking-tight">
                   <BarChart3 size={28} className="text-blue-500" /> Transparent Reasoning Trace
                </h5>
                <div className="space-y-10">
                   {[
                     {l: "Identity Verification Agent", v: "100%", c: "bg-emerald-500", d: "Aadhaar e-KYC cross-referenced successfully."},
                     {l: "Explainable Risk Engine (EBM)", v: "84%", c: "bg-blue-500", d: "Positive interactions found between income and stability."},
                     {l: "Market Interaction Check", v: "12%", c: "bg-rose-500", d: "Minor interaction penalty due to current market inflation."}
                   ].map((it, i) => (
                     <div key={i}>
                        <div className="flex justify-between text-[10px] font-black uppercase mb-3 text-slate-400 tracking-widest"><span>{it.l}</span><span>{it.v}</span></div>
                        <div className="h-4 w-full bg-slate-200/50 rounded-full overflow-hidden mb-3">
                           <div className={`h-full ${it.c} transition-all duration-1000`} style={{width: it.v}} />
                        </div>
                        <p className="text-[10px] text-slate-500 font-medium italic leading-relaxed">{it.d}</p>
                     </div>
                   ))}
                </div>
             </div>
             
             <div className="mt-12 p-8 bg-blue-500/5 border-2 border-dashed border-blue-500/20 rounded-[2.5rem] flex gap-6 text-left items-start">
                <AlertCircle className="text-blue-500 shrink-0 mt-1" />
                <div className="space-y-2">
                   <h6 className="text-[10px] font-black uppercase text-blue-500 tracking-widest">Advisor Insight</h6>
                   <p className="text-xs text-slate-500 font-medium leading-relaxed italic">
                      "To lower your premium further, maintaining this BMI for 6 months will unlock the 'Disciplined Lifestyle' discount (approx. ₹1,200/yr savings)."
                   </p>
                </div>
             </div>

             <button onClick={goHome} className="mt-16 w-full py-8 bg-slate-900 text-white rounded-[2.5rem] font-black uppercase tracking-[0.2em] text-xs hover:bg-black transition shadow-2xl shadow-slate-300">Return to Lobby</button>
          </div>
        )}

      </main>
    </div>
  );
};

export default App;