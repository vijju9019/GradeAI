import React, { useState, useEffect } from 'react';
import {
  Settings,
  Cpu,
  Sliders,
  Users,
  ShieldCheck,
  CheckCircle,
  AlertTriangle,
  Folder,
  Save,
  HelpCircle,
  Layers,
  Database
} from 'lucide-react';
import { Navbar } from '../components/Navbar';
import { useAuth } from '../context/AuthContext';
import { apiRequest } from '../api/client';

export const SettingsPage: React.FC = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const [health, setHealth] = useState<any>(null);
  const [weights, setWeights] = useState<any>({
    keyword_weight: 0.30,
    cosine_weight: 0.25,
    semantic_weight: 0.30,
    rubric_weight: 0.15
  });
  const [usersList, setUsersList] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);
  const [trainingMessage, setTrainingMessage] = useState<string | null>(null);
  const [isTraining, setIsTraining] = useState(false);

  useEffect(() => {
    loadSettingsData();
  }, []);

  const loadSettingsData = async () => {
    try {
      setLoading(true);
      const [healthData, weightsData] = await Promise.all([
        apiRequest('/admin/health'),
        apiRequest('/admin/scoring-weights')
      ]);

      setHealth(healthData);
      setWeights(weightsData);

      if (isAdmin) {
        const usersData = await apiRequest('/admin/users');
        setUsersList(usersData);
      }
    } catch (err) {
      console.error('Failed to load settings:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateWeights = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaveSuccess(null);
    try {
      await apiRequest('/admin/scoring-weights', {
        method: 'PUT',
        body: JSON.stringify({
          keyword_weight: parseFloat(weights.keyword_weight),
          cosine_weight: parseFloat(weights.cosine_weight),
          semantic_weight: parseFloat(weights.semantic_weight),
          rubric_weight: parseFloat(weights.rubric_weight)
        })
      });
      setSaveSuccess('Scoring pipeline weights updated and re-normalized successfully.');
    } catch (err: any) {
      alert(`Failed to update weights: ${err.message}`);
    }
  };

  const handleTrainModel = async () => {
    setIsTraining(true);
    setTrainingMessage(null);
    try {
      const res = await apiRequest('/evaluation/train', {
        method: 'POST',
        body: JSON.stringify({ min_samples: 5 })
      });
      if (res.success) {
        setTrainingMessage(`Model trained successfully! Samples: ${res.sample_count}, MAE: ${res.metrics.mae}, RMSE: ${res.metrics.rmse}, R²: ${res.metrics.r2_score}`);
        loadSettingsData();
      } else {
        setTrainingMessage(`Training aborted: ${res.error}`);
      }
    } catch (err: any) {
      setTrainingMessage(`Error during training: ${err.message}`);
    } finally {
      setIsTraining(false);
    }
  };

  return (
    <>
      <Navbar title="System Settings & Infrastructure" subtitle="Model diagnostics, scoring strategy weights, role access, and local pipeline configuration" />

      <main className="p-8 max-w-6xl mx-auto w-full space-y-8">
        {/* System Health & AI Model Status */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-5">
          <div className="border-b border-slate-100 pb-3">
            <h3 className="text-sm font-bold text-slate-900 flex items-center">
              <Cpu className="w-4 h-4 mr-2 text-indigo-600" />
              AI/ML Pipeline & Model Availability Diagnostics
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Honest environmental readiness indicators for local OCR and transformer embedding models.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            {/* SentenceTransformer Status */}
            <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-2">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                Embedding Model (Local)
              </span>
              <div className="flex items-center space-x-2">
                {health?.embedding_model_ready ? (
                  <CheckCircle className="w-4 h-4 text-emerald-600" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-amber-500" />
                )}
                <span className="font-bold text-slate-900">
                  {health?.embedding_model_ready ? 'Loaded & Active' : 'Fallback N-Gram Mode'}
                </span>
              </div>
              <p className="text-[11px] text-slate-500">
                Model: <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200">{health?.embedding_model_name}</code>
              </p>
            </div>

            {/* Tesseract OCR Status */}
            <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-2">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                Tesseract Printed OCR
              </span>
              <div className="flex items-center space-x-2">
                {health?.tesseract_ocr_available ? (
                  <CheckCircle className="w-4 h-4 text-emerald-600" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-amber-500" />
                )}
                <span className="font-bold text-slate-900">
                  {health?.tesseract_ocr_available ? 'Detected in PATH' : 'Not Detected in PATH'}
                </span>
              </div>
              <p className="text-[11px] text-slate-500">
                Digital PDF text extraction & manual correction remain fully operational.
              </p>
            </div>

            {/* Trainable Regressor Status */}
            <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-2">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                Supervised Model Calibrator
              </span>
              <div className="flex items-center space-x-2">
                {health?.trainable_scorer_trained ? (
                  <CheckCircle className="w-4 h-4 text-emerald-600" />
                ) : (
                  <HelpCircle className="w-4 h-4 text-slate-400" />
                )}
                <span className="font-bold text-slate-900">
                  {health?.trainable_scorer_trained ? 'Trained Artifact Active' : 'Untrained (Default Rule-Engine)'}
                </span>
              </div>
              <button
                type="button"
                onClick={handleTrainModel}
                disabled={isTraining}
                className="mt-1 px-2.5 py-1 text-[11px] font-semibold rounded bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 transition-colors"
              >
                {isTraining ? 'Training Model...' : 'Train on Approved Marks'}
              </button>
            </div>
          </div>

          {trainingMessage && (
            <div className="p-3 rounded-lg bg-indigo-50 border border-indigo-200 text-indigo-900 text-xs">
              {trainingMessage}
            </div>
          )}

          <div className="p-3 rounded-lg bg-slate-100/60 border border-slate-200 text-xs text-slate-600 flex items-start space-x-2">
            <Folder className="w-4 h-4 shrink-0 text-slate-500 mt-0.5" />
            <div>
              <span className="font-semibold text-slate-800">Private Local Storage Directory: </span>
              <span className="font-mono text-[11px] break-all">{health?.upload_dir}</span>
            </div>
          </div>
        </div>

        {/* Scoring Pipeline Weight Adjustments */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-4">
          <div className="border-b border-slate-100 pb-3">
            <h3 className="text-sm font-bold text-slate-900 flex items-center">
              <Sliders className="w-4 h-4 mr-2 text-indigo-600" />
              Configurable Scoring Weights Strategy
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Adjust the relative importance of lexical matching, semantic embeddings, keyword coverage, and rubric points.
            </p>
          </div>

          {saveSuccess && (
            <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs flex items-center space-x-2">
              <CheckCircle className="w-4 h-4 shrink-0" />
              <span>{saveSuccess}</span>
            </div>
          )}

          <form onSubmit={handleUpdateWeights} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Required Keyword Weight
                </label>
                <input
                  type="number"
                  step="0.05"
                  min="0"
                  max="1"
                  value={weights.keyword_weight}
                  onChange={(e) => setWeights({ ...weights, keyword_weight: e.target.value })}
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-600"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  TF-IDF Cosine Similarity
                </label>
                <input
                  type="number"
                  step="0.05"
                  min="0"
                  max="1"
                  value={weights.cosine_weight}
                  onChange={(e) => setWeights({ ...weights, cosine_weight: e.target.value })}
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-600"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Semantic Embedding Match
                </label>
                <input
                  type="number"
                  step="0.05"
                  min="0"
                  max="1"
                  value={weights.semantic_weight}
                  onChange={(e) => setWeights({ ...weights, semantic_weight: e.target.value })}
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-600"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Marking Rubrics Weight
                </label>
                <input
                  type="number"
                  step="0.05"
                  min="0"
                  max="1"
                  value={weights.rubric_weight}
                  onChange={(e) => setWeights({ ...weights, rubric_weight: e.target.value })}
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-600"
                />
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="submit"
                className="inline-flex items-center px-4 py-2 rounded-lg bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-700 shadow-xs"
              >
                <Save className="w-3.5 h-3.5 mr-1.5" />
                Update Scoring Weights
              </button>
            </div>
          </form>
        </div>

        {/* User Management (Admin Only) */}
        {isAdmin && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
            <div className="p-5 border-b border-slate-100 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-900 flex items-center">
                  <Users className="w-4 h-4 mr-2 text-indigo-600" />
                  Authorized Institutional Users
                </h3>
                <p className="text-xs text-slate-500">Instructor and administrator accounts</p>
              </div>
            </div>

            <table className="min-w-full divide-y divide-slate-200 text-xs">
              <thead className="bg-slate-50 text-slate-600 font-semibold">
                <tr>
                  <th className="px-4 py-3 text-left">Full Name</th>
                  <th className="px-4 py-3 text-left">Email Address</th>
                  <th className="px-4 py-3 text-center">Role</th>
                  <th className="px-4 py-3 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {usersList.map((u) => (
                  <tr key={u.id}>
                    <td className="px-4 py-3 font-semibold text-slate-900">{u.full_name}</td>
                    <td className="px-4 py-3 text-slate-600">{u.email}</td>
                    <td className="px-4 py-3 text-center">
                      <span className="capitalize px-2 py-0.5 rounded bg-slate-100 font-semibold text-slate-700">
                        {u.role}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 font-semibold">
                        Active
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Transparent Limitations & Human Oversight Statement */}
        <div className="p-5 rounded-xl bg-slate-900 text-white shadow-xs space-y-3">
          <div className="flex items-center space-x-2 text-indigo-400 font-bold text-sm">
            <ShieldCheck className="w-5 h-5" />
            <span>Academic Limitations & Ethical AI Guidelines</span>
          </div>
          <div className="text-xs text-slate-300 space-y-2 leading-relaxed">
            <p>
              <strong>1. Human Accountability:</strong> Automated suggested marks are probabilistic assistive recommendations.
              Final grading authority and legal responsibility remain strictly with the certified academic instructor.
            </p>
            <p>
              <strong>2. Handwriting OCR Limitations:</strong> Standard optical character recognition (OCR) models reliably process printed text.
              Cursive or irregular handwriting requires teacher verification or manual text entry. GradeAI never falsely claims unverified handwriting accuracy.
            </p>
            <p>
              <strong>3. Local-First Privacy:</strong> Student examination answers are processed entirely on-premises without mandatory calls to commercial third-party cloud LLM APIs.
            </p>
          </div>
        </div>
      </main>
    </>
  );
};
