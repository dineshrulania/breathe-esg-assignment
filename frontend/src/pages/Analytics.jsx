import { useQuery } from '@tanstack/react-query'
import { dashboardService, emissionRecordService } from '../api/services'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts'

export default function Analytics() {
  const { data: stats } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => dashboardService.getStats().then(res => res.data),
  })

  const scopeData = [
    { name: 'Scope 1', emissions: stats?.scope_breakdown?.scope_1 || 0 },
    { name: 'Scope 2', emissions: stats?.scope_breakdown?.scope_2 || 0 },
    { name: 'Scope 3', emissions: stats?.scope_breakdown?.scope_3 || 0 },
  ]

  const sourceData = stats?.source_stats?.map(s => ({
    name: s.source_type.toUpperCase(),
    records: s.count,
    processed: s.processed_rows,
  })) || []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
        <p className="mt-1 text-sm text-gray-600">
          Comprehensive insights into your ESG data
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <MetricCard
          title="Total Emissions"
          value={`${(stats?.total_emissions || 0).toFixed(2)} kg CO2e`}
          icon="🌍"
        />
        <MetricCard
          title="Data Sources"
          value={stats?.source_stats?.length || 0}
          icon="📁"
        />
        <MetricCard
          title="Approval Rate"
          value={`${stats?.total_records > 0 ? ((stats.approved_records / stats.total_records) * 100).toFixed(1) : 0}%`}
          icon="✓"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Emissions by Scope</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={scopeData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="emissions" fill="#22c55e" name="Emissions (kg CO2e)" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Records by Source</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={sourceData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="records" fill="#3b82f6" name="Total Records" />
              <Bar dataKey="processed" fill="#22c55e" name="Processed" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Review Status Breakdown</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatusCard
            label="Pending"
            value={stats?.pending_records || 0}
            color="yellow"
          />
          <StatusCard
            label="Approved"
            value={stats?.approved_records || 0}
            color="green"
          />
          <StatusCard
            label="Flagged"
            value={stats?.flagged_records || 0}
            color="red"
          />
          <StatusCard
            label="Total"
            value={stats?.total_records || 0}
            color="blue"
          />
        </div>
      </div>
    </div>
  )
}

function MetricCard({ title, value, icon }) {
  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="mt-2 text-2xl font-bold text-gray-900">{value}</p>
        </div>
        <div className="text-4xl">{icon}</div>
      </div>
    </div>
  )
}

function StatusCard({ label, value, color }) {
  const colorClasses = {
    yellow: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    green: 'bg-green-50 border-green-200 text-green-800',
    red: 'bg-red-50 border-red-200 text-red-800',
    blue: 'bg-blue-50 border-blue-200 text-blue-800',
  }

  return (
    <div className={`p-4 rounded-lg border-2 ${colorClasses[color]}`}>
      <p className="text-sm font-medium">{label}</p>
      <p className="mt-2 text-3xl font-bold">{value}</p>
    </div>
  )
}
