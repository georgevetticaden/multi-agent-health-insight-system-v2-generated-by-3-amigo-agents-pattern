import React, { useMemo, useState, useEffect } from 'react';
import * as Recharts from 'recharts';
import { Code2, Play, Copy, Check, Eye, FileCode } from 'lucide-react';
import * as LucideIcons from 'lucide-react';
import * as Babel from '@babel/standalone';

// Error boundary for catching Recharts context errors
class ChartErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Chart rendering error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="text-red-500 p-4 bg-red-50 rounded-lg">
          <h3 className="font-semibold mb-2">Error rendering chart</h3>
          <p className="text-sm">{this.state.error?.message}</p>
          <p className="text-xs mt-2 text-red-600">
            This might be due to Recharts components being used outside their parent chart context.
          </p>
        </div>
      );
    }

    return this.props.children;
  }
}

interface CodeArtifactProps {
  code: string;
  language?: string;
  data?: any;
  isStreaming?: boolean;
}

// Process imports and extract the component
const processCodeWithImports = (code: string) => {
  // Extract imports
  const importRegex = /^import\s+.*?from\s+['"].*?['"];?\s*$/gm;
  const imports = code.match(importRegex) || [];
  
  // Remove imports from code
  let componentCode = code;
  imports.forEach(imp => {
    componentCode = componentCode.replace(imp, '');
  });
  
  // Extract the default export if present
  const defaultExportRegex = /export\s+default\s+(\w+);?/;
  const defaultExportMatch = componentCode.match(defaultExportRegex);
  let componentName = null;
  
  if (defaultExportMatch) {
    componentName = defaultExportMatch[1];
    componentCode = componentCode.replace(defaultExportRegex, '');
  } else {
    // Try to find a component definition - multiple patterns
    const componentPatterns = [
      /const\s+(\w+)\s*=\s*\([^)]*\)\s*=>/,  // Arrow function with params
      /const\s+(\w+)\s*=\s*\(\s*\)\s*=>/,    // Arrow function no params
      /const\s+(\w+)\s*=\s*function/,        // Function expression
      /function\s+(\w+)\s*\(/,               // Function declaration
      /const\s+(\w+)\s*=\s*React\.memo/,     // React.memo wrapped
      /const\s+(\w+)\s*=\s*React\.forwardRef/ // React.forwardRef wrapped
    ];
    
    for (const pattern of componentPatterns) {
      const match = componentCode.match(pattern);
      if (match) {
        componentName = match[1];
        break;
      }
    }
    
    // If still no match, look for any const that ends with Chart/Component/Dashboard
    if (!componentName) {
      const genericPattern = /const\s+(\w*(?:Chart|Component|Dashboard|Visualization|View))\s*=/;
      const match = componentCode.match(genericPattern);
      if (match) {
        componentName = match[1];
      }
    }
  }
  
  return { imports, componentCode: componentCode.trim(), componentName };
};

const CodeArtifact: React.FC<CodeArtifactProps> = ({ code, language = 'javascript', data, isStreaming = false }) => {
  const [copied, setCopied] = React.useState(false);
  const [viewMode, setViewMode] = React.useState<'code' | 'preview'>('code');
  
  // Debug logging with better control
  useEffect(() => {
    if (!isStreaming && code && data) {
      console.log('=== CODE ARTIFACT FINAL RENDER ===');
      console.log('Code length:', code.length);
      console.log('Data object:', data);
      console.log('Data type:', typeof data);
      console.log('Data is array:', Array.isArray(data));
      console.log('Data.results exists:', data?.results !== undefined);
      console.log('Data records:', data?.results?.length || data?.length || 0);
      console.log('Is streaming:', isStreaming);
      
      // Determine the actual data structure
      const actualData = data?.results || data;
      
      if (Array.isArray(actualData) && actualData.length > 0) {
        const firstRecord = actualData[0];
        console.log('\nFirst record full structure:');
        console.log(JSON.stringify(firstRecord, null, 2));
        
        // Log all field names and types
        console.log('\nAll fields in first record:');
        Object.entries(firstRecord).forEach(([field, value]) => {
          console.log(`  ${field}: ${typeof value} = ${JSON.stringify(value).substring(0, 100)}`);
        });
        
        // Log key categorical fields to help debug mapping issues
        const categoricalFields = ['TEST_NAME', 'MEDICATION_NAME', 'VITAL_NAME', 'MEASUREMENT_TYPE', 
                                 'CATEGORY', 'TYPE', 'NAME', 'ITEM_DESCRIPTION', 'TEST_TYPE'];
        
        console.log('\nCategorical field analysis:');
        categoricalFields.forEach(field => {
          if (firstRecord[field] !== undefined) {
            const uniqueValues = [...new Set(actualData.map(r => r[field]))].filter(Boolean);
            console.log(`${field} - ${uniqueValues.length} unique values:`, uniqueValues.slice(0, 10));
          }
        });
        
        // Log date range
        const dateFields = ['RECORD_DATE', 'MEASUREMENT_DATE', 'DATE', 'COLLECTION_DATE'];
        console.log('\nDate field analysis:');
        dateFields.forEach(field => {
          if (firstRecord[field] !== undefined) {
            const dates = actualData.map(r => r[field]).filter(Boolean);
            if (dates.length > 0) {
              console.log(`${field}: min=${Math.min(...dates.map(d => new Date(d).getTime()))}, max=${Math.max(...dates.map(d => new Date(d).getTime()))}`);
              const minDate = new Date(Math.min(...dates.map(d => new Date(d).getTime())));
              const maxDate = new Date(Math.max(...dates.map(d => new Date(d).getTime())));
              const daysDiff = (maxDate.getTime() - minDate.getTime()) / (1000 * 60 * 60 * 24);
              console.log(`  Range: ${minDate.toISOString().split('T')[0]} to ${maxDate.toISOString().split('T')[0]} (${daysDiff.toFixed(0)} days)`);
            }
          }
        });
        
        // Show sample record structure
        console.log('\nSample record keys:', Object.keys(firstRecord));
      } else {
        console.log('No data records available or data is not in expected format');
        console.log('Raw data:', data);
      }
      console.log('=== END DEBUG ===');
    }
  }, [code, data, isStreaming]);
  
  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  
  // Execute the code to render the component
  const renderedComponent = useMemo(() => {
    if (language !== 'javascript' && language !== 'jsx' && language !== 'typescript' && language !== 'tsx') {
      return null;
    }
    
    // Don't try to execute while still streaming - return null so we don't show preview section
    if (isStreaming) {
      return null;
    }
    
    try {
      // Process the code to handle imports
      const { imports, componentCode, componentName } = processCodeWithImports(code);
      
      console.log('Processed code:', { 
        imports: imports.length, 
        componentName,
        hasJSX: componentCode.includes('<'),
        language
      });
      
      // Validate componentName - it should be a valid JavaScript identifier, not a language name
      const isValidComponentName = componentName && /^[a-zA-Z_$][a-zA-Z0-9_$]*$/.test(componentName) && 
                                   !['javascript', 'typescript', 'jsx', 'tsx'].includes(componentName.toLowerCase());
      
      console.log('Component name validation:', { componentName, isValid: isValidComponentName });
      
      // Build the full code with all dependencies in scope
      // Use a more robust approach to avoid temporal dead zone issues
      // IMPORTANT: Pass the actual data array, not the wrapper object
      const dataToPass = data?.results || data || [];
      const fullCode = `
        (function() {
          const React = window.React;
          const { useState } = React;
          const data = ${JSON.stringify(dataToPass)};
          
          // Recharts components
          const {
            LineChart, Line, BarChart, Bar, AreaChart, Area,
            PieChart, Pie, ScatterChart, Scatter, ComposedChart,
            RadarChart, Radar, RadialBarChart, RadialBar,
            XAxis, YAxis, ZAxis, CartesianGrid, PolarGrid,
            PolarAngleAxis, PolarRadiusAxis,
            Tooltip, Legend, ResponsiveContainer,
            ReferenceLine, ReferenceArea, ReferenceDot,
            Cell, Brush, ErrorBar, Label, LabelList,
            Sector, Curve, Dot, Rectangle, Cross, Symbols
          } = window.Recharts;
          
          // Lucide icons
          const {
            Activity, Heart, TrendingUp, TrendingDown,
            AlertCircle, CheckCircle, Info, AlertTriangle,
            Droplet, Calendar, Clock, User, Settings,
            ChevronUp, ChevronDown, ChevronLeft, ChevronRight,
            Pill, Package, FileText, Target, Zap, Shield, Star,
            Gauge, ArrowUp, ArrowDown, Filter, Download, Upload,
            Eye, Brain, Stethoscope, Beaker, TestTube, Syringe,
            Scale, Weight, Ruler, Calculator, ChartBar, ChartLine
          } = window.LucideIcons;
          
          // Execute the component code
          ${componentCode}
          
          // Try multiple strategies to find and return the component
          ${isValidComponentName ? `
          // Strategy 1: Direct reference if componentName was found
          if (typeof ${componentName} !== 'undefined') {
            return ${componentName};
          }
          ` : ''}
          
          // Strategy 2: Look for common component patterns in the global scope
          const possibleNames = ['Component', 'Chart', 'Dashboard', 'Visualization'];
          for (const name of possibleNames) {
            if (typeof window[name] !== 'undefined' && typeof window[name] === 'function') {
              const component = window[name];
              delete window[name]; // Clean up
              return component;
            }
          }
          
          // Strategy 3: Return the last defined function (common pattern)
          const allVars = Object.keys(this || {});
          for (let i = allVars.length - 1; i >= 0; i--) {
            const varName = allVars[i];
            const value = this[varName];
            if (typeof value === 'function' && value.prototype && 
                (value.prototype.isReactComponent || value.toString().includes('createElement'))) {
              return value;
            }
          }
          
          // Strategy 4: Fallback - try to find any function that looks like a component
          console.log('No component found via standard methods, trying fallback...');
          const fnNames = Object.getOwnPropertyNames(this || {}).filter(name => 
            typeof (this || {})[name] === 'function' && name[0] === name[0].toUpperCase()
          );
          console.log('Available function names:', fnNames);
          
          if (fnNames.length > 0) {
            return (this || {})[fnNames[0]];
          }
          
          // If no component found, throw error
          throw new Error('No React component found in the generated code');
        })()
      `;
      
      // Transform JSX to JavaScript
      const transformed = Babel.transform(fullCode, {
        presets: ['react'],
        filename: 'dynamic-component.jsx'
      });
      
      console.log('Transformed code successfully');
      console.log('Full code being executed:', fullCode.substring(0, 500) + '...');
      
      // Make dependencies available globally for the eval
      window.React = React;
      window.Recharts = Recharts;
      window.LucideIcons = LucideIcons;
      
      // Execute the transformed code
      const Component = eval(transformed.code);
      
      // Render the component with data prop
      if (typeof Component === 'function') {
        // Pass the data to the component - check if it's in results format
        const componentData = data?.results || data || [];
        console.log('Passing to visualization component:', {
          dataType: Array.isArray(componentData) ? 'array' : typeof componentData,
          recordCount: Array.isArray(componentData) ? componentData.length : 'N/A',
          firstRecordKeys: Array.isArray(componentData) && componentData.length > 0 ? Object.keys(componentData[0]) : []
        });
        return <Component data={componentData} />;
      } else {
        throw new Error('Generated code did not return a valid component');
      }
      
    } catch (error) {
      console.error('Error rendering component:', error);
      console.error('Error details:', error.message, error.stack);
      console.error('Code that failed to parse/execute:', code);
      
      let errorMessage = error.message;
      
      // Provide specific error messages
      if (error.message.includes('is not defined')) {
        const missingComponent = error.message.match(/(\w+) is not defined/)?.[1];
        if (missingComponent) {
          errorMessage = `Missing component: ${missingComponent}. Make sure it's imported correctly.`;
        }
      } else if (error.message.includes('Unexpected token')) {
        // Extract the specific syntax error
        const match = error.message.match(/Unexpected token (.+) \((\d+):(\d+)\)/);
        if (match) {
          errorMessage = `Syntax error: Unexpected token "${match[1]}" at line ${match[2]}, column ${match[3]}`;
          
          // Check if the code seems incomplete
          const codeLines = code.split('\n');
          if (codeLines.length > 0) {
            const lastLine = codeLines[codeLines.length - 1].trim();
            if (!lastLine.endsWith('};') && !lastLine.endsWith('}')) {
              errorMessage += '\n\nThe code appears to be incomplete. The component may have been cut off during generation.';
            }
          }
        } else {
          errorMessage = `Syntax error in the generated code. Check for unescaped JSX or invalid JavaScript.`;
        }
      } else if (error.message.includes('Could not find Recharts context')) {
        errorMessage = 'Recharts components must be properly nested inside their parent chart container (e.g., Line inside LineChart)';
      }
      
      return (
        <div className="text-red-500 p-4 bg-red-50 rounded-lg">
          <h3 className="font-semibold mb-2">Error rendering visualization</h3>
          <p className="text-sm">{errorMessage}</p>
          <details className="mt-2">
            <summary className="cursor-pointer text-sm text-red-600">Show error details</summary>
            <pre className="mt-2 text-xs overflow-auto">{error.stack}</pre>
          </details>
        </div>
      );
    }
  }, [code, data, language, isStreaming]);
  
  // Auto-switch to preview mode when streaming completes
  useEffect(() => {
    if (!isStreaming && renderedComponent) {
      setViewMode('preview');
    }
  }, [isStreaming, renderedComponent]);
  
  // Show code view while streaming, even if we want preview as default after
  const currentView = isStreaming ? 'code' : viewMode;
  
  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden flex flex-col h-full">
      {/* Header */}
      <div className="bg-gray-800 text-white px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Code2 className="w-4 h-4" />
          <span className="text-sm font-medium">React Component</span>
        </div>
        <div className="flex items-center gap-2">
          {/* View toggle buttons - only show when not streaming and preview is available */}
          {!isStreaming && renderedComponent && (
            <div className="flex bg-gray-700 rounded p-0.5 mr-2">
              <button
                onClick={() => setViewMode('preview')}
                className={`px-2 py-1 text-xs rounded transition-colors ${
                  viewMode === 'preview' 
                    ? 'bg-gray-600 text-white' 
                    : 'text-gray-400 hover:text-white'
                }`}
                title="Show visualization"
              >
                <Eye className="w-3 h-3" />
              </button>
              <button
                onClick={() => setViewMode('code')}
                className={`px-2 py-1 text-xs rounded transition-colors ${
                  viewMode === 'code' 
                    ? 'bg-gray-600 text-white' 
                    : 'text-gray-400 hover:text-white'
                }`}
                title="Show code"
              >
                <FileCode className="w-3 h-3" />
              </button>
            </div>
          )}
          <button
            onClick={handleCopy}
            className="p-1 hover:bg-gray-700 rounded transition-colors"
            title="Copy code"
          >
            {copied ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
          </button>
        </div>
      </div>
      
      {/* Code view - Show when streaming or when code view is selected */}
      {(currentView === 'code' || isStreaming) && (
        <div className="bg-gray-900 text-gray-100 p-4 overflow-x-auto flex-1">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-gray-400">
              {isStreaming ? '📡 Streaming code...' : 'Complete code'}
            </span>
            {isStreaming && (
              <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
            )}
          </div>
          <pre className="text-sm">
            <code>{code}</code>
          </pre>
        </div>
      )}
      
      {/* Preview view - Show when preview is selected and not streaming */}
      {currentView === 'preview' && !isStreaming && renderedComponent && (
        <div className="flex-1 flex flex-col">
          <div className="bg-gray-50 px-4 py-2 flex items-center gap-2">
            <Play className="w-4 h-4 text-green-600" />
            <span className="text-sm font-medium">Live Preview</span>
          </div>
          <div className="p-4 flex-1 overflow-auto">
            <div className="w-full">
              <ChartErrorBoundary>
                {renderedComponent}
              </ChartErrorBoundary>
            </div>
          </div>
        </div>
      )}
      
      {/* Streaming indicator - Show when streaming */}
      {isStreaming && (
        <div className="border-t flex items-center justify-center bg-gray-50 py-4">
          <div className="text-center">
            <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
            <p className="text-sm text-gray-600">Visualization will appear when code is complete</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default CodeArtifact;