import { Loader2 } from 'lucide-react';

const LoadingSpinner = ({ size = 'md', text = '' }) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16',
  };

  return (
    <div className="flex flex-col items-center justify-center gap-4">
      <Loader2
        className={`${sizeClasses[size]} text-blue-500 animate-spin`}
      />
      {text && (
        <p className="text-sm font-medium text-slate-500">{text}</p>
      )}
    </div>
  );
};

export default LoadingSpinner;
