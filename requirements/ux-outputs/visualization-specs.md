# Visualization Specifications

## Overview

The Health Insight Assistant uses dynamic data visualizations to make complex health data understandable and actionable. All visualizations are generated as self-contained React components using Recharts, with embedded data and interactive features.

## Core Visualization Types

### 1. Time Series Charts

#### Visual Design
```javascript
const timeSeriesConfig = {
  // Chart dimensions
  height: 400,
  margin: { top: 20, right: 30, left: 60, bottom: 60 },
  
  // Line styling
  strokeWidth: 2,
  dot: { r: 4, strokeWidth: 2 },
  activeDot: { r: 6, strokeWidth: 0 },
  
  // Grid configuration
  grid: {
    strokeDasharray: "3 3",
    stroke: "#E5E7EB",
    opacity: 0.5
  },
  
  // Axis styling
  xAxis: {
    stroke: "#6B7280",
    tick: { fill: "#6B7280", fontSize: 12 },
    axisLine: { strokeWidth: 1 }
  },
  yAxis: {
    stroke: "#6B7280",
    tick: { fill: "#6B7280", fontSize: 12 },
    axisLine: { strokeWidth: 1 }
  }
};
```

#### Health-Specific Features
- **Reference Ranges**: Shaded areas showing normal ranges
- **Abnormal Values**: Highlighted with different colors
- **Trend Indicators**: Arrows showing direction
- **Annotations**: Key events marked on timeline

#### Color Usage
```javascript
// Health metric colors
const healthMetricColors = {
  totalCholesterol: "#3B82F6",  // Blue
  ldlCholesterol: "#EF4444",    // Red (bad cholesterol)
  hdlCholesterol: "#10B981",    // Green (good cholesterol)
  triglycerides: "#F59E0B",     // Amber
  bloodPressureSystolic: "#8B5CF6",  // Purple
  bloodPressureDiastolic: "#EC4899", // Pink
  glucose: "#F97316",           // Orange
  hba1c: "#84CC16"             // Lime
};

// Reference range styling
const referenceRangeStyle = {
  fill: "rgba(16, 185, 129, 0.1)",  // Light green
  stroke: "rgba(16, 185, 129, 0.3)",
  strokeWidth: 1,
  strokeDasharray: "5 5"
};
```

#### Interactions
- **Hover**: Detailed tooltip with exact values
- **Click**: Toggle series visibility
- **Drag**: Zoom time range
- **Double-click**: Reset zoom
- **Touch**: Pinch to zoom on mobile

#### Example Implementation
```jsx
<ResponsiveContainer width="100%" height={400}>
  <LineChart data={data} margin={{ top: 20, right: 30, left: 60, bottom: 60 }}>
    <defs>
      <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
        <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.1}/>
        <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
      </linearGradient>
    </defs>
    
    <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" opacity={0.5} />
    
    <XAxis 
      dataKey="date"
      tick={{ fontSize: 12 }}
      tickFormatter={(date) => new Date(date).toLocaleDateString()}
    />
    
    <YAxis 
      label={{ value: 'mg/dL', angle: -90, position: 'insideLeft' }}
      domain={['dataMin - 10', 'dataMax + 10']}
    />
    
    <Tooltip 
      contentStyle={{ 
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        border: '1px solid #E5E7EB',
        borderRadius: '8px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
      }}
      formatter={(value, name) => [`${value} mg/dL`, name]}
    />
    
    <Legend 
      verticalAlign="bottom"
      height={36}
      iconType="line"
    />
    
    {/* Reference range */}
    <ReferenceArea 
      y1={0} 
      y2={200} 
      fill="rgba(16, 185, 129, 0.1)"
      fillOpacity={0.3}
      label="Normal Range"
    />
    
    <Line 
      type="monotone"
      dataKey="totalCholesterol"
      stroke="#3B82F6"
      strokeWidth={2}
      dot={{ r: 4 }}
      activeDot={{ r: 6 }}
      name="Total Cholesterol"
    />
  </LineChart>
</ResponsiveContainer>
```

