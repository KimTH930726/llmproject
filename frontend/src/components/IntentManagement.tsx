import { useState, useEffect } from 'react';

interface Intent {
  id: number;
  keyword: string;
  intent_type: string;
  priority: number;
  description: string | null;
  created_at: string;
  updated_at: string;
}

interface IntentFormData {
  keyword: string;
  intent_type: string;
  priority: number;
  description: string;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const INTENT_TYPES = [
  { value: 'rag_search', label: 'RAG 검색' },
  { value: 'sql_query', label: 'SQL 쿼리' },
  { value: 'general', label: '일반 대화' },
];

export default function IntentManagement() {
  const [intents, setIntents] = useState<Intent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingIntent, setEditingIntent] = useState<Intent | null>(null);
  const [formData, setFormData] = useState<IntentFormData>({
    keyword: '',
    intent_type: 'rag_search',
    priority: 5,
    description: '',
  });

  const fetchIntents = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/intent/`);
      if (!response.ok) throw new Error('Failed to fetch intents');
      const data = await response.json();
      setIntents(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIntents();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/intent/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create intent');
      }
      await fetchIntents();
      resetForm();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingIntent) return;
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/intent/${editingIntent.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update intent');
      }
      await fetchIntents();
      resetForm();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('정말로 이 Intent를 삭제하시겠습니까?')) return;
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/intent/${id}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error('Failed to delete intent');
      await fetchIntents();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  const startEdit = (intent: Intent) => {
    setEditingIntent(intent);
    setFormData({
      keyword: intent.keyword,
      intent_type: intent.intent_type,
      priority: intent.priority,
      description: intent.description || '',
    });
    setIsFormOpen(true);
  };

  const resetForm = () => {
    setFormData({ keyword: '', intent_type: 'rag_search', priority: 5, description: '' });
    setEditingIntent(null);
    setIsFormOpen(false);
  };

  const getIntentTypeBadge = (type: string) => {
    const colors = {
      rag_search: 'bg-blue-100 text-blue-800',
      sql_query: 'bg-green-100 text-green-800',
      general: 'bg-gray-100 text-gray-800',
    };
    return colors[type as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center bg-gradient-to-r from-blue-600 to-blue-700 p-6 rounded-xl shadow-lg">
        <div>
          <h2 className="text-3xl font-bold text-white">Intent 관리</h2>
          <p className="text-blue-100 mt-2">질의 키워드와 의도 타입을 매핑하여 관리합니다</p>
        </div>
        <button
          onClick={() => setIsFormOpen(!isFormOpen)}
          className="px-6 py-3 bg-white text-blue-600 rounded-lg hover:bg-blue-50 font-semibold shadow-md transition-all duration-200 hover:shadow-lg hover:scale-105"
        >
          {isFormOpen ? '✕ 닫기' : '+ 새 Intent'}
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border-l-4 border-red-500 text-red-700 rounded-lg shadow-sm">
          <p className="font-semibold">⚠ 오류</p>
          <p>{error}</p>
        </div>
      )}

      {isFormOpen && (
        <form
          onSubmit={editingIntent ? handleUpdate : handleCreate}
          className="p-8 bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-xl shadow-lg space-y-6"
        >
          <h3 className="text-2xl font-bold text-blue-800 border-b-2 border-blue-300 pb-3">
            {editingIntent ? '✏ Intent 수정' : '✨ 새 Intent 생성'}
          </h3>
          <div>
            <label className="block text-sm font-semibold text-blue-900 mb-2">
              키워드 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.keyword}
              onChange={(e) => setFormData({ ...formData, keyword: e.target.value })}
              className="w-full px-4 py-3 border-2 border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
              placeholder="예: 검색, 몇명, 안녕"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-blue-900 mb-2">
              의도 타입 <span className="text-red-500">*</span>
            </label>
            <select
              value={formData.intent_type}
              onChange={(e) => setFormData({ ...formData, intent_type: e.target.value })}
              className="w-full px-4 py-3 border-2 border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
              required
            >
              {INTENT_TYPES.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-semibold text-blue-900 mb-2">
              우선순위 <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              value={formData.priority}
              onChange={(e) => setFormData({ ...formData, priority: Number(e.target.value) })}
              className="w-full px-4 py-3 border-2 border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
              placeholder="0-10 (높을수록 우선)"
              min="0"
              max="10"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-blue-900 mb-2">설명</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-4 py-3 border-2 border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
              placeholder="키워드에 대한 설명"
              rows={3}
            />
          </div>
          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              className="flex-1 px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 font-semibold shadow-md transition-all duration-200 hover:shadow-lg hover:scale-105"
            >
              {editingIntent ? '💾 수정 완료' : '✨ 생성하기'}
            </button>
            <button
              type="button"
              onClick={resetForm}
              className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 font-semibold shadow-md transition-all duration-200 hover:shadow-lg"
            >
              취소
            </button>
          </div>
        </form>
      )}

      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-blue-600 border-t-transparent"></div>
          <p className="mt-4 text-blue-600 font-semibold">로딩 중...</p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl shadow-lg border border-blue-200">
          <table className="min-w-full bg-white">
            <thead className="bg-gradient-to-r from-blue-600 to-blue-700 text-white">
              <tr>
                <th className="px-6 py-4 text-left font-bold text-sm">ID</th>
                <th className="px-6 py-4 text-left font-bold text-sm">키워드</th>
                <th className="px-6 py-4 text-left font-bold text-sm">의도 타입</th>
                <th className="px-6 py-4 text-center font-bold text-sm">우선순위</th>
                <th className="px-6 py-4 text-left font-bold text-sm">설명</th>
                <th className="px-6 py-4 text-center font-bold text-sm">작업</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-blue-100">
              {intents.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                    <div className="text-5xl mb-4">📋</div>
                    <p className="text-lg font-semibold">등록된 Intent가 없습니다</p>
                  </td>
                </tr>
              ) : (
                intents.map((intent) => (
                  <tr key={intent.id} className="hover:bg-blue-50 transition-colors duration-150">
                    <td className="px-6 py-4 text-gray-700 font-medium">{intent.id}</td>
                    <td className="px-6 py-4">
                      <span className="font-bold text-blue-800 text-base">{intent.keyword}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-3 py-1.5 rounded-full text-xs font-semibold ${getIntentTypeBadge(intent.intent_type)}`}>
                        {intent.intent_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-800 font-bold">
                        {intent.priority}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-gray-600">{intent.description || '-'}</td>
                    <td className="px-6 py-4">
                      <div className="flex gap-2 justify-center">
                        <button
                          onClick={() => startEdit(intent)}
                          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 font-medium shadow-sm transition-all duration-200 hover:shadow-md hover:scale-105"
                        >
                          수정
                        </button>
                        <button
                          onClick={() => handleDelete(intent.id)}
                          className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 font-medium shadow-sm transition-all duration-200 hover:shadow-md hover:scale-105"
                        >
                          삭제
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
