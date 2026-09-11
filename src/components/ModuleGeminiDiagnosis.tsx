import React, { useState } from "react";
import {
  Sparkles,
  Bot,
  Copy,
  Download,
  AlertCircle,
  CheckCircle2,
  RefreshCw,
  Send,
  Building2,
  ShieldCheck,
  TrendingDown,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import { BaseRecord, BoardFixedExpense, BankLiability } from "../types.ts";
import {
  calculateFinancialDrains,
  calculateAbcCurve,
  calculateTrashAccounts,
  calculateMissingRegistration,
  auditNatureInconsistencies,
  runPredictiveProvisioning,
} from "../utils/financialCalculations.ts";

interface ModuleGeminiDiagnosisProps {
  filteredRecords: BaseRecord[];
  allRecords: BaseRecord[];
  boardExpenses: BoardFixedExpense[];
  bancosData: BankLiability[];
  availableMonths: string[];
}

export const ModuleGeminiDiagnosis: React.FC<ModuleGeminiDiagnosisProps> = ({
  filteredRecords,
  allRecords,
  boardExpenses,
  bancosData,
  availableMonths,
}) => {
  const [loading, setLoading] = useState(false);
  const [reportMarkdown, setReportMarkdown] = useState<string | null>(null);
  const [customPrompt, setCustomPrompt] = useState<string>("");
  const [copied, setCopied] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Compute metrics for the payload
  const totalVolume = filteredRecords.reduce((acc, r) => acc + r.valor, 0);
  const drenos = calculateFinancialDrains(filteredRecords);
  const abc = calculateAbcCurve(filteredRecords);
  const lixeira = calculateTrashAccounts(filteredRecords);
  const semCadastro = calculateMissingRegistration(filteredRecords);
  const audit = auditNatureInconsistencies(filteredRecords);
  const provisionamento = runPredictiveProvisioning(
    allRecords,
    availableMonths[availableMonths.length - 1] || "MAR/2026"
  );

  const handleGenerateDiagnosis = async () => {
    setLoading(true);
    setErrorMsg(null);

    const payload = {
      resumoGeral: {
        totalGasto: totalVolume,
        qtdLancamentos: filteredRecords.length,
        totalDrenosFinanceiros: drenos.total,
        qtdDrenos: drenos.qtd,
        topCredoresClasseA: abc.classeA.slice(0, 5).map((c) => ({
          razaoSocial: c.razaoSocial,
          valor: c.valorTotal,
          percentual: c.percentual.toFixed(1),
        })),
        contasLixeiraValor: lixeira.total,
        contasLixeiraQtd: lixeira.qtd,
        semCnpjValor: semCadastro.total,
        semCnpjQtd: semCadastro.qtd,
        divergenciasNaturezaQtd: audit.totalQtd,
        divergenciasNaturezaValor: audit.totalValor,
        riscoProvisaoAusenteValor: provisionamento.totalRiscoNaoProvisionado,
        passivosBancariosTotal: bancosData.reduce((acc, b) => acc + b.saldoDevedor, 0),
        parcelaMensalBancos: bancosData.reduce((acc, b) => acc + b.valorParcela, 0),
        despesasFixasBoardQtd: boardExpenses.length,
      },
      customPrompt: customPrompt.trim() || undefined,
    };

    try {
      const res = await fetch("/api/gemini/diagnostico", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || "Falha ao gerar diagnóstico com IA");
      }

      setReportMarkdown(data.diagnostico);
    } catch (err: any) {
      console.error(err);
      setErrorMsg(
        err.message ||
          "Não foi possível conectar ao modelo Gemini. Verifique a configuração da chave GEMINI_API_KEY."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (reportMarkdown) {
      navigator.clipboard.writeText(reportMarkdown);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownloadTxt = () => {
    if (!reportMarkdown) return;
    const blob = new Blob([reportMarkdown], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `parecer_controladoria_ia_${new Date().toISOString().slice(0, 10)}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 sm:p-5 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-purple-600" />
              Módulo 5: Diagnóstico Executivo de Controladoria & Governança com Gemini AI
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              Gera parecer pericial contábil de nível C-Level sintetizando riscos de caixa, reclassificações contábeis e plano de corte de gastos.
            </p>
          </div>

          <button
            id="btn-gerar-ia"
            onClick={handleGenerateDiagnosis}
            disabled={loading}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg text-xs font-bold bg-purple-600 hover:bg-purple-700 text-white shadow-xs transition-colors cursor-pointer disabled:opacity-60"
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Processando Parecer Contábil...
              </>
            ) : (
              <>
                <Bot className="w-4 h-4" />
                Gerar Diagnóstico Executivo com IA
              </>
            )}
          </button>
        </div>

        {/* Input for Custom Question/Prompt */}
        <div className="mt-4 pt-4 border-t border-slate-100">
          <label className="block text-xs font-semibold text-slate-700 mb-1.5">
            Personalizar Diretrizes do Diagnóstico (Opcional):
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              value={customPrompt}
              onChange={(e) => setCustomPrompt(e.target.value)}
              placeholder="Ex: Dar ênfase especial na mitigação tributária de contas sem CNPJ e alongamento de dívida bancária..."
              className="flex-1 px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-purple-500 focus:bg-white text-slate-900"
            />
            {customPrompt && (
              <button
                onClick={() => setCustomPrompt("")}
                className="px-2.5 py-1 text-xs text-slate-400 hover:text-slate-600"
              >
                Limpar
              </button>
            )}
          </div>
        </div>

        {/* Executive Pre-Diagnosis Metrics */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4">
          <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
            <span className="text-[10px] uppercase font-bold text-slate-400 block">Drenos Financeiros</span>
            <span className="text-sm font-bold text-rose-600">
              R$ {drenos.total.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
            </span>
          </div>
          <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
            <span className="text-[10px] uppercase font-bold text-slate-400 block">Contas "Lixeira"</span>
            <span className="text-sm font-bold text-amber-600">
              R$ {lixeira.total.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
            </span>
          </div>
          <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
            <span className="text-[10px] uppercase font-bold text-slate-400 block">Sem Razão / CNPJ</span>
            <span className="text-sm font-bold text-amber-700">
              R$ {semCadastro.total.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
            </span>
          </div>
          <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
            <span className="text-[10px] uppercase font-bold text-slate-400 block">Desvios de Natureza</span>
            <span className="text-sm font-bold text-purple-700">
              {audit.totalQtd} lançamentos ({`R$ ${audit.totalValor.toLocaleString("pt-BR", { minimumFractionDigits: 0 })}`})
            </span>
          </div>
        </div>
      </div>

      {/* Error Banner if any */}
      {errorMsg && (
        <div className="bg-rose-50 border border-rose-200 rounded-xl p-4 text-xs text-rose-800 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div>
            <p className="font-bold">Aviso do Sistema de IA:</p>
            <p className="mt-0.5">{errorMsg}</p>
            <p className="mt-1 text-[11px] text-rose-600">
              Certifique-se de que a variável de ambiente <code>GEMINI_API_KEY</code> está configurada no painel de configurações.
            </p>
          </div>
        </div>
      )}

      {/* Loading Skeleton */}
      {loading && (
        <div className="bg-white border border-slate-200 rounded-xl p-8 shadow-xs text-center space-y-3">
          <div className="w-12 h-12 rounded-full bg-purple-50 text-purple-600 mx-auto flex items-center justify-center animate-pulse">
            <Sparkles className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-bold text-slate-900">
            Auditando lançamentos e gerando parecer executivo...
          </h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            O Gemini está correlacionando saídas bancárias, contas genéricas, desvios de centro de custo e riscos de provisionamento.
          </p>
        </div>
      )}

      {/* Report Container */}
      {!loading && reportMarkdown && (
        <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
          {/* Action Header */}
          <div className="px-4 py-3 border-b border-slate-100 bg-slate-50/50 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Parecer de Controladoria Emitido
              </span>
            </div>
            <div className="flex items-center gap-2">
              <button
                id="btn-copiar-parecer"
                onClick={handleCopy}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 transition-colors cursor-pointer"
              >
                {copied ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                {copied ? "Copiado!" : "Copiar Texto"}
              </button>
              <button
                id="btn-baixar-parecer-txt"
                onClick={handleDownloadTxt}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-900 hover:bg-slate-800 text-white transition-colors cursor-pointer"
              >
                <Download className="w-3.5 h-3.5" />
                Baixar Parecer (.md)
              </button>
            </div>
          </div>

          {/* Markdown Content */}
          <div className="p-6 sm:p-8 prose prose-slate max-w-none text-slate-800 text-xs sm:text-sm leading-relaxed">
            <div className="markdown-body">
              <ReactMarkdown>{reportMarkdown}</ReactMarkdown>
            </div>
          </div>
        </div>
      )}

      {/* Placeholder state before first generation */}
      {!loading && !reportMarkdown && !errorMsg && (
        <div className="bg-white border border-dashed border-slate-300 rounded-xl p-8 sm:p-12 text-center">
          <div className="w-14 h-14 rounded-2xl bg-purple-50 text-purple-600 mx-auto flex items-center justify-center mb-3">
            <Bot className="w-7 h-7" />
          </div>
          <h3 className="text-base font-bold text-slate-900">
            Diagnóstico Executivo de Controladoria com Inteligência Artificial
          </h3>
          <p className="text-xs text-slate-500 max-w-lg mx-auto mt-1.5 leading-relaxed">
            Clique no botão acima para analisar a base de dados ativa. A IA avaliará automaticamente vulnerabilidades de liquidez, distorções contábeis e oportunidades de redução de despesas com base no extrato geral.
          </p>
          <button
            onClick={handleGenerateDiagnosis}
            className="mt-5 inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold bg-purple-600 hover:bg-purple-700 text-white transition-colors cursor-pointer"
          >
            <Sparkles className="w-4 h-4" />
            Iniciar Auditoria com IA
          </button>
        </div>
      )}
    </div>
  );
};
