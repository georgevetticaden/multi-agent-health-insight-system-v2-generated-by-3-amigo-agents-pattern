import React from 'react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { FileText, Calendar, CheckCircle, AlertCircle } from 'lucide-react';

interface ImportDashboardProps {
  data: any;
}

const COLORS = ['#0ea5e9', '#10b981', '#f59e0b', '#ef4444'];

const ImportDashboard: React.FC<ImportDashboardProps> = ({ data }) => {
  // Prepare data for visualizations
  const categoryData = Object.entries(data.records_by_category || {}).map(([name, value]) => ({
    name,
    value,
  }));
  
  const timelineData = Object.entries(data.timeline_coverage || {})
    .sort((a, b) => Number(a[0]) - Number(b[0]))
    .map(([year, count]) => ({
      year,
      count,
    }));
  
  const qualityMetrics = data.data_quality || {};
  
  return (
    <div className="space-y-6">
      {/* Overall Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="health-metric-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Records</p>
              <p className="text-2xl font-bold text-gray-800">{data.total_records || 0}</p>
            </div>
            <FileText className="w-8 h-8 text-primary-500" />
          </div>
        </div>
        
        <div className="health-metric-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Years Covered</p>
              <p className="text-2xl font-bold text-gray-800">
                {Object.keys(data.timeline_coverage || {}).length}
              </p>
            </div>
            <Calendar className="w-8 h-8 text-green-500" />
          </div>
        </div>
        
        <div className="health-metric-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Data Quality</p>
              <p className="text-2xl font-bold text-gray-800">
                {qualityMetrics.records_with_dates?.percentage || 0}%
              </p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-500" />
          </div>
        </div>
        
        <div className="health-metric-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Categories</p>
              <p className="text-2xl font-bold text-gray-800">{categoryData.length}</p>
            </div>
            <AlertCircle className="w-8 h-8 text-yellow-500" />
          </div>
        </div>
      </div>
      
      {/* Records by Category */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h4 className="text-lg font-semibold mb-4">Records by Category</h4>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={categoryData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {categoryData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
        
        {/* Timeline Coverage */}
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h4 className="text-lg font-semibold mb-4">Timeline Coverage</h4>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={timelineData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="year" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#0ea5e9" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
      
      {/* Data Quality Indicators */}
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <h4 className="text-lg font-semibold mb-4">Data Quality Indicators</h4>
        <div className="space-y-3">
          {Object.entries(qualityMetrics).map(([key, metric]: [string, any]) => (
            <div key={key} className="flex items-center justify-between">
              <span className="text-sm text-gray-600">
                {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </span>
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">
                  {metric.count} of {metric.total}
                </span>
                <div className="w-32 bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      metric.percentage >= 80 ? 'bg-green-500' :
                      metric.percentage >= 60 ? 'bg-yellow-500' :
                      'bg-red-500'
                    }`}
                    style={{ width: `${metric.percentage}%` }}
                  />
                </div>
                <span className="text-sm font-bold w-12 text-right">
                  {metric.percentage}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Key Insights */}
      {data.key_insights && data.key_insights.length > 0 && (
        <div className="bg-blue-50 p-6 rounded-lg">
          <h4 className="text-lg font-semibold mb-3 text-blue-900">Key Insights</h4>
          <ul className="space-y-2">
            {data.key_insights.map((insight: string, index: number) => (
              <li key={index} className="flex items-start gap-2">
                <CheckCircle className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-blue-800">{insight}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default ImportDashboard;