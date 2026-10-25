import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  FileCheck,
  Edit,
  Save,
  MessageSquare,
  Sparkles,
  HelpCircle,
  Eye,
  Lock,
  ChevronRight,
  ShieldCheck,
  ArrowRight,
  RotateCcw
} from 'lucide-react';
import { Navbar } from '../components/Navbar';
import { StatusBadge } from '../components/StatusBadge';
import { Modal } from '../components/Modal';
import { apiRequest } from '../api/client';

export const TeacherReviewPage: React.FC = () => {
  const { submissionId } = useParams<{ submissionId: string }>();
  const navigate = useNavigate();

  const [submissionsList, setSubmissionsList] = useState<any[]>([]);
  const [activeSubId, setActiveSubId] = useState<string>(submissionId || '');
  const [submission, setSubmission] = useState<any>(null);
  const [exam, setExam] = useState<any>(null);
  const [evaluationResults, setEvaluationResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Active Question under review
  const [selectedQuestionIndex, setSelectedQuestionIndex] = useState(0);

  // Teacher Mark Edit State
  const [teacherMarksInput, setTeacherMarksInput] = useState<string>('');
  const [reviewNotesInput, setReviewNotesInput] = useState<string>('');
  const [isSavingMark, setIsSavingMark] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Finalize Confirmation Modal
  const [isFinalizeModalOpen, setIsFinalizeModalOpen] = useState(false);
  const [isBatchApproveModalOpen, setIsBatchApproveModalOpen] = useState(false);

  useEffect(() => {
    fetchAllSubmissions();
  }, []);

  useEffect(() => {
    if (activeSubId) {
      loadSubmissionDetails(activeSubId);
    }
  }, [activeSubId]);

  const fetchAllSubmissions = async () => {
    try {
      const examsData = await apiRequest('/examinations');
      if (examsData.length > 0) {
        const subsData = await apiRequest(`/examinations/${examsData[0].id}/submissions`);
        setSubmissionsList(subsData);
        if (!activeSubId && subsData.length > 0) {
          setActiveSubId(subsData[0].id.toString());
        }
      }
    } catch (err) {
      console.error('Failed to load submissions list:', err);
    }
  };

  const loadSubmissionDetails = async (subId: string) => {
    try {
      setLoading(true);
      const sub = await apiRequest(`/submissions/${subId}`);
      setSubmission(sub);

      const examData = await apiRequest(`/examinations/${sub.examination_id}`);
      setExam(examData);

      // Check if evaluation results exist; if not, trigger evaluation
      let results = await apiRequest(`/submissions/${subId}/evaluation-results`);
      if (results.length === 0) {
        await apiRequest(`/submissions/${subId}/evaluate`, { method: 'POST' });
        results = await apiRequest(`/submissions/${subId}/evaluation-results`);
      }

      setEvaluationResults(results);
      if (results.length > 0) {
        setSelectedQuestionIndex(0);
        const first = results[0];
        setTeacherMarksInput(first.teacher_marks !== null ? first.teacher_marks.toString() : first.suggested_marks.toString());
        setReviewNotesInput(first.review_notes || '');
      }
    } catch (err) {
      console.error('Failed to load submission review details:', err);
    } finally {
      setLoading(false);
    }
  };

  const currentResult = evaluationResults[selectedQuestionIndex];

  const handleSelectQuestion = (index: number) => {
    setSelectedQuestionIndex(index);
    const item = evaluationResults[index];
    if (item) {
      setTeacherMarksInput(item.teacher_marks !== null ? item.teacher_marks.toString() : item.suggested_marks.toString());
      setReviewNotesInput(item.review_notes || '');
      setSaveMessage(null);
      setErrorMessage(null);
    }
  };

  const handleSaveTeacherMark = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentResult) return;
    setErrorMessage(null);
    setSaveMessage(null);

    const markVal = parseFloat(teacherMarksInput);
    if (isNaN(markVal)) {
      setErrorMessage('Please enter a valid numeric mark.');
      return;
    }
    if (markVal < 0 || markVal > currentResult.max_marks) {
      setErrorMessage(`Awarded marks must be between 0 and the maximum mark (${currentResult.max_marks}).`);
      return;
    }

    setIsSavingMark(true);
    try {
      await apiRequest(`/reviews/submissions/${activeSubId}/override`, {
        method: 'POST',
        body: JSON.stringify({
          question_id: currentResult.question_id,
          teacher_marks: markVal,
          review_notes: reviewNotesInput || undefined
        })
      });

      setSaveMessage('Teacher mark and verification notes approved successfully.');
      // Refresh current submission details
      await loadSubmissionDetails(activeSubId);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to save mark approval');
    } finally {
      setIsSavingMark(false);
    }
  };

  const handleBatchApprove = async () => {
    try {
      await apiRequest(`/reviews/submissions/${activeSubId}/batch-approve`, { method: 'POST' });
      setIsBatchApproveModalOpen(false);
      await loadSubmissionDetails(activeSubId);
      alert('All suggested marks approved for this answer sheet.');
    } catch (err: any) {
      alert(`Batch approval failed: ${err.message}`);
    }
  };

  const handleFinalizeSubmission = async () => {
    try {
      await apiRequest(`/reviews/submissions/${activeSubId}/finalize`, { method: 'POST' });
      setIsFinalizeModalOpen(false);
      await loadSubmissionDetails(activeSubId);
      alert('Submission successfully locked and finalized! Final grade reports are now generated.');
    } catch (err: any) {
      alert(`Finalization failed: ${err.message}`);
    }
  };

  if (loading && !submission) {
    return (
      <>
        <Navbar title="Loading Review Workspace..." />
        <div className="p-12 text-center text-xs text-slate-400">Loading student submission details...</div>
      </>
    );
  }

  return (
    <>
      <Navbar
        title="Teacher Evaluation & Review Workspace"
        subtitle="Verify AI-suggested marks, inspect side-by-side answers, adjust rubric credit, and approve final grades"
      />

      <main className="p-6 max-w-7xl mx-auto w-full space-y-6">
        {/* Top Control Bar */}
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          {/* Submission Selector */}
          <div className="flex items-center space-x-3">
            <span className="text-xs font-semibold text-slate-500">Student:</span>
            <select
              value={activeSubId}
              onChange={(e) => setActiveSubId(e.target.value)}
              className="text-xs font-bold text-slate-900 bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-600"
            >
              {submissionsList.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.student_name} ({s.student_id}) — {s.is_finalized ? 'Finalized' : 'Pending Review'}
                </option>
              ))}
            </select>
            <StatusBadge status={submission?.status || 'uploaded'} size="sm" />
          </div>

          {/* Quick Metrics */}
          <div className="flex items-center space-x-6 text-xs">
            <div>
              <span className="text-slate-400 block text-[10px]">AI Suggested Sum</span>
              <span className="font-bold text-slate-700">{submission?.total_suggested_marks || 0} Marks</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px]">Approved Total</span>
              <span className="font-bold text-indigo-700 text-sm">{submission?.total_approved_marks || 0} / {exam?.total_marks}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px]">Percentage</span>
              <span className="font-bold text-slate-900">{submission?.percentage || 0}%</span>
            </div>

            {/* Actions */}
            <div className="flex items-center space-x-2 pl-4 border-l border-slate-200">
              <button
                onClick={() => setIsBatchApproveModalOpen(true)}
                disabled={submission?.is_finalized}
                className="px-3 py-1.5 rounded-lg border border-indigo-200 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-xs font-semibold transition-colors disabled:opacity-40"
              >
                Approve All Suggested
              </button>
              <button
                onClick={() => setIsFinalizeModalOpen(true)}
                disabled={submission?.is_finalized}
                className="inline-flex items-center px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-xs transition-colors disabled:opacity-40"
              >
                <Lock className="w-3.5 h-3.5 mr-1" />
                {submission?.is_finalized ? 'Finalized' : 'Finalize Grades'}
              </button>
            </div>
          </div>
        </div>

        {/* Question Selector Tabs */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1">
          {evaluationResults.map((res, idx) => {
            const isApproved = res.teacher_marks !== null;
            const isLowConfidence = res.confidence_level === 'low';
            const isSelected = selectedQuestionIndex === idx;

            return (
              <button
                key={res.id}
                onClick={() => handleSelectQuestion(idx)}
                className={`flex items-center px-4 py-2.5 rounded-xl border text-xs font-medium transition-all shrink-0 ${
                  isSelected
                    ? 'border-indigo-600 bg-indigo-600 text-white shadow-sm'
                    : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300'
                }`}
              >
                <span className="font-bold mr-2">Q{res.question_number}</span>
                <span className="opacity-80 mr-2">({res.max_marks}M)</span>
                {isApproved ? (
                  <CheckCircle2 className={`w-3.5 h-3.5 ${isSelected ? 'text-white' : 'text-emerald-500'}`} />
                ) : isLowConfidence ? (
                  <AlertTriangle className={`w-3.5 h-3.5 ${isSelected ? 'text-amber-200' : 'text-rose-500'}`} />
                ) : null}
              </button>
            );
          })}
        </div>

        {/* Main Side-by-Side Review Grid */}
        {currentResult && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Left Column: Side-by-Side Student vs Model Answer (7 cols) */}
            <div className="lg:col-span-7 space-y-4">
              {/* Question Banner */}
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <span className="text-[11px] font-bold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">
                      Question {currentResult.question_number} • Max Marks: {currentResult.max_marks}
                    </span>
                    <h3 className="text-sm font-bold text-slate-900 mt-2">{currentResult.question_text}</h3>
                  </div>
                  <div className="text-right shrink-0">
                    <span className="text-[10px] text-slate-400 block">AI Suggestion</span>
                    <span className="text-base font-extrabold text-indigo-700">
                      {currentResult.suggested_marks} <span className="text-xs text-slate-400">/ {currentResult.max_marks}</span>
                    </span>
                  </div>
                </div>
              </div>

              {/* Answers Side-by-Side */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Student Answer */}
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-800">Student Answer</span>
                    <span className="text-[10px] text-slate-400">Extracted Text</span>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 text-xs text-slate-700 leading-relaxed min-h-[160px] whitespace-pre-wrap">
                    {currentResult.student_answer || <span className="text-slate-400 italic">No answer detected.</span>}
                  </div>
                </div>

                {/* Model Answer */}
                <div className="bg-white p-4 rounded-xl border border-indigo-100 shadow-xs space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-indigo-900">Model Answer</span>
                    <span className="text-[10px] text-indigo-500 font-medium">Instructor Reference</span>
                  </div>
                  <div className="p-3 bg-indigo-50/40 rounded-lg border border-indigo-100/60 text-xs text-slate-700 leading-relaxed min-h-[160px] whitespace-pre-wrap">
                    {currentResult.model_answer}
                  </div>
                </div>
              </div>

              {/* Rubrics Breakdown Card */}
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-3">
                <h4 className="text-xs font-bold text-slate-900 flex items-center">
                  <FileCheck className="w-4 h-4 mr-1.5 text-indigo-600" />
                  Marking Rubric Criteria Breakdown
                </h4>
                <div className="space-y-2">
                  {(currentResult.rubric_breakdown || []).map((rb: any, idx: number) => (
                    <div
                      key={idx}
                      className="p-3 rounded-lg border border-slate-100 bg-slate-50/70 flex items-center justify-between text-xs"
                    >
                      <div className="pr-4">
                        <div className="font-semibold text-slate-800 flex items-center gap-1.5">
                          {rb.met ? (
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                          ) : (
                            <AlertTriangle className="w-3.5 h-3.5 text-amber-500 shrink-0" />
                          )}
                          <span>{rb.criterion_title}</span>
                        </div>
                        <p className="text-[11px] text-slate-500 mt-0.5">{rb.explanation}</p>
                      </div>
                      <div className="text-right shrink-0">
                        <span className="font-bold text-indigo-700">{rb.awarded_marks}</span>
                        <span className="text-slate-400 text-[10px]"> / {rb.allocated_marks}M</span>
                      </div>
                    </div>
                  ))}
                  {(!currentResult.rubric_breakdown || currentResult.rubric_breakdown.length === 0) && (
                    <p className="text-xs text-slate-400 italic">No specific rubrics configured for this question.</p>
                  )}
                </div>
              </div>

              {/* Matched vs Missing Concepts */}
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div>
                  <span className="text-[11px] font-bold text-emerald-700 uppercase tracking-wider block mb-2">
                    Matched Keywords & Terms ({currentResult.matched_keywords?.length || 0})
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {(currentResult.matched_keywords || []).map((kw: string, i: number) => (
                      <span key={i} className="px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200 text-[11px]">
                        ✓ {kw}
                      </span>
                    ))}
                    {(!currentResult.matched_keywords || currentResult.matched_keywords.length === 0) && (
                      <span className="text-slate-400 italic text-[11px]">No keyword matches found.</span>
                    )}
                  </div>
                </div>

                <div>
                  <span className="text-[11px] font-bold text-rose-700 uppercase tracking-wider block mb-2">
                    Missing Expected Terms ({currentResult.missing_keywords?.length || 0})
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {(currentResult.missing_keywords || []).map((kw: string, i: number) => (
                      <span key={i} className="px-2 py-0.5 rounded-md bg-rose-50 text-rose-800 border border-rose-200 text-[11px]">
                        ✗ {kw}
                      </span>
                    ))}
                    {(!currentResult.missing_keywords || currentResult.missing_keywords.length === 0) && (
                      <span className="text-slate-400 italic text-[11px]">All required keywords present.</span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column: AI Signals, Warnings & Teacher Decision Box (5 cols) */}
            <div className="lg:col-span-5 space-y-4">
              {/* AI Explainability & Signal Gauges */}
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-4">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <div className="flex items-center space-x-2">
                    <Sparkles className="w-4 h-4 text-indigo-600" />
                    <h4 className="text-xs font-bold text-slate-800">Automated Signal Breakdown</h4>
                  </div>
                  <StatusBadge status={currentResult.confidence_level} size="sm" />
                </div>

                {/* Signals Meters */}
                <div className="space-y-2.5 text-xs">
                  <div>
                    <div className="flex justify-between text-[11px] text-slate-600 mb-1">
                      <span>Keyword Coverage</span>
                      <span className="font-semibold">{Math.round(currentResult.keyword_coverage_score * 100)}%</span>
                    </div>
                    <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                      <div className="bg-indigo-600 h-full rounded-full" style={{ width: `${currentResult.keyword_coverage_score * 100}%` }} />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-[11px] text-slate-600 mb-1">
                      <span>Lexical Cosine Similarity (TF-IDF)</span>
                      <span className="font-semibold">{Math.round(currentResult.cosine_similarity_score * 100)}%</span>
                    </div>
                    <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                      <div className="bg-sky-500 h-full rounded-full" style={{ width: `${currentResult.cosine_similarity_score * 100}%` }} />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-[11px] text-slate-600 mb-1">
                      <span>Dense Semantic Embedding Match</span>
                      <span className="font-semibold">{Math.round(currentResult.semantic_similarity_score * 100)}%</span>
                    </div>
                    <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                      <div className="bg-teal-500 h-full rounded-full" style={{ width: `${currentResult.semantic_similarity_score * 100}%` }} />
                    </div>
                  </div>
                </div>

                {/* Uncertainty Warnings */}
                {currentResult.uncertainty_reasons && currentResult.uncertainty_reasons.length > 0 && (
                  <div className="p-3 rounded-lg bg-amber-50/80 border border-amber-200 space-y-1.5 text-xs">
                    <span className="font-bold text-amber-800 flex items-center">
                      <AlertTriangle className="w-3.5 h-3.5 mr-1" />
                      Instructor Review Flags ({currentResult.uncertainty_reasons.length})
                    </span>
                    <ul className="list-disc pl-4 text-[11px] text-amber-700 space-y-0.5">
                      {currentResult.uncertainty_reasons.map((r: string, i: number) => (
                        <li key={i}>{r}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Teacher Decision & Mark Approval Form */}
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-4">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <div className="flex items-center space-x-2">
                    <ShieldCheck className="w-4 h-4 text-indigo-600" />
                    <h4 className="text-xs font-bold text-slate-900">Certified Teacher Evaluation</h4>
                  </div>
                  {currentResult.teacher_marks !== null && (
                    <span className="text-[10px] text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded font-semibold border border-emerald-200">
                      Approved by {currentResult.reviewer_name || 'Instructor'}
                    </span>
                  )}
                </div>

                {errorMessage && (
                  <div className="p-2.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs">
                    {errorMessage}
                  </div>
                )}

                {saveMessage && (
                  <div className="p-2.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs">
                    {saveMessage}
                  </div>
                )}

                <form onSubmit={handleSaveTeacherMark} className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Teacher Approved Marks (0 to {currentResult.max_marks})
                    </label>
                    <div className="relative">
                      <input
                        type="number"
                        step="0.5"
                        min="0"
                        max={currentResult.max_marks}
                        required
                        disabled={submission?.is_finalized}
                        value={teacherMarksInput}
                        onChange={(e) => setTeacherMarksInput(e.target.value)}
                        className="w-full text-base font-bold text-slate-900 p-2.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-600 bg-white"
                      />
                      <span className="absolute right-3 top-3 text-xs text-slate-400">
                        / {currentResult.max_marks} Max
                      </span>
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Instructor Feedback & Audit Notes
                    </label>
                    <textarea
                      rows={3}
                      disabled={submission?.is_finalized}
                      value={reviewNotesInput}
                      onChange={(e) => setReviewNotesInput(e.target.value)}
                      placeholder="Add justification for mark adjustments or constructive student feedback..."
                      className="w-full text-xs p-2.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-600 bg-white"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={isSavingMark || submission?.is_finalized}
                    className="w-full py-2.5 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs transition-colors flex items-center justify-center disabled:opacity-50"
                  >
                    <Save className="w-3.5 h-3.5 mr-1.5" />
                    {isSavingMark ? 'Recording Approval...' : 'Approve Question Grade'}
                  </button>
                </form>
              </div>
            </div>
          </div>
        )}

        {/* Batch Approve Modal */}
        <Modal
          isOpen={isBatchApproveModalOpen}
          onClose={() => setIsBatchApproveModalOpen(false)}
          title="Approve All Suggested Marks"
          maxWidth="sm"
        >
          <div className="space-y-3">
            <p className="text-xs text-slate-600">
              This action will approve the AI suggested marks for all unreviewed questions in this submission.
              You can still modify individual questions after approving.
            </p>
            <div className="flex justify-end space-x-2 pt-3 border-t border-slate-100">
              <button
                onClick={() => setIsBatchApproveModalOpen(false)}
                className="px-3.5 py-1.5 text-xs font-semibold rounded-lg border border-slate-300 text-slate-700"
              >
                Cancel
              </button>
              <button
                onClick={handleBatchApprove}
                className="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-indigo-600 text-white hover:bg-indigo-700"
              >
                Confirm Batch Approval
              </button>
            </div>
          </div>
        </Modal>

        {/* Finalize Submission Modal */}
        <Modal
          isOpen={isFinalizeModalOpen}
          onClose={() => setIsFinalizeModalOpen(false)}
          title="Finalize & Lock Submission Marks"
          maxWidth="sm"
        >
          <div className="space-y-3">
            <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-xs">
              <strong>Mandatory Human Oversight Confirmation:</strong> Finalizing will permanently lock these grades and certify that they have been verified by the course instructor.
            </div>
            <p className="text-xs text-slate-600">
              Student: <strong className="text-slate-900">{submission?.student_name}</strong> ({submission?.student_id})<br />
              Total Approved Score: <strong className="text-indigo-700">{submission?.total_approved_marks} / {exam?.total_marks} ({submission?.percentage}%)</strong>
            </p>
            <div className="flex justify-end space-x-2 pt-3 border-t border-slate-100">
              <button
                onClick={() => setIsFinalizeModalOpen(false)}
                className="px-3.5 py-1.5 text-xs font-semibold rounded-lg border border-slate-300 text-slate-700"
              >
                Cancel
              </button>
              <button
                onClick={handleFinalizeSubmission}
                className="px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-emerald-600 text-white hover:bg-emerald-700"
              >
                Certify & Finalize Marks
              </button>
            </div>
          </div>
        </Modal>
      </main>
    </>
  );
};
