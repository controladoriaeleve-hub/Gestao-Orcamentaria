import React, { useRef } from "react";
import {
  FileSpreadsheet,
  Upload,
  Sparkles,
  Download,
  CheckCircle2,
  Database,
  Building2,
} from "lucide-react";
import { BaseRecord, BoardFixedExpense, BankLiability } from "../types.ts";
import { generateSampleExcelWorkbook } from "../utils/excelParser.ts";

interface HeaderProps {
  filename: string;
  isDemo: boolean;
  totalRecords: number;
  totalVolume: number;
  onUpload: (file: File) => void;
  onLoadDemo: () => void;
  baseData: BaseRecord[];
  boardData: BoardFixedExpense[];
  bancosData: BankLiability[];
}

export const Header: React.FC<HeaderProps> = ({
  filename,
  isDemo,
  totalRecords,
  totalVolume,
  onUpload,
  onLoadDemo,
  baseData,
  boardData,
  bancosData,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onUpload(file);
    }
  };

  const handleDownloadTemplate = () => {
    generateSampleExcelWorkbook(baseData, boardData, bancosData);
  };

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          {/* Logo & Title */}
          <div className="flex items-center gap-3.5">
            <div className="w-11 h-11 rounded-xl bg-slate-900 text-white flex items-center justify-center shadow-sm">
              <Building2 className="w-6 h-6 text-emerald-400" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h1 className="text-xl font-bold text-slate-900 tracking-tight">
                  Controladoria & Auditoria Financeira
                </h1>
                <span
                  className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                    isDemo
                      ? "bg-amber-50 text-amber-800 border border-amber-200"
                      : "bg-emerald-50 text-emerald-800 border border-emerald-200"
                  }`}
                >
                  <Database className="w-3 h-3" />
                  {isDemo ? "Demonstração (0. EXTRATO GERAL)" : filename}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Saneamento de naturezas de despesas, otimização de fluxo de caixa e diagnóstico de governança
              </p>
            </div>
          </div>

          {/* Quick Metrics & Actions */}
          <div className="flex flex-wrap items-center gap-2.5 sm:gap-3">
            <div className="hidden sm:flex items-center gap-3 px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs">
              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-semibold">Lançamentos</span>
                <span className="font-bold text-slate-800">{totalRecords}</span>
              </div>
              <div className="w-px h-6 bg-slate-200" />
              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-semibold">Volume Analisado</span>
                <span className="font-bold text-slate-900">
                  R$ {totalVolume.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
              </div>
            </div>

            {/* Hidden Input */}
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".xlsx,.xls,.csv"
              className="hidden"
            />

            {/* Actions */}
            <button
              id="btn-upload-excel"
              onClick={() => fileInputRef.current?.click()}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white shadow-xs transition-colors cursor-pointer"
              title="Carregar seu arquivo Excel ou CSV"
            >
              <Upload className="w-3.5 h-3.5" />
              Importar Extrato (.xlsx)
            </button>

            <button
              id="btn-load-demo"
              onClick={onLoadDemo}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-300 transition-colors cursor-pointer"
              title="Recarregar base modelo com inconsistências pré-configuradas"
            >
              <Sparkles className="w-3.5 h-3.5 text-amber-600" />
              Restaurar Dados Modelo
            </button>

            <button
              id="btn-download-template"
              onClick={handleDownloadTemplate}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 transition-colors cursor-pointer"
              title="Baixar planilha modelo '0. EXTRATO GERAL.xlsx' com 3 abas"
            >
              <Download className="w-3.5 h-3.5 text-slate-500" />
              Baixar Modelo (.xlsx)
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
