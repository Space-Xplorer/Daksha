import React from 'react';
import { useShield } from '../context/ShieldContext';
import { Fingerprint } from 'lucide-react';

const KYC = () => {
  const { setView, userData, setUserData } = useShield();

  return (
    <div className="max-w-xl mx-auto py-20 text-center px-6 animate-in zoom-in-95">
      <div className="w-24 h-24 bg-[#4B0082] rounded-[2.5rem] flex items-center justify-center mx-auto mb-10 pink-glow rotate-6">
        <Fingerprint className="text-[#F4C2C2]" size={48} />
      </div>
      <h2 className="text-4xl font-black text-[#4B0082] tracking-tighter mb-4 italic">Identity Quest</h2>
      <p className="text-slate-400 mb-12 font-medium">Verify your Aadhaar to enter the Daksha Nexus.</p>
      
      <input 
        type="text" 
        placeholder="0000 0000 0000" 
        maxLength="12" 
        onChange={(e) => setUserData({...userData, aadhaar: e.target.value})}
        className="w-full bg-white/50 border-4 border-white p-8 rounded-[2.5rem] text-center text-4xl font-black text-[#4B0082] outline-none focus:border-[#F4C2C2] transition-all mb-8 shadow-inner" 
      />
      
      <button 
        onClick={() => setView('selection')} 
        disabled={userData.aadhaar.length < 12}
       className="w-full py-8 brinjal-gradient text-[#533377] drop-shadow-sm rounded-[2rem] font-black uppercase tracking-widest shadow-xl hover:scale-[1.01] transition-all"
      >
        Validate Identity
      </button>
    </div>
  );
};

export default KYC;