import { useState } from 'react';
import { CheckCircle, Edit2, AlertCircle } from 'lucide-react';

const HITLReview = ({ data, onApprove, onCancel }) => {
  const [corrections, setCorrections] = useState({});
  const [loading, setLoading] = useState(false);

  const handleFieldEdit = (field, value) => {
    setCorrections({
      ...corrections,
      [field]: value,
    });
  };

  const handleApprove = async () => {
    setLoading(true);
    try {
      await onApprove(corrections);
    } catch (error) {
      console.error('HITL approval error:', error);
    } finally {
      setLoading(false);
    }
  };

  const extractedData = data?.extracted_data || {};
  const fields = Object.entries(extractedData);

  return (
    <div className="bg-white rounded-[4rem] p-12 shadow-2xl animate-in zoom-in-95">
      {/* Header */}
      <div className="text-center mb-10">
        <div className="w-20 h-20 bg-yellow-50 rounded-[2rem] flex items-center justify-center mx-auto mb-6 border border-yellow-100">
          <AlertCircle className="text-yellow-500" size={40} />
        </div>
        <h2 className="text-3xl font-black mb-3 italic tracking-tighter">
          Human Review Required
        </h2>
        <p className="text-slate-400 font-medium text-sm">
          Please verify the extracted data below. Make corrections if needed.
        </p>
      </div>

      {/* Extracted Data */}
      <div className="space-y-6 mb-10">
        <h3 className="text-xs font-black uppercase text-slate-400 tracking-widest">
          Extracted Information
        </h3>

        <div className="space-y-4">
          {fields.length === 0 ? (
            <p className="text-slate-400 text-sm italic text-center py-8">
              No data extracted yet
            </p>
          ) : (
            fields.map(([field, value]) => (
              <div
                key={field}
                className="bg-slate-50 rounded-2xl p-6 border-2 border-slate-100"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <label className="block text-xs font-black uppercase text-slate-400 tracking-widest mb-2">
                      {field.replace(/_/g, ' ')}
                    </label>
                    <input
                      type="text"
                      defaultValue={value}
                      onChange={(e) => handleFieldEdit(field, e.target.value)}
                      className="w-full bg-white border-2 border-slate-200 rounded-xl px-4 py-3 font-medium focus:border-blue-300 outline-none transition"
                    />
                  </div>
                  <Edit2 size={16} className="text-slate-300 mt-8" />
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Info Box */}
      <div className="mb-10 p-6 bg-blue-50 border-2 border-dashed border-blue-200 rounded-2xl flex gap-4 items-start">
        <AlertCircle className="text-blue-500 shrink-0 mt-1" size={20} />
        <div>
          <h4 className="text-xs font-black uppercase text-blue-500 tracking-widest mb-2">
            Why This Step?
          </h4>
          <p className="text-blue-700 text-sm font-medium leading-relaxed">
            Our OCR agents extracted this data from your documents. Please
            verify accuracy before proceeding to compliance checks.
          </p>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4">
        <button
          onClick={onCancel}
          className="flex-1 py-4 bg-slate-100 text-slate-600 font-black text-xs uppercase tracking-widest rounded-2xl hover:bg-slate-200 transition"
        >
          Cancel
        </button>
        <button
          onClick={handleApprove}
          disabled={loading}
          className="flex-1 py-4 bg-blue-500 text-white font-black text-xs uppercase tracking-widest rounded-2xl shadow-xl shadow-blue-200 hover:bg-blue-600 transition disabled:opacity-50 flex items-center justify-center gap-2"
        >
          <CheckCircle size={16} />
          {loading ? 'PROCESSING...' : 'APPROVE & CONTINUE'}
        </button>
      </div>
    </div>
  );
};

export default HITLReview;
