import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const uploadBillImage = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post('/bills/upload-image', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  
  return response.data;
};

export const uploadBillCSV = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post('/bills/upload-csv', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  
  return response.data;
};

export const fetchBills = async (month = null, year = null) => {
  const params = {};
  if (month) params.month = month;
  if (year) params.year = year;
  
  const response = await api.get('/bills', { params });
  return response.data;
};

export const fetchMonthlyAnalysis = async (month, year) => {
  const response = await api.get('/analysis/monthly', {
    params: { month, year },
  });
  return response.data;
};

export const fetchSummary = async (month = null, year = null) => {
  const params = {};
  if (month) params.month = month;
  if (year) params.year = year;
  
  const response = await api.get('/analysis/summary', { params });
  return response.data;
};

export default api;