### 2. Comparison Charts

#### Visual Design
- **Bar Chart**: For comparing discrete values
- **Grouped Bars**: For multiple metrics
- **Stacked Bars**: For composition analysis
- **Horizontal Bars**: For many categories

#### Color Patterns
```javascript
// Status-based coloring
const getBarColor = (value, normalRange) => {
  if (value < normalRange.min) return "#3B82F6"; // Below normal (blue)
  if (value > normalRange.max) return "#EF4444"; // Above normal (red)
  return "#10B981"; // Normal (green)
};

// Gradient fills for emphasis
const gradientDefs = (
  <defs>
    <linearGradient id="normalGradient" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stopColor="#10B981" stopOpacity={0.8}/>
      <stop offset="100%" stopColor="#10B981" stopOpacity={0.3}/>
    </linearGradient>
    <linearGradient id="warningGradient" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stopColor="#F59E0B" stopOpacity={0.8}/>
      <stop offset="100%" stopColor="#F59E0B" stopOpacity={0.3}/>
    </linearGradient>
    <linearGradient id="criticalGradient" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stopColor="#EF4444" stopOpacity={0.8}/>
      <stop offset="100%" stopColor="#EF4444" stopOpacity={0.3}/>
    </linearGradient>
  </defs>
);
```

#### Interactions
- **Hover**: Highlight bar with shadow
- **Click**: Drill down to details
- **Sort**: Click axis to sort
- **Filter**: Legend toggles categories

### 3. Correlation Visualizations

#### Scatter Plots
```javascript
const scatterConfig = {
  // Point styling
  symbol: {
    size: 60,
    type: 'circle',
    fill: (entry) => getHealthStatusColor(entry),
    stroke: '#fff',
    strokeWidth: 2
  },
  
  // Trend line
  trendline: {
    stroke: '#6B7280',
    strokeWidth: 2,
    strokeDasharray: '5 5',
    opacity: 0.5
  },
  
  // Quadrant backgrounds
  quadrants: {
    optimal: { fill: 'rgba(16, 185, 129, 0.05)' },
    warning: { fill: 'rgba(245, 158, 11, 0.05)' },
    critical: { fill: 'rgba(239, 68, 68, 0.05)' }
  }
};
```

#### Correlation Matrix
```javascript
const correlationMatrix = {
  // Cell styling based on correlation strength
  getCellColor: (correlation) => {
    const intensity = Math.abs(correlation);
    if (correlation > 0) {
      return `rgba(16, 185, 129, ${intensity})`; // Green for positive
    } else {
      return `rgba(239, 68, 68, ${intensity})`;   // Red for negative
    }
  },
  
  // Text contrast
  getTextColor: (correlation) => {
    return Math.abs(correlation) > 0.5 ? '#FFFFFF' : '#111827';
  }
};
```

### 4. Distribution Charts

#### Histogram Configuration
```javascript
const histogramConfig = {
  // Bin settings
  binCount: 20,
  binColor: '#3B82F6',
  binOpacity: 0.7,
  binStroke: '#2563EB',
  binStrokeWidth: 1,
  
  // Normal distribution overlay
  normalCurve: {
    stroke: '#EF4444',
    strokeWidth: 2,
    strokeDasharray: 'none',
    fill: 'none'
  },
  
  // Statistical markers
  markers: {
    mean: { stroke: '#10B981', strokeWidth: 2 },
    median: { stroke: '#F59E0B', strokeWidth: 2 },
    standardDeviation: { fill: 'rgba(59, 130, 246, 0.1)' }
  }
};
```

### 5. Multi-Metric Dashboards

