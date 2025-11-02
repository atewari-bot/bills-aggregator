import React from 'react';
import './BillsList.css';

const BillsList = ({ bills }) => {
  if (!bills || bills.length === 0) {
    return (
      <div className="bills-list">
        <h2>📋 Bills</h2>
        <div className="no-bills">No bills found for the selected period.</div>
      </div>
    );
  }

  return (
    <div className="bills-list">
      <h2>📋 Bills ({bills.length})</h2>
      <div className="bills-grid">
        {bills.map((bill) => (
          <div key={bill.id} className="bill-card">
            <div className="bill-header">
              <div className="bill-shop">{bill.shop_name}</div>
              <div className="bill-date">
                {new Date(bill.date).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric',
                })}
              </div>
            </div>

            <div className="bill-total">
              Total: <span>${bill.total_amount.toFixed(2)}</span>
            </div>

            <div className="bill-type-badge">
              {bill.upload_type === 'image' ? '📷 Image' : '📄 CSV'}
            </div>

            {bill.line_items && bill.line_items.length > 0 && (
              <div className="bill-items">
                <div className="items-header">Line Items ({bill.line_items.length})</div>
                <div className="items-list">
                  {bill.line_items.map((item, index) => (
                    <div key={index} className="item-row">
                      <div className="item-name">{item.name}</div>
                      <div className="item-details">
                        {item.quantity > 1 && (
                          <span className="item-quantity">{item.quantity}x</span>
                        )}
                        <span className="item-price">${item.price.toFixed(2)}</span>
                        <span className="item-category">{item.category}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default BillsList;

