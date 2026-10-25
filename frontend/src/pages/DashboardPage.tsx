import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BookOpen,
  Users,
  CheckCircle,
  Clock,
  ArrowUpRight,
  Plus,
  Upload,
  FileCheck,
  BarChart2,
  AlertCircle,
  Activity
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid
} from 'recharts';
import { Navbar } from '../components/Navbar';
import { StatusBadge } from '../components/StatusBadge';
import { apiRequest } from '../api/client';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<any>(null);
  const [distribution, setDistribution] = useState<any[]>([]);
  const [subjectPerf, setSubjectPerf] = useState<any[]>([]);
  const [recentExams, setRecentExams] = useState<any[]>([]);
  const [recentActivity, setRecentActivity] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const [statsData, distData, subjData, examsData, actData] = await Promise.all([
        apiRequest('/analytics/dashboard-stats'),
        apiRequest('/analytics/marks-distribution'),
        apiRequest('/analytics/subject-performance'),
        apiRequest('/examinations'),
        apiRequest('/analytics/recent-activity?limit=6')
      ]);

      setStats(statsData);
      setDistribution(distData);
      setSubjectPerf(subjData);
      setRecentExams(examsData.slice(0, 4));
      setRecentActivity(actData);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Navbar title="Academic Evaluation Dashboard" subtitle="Real-time exam evaluation progress, review queues, and performance metrics" />
      
      <main className="p-8 space-y-8 max-w-7xl mx-auto w-full">
        {/* Quick Action Banner */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5 rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white shadow-sm">
          <div>
            <h2 className="text-lg font-bold">Welcome to GradeAI Human-in-the-Loop Evaluation</h2>
            <p className="text-xs text-slate-300 mt-0.5">
              Automate answer extraction & explainable scoring while keeping final grade approval strictly with teachers.
            </p>
          </div>
          <div className="flex items-center gap-2.5 shrink-0">
            <button
              onClick={() => navigate('/examinations')}
              className="inline-flex items-center px-3.5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-sm transition-colors"
            >
              <Plus className="w-3.5 h-3.5 mr-1.5" />
              New Examination
            </button>
            <button
              onClick={() => navigate('/upload')}
              className="inline-flex items-center px-3.5 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white text-xs font-semibold transition-colors border border-white/10"
            >
              <Upload className="w-3.5 h-3.5 mr-1.5" />
              Upload Answers
            </button>
            <button
              onClick={() => navigate('/review')}
              className="inline-flex items-center px-3.5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-sm transition-colors"
            >
              <FileCheck className="w-3.5 h-3.5 mr-1.5" />
              Review Workspace
            </button>
          </div>
        </div>

        {/* Real KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500">Total Examinations</span>
              <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
                <BookOpen className="w-4 h-4" />
              </div>
            </div>
            <p className="text-2xl font-bold text-slate-900 mt-2">{loading ? '...' : stats?.total_examinations || 0}</p>
            <div className="flex items-center text-[11px] text-slate-400 mt-1">
              <span>Managed in database</span>
            </div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500">Evaluated Students</span>
              <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
                <Users className="w-4 h-4" />
              </div>
            </div>
            <p className="text-2xl font-bold text-slate-900 mt-2">{loading ? '...' : stats?.total_students_evaluated || 0}</p>
            <div className="flex items-center text-[11px] text-emerald-600 mt-1 font-medium">
              <span>{stats?.finalized_submissions || 0} finalized</span>
            </div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500">Pending Teacher Reviews</span>
              <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center">
                <Clock className="w-4 h-4" />
              </div>
            </div>
            <p className="text-2xl font-bold text-slate-900 mt-2">{loading ? '...' : stats?.pending_teacher_reviews || 0}</p>
            <div className="flex items-center text-[11px] text-amber-600 mt-1 font-medium">
              <span>Requires instructor sign-off</span>
            </div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-500">Teacher Override Rate</span>
              <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
                <CheckCircle className="w-4 h-4" />
              </div>
            </div>
            <p className="text-2xl font-bold text-slate-900 mt-2">{loading ? '...' : `${stats?.teacher_override_rate || 0}%`}</p>
            <div className="flex items-center text-[11px] text-slate-400 mt-1">
              <span>Avg Approved Score: {stats?.average_approved_percentage || 0}%</span>
            </div>
          </div>
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Marks Distribution Histogram */}
          <div className="bg-white p-6 rounded-xl border border-slate-200/80 shadow-xs">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-bold text-slate-800">Approved Marks Distribution</h3>
                <p className="text-xs text-slate-500">Verified score brackets across student submissions</p>
              </div>
              <span className="text-[11px] font-semibold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">
                Live DB
              </span>
            </div>
            <div className="h-64 w-full">
              {distribution.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={distribution}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                    <XAxis dataKey="range_label" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={{ stroke: '#e2e8f0' }} />
                    <YAxis tick={{ fontSize: 11, fill: '#64748b' }} axisLine={{ stroke: '#e2e8f0' }} allowDecimals={false} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                      itemStyle={{ color: '#818cf8' }}
                    />
                    <Bar dataKey="count" fill="#4f46e5" radius={[4, 4, 0, 0]} name="Students" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-xs text-slate-400">
                  No evaluated submissions available yet.
                </div>
              )}
            </div>
          </div>

          {/* Subject Performance Breakdown */}
          <div className="bg-white p-6 rounded-xl border border-slate-200/80 shadow-xs">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-bold text-slate-800">Subject Performance Overview</h3>
                <p className="text-xs text-slate-500">Average student percentages across examination subjects</p>
              </div>
              <BarChart2 className="w-4 h-4 text-slate-400" />
            </div>
            <div className="h-64 w-full">
              {subjectPerf.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={subjectPerf} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
                    <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11, fill: '#64748b' }} unit="%" />
                    <YAxis dataKey="subject" type="category" tick={{ fontSize: 11, fill: '#64748b' }} width={120} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                      itemStyle={{ color: '#38bdf8' }}
                    />
                    <Bar dataKey="average_score" fill="#0284c7" radius={[0, 4, 4, 0]} name="Average %" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-xs text-slate-400">
                  No subject performance metrics yet.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Recent Examinations & Activity Feed */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Exams (2 cols) */}
          <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200/80 shadow-xs overflow-hidden">
            <div className="p-5 border-b border-slate-100 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-800">Recent Examinations</h3>
                <p className="text-xs text-slate-500">Latest active examination schemes</p>
              </div>
              <button
                onClick={() => navigate('/examinations')}
                className="text-xs font-semibold text-indigo-600 hover:text-indigo-700 flex items-center"
              >
                View all <ArrowUpRight className="w-3.5 h-3.5 ml-0.5" />
              </button>
            </div>

            <div className="divide-y divide-slate-100">
              {recentExams.map((exam) => (
                <div
                  key={exam.id}
                  onClick={() => navigate(`/examinations/${exam.id}`)}
                  className="p-4 hover:bg-slate-50/80 transition-colors cursor-pointer flex items-center justify-between"
                >
                  <div className="min-w-0 pr-4">
                    <h4 className="text-xs font-bold text-slate-900 truncate">{exam.title}</h4>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      {exam.subject} • {exam.class_name} • Total {exam.total_marks} Marks
                    </p>
                  </div>
                  <div className="flex items-center space-x-3 shrink-0">
                    <StatusBadge status={exam.status} size="sm" />
                    <span className="text-xs text-slate-400 font-medium">
                      {exam.submissions_count || 0} submissions
                    </span>
                  </div>
                </div>
              ))}
              {recentExams.length === 0 && (
                <div className="p-8 text-center text-xs text-slate-400">
                  No examinations created yet. Click "New Examination" to begin.
                </div>
              )}
            </div>
          </div>

          {/* Activity Stream (1 col) */}
          <div className="bg-white rounded-xl border border-slate-200/80 shadow-xs overflow-hidden">
            <div className="p-5 border-b border-slate-100 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Activity className="w-4 h-4 text-indigo-600" />
                <h3 className="text-sm font-bold text-slate-800">Audit Activity</h3>
              </div>
              <span className="text-[11px] text-slate-400">Real Log</span>
            </div>

            <div className="p-4 space-y-3">
              {recentActivity.map((act) => (
                <div key={act.id} className="text-xs flex items-start space-x-2.5">
                  <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 mt-1.5 shrink-0" />
                  <div>
                    <p className="text-slate-800 font-medium">{act.description}</p>
                    <p className="text-[10px] text-slate-400 mt-0.5">
                      by {act.user_name} • {act.timestamp}
                    </p>
                  </div>
                </div>
              ))}
              {recentActivity.length === 0 && (
                <p className="text-center text-xs text-slate-400 py-6">No recent actions logged.</p>
              )}
            </div>
          </div>
        </div>
      </main>
    </>
  );
};
