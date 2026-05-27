import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { dataSourceService } from '../api/services'
import { useAuthStore } from '../store/authStore'

export default function UploadCenter() {
  const queryClient = useQueryClient()
  const { user } = useAuthStore()
  const [selectedFile, setSelectedFile] = useState(null)
  const [sourceType, setSourceType] = useState('sap')
  const [uploadMethod, setUploadMethod] = useState('csv')

  const { data: uploads } = useQuery({
    queryKey: ['data-sources'],
    queryFn: () => dataSourceService.getAll().then(res => res.data.results || res.data),
  })

  const uploadMutation = useMutation({
    mutationFn: (formData) => dataSourceService.create(formData),
    onSuccess: () => {
      queryClient.invalidateQueries(['data-sources'])
      setSelectedFile(null)
      alert('File uploaded successfully! Processing will begin shortly.')
    },
    onError: (error) => {
      alert('Upload failed: ' + (error.response?.data?.detail || error.message))
    },
  })

  const handleFileChange = (e) => {
    setSelectedFile(e.target.files[0])
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    
    if (!selectedFile) {
      alert('Please select a file')
      return
    }

    const formData = new FormData()
    formData.append('file_path', selectedFile)
    formData.append('source_type', sourceType)
    formData.append('upload_method', uploadMethod)
    formData.append('file_name', selectedFile.name)
    formData.append('company', user.company)

    uploadMutation.mutate(formData)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Upload Center</h1>
        <p className="mt-1 text-sm text-gray-600">
          Upload ESG data from SAP, utility portals, or travel platforms
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Upload New Data</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Data Source Type
              </label>
              <select
                value={sourceType}
                onChange={(e) => setSourceType(e.target.value)}
                className="input"
              >
                <option value="sap">SAP Export (Fuel & Procurement)</option>
                <option value="utility">Utility Data (Electricity)</option>
                <option value="travel">Corporate Travel</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Upload Method
              </label>
              <select
                value={uploadMethod}
                onChange={(e) => setUploadMethod(e.target.value)}
                className="input"
              >
                <option value="csv">CSV Upload</option>
                <option value="api">API Integration</option>
                <option value="manual">Manual Entry</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select File
              </label>
              <input
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                className="input"
              />
              {selectedFile && (
                <p className="mt-2 text-sm text-gray-600">
                  Selected: {selectedFile.name}
                </p>
              )}
            </div>

            <button
              type="submit"
              disabled={uploadMutation.isPending}
              className="w-full btn-primary disabled:opacity-50"
            >
              {uploadMutation.isPending ? 'Uploading...' : 'Upload File'}
            </button>
          </form>

          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <h3 className="text-sm font-medium text-blue-900 mb-2">Expected Format</h3>
            <p className="text-xs text-blue-700">
              {sourceType === 'sap' && 'Columns: Plant_Code, Material_Description, Quantity, Unit, Posting_Date, Vendor'}
              {sourceType === 'utility' && 'Columns: Meter_ID, Facility_Name, Billing_Period_Start, Total_kWh'}
              {sourceType === 'travel' && 'Columns: Traveler_Name, Travel_Date, Transport_Type, Origin, Destination'}
            </p>
          </div>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Upload History</h2>
          <div className="space-y-3">
            {uploads?.map((upload) => (
              <div key={upload.id} className="p-4 bg-gray-50 rounded-lg">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">{upload.file_name}</p>
                    <p className="text-xs text-gray-600 mt-1">
                      {upload.source_type} • Uploaded {new Date(upload.uploaded_at).toLocaleString()}
                    </p>
                    <div className="mt-2 flex items-center space-x-4 text-xs text-gray-600">
                      <span>Total: {upload.total_rows}</span>
                      <span>Processed: {upload.processed_rows}</span>
                      <span>Failed: {upload.failed_rows}</span>
                      <span>Success: {upload.success_rate}%</span>
                    </div>
                  </div>
                  <span className={`badge ${getStatusColor(upload.processing_status)}`}>
                    {upload.processing_status}
                  </span>
                </div>
                {upload.error_message && (
                  <p className="mt-2 text-xs text-red-600">{upload.error_message}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function getStatusColor(status) {
  const colors = {
    pending: 'bg-yellow-100 text-yellow-800',
    processing: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
  }
  return colors[status] || 'bg-gray-100 text-gray-800'
}