#### Layout Patterns
```javascript
const dashboardLayouts = {
  // 2x2 Grid for 4 key metrics
  fourMetric: {
    grid: 'grid-cols-2 grid-rows-2',
    gap: 'gap-4',
    cardHeight: 200
  },
  
  // Hero + Supporting metrics
  heroMetric: {
    hero: { colSpan: 2, height: 300 },
    supporting: { colSpan: 1, height: 150 }
  },
  
  // Timeline + Metrics
  timelineDashboard: {
    timeline: { colSpan: 3, height: 400 },
    metrics: { colSpan: 1, height: 'auto' }
  }
};
```

#### Metric Card Design
```jsx
const MetricCard = ({ title, value, unit, change, status }) => (
  <div className={`
    bg-white rounded-xl p-6 shadow-sm border
    ${status === 'normal' ? 'border-green-200' : ''}
    ${status === 'warning' ? 'border-amber-200' : ''}
    ${status === 'critical' ? 'border-red-200' : ''}
  `}>
    <h3 className="text-sm font-medium text-gray-600">{title}</h3>
    <div className="mt-2 flex items-baseline">
      <span className="text-3xl font-semibold text-gray-900">{value}</span>
      <span className="ml-2 text-sm text-gray-500">{unit}</span>
    </div>
    <div className={`
      mt-2 flex items-center text-sm
      ${change > 0 ? 'text-red-600' : 'text-green-600'}
    `}>
      {change > 0 ? '↑' : '↓'} {Math.abs(change)}% from last test
    </div>
  </div>
);
```

## Interactive Features

### Tooltips
```javascript
const customTooltip = ({ active, payload, label }) => {
  if (!active || !payload) return null;
  
  return (
    <div className="bg-white p-4 rounded-lg shadow-lg border border-gray-200">
      <p className="font-semibold text-gray-900">{label}</p>
      {payload.map((entry, index) => (
        <div key={index} className="flex items-center mt-2">
          <div 
            className="w-3 h-3 rounded-full mr-2"
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-sm text-gray-600">{entry.name}:</span>
          <span className="text-sm font-medium ml-1">{entry.value} {entry.unit}</span>
        </div>
      ))}
      {/* Additional context */}
      <div className="mt-3 pt-3 border-t border-gray-100">
        <p className="text-xs text-gray-500">
          {getHealthContext(payload[0].value, payload[0].dataKey)}
        </p>
      </div>
    </div>
  );
};
```

### Zoom Controls
```jsx
const ZoomControls = ({ onZoomIn, onZoomOut, onReset }) => (
  <div className="absolute top-4 right-4 flex space-x-2">
    <button 
      onClick={onZoomIn}
      className="p-2 bg-white rounded-lg shadow-sm hover:bg-gray-50"
    >
      <ZoomIn className="w-4 h-4" />
    </button>
    <button 
      onClick={onZoomOut}
      className="p-2 bg-white rounded-lg shadow-sm hover:bg-gray-50"
    >
      <ZoomOut className="w-4 h-4" />
    </button>
    <button 
      onClick={onReset}
      className="p-2 bg-white rounded-lg shadow-sm hover:bg-gray-50"
    >
      <Maximize2 className="w-4 h-4" />
    </button>
  </div>
);
```

### Export Options
```javascript
const exportOptions = {
  png: {
    scale: 2,
    backgroundColor: '#FFFFFF',
    quality: 0.95
  },
  csv: {
    headers: true,
    separator: ',',
    dateFormat: 'YYYY-MM-DD'
  },
  pdf: {
    orientation: 'landscape',
    format: 'letter',
    margins: { top: 20, bottom: 20, left: 20, right: 20 }
  }
};
```

## Responsive Behavior

### Desktop (>1024px)
- Full interactive features
- Detailed tooltips
- All animations enabled
- Fine-grained controls

### Tablet (768px - 1024px)
- Touch-optimized interactions
- Simplified tooltips
- Larger touch targets
- Swipe gestures for panning

### Mobile (<768px)
- Vertical orientation preferred
- Stacked legends
- Tap to show tooltips
- Pinch to zoom
- Reduced data density

