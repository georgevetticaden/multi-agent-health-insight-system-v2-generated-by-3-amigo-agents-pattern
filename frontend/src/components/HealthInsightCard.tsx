import React from 'react';
import { 
  TrendingUp, TrendingDown, AlertTriangle, 
  CheckCircle, Info, Activity 
} from 'lucide-react';

interface HealthMetric {
  label: string;
  value: string | number;
  unit?: string;
  trend?: 'up' | 'down' | 'stable';
  status: 'normal' | 'warning' | 'critical';
  previousValue?: string | number;
  description?: string;
}

interface HealthInsightCardProps {
  title: string;
  metrics: HealthMetric[];
  summary?: string;
  recommendations?: string[];
  type?: 'primary' | 'warning' | 'danger';
}

const HealthInsightCard: React.FC<HealthInsightCardProps> = ({
  title,
  metrics,
  summary,
  recommendations,
  type = 'primary'
}) => {
  const getTypeStyles = () => {
    switch (type) {
      case 'warning':
        return 'border-l-4 border-yellow-500 bg-yellow-50';
      case 'danger':
        return 'border-l-4 border-red-500 bg-red-50';
      default:
        return 'border-l-4 border-blue-500 bg-blue-50';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'normal':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-yellow-600" />;
      case 'critical':
        return <AlertTriangle className="w-4 h-4 text-red-600" />;
      default:
        return <Info className="w-4 h-4 text-blue-600" />;
    }
  };

  const getTrendIcon = (trend?: string) => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="w-4 h-4 text-green-600" />;
      case 'down':
        return <TrendingDown className="w-4 h-4 text-red-600" />;
      default:
        return <Activity className="w-4 h-4 text-gray-500" />;
    }
  };

  return (
    <div className={`bg-white rounded-xl shadow-sm border border-gray-200 p-6 ${getTypeStyles()}`}>
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>

      {summary && (
        <p className="text-sm text-gray-600 mb-4">{summary}</p>
      )}

      <div className="space-y-3">
        {metrics.map((metric, index) => (
          <div key={index} className={`flex items-center justify-between p-3 rounded-lg border ${
            metric.status === 'critical' ? 'bg-red-50 border-red-200' :
            metric.status === 'warning' ? 'bg-yellow-50 border-yellow-200' :
            'bg-green-50 border-green-200'
          }`}>
            <div className="flex items-start gap-2">
              {getStatusIcon(metric.status)}
              <div>
                <p className="text-sm font-medium text-gray-900">{metric.label}</p>
                {metric.description && (
                  <p className="text-xs text-gray-600 mt-1">{metric.description}</p>
                )}
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <div className="text-right">
                <p className={`font-semibold text-lg ${
                  metric.status === 'critical' ? 'text-red-700' :
                  metric.status === 'warning' ? 'text-yellow-700' :
                  'text-green-700'
                }`}>
                  {metric.value}{metric.unit && ` ${metric.unit}`}
                </p>
                {metric.previousValue && (
                  <p className="text-xs text-gray-500">
                    was {metric.previousValue}{metric.unit && ` ${metric.unit}`}
                  </p>
                )}
              </div>
              {getTrendIcon(metric.trend)}
            </div>
          </div>
        ))}
      </div>

      {recommendations && recommendations.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <h4 className="text-sm font-semibold text-gray-900 mb-2">Recommendations</h4>
          <ul className="space-y-1">
            {recommendations.map((rec, index) => (
              <li key={index} className="text-sm text-gray-600 flex items-start gap-2">
                <span className="text-blue-600 mt-0.5">•</span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default HealthInsightCard;