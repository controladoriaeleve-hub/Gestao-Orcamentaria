import React from "react";
import { Filter, Search, RotateCcw, Calendar, CheckSquare, Layers, Building } from "lucide-react";
import { GlobalFilters } from "../types.ts";

interface SidebarFiltersProps {
  filters: GlobalFilters;
  onFilterChange: (newFilters: GlobalFilters) => void;
  availableMonths: string[];
  availableStatuses: string[];
  availableGroups: string[];
  availableSuppliers: string[];
  filteredCount: number;
  totalCount: number;
  filteredVolume: number;
}

export const SidebarFilters: React.FC<SidebarFiltersProps> = ({
  filters,
  onFilterChange,
  availableMonths,
  availableStatuses,
  availableGroups,
  availableSuppliers,
  filteredCount,
  totalCount,
  filteredVolume,
}) => {
  const handleReset = () => {
    onFilterChange({
      mes: "TODOS",
      status: "TODOS",
      grupo: "TODOS",
      fornecedor: "TODOS",
      buscaGeral: "",
    });
  };

  const isFiltered =
    filters.mes !== "TODOS" ||
    filters.status !== "TODOS" ||
    filters.grupo !== "TODOS" ||
    filters.fornecedor !== "TODOS" ||
    filters.buscaGeral.trim() !== "";

  return (
    <aside className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs h-fit space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-emerald-600" />
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
            Filtros Globais
          </h2>
        </div>
        {isFiltered && (
          <button
            id="btn-reset-filters"
            onClick={handleReset}
            className="inline-flex items-center gap-1 text-xs font-semibold text-slate-500 hover:text-rose-600 transition-colors cursor-pointer"
            title="Limpar todos os filtros"
          >
            <RotateCcw className="w-3 h-3" />
            Limpar
          </button>
        )}
      </div>

      {/* Busca Rápida */}
      <div>
        <label className="block text-xs font-semibold text-slate-600 mb-1.5">
          Busca Geral (Histórico, Credor, CNPJ)
        </label>
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            id="input-busca-geral"
            type="text"
            value={filters.buscaGeral}
            onChange={(e) => onFilterChange({ ...filters, buscaGeral: e.target.value })}
            placeholder="Ex: Tarifa, PIX, Manutenção..."
            className="w-full pl-8.5 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-emerald-500 focus:bg-white text-slate-900 transition-all"
          />
        </div>
      </div>

      {/* Mês */}
      <div>
        <label className="flex items-center gap-1.5 text-xs font-semibold text-slate-600 mb-1.5">
          <Calendar className="w-3.5 h-3.5 text-slate-400" />
          Mês de Competência
        </label>
        <select
          id="select-filtro-mes"
          value={filters.mes}
          onChange={(e) => onFilterChange({ ...filters, mes: e.target.value })}
          className="w-full px-2.5 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-emerald-500 focus:bg-white text-slate-900 font-medium"
        >
          <option value="TODOS">Todos os Meses ({availableMonths.length})</option>
          {availableMonths.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>
      </div>

      {/* Status */}
      <div>
        <label className="flex items-center gap-1.5 text-xs font-semibold text-slate-600 mb-1.5">
          <CheckSquare className="w-3.5 h-3.5 text-slate-400" />
          Status de Pagamento
        </label>
        <select
          id="select-filtro-status"
          value={filters.status}
          onChange={(e) => onFilterChange({ ...filters, status: e.target.value })}
          className="w-full px-2.5 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-emerald-500 focus:bg-white text-slate-900 font-medium"
        >
          <option value="TODOS">Todos os Status</option>
          {availableStatuses.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>

      {/* Grupo de Despesa */}
      <div>
        <label className="flex items-center gap-1.5 text-xs font-semibold text-slate-600 mb-1.5">
          <Layers className="w-3.5 h-3.5 text-slate-400" />
          Grupo de Despesa
        </label>
        <select
          id="select-filtro-grupo"
          value={filters.grupo}
          onChange={(e) => onFilterChange({ ...filters, grupo: e.target.value })}
          className="w-full px-2.5 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-emerald-500 focus:bg-white text-slate-900 font-medium"
        >
          <option value="TODOS">Todos os Grupos ({availableGroups.length})</option>
          {availableGroups.map((g) => (
            <option key={g} value={g}>
              {g}
            </option>
          ))}
        </select>
      </div>

      {/* Fornecedor / Razão Social */}
      <div>
        <label className="flex items-center gap-1.5 text-xs font-semibold text-slate-600 mb-1.5">
          <Building className="w-3.5 h-3.5 text-slate-400" />
          Credor / Razão Social
        </label>
        <select
          id="select-filtro-fornecedor"
          value={filters.fornecedor}
          onChange={(e) => onFilterChange({ ...filters, fornecedor: e.target.value })}
          className="w-full px-2.5 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-emerald-500 focus:bg-white text-slate-900 font-medium"
        >
          <option value="TODOS">Todos os Credores ({availableSuppliers.length})</option>
          {availableSuppliers.map((f) => (
            <option key={f} value={f}>
              {f.length > 28 ? `${f.slice(0, 28)}...` : f}
            </option>
          ))}
        </select>
      </div>

      {/* Filtered Summary Card */}
      <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 space-y-1.5 text-xs">
        <div className="flex justify-between items-center text-slate-500">
          <span>Itens Selecionados:</span>
          <span className="font-semibold text-slate-800">
            {filteredCount} de {totalCount} ({((filteredCount / Math.max(1, totalCount)) * 100).toFixed(0)}%)
          </span>
        </div>
        <div className="flex justify-between items-center text-slate-500">
          <span>Subtotal Filtrado:</span>
          <span className="font-bold text-emerald-700">
            R$ {filteredVolume.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
        </div>
      </div>
    </aside>
  );
};
