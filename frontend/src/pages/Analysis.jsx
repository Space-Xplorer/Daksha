import React, { useState, useEffect } from 'react';
import { useShield } from '../context/ShieldContext';
import { Network, Loader2 } from 'lucide-react';
import GlassCard from '../components/GlassCard';
import AgentStatus from '../components/AgentStatus';
import { createApplication, submitWorkflow, getWorkflowStatus, getWorkflowResults } from '../utils/api';

const Analysis = () => {
  const {
    setView,
    service,
    authToken,
    applicantData,
    uploadedDocuments,
    loanType,
    userData,
    applicationId,
    setApplicationId,
    requestId,
    setRequestId,
    workflowStatus,
    setWorkflowStatus,
    setWorkflowResult,
    workflowError,
    setWorkflowError
  } = useShield();
  const [step, setStep] = useState(0);
  const [isRunning, setIsRunning] = useState(false);

  const steps = [
    "KYC Agent: Verifying identity...",
    "Onboarding Agent: OCR extraction...",
    "Rules Agent: Checking underwriting rules...",
    "Fraud Agent: OCR fraud scan...",
    "Feature Engineering Agent: Deriving risk features...",
    "Compliance Agent: Regulatory checks...",
    "Underwriting Agent: Model inference...",
    "Verification Agent: Sanity checks...",
    "Transparency Agent: Explanation draft..."
  ];

  useEffect(() => {
    if (!authToken || !service || isRunning || workflowStatus?.status === 'completed' || workflowError) {
      return;
    }

    const runWorkflow = async () => {
      setIsRunning(true);
      setWorkflowError(null);

      try {
        let appId = applicationId;
        if (!appId) {
          const createPayload = {
            request_type: service,
            loan_type: service === 'loan' ? loanType : null,
            submitted_name: userData.name,
            submitted_dob: userData.dob,
            submitted_aadhaar: userData.aadhaar,
            applicant_data: applicantData,
            uploaded_documents: uploadedDocuments
          };

          const created = await createApplication(authToken, createPayload);
          appId = created.application.id;
          setApplicationId(appId);
        }

        try {
          const submitResponse = await submitWorkflow(authToken, appId);
          setRequestId(submitResponse.request_id || requestId);
        } catch (error) {
          const message = String(error.message || '').toLowerCase();
          if (!message.includes('already submitted')) {
            throw error;
          }
        }

        const poll = setInterval(async () => {
          try {
            const statusResponse = await getWorkflowStatus(authToken, appId);
            setWorkflowStatus(statusResponse);
            setStep((prev) => Math.min(prev + 1, steps.length - 1));

            if (statusResponse.status === 'completed') {
              clearInterval(poll);
              const results = await getWorkflowResults(authToken, appId);
              setWorkflowResult(results);
              setView('result');
            }
            if (statusResponse.status === 'failed') {
              clearInterval(poll);
              setWorkflowError(statusResponse.error || 'Workflow failed');
            }
          } catch (error) {
            clearInterval(poll);
            setWorkflowError(error.message || 'Failed to fetch workflow status');
          }
        }, 2000);
      } catch (error) {
        setWorkflowError(error.message || 'Workflow initialization failed');
      } finally {
        setIsRunning(false);
      }
    };

    runWorkflow();
  }, [
    authToken,
    service,
    loanType,
    applicantData,
    uploadedDocuments,
    userData,
    applicationId,
    requestId,
    setApplicationId,
    setRequestId,
    setWorkflowStatus,
    setWorkflowResult,
    setWorkflowError,
    setView,
    steps.length,
    isRunning,
    workflowStatus,
    workflowError
  ]);

  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center px-6 text-center">
      <div className="relative w-32 h-32 mb-12">
        <div className="absolute inset-0 border-8 border-[#4B0082]/5 rounded-full" />
        <div className="absolute inset-0 border-8 border-[#F4C2C2] border-t-transparent rounded-full animate-spin" />
        <div className="absolute inset-0 flex items-center justify-center text-[#4B0082]"><Network size={40} /></div>
      </div>
      <h2 className="text-2xl font-black text-[#4B0082] italic uppercase tracking-[0.2em] mb-4">Agentic Orchestration</h2>
      <div className="bg-white p-6 rounded-4xl shadow-sm border border-slate-100 min-w-[320px]">
        <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Active Task</p>
        <p className="text-sm font-black text-[#4B0082] animate-pulse">{steps[step]}</p>
      </div>
      {workflowError ? (
        <div className="mt-6 text-red-500 text-xs font-bold uppercase tracking-widest">
          {workflowError}
        </div>
      ) : null}
      <GlassCard className="p-12 max-w-md mx-auto">
        <h4 className="text-center font-black text-[#4B0082] mb-8 uppercase italic tracking-widest">
          Orchestration Pulse
        </h4>
        <div className="space-y-4">
          <AgentStatus name="KYC Agent" status="complete" />
          <AgentStatus name="Onboarding Agent" status="loading" />
          <AgentStatus name="Rules Agent" status="waiting" />
        </div>
      </GlassCard>
    </div>
  );
};

export default Analysis;