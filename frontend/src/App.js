import React, { useState, useEffect } from 'react';
import './App.css';
import UploadSection from './components/UploadSection';
import AnalysisDashboard from './components/AnalysisDashboard';
import BillsList from './components/BillsList';
import { fetchBills, fetchMonthlyAnalysis, fetchSummary } from './services/api';

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
    } finally {
      setLoading(false);
    }
  };

  const handleUploadSuccess = () => {
    loadData();
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>📊 Bills Analyzer & Aggregator</h1>
        <p>Upload bills, analyze spending, and track expenses</p>
      </header>

      <div className="container">
        <UploadSection onUploadSuccess={handleUploadSuccess} />

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
            {summary && <AnalysisDashboard analysis={analysis} summary={summary} />}
            <BillsList bills={bills} />
          </>
        )}
      </div>
    </div>
  );
}

export default App;

