import { createContext, useContext, useState } from 'react';
import { applicationsService } from '../services/applications';
import { workflowService } from '../services/workflow';

const ApplicationContext = createContext(null);

export const ApplicationProvider = ({ children }) => {
  const [currentApplication, setCurrentApplication] = useState(null);
  const [applications, setApplications] = useState([]);
  const [workflowStatus, setWorkflowStatus] = useState(null);
  const [workflowResults, setWorkflowResults] = useState(null);

  // Create new application
  const createApplication = async (data) => {
    const app = await applicationsService.create(data);
    setCurrentApplication(app);
    return app;
  };

  // Update application
  const updateApplication = async (appId, data) => {
    const app = await applicationsService.update(appId, data);
    setCurrentApplication(app);
    return app;
  };

  // Get application by ID
  const getApplication = async (appId) => {
    const app = await applicationsService.getById(appId);
    setCurrentApplication(app);
    return app;
  };

  // Get all applications
  const getAllApplications = async () => {
    const apps = await applicationsService.getAll();
    setApplications(apps);
    return apps;
  };

  // Submit workflow
  const submitWorkflow = async (appId) => {
    const result = await workflowService.submit(appId);
    return result;
  };

  // Poll workflow status
  const pollWorkflow = async (appId, onProgress) => {
    try {
      const results = await workflowService.pollStatus(appId, (status) => {
        setWorkflowStatus(status);
        if (onProgress) onProgress(status);
      });

      if (results.status === 'hitl_pending') {
        return results;
      }

      setWorkflowResults(results);
      return results;
    } catch (error) {
      console.error('Workflow polling error:', error);
      throw error;
    }
  };

  // Get HITL data
  const getHITLData = async (appId) => {
    const data = await workflowService.getHITL(appId);
    return data;
  };

  // Approve HITL
  const approveHITL = async (appId, corrections) => {
    const result = await workflowService.approveHITL(appId, corrections);
    return result;
  };

  // Reset current application
  const resetApplication = () => {
    setCurrentApplication(null);
    setWorkflowStatus(null);
    setWorkflowResults(null);
  };

  const value = {
    currentApplication,
    applications,
    workflowStatus,
    workflowResults,
    createApplication,
    updateApplication,
    getApplication,
    getAllApplications,
    submitWorkflow,
    pollWorkflow,
    getHITLData,
    approveHITL,
    resetApplication,
  };

  return (
    <ApplicationContext.Provider value={value}>
      {children}
    </ApplicationContext.Provider>
  );
};

export const useApplication = () => {
  const context = useContext(ApplicationContext);
  if (!context) {
    throw new Error('useApplication must be used within ApplicationProvider');
  }
  return context;
};
