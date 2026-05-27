import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { emissionRecordService } from '../api/services'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

export default function ReviewDashboard() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user } = useAuthStore()
  const [filters, setFilters] = useState({
    status: '',
    scope: '',
    suspicious: '',
    search: '',
  })
  const [selectedRecords, setSelectedRecords] = useState([])

  const { data: records, isLoading } = useQuery({
    queryKey: ['emission-records', filters],
    queryFn: () => emissionRecordService.getAll(filters).then(res => res.data.results || res.data),
  })

  const approveMutation = useMutation({
    mutationFn: (id) => emissionRecordService.approve(id),
    onSuccess: () => {
      queryClient.invalidateQueries(['emission-records'])
    },
  })

  const rejectMutation = useMutation({
    mutationFn: ({ id, notes }) => emissionRecordService.reject(id, notes),
    onSuccess: () => {
      queryClient.invalidateQueries(['emission-records'])
    },
  })

  const bulkApproveMutation = useMutation({
    mutationFn: (recordIds) => emissionRecordService.bulkApprove(recordIds),
    onSuccess: () => {
      queryClient.invalidateQueries(['emission-records'])
      setSelectedRecords([])
      alert('Records approved successfully')
    },
  })

  const handleApprove = (id) => {
    if (confirm('Approve this record?')) {
      approveMutation.mutate(id)
    }
  }

  const handleReject = (id) => {
    const notes = prompt('Enter rejection reason:')
    if (notes) {
      rejectMutation.mutate({ id, notes })
    }
  }

  const handleBulkApprove = () => {
    if (selectedRecords.length === 0) {
      alert('No records selected')
      return
    }
    if (confirm(`Approve ${selectedRecords.length} records?`)) {
      bulkApproveMutation.mutate(selectedRecords)
    }
  }

  const toggleSelectRecord = (id) => {
    setSelectedRecords(prev =>
      prev.includes(id) ? prev.filter(r => r !== id) : [...prev, id]
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Review Dashboard</h1>
          <p className="mt-1 text-sm text-gray-600">
            Review and approve emission records before audit lock
          </p>
        </div>
        {user?.role !== 'viewer' && selectedRecords.length > 0 && (
          <button
            onClick={handleBulkApprove}
            className="btn-primary"
          >
            Approve Selected ({selectedRecords.length})
          </button>
        )}
      </div>

      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <select
            value={filters.status}
            onChange={(e) => setFilters({ ...filters, status: e.target.value })}
            className="input"
          >
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
            <option value="flagged">Flagged</option>
          </select>

          <select
            value={filters.scope}
            onChange={(e) => setFilters({ ...filters, scope: e.target.value })}
            className="input"
          >
            <option value="">All Scopes</option>
            <option value="scope_1">Scope 1</option>
            <option value="scope_2">Scope 2</option>
            <option value="scope_3">Scope 3</option>
          </select>

          <select
            value={filters.suspicious}
            onChange={(e) => setFilters({ ...filters, suspicious: e.target.value })}
            className="input"
          >
            <option value="">All Records</option>
            <option value="true">Suspicious Only</option>
          </select>

          <input
            type="text"
            placeholder="Search..."
            value={filters.search}
            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            className="input"
          />
        </div>

        {isLoading ? (
          <div className="text-center py-8 text-gray-500">Loading records...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  {user?.role !== 'viewer' && (
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      <input
                        type="checkbox"
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedRecords(records?.map(r => r.id) || [])
                          } else {
                            setSelectedRecords([])
                          }
                        }}
                      />
                    </th>
                  )}
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Scope</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Category</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Activity</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Quantity</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Emissions</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {records?.map((record) => (
                  <tr key={record.id} className={record.suspicious_flag ? 'bg-yellow-50' : ''}>
                    {user?.role !== 'viewer' && (
                      <td className="px-4 py-4">
                        <input
                          type="checkbox"
                          checked={selectedRecords.includes(record.id)}
                          onChange={() => toggleSelectRecord(record.id)}
                          disabled={record.locked_for_audit}
                        />
                      </td>
                    )}
                    <td className="px-4 py-4 text-sm text-gray-900">
                      {new Date(record.activity_date).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-4">
                      <span className={`badge ${getScopeColor(record.scope)}`}>
                        {record.scope.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-sm text-gray-900">{record.category}</td>
                    <td className="px-4 py-4 text-sm text-gray-900">{record.activity_type}</td>
                    <td className="px-4 py-4 text-sm text-gray-900">
                      {parseFloat(record.quantity).toFixed(2)} {record.normalized_unit}
                    </td>
                    <td className="px-4 py-4 text-sm text-gray-900">
                      {record.emission_value ? `${parseFloat(record.emission_value).toFixed(2)} kg CO2e` : 'N/A'}
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex flex-col space-y-1">
                        <span className={`badge ${getStatusColor(record.status)}`}>
                          {record.status}
                        </span>
                        {record.suspicious_flag && (
                          <span className="badge bg-yellow-100 text-yellow-800">⚠ Suspicious</span>
                        )}
                        {record.locked_for_audit && (
                          <span className="badge bg-gray-100 text-gray-800">🔒 Locked</span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-4 text-sm space-x-2">
                      <button
                        onClick={() => navigate(`/records/${record.id}`)}
                        className="text-blue-600 hover:text-blue-800"
                      >
                        View
                      </button>
                      {user?.role !== 'viewer' && !record.locked_for_audit && (
                        <>
                          {record.status !== 'approved' && (
                            <button
                              onClick={() => handleApprove(record.id)}
                              className="text-green-600 hover:text-green-800"
                            >
                              Approve
                            </button>
                          )}
                          {record.status !== 'rejected' && (
                            <button
                              onClick={() => handleReject(record.id)}
                              className="text-red-600 hover:text-red-800"
                            >
                              Reject
                            </button>
                          )}
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

function getScopeColor(scope) {
  const colors = {
    scope_1: 'bg-red-100 text-red-800',
    scope_2: 'bg-orange-100 text-orange-800',
    scope_3: 'bg-green-100 text-green-800',
  }
  return colors[scope] || 'bg-gray-100 text-gray-800'
}

function getStatusColor(status) {
  const colors = {
    pending: 'bg-yellow-100 text-yellow-800',
    approved: 'bg-green-100 text-green-800',
    rejected: 'bg-red-100 text-red-800',
    flagged: 'bg-orange-100 text-orange-800',
  }
  return colors[status] || 'bg-gray-100 text-gray-800'
}
