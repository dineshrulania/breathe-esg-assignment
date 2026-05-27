import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { emissionRecordService, auditLogService } from '../api/services'

export default function RecordDetails() {
  const { id } = useParams()
  const navigate = useNavigate()

  const { data: record, isLoading } = useQuery({
    queryKey: ['emission-record', id],
    queryFn: () => emissionRecordService.getById(id).then(res => res.data),
  })

  const { data: auditLogs } = useQuery({
    queryKey: ['audit-logs', id],
    queryFn: () => auditLogService.getAll({ record_id: id }).then(res => res.data.results || res.data),
  })

  if (isLoading) {
    return <div className="text-center py-8">Loading...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/review')}
          className="text-gray-600 hover:text-gray-900"
        >
          ← Back to Review
        </button>
      </div>

      <div className="card">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Record Details</h1>
            <p className="text-sm text-gray-600 mt-1">ID: {record?.id}</p>
          </div>
          <div className="flex flex-col space-y-2">
            <span className={`badge ${getStatusColor(record?.status)}`}>
              {record?.status}
            </span>
            {record?.suspicious_flag && (
              <span className="badge bg-yellow-100 text-yellow-800">⚠ Suspicious</span>
            )}
            {record?.locked_for_audit && (
              <span className="badge bg-gray-100 text-gray-800">🔒 Locked</span>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <DetailSection title="Activity Information">
            <DetailRow label="Activity Date" value={new Date(record?.activity_date).toLocaleDateString()} />
            <DetailRow label="Scope" value={record?.scope?.replace('_', ' ')} />
            <DetailRow label="Category" value={record?.category} />
            <DetailRow label="Activity Type" value={record?.activity_type} />
          </DetailSection>

          <DetailSection title="Quantity & Emissions">
            <DetailRow label="Quantity" value={`${parseFloat(record?.quantity).toFixed(2)} ${record?.normalized_unit}`} />
            <DetailRow label="Original Unit" value={record?.original_unit || 'N/A'} />
            <DetailRow label="Emission Factor" value={record?.emission_factor ? `${record.emission_factor} kg CO2e/unit` : 'N/A'} />
            <DetailRow label="Total Emissions" value={record?.emission_value ? `${parseFloat(record.emission_value).toFixed(2)} kg CO2e` : 'N/A'} />
          </DetailSection>

          <DetailSection title="Location & Source">
            <DetailRow label="Location" value={record?.location || 'N/A'} />
            <DetailRow label="Facility" value={record?.facility || 'N/A'} />
            <DetailRow label="Vendor" value={record?.vendor || 'N/A'} />
            <DetailRow label="Source File" value={record?.source_file || 'N/A'} />
          </DetailSection>

          <DetailSection title="Review Status">
            <DetailRow label="Status" value={record?.status} />
            <DetailRow label="Approved By" value={record?.approved_by_name || 'Not approved'} />
            <DetailRow label="Approved At" value={record?.approved_at ? new Date(record.approved_at).toLocaleString() : 'N/A'} />
            <DetailRow label="Created At" value={new Date(record?.created_at).toLocaleString()} />
          </DetailSection>
        </div>

        {record?.suspicious_flag && (
          <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <h3 className="text-sm font-medium text-yellow-900 mb-2">⚠ Suspicious Record</h3>
            <p className="text-sm text-yellow-700">{record.suspicious_reason}</p>
          </div>
        )}

        {record?.notes && (
          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <h3 className="text-sm font-medium text-gray-900 mb-2">Notes</h3>
            <p className="text-sm text-gray-700">{record.notes}</p>
          </div>
        )}
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Audit Trail</h2>
        <div className="space-y-3">
          {auditLogs?.map((log) => (
            <div key={log.id} className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {log.action} by {log.changed_by_name}
                  </p>
                  <p className="text-xs text-gray-600 mt-1">
                    {new Date(log.changed_at).toLocaleString()}
                  </p>
                  {log.notes && (
                    <p className="text-sm text-gray-700 mt-2">{log.notes}</p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function DetailSection({ title, children }) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-900 mb-3">{title}</h3>
      <div className="space-y-2">
        {children}
      </div>
    </div>
  )
}

function DetailRow({ label, value }) {
  return (
    <div className="flex justify-between py-2 border-b border-gray-100">
      <span className="text-sm text-gray-600">{label}</span>
      <span className="text-sm font-medium text-gray-900">{value}</span>
    </div>
  )
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
