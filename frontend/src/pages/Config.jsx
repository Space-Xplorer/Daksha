import React, { useState } from 'react';
import { useShield } from '../context/ShieldContext';
import { ArrowLeft, Landmark, Heart, ChevronRight, Scale, Ruler } from 'lucide-react';
import GlassCard from '../components/GlassCard';

const Config = () => {
  const { setView, service, userData, setUserData } = useShield();
  const [formData, setFormData] = useState({});

  const handleNext = () => {
    // Save details to global context if needed
    setUserData({ ...userData, ...formData });
    setView('upload');
  };

  return (
    <div className="max-w-3xl mx-auto py-10 px-6 animate-in slide-in-from-bottom-10">
      <div className="flex items-center gap-4 mb-10">
        <button onClick={() => setView('selection')} className="p-3 bg-white rounded-2xl text-[#4B0082] shadow-sm">
          <ArrowLeft size={20} />
        </button>
        <h2 className="text-3xl font-black text-[#4B0082] italic tracking-tighter">
          {service === 'loan' ? 'Loan Configuration' : 'Health Profiling'}
        </h2>
      </div>

      <GlassCard className="p-12">
        <div className="space-y-8">
          {service === 'loan' ? (
            /* --- LOAN FORM --- */
            <div className="grid md:grid-cols-2 gap-8">
              <div className="space-y-3">
                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-2">Annual Income (INR)</label>
                <input type="number" placeholder="e.g. 12,00,000" className="w-full bg-[#FAF9F6] p-6 rounded-3xl outline-none focus:ring-2 ring-[#F4C2C2] font-bold text-[#4B0082]" />
              </div>
              <div className="space-y-3">
                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-2">Desired Loan Amount</label>
                <input type="number" placeholder="e.g. 50,00,000" className="w-full bg-[#FAF9F6] p-6 rounded-3xl outline-none focus:ring-2 ring-[#F4C2C2] font-bold text-[#4B0082]" />
              </div>
              <div className="space-y-3">
                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-2">Tenure (Years)</label>
                <select className="w-full bg-[#FAF9F6] p-6 rounded-3xl outline-none focus:ring-2 ring-[#F4C2C2] font-bold text-[#4B0082] appearance-none">
                  <option>5 Years</option>
                  <option>10 Years</option>
                  <option>20 Years</option>
                </select>
              </div>
              <div className="space-y-3">
                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-2">Purpose</label>
                <input type="text" placeholder="Home, Education, etc." className="w-full bg-[#FAF9F6] p-6 rounded-3xl outline-none focus:ring-2 ring-[#F4C2C2] font-bold text-[#4B0082]" />
              </div>
            </div>
          ) : (
            /* --- HEALTH FORM --- */
            <div className="grid md:grid-cols-2 gap-8">
              <div className="space-y-3">
                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-2">Age</label>
                <input type="number" placeholder="e.g. 25" className="w-full bg-[#FAF9F6] p-6 rounded-3xl outline-none focus:ring-2 ring-[#F4C2C2] font-bold text-[#4B0082]" />
              </div>
              <div className="flex gap-4">
                <div className="space-y-3 flex-1">
                  <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-2">Weight (kg)</label>
                  <input type="number" placeholder="70" className="w-full bg-[#FAF9F6] p-4 rounded-3xl outline-none focus:ring-2 ring-[#F4C2C2] font-bold text-[#4B0082]" />
                </div>
                <div className="space-y-3 flex-1">
                  <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-2">Height (cm)</label>
                  <input type="number" placeholder="175" className="w-full bg-[#FAF9F6] p-4 rounded-3xl outline-none focus:ring-2 ring-[#F4C2C2] font-bold text-[#4B0082]" />
                </div>
              </div>
              <div className="space-y-3 md:col-span-2">
                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-2">Hereditary Conditions</label>
                <input type="text" placeholder="Diabetes, Heart Disease, None" className="w-full bg-[#FAF9F6] p-6 rounded-3xl outline-none focus:ring-2 ring-[#F4C2C2] font-bold text-[#4B0082]" />
              </div>
              <div className="flex items-center gap-4 p-4 bg-[#4B0082]/5 rounded-3xl md:col-span-2">
                <input type="checkbox" className="w-6 h-6 rounded-lg accent-[#4B0082]" />
                <span className="text-xs font-bold text-[#4B0082]">I am a regular smoker / tobacco user</span>
              </div>
            </div>
          )}

          <button 
            onClick={handleNext} 
            // Added 'drop-shadow-sm' for extra crispness
            className="w-full py-8 brinjal-gradient text-[#533377] drop-shadow-sm rounded-[2rem] font-black uppercase tracking-widest shadow-xl hover:scale-[1.01] transition-all"
          >
            Confirm Details & Proceed
          </button>
        </div>
      </GlassCard>
    </div>
  );
};

export default Config;