import React from 'react';
import { Info } from 'lucide-react';
import { TestCase } from '../types';

interface TestCaseEditorProps {
  testCase: TestCase;
  onTestCaseChange: (testCase: TestCase) => void;
  isReadOnly: boolean;
}

const TestCaseEditor: React.FC<TestCaseEditorProps> = ({
  testCase,
  onTestCaseChange,
  isReadOnly
}) => {
  const handleFieldChange = (field: keyof TestCase, value: any) => {
    onTestCaseChange({
      ...testCase,
      [field]: value,
      updated_at: new Date().toISOString()
    });
  };

  const handleSpecialtyToggle = (specialty: string) => {
    const currentSpecialties = testCase.expected_specialties || [];
    const newSpecialties = currentSpecialties.includes(specialty)
      ? currentSpecialties.filter(s => s !== specialty)
      : [...currentSpecialties, specialty];
    
    handleFieldChange('expected_specialties', newSpecialties);
  };

  const availableSpecialties = [
    'CARDIOLOGY',
    'ENDOCRINOLOGY',
    'LABORATORY_MEDICINE',
    'DATA_ANALYTICS',
    'PREVENTIVE_MEDICINE',
    'PHARMACY',
    'NUTRITION',
    'GENERAL'
  ];

  const complexityOptions = ['SIMPLE', 'STANDARD', 'COMPLEX', 'COMPREHENSIVE'];

  return (
    <div className="p-4 space-y-4">
      {/* Query */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Health Query
        </label>
        <div className="p-3 bg-gray-50 rounded-md border border-gray-200">
          <p className="text-sm text-gray-900">{testCase.query}</p>
        </div>
      </div>

      {/* Expected Complexity */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Expected Complexity
        </label>
        <select
          value={testCase.expected_complexity}
          onChange={(e) => handleFieldChange('expected_complexity', e.target.value)}
          disabled={isReadOnly}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {complexityOptions.map(option => (
            <option key={option} value={option}>{option}</option>
          ))}
        </select>
        {testCase.actual_specialties && testCase.expected_complexity !== testCase.actual_specialties[0] && (
          <p className="text-xs text-amber-600 mt-1 flex items-center gap-1">
            <Info className="w-3 h-3" />
            Actual complexity was: {testCase.actual_specialties[0] || 'unknown'}
          </p>
        )}
      </div>

      {/* Expected Specialists */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Expected Specialists
        </label>
        <div className="space-y-2 p-3 bg-gray-50 rounded-md border border-gray-200">
          {availableSpecialties.map(specialty => (
            <label
              key={specialty}
              className="flex items-center gap-2 cursor-pointer hover:bg-gray-100 p-1 rounded"
            >
              <input
                type="checkbox"
                checked={testCase.expected_specialties.includes(specialty)}
                onChange={() => handleSpecialtyToggle(specialty)}
                disabled={isReadOnly}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-900">
                {specialty.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, l => l.toUpperCase())}
              </span>
              {testCase.actual_specialties.includes(specialty) && (
                <span className="text-xs text-green-600">(actual)</span>
              )}
            </label>
          ))}
        </div>
      </div>

      {/* Key Data Points */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Key Data Points
        </label>
        <textarea
          value={testCase.key_data_points.join('\n')}
          onChange={(e) => handleFieldChange('key_data_points', e.target.value.split('\n').filter(s => s.trim()))}
          disabled={isReadOnly}
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Enter key data points, one per line..."
        />
      </div>

      {/* Notes */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Notes
        </label>
        <textarea
          value={testCase.notes}
          onChange={(e) => handleFieldChange('notes', e.target.value)}
          disabled={isReadOnly}
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Add any notes about this test case..."
        />
      </div>

      {/* Metadata */}
      <div className="pt-4 border-t border-gray-200">
        <div className="grid grid-cols-2 gap-4 text-xs text-gray-600">
          <div>
            <span className="font-medium">Created:</span> {new Date(testCase.created_at).toLocaleString()}
          </div>
          <div>
            <span className="font-medium">Updated:</span> {new Date(testCase.updated_at).toLocaleString()}
          </div>
          <div>
            <span className="font-medium">Category:</span> {testCase.category}
          </div>
          <div>
            <span className="font-medium">Based on real query:</span> {testCase.based_on_real_query ? 'Yes' : 'No'}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TestCaseEditor;