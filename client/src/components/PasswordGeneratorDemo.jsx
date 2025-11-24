import React, { useState } from 'react';
import PasswordGenerator from '../components/PasswordGenerator';
import { checkPasswordStrength } from '../utils/passwordGenerator';

const PasswordGeneratorDemo = () => {
  const [demoPassword, setDemoPassword] = useState('');

  const handlePasswordGenerated = (password) => {
    setDemoPassword(password);
  };

  const strength = checkPasswordStrength(demoPassword);

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold text-gray-800 mb-6 text-center">
        🔐 Password Generator Demo
      </h2>
      
      <div className="space-y-6">
        <PasswordGenerator onPasswordGenerated={handlePasswordGenerated} />
        
        {demoPassword && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-blue-800 mb-2">
              Generated Password Analysis
            </h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Length:</span>
                <span className="font-medium">{demoPassword.length} characters</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Strength:</span>
                <span className={`font-medium text-${strength.color}-600`}>
                  {strength.strength.toUpperCase()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Score:</span>
                <span className="font-medium">{strength.score}/8</span>
              </div>
            </div>
            
            {strength.feedback.length > 0 && (
              <div className="mt-3">
                <h4 className="text-sm font-medium text-gray-700 mb-1">Feedback:</h4>
                <ul className="text-xs text-gray-600 space-y-1">
                  {strength.feedback.map((item, index) => (
                    <li key={index} className="flex items-center">
                      <span className="mr-2">
                        {item.includes('Password looks good') ? '✅' : '⚠️'}
                      </span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default PasswordGeneratorDemo;
