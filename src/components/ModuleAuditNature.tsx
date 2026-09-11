import React, { useState } from "react";
import {
  ShieldAlert,
  Trash2,
  UserX,
  FileSpreadsheet,
  Download,
  Check,
  X,
  AlertTriangle,
  ArrowRight,
  Filter,
} from "lucide-react";
import { BaseRecord, ReclassificationAdjustment } from "../types.ts";
import {
  calculateTrashAccounts,
  calculateMissingRegistration,
  auditNatureInconsistencies,
} from "../utils/financialCalculations.ts";
import { exportAdjustmentsToCsv } from "../utils/excelParser.ts";

interface ModuleAuditNatureProps {
  filteredRecords: BaseRecord[];
  allRecords: BaseRecord[];
}

export const ModuleAuditNature: React.FC<ModuleAuditNatureProps> = ({
  filteredRecords,
}) => {
  const [activeSubTab, setActiveSubTab] = useState<"lixeira" | "sem_cadastro" | "inconsistencias">("inconsistencias");

  // Contas Lixeira
  const lixeira = calculateTrashAccounts(filteredRecords);

  // Sem Cadastro
  const semCadastro = calculateMissingRegistration(filteredRecords);

  // Inconsistências de Natureza
  const initialAudit = auditNatureInconsistencies(filteredRecords);
  const [adjustments, setAdjustments] = useState<ReclassificationAdjustment[]>(initialAudit.ajustes);

  // Keep state updated when filtered records change
  React.useEffect(() => {
    const updated = auditNatureInconsistencies(filteredRecords);
    setAdjustments(updated.ajustes);
  }, [filteredRecords]);

  const handleApprove = (idLinha: number) => {
    setAdjustments((prev) =>
      prev.map((a) => (a.idLinha === idLinha ? { ...a, statusAprovacao: "APROVADO" } : a))
    );
  };

  const handleDiscard = (idLinha: number) => {
    setAdjustments((prev) =>
      prev.map((a) => (a.idLinha === idLinha ? { ...a, statusAprovacao: "DESCARTADO" } : a))
    );
  };

  const handleExportCsv = () => {
    exportAdjustmentsToCsv(adjustments);
  };

  const totalAprovados = adjustments.filter((a) => a.statusAprovacao === "APROVADO").length;
  const totalAuditadoValor = adjustments.reduce((acc, a) => acc + a.valor, 0);

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 sm:p-5 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-rose-600" />
              Módulo 3: Auditoria de Naturezas de Gastos & Erros Contábeis
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              Varredura de contas "lixeira", pagamentos avulsos sem CNPJ e inconsistências semânticas entre histórico e plano de contas.
            </p>
          </div>

          <div className="flex items-center bg-slate-100 p-1 rounded-lg border border-slate-200 text-xs font-semibold">
            <button
              id="subtab-inconsistencias"
              onClick={() => setActiveSubTab("inconsistencias")}
              className={`px-3 py-1.5 rounded-md transition-all cursor-pointer flex items-center gap-1.5 ${
                activeSubTab === "inconsistencias"
                  ? "bg-white text-slate-900 shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Matriz de Reclassificação
              {adjustments.length > 0 && (
                <span className="w-4 h-4 rounded-full bg-rose-600 text-white text-[10px] flex items-center justify-center font-bold">
                  {adjustments.length}
                </span>
              )}
            </button>
            <button
              id="subtab-lixeira"
              onClick={() => setActiveSubTab("lixeira")}
              className={`px-3 py-1.5 rounded-md transition-all cursor-pointer ${
                activeSubTab === "lixeira"
                  ? "bg-white text-slate-900 shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Contas "Lixeira" ({lixeira.qtd})
            </button>
            <button
              id="subtab-sem-cadastro"
              onClick={() => setActiveSubTab("sem_cadastro")}
              className={`px-3 py-1.5 rounded-md transition-all cursor-pointer ${
                activeSubTab === "sem_cadastro"
                  ? "bg-white text-slate-900 shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Sem Razão / CNPJ ({semCadastro.qtd})
            </button>
          </div>
        </div>

        {/* Global Summary Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5 mt-5">
          <div className="bg-rose-50/80 border border-rose-200 rounded-xl p-3.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-rose-700">Contas "Lixeira" / Genéricas</span>
              <Trash2 className="w-4 h-4 text-rose-600" />
            </div>
            <div className="text-xl font-bold text-rose-900 mt-1">
              R$ {lixeira.total.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
            </div>
            <span className="text-[11px] text-rose-700">
              {lixeira.qtd} lançamentos em grupos vagos (Ex: Outros, Diversos)
            </span>
          </div>

          <div className="bg-amber-50/80 border border-amber-200 rounded-xl p-3.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-amber-700">Sem Cadastro / Sem CNPJ</span>
              <UserX className="w-4 h-4 text-amber-600" />
            </div>
            <div className="text-xl font-bold text-amber-900 mt-1">
              R$ {semCadastro.total.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
            </div>
            <span className="text-[11px] text-amber-700">
              {semCadastro.qtd} pagamentos com alto risco de glosa fiscal
            </span>
          </div>

          <div className="bg-purple-50/80 border border-purple-200 rounded-xl p-3.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-purple-700">Desvios de Natureza Detectados</span>
              <AlertTriangle className="w-4 h-4 text-purple-600" />
            </div>
            <div className="text-xl font-bold text-purple-900 mt-1">
              R$ {totalAuditadoValor.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
            </div>
            <span className="text-[11px] text-purple-700">
              {adjustments.length} ajustes sugeridos para reclassificação
            </span>
          </div>
        </div>
      </div>

      {/* SUB-VIEW 1: MATRIZ DE RECLASSIFICAÇÃO */}
      {activeSubTab === "inconsistencias" && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
            <div>
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
                Matriz de Reclassificação Contábil & Exportação ERP
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Valide os ajustes identificados pelas regras semânticas e faça o download do lote para importação no ERP.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button
                id="btn-export-matriz-csv"
                onClick={handleExportCsv}
                disabled={adjustments.length === 0}
                className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white disabled:opacity-50 shadow-xs transition-colors cursor-pointer"
              >
                <Download className="w-3.5 h-3.5" />
                Baixar Matriz de Ajustes (CSV)
              </button>
            </div>
          </div>

          {adjustments.length === 0 ? (
            <div className="bg-white border border-slate-200 rounded-xl p-8 text-center shadow-xs">
              <Check className="w-8 h-8 text-emerald-600 mx-auto mb-2" />
              <h4 className="text-sm font-bold text-slate-900">Nenhuma divergência semântica encontrada!</h4>
              <p className="text-xs text-slate-500 mt-1">
                Todas as despesas no recorte filtrado estão compatíveis com o plano de contas configurado.
              </p>
            </div>
          ) : (
            <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-100 bg-slate-50/50 flex justify-between items-center text-xs">
                <span className="font-semibold text-slate-700">
                  Total de {adjustments.length} lançamentos a reclassificar ({totalAprovados} validados pelo auditor)
                </span>
                <span className="text-slate-500">
                  Volume auditado: R$ {totalAuditadoValor.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                </span>
              </div>

              <div className="overflow-x-auto max-h-[500px]">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-slate-100/75 text-slate-600 font-semibold sticky top-0 z-10">
                    <tr>
                      <th className="py-2.5 px-3">Linha / ID</th>
                      <th className="py-2.5 px-3">Lançamento / Histórico</th>
                      <th className="py-2.5 px-3">Fornecedor</th>
                      <th className="py-2.5 px-3 text-right">Valor (R$)</th>
                      <th className="py-2.5 px-3">Grupo Atual</th>
                      <th className="py-2.5 px-3 text-center"></th>
                      <th className="py-2.5 px-3">Grupo Sugerido</th>
                      <th className="py-2.5 px-3">Motivo / Palavra-Chave</th>
                      <th className="py-2.5 px-3 text-center">Status / Ação</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {adjustments.map((adj) => (
                      <tr
                        key={adj.idLinha}
                        className={`transition-colors ${
                          adj.statusAprovacao === "APROVADO"
                            ? "bg-emerald-50/50"
                            : adj.statusAprovacao === "DESCARTADO"
                            ? "bg-slate-100/60 opacity-60"
                            : "hover:bg-slate-50"
                        }`}
                      >
                        <td className="py-2 px-3 text-slate-400 font-mono">#{adj.idLinha}</td>
                        <td className="py-2 px-3 font-medium text-slate-900 max-w-xs">{adj.lancamento}</td>
                        <td className="py-2 px-3 text-slate-600">{adj.razaoSocial}</td>
                        <td className="py-2 px-3 text-right font-bold text-slate-900">
                          R$ {adj.valor.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                        </td>
                        <td className="py-2 px-3">
                          <span className="px-2 py-0.5 rounded-md text-[11px] font-medium bg-rose-50 text-rose-800 border border-rose-200">
                            {adj.grupoAtual}
                          </span>
                        </td>
                        <td className="py-2 px-1 text-center text-slate-400">
                          <ArrowRight className="w-3.5 h-3.5 inline" />
                        </td>
                        <td className="py-2 px-3">
                          <span className="px-2 py-0.5 rounded-md text-[11px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
                            {adj.grupoSugerido}
                          </span>
                        </td>
                        <td className="py-2 px-3 text-slate-500 text-[11px]">
                          <span className="font-semibold text-slate-700">'{adj.palavraChave}'</span>: {adj.motivo}
                        </td>
                        <td className="py-2 px-3 text-center whitespace-nowrap">
                          {adj.statusAprovacao === "APROVADO" ? (
                            <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-700">
                              <Check className="w-3.5 h-3.5" /> Aprovado
                            </span>
                          ) : adj.statusAprovacao === "DESCARTADO" ? (
                            <span className="inline-flex items-center gap-1 text-[11px] font-bold text-slate-500">
                              <X className="w-3.5 h-3.5" /> Descartado
                            </span>
                          ) : (
                            <div className="flex items-center justify-center gap-1.5">
                              <button
                                onClick={() => handleApprove(adj.idLinha)}
                                className="p-1 rounded-md bg-emerald-100 hover:bg-emerald-200 text-emerald-800 transition-colors cursor-pointer"
                                title="Aprovar Reclassificação"
                              >
                                <Check className="w-3.5 h-3.5" />
                              </button>
                              <button
                                onClick={() => handleDiscard(adj.idLinha)}
                                className="p-1 rounded-md bg-slate-100 hover:bg-slate-200 text-slate-600 transition-colors cursor-pointer"
                                title="Descartar Sugestão"
                              >
                                <X className="w-3.5 h-3.5" />
                              </button>
                            </div>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* SUB-VIEW 2: CONTAS LIXEIRA */}
      {activeSubTab === "lixeira" && (
        <div className="space-y-4">
          <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
            <div className="px-4 py-3 border-b border-slate-100 bg-slate-50/50 flex justify-between items-center text-xs">
              <h4 className="font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
                <Trash2 className="w-4 h-4 text-rose-500" />
                Lançamentos em Grupos Genéricos / "Lixeira"
              </h4>
              <span className="text-slate-500">
                Total de {lixeira.itens.length} lançamentos a redistribuir
              </span>
            </div>

            {lixeira.itens.length === 0 ? (
              <div className="p-8 text-center text-slate-500 text-xs">
                Nenhum lançamento alocado em contas genéricas no período filtrado.
              </div>
            ) : (
              <div className="overflow-x-auto max-h-96">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-slate-100/75 text-slate-600 font-semibold sticky top-0">
                    <tr>
                      <th className="py-2.5 px-3">Data</th>
                      <th className="py-2.5 px-3">Histórico / Lançamento</th>
                      <th className="py-2.5 px-3">Grupo Contábil Atual</th>
                      <th className="py-2.5 px-3">Fornecedor</th>
                      <th className="py-2.5 px-3 text-right">Valor (R$)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {lixeira.itens.map((i) => (
                      <tr key={i.id} className="hover:bg-rose-50/30">
                        <td className="py-2 px-3 text-slate-500 whitespace-nowrap">{i.data}</td>
                        <td className="py-2 px-3 font-medium text-slate-800">{i.lancamento}</td>
                        <td className="py-2 px-3">
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800">
                            {i.grupo}
                          </span>
                        </td>
                        <td className="py-2 px-3 text-slate-600">{i.razaoSocial}</td>
                        <td className="py-2 px-3 text-right font-bold text-rose-700">
                          R$ {i.valor.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* SUB-VIEW 3: SEM CADASTRO / SEM CNPJ */}
      {activeSubTab === "sem_cadastro" && (
        <div className="space-y-4">
          <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
            <div className="px-4 py-3 border-b border-slate-100 bg-slate-50/50 flex justify-between items-center text-xs">
              <h4 className="font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
                <UserX className="w-4 h-4 text-amber-500" />
                Pagamentos sem Razão Social ou CNPJ Preenchidos
              </h4>
              <span className="text-slate-500">
                {semCadastro.itens.length} ocorrências cadastrais
              </span>
            </div>

            {semCadastro.itens.length === 0 ? (
              <div className="p-8 text-center text-slate-500 text-xs">
                Todos os lançamentos do período possuem credor e CNPJ identificados!
              </div>
            ) : (
              <div className="overflow-x-auto max-h-96">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-slate-100/75 text-slate-600 font-semibold sticky top-0">
                    <tr>
                      <th className="py-2.5 px-3">Data</th>
                      <th className="py-2.5 px-3">Histórico</th>
                      <th className="py-2.5 px-3">Credor Informado</th>
                      <th className="py-2.5 px-3">Documento (CPF/CNPJ)</th>
                      <th className="py-2.5 px-3">Risco Fiscal</th>
                      <th className="py-2.5 px-3 text-right">Valor (R$)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {semCadastro.itens.map((item) => (
                      <tr key={item.id} className="hover:bg-amber-50/30">
                        <td className="py-2 px-3 text-slate-500 whitespace-nowrap">{item.data}</td>
                        <td className="py-2 px-3 font-medium text-slate-800">{item.lancamento}</td>
                        <td className="py-2 px-3 text-amber-900 font-semibold">
                          {item.razaoSocial === "NAN" || !item.razaoSocial ? "NÃO IDENTIFICADO" : item.razaoSocial}
                        </td>
                        <td className="py-2 px-3 text-slate-400 font-mono">
                          {item.cpfCnpj || "CAMPO VAZIO"}
                        </td>
                        <td className="py-2 px-3">
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800">
                            Falta Cadastro / Risco de Glosa
                          </span>
                        </td>
                        <td className="py-2 px-3 text-right font-bold text-slate-900">
                          R$ {item.valor.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
