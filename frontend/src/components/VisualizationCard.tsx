import React from 'react';
import { Visualization } from '@/types';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import ImportDashboard from './visualizations/ImportDashboard';
import DataTable from './visualizations/DataTable';

interface VisualizationCardProps {
  visualization: Visualization;
}

const COLORS = ['#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

const VisualizationCard: React.FC<VisualizationCardProps> = ({ visualization }) => {
  const renderVisualization = () => {
    switch (visualization.type) {
      case 'line_chart':
        // Use specific lines if provided, otherwise auto-detect
        const linesToShow = visualization.lines || (
          visualization.data.length > 0 
            ? Object.keys(visualization.data[0]).filter(key => key !== 'date' && typeof visualization.data[0][key] === 'number')
            : []
        );
        
        return (
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={visualization.data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                <XAxis 
                  dataKey="date" 
                  tick={{ fontSize: 12 }}
                  angle={-45}
                  textAnchor="end"
                  height={60}
                />
                <YAxis 
                  label={{ 
                    value: visualization.yAxis || 'Value', 
                    angle: -90, 
                    position: 'insideLeft' 
                  }}
                  tick={{ fontSize: 12 }}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    border: '1px solid #ccc',
                    borderRadius: '4px'
                  }}
                />
                <Legend 
                  wrapperStyle={{ paddingTop: '20px' }}
                  iconType="line"
                />
                {linesToShow.map((key, index) => (
                  <Line
                    key={key}
                    type="monotone"
                    dataKey={key}
                    stroke={COLORS[index % COLORS.length]}
                    strokeWidth={2}
                    dot={{ r: 3 }}
                    activeDot={{ r: 5 }}
                    name={key}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        );
        
      case 'bar_chart':
        return (
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={visualization.data}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="value" fill={COLORS[0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        );
        
      case 'pie_chart':
        return (
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={visualization.data}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {visualization.data.map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        );
        
      case 'table':
        return <DataTable data={visualization.data} />;
        
      case 'import_dashboard':
        return <ImportDashboard data={visualization.data} />;
        
      case 'auto':
      default:
        // Auto-detect best visualization type
        if (visualization.data.length === 0) {
          return <p className="text-gray-500">No data to display</p>;
        }
        
        // If data has time series characteristics, use line chart
        if (visualization.data[0]?.date || visualization.data[0]?.time) {
          return renderVisualization(); // Recursive call with line_chart
        }
        
        // Otherwise, use table
        return <DataTable data={visualization.data} />;
    }
  };
  
  return (
    <div className="visualization-card">
      {visualization.title && (
        <h3 className="text-lg font-semibold text-gray-800 mb-4">
          {visualization.title}
        </h3>
      )}
      
      {renderVisualization()}
      
      {visualization.metrics && (
        <div className="mt-4 pt-4 border-t">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(visualization.metrics).map(([key, value]) => (
              <div key={key} className="text-center">
                <p className="text-sm text-gray-600">{key}</p>
                <p className="text-lg font-semibold text-gray-800">{String(value)}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default VisualizationCard;