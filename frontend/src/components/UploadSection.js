import React, { useState } from 'react';
import './UploadSection.css';
import { uploadBillImage, uploadBillCSV } from '../services/api';

const UploadSection = ({ onUploadSuccess }) => {
  const [uploading, setUploading] = useState(false);
  const [uploadType, setUploadType] = useState('image');
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploading(true);
    setMessage(null);
    setError(null);

    try {
      let response;
      if (uploadType === 'image') {
        response = await uploadBillImage(file);
      } else {
        response = await uploadBillCSV(file);
      }

      setMessage(
        uploadType === 'image'
          ? `Successfully uploaded bill! Processed ${response.line_items?.length || 0} line items.`
          : `Successfully uploaded CSV! Created ${response.bills_created || 0} bills.`
      );

      if (onUploadSuccess) {
        onUploadSuccess();
      }

      // Reset file input
      event.target.value = '';
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to upload file. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="upload-section">
      <div className="upload-header">
        <h2>Upload Bills</h2>
        <div className="upload-type-selector">
          <button
            className={uploadType === 'image' ? 'active' : ''}
            onClick={() => setUploadType('image')}
          >
            📷 Image
          </button>
          <button
            className={uploadType === 'csv' ? 'active' : ''}
            onClick={() => setUploadType('csv')}
          >
            📄 CSV
          </button>
        </div>
      </div>

      <div className="upload-area">
        <input
          type="file"
          id="file-upload"
          accept={uploadType === 'image' ? 'image/*' : '.csv'}
          onChange={handleFileChange}
          disabled={uploading}
          style={{ display: 'none' }}
        />
        <label htmlFor="file-upload" className="upload-button">
          {uploading ? (
            <span>Uploading...</span>
          ) : (
            <span>
              {uploadType === 'image'
                ? '📷 Click to upload bill image'
                : '📄 Click to upload CSV file'}
            </span>
          )}
        </label>

        <div className="upload-info">
          {uploadType === 'image' ? (
            <p>Upload a photo of your bill. We'll automatically scan and extract line items.</p>
          ) : (
            <p>
              Upload a CSV file with columns: shop_name, date (YYYY-MM-DD), total_amount, line_items (format: "Item1,quantity,price,category|Item2,quantity,price,category")
            </p>
          )}
        </div>

        {message && <div className="message success">{message}</div>}
        {error && <div className="message error">{error}</div>}
      </div>
    </div>
  );
};

export default UploadSection;

