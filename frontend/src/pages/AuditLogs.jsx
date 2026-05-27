import { useQuery } from '@tanstack/react-query'
import { auditLogService } from '../api/services'

export default function AuditLogs() {
  const { data: logs, isLoading } = useQuery({
    queryKey: ['audit-logs'],
    queryFn: () => auditLogService.getAll().then(res => res.data.results || res.data),
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Audit Logs</h1>
        <p className="mt-1 text-sm text-gray-600">
          Complete audit trail of all record changes and approvals
        </p>
      </div>

      <div className="card">
        {isLoading ? (
          <div className="text-center py-8 text-gray-500">Loading audit logs...</div>
        ) : (
          <div className="space-y-3">
            {logs?.map((log) => (
              <div key={log.id} className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <span className={`badge ${getActionColor(log.action)}`}>
                        {log.action}
                      </span>
                      <span className="text-sm font-medium text-gray-900">
                        Record #{log.record_id}
                      </span>
                    </div>
                    <p className="text-sm text-gray-700 mt-2">
                      Changed by <span className="font-medium">{log.changed_by_name}</span>
                    </p>
                    <p className="text-xs text-gray-600 mt-1">
                      {new Date(log.changed_at).toLocaleString()}
                    </p>
                    {log.notes && (
                      <p className="text-sm text-gray-700 mt-2 p-2 bg-white rounded">
                        {log.notes}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function getActionColor(action) {
  const colors = {
    create: 'bg-blue-100 text-blue-800',
    update: 'bg-yellow-100 text-yellow-800',
    approve: 'bg-green-100 text-green-800',
    reject: 'bg-red-100 text-red-800',
    flag: 'bg-orange-100 text-orange-800',
    lock: 'bg-gray-100 text-gray-800',
    unlock: 'bg-purple-100 text-purple-800',
  }
  return colors[action] || 'bg-gray-100 text-gray-800'
}
