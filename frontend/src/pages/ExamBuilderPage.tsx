import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Plus,
  Trash2,
  Edit,
  Save,
  CheckCircle,
  AlertCircle,
  BookOpen,
  Sparkles,
  HelpCircle,
  Layers,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { Navbar } from '../components/Navbar';
import { StatusBadge } from '../components/StatusBadge';
import { Modal } from '../components/Modal';
import { apiRequest } from '../api/client';

export const ExamBuilderPage: React.FC = () => {
  const { examId } = useParams<{ examId: string }>();
  const navigate = useNavigate();

  const [exam, setExam] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Question Modal State
  const [isQuestionModalOpen, setIsQuestionModalOpen] = useState(false);
  const [editingQuestionId, setEditingQuestionId] = useState<number | null>(null);

  // Form State
  const [qNumber, setQNumber] = useState('');
  const [qText, setQText] = useState('');
  const [qMaxMarks, setQMaxMarks] = useState('');
  const [modelAnswer, setModelAnswer] = useState('');
  const [keywordsInput, setKeywordsInput] = useState('');
  const [conceptsInput, setConceptsInput] = useState('');
  const [rubrics, setRubrics] = useState<{ criterion_title: string; allocated_marks: string; description: string }[]>([]);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    fetchExamDetails();
  }, [examId]);

  const fetchExamDetails = async () => {
    try {
      setLoading(true);
      const data = await apiRequest(`/examinations/${examId}`);
      setExam(data);
    } catch (err) {
      console.error('Failed to load exam details:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenAddQuestion = () => {
    setEditingQuestionId(null);
    setQNumber(`${(exam?.questions?.length || 0) + 1}`);
    setQText('');
    setQMaxMarks('10');
    setModelAnswer('');
    setKeywordsInput('');
    setConceptsInput('');
    setRubrics([
      { criterion_title: 'Core Concept Definition', allocated_marks: '4', description: 'Accurate technical formulation' },
      { criterion_title: 'Mechanism / Working Principles', allocated_marks: '6', description: 'Key components & execution steps' }
    ]);
    setFormError(null);
    setIsQuestionModalOpen(true);
  };

  const handleOpenEditQuestion = (q: any) => {
    setEditingQuestionId(q.id);
    setQNumber(q.question_number);
    setQText(q.question_text);
    setQMaxMarks(q.max_marks.toString());
    setModelAnswer(q.model_answer);
    setKeywordsInput((q.required_keywords || []).join(', '));
    setConceptsInput((q.important_concepts || []).join(', '));
    setRubrics(
      (q.rubrics || []).map((r: any) => ({
        criterion_title: r.criterion_title,
        allocated_marks: r.allocated_marks.toString(),
        description: r.description || ''
      }))
    );
    setFormError(null);
    setIsQuestionModalOpen(true);
  };

  const handleAddRubricRow = () => {
    setRubrics([...rubrics, { criterion_title: '', allocated_marks: '2', description: '' }]);
  };

  const handleRemoveRubricRow = (idx: number) => {
    setRubrics(rubrics.filter((_, i) => i !== idx));
  };

  const handleRubricChange = (index: number, field: string, value: string) => {
    const updated = [...rubrics];
    (updated[index] as any)[field] = value;
    setRubrics(updated);
  };

  const handleSaveQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    const maxM = parseFloat(qMaxMarks);
    if (isNaN(maxM) || maxM <= 0) {
      setFormError('Please enter a valid maximum mark greater than 0.');
      return;
    }

    // Validate rubrics sum
    const rubricSum = rubrics.reduce((acc, r) => acc + (parseFloat(r.allocated_marks) || 0), 0);
    if (rubrics.length > 0 && rubricSum > maxM) {
      setFormError(`Total allocated rubric marks (${rubricSum}) exceeds question max marks (${maxM}).`);
      return;
    }

    // Check exam total
    const otherSum = (exam?.questions || [])
      .filter((q: any) => q.id !== editingQuestionId)
      .reduce((acc: number, q: any) => acc + q.max_marks, 0);

    if (otherSum + maxM > exam.total_marks) {
      setFormError(`Total question marks (${otherSum + maxM}) would exceed the examination total (${exam.total_marks}).`);
      return;
    }

    const keywords = keywordsInput
      .split(',')
      .map((k) => k.trim())
      .filter((k) => k.length > 0);

    const concepts = conceptsInput
      .split(',')
      .map((c) => c.trim())
      .filter((c) => c.length > 0);

    const formattedRubrics = rubrics
      .filter((r) => r.criterion_title.trim().length > 0)
      .map((r, i) => ({
        criterion_title: r.criterion_title.trim(),
        allocated_marks: parseFloat(r.allocated_marks) || 1.0,
        description: r.description.trim() || undefined,
        order_index: i + 1
      }));

    try {
      if (editingQuestionId) {
        await apiRequest(`/questions/${editingQuestionId}`, {
          method: 'PUT',
          body: JSON.stringify({
            question_number: qNumber,
            question_text: qText,
            max_marks: maxM,
            model_answer: modelAnswer,
            required_keywords: keywords,
            important_concepts: concepts,
            rubrics: formattedRubrics
          })
        });
      } else {
        await apiRequest(`/examinations/${examId}/questions`, {
          method: 'POST',
          body: JSON.stringify({
            question_number: qNumber,
            question_text: qText,
            max_marks: maxM,
            model_answer: modelAnswer,
            required_keywords: keywords,
            important_concepts: concepts,
            rubrics: formattedRubrics
          })
        });
      }

      setIsQuestionModalOpen(false);
      fetchExamDetails();
    } catch (err: any) {
      setFormError(err.message || 'Failed to save question');
    }
  };

  const handleDeleteQuestion = async (qId: number) => {
    if (!window.confirm('Are you sure you want to delete this question?')) return;
    try {
      await apiRequest(`/questions/${qId}`, { method: 'DELETE' });
      fetchExamDetails();
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  if (loading || !exam) {
    return (
      <>
        <Navbar title="Loading Scheme..." />
        <div className="p-8 text-center text-xs text-slate-400">Loading examination builder...</div>
      </>
    );
  }

  const currentAllocated = (exam.questions || []).reduce((acc: number, q: any) => acc + q.max_marks, 0);
  const remainingMarks = exam.total_marks - currentAllocated;

  return (
    <>
      <Navbar title={exam.title} subtitle={`${exam.subject} • ${exam.class_name} • Academic Year ${exam.academic_year}`} />

      <main className="p-8 max-w-7xl mx-auto w-full space-y-6">
        {/* Top Navigation & Status Banner */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <button
            onClick={() => navigate('/examinations')}
            className="inline-flex items-center text-xs font-semibold text-slate-600 hover:text-slate-900 transition-colors"
          >
            <ArrowLeft className="w-4 h-4 mr-1.5" />
            Back to Examinations
          </button>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => navigate(`/upload?examId=${exam.id}`)}
              className="inline-flex items-center px-3.5 py-2 text-xs font-semibold rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 shadow-xs"
            >
              Upload Answer Sheets
            </button>
            <button
              onClick={handleOpenAddQuestion}
              className="inline-flex items-center px-3.5 py-2 text-xs font-semibold rounded-lg bg-slate-900 text-white hover:bg-slate-800 shadow-xs"
            >
              <Plus className="w-4 h-4 mr-1.5" />
              Add Question
            </button>
          </div>
        </div>

        {/* Mark Allocation Meter */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-sm font-bold text-slate-900">Marking Scheme Balance</h3>
              <StatusBadge status={exam.status} size="sm" />
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              {currentAllocated === exam.total_marks
                ? 'All exam marks are fully allocated to questions. Ready for evaluation.'
                : `Allocated ${currentAllocated} of ${exam.total_marks} marks (${remainingMarks} remaining).`}
            </p>
          </div>

          <div className="flex items-center space-x-4">
            <div className="text-right">
              <span className="text-xs text-slate-400">Allocated</span>
              <p className="text-base font-bold text-slate-900">
                {currentAllocated} <span className="text-xs font-normal text-slate-400">/ {exam.total_marks}</span>
              </p>
            </div>
            <div className="w-32 bg-slate-100 h-3 rounded-full overflow-hidden border border-slate-200">
              <div
                className={`h-full rounded-full transition-all duration-300 ${
                  currentAllocated === exam.total_marks ? 'bg-emerald-500' : 'bg-indigo-600'
                }`}
                style={{ width: `${Math.min(100, (currentAllocated / exam.total_marks) * 100)}%` }}
              />
            </div>
          </div>
        </div>

        {/* Questions List */}
        <div className="space-y-4">
          {(exam.questions || []).map((q: any) => (
            <div
              key={q.id}
              className="bg-white rounded-xl border border-slate-200 shadow-xs hover:border-slate-300 transition-colors p-6 space-y-4"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start space-x-3">
                  <span className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-700 font-bold text-sm flex items-center justify-center shrink-0">
                    Q{q.question_number}
                  </span>
                  <div>
                    <h4 className="text-sm font-bold text-slate-900">{q.question_text}</h4>
                    <span className="inline-block mt-1 text-xs font-semibold text-indigo-600 bg-indigo-50/70 px-2 py-0.5 rounded">
                      Maximum Marks: {q.max_marks}
                    </span>
                  </div>
                </div>

                <div className="flex items-center space-x-1 shrink-0">
                  <button
                    onClick={() => handleOpenEditQuestion(q)}
                    className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-slate-50 rounded-lg transition-colors"
                    title="Edit question"
                  >
                    <Edit className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDeleteQuestion(q.id)}
                    className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-slate-50 rounded-lg transition-colors"
                    title="Delete question"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Model Answer Preview */}
              <div className="p-3.5 rounded-lg bg-slate-50/80 border border-slate-100 text-xs">
                <span className="font-semibold text-slate-700 block mb-1">Model Answer:</span>
                <p className="text-slate-600 leading-relaxed whitespace-pre-wrap">{q.model_answer}</p>
              </div>

              {/* Keywords & Concepts */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                <div>
                  <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                    Required Keywords ({q.required_keywords?.length || 0})
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {(q.required_keywords || []).map((kw: string, i: number) => (
                      <span key={i} className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-[11px]">
                        {kw}
                      </span>
                    ))}
                    {(!q.required_keywords || q.required_keywords.length === 0) && (
                      <span className="text-slate-400 italic text-[11px]">No keywords defined</span>
                    )}
                  </div>
                </div>

                <div>
                  <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                    Important Concepts ({q.important_concepts?.length || 0})
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {(q.important_concepts || []).map((cp: string, i: number) => (
                      <span key={i} className="px-2 py-0.5 rounded bg-violet-50 text-violet-700 text-[11px] border border-violet-100">
                        {cp}
                      </span>
                    ))}
                    {(!q.important_concepts || q.important_concepts.length === 0) && (
                      <span className="text-slate-400 italic text-[11px]">No concepts defined</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Rubric Criteria Table */}
              {q.rubrics && q.rubrics.length > 0 && (
                <div className="pt-3 border-t border-slate-100">
                  <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-2">
                    Marking Rubrics ({q.rubrics.length} Criteria)
                  </span>
                  <div className="border border-slate-200 rounded-lg overflow-hidden text-xs">
                    <table className="min-w-full divide-y divide-slate-200">
                      <thead className="bg-slate-50 text-slate-600 font-semibold">
                        <tr>
                          <th className="px-3 py-2 text-left">Criterion</th>
                          <th className="px-3 py-2 text-left">Description</th>
                          <th className="px-3 py-2 text-right">Marks</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 bg-white">
                        {q.rubrics.map((r: any) => (
                          <tr key={r.id}>
                            <td className="px-3 py-2 font-medium text-slate-800">{r.criterion_title}</td>
                            <td className="px-3 py-2 text-slate-500">{r.description || '-'}</td>
                            <td className="px-3 py-2 text-right font-bold text-indigo-700">{r.allocated_marks}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          ))}

          {(!exam.questions || exam.questions.length === 0) && (
            <div className="p-12 text-center bg-white rounded-xl border border-dashed border-slate-300">
              <Layers className="w-10 h-10 text-slate-300 mx-auto mb-3" />
              <h3 className="text-sm font-bold text-slate-700">No questions added yet</h3>
              <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
                Add questions with model answers, expected keywords, and rubrics to build the automated evaluation scheme.
              </p>
              <button
                onClick={handleOpenAddQuestion}
                className="mt-4 inline-flex items-center px-4 py-2 text-xs font-semibold rounded-lg bg-indigo-600 text-white hover:bg-indigo-700"
              >
                <Plus className="w-4 h-4 mr-1.5" />
                Add First Question
              </button>
            </div>
          )}
        </div>

        {/* Add/Edit Question Modal */}
        <Modal
          isOpen={isQuestionModalOpen}
          onClose={() => setIsQuestionModalOpen(false)}
          title={editingQuestionId ? `Edit Question ${qNumber}` : 'Add New Question'}
          maxWidth="2xl"
        >
          {formError && (
            <div className="mb-4 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{formError}</span>
            </div>
          )}

          <form onSubmit={handleSaveQuestion} className="space-y-4">
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Question Number</label>
                <input
                  type="text"
                  required
                  value={qNumber}
                  onChange={(e) => setQNumber(e.target.value)}
                  placeholder="e.g. 1 or 2(a)"
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-600"
                />
              </div>
              <div className="col-span-2">
                <label className="block text-xs font-semibold text-slate-700 mb-1">Maximum Marks</label>
                <input
                  type="number"
                  step="0.5"
                  required
                  min="0.5"
                  value={qMaxMarks}
                  onChange={(e) => setQMaxMarks(e.target.value)}
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-600"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Question Prompt / Statement</label>
              <textarea
                rows={2}
                required
                value={qText}
                onChange={(e) => setQText(e.target.value)}
                placeholder="State the examination question clearly..."
                className="w-full text-xs p-2.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-600"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Model / Benchmark Answer (Used for Semantic & Lexical Matching)
              </label>
              <textarea
                rows={4}
                required
                value={modelAnswer}
                onChange={(e) => setModelAnswer(e.target.value)}
                placeholder="Provide a comprehensive and accurate reference answer..."
                className="w-full text-xs p-2.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-600"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Required Keywords (Comma-separated)
                </label>
                <input
                  type="text"
                  value={keywordsInput}
                  onChange={(e) => setKeywordsInput(e.target.value)}
                  placeholder="virtual memory, paging, frames, disk"
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-600"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Important Concepts (Comma-separated)
                </label>
                <input
                  type="text"
                  value={conceptsInput}
                  onChange={(e) => setConceptsInput(e.target.value)}
                  placeholder="address translation, page replacement"
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-600"
                />
              </div>
            </div>

            {/* Rubrics Builder */}
            <div className="pt-2 border-t border-slate-100">
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs font-semibold text-slate-700">Marking Rubrics Criteria</label>
                <button
                  type="button"
                  onClick={handleAddRubricRow}
                  className="text-xs text-indigo-600 hover:text-indigo-700 font-medium flex items-center"
                >
                  <Plus className="w-3.5 h-3.5 mr-1" /> Add Criterion
                </button>
              </div>

              <div className="space-y-2 max-h-48 overflow-y-auto">
                {rubrics.map((r, idx) => (
                  <div key={idx} className="flex items-center gap-2 bg-slate-50 p-2 rounded-lg border border-slate-200">
                    <input
                      type="text"
                      placeholder="Criterion title"
                      value={r.criterion_title}
                      onChange={(e) => handleRubricChange(idx, 'criterion_title', e.target.value)}
                      className="flex-1 text-xs p-1.5 rounded border border-slate-300 bg-white"
                    />
                    <input
                      type="number"
                      step="0.5"
                      placeholder="Marks"
                      value={r.allocated_marks}
                      onChange={(e) => handleRubricChange(idx, 'allocated_marks', e.target.value)}
                      className="w-20 text-xs p-1.5 rounded border border-slate-300 bg-white text-right"
                    />
                    <button
                      type="button"
                      onClick={() => handleRemoveRubricRow(idx)}
                      className="text-slate-400 hover:text-rose-600 p-1"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-end space-x-2 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setIsQuestionModalOpen(false)}
                className="px-4 py-2 text-xs font-semibold rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-xs font-semibold rounded-lg bg-indigo-600 text-white hover:bg-indigo-700"
              >
                Save Question Scheme
              </button>
            </div>
          </form>
        </Modal>
      </main>
    </>
  );
};
