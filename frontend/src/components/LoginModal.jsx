import { useState } from 'react';
import { X, Mail, Lock, User } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { validators } from '../utils/validators';

const LoginModal = ({ isOpen, onClose, onSuccess }) => {
  const [mode, setMode] = useState('login'); // 'login' or 'register'
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState('');

  const { login, register } = useAuth();

  if (!isOpen) return null;

  const validate = () => {
    const newErrors = {};

    if (!validators.email(formData.email)) {
      newErrors.email = 'Invalid email address';
    }

    if (!validators.password(formData.password)) {
      newErrors.password = 'Password must be at least 6 characters';
    }

    if (mode === 'register' && !formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setApiError('');

    if (!validate()) return;

    setLoading(true);

    try {
      if (mode === 'login') {
        await login(formData.email, formData.password);
      } else {
        await register(formData.email, formData.password, formData.name);
      }
      onSuccess?.();
      onClose();
    } catch (error) {
      setApiError(
        error.response?.data?.error || 
        error.message || 
        'An error occurred. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  const switchMode = () => {
    setMode(mode === 'login' ? 'register' : 'login');
    setErrors({});
    setApiError('');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-[3rem] p-12 max-w-md w-full mx-4 shadow-2xl animate-in zoom-in-95 duration-300">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-8 right-8 p-2 hover:bg-slate-100 rounded-full transition"
        >
          <X size={20} className="text-slate-400" />
        </button>

        {/* Header */}
        <div className="text-center mb-8">
          <h2 className="text-3xl font-black mb-2 italic tracking-tighter">
            {mode === 'login' ? 'Welcome Back' : 'Join Daksha'}
          </h2>
          <p className="text-slate-400 text-sm font-medium">
            {mode === 'login'
              ? 'Login to continue your quest'
              : 'Create your account to get started'}
          </p>
        </div>

        {/* API Error */}
        {apiError && (
          <div className="mb-6 p-4 bg-rose-50 border border-rose-200 rounded-2xl">
            <p className="text-rose-600 text-sm font-medium">{apiError}</p>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Name (register only) */}
          {mode === 'register' && (
            <div>
              <label className="block text-xs font-black uppercase text-slate-400 tracking-widest mb-2">
                Full Name
              </label>
              <div className="relative">
                <User
                  size={20}
                  className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-300"
                />
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                  className="w-full pl-12 pr-4 py-4 bg-slate-50 border-2 border-slate-100 rounded-2xl focus:border-blue-300 focus:bg-white outline-none font-medium transition"
                  placeholder="Rajesh Kumar"
                />
              </div>
              {errors.name && (
                <p className="text-rose-500 text-xs mt-2 font-medium">
                  {errors.name}
                </p>
              )}
            </div>
          )}

          {/* Email */}
          <div>
            <label className="block text-xs font-black uppercase text-slate-400 tracking-widest mb-2">
              Email
            </label>
            <div className="relative">
              <Mail
                size={20}
                className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-300"
              />
              <input
                type="email"
                value={formData.email}
                onChange={(e) =>
                  setFormData({ ...formData, email: e.target.value })
                }
                className="w-full pl-12 pr-4 py-4 bg-slate-50 border-2 border-slate-100 rounded-2xl focus:border-blue-300 focus:bg-white outline-none font-medium transition"
                placeholder="you@example.com"
              />
            </div>
            {errors.email && (
              <p className="text-rose-500 text-xs mt-2 font-medium">
                {errors.email}
              </p>
            )}
          </div>

          {/* Password */}
          <div>
            <label className="block text-xs font-black uppercase text-slate-400 tracking-widest mb-2">
              Password
            </label>
            <div className="relative">
              <Lock
                size={20}
                className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-300"
              />
              <input
                type="password"
                value={formData.password}
                onChange={(e) =>
                  setFormData({ ...formData, password: e.target.value })
                }
                className="w-full pl-12 pr-4 py-4 bg-slate-50 border-2 border-slate-100 rounded-2xl focus:border-blue-300 focus:bg-white outline-none font-medium transition"
                placeholder="••••••••"
              />
            </div>
            {errors.password && (
              <p className="text-rose-500 text-xs mt-2 font-medium">
                {errors.password}
              </p>
            )}
          </div>

          {/* Submit button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-4 bg-blue-500 text-white font-black text-xs uppercase tracking-widest rounded-2xl shadow-xl shadow-blue-200 hover:bg-blue-600 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading
              ? 'PROCESSING...'
              : mode === 'login'
              ? 'LOGIN'
              : 'CREATE ACCOUNT'}
          </button>
        </form>

        {/* Switch mode */}
        <div className="mt-8 text-center">
          <p className="text-slate-400 text-sm font-medium">
            {mode === 'login'
              ? "Don't have an account? "
              : 'Already have an account? '}
            <button
              onClick={switchMode}
              className="text-blue-500 font-bold hover:underline"
            >
              {mode === 'login' ? 'Register' : 'Login'}
            </button>
          </p>
        </div>

        {/* Demo credentials hint */}
        {mode === 'login' && (
          <div className="mt-6 p-4 bg-blue-50 rounded-2xl border border-blue-100">
            <p className="text-xs text-blue-600 font-medium text-center">
              <strong>Demo:</strong> admin@daksha.com / admin123
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default LoginModal;
