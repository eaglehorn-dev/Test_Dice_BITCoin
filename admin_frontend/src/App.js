import React, { useState } from 'react';
import Dashboard from './pages/Dashboard';
import ServerSeeds from './pages/ServerSeeds';
import './index.css';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className="App">
      {/* Navigation Tabs */}
      <div className="bg-white shadow-md border-b">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex space-x-8">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`py-4 px-2 border-b-2 font-medium text-sm ${
                activeTab === 'dashboard'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              📊 Dashboard
            </button>
            <button
              onClick={() => setActiveTab('seeds')}
              className={`py-4 px-2 border-b-2 font-medium text-sm ${
                activeTab === 'seeds'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              🔐 Server Seeds
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      {activeTab === 'dashboard' && <Dashboard />}
      {activeTab === 'seeds' && <ServerSeeds />}
    </div>
  );
}

export default App;