```javascript
const getResponsiveConfig = (width) => {
  if (width < 768) {
    return {
      fontSize: 10,
      strokeWidth: 1.5,
      dotSize: 3,
      margin: { top: 10, right: 10, bottom: 40, left: 40 }
    };
  } else if (width < 1024) {
    return {
      fontSize: 11,
      strokeWidth: 2,
      dotSize: 4,
      margin: { top: 15, right: 20, bottom: 50, left: 50 }
    };
  }
  return {
    fontSize: 12,
    strokeWidth: 2,
    dotSize: 4,
    margin: { top: 20, right: 30, bottom: 60, left: 60 }
  };
};
```

## Accessibility Features

### Color Blind Safe Palettes
```javascript
const colorBlindSafePalette = {
  categorical: [
    '#0173B2', // Blue
    '#DE8F05', // Orange
    '#029E73', // Green
    '#CC78BC', // Light Purple
    '#CA9161', // Light Brown
    '#949494', // Gray
    '#FBAFE4', // Light Pink
    '#ECE133'  // Yellow
  ],
  sequential: {
    blue: ['#EFF3FF', '#BDD7E7', '#6BAED6', '#3182BD', '#08519C'],
    orange: ['#FEEDDE', '#FDBE85', '#FD8D3C', '#E6550D', '#A63603']
  }
};
```

### Screen Reader Support
```jsx
// Provide data tables as alternative
const DataTable = ({ data, columns }) => (
  <table className="sr-only" role="table" aria-label="Chart data in table format">
    <thead>
      <tr>
        {columns.map(col => (
          <th key={col.key} scope="col">{col.label}</th>
        ))}
      </tr>
    </thead>
    <tbody>
      {data.map((row, i) => (
        <tr key={i}>
          {columns.map(col => (
            <td key={col.key}>{row[col.key]}</td>
          ))}
        </tr>
      ))}
    </tbody>
  </table>
);
```

### Keyboard Navigation
- Tab through interactive elements
- Arrow keys for data points
- Enter/Space to toggle series
- Escape to close tooltips

## Performance Guidelines

### Data Optimization
```javascript
// Downsample large datasets
const downsampleData = (data, maxPoints = 200) => {
  if (data.length <= maxPoints) return data;
  
  const step = Math.ceil(data.length / maxPoints);
  return data.filter((_, index) => index % step === 0);
};

// Virtualize large legends
const VirtualizedLegend = ({ items, height = 200 }) => {
  // Use react-window for large item counts
};
```

### Animation Performance
```javascript
// Disable animations for large datasets
const shouldAnimate = (dataLength) => dataLength < 500;

// Use CSS transforms for smooth animations
const animationConfig = {
  animateOnMount: shouldAnimate(data.length),
  animationDuration: 300,
  animationEasing: 'ease-out'
};
```

### Lazy Loading
```javascript
// Load charts when visible
const ChartContainer = ({ children }) => {
  const [isVisible, setIsVisible] = useState(false);
  const ref = useRef();
  
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => setIsVisible(entry.isIntersecting),
      { threshold: 0.1 }
    );
    
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);
  
  return (
    <div ref={ref}>
      {isVisible ? children : <ChartSkeleton />}
    </div>
  );
};
```

## Chart Templates

### Basic Time Series Template
```jsx
const TimeSeriesChart = ({ data, metrics, title }) => (
  <div className="bg-white rounded-xl p-6 shadow-sm">
    <h3 className="text-lg font-semibold mb-4">{title}</h3>
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={data}>
        {/* Standard configuration */}
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis />
        <Tooltip content={<CustomTooltip />} />
        <Legend />
        {metrics.map(metric => (
          <Line
            key={metric.key}
            type="monotone"
            dataKey={metric.key}
            stroke={metric.color}
            name={metric.name}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  </div>
);
```

These specifications ensure that all visualizations in the Health Insight Assistant are not only visually appealing but also functional, accessible, and performant across all devices and use cases.