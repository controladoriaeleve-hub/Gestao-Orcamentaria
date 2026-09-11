import React, { useState } from "react";
import {
  Clock,
  AlertOctagon,
  CalendarCheck2,
  CheckCircle2,
  HelpCircle,
  TrendingUp,
  DollarSign,
  ArrowRight,
} from "lucide-react";
import { BaseRecord } from "../types.ts";
import { runPredictiveProvisioning } from "../utils/financialCalculations.ts";

interface ModuleProvisioningProps {
  allRecords: BaseRecord[];
  availableMonths: string[];
}

export const ModuleProvisioning: React.FC<ModuleProvisioningProps> = ({
  allRecords,
  availableMonths,
}) => {
  // Default to the last month or first
  const [selectedMonth, setSelectedMonth] = useState<string>(
    availableMonths[availableMonths.length - 1] || "MAR/2026"
  );

  const { recorrentesHistoricos, alertasFaltaProvisao, totalRiscoNaoProvisionado } =
    runPredictiveProvisioning(allRecords, selectedMonth);

  const volumeTotalMes = allRecords
    .filter((r) => r.mes === selectedMonth)
    .reduce((acc, r) => acc + r.valor, 0);

  const volumeRealEstimado = volumeTotalMes + totalRiscoNaoProvisionado;

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 sm:p-5 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Clock className="w-5 h-5 text-emerald-600" />
              Módulo 4: Necessidade de Provisionamento Preditivo & Contas a Pagar Ocultas
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              Varredura de fornecedores e contas essenciais recorrentes que ainda não constam no extrato do mês selecionado.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-600 whitespace-nowrap">
              Mês de Análise:
            </span>
            <select
              id="select-mes-provisao"
              value={selectedMonth}
              onChange={(e) => setSelectedMonth(e.target.value)}
              className="px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-emerald-500 font-bold text-slate-900"
            >
              {availableMonths.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Global Summary Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5 mt-5">
          <div className="bg-rose-50/80 border border-rose-200 rounded-xl p-3.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-rose-700">Risco em Despesas Não Provisionadas</span>
              <AlertOctagon className="w-4 h-4 text-rose-600" />
            </div>
            <div className="text-xl font-bold text-rose-900 mt-1">
              R$ {totalRiscoNaoProvisionado.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
            </div>
            <span className="text-[11px] text-rose-700">
              {alertasFaltaProvisao.length} contas recorrentes ausentes em {selectedMonth}
            </span>
          </div>

          <div className="bg-blue-50/80 border border-blue-200 rounded-xl p-3.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-blue-700">Desembolso Já Registrado ({selectedMonth})</span>
              <DollarSign className="w-4 h-4 text-blue-600" />
            </div>
            <div className="text-xl font-bold text-blue-900 mt-1">
              R$ {volumeTotalMes.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
            </div>
            <span className="text-[11px] text-blue-700">
              Lançamentos já contidos na base do mês
            </span>
          </div>

          <div className="bg-emerald-50/80 border border-emerald-200 rounded-xl p-3.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-emerald-700">Impacto Financeiro Real Estimado</span>
              <TrendingUp className="w-4 h-4 text-emerald-600" />
            </div>
            <div className="text-xl font-bold text-emerald-900 mt-1">
              R$ {volumeRealEstimado.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
            </div>
            <span className="text-[11px] text-emerald-700">
              Desembolsos atuais + Provisões necessárias
            </span>
          </div>
        </div>
      </div>

      {/* Alertas de Provisão */}
      <div className="space-y-4">
        <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-100 bg-slate-50/50 flex justify-between items-center text-xs">
            <h3 className="font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
              <AlertOctagon className="w-4 h-4 text-rose-500" />
              Fornecedores Críticos Recorrentes Ausentes no Mês ({selectedMonth})
            </h3>
            <span className="text-slate-500">
              {alertasFaltaProvisao.length} alertas identificados
            </span>
          </div>

          {alertasFaltaProvisao.length === 0 ? (
            <div className="p-8 text-center text-slate-500 text-xs">
              <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto mb-2" />
              <p className="font-bold text-slate-800">Todas as despesas recorrentes mapeadas constam no mês!</p>
              <p className="text-slate-400 mt-0.5">Nenhuma anomalia de provisionamento identificada.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-100/75 text-slate-600 font-semibold">
                  <tr>
                    <th className="py-2.5 px-3">Razão Social / Credor</th>
                    <th className="py-2.5 px-3">Categoria Estimada</th>
                    <th className="py-2.5 px-3 text-center">Frequência Histórica</th>
                    <th className="py-2.5 px-3 text-right">Média Mensal Histórica</th>
                    <th className="py-2.5 px-3 text-center">Status no Mês {selectedMonth}</th>
                    <th className="py-2.5 px-3">Ação Recomendada pela Controladoria</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {alertasFaltaProvisao.map((alerta) => (
                    <tr key={alerta.razaoSocial} className="hover:bg-rose-50/20">
                      <td className="py-2.5 px-3 font-bold text-slate-900">{alerta.razaoSocial}</td>
                      <td className="py-2.5 px-3">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-100 text-slate-700">
                          {alerta.categoriaEstimada}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-center text-slate-600 font-medium">
                        Presente em {alerta.mesesRecorrentes} meses
                      </td>
                      <td className="py-2.5 px-3 text-right font-bold text-rose-600">
                        R$ {alerta.valorMedioMensal.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-2.5 px-3 text-center">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800">
                          NÃO LOCALIZADO
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-slate-600 text-[11px]">
                        Provisionar R$ {alerta.valorMedioMensal.toLocaleString("pt-BR", { minimumFractionDigits: 2 })} no fluxo de caixa ou verificar se boleto/nota fiscal já foi emitido.
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Informative Governance Card */}
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-xs text-slate-700 flex items-start gap-3">
          <CalendarCheck2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="font-bold text-slate-900">Por que o Provisionamento Preditivo é Essencial?</h4>
            <p className="text-slate-600 leading-relaxed">
              Muitas empresas operam com falsa sensação de sobra de caixa no início ou meio do mês porque fornecedores essenciais (energia elétrica, servidores na nuvem, aluguéis ou folha complementar) ainda não enviaram a fatura. Ao comparar a recorrência histórica contra a base do mês corrente, a Controladoria protege o saldo mínimo operacional.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
