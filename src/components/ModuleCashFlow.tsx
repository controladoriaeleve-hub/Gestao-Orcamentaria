import React, { useState } from "react";
import {
  Banknote,
  AlertTriangle,
  TrendingDown,
  Building2,
  Calendar,
  Layers,
  ArrowUpRight,
  Receipt,
  Percent,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  CartesianGrid,
  Cell,
} from "recharts";
import { BaseRecord, BankLiability } from "../types.ts";
import {
  calculateFinancialDrains,
  calculateDailyCashFlow,
} from "../utils/financialCalculations.ts";

interface ModuleCashFlowProps {
  filteredRecords: BaseRecord[];
  allRecords: BaseRecord[];
  bancosData: BankLiability[];
}

export const ModuleCashFlow: React.FC<ModuleCashFlowProps> = ({
  filteredRecords,
  bancosData,
}) => {
  const [activeSubTab, setActiveSubTab] = useState<"drenos" | "descascamento" | "passivos">("drenos");

  // Drenos
  const drenos = calculateFinancialDrains(filteredRecords);
  const totalVolume = filteredRecords.reduce((acc, r) => acc + r.valor, 0);
  const percentDrenos = totalVolume > 0 ? (drenos.total / totalVolume) * 100 : 0;

  // Descascamento de Caixa
  const { dias, mediaDiaria, maiorPico } = calculateDailyCashFlow(filteredRecords);

  // Passivos (Bancos)
  const passivosAbertos = bancosData.filter((b) => b.status === "EM ABERTO");
  const totalSaldoDevedor = passivosAbertos.reduce((acc, b) => acc + b.saldoDevedor, 0);
  const totalParcelasMes = passivosAbertos.reduce((acc, b) => acc + b.valorParcela, 0);

  return (
    <div className="space-y-6">
      {/* Top Banner & Sub-Navigation */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 sm:p-5 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Banknote className="w-5 h-5 text-emerald-600" />
              Módulo 1: Oportunidades de Fluxo de Caixa & Gestão de Liquidez
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              Monitore vazamentos de caixa em tarifas e encargos, equilibre o descascamento diário de pagamentos e acompanhe os passivos bancários.
            </p>
          </div>

          {/* Sub-Tabs Pills */}
          <div className="flex items-center bg-slate-100 p-1 rounded-lg border border-slate-200 text-xs font-semibold">
            <button
              id="subtab-drenos"
              onClick={() => setActiveSubTab("drenos")}
              className={`px-3 py-1.5 rounded-md transition-all cursor-pointer ${
                activeSubTab === "drenos"
                  ? "bg-white text-slate-900 shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Drenos Financeiros ({drenos.qtd})
            </button>
            <button
              id="subtab-descascamento"
              onClick={() => setActiveSubTab("descascamento")}
              className={`px-3 py-1.5 rounded-md transition-all cursor-pointer ${
                activeSubTab === "descascamento"
                  ? "bg-white text-slate-900 shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Descascamento Diário
            </button>
            <button
              id="subtab-passivos"
              onClick={() => setActiveSubTab("passivos")}
              className={`px-3 py-1.5 rounded-md transition-all cursor-pointer ${
                activeSubTab === "passivos"
                  ? "bg-white text-slate-900 shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Passivos Bancários ({bancosData.length})
            </button>
          </div>
        </div>

        {/* Global Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5 mt-5">
          <div className="bg-rose-50/70 border border-rose-200/80 rounded-xl p-3.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-rose-700">Drenos Financeiros Totais</span>
              <AlertTriangle className="w-4 h-4 text-rose-600" />
            </div>
            <div className="text-xl font-bold text-rose-900 mt-1">
              R$ {drenos.total.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <span className="text-[11px] text-rose-600">
              {percentDrenos.toFixed(2)}% do volume total ({drenos.qtd} ocorrências)
            </span>
          </div>

          <div className="bg-blue-50/70 border border-blue-200/80 rounded-xl p-3.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-blue-700">Média Diária de Saída</span>
              <Calendar className="w-4 h-4 text-blue-600" />
            </div>
            <div className="text-xl font-bold text-blue-900 mt-1">
              R$ {mediaDiaria.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <span className="text-[11px] text-blue-600">
              Pico máximo: {maiorPico.data ? `R$ ${maiorPico.valor.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}` : "N/D"}
            </span>
          </div>

          <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-700">Parcelas Mensais Bancos</span>
              <Building2 className="w-4 h-4 text-slate-600" />
            </div>
            <div className="text-xl font-bold text-slate-900 mt-1">
              R$ {totalParcelasMes.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <span className="text-[11px] text-slate-500">
              Saldo Devedor Total: R$ {totalSaldoDevedor.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
            </span>
          </div>
        </div>
      </div>

      {/* SUB-VIEW 1: DRENOS FINANCEIROS */}
      {activeSubTab === "drenos" && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            {drenos.porTipo.map((item) => (
              <div
                key={item.tipo}
                className="bg-white border border-slate-200 rounded-xl p-3 shadow-2xs hover:border-slate-300 transition-all"
              >
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                  {item.tipo}
                </span>
                <div className="text-base font-bold text-slate-900 mt-0.5">
                  R$ {item.total.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                </div>
                <span className="text-[11px] text-slate-500 font-medium">
                  {item.qtd} lançamento{item.qtd > 1 ? "s" : ""}
                </span>
              </div>
            ))}
          </div>

          {/* Drenos Table */}
          <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
            <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
              <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
                <Receipt className="w-4 h-4 text-slate-500" />
                Detalhamento dos Drenos Financeiros (Tarifas, IOF, Juros e Custas)
              </h3>
              <span className="text-xs text-slate-500">
                Mostrando {drenos.itens.length} lançamentos
              </span>
            </div>

            {drenos.itens.length === 0 ? (
              <div className="p-8 text-center text-slate-500 text-xs">
                Nenhum dreno financeiro identificado com os filtros selecionados.
              </div>
            ) : (
              <div className="overflow-x-auto max-h-96">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-slate-100/75 text-slate-600 font-semibold sticky top-0 z-10">
                    <tr>
                      <th className="py-2.5 px-3">Data</th>
                      <th className="py-2.5 px-3">Tipo de Dreno</th>
                      <th className="py-2.5 px-3">Histórico / Lançamento</th>
                      <th className="py-2.5 px-3">Credor / Banco</th>
                      <th className="py-2.5 px-3 text-right">Valor (R$)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {drenos.itens.map((d) => (
                      <tr key={d.id} className="hover:bg-rose-50/30 transition-colors">
                        <td className="py-2 px-3 text-slate-500 whitespace-nowrap">{d.data}</td>
                        <td className="py-2 px-3 whitespace-nowrap">
                          <span
                            className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-bold ${
                              d.tipoDreno === "TARIFA"
                                ? "bg-amber-100 text-amber-800"
                                : d.tipoDreno === "IOF"
                                ? "bg-purple-100 text-purple-800"
                                : d.tipoDreno === "JUROS" || d.tipoDreno === "MULTA"
                                ? "bg-rose-100 text-rose-800"
                                : "bg-slate-100 text-slate-800"
                            }`}
                          >
                            {d.tipoDreno}
                          </span>
                        </td>
                        <td className="py-2 px-3 font-medium text-slate-800">{d.lancamento}</td>
                        <td className="py-2 px-3 text-slate-600">{d.razaoSocial}</td>
                        <td className="py-2 px-3 text-right font-bold text-rose-700 whitespace-nowrap">
                          R$ {d.valor.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
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

      {/* SUB-VIEW 2: DESCASCAMENTO DE CAIXA */}
      {activeSubTab === "descascamento" && (
        <div className="space-y-4">
          <div className="bg-white border border-slate-200 rounded-xl p-4 sm:p-5 shadow-xs">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-4">
              <div>
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <TrendingDown className="w-4 h-4 text-emerald-600" />
                  Distribuição Diária de Desembolsos (Prevenção de Picos de Saída)
                </h3>
                <p className="text-xs text-slate-500">
                  Barras em vermelho representam dias com saídas superiores a 150% da média diária (R$ {mediaDiaria.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}).
                </p>
              </div>
              <div className="flex items-center gap-3 text-xs">
                <span className="flex items-center gap-1 text-slate-600">
                  <span className="w-3 h-3 rounded-xs bg-emerald-600 inline-block" /> Fluxo Regular
                </span>
                <span className="flex items-center gap-1 text-rose-700 font-semibold">
                  <span className="w-3 h-3 rounded-xs bg-rose-500 inline-block" /> Pico de Saída
                </span>
                <span className="flex items-center gap-1 text-slate-500">
                  <span className="w-3 h-0.5 border-t border-dashed border-red-500 inline-block" /> Média Diária
                </span>
              </div>
            </div>

            {dias.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-slate-400 text-xs">
                Nenhum lançamento no período filtrado.
              </div>
            ) : (
              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={dias} margin={{ top: 10, right: 10, left: 10, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis dataKey="dataFormatada" tick={{ fontSize: 11, fill: "#64748b" }} />
                    <YAxis
                      tick={{ fontSize: 11, fill: "#64748b" }}
                      tickFormatter={(val) => `R$ ${(val / 1000).toFixed(0)}k`}
                    />
                    <Tooltip
                      formatter={(val: any) => [
                        `R$ ${Number(val).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}`,
                        "Total Desembolsado",
                      ]}
                      labelFormatter={(lbl) => `Data: ${lbl}`}
                      contentStyle={{
                        backgroundColor: "#ffffff",
                        borderRadius: "8px",
                        border: "1px solid #e2e8f0",
                        fontSize: "12px",
                      }}
                    />
                    <ReferenceLine
                      y={mediaDiaria}
                      stroke="#ef4444"
                      strokeDasharray="4 4"
                      label={{ value: "Média Diária", fill: "#ef4444", fontSize: 10, position: "top" }}
                    />
                    <Bar dataKey="totalDia" radius={[4, 4, 0, 0]}>
                      {dias.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.isPico ? "#ef4444" : "#059669"} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          {/* Table of Peak Days */}
          <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
            <div className="px-4 py-3 border-b border-slate-100 bg-slate-50/50 flex justify-between items-center">
              <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Concentração Diária de Liquidez & Maiores Vencimentos
              </h4>
              <span className="text-[11px] text-slate-500">
                Ordene ou identifique dias que demandam alongamento de prazo com fornecedores
              </span>
            </div>
            <div className="overflow-x-auto max-h-64">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-100/75 text-slate-600 font-semibold sticky top-0">
                  <tr>
                    <th className="py-2.5 px-3">Data</th>
                    <th className="py-2.5 px-3">Status de Risco</th>
                    <th className="py-2.5 px-3">Qtd Lançamentos</th>
                    <th className="py-2.5 px-3">Principais Credores do Dia</th>
                    <th className="py-2.5 px-3 text-right">Total do Dia (R$)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {dias
                    .slice()
                    .sort((a, b) => b.totalDia - a.totalDia)
                    .map((dia) => (
                      <tr key={dia.data} className={dia.isPico ? "bg-rose-50/40" : "hover:bg-slate-50"}>
                        <td className="py-2 px-3 font-semibold text-slate-800">{dia.data}</td>
                        <td className="py-2 px-3">
                          {dia.isPico ? (
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800">
                              PICO DE SAÍDA (Alto Desembolso)
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-slate-100 text-slate-700">
                              Estável
                            </span>
                          )}
                        </td>
                        <td className="py-2 px-3 text-slate-600">{dia.qtdLancamentos} itens</td>
                        <td className="py-2 px-3 text-slate-500 truncate max-w-xs">{dia.fornecedoresPrincipais || "-"}</td>
                        <td className="py-2 px-3 text-right font-bold text-slate-900">
                          R$ {dia.totalDia.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* SUB-VIEW 3: PAINEL DE PASSIVOS (BANCOS) */}
      {activeSubTab === "passivos" && (
        <div className="space-y-4">
          <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
            <div className="px-4 py-3 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
              <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
                <Building2 className="w-4 h-4 text-slate-500" />
                Contratos Bancários, Empréstimos e Consórcios (Aba BANCOS)
              </h3>
              <span className="text-xs text-slate-500">
                Total de {bancosData.length} contratos cadastrados
              </span>
            </div>

            {bancosData.length === 0 ? (
              <div className="p-8 text-center text-slate-400 text-xs">
                Nenhum contrato encontrado na aba BANCOS do arquivo.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-slate-100/75 text-slate-600 font-semibold">
                    <tr>
                      <th className="py-2.5 px-3">Instituição Bancária</th>
                      <th className="py-2.5 px-3">Operação</th>
                      <th className="py-2.5 px-3">Contrato</th>
                      <th className="py-2.5 px-3">Dia Venc.</th>
                      <th className="py-2.5 px-3">Taxa / Custo Efetivo</th>
                      <th className="py-2.5 px-3">Parcelas Restantes</th>
                      <th className="py-2.5 px-3 text-right">Valor Parcela (R$)</th>
                      <th className="py-2.5 px-3 text-right">Saldo Devedor (R$)</th>
                      <th className="py-2.5 px-3 text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {bancosData.map((b) => (
                      <tr key={b.id} className="hover:bg-slate-50">
                        <td className="py-2.5 px-3 font-semibold text-slate-900">{b.banco}</td>
                        <td className="py-2.5 px-3">
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-700">
                            {b.tipoOperacao}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-slate-600">{b.contrato}</td>
                        <td className="py-2.5 px-3 text-slate-600">Dia {b.vencimentoDia}</td>
                        <td className="py-2.5 px-3 text-slate-600">{b.taxaJuros}</td>
                        <td className="py-2.5 px-3 text-slate-600">
                          {b.parcelasRestantes > 0 ? `${b.parcelasRestantes} meses` : "Quitado"}
                        </td>
                        <td className="py-2.5 px-3 text-right font-bold text-slate-900">
                          R$ {b.valorParcela.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                        </td>
                        <td className="py-2.5 px-3 text-right font-bold text-rose-700">
                          R$ {b.saldoDevedor.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                        </td>
                        <td className="py-2.5 px-3 text-center">
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                              b.status === "EM ABERTO"
                                ? "bg-amber-100 text-amber-800"
                                : "bg-emerald-100 text-emerald-800"
                            }`}
                          >
                            {b.status}
                          </span>
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
