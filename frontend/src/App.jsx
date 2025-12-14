import { useState } from 'react'
import axios from 'axios'
import './App.css'

function App() {
  const [repoUrl, setRepoUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleAnalyze = async () => {
    if (!repoUrl.trim()) {
      setError('Please enter a GitHub repository URL')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await axios.post('/api/analyze', {
        repo_url: repoUrl
      })
      setResult(response.data)
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to analyze repository. Please check the URL and try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleAnalyze()
    }
  }

  const getScoreColor = (score) => {
    if (score >= 85) return '#10b981' // green
    if (score >= 70) return '#3b82f6' // blue
    if (score >= 50) return '#f59e0b' // orange
    return '#ef4444' // red
  }

  const getScoreGrade = (score) => {
    if (score >= 85) return 'A'
    if (score >= 70) return 'B'
    if (score >= 50) return 'C'
    if (score >= 35) return 'D'
    return 'F'
  }

  return (
    <div className="min-h-screen py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8 animate-fade-in">
          <h1 className="text-5xl font-bold text-white mb-3">
            🔍 Repository Mirror
          </h1>
          <p className="text-xl text-white/90">
            AI-Powered GitHub Repository Analysis & Developer Profiling
          </p>
          <p className="text-sm text-white/70 mt-2">
            Get instant insights, scores, and personalized roadmaps for any public GitHub repository
          </p>
        </div>

        {/* Input Section */}
        <div className="bg-white rounded-2xl shadow-2xl p-8 mb-8 animate-fade-in">
          <label className="block text-gray-700 text-sm font-semibold mb-3">
            GitHub Repository URL
          </label>
          <div className="flex gap-3">
            <input
              type="text"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="https://github.com/username/repository"
              className="flex-1 px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-primary transition-colors"
              disabled={loading}
            />
            <button
              onClick={handleAnalyze}
              disabled={loading}
              className="px-8 py-3 bg-gradient-to-r from-primary to-secondary text-white font-semibold rounded-lg hover:shadow-lg transform hover:scale-105 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Analyzing...
                </span>
              ) : (
                'Analyze'
              )}
            </button>
          </div>
          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
              ⚠️ {error}
            </div>
          )}
        </div>

        {/* Results Section */}
        {result && (
          <div className="space-y-6 animate-fade-in">
            {/* Score Card */}
            <div className="bg-white rounded-2xl shadow-2xl p-8">
              <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
                <span>📊</span> Repository Score
              </h2>
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-6xl font-bold mb-2" style={{ color: getScoreColor(result.score) }}>
                    {result.score}
                    <span className="text-3xl text-gray-400">/100</span>
                  </div>
                  <div className="text-2xl font-semibold text-gray-600">
                    Grade: <span style={{ color: getScoreColor(result.score) }}>{getScoreGrade(result.score)}</span>
                  </div>
                </div>
                <div className="w-32 h-32 relative">
                  <svg className="w-full h-full" viewBox="0 0 100 100">
                    <circle
                      cx="50"
                      cy="50"
                      r="40"
                      fill="none"
                      stroke="#e5e7eb"
                      strokeWidth="8"
                    />
                    <circle
                      cx="50"
                      cy="50"
                      r="40"
                      fill="none"
                      stroke={getScoreColor(result.score)}
                      strokeWidth="8"
                      strokeDasharray={`${result.score * 2.51} 251`}
                      strokeLinecap="round"
                      transform="rotate(-90 50 50)"
                    />
                  </svg>
                </div>
              </div>

              {/* Score Breakdown */}
              {result.breakdown && (
                <div className="mt-6 pt-6 border-t border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-700 mb-4">Score Breakdown</h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    {Object.entries(result.breakdown).map(([key, value]) => (
                      <div key={key} className="bg-gray-50 rounded-lg p-3">
                        <div className="text-sm text-gray-600 capitalize mb-1">
                          {key.replace('_', ' ')}
                        </div>
                        <div className="text-2xl font-bold text-gray-800">{value}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Summary Card */}
            <div className="bg-white rounded-2xl shadow-2xl p-8">
              <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                <span>📝</span> Summary
              </h2>
              <p className="text-gray-700 leading-relaxed text-lg">
                {result.summary}
              </p>

              {/* Metrics */}
              {result.metrics && (
                <div className="mt-6 pt-6 border-t border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-700 mb-4">Key Metrics</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center p-3 bg-blue-50 rounded-lg">
                      <div className="text-3xl mb-1">📄</div>
                      <div className="text-2xl font-bold text-gray-800">{result.metrics.file_count}</div>
                      <div className="text-xs text-gray-600">Files</div>
                    </div>
                    <div className="text-center p-3 bg-green-50 rounded-lg">
                      <div className="text-3xl mb-1">💾</div>
                      <div className="text-2xl font-bold text-gray-800">{result.metrics.commit_count}</div>
                      <div className="text-xs text-gray-600">Commits</div>
                    </div>
                    <div className="text-center p-3 bg-purple-50 rounded-lg">
                      <div className="text-3xl mb-1">🌿</div>
                      <div className="text-2xl font-bold text-gray-800">{result.metrics.branch_count}</div>
                      <div className="text-xs text-gray-600">Branches</div>
                    </div>
                    <div className="text-center p-3 bg-yellow-50 rounded-lg">
                      <div className="text-3xl mb-1">⭐</div>
                      <div className="text-2xl font-bold text-gray-800">{result.metrics.stars}</div>
                      <div className="text-xs text-gray-600">Stars</div>
                    </div>
                  </div>
                  
                  {result.metrics.languages && result.metrics.languages.length > 0 && (
                    <div className="mt-4">
                      <div className="text-sm font-semibold text-gray-700 mb-2">Languages:</div>
                      <div className="flex flex-wrap gap-2">
                        {result.metrics.languages.map((lang) => (
                          <span key={lang} className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm font-medium">
                            {lang}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Roadmap Card */}
            <div className="bg-white rounded-2xl shadow-2xl p-8">
              <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                <span>🗺️</span> Personalized Roadmap
              </h2>
              <p className="text-gray-600 mb-6">
                Follow these actionable steps to improve your repository:
              </p>
              <div className="space-y-3">
                {result.roadmap.map((step, index) => (
                  <div
                    key={index}
                    className="flex items-start gap-3 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg hover:shadow-md transition-shadow border-l-4 border-primary"
                  >
                    <div className="flex-shrink-0 w-7 h-7 bg-gradient-to-r from-primary to-secondary text-white rounded-full flex items-center justify-center font-bold text-sm">
                      {index + 1}
                    </div>
                    <p className="text-gray-800 flex-1 leading-relaxed">{step}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="text-center mt-12 text-white/70 text-sm">
          <p>Built with ❤️ for developers who want to level up their GitHub game</p>
          <p className="mt-1">Powered by AI • Real-time GitHub API Analysis</p>
        </div>
      </div>
    </div>
  )
}

export default App
