import { useState } from 'react';
import { 
  Shield, UserCheck, FileText, Activity, Landmark, Upload, 
  CheckCircle, AlertCircle, ChevronRight, Fingerprint, 
  Search, Info, ArrowLeft, Clock, Zap, ArrowRight, Eye, ShieldCheck, 
  TrendingUp, Building2, BarChart3, Rocket, Star, Trophy, Target,
  ZapOff, ShieldAlert, PieChart, Layers, Network, LogOut
} from 'lucide-react';
import { useAuth } from './context/AuthContext';
import { useApplication } from './context/ApplicationContext';
import LoginModal from './components/LoginModal';
import LoadingSpinner from './components/LoadingSpinner';
import ErrorMessage from './components/ErrorMessage';
import HITLReview from './components/HITLReview';
import { validators, formatAadhaar, formatCurrency } from './utils/validators';

const App = () => {
  const [view, setView] = useState('landing'); 
  const [step, setStep] = useState(1);
  const [shieldType, setShieldType] = useState(null);
  const [aadhaar, setAadhaar] = useState("");
  const [isVerifying, setIsVerifying] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [error, setError] = useState('');
  const [showHITL, setShowHITL] = useState(false);
  const [hitlData, setHitlData] = useState(null);
  const [uploadedDocs, setUploadedDocs] = useState({});
  const [isUploading, setIsUploading] = useState(false);
  
  // Form data
  const [formData, setFormData] = useState({
    // Loan fields
    annual_income: '',
    loan_amount: '',
    existing_debt: '',
    employment_type: 'salaried',
    employment_years: '',
    cibil_score: '',
    // Health fields
    height: '',
    weight: '',
    age: '',
    smoker: false,
    gender: 'M',
    // Common
    name: '',
  });

  const { user, isAuthenticated, logout } = useAuth();
  const {
    currentApplication,
    workflowStatus,
    workflowResults,
    createApplication,
    updateApplication,
    submitWorkflow,
    pollWorkflow,
    getHITLData,
    approveHITL,
    resetApplication,
  } = useApplication();

  const startPlatform = () => {
    if (!isAuthenticated) {
      setShowLoginModal(true);
      return;
    }
    setView('platform');
    setStep(1);
    setError('');
    resetApplication();
    window.scrollTo(0, 0);
  };


  const viewPartner = () => { setView('partner'); window.scrollTo(0,0); };
  const goHome = () => { 
    setView('landing'); 
    setStep(1); 
    setShieldType(null); 
    setError('');
    setShowHITL(false);
    resetApplication();
    window.scrollTo(0,0); 
  };

  const handleLogout = async () => {
    await logout();
    goHome();
  };

  // Step 1: Create application with KYC
  const handleKYCSubmit = async () => {
    if (!validators.aadhaar(aadhaar)) {
      setError('Please enter a valid 12-digit Aadhaar number');
      return;
    }

    setIsVerifying(true);
    setError('');

    try {
      // Create application with KYC data
      const app = await createApplication({
        submitted_aadhaar: aadhaar,
        request_type: 'both', // Will be updated in next step
        applicant_data: {},
      });

      console.log('Application created:', app);
      
      if (!app || !app.id) {
        throw new Error('Invalid application response');
      }
      
      setStep(2);
    } catch (err) {
      console.error('KYC submit error:', err);
      setError(err.response?.data?.error || err.message || 'KYC verification failed');
    } finally {
      setIsVerifying(false);
    }
  };

  // Step 2: Update request type
  const handleProductSelect = async (type) => {
    setShieldType(type);
    setError('');

    if (!currentApplication || !currentApplication.id) {
      setError('No application found. Please start over.');
      return;
    }

    try {
      await updateApplication(currentApplication.id, {
        request_type: type,
      });
      setStep(3);
    } catch (err) {
      console.error('Product select error:', err);
      setError(err.response?.data?.error || 'Failed to update application');
    }
  };

  // Step 3: Update form data
  const handleFormSubmit = async () => {
    setError('');

    if (!currentApplication || !currentApplication.id) {
      setError('No application found. Please start over.');
      return;
    }

    // Build applicant data based on shield type
    const applicantData = {
      name: formData.name || user?.name,
    };

    if (shieldType === 'loan' || shieldType === 'both') {
      applicantData.annual_income = parseFloat(formData.annual_income);
      applicantData.loan_amount = parseFloat(formData.loan_amount);
      applicantData.existing_debt = parseFloat(formData.existing_debt || 0);
      applicantData.employment_type = formData.employment_type;
      applicantData.employment_years = parseInt(formData.employment_years);
      applicantData.cibil_score = parseInt(formData.cibil_score || 750);
    }

    if (shieldType === 'health' || shieldType === 'both') {
      const height = parseFloat(formData.height) / 100; // cm to m
      const weight = parseFloat(formData.weight);
      applicantData.bmi = weight / (height * height);
      applicantData.age = parseInt(formData.age);
      applicantData.smoker = formData.smoker;
      applicantData.gender = formData.gender;
    }

    try {
      await updateApplication(currentApplication.id, {
        applicant_data: applicantData,
      });
      setStep(4);
    } catch (err) {
      console.error('Form submit error:', err);
      setError(err.response?.data?.error || 'Failed to save form data');
    }
  };


  // Step 4: Upload documents and go to workflow
  const handleDocumentUpload = async () => {
    setError('');

    if (!currentApplication || !currentApplication.id) {
      setError('No application found. Please start over.');
      return;
    }

    const documents = Object.entries(uploadedDocs).map(([type, doc]) => ({
      type,
      name: doc.name,
      mime_type: doc.mime_type,
      content_base64: doc.data,
    }));

    try {
      await updateApplication(currentApplication.id, {
        uploaded_documents: documents,
      });
      setStep(5);
      startWorkflow();
    } catch (err) {
      console.error('Document upload submit error:', err);
      setError(err.response?.data?.error || 'Failed to submit documents');
    }
  };

  // Handle file upload
  const handleFileUpload = async (docType, file) => {
    if (!file) return;

    // Define which documents accept images
    const imageAcceptedDocs = ['tenth_marksheet'];
    const acceptsPdf = file.type === 'application/pdf';
    const acceptsImage = imageAcceptedDocs.includes(docType) && 
                         (file.type === 'image/jpeg' || file.type === 'image/jpg' || file.type === 'image/png');

    // Validate file type
    if (!acceptsPdf && !acceptsImage) {
      if (imageAcceptedDocs.includes(docType)) {
        setError('Please upload PDF or image files (JPG, PNG) only');
      } else {
        setError('Please upload PDF files only');
      }
      return;
    }

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      setError('File size must be less than 5MB');
      return;
    }

    setIsUploading(true);
    setError('');

    try {
      // Convert to base64
      const reader = new FileReader();
      reader.onload = async (e) => {
        const base64 = e.target.result.split(',')[1];
        
        // Store uploaded document
        setUploadedDocs(prev => ({
          ...prev,
          [docType]: {
            name: file.name,
            size: file.size,
            data: base64,
            type: docType,
            mime_type: file.type
          }
        }));

        setIsUploading(false);
      };

      reader.onerror = () => {
        setError('Failed to read file');
        setIsUploading(false);
      };

      reader.readAsDataURL(file);
    } catch (err) {
      console.error('File upload error:', err);
      setError('Failed to upload file');
      setIsUploading(false);
    }
  };

  // Remove uploaded document
  const removeDocument = (docType) => {
    setUploadedDocs(prev => {
      const updated = { ...prev };
      delete updated[docType];
      return updated;
    });
  };

  // Proceed to workflow with documents
  const REQUIRED_DOCS = {
    loan: ['bank_statement', 'salary_slip', 'itr', 'form_16'],
    health: ['diagnostic_report', 'medical_history', 'tenth_marksheet']
  };

  const DOC_LABELS = {
    bank_statement: 'Bank Statements',
    salary_slip: 'Salary Slips',
    itr: 'Income Tax Returns (ITR)',
    form_16: 'Form 16 / TDS',
    diagnostic_report: 'Diagnostic Reports',
    medical_history: 'Medical History',
    tenth_marksheet: '10th Marksheet'
  };

  const getMissingDocs = () => {
    const required = [];
    if (shieldType === 'loan' || shieldType === 'both') {
      required.push(...REQUIRED_DOCS.loan);
    }
    if (shieldType === 'health' || shieldType === 'both') {
      required.push(...REQUIRED_DOCS.health);
    }
    return required.filter((docType) => !uploadedDocs[docType]);
  };

  const proceedWithDocuments = async () => {
    const missingDocs = getMissingDocs();

    if (missingDocs.length > 0) {
      const missingLabels = missingDocs.map((doc) => DOC_LABELS[doc] || doc).join(', ');
      setError(`Please upload required documents: ${missingLabels}`);
      return;
    }

    await handleDocumentUpload();
  };

  // Step 5: Start workflow execution
  const startWorkflow = async () => {
    setError('');

    try {
      // Submit workflow
      await submitWorkflow(currentApplication.id);

      // Poll for status
      const results = await pollWorkflow(
        currentApplication.id,
        (status) => {
          console.log('Workflow status:', status);
        }
      );

      // Check if HITL is required
      if (results.status === 'hitl_pending') {
        const hitl = await getHITLData(currentApplication.id);
        setHitlData(hitl);
        setShowHITL(true);
      } else {
        // Workflow completed
        setStep(6);
      }
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Workflow execution failed');
      console.error('Workflow error:', err);
    }
  };

  // Handle HITL approval
  const handleHITLApprove = async (corrections) => {
    setError('');

    try {
      await approveHITL(currentApplication.id, corrections);
      setShowHITL(false);

      // Continue polling workflow
      const results = await pollWorkflow(currentApplication.id);
      setStep(6);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to approve HITL');
    }
  };

  const handleHITLCancel = () => {
    setShowHITL(false);
    goHome();
  };


  // --- VIEW 1: LANDING PAGE ---
  if (view === 'landing') {
    return (
      <div className="min-h-screen bg-[#f5f7fa]">
        
        {/* Hero Section */}
        <header className="bg-[#0b1f3a] text-white py-16 px-5 text-center">
          <h1 className="text-5xl font-bold mb-5">Daksha</h1>
          <p className="text-xl mb-8">Explainable AI for Financial & Health Risk</p>
          <button 
            onClick={startPlatform}
            className="px-6 py-3 bg-white text-[#0b1f3a] rounded-lg font-semibold hover:bg-gray-100 transition-colors"
          >
            Sign Me Up
          </button>
        </header>

        {/* Features */}
        <section className="max-w-[1000px] mx-auto py-10 px-5">
          <h2 className="text-3xl font-bold text-center mb-8">Efficiency at Scale</h2>

          <div className="bg-white p-6 my-5 rounded-xl shadow-sm hover:shadow-md transition-shadow">
            <h3 className="text-xl font-semibold mb-3 text-[#0b1f3a]">Identity & Extraction</h3>
            <p className="text-gray-700 leading-relaxed">
              Secure Aadhaar e-KYC and automated OCR document syncing.
            </p>
          </div>

          <div className="bg-white p-6 my-5 rounded-xl shadow-sm hover:shadow-md transition-shadow">
            <h3 className="text-xl font-semibold mb-3 text-[#0b1f3a]">EBM Engine</h3>
            <p className="text-gray-700 leading-relaxed">
              Transparent risk scoring using glass-box mathematical logic.
            </p>
          </div>

          <div className="bg-white p-6 my-5 rounded-xl shadow-sm hover:shadow-md transition-shadow">
            <h3 className="text-xl font-semibold mb-3 text-[#0b1f3a]">Advisor Agent</h3>
            <p className="text-gray-700 leading-relaxed">
              Human-readable reasoning trace for decision transparency.
            </p>
          </div>
        </section>

        {/* Why Choose Us */}
        <section className="max-w-[1000px] mx-auto py-10 px-5">
          <h2 className="text-3xl font-bold text-center mb-8">Why Organizations Choose Us</h2>

          <div className="bg-white p-6 my-5 rounded-xl shadow-sm">
            <ul className="space-y-3">
              <li className="text-gray-800 flex items-start">
                <span className="text-green-500 font-bold mr-3 text-xl">✓</span>
                <span>Open-source transparent framework</span>
              </li>
              <li className="text-gray-800 flex items-start">
                <span className="text-green-500 font-bold mr-3 text-xl">✓</span>
                <span>No black-box AI guesses</span>
              </li>
              <li className="text-gray-800 flex items-start">
                <span className="text-green-500 font-bold mr-3 text-xl">✓</span>
                <span>Regulatory compliance ready</span>
              </li>
            </ul>
          </div>
        </section>

        {/* Pricing */}
        <section className="max-w-[1000px] mx-auto py-10 px-5">
          <h2 className="text-3xl font-bold text-center mb-8">Service Package</h2>

          <div className="bg-white p-6 my-5 rounded-xl shadow-sm">
            <h3 className="text-xl font-semibold mb-3 text-[#0b1f3a]">Basic Package</h3>
            <p className="text-gray-700">Open-source platform — $0</p>
          </div>
        </section>

        {/* Contact */}
        <footer className="bg-[#0b1f3a] text-white py-8 px-5 text-center mt-12">
          contact_us@daksha.in
        </footer>

        {/* Login Modal */}
        <LoginModal 
          isOpen={showLoginModal} 
          onClose={() => setShowLoginModal(false)}
          onSuccess={() => {
            setShowLoginModal(false);
            startPlatform();
          }}
        />
      </div>
    );
  }


  // --- VIEW 2: B2B PARTNER PAGE ---
  if (view === 'partner') {
    return (
      <div className="min-h-screen bg-white text-slate-800 font-sans">
        <nav className="h-20 border-b border-slate-100 px-8 flex items-center justify-between sticky top-0 bg-white/90 backdrop-blur-md z-50">
          <div onClick={goHome} className="flex items-center gap-2 cursor-pointer font-black text-blue-600 italic tracking-tighter text-xl">DAKSHA B2B</div>
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


  // --- VIEW 3: THE GAME PLATFORM (Integrated with Backend) ---
  return (
    <div className="min-h-screen bg-[#F8F9FF] text-slate-800 font-sans">
      <nav className="h-20 bg-white border-b border-slate-100 px-8 flex items-center justify-between sticky top-0 z-50">
        <div onClick={goHome} className="flex items-center gap-2 cursor-pointer">
          <div className="p-1.5 bg-blue-500 rounded-xl shadow-lg shadow-blue-100"><Shield className="text-white w-4 h-4" /></div>
          <span className="font-black text-blue-600 italic tracking-tighter">DAKSHA PLAY</span>
        </div>
        <div className="flex items-center gap-4">
          <div className="hidden md:flex gap-2">
             {[1, 2, 3, 4, 5, 6].map(i => (
               <div key={i} className={`h-2 w-10 rounded-full transition-all duration-500 ${step >= i ? 'bg-blue-500' : 'bg-slate-100'}`} />
             ))}
          </div>
          {isAuthenticated && (
            <button onClick={handleLogout} className="text-xs font-black uppercase tracking-widest text-slate-400 hover:text-rose-500 flex items-center gap-2">
              <LogOut size={14} /> Logout
            </button>
          )}
        </div>
      </nav>

      <main className="max-w-3xl mx-auto py-12 px-6">
        
        {/* Error Message */}
        {error && (
          <div className="mb-6">
            <ErrorMessage message={error} onClose={() => setError('')} />
          </div>
        )}

        {/* HITL Review */}
        {showHITL && hitlData && (
          <HITLReview
            data={hitlData}
            onApprove={handleHITLApprove}
            onCancel={handleHITLCancel}
          />
        )}

        {/* Step 1: KYC (Identity Key) */}
        {!showHITL && step === 1 && (
          <div className="bg-white rounded-[4rem] p-16 shadow-2xl text-center animate-in fade-in slide-in-from-bottom-8 border border-blue-50">
            <div className="w-24 h-24 bg-blue-50 rounded-[2.5rem] flex items-center justify-center mx-auto mb-8 border border-blue-100 shadow-inner">
               <Fingerprint className="text-blue-500" size={48} />
            </div>
            <h2 className="text-4xl font-black mb-4 tracking-tighter italic">Identity Quest</h2>
            <p className="text-slate-400 font-medium mb-12">Login with your Aadhaar ID to summon your verified profile.</p>
            <input 
              type="text" 
              placeholder="0000 0000 0000" 
              maxLength="14"
              value={formatAadhaar(aadhaar)}
              className="w-full bg-slate-50 border-4 border-slate-100 p-8 rounded-[2.5rem] text-center text-4xl font-black tracking-[0.2em] focus:border-blue-400 focus:bg-white outline-none transition-all shadow-inner"
              onChange={(e) => setAadhaar(e.target.value.replace(/\s/g, ''))}
            />
            <button 
              onClick={handleKYCSubmit}
              disabled={!validators.aadhaar(aadhaar) || isVerifying}
              className="w-full mt-10 py-8 bg-blue-500 text-white font-black text-xs uppercase tracking-widest rounded-[2.5rem] shadow-2xl shadow-blue-200 hover:scale-[1.02] transition-all disabled:opacity-20 disabled:cursor-not-allowed"
            >
              {isVerifying ? "CONNECTING TO IDENTITY AGENT..." : "UNLOCK SHIELD"}
            </button>
          </div>
        )}


        {/* Step 2: Product Pick */}
        {!showHITL && step === 2 && (
          <div className="space-y-8 animate-in fade-in zoom-in-95">
             <div className="text-center">
                <h2 className="text-4xl font-black mb-2 italic tracking-tighter">Hi, {user?.name || 'User'}!</h2>
                <p className="text-slate-400 font-bold uppercase tracking-widest text-[10px]">What is your mission today?</p>
             </div>
             <div className="grid md:grid-cols-3 gap-6">
                <button onClick={() => handleProductSelect('loan')} className="group p-10 bg-white border-4 border-transparent hover:border-blue-400 rounded-[3rem] shadow-2xl transition-all text-left">
                   <div className="p-5 bg-blue-50 text-blue-500 rounded-2xl w-fit mb-6 group-hover:scale-110 transition shadow-sm"><Landmark size={32} /></div>
                  <h4 className="text-xl font-black">LOAN</h4>
                   <p className="text-xs text-slate-400 mt-3 font-medium leading-relaxed">Verify your credit and get instant approval.</p>
                </button>
                <button onClick={() => handleProductSelect('health')} className="group p-10 bg-white border-4 border-transparent hover:border-emerald-400 rounded-[3rem] shadow-2xl transition-all text-left">
                   <div className="p-5 bg-emerald-50 text-emerald-500 rounded-2xl w-fit mb-6 group-hover:scale-110 transition shadow-sm"><Activity size={32} /></div>
                  <h4 className="text-xl font-black">HEALTH</h4>
                   <p className="text-xs text-slate-400 mt-3 font-medium leading-relaxed">Assess health and unlock custom premiums.</p>
                </button>
                <button onClick={() => handleProductSelect('both')} className="group p-10 bg-white border-4 border-transparent hover:border-purple-400 rounded-[3rem] shadow-2xl transition-all text-left">
                   <div className="p-5 bg-purple-50 text-purple-500 rounded-2xl w-fit mb-6 group-hover:scale-110 transition shadow-sm"><Shield size={32} /></div>
                   <h4 className="text-xl font-black">BOTH SHIELDS</h4>
                   <p className="text-xs text-slate-400 mt-3 font-medium leading-relaxed">Complete loan + insurance in one go.</p>
                </button>
             </div>
          </div>
        )}

        {/* Step 3: Interactive Form */}
        {!showHITL && step === 3 && (
          <div className="bg-white rounded-[4rem] p-12 shadow-2xl animate-in fade-in slide-in-from-right-8">
            <h2 className="text-3xl font-black mb-10 italic tracking-tighter text-center">Base Configuration</h2>
            <div className="space-y-8">
               {(shieldType === 'loan' || shieldType === 'both') && (
                 <>
                   <div className="mb-6">
                     <h3 className="text-lg font-black text-blue-600 mb-4 flex items-center gap-2">
                       <Landmark size={20} /> Loan Details
                     </h3>
                   </div>
                   <div className="space-y-4">
                      <label className="text-[10px] font-black uppercase text-slate-400 tracking-widest">Annual Income (INR)</label>
                      <input 
                        type="number" 
                        placeholder="e.g. 1500000" 
                        value={formData.annual_income}
                        onChange={(e) => setFormData({...formData, annual_income: e.target.value})}
                        className="w-full bg-slate-50 border-2 border-slate-100 p-6 rounded-3xl focus:border-blue-300 outline-none font-bold" 
                      />
                   </div>
                   <div className="space-y-4">
                      <label className="text-[10px] font-black uppercase text-slate-400 tracking-widest">Requested Amount (INR)</label>
                      <input 
                        type="number" 
                        placeholder="e.g. 5000000" 
                        value={formData.loan_amount}
                        onChange={(e) => setFormData({...formData, loan_amount: e.target.value})}
                        className="w-full bg-slate-50 border-2 border-slate-100 p-6 rounded-3xl focus:border-blue-300 outline-none font-bold" 
                      />
                   </div>
                   <div className="space-y-4">
                      <label className="text-[10px] font-black uppercase text-slate-400 tracking-widest">Existing Debt (INR)</label>
                      <input 
                        type="number" 
                        placeholder="e.g. 100000" 
                        value={formData.existing_debt}
                        onChange={(e) => setFormData({...formData, existing_debt: e.target.value})}
                        className="w-full bg-slate-50 border-2 border-slate-100 p-6 rounded-3xl focus:border-blue-300 outline-none font-bold" 
                      />
                   </div>
                   <div className="space-y-4">
                      <label className="text-[10px] font-black uppercase text-slate-400 tracking-widest">Employment Years</label>
                      <input 
                        type="number" 
                        placeholder="e.g. 5" 
                        value={formData.employment_years}
                        onChange={(e) => setFormData({...formData, employment_years: e.target.value})}
                        className="w-full bg-slate-50 border-2 border-slate-100 p-6 rounded-3xl focus:border-blue-300 outline-none font-bold" 
                      />
                   </div>
                 </>
               )}
               
               {(shieldType === 'health' || shieldType === 'both') && (
                 <>
                   {shieldType === 'both' && <div className="border-t-2 border-slate-100 my-8" />}
                   <div className="mb-6">
                     <h3 className="text-lg font-black text-emerald-600 mb-4 flex items-center gap-2">
                       <Activity size={20} /> Health Details
                     </h3>
                   </div>
                   <div className="space-y-4">
                      <label className="text-[10px] font-black uppercase text-slate-400 tracking-widest">Height (CM)</label>
                      <input 
                        type="number" 
                        placeholder="e.g. 175" 
                        value={formData.height}
                        onChange={(e) => setFormData({...formData, height: e.target.value})}
                        className="w-full bg-slate-50 border-2 border-slate-100 p-6 rounded-3xl focus:border-emerald-300 outline-none font-bold" 
                      />
                   </div>
                   <div className="space-y-4">
                      <label className="text-[10px] font-black uppercase text-slate-400 tracking-widest">Weight (KG)</label>
                      <input 
                        type="number" 
                        placeholder="e.g. 70" 
                        value={formData.weight}
                        onChange={(e) => setFormData({...formData, weight: e.target.value})}
                        className="w-full bg-slate-50 border-2 border-slate-100 p-6 rounded-3xl focus:border-emerald-300 outline-none font-bold" 
                      />
                   </div>
                   <div className="space-y-4">
                      <label className="text-[10px] font-black uppercase text-slate-400 tracking-widest">Age</label>
                      <input 
                        type="number" 
                        placeholder="e.g. 32" 
                        value={formData.age}
                        onChange={(e) => setFormData({...formData, age: e.target.value})}
                        className="w-full bg-slate-50 border-2 border-slate-100 p-6 rounded-3xl focus:border-emerald-300 outline-none font-bold" 
                      />
                   </div>
                   <div className="space-y-4">
                      <label className="text-[10px] font-black uppercase text-slate-400 tracking-widest">Smoker?</label>
                      <div className="flex gap-4">
                        <button 
                          onClick={() => setFormData({...formData, smoker: false})}
                          className={`flex-1 py-4 rounded-2xl font-bold transition ${!formData.smoker ? 'bg-emerald-500 text-white' : 'bg-slate-100 text-slate-400'}`}
                        >
                          No
                        </button>
                        <button 
                          onClick={() => setFormData({...formData, smoker: true})}
                          className={`flex-1 py-4 rounded-2xl font-bold transition ${formData.smoker ? 'bg-rose-500 text-white' : 'bg-slate-100 text-slate-400'}`}
                        >
                          Yes
                        </button>
                      </div>
                   </div>
                 </>
               )}
               <button 
                 onClick={handleFormSubmit} 
                 className={`w-full py-6 text-white font-black rounded-3xl shadow-xl transition-all ${
                   shieldType === 'loan' ? 'bg-blue-500 shadow-blue-200' : 
                   shieldType === 'health' ? 'bg-emerald-500 shadow-emerald-200' :
                   'bg-purple-500 shadow-purple-200'
                 }`}
               >
                 NEXT STAGE: DOCUMENT SCAN
               </button>
            </div>
          </div>
        )}


        {/* Step 4: Doc Upload */}
        {!showHITL && step === 4 && (
          <div className="bg-white rounded-[4rem] p-12 shadow-2xl animate-in fade-in">
             {/* Header - Sticky */}
             <div className="text-center mb-8 sticky top-0 bg-white z-10 pb-6">
               <div className="w-20 h-20 bg-blue-50 rounded-[2rem] flex items-center justify-center mx-auto mb-6 border border-blue-100 shadow-inner">
                  <Upload className="text-blue-500" size={32} />
               </div>
               <h2 className="text-3xl font-black mb-3 italic tracking-tighter">
                 Document Upload
               </h2>
               <p className="text-slate-400 font-medium text-sm mb-4">
                 Upload your documents. Our OCR Agent will auto-extract the features.
               </p>
               {/* Document Counter */}
               <div className="inline-flex items-center gap-2 bg-blue-50 text-blue-600 px-6 py-2 rounded-full text-xs font-black">
                 <FileText size={14} />
                 {Object.keys(uploadedDocs).length} Document{Object.keys(uploadedDocs).length !== 1 ? 's' : ''} Uploaded
               </div>
             </div>

             {/* Scrollable Document List */}
             <div className="max-h-[500px] overflow-y-auto pr-2 space-y-8 mb-8">
               
             {/* Loan Documents */}
             {(shieldType === 'loan' || shieldType === 'both') && (
               <div>
                 <h3 className="text-lg font-black text-blue-600 mb-4 flex items-center gap-2 sticky top-0 bg-white py-2">
                   <Landmark size={20} /> Loan Documents
                 </h3>
                 <div className="space-y-4">
                   {/* Bank Statement */}
                   <div className="p-6 bg-blue-50 rounded-2xl border-2 border-blue-100">
                     <div className="flex items-center justify-between mb-3">
                       <div>
                         <h4 className="font-black text-sm">Bank Statements</h4>
                         <p className="text-xs text-slate-400 mt-1">Last 6 months (PDF)</p>
                       </div>
                       {uploadedDocs['bank_statement'] ? (
                         <button
                           onClick={() => removeDocument('bank_statement')}
                           className="px-4 py-2 bg-rose-100 text-rose-600 rounded-xl text-xs font-bold hover:bg-rose-200 transition"
                         >
                           Remove
                         </button>
                       ) : (
                         <label className="px-4 py-2 bg-blue-500 text-white rounded-xl text-xs font-bold cursor-pointer hover:bg-blue-600 transition">
                           Upload
                           <input
                             type="file"
                             accept=".pdf"
                             className="hidden"
                             onChange={(e) => handleFileUpload('bank_statement', e.target.files[0])}
                           />
                         </label>
                       )}
                     </div>
                     {uploadedDocs['bank_statement'] && (
                       <div className="flex items-center gap-2 text-xs text-emerald-600 font-medium">
                         <CheckCircle size={14} />
                         {uploadedDocs['bank_statement'].name}
                       </div>
                     )}
                   </div>

                   {/* Salary Slips */}
                   <div className="p-6 bg-blue-50 rounded-2xl border-2 border-blue-100">
                     <div className="flex items-center justify-between mb-3">
                       <div>
                         <h4 className="font-black text-sm">Salary Slips</h4>
                         <p className="text-xs text-slate-400 mt-1">Last 3 to 6 months (PDF)</p>
                       </div>
                       {uploadedDocs['salary_slip'] ? (
                         <button
                           onClick={() => removeDocument('salary_slip')}
                           className="px-4 py-2 bg-rose-100 text-rose-600 rounded-xl text-xs font-bold hover:bg-rose-200 transition"
                         >
                           Remove
                         </button>
                       ) : (
                         <label className="px-4 py-2 bg-blue-500 text-white rounded-xl text-xs font-bold cursor-pointer hover:bg-blue-600 transition">
                           Upload
                           <input
                             type="file"
                             accept=".pdf"
                             className="hidden"
                             onChange={(e) => handleFileUpload('salary_slip', e.target.files[0])}
                           />
                         </label>
                       )}
                     </div>
                     {uploadedDocs['salary_slip'] && (
                       <div className="flex items-center gap-2 text-xs text-emerald-600 font-medium">
                         <CheckCircle size={14} />
                         {uploadedDocs['salary_slip'].name}
                       </div>
                     )}
                   </div>

                   {/* ITR */}
                   <div className="p-6 bg-blue-50 rounded-2xl border-2 border-blue-100">
                     <div className="flex items-center justify-between mb-3">
                       <div>
                         <h4 className="font-black text-sm">Income Tax Returns (ITR)</h4>
                         <p className="text-xs text-slate-400 mt-1">Last 2 years (PDF)</p>
                       </div>
                       {uploadedDocs['itr'] ? (
                         <button
                           onClick={() => removeDocument('itr')}
                           className="px-4 py-2 bg-rose-100 text-rose-600 rounded-xl text-xs font-bold hover:bg-rose-200 transition"
                         >
                           Remove
                         </button>
                       ) : (
                         <label className="px-4 py-2 bg-blue-500 text-white rounded-xl text-xs font-bold cursor-pointer hover:bg-blue-600 transition">
                           Upload
                           <input
                             type="file"
                             accept=".pdf"
                             className="hidden"
                             onChange={(e) => handleFileUpload('itr', e.target.files[0])}
                           />
                         </label>
                       )}
                     </div>
                     {uploadedDocs['itr'] && (
                       <div className="flex items-center gap-2 text-xs text-emerald-600 font-medium">
                         <CheckCircle size={14} />
                         {uploadedDocs['itr'].name}
                       </div>
                     )}
                   </div>

                   {/* Form 16 */}
                   <div className="p-6 bg-blue-50 rounded-2xl border-2 border-blue-100">
                     <div className="flex items-center justify-between mb-3">
                       <div>
                         <h4 className="font-black text-sm">Form 16</h4>
                         <p className="text-xs text-slate-400 mt-1">TDS Certificate (PDF)</p>
                       </div>
                       {uploadedDocs['form_16'] ? (
                         <button
                           onClick={() => removeDocument('form_16')}
                           className="px-4 py-2 bg-rose-100 text-rose-600 rounded-xl text-xs font-bold hover:bg-rose-200 transition"
                         >
                           Remove
                         </button>
                       ) : (
                         <label className="px-4 py-2 bg-blue-500 text-white rounded-xl text-xs font-bold cursor-pointer hover:bg-blue-600 transition">
                           Upload
                           <input
                             type="file"
                             accept=".pdf"
                             className="hidden"
                             onChange={(e) => handleFileUpload('form_16', e.target.files[0])}
                           />
                         </label>
                       )}
                     </div>
                     {uploadedDocs['form_16'] && (
                       <div className="flex items-center gap-2 text-xs text-emerald-600 font-medium">
                         <CheckCircle size={14} />
                         {uploadedDocs['form_16'].name}
                       </div>
                     )}
                   </div>

                   {/* GST Certificate (Optional) */}
                   <div className="p-6 bg-slate-50 rounded-2xl border-2 border-dashed border-blue-200">
                     <div className="flex items-center justify-between mb-3">
                       <div>
                         <h4 className="font-black text-sm">GST Certificate (Optional)</h4>
                         <p className="text-xs text-slate-400 mt-1">Self-employed only (PDF)</p>
                       </div>
                       {uploadedDocs['gst_certificate'] ? (
                         <button
                           onClick={() => removeDocument('gst_certificate')}
                           className="px-4 py-2 bg-rose-100 text-rose-600 rounded-xl text-xs font-bold hover:bg-rose-200 transition"
                         >
                           Remove
                         </button>
                       ) : (
                         <label className="px-4 py-2 bg-slate-200 text-slate-600 rounded-xl text-xs font-bold cursor-pointer hover:bg-slate-300 transition">
                           Upload
                           <input
                             type="file"
                             accept=".pdf"
                             className="hidden"
                             onChange={(e) => handleFileUpload('gst_certificate', e.target.files[0])}
                           />
                         </label>
                       )}
                     </div>
                     {uploadedDocs['gst_certificate'] && (
                       <div className="flex items-center gap-2 text-xs text-emerald-600 font-medium">
                         <CheckCircle size={14} />
                         {uploadedDocs['gst_certificate'].name}
                       </div>
                     )}
                   </div>

                   {/* Trade License (Optional) */}
                   <div className="p-6 bg-slate-50 rounded-2xl border-2 border-dashed border-blue-200">
                     <div className="flex items-center justify-between mb-3">
                       <div>
                         <h4 className="font-black text-sm">Trade License (Optional)</h4>
                         <p className="text-xs text-slate-400 mt-1">Self-employed only (PDF)</p>
                       </div>
                       {uploadedDocs['trade_license'] ? (
                         <button
                           onClick={() => removeDocument('trade_license')}
                           className="px-4 py-2 bg-rose-100 text-rose-600 rounded-xl text-xs font-bold hover:bg-rose-200 transition"
                         >
                           Remove
                         </button>
                       ) : (
                         <label className="px-4 py-2 bg-slate-200 text-slate-600 rounded-xl text-xs font-bold cursor-pointer hover:bg-slate-300 transition">
                           Upload
                           <input
                             type="file"
                             accept=".pdf"
                             className="hidden"
                             onChange={(e) => handleFileUpload('trade_license', e.target.files[0])}
                           />
                         </label>
                       )}
                     </div>
                     {uploadedDocs['trade_license'] && (
                       <div className="flex items-center gap-2 text-xs text-emerald-600 font-medium">
                         <CheckCircle size={14} />
                         {uploadedDocs['trade_license'].name}
                       </div>
                     )}
                   </div>
                 </div>
               </div>
             )}

             {/* Health Documents */}
             {(shieldType === 'health' || shieldType === 'both') && (
               <div>
                 {shieldType === 'both' && <div className="border-t-2 border-slate-100 my-8" />}
                 <h3 className="text-lg font-black text-emerald-600 mb-4 flex items-center gap-2 sticky top-0 bg-white py-2">
                   <Activity size={20} /> Health Documents
                 </h3>
                 <div className="space-y-4">
                   {/* Diagnostic Reports */}
                   <div className="p-6 bg-emerald-50 rounded-2xl border-2 border-emerald-100">
                     <div className="flex items-center justify-between mb-3">
                       <div>
                         <h4 className="font-black text-sm">Diagnostic Reports</h4>
                         <p className="text-xs text-slate-400 mt-1">Blood Sugar, Cholesterol, HbA1c, BP (PDF)</p>
                       </div>
                       {uploadedDocs['diagnostic_report'] ? (
                         <button
                           onClick={() => removeDocument('diagnostic_report')}
                           className="px-4 py-2 bg-rose-100 text-rose-600 rounded-xl text-xs font-bold hover:bg-rose-200 transition"
                         >
                           Remove
                         </button>
                       ) : (
                         <label className="px-4 py-2 bg-emerald-500 text-white rounded-xl text-xs font-bold cursor-pointer hover:bg-emerald-600 transition">
                           Upload
                           <input
                             type="file"
                             accept=".pdf"
                             className="hidden"
                             onChange={(e) => handleFileUpload('diagnostic_report', e.target.files[0])}
                           />
                         </label>
                       )}
                     </div>
                     {uploadedDocs['diagnostic_report'] && (
                       <div className="flex items-center gap-2 text-xs text-emerald-600 font-medium">
                         <CheckCircle size={14} />
                         {uploadedDocs['diagnostic_report'].name}
                       </div>
                     )}
                   </div>

                   {/* Medical History */}
                   <div className="p-6 bg-emerald-50 rounded-2xl border-2 border-emerald-100">
                     <div className="flex items-center justify-between mb-3">
                       <div>
                         <h4 className="font-black text-sm">Medical History</h4>
                         <p className="text-xs text-slate-400 mt-1">Prescription history or medical records (PDF)</p>
                       </div>
                       {uploadedDocs['medical_history'] ? (
                         <button
                           onClick={() => removeDocument('medical_history')}
                           className="px-4 py-2 bg-rose-100 text-rose-600 rounded-xl text-xs font-bold hover:bg-rose-200 transition"
                         >
                           Remove
                         </button>
                       ) : (
                         <label className="px-4 py-2 bg-emerald-500 text-white rounded-xl text-xs font-bold cursor-pointer hover:bg-emerald-600 transition">
                           Upload
                           <input
                             type="file"
                             accept=".pdf"
                             className="hidden"
                             onChange={(e) => handleFileUpload('medical_history', e.target.files[0])}
                           />
                         </label>
                       )}
                     </div>
                     {uploadedDocs['medical_history'] && (
                       <div className="flex items-center gap-2 text-xs text-emerald-600 font-medium">
                         <CheckCircle size={14} />
                         {uploadedDocs['medical_history'].name}
                       </div>
                     )}
                   </div>

                   {/* Discharge Summaries (Optional) */}
                   <div className="p-6 bg-slate-50 rounded-2xl border-2 border-dashed border-emerald-200">
                     <div className="flex items-center justify-between mb-3">
                       <div>
                         <h4 className="font-black text-sm">Discharge Summaries (Optional)</h4>
                         <p className="text-xs text-slate-400 mt-1">Major hospitalizations in last 5 years (PDF)</p>
                       </div>
                       {uploadedDocs['discharge_summary'] ? (
                         <button
                           onClick={() => removeDocument('discharge_summary')}
                           className="px-4 py-2 bg-rose-100 text-rose-600 rounded-xl text-xs font-bold hover:bg-rose-200 transition"
                         >
                           Remove
                         </button>
                       ) : (
                         <label className="px-4 py-2 bg-slate-200 text-slate-600 rounded-xl text-xs font-bold cursor-pointer hover:bg-slate-300 transition">
                           Upload
                           <input
                             type="file"
                             accept=".pdf"
                             className="hidden"
                             onChange={(e) => handleFileUpload('discharge_summary', e.target.files[0])}
                           />
                         </label>
                       )}
                     </div>
                     {uploadedDocs['discharge_summary'] && (
                       <div className="flex items-center gap-2 text-xs text-emerald-600 font-medium">
                         <CheckCircle size={14} />
                         {uploadedDocs['discharge_summary'].name}
                       </div>
                     )}
                   </div>

                    {/* Proof of Age - 10th Marksheet */}
                    <div className="p-6 bg-emerald-50 rounded-2xl border-2 border-emerald-100">
                      <div className="flex items-center justify-between mb-3">
                        <div>
                          <h4 className="font-black text-sm">10th Marksheet</h4>
                          <p className="text-xs text-slate-400 mt-1">Proof of age (PDF/Image)</p>
                        </div>
                        {uploadedDocs['tenth_marksheet'] ? (
                          <button
                            onClick={() => removeDocument('tenth_marksheet')}
                            className="px-4 py-2 bg-rose-100 text-rose-600 rounded-xl text-xs font-bold hover:bg-rose-200 transition"
                          >
                            Remove
                          </button>
                        ) : (
                          <label className="px-4 py-2 bg-emerald-500 text-white rounded-xl text-xs font-bold cursor-pointer hover:bg-emerald-600 transition">
                            Upload
                            <input
                              type="file"
                              accept=".pdf,.jpg,.jpeg,.png"
                              className="hidden"
                              onChange={(e) => handleFileUpload('tenth_marksheet', e.target.files[0])}
                            />
                          </label>
                        )}
                      </div>
                      {uploadedDocs['tenth_marksheet'] && (
                        <div className="flex items-center gap-2 text-xs text-emerald-600 font-medium">
                          <CheckCircle size={14} />
                          {uploadedDocs['tenth_marksheet'].name}
                        </div>
                      )}
                    </div>

                 </div>
               </div>
             )}

             </div>

             {/* Info Box */}
             <div className="mb-8 p-6 bg-blue-50 border-2 border-dashed border-blue-200 rounded-2xl flex gap-4 items-start">
                <Info className="text-blue-500 shrink-0 mt-1" size={20} />
                <div>
                   <h4 className="text-xs font-black uppercase text-blue-500 tracking-widest mb-2">
                     Why These Documents?
                   </h4>
                   <p className="text-blue-700 text-xs font-medium leading-relaxed">
                     Our Extraction Agent scans these documents to calculate your Debt-to-Income ratio (loans) 
                     and identify biomarkers (health) automatically. No manual data entry required!
                   </p>
                </div>
             </div>

             {/* Upload Status */}
             {isUploading && (
               <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-2xl flex items-center gap-3">
                 <div className="w-5 h-5 border-3 border-yellow-500 border-t-transparent rounded-full animate-spin" />
                 <p className="text-yellow-700 text-sm font-medium">Uploading document...</p>
               </div>
             )}

             {/* Action Buttons - Sticky Footer */}
             <div className="flex gap-4 sticky bottom-0 bg-white pt-6">
               <button
                 onClick={() => setStep(3)}
                 className="flex-1 py-4 bg-slate-100 text-slate-600 font-black text-xs uppercase tracking-widest rounded-2xl hover:bg-slate-200 transition"
               >
                 Back
               </button>
               <button 
                 onClick={proceedWithDocuments}
                 disabled={getMissingDocs().length > 0 || isUploading}
                 className={`flex-2 py-4 text-white font-black rounded-2xl text-xs uppercase tracking-widest transition disabled:opacity-50 disabled:cursor-not-allowed ${
                   shieldType === 'loan' ? 'bg-blue-500 hover:bg-blue-600' : 
                   shieldType === 'health' ? 'bg-emerald-500 hover:bg-emerald-600' :
                   'bg-purple-500 hover:bg-purple-600'
                 }`}
                 style={{flex: 2}}
               >
                 {getMissingDocs().length > 0
                   ? `UPLOAD REQUIRED DOCUMENTS (${getMissingDocs().length} MISSING)`
                   : `START AGENTIC ANALYSIS (${Object.keys(uploadedDocs).length} DOCS)`}
               </button>
             </div>
          </div>
        )}

        {/* Step 5: Multi-Agent Processing */}
        {!showHITL && step === 5 && (
          <div className="bg-white rounded-[4rem] p-20 shadow-2xl text-center flex flex-col items-center">
             <div className={`w-20 h-20 border-8 ${
               shieldType === 'loan' ? 'border-blue-500' : 
               shieldType === 'health' ? 'border-emerald-500' :
               'border-purple-500'
             } border-t-transparent rounded-full animate-spin mb-10`} />
             <h2 className="text-2xl font-black mb-4 uppercase tracking-[0.2em] italic">Orchestrating...</h2>
             
             {workflowStatus && (
               <div className="space-y-4 w-full mt-8">
                 <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                   {workflowStatus.current_step || 'Processing...'}
                 </p>
                 <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                   <div className={`h-full ${
                     shieldType === 'loan' ? 'bg-blue-500' : 
                     shieldType === 'health' ? 'bg-emerald-500' :
                     'bg-purple-500'
                   } rounded-full transition-all duration-500`} style={{width: `${workflowStatus.progress || 0}%`}} />
                 </div>
                 {workflowStatus.message && (
                   <p className="text-xs text-slate-500 font-medium mt-4">{workflowStatus.message}</p>
                 )}
               </div>
             )}
          </div>
        )}


        {/* Step 6: Final Verdict */}
        {!showHITL && step === 6 && workflowResults && (
          <div className="bg-white rounded-[4rem] p-16 shadow-2xl text-center animate-in zoom-in-95 duration-1000 border-b-16 border-blue-50">
             <div className="inline-flex items-center gap-2 bg-emerald-100 text-emerald-600 px-8 py-3 rounded-full font-black text-[10px] uppercase tracking-widest mb-12 shadow-sm">
                <CheckCircle size={16} /> Verified by Daksha AI
             </div>
             
             {/* Loan Results */}
             {workflowResults.loan_prediction && (
               <div className="mb-12">
                 <h2 className="text-8xl font-black text-slate-900 mb-2 italic tracking-tighter uppercase">
                   {workflowResults.loan_prediction.approved ? 'APPROVED' : 'REJECTED'}
                 </h2>
                 <p className="text-slate-400 font-bold text-xs uppercase tracking-[0.4em] mb-4">Loan Decision</p>
                 <p className="text-2xl font-bold text-blue-600">
                   Confidence: {((workflowResults.loan_prediction.probability || 0) * 100).toFixed(1)}%
                 </p>
               </div>
             )}

             {/* Insurance Results */}
             {workflowResults.insurance_prediction && (
               <div className="mb-12">
                 <h2 className="text-8xl font-black text-slate-900 mb-2 italic tracking-tighter">
                   {formatCurrency(workflowResults.insurance_prediction.premium || 0)}
                 </h2>
                 <p className="text-slate-400 font-bold text-xs uppercase tracking-[0.4em]">Annual Premium</p>
               </div>
             )}

             {/* Transparency Explanation */}
             {workflowResults.explanation && (
               <div className="bg-[#F8FBFF] rounded-[3rem] p-12 text-left border border-blue-50 shadow-inner mt-12">
                  <h5 className="font-black text-xl flex items-center gap-4 mb-10 italic tracking-tight">
                     <BarChart3 size={28} className="text-blue-500" /> Transparent Reasoning Trace
                  </h5>
                  <div className="space-y-6">
                    <div className="p-6 bg-white rounded-2xl border border-slate-100">
                      <p className="text-sm text-slate-700 font-medium leading-relaxed">
                        {workflowResults.explanation.summary || workflowResults.explanation}
                      </p>
                    </div>

                    {/* Feature Contributions */}
                    {workflowResults.explanation.key_factors && (
                      <div className="space-y-4">
                        <h6 className="text-xs font-black uppercase text-slate-400 tracking-widest">Key Factors</h6>
                        {workflowResults.explanation.key_factors.map((factor, i) => (
                          <div key={i} className="p-4 bg-white rounded-xl border border-slate-100">
                            <div className="flex justify-between items-center mb-2">
                              <span className="text-xs font-bold text-slate-700">{factor.name}</span>
                              <span className={`text-xs font-black ${factor.impact > 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                                {factor.impact > 0 ? '+' : ''}{factor.impact}%
                              </span>
                            </div>
                            <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                              <div 
                                className={`h-full ${factor.impact > 0 ? 'bg-emerald-500' : 'bg-rose-500'} transition-all`}
                                style={{width: `${Math.abs(factor.impact)}%`}}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
               </div>
             )}
             
             {/* Advisor Insight */}
             {workflowResults.recommendation && (
               <div className="mt-12 p-8 bg-blue-500/5 border-2 border-dashed border-blue-500/20 rounded-[2.5rem] flex gap-6 text-left items-start">
                  <AlertCircle className="text-blue-500 shrink-0 mt-1" />
                  <div className="space-y-2">
                     <h6 className="text-[10px] font-black uppercase text-blue-500 tracking-widest">Advisor Insight</h6>
                     <p className="text-xs text-slate-500 font-medium leading-relaxed italic">
                        {workflowResults.recommendation}
                     </p>
                  </div>
               </div>
             )}

             <button onClick={goHome} className="mt-16 w-full py-8 bg-slate-900 text-white rounded-[2.5rem] font-black uppercase tracking-[0.2em] text-xs hover:bg-black transition shadow-2xl shadow-slate-300">
               Return to Lobby
             </button>
          </div>
        )}

      </main>
    </div>
  );
};

export default App;
