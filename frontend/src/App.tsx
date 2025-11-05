import { useState } from 'react';
import IntentManagement from './components/IntentManagement';
import QueryLogManagement from './components/QueryLogManagement';
import FewShotManagement from './components/FewShotManagement';
import './App.css';

type TabType = 'intent' | 'querylog' | 'fewshot';

function App() {
  const [activeTab, setActiveTab] = useState<TabType>('intent');

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-blue-100">
      {/* Header */}
      <header className="bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-700 shadow-xl">
        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-white rounded-xl flex items-center justify-center shadow-lg">
              <span className="text-4xl">🤖</span>
            </div>
            <div>
              <h1 className="text-4xl font-bold text-white drop-shadow-md">
                LLM 관리 시스템
              </h1>
              <p className="text-blue-100 mt-2">
                Intent 및 Few-shot 예제를 관리하여 AI 성능을 향상시키세요
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="bg-white rounded-2xl shadow-xl border-2 border-blue-100">
          <div className="flex gap-2 p-2 bg-blue-50 rounded-t-2xl border-b-2 border-blue-200">
            <button
              onClick={() => setActiveTab('intent')}
              className={`flex-1 px-6 py-4 font-bold text-lg rounded-xl transition-all duration-200 ${
                activeTab === 'intent'
                  ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg scale-105'
                  : 'text-blue-600 hover:bg-blue-100 hover:scale-102'
              }`}
            >
              🎯 Intent 관리
            </button>
            <button
              onClick={() => setActiveTab('querylog')}
              className={`flex-1 px-6 py-4 font-bold text-lg rounded-xl transition-all duration-200 ${
                activeTab === 'querylog'
                  ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg scale-105'
                  : 'text-blue-600 hover:bg-blue-100 hover:scale-102'
              }`}
            >
              💬 질의 로그
            </button>
            <button
              onClick={() => setActiveTab('fewshot')}
              className={`flex-1 px-6 py-4 font-bold text-lg rounded-xl transition-all duration-200 ${
                activeTab === 'fewshot'
                  ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg scale-105'
                  : 'text-blue-600 hover:bg-blue-100 hover:scale-102'
              }`}
            >
              📚 Few-shot 예제
            </button>
          </div>

          {/* Content Area */}
          <div className="p-8">
            {activeTab === 'intent' && <IntentManagement />}
            {activeTab === 'querylog' && <QueryLogManagement />}
            {activeTab === 'fewshot' && <FewShotManagement />}
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="max-w-7xl mx-auto px-4 py-8 text-center">
        <div className="bg-white rounded-xl shadow-md p-4 border border-blue-200">
          <p className="text-blue-800 font-semibold">
            ✨ 지원자 자기소개서 분석 및 RAG 채팅 시스템 v2.0
          </p>
          <p className="text-blue-600 text-sm mt-1">
            Powered by FastAPI + React + PostgreSQL + Qdrant
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
