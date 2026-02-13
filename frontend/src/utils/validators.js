/**
 * Input validation utilities
 */

export const validators = {
  /**
   * Validate Aadhaar number (12 digits)
   */
  aadhaar: (value) => {
    const cleaned = value.replace(/\s/g, '');
    return /^\d{12}$/.test(cleaned);
  },

  /**
   * Validate email
   */
  email: (value) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
  },

  /**
   * Validate password (min 6 characters)
   */
  password: (value) => {
    return value.length >= 6;
  },

  /**
   * Validate positive number
   */
  positiveNumber: (value) => {
    const num = parseFloat(value);
    return !isNaN(num) && num > 0;
  },

  /**
   * Validate BMI range (10-50)
   */
  bmi: (value) => {
    const num = parseFloat(value);
    return !isNaN(num) && num >= 10 && num <= 50;
  },

  /**
   * Validate age range (18-100)
   */
  age: (value) => {
    const num = parseInt(value);
    return !isNaN(num) && num >= 18 && num <= 100;
  },

  /**
   * Validate CIBIL score (300-900)
   */
  cibilScore: (value) => {
    const num = parseInt(value);
    return !isNaN(num) && num >= 300 && num <= 900;
  },
};

/**
 * Format Aadhaar number with spaces (XXXX XXXX XXXX)
 */
export const formatAadhaar = (value) => {
  const cleaned = value.replace(/\s/g, '');
  const match = cleaned.match(/(\d{1,4})(\d{0,4})(\d{0,4})/);
  if (match) {
    return [match[1], match[2], match[3]].filter(Boolean).join(' ');
  }
  return value;
};

/**
 * Format currency (Indian Rupees)
 */
export const formatCurrency = (value) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value);
};

/**
 * Format percentage
 */
export const formatPercentage = (value) => {
  return `${(value * 100).toFixed(1)}%`;
};
