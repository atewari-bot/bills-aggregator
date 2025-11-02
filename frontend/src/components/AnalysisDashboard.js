import React from 'react';
import './AnalysisDashboard.css';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar, Doughnut, Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const AnalysisDashboard = ({ analysis, summary }) => {
  if (!analysis || !summary) return null;

  // Prepare data for shop spending chart
  const shopData = {
    labels: analysis.shops?.map((s) => s.shop_name) || [],
    datasets: [
      {
        label: 'Total Spent ($)',
        data: analysis.shops?.map((s) => s.total_spent) || [],
        backgroundColor: 'rgba(102, 126, 234, 0.8)',
        borderColor: 'rgba(102, 126, 234, 1)',
        borderWidth: 1,
      },
    ],
  };

  // Prepare data for category spending chart
  const categoryData = {
    labels: analysis.categories?.map((c) => c.category) || [],
    datasets: [
      {
        label: 'Total Spent ($)',
        data: analysis.categories?.map((c) => c.total_spent) || [],
        backgroundColor: [
          'rgba(255, 99, 132, 0.8)',
          'rgba(54, 162, 235, 0.8)',
          'rgba(255, 206, 86, 0.8)',
          'rgba(75, 192, 192, 0.8)',
          'rgba(153, 102, 255, 0.8)',
          'rgba(255, 159, 64, 0.8)',
          'rgba(199, 199, 199, 0.8)',
        ],
        borderWidth: 2,
      },
    ],
  };

  // Prepare data for top items chart
  const topItemsData = {
    labels: analysis.top_items?.slice(0, 10).map((i) => i.item_name) || [],
    datasets: [
      {
        label: 'Total Spent ($)',
        data: analysis.top_items?.slice(0, 10).map((i) => i.total_spent) || [],
        backgroundColor: 'rgba(118, 75, 162, 0.8)',
        borderColor: 'rgba(118, 75, 162, 1)',
        borderWidth: 1,
      },
    ],
  };

  return (
    <div className="analysis-dashboard">
      <h2>📊 Monthly Analysis</h2>

      <div className="summary-cards">
        <div className="summary-card">
          <div className="card-icon">💰</div>
          <div className="card-content">
            <div className="card-label">Total Spent</div>
            <div className="card-value">${summary.total_spent?.toFixed(2) || '0.00'}</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon">🧾</div>
          <div className="card-content">
            <div className="card-label">Total Bills</div>
            <div className="card-value">{summary.total_bills || 0}</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon">🏪</div>
          <div className="card-content">
            <div className="card-label">Unique Shops</div>
            <div className="card-value">{summary.unique_shops || 0}</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon">📦</div>
          <div className="card-content">
            <div className="card-label">Total Items</div>
            <div className="card-value">{summary.total_items || 0}</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon">📊</div>
          <div className="card-content">
            <div className="card-label">Avg Bill Amount</div>
            <div className="card-value">${summary.avg_bill_amount?.toFixed(2) || '0.00'}</div>
          </div>
        </div>
      </div>

      <div className="charts-grid">
        <div className="chart-card">
          <h3>Spending by Shop</h3>
          {analysis.shops && analysis.shops.length > 0 ? (
            <Bar
              data={shopData}
              options={{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                  legend: {
                    display: false,
                  },
                },
              }}
            />
          ) : (
            <div className="no-data">No shop data available</div>
          )}
        </div>

        <div className="chart-card">
          <h3>Spending by Category</h3>
          {analysis.categories && analysis.categories.length > 0 ? (
            <Doughnut
              data={categoryData}
              options={{
                responsive: true,
                maintainAspectRatio: true,
              }}
            />
          ) : (
            <div className="no-data">No category data available</div>
          )}
        </div>

        <div className="chart-card full-width">
          <h3>Top Items by Spending</h3>
          {analysis.top_items && analysis.top_items.length > 0 ? (
            <Bar
              data={topItemsData}
              options={{
                responsive: true,
                maintainAspectRatio: true,
                indexAxis: 'y',
                plugins: {
                  legend: {
                    display: false,
                  },
                },
              }}
            />
          ) : (
            <div className="no-data">No item data available</div>
          )}
        </div>
      </div>

      <div className="tables-grid">
        <div className="table-card">
          <h3>Shop Breakdown</h3>
          <table>
            <thead>
              <tr>
                <th>Shop Name</th>
                <th>Bills</th>
                <th>Total Spent</th>
              </tr>
            </thead>
            <tbody>
              {analysis.shops && analysis.shops.length > 0 ? (
                analysis.shops.map((shop, index) => (
                  <tr key={index}>
                    <td>{shop.shop_name}</td>
                    <td>{shop.bill_count}</td>
                    <td>${shop.total_spent.toFixed(2)}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="3">No shop data available</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="table-card">
          <h3>Category Breakdown</h3>
          <table>
            <thead>
              <tr>
                <th>Category</th>
                <th>Items</th>
                <th>Total Spent</th>
              </tr>
            </thead>
            <tbody>
              {analysis.categories && analysis.categories.length > 0 ? (
                analysis.categories.map((category, index) => (
                  <tr key={index}>
                    <td>{category.category}</td>
                    <td>{category.item_count}</td>
                    <td>${category.total_spent.toFixed(2)}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="3">No category data available</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AnalysisDashboard;

