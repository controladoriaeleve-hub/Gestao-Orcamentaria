import React, { useState, useMemo } from "react";
import {
  Banknote,
  TrendingDown,
  ShieldAlert,
  Clock,
  Sparkles,
  Table,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";
import {
  BaseRecord,
  BoardFixedExpense,
  BankLiability,
  GlobalFilters,
} from "./types.ts";
import {
  mockBaseRecords,
  mockBoardExpenses,
  mockBankLiabilities,
} from "./data/mockExtrato.ts";
import { parseExcelFile } from "./utils/excelParser.ts";

import { Header } from "./components/Header.tsx";
import { SidebarFilters } from "./components/SidebarFilters.tsx";
import { ModuleCashFlow } from "./components/ModuleCashFlow.tsx";
import { ModuleExpenseReduction } from "./components/ModuleExpenseReduction.tsx";
import { ModuleAuditNature } from "./components/ModuleAuditNature.tsx";
import { ModuleProvisioning } from "./components/ModuleProvisioning.tsx";
import { ModuleGeminiDiagnosis } from "./components/ModuleGeminiDiagnosis.tsx";
import { RawDataTable } from "./components/RawDataTable.tsx";

export default function App() {
  // Datasets
  const [baseRecords, setBaseRecords] = useState<BaseRecord[]>(mockBaseRecords);
  const [boardExpenses, setBoardExpenses] = useState<BoardFixedExpense[]>(mockBoardExpenses);
  const [bancosData, setBancosData] = useState<BankLiability[]>(mockBankLiabilities);
  const [filename, setFilename] = useState<string>("0. EXTRATO GERAL (DEMO)");
  const [isDemo, setIsDemo] = useState<boolean>(true);

  // Tab State
  const [activeTab, setActiveTab] = useState<"caixa" | "despesas" | "auditoria" | "provisao" | "ia" | "tabela">("caixa");

  // Notifications
  const [notification, setNotification] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Global Filters
  const [filters, setFilters] = useState<GlobalFilters>({
    mes: "TODOS",
    status: "TODOS",
    grupo: "TODOS",
    fornecedor: "TODOS",
    buscaGeral: "",
  });

  // Extract available filter options
  const availableMonths = useMemo(() => {
    return Array.from(new Set(baseRecords.map((r) => r.mes))).filter(Boolean);
  }, [baseRecords]);

  const availableStatuses = useMemo(() => {
    return Array.from(new Set(baseRecords.map((r) => r.status))).filter(Boolean);
  }, [baseRecords]);

  const availableGroups = useMemo(() => {
    return Array.from(new Set(baseRecords.map((r) => r.grupo))).filter(Boolean).sort();
  }, [baseRecords]);

  const availableSuppliers = useMemo(() => {
    return Array.from(new Set(baseRecords.map((r) => r.razaoSocial)))
      .filter((s) => s && s !== "NAN")
      .sort();
  }, [baseRecords]);

  // Filtered Records
  const filteredRecords = useMemo(() => {
    return baseRecords.filter((r) => {
      if (filters.mes !== "TODOS" && r.mes !== filters.mes) return false;
      if (filters.status !== "TODOS" && r.status !== filters.status) return false;
      if (filters.grupo !== "TODOS" && r.grupo !== filters.grupo) return false;
      if (filters.fornecedor !== "TODOS" && r.razaoSocial !== filters.fornecedor) return false;

      if (filters.buscaGeral.trim() !== "") {
        const query = filters.buscaGeral.toUpperCase();
        const matchesLancamento = (r.lancamento || "").includes(query);
        const matchesRazao = (r.razaoSocial || "").includes(query);
        const matchesCnpj = (r.cpfCnpj || "").includes(query);
        const matchesNatureza = (r.descricaoNatureza || "").includes(query);
        const matchesGrupo = (r.grupo || "").includes(query);

        if (!matchesLancamento && !matchesRazao && !matchesCnpj && !matchesNatureza && !matchesGrupo) {
          return false;
        }
      }

      return true;
    });
  }, [baseRecords, filters]);

  // Volume calculations
  const totalVolumeGeral = useMemo(() => {
    return baseRecords.reduce((acc, r) => acc + r.valor, 0);
  }, [baseRecords]);

  const filteredVolume = useMemo(() => {
    return filteredRecords.reduce((acc, r) => acc + r.valor, 0);
  }, [filteredRecords]);

  // File Upload Handler
  const handleUploadFile = async (file: File) => {
    try {
      const parsed = await parseExcelFile(file);
      if (parsed.base.length === 0) {
        setNotification({
          type: "error",
          text: "Nenhum lançamento foi encontrado na aba BASE do arquivo enviado.",
        });
        return;
      }

      setBaseRecords(parsed.base);
      if (parsed.despesasFixas.length > 0) {
        setBoardExpenses(parsed.despesasFixas);
      }
      if (parsed.bancos.length > 0) {
        setBancosData(parsed.bancos);
      }
      setFilename(parsed.filename);
      setIsDemo(false);

      // Reset filters to default
      setFilters({
        mes: "TODOS",
        status: "TODOS",
        grupo: "TODOS",
        fornecedor: "TODOS",
        buscaGeral: "",
      });

      setNotification({
        type: "success",
        text: `Arquivo '${file.name}' carregado com sucesso! ${parsed.base.length} lançamentos processados.`,
      });

      setTimeout(() => setNotification(null), 5000);
    } catch (err: any) {
      console.error("Erro ao analisar arquivo:", err);
      setNotification({
        type: "error",
        text: `Erro ao processar a planilha: ${err.message || "Formato incompatível"}.`,
      });
    }
  };

  const handleLoadDemo = () => {
    setBaseRecords(mockBaseRecords);
    setBoardExpenses(mockBoardExpenses);
    setBancosData(mockBankLiabilities);
    setFilename("0. EXTRATO GERAL (DEMO)");
    setIsDemo(true);
    setFilters({
      mes: "TODOS",
      status: "TODOS",
      grupo: "TODOS",
      fornecedor: "TODOS",
      buscaGeral: "",
    });
    setNotification({
      type: "success",
      text: "Dados modelo restaurados com sucesso.",
    });
    setTimeout(() => setNotification(null), 3500);
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
      {/* Header */}
      <Header
        filename={filename}
        isDemo={isDemo}
        totalRecords={baseRecords.length}
        totalVolume={totalVolumeGeral}
        onUpload={handleUploadFile}
        onLoadDemo={handleLoadDemo}
        baseData={baseRecords}
        boardData={boardExpenses}
        bancosData={bancosData}
      />

      {/* Notification Toast Banner */}
      {notification && (
        <div
          className={`px-4 py-2.5 text-xs font-semibold flex items-center justify-between border-b ${
            notification.type === "success"
              ? "bg-emerald-50 text-emerald-900 border-emerald-200"
              : "bg-rose-50 text-rose-900 border-rose-200"
          }`}
        >
          <div className="max-w-7xl mx-auto w-full flex items-center gap-2">
            {notification.type === "success" ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
            )}
            <span>{notification.text}</span>
          </div>
          <button
            onClick={() => setNotification(null)}
            className="text-slate-400 hover:text-slate-700 ml-4 font-bold"
          >
            &times;
          </button>
        </div>
      )}

      {/* Main Body */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 w-full flex-1">
        {/* Main Navigation Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-2 mb-6 border-b border-slate-200 scrollbar-none">
          <button
            id="tab-caixa"
            onClick={() => setActiveTab("caixa")}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-bold transition-all whitespace-nowrap cursor-pointer ${
              activeTab === "caixa"
                ? "bg-emerald-600 text-white shadow-xs"
                : "bg-white text-slate-600 hover:bg-slate-100 hover:text-slate-900 border border-slate-200"
            }`}
          >
            <Banknote className="w-4 h-4" />
            1. Fluxo de Caixa
          </button>

          <button
            id="tab-despesas"
            onClick={() => setActiveTab("despesas")}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-bold transition-all whitespace-nowrap cursor-pointer ${
              activeTab === "despesas"
                ? "bg-emerald-600 text-white shadow-xs"
                : "bg-white text-slate-600 hover:bg-slate-100 hover:text-slate-900 border border-slate-200"
            }`}
          >
            <TrendingDown className="w-4 h-4" />
            2. Redução de Despesas
          </button>

          <button
            id="tab-auditoria"
            onClick={() => setActiveTab("auditoria")}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-bold transition-all whitespace-nowrap cursor-pointer ${
              activeTab === "auditoria"
                ? "bg-emerald-600 text-white shadow-xs"
                : "bg-white text-slate-600 hover:bg-slate-100 hover:text-slate-900 border border-slate-200"
            }`}
          >
            <ShieldAlert className="w-4 h-4" />
            3. Auditoria de Naturezas
          </button>

          <button
            id="tab-provisao"
            onClick={() => setActiveTab("provisao")}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-bold transition-all whitespace-nowrap cursor-pointer ${
              activeTab === "provisao"
                ? "bg-emerald-600 text-white shadow-xs"
                : "bg-white text-slate-600 hover:bg-slate-100 hover:text-slate-900 border border-slate-200"
            }`}
          >
            <Clock className="w-4 h-4" />
            4. Provisionamento Preditivo
          </button>

          <button
            id="tab-ia"
            onClick={() => setActiveTab("ia")}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-bold transition-all whitespace-nowrap cursor-pointer ${
              activeTab === "ia"
                ? "bg-purple-600 text-white shadow-xs"
                : "bg-white text-purple-700 hover:bg-purple-50 border border-purple-200"
            }`}
          >
            <Sparkles className="w-4 h-4" />
            5. Diagnóstico IA
          </button>

          <button
            id="tab-tabela"
            onClick={() => setActiveTab("tabela")}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-bold transition-all whitespace-nowrap cursor-pointer ml-auto ${
              activeTab === "tabela"
                ? "bg-slate-900 text-white shadow-xs"
                : "bg-white text-slate-600 hover:bg-slate-100 hover:text-slate-900 border border-slate-200"
            }`}
          >
            <Table className="w-4 h-4" />
            Extrato Geral Completo
          </button>
        </div>

        {/* 2-Column Responsive Layout: Sidebar Filters + Main Active View */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 items-start">
          {/* Left Column: Filters */}
          <div className="lg:col-span-1">
            <SidebarFilters
              filters={filters}
              onFilterChange={setFilters}
              availableMonths={availableMonths}
              availableStatuses={availableStatuses}
              availableGroups={availableGroups}
              availableSuppliers={availableSuppliers}
              filteredCount={filteredRecords.length}
              totalCount={baseRecords.length}
              filteredVolume={filteredVolume}
            />
          </div>

          {/* Right Column: Active Module View */}
          <main className="lg:col-span-3 space-y-6">
            {activeTab === "caixa" && (
              <ModuleCashFlow
                filteredRecords={filteredRecords}
                allRecords={baseRecords}
                bancosData={bancosData}
              />
            )}

            {activeTab === "despesas" && (
              <ModuleExpenseReduction
                filteredRecords={filteredRecords}
                allRecords={baseRecords}
                boardExpenses={boardExpenses}
              />
            )}

            {activeTab === "auditoria" && (
              <ModuleAuditNature
                filteredRecords={filteredRecords}
                allRecords={baseRecords}
              />
            )}

            {activeTab === "provisao" && (
              <ModuleProvisioning
                allRecords={baseRecords}
                availableMonths={availableMonths}
              />
            )}

            {activeTab === "ia" && (
              <ModuleGeminiDiagnosis
                filteredRecords={filteredRecords}
                allRecords={baseRecords}
                boardExpenses={boardExpenses}
                bancosData={bancosData}
                availableMonths={availableMonths}
              />
            )}

            {activeTab === "tabela" && <RawDataTable records={filteredRecords} />}
          </main>
        </div>
      </div>
    </div>
  );
}
