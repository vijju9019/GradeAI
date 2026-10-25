import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { Navbar } from '../components/Navbar';
import { apiRequest } from '../api/client';

export const AnalyticsPage: React.FC = () => {
  const [stats, setStats] = useState<any>(null);
  const [distribution, setDistribution] = useState<any[]>([]);
  const [subjectPerf, setSubjectPerf] = useState<any[]>([]);
  const [questionsDifficulty, setQuestionsDifficulty] = useState<any[]>([]);
  const [exams, setExams] = useState<any[]>([]);
  const [selectedExamId, setSelectedExamId] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchInitialData();
  }, []);

  useEffect(() => {
    if (selectedExamId) {
      fetchExamDifficulty(selectedExamId);
    }
  }, [selectedExamId]);

  const fetchInitialData = async () => {
    try {
      setLoading(true);
      const [statsData, distData, subjData, examsData] = await Promise.all([
        apiRequest('/analytics/dashboard-stats'),
        apiRequest('/analytics/marks-distribution'),
        apiRequest('/analytics/subject-performance'),
        apiRequest('/examinations')
      ]);

      setStats(statsData);
      setDistribution(distData);
      setSubjectPerf(subjData);
      setExams(examsData);
      if (examsData.length > 0) {
        setSelectedExamId(examsData[0].id.toString());
      }
    } catch (err) {
      console.error('Failed to load analytics data:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchExamDifficulty = async (examId: string) => {
    try {
      const diffData = await apiRequest(`/analytics/examinations/${examId}/difficulty`);
      setQuestionsDifficulty(diffData);
    } catch (err) {
      console.error('Failed to load difficulty breakdown:', err);
    }
  };

  const COLORS = ['#ef4444', '#f97316', '#eab308', '#06b6d4', '#10b981'];

  return (
    <>
      <Navbar title="Academic Evaluation Analytics" subtitle="Database-derived difficulty distributions, question trends, and teacher calibration metrics" />

      <main className="p-8 max-w-7xl mx-auto w-full space-y-8">
        {/* Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
            <span className="text-xs font-semibold text-slate-500">Average Approved Score</span>
            <p className="text-2xl font-bold text-slate-900 mt-2">{stats?.average_approved_percentage || 0}%</p>
            <span className="text-[11px] text-slate-400 mt-1 block">Across finalized submissions</span>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
            <span className="text-xs font-semibold text-slate-500">Teacher Override Rate</span>
            <p className="text-2xl font-bold text-indigo-700 mt-2">{stats?.teacher_override_rate || 0}%</p>
            <span className="text-[11px] text-slate-400 mt-1 block">Marks modified by instructor</span>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
            <span className="text-xs font-semibold text-slate-500">OCR Extraction Success Rate</span>
            <p className="text-2xl font-bold text-emerald-600 mt-2">{stats?.ocr_success_rate || 100}%</p>
            <span className="text-[11px] text-slate-400 mt-1 block">Legible digital / scan quality</span>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
            <span className="text-xs font-semibold text-slate-500">Pending Review Queue</span>
            <p className="text-2xl font-bold text-amber-600 mt-2">{stats?.pending_teacher_reviews || 0}</p>
            <span className="text-[11px] text-slate-400 mt-1 block">Submissions awaiting sign-off</span>
          </div>
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs">
            <h3 className="text-sm font-bold text-slate-900 mb-1">Approved Marks Distribution Histogram</h3>
            <p className="text-xs text-slate-500 mb-4">Breakdown of students across grade brackets</p>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={distribution}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                  <XAxis dataKey="range_label" tick={{ fontSize: 11, fill: '#64748b' }} />
                  <YAxis tick={{ fontSize: 11, fill: '#64748b' }} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                  />
                  <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} name="Students" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs">
            <h3 className="text-sm font-bold text-slate-900 mb-1">Subject Performance Comparison</h3>
            <p className="text-xs text-slate-500 mb-4">Average percentage attained by department</p>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={subjectPerf} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
                  <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11, fill: '#64748b' }} unit="%" />
                  <YAxis dataKey="subject" type="category" tick={{ fontSize: 11, fill: '#64748b' }} width={120} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                  />
                  <Bar dataKey="average_score" fill="#0ea5e9" radius={[0, 4, 4, 0]} name="Average Score %" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Question Difficulty Rating Table */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="p-5 border-b border-slate-100 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Question Difficulty & Discrimination Assessment</h3>
              <p className="text-xs text-slate-500">Derived from actual student performance and teacher awarded marks</p>
            </div>
            <select
              value={selectedExamId}
              onChange={(e) => setSelectedExamId(e.target.value)}
              className="text-xs font-bold text-slate-900 bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5"
            >
              {exams.map((ex) => (
                <option key={ex.id} value={ex.id}>
                  {ex.title}
                </option>
              ))}
            </select>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-xs">
              <thead className="bg-slate-50 text-slate-600 font-semibold">
                <tr>
                  <th className="px-4 py-3 text-left">Question Number</th>
                  <th className="px-4 py-3 text-center">Maximum Marks</th>
                  <th className="px-4 py-3 text-center">Average Awarded</th>
                  <th className="px-4 py-3 text-center">Success Rate (%)</th>
                  <th className="px-4 py-3 text-right">Assessed Difficulty</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {questionsDifficulty.map((qd, i) => {
                  let badgeBg = 'bg-emerald-50 text-emerald-700 border-emerald-200';
                  if (qd.difficulty === 'Challenging') {
                    badgeBg = 'bg-rose-50 text-rose-700 border-rose-200';
                  } else if (qd.difficulty === 'Moderate') {
                    badgeBg = 'bg-amber-50 text-amber-700 border-amber-200';
                  }

                  return (
                    <tr key={i} className="hover:bg-slate-50/70">
                      <td className="px-4 py-3 font-bold text-slate-900">Question {qd.question_number}</td>
                      <td className="px-4 py-3 text-center text-slate-500">{qd.max_marks}</td>
                      <td className="px-4 py-3 text-center font-semibold text-slate-800">{qd.average_marks}</td>
                      <td className="px-4 py-3 text-center font-bold text-indigo-700">{qd.average_percentage}%</td>
                      <td className="px-4 py-3 text-right">
                        <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold border ${badgeBg}`}>
                          {qd.difficulty}
                        </span>
                      </td>
                    </tr>
                  );
                })}

                {questionsDifficulty.length === 0 && (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-xs text-slate-400">
                      No question difficulty data available for this examination.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </>
  );
};
