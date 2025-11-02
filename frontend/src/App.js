import React, { useState, useEffect } from 'react';
import './App.css';
import UploadSection from './components/UploadSection';
import AnalysisDashboard from './components/AnalysisDashboard';
import BillsList from './components/BillsList';
import { fetchBills, fetchMonthlyAnalysis, fetchSummary, deleteAllBills } from './services/api';

function App() {
  const [bills, setBills] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const [summary, setSummary] = useState(null);
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, [selectedMonth, selectedYear]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [billsData, analysisData, summaryData] = await Promise.all([
        fetchBills(selectedMonth, selectedYear),
        fetchMonthlyAnalysis(selectedMonth, selectedYear),
        fetchSummary(selectedMonth, selectedYear)
      ]);
      setBills(billsData.bills || []);
      setAnalysis(analysisData);
      setSummary(summaryData);
    } catch (error) {
      console.error('Error loading data:', error);
      // Set empty data on error to prevent white screen
      setBills([]);
      setAnalysis(null);
      setSummary(null);
    } finally {
      setLoading(false);
    }
  };

  const handleUploadSuccess = () => {
    loadData();
  };

  const handleClearDatabase = async () => {
    if (!window.confirm('⚠️ Are you sure you want to delete ALL bills from the database? This action cannot be undone.')) {
      return;
    }
    
    try {
      const result = await deleteAllBills();
      alert(`✅ Database cleared successfully!\n\nDeleted:\n- ${result.bills_deleted} bills\n- ${result.line_items_deleted} line items`);
      
      // Reset state
      setBills([]);
      setAnalysis(null);
      setSummary(null);
    } catch (error) {
      alert(`❌ Error clearing database: ${error.response?.data?.error || error.message}`);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>📊 Bills Analyzer & Aggregator</h1>
        <p>Upload bills, analyze spending, and track expenses</p>
      </header>

      <div className="container">
        <div className="header-actions">
          <UploadSection onUploadSuccess={handleUploadSuccess} />
          <button 
            className="clear-db-button" 
            onClick={handleClearDatabase}
            title="Delete all bills from the database"
          >
            🗑️ Clear Database
          </button>
        </div>

        <div className="filters-section">
          <div className="filter-group">
            <label htmlFor="month">Month:</label>
            <select
              id="month"
              value={selectedMonth}
              onChange={(e) => setSelectedMonth(parseInt(e.target.value))}
            >
              {[...Array(12)].map((_, i) => {
                const month = i + 1;
                return (
                  <option key={month} value={month}>
                    {new Date(2000, month - 1).toLocaleString('default', { month: 'long' })}
                  </option>
                );
              })}
            </select>
          </div>

          <div className="filter-group">
            <label htmlFor="year">Year:</label>
            <select
              id="year"
              value={selectedYear}
              onChange={(e) => setSelectedYear(parseInt(e.target.value))}
            >
              {[...Array(5)].map((_, i) => {
                const year = new Date().getFullYear() - i;
                return <option key={year} value={year}>{year}</option>;
              })}
            </select>
          </div>
        </div>

        {loading ? (
          <div className="loading">Loading...</div>
        ) : (
          <>
            {summary && analysis && <AnalysisDashboard analysis={analysis} summary={summary} />}
            <BillsList bills={bills} />
          </>
        )}
      </div>
    </div>
  );
}

export default App;

