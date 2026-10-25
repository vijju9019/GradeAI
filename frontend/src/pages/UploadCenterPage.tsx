import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  UploadCloud,
  FileText,
  FileImage,
  CheckCircle,
  AlertCircle,
  Layers,
  ArrowRight,
  Eye,
  Trash2,
  Cpu,
  Edit,
  UserCheck
} from 'lucide-react';
import { Navbar } from '../components/Navbar';
import { StatusBadge } from '../components/StatusBadge';
import { apiRequest } from '../api/client';

export const UploadCenterPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const queryExamId = searchParams.get('examId');

  const [exams, setExams] = useState<any[]>([]);
  const [selectedExamId, setSelectedExamId] = useState<string>(queryExamId || '');
  const [submissions, setSubmissions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  // Form State
  const [studentId, setStudentId] = useState('');
  const [studentName, setStudentName] = useState('');
  const [studentRollNo, setStudentRollNo] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  useEffect(() => {
    fetchExams();
  }, []);

  useEffect(() => {
    if (selectedExamId) {
      fetchSubmissions(selectedExamId);
    }
  }, [selectedExamId]);

  const fetchExams = async () => {
    try {
      const data = await apiRequest('/examinations');
      setExams(data);
      if (!selectedExamId && data.length > 0) {
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
    } catch (err) {
      console.error('Failed to load submissions:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setUploadError(null);
    }
  };

  const handleUploadSubmission = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedExamId) {
      setUploadError('Please select an examination first.');
      return;
    }
    if (!file) {
      setUploadError('Please select a student answer sheet file.');
      return;
    }

    setUploadError(null);
    setUploadSuccess(null);
    setIsUploading(true);

    try {
      // 1. Create Student Submission
      const sub = await apiRequest(`/examinations/${selectedExamId}/submissions`, {
        method: 'POST',
        body: JSON.stringify({
          examination_id: parseInt(selectedExamId, 10),
          student_id: studentId,
          student_name: studentName,
          student_roll_no: studentRollNo || undefined
        })
      });

      // 2. Upload Document & Extract text
      const formData = new FormData();
      formData.append('file', file);

      await apiRequest(`/submissions/${sub.id}/upload`, {
        method: 'POST',
        body: formData
      });

      // 3. Automatically run initial segmentation
      await apiRequest(`/submissions/${sub.id}/segment`, {
        method: 'POST'
      });

      setUploadSuccess(`Answer sheet for ${studentName} successfully uploaded, extracted, and segmented!`);
      // Reset form
      setStudentId('');
      setStudentName('');
      setStudentRollNo('');
      setFile(null);
      fetchSubmissions(selectedExamId);
    } catch (err: any) {
      setUploadError(err.message || 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDeleteSubmission = async (subId: number) => {
    if (!window.confirm('Delete this submission and its evaluation records?')) return;
    try {
      await apiRequest(`/submissions/${subId}`, { method: 'DELETE' });
      fetchSubmissions(selectedExamId);
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  return (
    <>
      <Navbar title="Answer Sheet Upload & Intake Center" subtitle="Ingest student answer sheets (PDF, Images, Text) with document extraction and segmentation" />

      <main className="p-8 max-w-7xl mx-auto w-full space-y-8">
        {/* Examination Selector */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
              Active Examination
            </label>
            <select
              value={selectedExamId}
              onChange={(e) => setSelectedExamId(e.target.value)}
              className="text-sm font-bold text-slate-800 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-600"
            >
              {exams.map((ex) => (
                <option key={ex.id} value={ex.id}>
                  {ex.title} ({ex.subject} • Total {ex.total_marks} Marks)
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center space-x-2 text-xs text-slate-500">
            <span>Submissions: <strong className="text-slate-900">{submissions.length}</strong></span>
          </div>
        </div>

        {/* Upload Form Card */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-5">
          <div className="border-b border-slate-100 pb-3">
            <h3 className="text-sm font-bold text-slate-900 flex items-center">
              <UploadCloud className="w-4 h-4 mr-2 text-indigo-600" />
              Upload Student Answer Sheet
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Supports scanned PDFs, digital PDFs, plain text, and high-contrast printed answer sheet images.
            </p>
          </div>

          {uploadError && (
            <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{uploadError}</span>
            </div>
          )}

          {uploadSuccess && (
            <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs flex items-center space-x-2">
              <CheckCircle className="w-4 h-4 shrink-0" />
              <span>{uploadSuccess}</span>
            </div>
          )}

          <form onSubmit={handleUploadSubmission} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Student Identifier (ID)</label>
                <input
                  type="text"
                  required
                  value={studentId}
                  onChange={(e) => setStudentId(e.target.value)}
                  placeholder="e.g. STU-2026-004"
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-600"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Student Full Name</label>
                <input
                  type="text"
                  required
                  value={studentName}
                  onChange={(e) => setStudentName(e.target.value)}
                  placeholder="e.g. Priya Nair"
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-600"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Roll / Seat Number</label>
                <input
                  type="text"
                  value={studentRollNo}
                  onChange={(e) => setStudentRollNo(e.target.value)}
                  placeholder="e.g. CS-22-089"
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-600"
                />
              </div>
            </div>

            {/* Drop Zone */}
            <div className="border-2 border-dashed border-slate-300 rounded-xl p-6 text-center hover:border-indigo-400 transition-colors bg-slate-50/50">
              <input
                type="file"
                id="file-upload"
                onChange={handleFileChange}
                accept=".pdf,.png,.jpg,.jpeg,.txt"
                className="hidden"
              />
              <label htmlFor="file-upload" className="cursor-pointer">
                <div className="w-10 h-10 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto mb-2">
                  <FileText className="w-5 h-5" />
                </div>
                <p className="text-xs font-semibold text-slate-800">
                  {file ? file.name : 'Click to select or drag and drop answer sheet'}
                </p>
                <p className="text-[11px] text-slate-400 mt-1">
                  Supported formats: PDF, PNG, JPG, JPEG, TXT (Max 25MB)
                </p>
              </label>
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="submit"
                disabled={isUploading}
                className="inline-flex items-center px-4 py-2.5 rounded-lg bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-700 shadow-xs transition-colors disabled:opacity-50"
              >
                <UploadCloud className="w-4 h-4 mr-1.5" />
                {isUploading ? 'Extracting & Segmenting...' : 'Upload & Process Submission'}
              </button>
            </div>
          </form>
        </div>

        {/* Existing Submissions Table */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="p-5 border-b border-slate-100 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Student Submissions Queue</h3>
              <p className="text-xs text-slate-500">Track extraction, segmentation, AI evaluation, and teacher approval status</p>
            </div>
            <button
              onClick={() => fetchSubmissions(selectedExamId)}
              className="text-xs text-indigo-600 hover:text-indigo-700 font-semibold"
            >
              Refresh Table
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-xs">
              <thead className="bg-slate-50 text-slate-600 font-semibold">
                <tr>
                  <th className="px-4 py-3 text-left">Student Info</th>
                  <th className="px-4 py-3 text-left">Status</th>
                  <th className="px-4 py-3 text-center">Suggested Marks</th>
                  <th className="px-4 py-3 text-center">Approved Marks</th>
                  <th className="px-4 py-3 text-center">Percentage</th>
                  <th className="px-4 py-3 text-right">Workflow Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {submissions.map((sub) => (
                  <tr key={sub.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="px-4 py-3">
                      <div className="font-bold text-slate-900">{sub.student_name}</div>
                      <div className="text-[11px] text-slate-500">
                        {sub.student_id} {sub.student_roll_no ? `• ${sub.student_roll_no}` : ''}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={sub.status} size="sm" />
                    </td>
                    <td className="px-4 py-3 text-center font-medium text-slate-700">
                      {sub.total_suggested_marks ? `${sub.total_suggested_marks}` : '-'}
                    </td>
                    <td className="px-4 py-3 text-center font-bold text-indigo-700">
                      {sub.total_approved_marks ? `${sub.total_approved_marks}` : '-'}
                    </td>
                    <td className="px-4 py-3 text-center font-bold text-slate-900">
                      {sub.percentage ? `${sub.percentage}%` : '-'}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          onClick={() => navigate(`/review/${sub.id}`)}
                          className="px-2.5 py-1 rounded bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-[11px] flex items-center"
                        >
                          <UserCheck className="w-3.5 h-3.5 mr-1" />
                          Teacher Review
                        </button>
                        <button
                          onClick={() => handleDeleteSubmission(sub.id)}
                          className="p-1 text-slate-400 hover:text-rose-600 rounded"
                          title="Delete submission"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}

                {submissions.length === 0 && !loading && (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-xs text-slate-400">
                      No student submissions uploaded for this examination yet.
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
