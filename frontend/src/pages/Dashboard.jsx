import { useQuery } from '@tanstack/react-query'
import { dashboardService } from '../api/services'
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'

export default function Dashboard() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => dashboardService.getStats().then(res => res.data),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading dashboard...</div>
      </div>
    )
  }

  const scopeData = [
    { name: 'Scope 1', value: stats?.scope_breakdown?.scope_1 || 0, color: '#ef4444' },
    { name: 'Scope 2', value: stats?.scope_breakdown?.scope_2 || 0, color: '#f59e0b' },
    { name: 'Scope 3', value: stats?.scope_breakdown?.scope_3 || 0, color: '#10b981' },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-600">
          Overview of your ESG data ingestion and review status
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Records"
          value={stats?.total_records || 0}
          icon="📊"
          color="blue"
        />
        <StatCard
          title="Pending Review"
          value={stats?.pending_records || 0}
          icon="⏳"
          color="yellow"
        />
        <StatCard
          title="Approved"
          value={stats?.approved_records || 0}
          icon="✓"
          color="green"
        />
        <StatCard
          title="Flagged"
          value={stats?.flagged_records || 0}
          icon="⚠"
          color="red"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Emissions by Scope</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={scopeData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value.toFixed(0)} kg CO2e`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {scopeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 text-center">
            <p className="text-2xl font-bold text-gray-900">
              {(stats?.total_emissions || 0).toFixed(2)} kg CO2e
            </p>
            <p className="text-sm text-gray-600">Total Emissions</p>
          </div>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Uploads</h2>
          <div className="space-y-3">
            {stats?.recent_uploads?.slice(0, 5).map((upload) => (
              <div key={upload.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-gray-900">{upload.file_name}</p>
                  <p className="text-xs text-gray-600">
                    {upload.source_type} • {new Date(upload.uploaded_at).toLocaleDateString()}
                  </p>
                </div>
                <span className={`badge ${getStatusColor(upload.processing_status)}`}>
                  {upload.processing_status}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function StatCard({ title, value, icon, color }) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    green: 'bg-green-50 text-green-600',
    red: 'bg-red-50 text-red-600',
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="mt-2 text-3xl font-bold text-gray-900">{value}</p>
        </div>
        <div className={`text-4xl ${colorClasses[color]} p-3 rounded-lg`}>
          {icon}
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
