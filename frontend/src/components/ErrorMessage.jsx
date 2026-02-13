import { AlertCircle, X } from 'lucide-react';

const ErrorMessage = ({ message, onClose }) => {
  if (!message) return null;

  return (
    <div className="bg-rose-50 border-2 border-rose-200 rounded-2xl p-6 flex items-start gap-4 animate-in slide-in-from-top-4">
      <AlertCircle className="text-rose-500 shrink-0 mt-0.5" size={20} />
      <div className="flex-1">
        <h4 className="font-black text-rose-900 text-sm mb-1">Error</h4>
        <p className="text-rose-700 text-sm font-medium">{message}</p>
      </div>
      {onClose && (
        <button
          onClick={onClose}
          className="p-1 hover:bg-rose-100 rounded-lg transition"
        >
          <X size={16} className="text-rose-400" />
        </button>
      )}
    </div>
  );
};

export default ErrorMessage;
