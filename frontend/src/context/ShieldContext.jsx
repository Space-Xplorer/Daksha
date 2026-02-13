import React, { createContext, useState, useContext } from 'react';

const ShieldContext = createContext();

export const ShieldProvider = ({ children }) => {
  const [view, setView] = useState('landing');
  const [service, setService] = useState(null); // 'loan' or 'health'
  const [userData, setUserData] = useState({ aadhaar: "", name: "Spoorthy" });
  const [uploadedDocs, setUploadedDocs] = useState({});

  return (
    <ShieldContext.Provider value={{ 
      view, setView, service, setService, 
      userData, setUserData, uploadedDocs, setUploadedDocs 
    }}>
      {children}
    </ShieldContext.Provider>
  );
};

export const useShield = () => useContext(ShieldContext);