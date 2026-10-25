import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Plus,
  BookOpen,
  Search,
  Filter,
  Calendar,
  Clock,
  Layers,
  ArrowRight,
  Trash2,
  Edit3,
  FileCheck,
  AlertTriangle
} from 'lucide-react';
import { Navbar } from '../components/Navbar';
import { StatusBadge } from '../components/StatusBadge';
import { Modal } from '../components/Modal';
import { apiRequest } from '../api/client';

export const ExamsPage: React.FC = () => {
  const navigate = useNavigate();
  const [exams, setExams] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // Modal State
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<any>(null);

  // Form State
  const [title, setTitle] = useState('');
  const [subject, setSubject] = useState('');
  const [className, setClassName] = useState('');
  const [academicYear, setAcademicYear] = useState('2026-2027');
  const [examDate, setExamDate] = useState('2026-10-25');
  const [totalMarks, setTotalMarks] = useState('50');
  const [durationMinutes, setDurationMinutes] = useState('120');
  const [description, setDescription] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    fetchExams();
  }, [statusFilter]);

  const fetchExams = async () => {
    try {
      setLoading(true);
      const url = statusFilter ? `/examinations?status=${statusFilter}` : '/examinations';
      const data = await apiRequest(url);
      setExams(data);
    } catch (err) {
      console.error('Failed to load examinations:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateExam = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    try {
      const newExam = await apiRequest('/examinations', {
        method: 'POST',
        body: JSON.stringify({
          title,
          subject,
          class_name: className,
          academic_year: academicYear,
          exam_date: examDate,
          total_marks: parseFloat(totalMarks),
          duration_minutes: parseInt(durationMinutes, 10),
          description
        })
      });

      setIsCreateOpen(false);
      resetForm();
      fetchExams();
      navigate(`/examinations/${newExam.id}`);
    } catch (err: any) {
      setFormError(err.message || 'Failed to create examination');
    }
  };

  const handleDeleteExam = async () => {
    if (!deleteTarget) return;
    try {
      await apiRequest(`/examinations/${deleteTarget.id}`, { method: 'DELETE' });
      setDeleteTarget(null);
      fetchExams();
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  const resetForm = () => {
    setTitle('');
    setSubject('');
    setClassName('');
    setDescription('');
    setTotalMarks('50');
    setDurationMinutes('120');
  };

  const filteredExams = exams.filter((ex) =>
    ex.title.toLowerCase().includes(search.toLowerCase()) ||
    ex.subject.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <>
      <Navbar title="Examination Management" subtitle="Define exam details, question schemes, model answers, and rubrics" />

      <main className="p-8 max-w-7xl mx-auto w-full space-y-6">
        {/* Header & Controls */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search examination or subject..."
                className="pl-9 pr-4 py-2 text-xs rounded-lg border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-600 w-64"
              />
            </div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="py-2 px-3 text-xs rounded-lg border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-600 text-slate-700 font-medium"
            >
              <option value="">All Statuses</option>
              <option value="draft">Draft</option>
              <option value="ready">Ready</option>
              <option value="processing">Processing</option>
              <option value="review_pending">Review Pending</option>
              <option value="finalized">Finalized</option>
            </select>
          </div>

          <button
            onClick={() => setIsCreateOpen(true)}
            className="inline-flex items-center px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs transition-colors"
          >
            <Plus className="w-4 h-4 mr-1.5" />
            Create Examination
          </button>
        </div>

        {/* Examinations Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredExams.map((exam) => (
            <div
              key={exam.id}
              className="bg-white rounded-xl border border-slate-200 shadow-xs hover:border-indigo-200 transition-all flex flex-col justify-between"
            >
              <div className="p-5 space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <span className="text-[11px] font-semibold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded">
                    {exam.subject}
                  </span>
                  <StatusBadge status={exam.status} size="sm" />
                </div>

                <div>
                  <h3 className="text-sm font-bold text-slate-900 leading-snug hover:text-indigo-600 transition-colors cursor-pointer" onClick={() => navigate(`/examinations/${exam.id}`)}>
                    {exam.title}
                  </h3>
                  <p className="text-xs text-slate-500 mt-1 line-clamp-2">
                    {exam.description || 'No description provided.'}
                  </p>
                </div>

                <div className="pt-2 border-t border-slate-100 grid grid-cols-2 gap-2 text-[11px] text-slate-600">
                  <div className="flex items-center space-x-1.5">
                    <Calendar className="w-3.5 h-3.5 text-slate-400" />
                    <span>{exam.exam_date}</span>
                  </div>
                  <div className="flex items-center space-x-1.5">
                    <Clock className="w-3.5 h-3.5 text-slate-400" />
                    <span>{exam.duration_minutes} mins</span>
                  </div>
                  <div className="flex items-center space-x-1.5">
                    <Layers className="w-3.5 h-3.5 text-slate-400" />
                    <span>{exam.questions_count || 0} Questions</span>
                  </div>
                  <div className="flex items-center space-x-1.5 font-semibold text-slate-800">
                    <span>Total {exam.total_marks} Marks</span>
                  </div>
                </div>
              </div>

              {/* Card Footer Actions */}
              <div className="px-5 py-3 bg-slate-50/70 border-t border-slate-100 rounded-b-xl flex items-center justify-between">
                <button
                  onClick={() => setDeleteTarget(exam)}
                  className="text-slate-400 hover:text-rose-600 p-1.5 rounded-md hover:bg-white transition-colors"
                  title="Delete examination"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => navigate(`/examinations/${exam.id}`)}
                    className="inline-flex items-center px-3 py-1.5 text-xs font-semibold rounded-lg bg-white border border-slate-200 text-slate-700 hover:bg-slate-100 transition-colors"
                  >
                    <Edit3 className="w-3.5 h-3.5 mr-1" />
                    Scheme
                  </button>
                  <button
                    onClick={() => navigate(`/upload?examId=${exam.id}`)}
                    className="inline-flex items-center px-3 py-1.5 text-xs font-semibold rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 transition-colors"
                  >
                    Submissions ({exam.submissions_count || 0})
                  </button>
                </div>
              </div>
            </div>
          ))}

          {filteredExams.length === 0 && !loading && (
            <div className="col-span-full py-16 text-center bg-white rounded-xl border border-dashed border-slate-300">
              <BookOpen className="w-10 h-10 text-slate-300 mx-auto mb-3" />
              <h3 className="text-sm font-bold text-slate-700">No examinations found</h3>
              <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
                Create a new examination to define marking schemes and upload student answer sheets.
              </p>
              <button
                onClick={() => setIsCreateOpen(true)}
                className="mt-4 inline-flex items-center px-3.5 py-2 text-xs font-semibold rounded-lg bg-indigo-600 text-white hover:bg-indigo-700"
              >
                <Plus className="w-3.5 h-3.5 mr-1.5" />
                Create First Exam
              </button>
            </div>
          )}
        </div>

        {/* Create Examination Modal */}
        <Modal
          isOpen={isCreateOpen}
          onClose={() => setIsCreateOpen(false)}
          title="Create New Examination"
          maxWidth="lg"
        >
          {formError && (
            <div className="mb-4 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{formError}</span>
            </div>
          )}
          <form onSubmit={handleCreateExam} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Examination Title</label>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. CS301: Operating Systems & Data Structures Midterm"
                className="w-full text-xs p-2.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-600"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Subject / Course</label>
                <input
                  type="text"
                  required
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  placeholder="e.g. Computer Science"
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-600"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Class / Semester</label>
                <input
                  type="text"
                  required
                  value={className}
                  onChange={(e) => setClassName(e.target.value)}
                  placeholder="e.g. B.Tech Semester V"
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-600"
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Academic Year</label>
                <input
                  type="text"
                  required
                  value={academicYear}
                  onChange={(e) => setAcademicYear(e.target.value)}
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-600"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Exam Date</label>
                <input
                  type="date"
                  required
                  value={examDate}
                  onChange={(e) => setExamDate(e.target.value)}
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-600"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Total Marks</label>
                <input
                  type="number"
                  required
                  min="1"
                  value={totalMarks}
                  onChange={(e) => setTotalMarks(e.target.value)}
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-600"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Duration (Minutes)</label>
              <input
                type="number"
                required
                min="1"
                value={durationMinutes}
                onChange={(e) => setDurationMinutes(e.target.value)}
                className="w-full text-xs p-2.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-600"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Description / Instructions</label>
              <textarea
                rows={2}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Optional assessment guidelines or syllabus topics..."
                className="w-full text-xs p-2.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-600"
              />
            </div>

            <div className="flex justify-end space-x-2 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setIsCreateOpen(false)}
                className="px-4 py-2 text-xs font-semibold rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-xs font-semibold rounded-lg bg-indigo-600 text-white hover:bg-indigo-700"
              >
                Create & Add Questions
              </button>
            </div>
          </form>
        </Modal>

        {/* Delete Confirmation Modal */}
        <Modal
          isOpen={!!deleteTarget}
          onClose={() => setDeleteTarget(null)}
          title="Confirm Examination Deletion"
          maxWidth="sm"
        >
          <div className="space-y-3">
            <p className="text-xs text-slate-600">
              Are you sure you want to delete <span className="font-bold text-slate-900">{deleteTarget?.title}</span>?
              All questions, uploaded answer sheets, and evaluation records will be permanently removed.
            </p>
            <div className="flex justify-end space-x-2 pt-3 border-t border-slate-100">
              <button
                onClick={() => setDeleteTarget(null)}
                className="px-3.5 py-1.5 text-xs font-semibold rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteExam}
                className="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-rose-600 text-white hover:bg-rose-700"
              >
                Delete Permanently
              </button>
            </div>
          </div>
        </Modal>
      </main>
    </>
  );
};
