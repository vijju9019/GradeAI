import React, { useState, useEffect } from 'react';
import {
  FileText,
  Download,
  FileSpreadsheet,
  CheckCircle,
  Clock,
  Printer,
  ChevronRight,
  ShieldCheck,
  User,
  Search
} from 'lucide-react';
import { Navbar } from '../components/Navbar';
import { StatusBadge } from '../components/StatusBadge';
import { apiRequest } from '../api/client';

export const ReportsPage: React.FC = () => {
  const [exams, setExams] = useState<any[]>([]);
  const [selectedExamId, setSelectedExamId] = useState<string>('');
  const [submissions, setSubmissions] = useState<any[]>([]);
  const [selectedSubId, setSelectedSubId] = useState<string>('');
  const [scorecard, setScorecard] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    fetchExams();
  }, []);

  useEffect(() => {
    if (selectedExamId) {
      fetchSubmissions(selectedExamId);
    }
  }, [selectedExamId]);

  useEffect(() => {
    if (selectedSubId) {
      fetchScorecard(selectedSubId);
    }
  }, [selectedSubId]);

  const fetchExams = async () => {
    try {
      const data = await apiRequest('/examinations');
      setExams(data);
      if (data.length > 0) {
        setSelectedExamId(data[0].id.toString());
      }
    } catch (err) {
      console.error('Failed to load examinations:', err);
    }
  };

  const fetchSubmissions = async (examId: string) => {
    try {
      setLoading(true);
      const data = await apiRequest(`/examinations/${examId}/submissions`);
      setSubmissions(data);
      if (data.length > 0) {
        setSelectedSubId(data[0].id.toString());
      } else {
        setSelectedSubId('');
        setScorecard(null);
      }
    } catch (err) {
      console.error('Failed to load submissions:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchScorecard = async (subId: string) => {
    try {
      setLoading(true);
      const data = await apiRequest(`/reports/submissions/${subId}/report`);
      setScorecard(data);
    } catch (err) {
      console.error('Failed to load scorecard:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPDF = async () => {
    if (!selectedSubId) return;
    setDownloading(true);
    try {
      const blob = await apiRequest(`/reports/submissions/${selectedSubId}/report/pdf`);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Scorecard_${scorecard?.student_id || 'student'}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err: any) {
      alert(`PDF download failed: ${err.message}`);
    } finally {
      setDownloading(false);
    }
  };

  const handleDownloadCSV = async () => {
    if (!selectedExamId) return;
    try {
      const blob = await apiRequest(`/reports/examinations/${selectedExamId}/report/csv`);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `exam_${selectedExamId}_results.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err: any) {
      alert(`CSV download failed: ${err.message}`);
    }
  };

  const handleDownloadExcel = async () => {
    if (!selectedExamId) return;
    try {
      const blob = await apiRequest(`/reports/examinations/${selectedExamId}/report/excel`);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `exam_${selectedExamId}_results.xlsx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err: any) {
      alert(`Excel download failed: ${err.message}`);
    }
  };

  return (
    <>
      <Navbar title="Results, Scorecards & Report Center" subtitle="Download official certified academic scorecards (PDF) and export mark distributions (CSV/Excel)" />

      <main className="p-8 max-w-7xl mx-auto w-full space-y-6">
        {/* Top Controls & Bulk Export Bar */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-4">
            <div>
              <label className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1">
                Select Examination
              </label>
              <select
                value={selectedExamId}
                onChange={(e) => setSelectedExamId(e.target.value)}
                className="text-xs font-bold text-slate-900 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2"
              >
                {exams.map((ex) => (
                  <option key={ex.id} value={ex.id}>
                    {ex.title} ({ex.subject})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1">
                Student Submission
              </label>
              <select
                value={selectedSubId}
                onChange={(e) => setSelectedSubId(e.target.value)}
                disabled={submissions.length === 0}
                className="text-xs font-bold text-slate-900 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 disabled:opacity-50"
              >
                {submissions.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.student_name} ({s.student_id}) — {s.is_finalized ? 'Finalized' : 'Draft'}
                  </option>
                ))}
                {submissions.length === 0 && <option value="">No submissions</option>}
              </select>
            </div>
          </div>

          {/* Export Buttons */}
          <div className="flex items-center space-x-2 shrink-0">
            <button
              onClick={handleDownloadCSV}
              className="inline-flex items-center px-3 py-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold shadow-xs"
            >
              <Download className="w-3.5 h-3.5 mr-1.5 text-slate-500" />
              Export CSV
            </button>
            <button
              onClick={handleDownloadExcel}
              className="inline-flex items-center px-3 py-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold shadow-xs"
            >
              <FileSpreadsheet className="w-3.5 h-3.5 mr-1.5 text-emerald-600" />
              Export Excel (.xlsx)
            </button>
            <button
              onClick={handleDownloadPDF}
              disabled={downloading || !scorecard}
              className="inline-flex items-center px-3.5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs disabled:opacity-50"
            >
              <Printer className="w-3.5 h-3.5 mr-1.5" />
              {downloading ? 'Rendering PDF...' : 'Download Scorecard PDF'}
            </button>
          </div>
        </div>

        {/* Scorecard Preview Canvas */}
        {scorecard ? (
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-8 space-y-6 max-w-4xl mx-auto">
            {/* Academic Header Banner */}
            <div className="text-center border-b border-slate-200 pb-6 space-y-1">
              <span className="text-[11px] font-bold text-indigo-700 tracking-wider uppercase">
                GradeAI — Automated Examination Evaluation System
              </span>
              <h2 className="text-xl font-bold text-slate-900">{scorecard.exam_title}</h2>
              <p className="text-xs text-slate-500">
                Subject: {scorecard.subject} • Class: {scorecard.class_name} • Academic Year: {scorecard.academic_year}
              </p>
            </div>

            {/* Student & Score Meta Info Box */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs">
              <div>
                <span className="text-slate-400 block text-[11px]">Student Name</span>
                <span className="font-bold text-slate-900">{scorecard.student_name}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[11px]">Student ID / Roll No</span>
                <span className="font-bold text-slate-900">{scorecard.student_id} ({scorecard.student_roll_no || 'N/A'})</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[11px]">Total Approved Score</span>
                <span className="font-bold text-indigo-700 text-sm">
                  {scorecard.total_approved_marks} / {scorecard.total_exam_marks}
                </span>
              </div>
              <div>
                <span className="text-slate-400 block text-[11px]">Percentage</span>
                <span className="font-extrabold text-slate-900 text-sm">{scorecard.percentage}%</span>
              </div>
            </div>

            {/* Questions Table */}
            <div>
              <h4 className="text-xs font-bold text-slate-900 mb-3">Question-by-Question Evaluation Breakdown</h4>
              <div className="border border-slate-200 rounded-lg overflow-hidden text-xs">
                <table className="min-w-full divide-y divide-slate-200">
                  <thead className="bg-slate-900 text-white font-semibold">
                    <tr>
                      <th className="px-3.5 py-2.5 text-left w-12">Q#</th>
                      <th className="px-3.5 py-2.5 text-left">Question Details</th>
                      <th className="px-3.5 py-2.5 text-center w-16">Max</th>
                      <th className="px-3.5 py-2.5 text-center w-24">AI Suggested</th>
                      <th className="px-3.5 py-2.5 text-center w-24">Approved</th>
                      <th className="px-3.5 py-2.5 text-left">Teacher Audit Notes</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 bg-white">
                    {scorecard.questions.map((q: any, i: number) => (
                      <tr key={i} className="hover:bg-slate-50/70">
                        <td className="px-3.5 py-2.5 font-bold text-slate-900">Q{q.question_number}</td>
                        <td className="px-3.5 py-2.5 text-slate-700 max-w-xs truncate">{q.question_text}</td>
                        <td className="px-3.5 py-2.5 text-center text-slate-500">{q.max_marks}</td>
                        <td className="px-3.5 py-2.5 text-center font-medium text-slate-600">{q.suggested_marks}</td>
                        <td className="px-3.5 py-2.5 text-center font-bold text-indigo-700">{q.approved_marks}</td>
                        <td className="px-3.5 py-2.5 text-slate-500 text-[11px]">{q.review_notes || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Certification Footer */}
            <div className="pt-4 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
              <div className="flex items-center space-x-1.5">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                <span>Certified by Course Instructor • Status: {scorecard.is_finalized ? 'Finalized' : 'Draft Review'}</span>
              </div>
              <span className="text-[11px] text-slate-400">Generated on {new Date(scorecard.generated_at).toLocaleString()}</span>
            </div>
          </div>
        ) : (
          <div className="bg-white p-16 rounded-xl border border-dashed border-slate-300 text-center text-xs text-slate-400">
            No student scorecard selected. Please choose an examination and student submission above.
          </div>
        )}
      </main>
    </>
  );
};
