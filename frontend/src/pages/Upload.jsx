import React from 'react';
import { useShield } from '../context/ShieldContext';
import { ArrowLeft, FileText, Upload as UploadIcon, CheckCircle } from 'lucide-react';

const Upload = () => {
  const { setView, service, uploadedDocs, setUploadedDocs } = useShield();

  const loanDocs = ["Aadhaar Card", "PAN Card", "6 Months Bank Statement", "Latest ITR"];
  const healthDocs = ["Aadhaar Card", "PAN Card", "Lab Diagnostic Report", "Medical History"];
  const currentDocs = service === 'loan' ? loanDocs : healthDocs;

  const handleUpload = (doc) => {
    setUploadedDocs(prev => ({ ...prev, [doc]: true }));
  };

  const isComplete = Object.keys(uploadedDocs).length === currentDocs.length;

  return (
    <div className="max-w-3xl mx-auto py-10 px-6 animate-in fade-in">
      <div className="flex items-center gap-4 mb-10">
        <button onClick={() => setView('selection')} className="p-3 bg-white rounded-2xl text-[#4B0082] shadow-sm"><ArrowLeft size={20} /></button>
        <h2 className="text-3xl font-black text-[#4B0082] italic tracking-tighter">Vault: {service === 'loan' ? 'Loan Quest' : 'Life Quest'}</h2>
      </div>

      <div className="space-y-4 mb-12">
        {currentDocs.map((doc, i) => (
          <div key={i} className="flex items-center justify-between p-6 glass-card rounded-3xl">
            <div className="flex items-center gap-4">
              <FileText className="text-[#4B0082]" size={20} />
              <span className="font-bold text-[#4B0082] text-sm">{doc}</span>
            </div>
            {uploadedDocs[doc] ? (
              <div className="flex items-center gap-2 text-emerald-500 font-black text-[10px] uppercase"><CheckCircle size={16} /> Verified</div>
            ) : (
              <button onClick={() => handleUpload(doc)} className="bg-white px-6 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest text-[#4B0082] border border-[#4B0082]/10 hover:bg-[#F4C2C2] transition-all">Upload</button>
            )}
          </div>
        ))}
      </div>

      <button 
        onClick={() => setView('analysis')} 
        disabled={!isComplete}
        className="w-full py-8 brinjal-gradient text-white rounded-[2.5rem] font-black uppercase tracking-widest shadow-2xl disabled:opacity-30"
      >
        Execute Preliminary Analysis
      </button>
    </div>
  );
};

export default Upload;