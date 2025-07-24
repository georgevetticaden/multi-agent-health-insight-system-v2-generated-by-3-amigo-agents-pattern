import React from 'react';
import { Info, CheckCircle, AlertCircle, Target, Activity, Edit3, DollarSign } from 'lucide-react';
import { TestCase } from '../types';

interface TestCaseDisplayProps {
  testCase: TestCase;
  onRunEvaluation?: () => void;
  onSaveTestCase?: () => void;
  isEvaluating?: boolean;
}

const TestCaseDisplay: React.FC<TestCaseDisplayProps> = ({ 
  testCase, 
  onRunEvaluation, 
  onSaveTestCase,
  isEvaluating 
}) => {
  // Debug logging
  console.log('TestCaseDisplay render:', {
    modified_fields: testCase.modified_fields,
    expected_complexity: testCase.expected_complexity,
    actual_complexity: testCase.actual_complexity,
    expected_specialties: testCase.expected_specialties,
    actual_specialties: testCase.actual_specialties
  });
  const complexityColors = {
    SIMPLE: 'bg-green-100 text-green-700 border-green-200',
    STANDARD: 'bg-blue-100 text-blue-700 border-blue-200',
    COMPLEX: 'bg-orange-100 text-orange-700 border-orange-200',
    COMPREHENSIVE: 'bg-purple-100 text-purple-700 border-purple-200'
  };

  const isSpecialtyExpected = (specialty: string) => 
    testCase.expected_specialties.includes(specialty);

  const isSpecialtyActual = (specialty: string) => 
    testCase.actual_specialties.includes(specialty);

  // Check if expected values match actual values (indicating pre-population)
  const isExpectedMatchingActual = () => {
    const costMatches = testCase.expected_cost_threshold !== null && 
                       testCase.expected_cost_threshold !== undefined &&
                       testCase.actual_total_cost !== null && 
                       testCase.actual_total_cost !== undefined &&
                       Math.abs(testCase.expected_cost_threshold - testCase.actual_total_cost) < 0.0001;
    
    return testCase.expected_complexity === testCase.actual_complexity &&
           testCase.expected_specialties.length === testCase.actual_specialties.length &&
           testCase.expected_specialties.every(spec => testCase.actual_specialties.includes(spec)) &&
           (costMatches || (testCase.expected_cost_threshold === undefined && testCase.actual_total_cost === undefined));
  };

  // Check if a field has been modified by QE Agent
  const isFieldModified = (fieldName: string) => {
    return testCase.modified_fields?.includes(fieldName) || false;
  };

  // Check if specialty list has been modified
  const areSpecialtiesModified = () => {
    const modified = isFieldModified('expected_specialties');
    console.log('areSpecialtiesModified:', modified, 'from modified_fields:', testCase.modified_fields);
    return modified;
  };

  // Check if specialties actually differ from the actual specialties
  const areSpecialtiesDifferentFromActual = () => {
    if (testCase.expected_specialties.length !== testCase.actual_specialties.length) {
      return true;
    }
    const allMatch = testCase.expected_specialties.every(spec => testCase.actual_specialties.includes(spec));
    console.log('Specialties comparison:', {
      expected: testCase.expected_specialties,
      actual: testCase.actual_specialties,
      allMatch,
      different: !allMatch
    });
    return !allMatch;
  };

  // Check if key data points differ from actual
  const areKeyDataPointsDifferentFromActual = () => {
    if (!testCase.actual_key_data_points) return false;
    if (testCase.key_data_points.length !== testCase.actual_key_data_points.length) {
      return true;
    }
    return !testCase.key_data_points.every(point => testCase.actual_key_data_points.includes(point));
  };

  // Check if this field should show pre-population indicator
  const showPrePopulationIndicator = (fieldName: string) => {
    // Show pre-population indicator only if field hasn't been modified
    if (fieldName === 'expected_complexity') {
      return !isFieldModified('expected_complexity') && testCase.expected_complexity === testCase.actual_complexity;
    }
    if (fieldName === 'expected_specialties') {
      return !isFieldModified('expected_specialties') && 
             testCase.expected_specialties.length === testCase.actual_specialties.length &&
             testCase.expected_specialties.every(spec => testCase.actual_specialties.includes(spec));
    }
    if (fieldName === 'key_data_points') {
      return !isFieldModified('key_data_points') && 
             testCase.key_data_points.length > 0 &&
             testCase.actual_key_data_points?.length === testCase.key_data_points.length &&
             testCase.key_data_points.every(point => testCase.actual_key_data_points?.includes(point));
    }
    if (fieldName === 'expected_cost_threshold') {
      return !isFieldModified('expected_cost_threshold') && 
             testCase.expected_cost_threshold !== null && 
             testCase.expected_cost_threshold !== undefined &&
             testCase.actual_total_cost !== null && 
             testCase.actual_total_cost !== undefined &&
             Math.abs(testCase.expected_cost_threshold - testCase.actual_total_cost) < 0.0001; // Allow for floating point precision
    }
    return false;
  };

  // Group specialists by their status
  const allSpecialties = [...new Set([...testCase.expected_specialties, ...testCase.actual_specialties])];
  
  // Generate a logical test name from the query
  const generateTestName = (query: string) => {
    // Extract key terms from the query (limit to 3 main terms)
    const keyTerms = [];
    if (query.toLowerCase().includes('hba1c')) keyTerms.push('hba1c');
    if (query.toLowerCase().includes('metformin')) keyTerms.push('metformin');
    if (query.toLowerCase().includes('weight')) keyTerms.push('weight');
    if (query.toLowerCase().includes('correlation') && keyTerms.length < 3) keyTerms.push('correlation');
    if (query.toLowerCase().includes('dosage') && keyTerms.length < 3) keyTerms.push('dosage');
    
    if (keyTerms.length === 0) {
      return 'health_query_test';
    }
    // Take only first 3 terms and join with underscores
    return keyTerms.slice(0, 3).join('_') + '_test';
  };

  return (
    <div className="flex flex-col h-full">
      {/* Pre-population Notice */}
      {isExpectedMatchingActual() && (!testCase.modified_fields || testCase.modified_fields.length === 0) && (
        <div className="bg-blue-50 border-b border-blue-200 px-4 py-2 flex items-center gap-2">
          <Info className="w-4 h-4 text-blue-600 flex-shrink-0" />
          <p className="text-xs text-blue-700">
            Expected values have been pre-populated from actual execution. Please review and adjust them based on your analysis with the QE Agent.
          </p>
        </div>
      )}
      
      {/* Test Case Header */}
      <div className="bg-gray-50 border-b border-gray-200 px-4 py-3">
        <div className="flex-1">
          <div className="text-sm text-gray-900">
            <span className="font-medium">Test Name:</span> {generateTestName(testCase.query)}
          </div>
          <div className="text-xs text-gray-600 mt-1">
            <span className="font-medium">Health Query:</span> <span className="line-clamp-2">{testCase.query}</span>
          </div>
        </div>
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-scroll p-4 space-y-4" style={{ overscrollBehavior: 'contain' }}>
        {/* Complexity Comparison Card */}
      <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
        <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
          <Target className="w-4 h-4 text-indigo-600" />
          Complexity Classification
        </h4>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-gray-600 mb-1 flex items-center gap-1">
              Expected
              {showPrePopulationIndicator('expected_complexity') && (
                <span className="text-xs text-blue-600 italic">(pre-filled from actual)</span>
              )}
              {isFieldModified('expected_complexity') && (
                <span className="text-xs text-orange-600 italic flex items-center gap-0.5">
                  <Edit3 className="w-3 h-3" />
                  (modified)
                </span>
              )}
            </p>
            {testCase.expected_complexity ? (
              <div className="relative inline-block">
                <span className={`inline-block px-3 py-1 rounded-md text-xs font-medium border ${
                  isFieldModified('expected_complexity') 
                    ? `${complexityColors[testCase.expected_complexity]} ring-2 ring-orange-400 ring-offset-1`
                    : complexityColors[testCase.expected_complexity]
                }`}>
                  {testCase.expected_complexity}
                </span>
                {showPrePopulationIndicator('expected_complexity') && (
                  <div className="absolute -top-1 -right-1">
                    <Info className="w-3 h-3 text-blue-500" title="Pre-populated from actual execution" />
                  </div>
                )}
                {isFieldModified('expected_complexity') && (
                  <div className="absolute -top-1 -right-1">
                    <Edit3 className="w-3 h-3 text-orange-500" title="Modified by QE Agent" />
                  </div>
                )}
              </div>
            ) : (
              <span className="inline-block px-3 py-1 rounded-md text-xs font-medium border bg-gray-100 text-gray-500 border-gray-200 italic">
                Not set
              </span>
            )}
          </div>
          <div>
            <p className="text-xs text-gray-600 mb-1">Actual (from trace)</p>
            <span className={`inline-block px-3 py-1 rounded-md text-xs font-medium border ${complexityColors[testCase.actual_complexity] || 'bg-gray-100 text-gray-700 border-gray-200'}`}>
              {testCase.actual_complexity}
            </span>
          </div>
        </div>
      </div>

      {/* Specialists Comparison Card */}
      <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
        <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
          <Activity className="w-4 h-4 text-green-600" />
          Specialty Selection
        </h4>
        
        {/* Expected vs Actual Grid */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-gray-600 mb-2 flex items-center gap-1">
              Expected
              {showPrePopulationIndicator('expected_specialties') && (
                <span className="text-xs text-blue-600 italic">(verify these)</span>
              )}
              {areSpecialtiesModified() && areSpecialtiesDifferentFromActual() && (
                <span className="text-xs text-orange-600 italic flex items-center gap-0.5">
                  <Edit3 className="w-3 h-3" />
                  (modified)
                </span>
              )}
            </p>
            <div className="space-y-1">
              {testCase.expected_specialties.map(specialty => (
                <div
                  key={`expected-${specialty}`}
                  className={`text-xs px-2 py-1 rounded flex items-center justify-between ${
                    areSpecialtiesModified() && areSpecialtiesDifferentFromActual()
                      ? isSpecialtyActual(specialty)
                        ? 'bg-green-50 text-green-700 border border-green-200 ring-2 ring-orange-400 ring-offset-1'
                        : 'bg-gray-50 text-gray-700 border border-gray-200 ring-2 ring-orange-400 ring-offset-1'
                      : isSpecialtyActual(specialty)
                        ? 'bg-green-50 text-green-700 border border-green-200'
                        : 'bg-gray-50 text-gray-700 border border-gray-200'
                  }`}
                >
                  <span>{specialty.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, l => l.toUpperCase())}</span>
                  <div className="flex items-center gap-1">
                    {isSpecialtyActual(specialty) && <CheckCircle className="w-3 h-3 text-green-600" />}
                    {areSpecialtiesModified() && areSpecialtiesDifferentFromActual() && <Edit3 className="w-3 h-3 text-orange-500" />}
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          <div>
            <p className="text-xs text-gray-600 mb-2">Actual (from trace)</p>
            <div className="space-y-1">
              {testCase.actual_specialties.map(specialty => (
                <div
                  key={`actual-${specialty}`}
                  className={`text-xs px-2 py-1 rounded flex items-center justify-between ${
                    isSpecialtyExpected(specialty)
                      ? 'bg-green-50 text-green-700 border border-green-200'
                      : 'bg-yellow-50 text-yellow-700 border border-yellow-200'
                  }`}
                >
                  <span>{specialty.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, l => l.toUpperCase())}</span>
                  {!isSpecialtyExpected(specialty) && <AlertCircle className="w-3 h-3 text-yellow-600" />}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Analysis Quality Card */}
      <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
        <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-blue-600" />
          Analysis Quality
        </h4>
        
        {/* Keywords Section */}
        <div className="mb-4">
          <h5 className="text-xs font-medium text-gray-700 mb-2">Keywords</h5>
          
          {/* Expected vs Actual Grid */}
          <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-gray-600 mb-2 flex items-center gap-1">
              Expected
              {showPrePopulationIndicator('key_data_points') && (
                <span className="text-xs text-blue-600 italic">(pre-filled from actual)</span>
              )}
              {isFieldModified('key_data_points') && (
                <span className="text-xs text-orange-600 italic flex items-center gap-0.5">
                  <Edit3 className="w-3 h-3" />
                  (modified)
                </span>
              )}
            </p>
            {testCase.key_data_points.length > 0 ? (
              <div className="space-y-1">
                {testCase.key_data_points.map((point, idx) => {
                  const isPointInActual = testCase.actual_key_data_points?.includes(point);
                  return (
                    <div
                      key={`expected-${idx}`}
                      className={`text-xs px-2 py-1 rounded flex items-center justify-between border ${
                        isFieldModified('key_data_points') && areKeyDataPointsDifferentFromActual()
                          ? isPointInActual
                            ? 'bg-green-50 text-green-700 border-green-200 ring-2 ring-orange-400 ring-offset-1'
                            : 'bg-gray-50 text-gray-700 border-gray-200 ring-2 ring-orange-400 ring-offset-1'
                          : isPointInActual
                            ? 'bg-green-50 text-green-700 border-green-200'
                            : 'bg-gray-50 text-gray-700 border-gray-200'
                      }`}
                    >
                      <span>{point}</span>
                      <div className="flex items-center gap-1">
                        {isPointInActual && <CheckCircle className="w-3 h-3 text-green-600" />}
                        {isFieldModified('key_data_points') && areKeyDataPointsDifferentFromActual() && <Edit3 className="w-3 h-3 text-orange-500" />}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-xs text-gray-500 italic">No key data points identified</p>
            )}
          </div>
          
          <div>
            <p className="text-xs text-gray-600 mb-2">Actual (from approach)</p>
            {testCase.actual_key_data_points?.length > 0 ? (
              <div className="space-y-1">
                {testCase.actual_key_data_points.map((point, idx) => {
                  const isPointExpected = testCase.key_data_points.includes(point);
                  return (
                    <div
                      key={`actual-${idx}`}
                      className={`text-xs px-2 py-1 rounded flex items-center justify-between border ${
                        isPointExpected
                          ? 'bg-green-50 text-green-700 border-green-200'
                          : 'bg-yellow-50 text-yellow-700 border-yellow-200'
                      }`}
                    >
                      <span>{point}</span>
                      {!isPointExpected && <AlertCircle className="w-3 h-3 text-yellow-600" />}
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-xs text-gray-500 italic">No key points extracted from approach</p>
            )}
          </div>
        </div>
        </div>
        
        {/* Placeholder for future Analysis Quality sections */}
        {/* Future sections like "Coverage", "Completeness", etc. can be added here */}
      </div>

      {/* Cost Efficiency Card - Only show if we have cost data */}
      {(testCase.actual_total_cost !== undefined || testCase.expected_cost_threshold !== undefined) && (
        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
          <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <DollarSign className="w-4 h-4 text-green-600" />
            Cost Efficiency
          </h4>
          
          {/* Cost Threshold Section */}
          <div className="mb-4">
            <h5 className="text-xs font-medium text-gray-700 mb-2">Cost Threshold</h5>
            
            {/* Expected vs Actual Grid */}
            <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-gray-600 mb-1 flex items-center gap-1">
                Expected
                {showPrePopulationIndicator('expected_cost_threshold') && (
                  <span className="text-xs text-blue-600 italic">(pre-filled from actual)</span>
                )}
                {isFieldModified('expected_cost_threshold') && (
                  <span className="text-xs text-orange-600 italic flex items-center gap-0.5">
                    <Edit3 className="w-3 h-3" />
                    (modified)
                  </span>
                )}
              </p>
              {testCase.expected_cost_threshold !== undefined && testCase.expected_cost_threshold !== null ? (
                <div className="relative inline-block">
                  <span className={`inline-block px-3 py-1 rounded-md text-xs font-medium border ${
                    isFieldModified('expected_cost_threshold')
                      ? 'bg-yellow-50 text-yellow-700 border-yellow-200 ring-2 ring-orange-400 ring-offset-1'
                      : 'bg-yellow-50 text-yellow-700 border-yellow-200'
                  }`}>
                    ${testCase.expected_cost_threshold.toFixed(3)}
                  </span>
                  {isFieldModified('expected_cost_threshold') && (
                    <div className="absolute -top-1 -right-1">
                      <Edit3 className="w-3 h-3 text-orange-500" title="Modified by QE Agent" />
                    </div>
                  )}
                </div>
              ) : (
                <span className="inline-block px-3 py-1 rounded-md text-xs font-medium border bg-gray-100 text-gray-500 border-gray-200 italic">
                  Not set
                </span>
              )}
            </div>
            
            <div>
              <p className="text-xs text-gray-600 mb-1">Actual (from trace)</p>
              {testCase.actual_total_cost !== undefined && testCase.actual_total_cost !== null ? (
                <span className={`inline-block px-3 py-1 rounded-md text-xs font-medium border ${
                  testCase.expected_cost_threshold && testCase.actual_total_cost <= testCase.expected_cost_threshold
                    ? 'bg-green-50 text-green-700 border-green-200'
                    : testCase.expected_cost_threshold && testCase.actual_total_cost > testCase.expected_cost_threshold
                    ? 'bg-red-50 text-red-700 border-red-200'
                    : 'bg-gray-50 text-gray-700 border-gray-200'
                }`}>
                  ${testCase.actual_total_cost.toFixed(3)}
                  {testCase.actual_total_cost === null && ' (est.)'}
                </span>
              ) : (
                <span className="inline-block px-3 py-1 rounded-md text-xs font-medium border bg-gray-100 text-gray-500 border-gray-200 italic">
                  Not available
                </span>
              )}
            </div>
            </div>
          </div>
        </div>
      )}

        {/* Metadata Footer - Compact */}
        <div className="text-xs text-gray-500 px-2">
          <div className="flex items-center justify-between">
            <span>Test Case ID: {testCase.id.slice(0, 8)}...</span>
            <span>Last updated: {new Date(testCase.updated_at).toLocaleDateString()}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TestCaseDisplay;