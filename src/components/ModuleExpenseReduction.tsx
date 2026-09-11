import React, { useState } from "react";
import {
  TrendingDown,
  AlertCircle,
  Copy,
  Target,
  BarChart3,
  Award,
  Layers,
  CheckCircle,
} from "lucide-react";
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from "recharts";
import { BaseRecord, BoardFixedExpense } from "../types.ts";
import {
  calculateAbcCurve,
  detectDuplicatesAndAnomalies,
} from "../utils/financialCalculations.ts";

interface ModuleExpenseReductionProps {
  filteredRecords: BaseRecord[];
  allRecords: BaseRecord[];
  boardExpenses: BoardFixedExpense[];
}

export const ModuleExpenseReduction: React.FC<ModuleExpenseReductionProps> = ({
  filteredRecords,
  allRecords,
  boardExpenses,
}) => {
  const [activeSubTab, setActiveSubTab] = useState<"abc" | "duplicidades" | "fixas">("abc");

  // ABC Pareto
  const { fornecedores, classeA, classeB, classeC, totalGeral } = calculateAbcCurve(filteredRecords);

  // Top 15 for Pareto Chart
  const top15 = fornecedores.slice(0, 15).map((f) => ({
    name: f.razaoSocial.length > 18 ? `${f.razaoSocial.slice(0, 18)}...` : f.razaoSocial,
    fullName: f.razaoSocial,
    valor: f.valorTotal,
    percentualAcumulado: Number(f.percentualAcumulado.toFixed(1)),
    classe: f.classe,
  }));

  // Duplicidades
  const duplicidades = detectDuplicatesAndAnomalies(filteredRecords);
  const totalRiscoDuplicidade = duplicidades.reduce((acc, d) => acc + d.valor * (d.qtd - 1), 0);

  // Despesas Fixas: Comparação Realizado vs Meta
  const comparativoFixas = boardExpenses.map((meta) => {
    // Look for matching items in allRecords or filteredRecords
    const realizadosDoGrupo = filteredRecords.filter((r) => {
      const g = (r.grupo || "").toUpperCase();
      const l = (r.lancamento || "").toUpperCase();
      const target = meta.categoria.toUpperCase();
      return g.includes(target) || target.includes(g) || l.includes(target);
    });

    const totalRealizado = realizadosDoGrupo.reduce((acc, r) => acc + r.valor, 0);
    // If user filtered by a single month, compare directly to monthly budget; else average or total
    const desvio = totalRealizado - meta.metaMensal;
    const percentDesvio = meta.metaMensal > 0 ? (desvio / meta.metaMensal) * 100 : 0;

    return {
      categoria: meta.categoria,
      descricao: meta.descricao,
      metaMensal: meta.metaMensal,
      realizado: totalRealizado,
      desvio,
      percentDesvio,
      isOverBudget: desvio > 0,
      observacao: meta.observacao,
    };
  });

  return (
    <div className="space-y-6">
      {/* Top Card & Sub-Navigation */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 sm:p-5 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <TrendingDown className="w-5 h-5 text-emerald-600" />
              Módulo 2: Redução & Eficiência de Despesas
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              Curva de Pareto de credores para negociação estratégica, varredura de duplicidades e comparação contra o Board.
            </p>
          </div>

          <div className="flex items-center bg-slate-100 p-1 rounded-lg border border-slate-200 text-xs font-semibold">
            <button
              id="subtab-abc"
              onClick={() => setActiveSubTab("abc")}
              className={`px-3 py-1.5 rounded-md transition-all cursor-pointer ${
                activeSubTab === "abc"
                  ? "bg-white text-slate-900 shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Curva ABC (Pareto)
            </button>
            <button
              id="subtab-duplicidades"
              onClick={() => setActiveSubTab("duplicidades")}
              className={`px-3 py-1.5 rounded-md transition-all cursor-pointer flex items-center gap-1.5 ${
                activeSubTab === "duplicidades"
                  ? "bg-white text-slate-900 shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Duplicidades & Anomalias
              {duplicidades.length > 0 && (
                <span className="w-4 h-4 rounded-full bg-rose-600 text-white text-[10px] flex items-center justify-center font-bold">
                  {duplicidades.length}
                </span>
              )}
            </button>
            <button
              id="subtab-fixas"
              onClick={() => setActiveSubTab("fixas")}
              className={`px-3 py-1.5 rounded-md transition-all cursor-pointer ${
                activeSubTab === "fixas"
                  ? "bg-white text-slate-900 shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Metas Board vs Realizado
            </button>
          </div>
        </div>

        {/* Global KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5 mt-5">
          <div className="bg-emerald-50/70 border border-emerald-200/80 rounded-xl p-3.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-emerald-700">Fornecedores Classe A (Top 80%)</span>
              <Award className="w-4 h-4 text-emerald-600" />
            </div>
            <div className="text-xl font-bold text-emerald-900 mt-1">
              {classeA.length} credores ({((classeA.length / Math.max(1, fornecedores.length)) * 100).toFixed(0)}%)
            </div>
            <span className="text-[11px] text-emerald-700">
              Concentram R$ {classeA.reduce((acc, c) => acc + c.valorTotal, 0).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
            </span>
          </div>

          <div className="bg-amber-50/70 border border-amber-200/80 rounded-xl p-3.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-amber-700">Risco em Duplicidades</span>
              <AlertCircle className="w-4 h-4 text-amber-600" />
            </div>
            <div className="text-xl font-bold text-amber-900 mt-1">
              R$ {totalRiscoDuplicidade.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
            </div>
            <span className="text-[11px] text-amber-700">
              {duplicidades.length} alertas de pagamentos repetidos no mesmo mês
            </span>
          </div>

          <div className="bg-purple-50/70 border border-purple-200/80 rounded-xl p-3.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-purple-700">Categorias Despesas Fixas</span>
              <Target className="w-4 h-4 text-purple-600" />
            </div>
            <div className="text-xl font-bold text-purple-900 mt-1">
              {boardExpenses.length} centros monitorados
            </div>
            <span className="text-[11px] text-purple-700">
              Comparativo direto da aba 'DESPESA FIXA BOARD'
            </span>
          </div>
        </div>
      </div>

      {/* SUB-VIEW 1: CURVA ABC / PARETO */}
      {activeSubTab === "abc" && (
        <div className="space-y-4">
          <div className="bg-white border border-slate-200 rounded-xl p-4 sm:p-5 shadow-xs">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-4">
              <div>
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-emerald-600" />
                  Gráfico de Pareto (Top 15 Fornecedores vs % Acumulado)
                </h3>
                <p className="text-xs text-slate-500">
                  Foque a renegociação de prazos e descontos nos fornecedores Classe A para máximo impacto no caixa.
                </p>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
                  Classe A (80% do volume)
                </span>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-800">
                  Classe B (15% do volume)
                </span>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-700">
                  Classe C (5% cauda longa)
                </span>
              </div>
            </div>

            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={top15} margin={{ top: 20, right: 20, bottom: 40, left: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis
                    dataKey="name"
                    tick={{ fontSize: 10, fill: "#64748b" }}
                    angle={-25}
                    textAnchor="end"
                    interval={0}
                  />
                  <YAxis
                    yAxisId="left"
                    tick={{ fontSize: 11, fill: "#64748b" }}
                    tickFormatter={(val) => `R$ ${(val / 1000).toFixed(0)}k`}
                  />
                  <YAxis
                    yAxisId="right"
                    orientation="right"
                    domain={[0, 100]}
                    tick={{ fontSize: 11, fill: "#64748b" }}
                    tickFormatter={(val) => `${val}%`}
                  />
                  <Tooltip
                    formatter={(val: any, name: string) => {
                      if (name === "Percentual Acumulado") return [`${val}%`, name];
                      return [`R$ ${Number(val).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}`, name];
                    }}
                    labelFormatter={(_label, payload) => {
                      const full = payload?.[0]?.payload?.fullName;
                      return full ? `Fornecedor: ${full}` : "";
                    }}
                    contentStyle={{
                      backgroundColor: "#ffffff",
                      borderRadius: "8px",
                      border: "1px solid #e2e8f0",
                      fontSize: "12px",
                    }}
                  />
                  <Legend wrapperStyle={{ paddingTop: "12px", fontSize: "12px" }} />
                  <Bar
                    yAxisId="left"
                    dataKey="valor"
                    name="Valor Desembolsado (R$)"
                    fill="#059669"
                    radius={[4, 4, 0, 0]}
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="percentualAcumulado"
                    name="Percentual Acumulado"
                    stroke="#2563eb"
                    strokeWidth={2.5}
                    dot={{ r: 3, fill: "#2563eb" }}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Suppliers Table */}
          <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
            <div className="px-4 py-3 border-b border-slate-100 bg-slate-50/50 flex justify-between items-center">
              <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Ranking Completo da Curva ABC de Credores
              </h4>
              <span className="text-xs text-slate-500">
                {fornecedores.length} fornecedores identificados
              </span>
            </div>
            <div className="overflow-x-auto max-h-72">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-100/75 text-slate-600 font-semibold sticky top-0">
                  <tr>
                    <th className="py-2.5 px-3">Posição</th>
                    <th className="py-2.5 px-3">Classe ABC</th>
                    <th className="py-2.5 px-3">Razão Social / Credor</th>
                    <th className="py-2.5 px-3 text-center">Lançamentos</th>
                    <th className="py-2.5 px-3 text-right">% do Total</th>
                    <th className="py-2.5 px-3 text-right">% Acumulado</th>
                    <th className="py-2.5 px-3 text-right">Valor Total (R$)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {fornecedores.map((f, idx) => (
                    <tr key={f.razaoSocial} className="hover:bg-slate-50">
                      <td className="py-2 px-3 text-slate-400 font-bold">{idx + 1}º</td>
                      <td className="py-2 px-3">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            f.classe === "A"
                              ? "bg-emerald-100 text-emerald-800"
                              : f.classe === "B"
                              ? "bg-blue-100 text-blue-800"
                              : "bg-slate-100 text-slate-700"
                          }`}
                        >
                          Classe {f.classe}
                        </span>
                      </td>
                      <td className="py-2 px-3 font-semibold text-slate-900">{f.razaoSocial}</td>
                      <td className="py-2 px-3 text-center text-slate-600">{f.qtdLancamentos}</td>
                      <td className="py-2 px-3 text-right text-slate-600">{f.percentual.toFixed(2)}%</td>
                      <td className="py-2 px-3 text-right text-slate-600">{f.percentualAcumulado.toFixed(1)}%</td>
                      <td className="py-2 px-3 text-right font-bold text-slate-900">
                        R$ {f.valorTotal.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* SUB-VIEW 2: DUPLICIDADES & ANOMALIAS */}
      {activeSubTab === "duplicidades" && (
        <div className="space-y-4">
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-xs text-amber-900 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-amber-900">
                Detecção Preditiva de Pagamentos em Duplicidade
              </p>
              <p className="text-amber-800 mt-1">
                Lançamentos com mesmo fornecedor, mesmo valor monetário exato e no mesmo mês de competência. Em caso de emissão equivocada de boleto ou falha humana no ERP, este filtro previne pagamento duplo antes da compensação.
              </p>
            </div>
          </div>

          {duplicidades.length === 0 ? (
            <div className="bg-white border border-slate-200 rounded-xl p-8 text-center shadow-xs">
              <CheckCircle className="w-10 h-10 text-emerald-600 mx-auto mb-2" />
              <h4 className="text-sm font-bold text-slate-900">Nenhuma duplicidade óbvia encontrada!</h4>
              <p className="text-xs text-slate-500 mt-1">
                Não foram identificados lançamentos com mesmo fornecedor, valor e mês nos registros filtrados.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {duplicidades.map((dup, idx) => (
                <div
                  key={`${dup.mes}-${dup.razaoSocial}-${dup.valor}-${idx}`}
                  className="bg-white border border-amber-200 rounded-xl p-4 shadow-xs"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-100 pb-3 mb-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-900">
                          {dup.qtd} lançamentos idênticos
                        </span>
                        <span className="text-xs font-semibold text-slate-500">Mês: {dup.mes}</span>
                      </div>
                      <h4 className="text-sm font-bold text-slate-900 mt-1">{dup.razaoSocial}</h4>
                    </div>
                    <div className="text-right">
                      <span className="text-xs text-slate-500 block">Valor Unitário</span>
                      <span className="text-base font-bold text-rose-600">
                        R$ {dup.valor.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                      </span>
                    </div>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead className="bg-slate-50 text-slate-600 font-semibold">
                        <tr>
                          <th className="py-2 px-3">ID / Linha</th>
                          <th className="py-2 px-3">Data</th>
                          <th className="py-2 px-3">Histórico / Lançamento</th>
                          <th className="py-2 px-3">Grupo Contábil</th>
                          <th className="py-2 px-3 text-center">Status</th>
                          <th className="py-2 px-3 text-right">Valor</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {dup.registros.map((reg) => (
                          <tr key={reg.id} className="hover:bg-amber-50/40">
                            <td className="py-2 px-3 text-slate-400">#{reg.id}</td>
                            <td className="py-2 px-3 text-slate-600">{reg.data}</td>
                            <td className="py-2 px-3 font-medium text-slate-800">{reg.lancamento}</td>
                            <td className="py-2 px-3 text-slate-600">{reg.grupo}</td>
                            <td className="py-2 px-3 text-center">
                              <span
                                className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                                  reg.status === "EM ABERTO"
                                    ? "bg-amber-100 text-amber-800"
                                    : "bg-emerald-100 text-emerald-800"
                                }`}
                              >
                                {reg.status}
                              </span>
                            </td>
                            <td className="py-2 px-3 text-right font-bold text-slate-900">
                              R$ {reg.valor.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* SUB-VIEW 3: DESPESAS FIXAS BOARD VS REALIZADO */}
      {activeSubTab === "fixas" && (
        <div className="space-y-4">
          <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
            <div className="px-4 py-3 border-b border-slate-100 bg-slate-50/50 flex justify-between items-center">
              <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
                <Target className="w-4 h-4 text-slate-500" />
                Acompanhamento Orçamentário: Metas da Diretoria vs. Realizado
              </h3>
              <span className="text-xs text-slate-500">
                Alinhado com a aba 'DESPESA FIXA BOARD'
              </span>
            </div>

            {comparativoFixas.length === 0 ? (
              <div className="p-8 text-center text-slate-500 text-xs">
                Nenhuma meta cadastrada na aba 'DESPESA FIXA BOARD'.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-slate-100/75 text-slate-600 font-semibold">
                    <tr>
                      <th className="py-2.5 px-3">Centro de Custo / Categoria</th>
                      <th className="py-2.5 px-3">Descrição / Escopo</th>
                      <th className="py-2.5 px-3 text-right">Meta Mensal (R$)</th>
                      <th className="py-2.5 px-3 text-right">Realizado (R$)</th>
                      <th className="py-2.5 px-3 text-right">Variação (R$)</th>
                      <th className="py-2.5 px-3 text-center">Status Orçamentário</th>
                      <th className="py-2.5 px-3">Observação da Controladoria</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {comparativoFixas.map((comp) => (
                      <tr key={comp.categoria} className={comp.isOverBudget ? "bg-rose-50/30" : "hover:bg-slate-50"}>
                        <td className="py-2.5 px-3 font-bold text-slate-900">{comp.categoria}</td>
                        <td className="py-2.5 px-3 text-slate-600">{comp.descricao}</td>
                        <td className="py-2.5 px-3 text-right font-medium text-slate-700">
                          R$ {comp.metaMensal.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                        </td>
                        <td className="py-2.5 px-3 text-right font-bold text-slate-900">
                          R$ {comp.realizado.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                        </td>
                        <td
                          className={`py-2.5 px-3 text-right font-bold ${
                            comp.desvio > 0 ? "text-rose-600" : "text-emerald-700"
                          }`}
                        >
                          {comp.desvio > 0 ? "+" : ""}
                          R$ {comp.desvio.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                        </td>
                        <td className="py-2.5 px-3 text-center">
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                              comp.isOverBudget
                                ? "bg-rose-100 text-rose-800"
                                : "bg-emerald-100 text-emerald-800"
                            }`}
                          >
                            {comp.isOverBudget ? `Acima da Meta (+${comp.percentDesvio.toFixed(0)}%)` : "Dentro da Meta"}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-slate-500 text-[11px]">{comp.observacao || "-"}</td>
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
