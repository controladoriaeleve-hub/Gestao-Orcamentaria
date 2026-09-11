import React, { useState, useMemo } from "react";
import { Table, Search, Download, ChevronLeft, ChevronRight } from "lucide-react";
import { BaseRecord } from "../types.ts";
import * as XLSX from "xlsx";

interface RawDataTableProps {
  records: BaseRecord[];
}

export const RawDataTable: React.FC<RawDataTableProps> = ({ records }) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 25;

  const filtered = useMemo(() => {
    if (!searchTerm.trim()) return records;
    const term = searchTerm.toUpperCase();
    return records.filter(
      (r) =>
        r.lancamento.includes(term) ||
        r.razaoSocial.includes(term) ||
        r.cpfCnpj.includes(term) ||
        r.grupo.includes(term) ||
        r.descricaoNatureza.includes(term)
    );
  }, [records, searchTerm]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const displayed = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filtered.slice(start, start + pageSize);
  }, [filtered, currentPage, pageSize]);

  const handleExportAll = () => {
    const ws = XLSX.utils.json_to_sheet(filtered);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "EXTRATO_FILTRADO");
    XLSX.writeFile(wb, `extrato_filtrado_${new Date().toISOString().slice(0, 10)}.xlsx`);
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-xs overflow-hidden space-y-3">
      {/* Table Header Controls */}
      <div className="p-4 border-b border-slate-100 bg-slate-50/50 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Table className="w-4 h-4 text-emerald-600" />
            Extrato Geral: Lançamentos Detalhados (Aba BASE)
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Exibindo {filtered.length} lançamentos após filtros aplicados
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              placeholder="Buscar nesta tabela..."
              className="pl-8.5 pr-3 py-1.5 text-xs bg-white border border-slate-200 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-emerald-500 w-52 sm:w-64"
            />
          </div>

          <button
            onClick={handleExportAll}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 transition-colors cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            Exportar Excel
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead className="bg-slate-100/75 text-slate-600 font-semibold">
            <tr>
              <th className="py-2.5 px-3">Status</th>
              <th className="py-2.5 px-3">Mês</th>
              <th className="py-2.5 px-3">Data</th>
              <th className="py-2.5 px-3">Lançamento / Histórico</th>
              <th className="py-2.5 px-3">Razão Social</th>
              <th className="py-2.5 px-3">CPF/CNPJ</th>
              <th className="py-2.5 px-3">Grupo</th>
              <th className="py-2.5 px-3">Natureza</th>
              <th className="py-2.5 px-3">Tipo</th>
              <th className="py-2.5 px-3 text-right">Valor (R$)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {displayed.map((r) => (
              <tr key={r.id} className="hover:bg-slate-50">
                <td className="py-2 px-3">
                  <span
                    className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-bold ${
                      r.status === "EM ABERTO"
                        ? "bg-amber-100 text-amber-800"
                        : "bg-emerald-100 text-emerald-800"
                    }`}
                  >
                    {r.status}
                  </span>
                </td>
                <td className="py-2 px-3 text-slate-500">{r.mes}</td>
                <td className="py-2 px-3 text-slate-500 whitespace-nowrap">{r.data}</td>
                <td className="py-2 px-3 font-medium text-slate-800 max-w-xs truncate" title={r.lancamento}>
                  {r.lancamento}
                </td>
                <td className="py-2 px-3 text-slate-700 font-semibold">{r.razaoSocial}</td>
                <td className="py-2 px-3 text-slate-400 font-mono text-[11px]">{r.cpfCnpj || "-"}</td>
                <td className="py-2 px-3">
                  <span className="px-2 py-0.5 rounded-md text-[10px] font-medium bg-slate-100 text-slate-700">
                    {r.grupo}
                  </span>
                </td>
                <td className="py-2 px-3 text-slate-500 text-[11px] truncate max-w-xs">
                  {r.descricaoNatureza}
                </td>
                <td className="py-2 px-3 text-slate-500 text-[11px]">{r.tipo}</td>
                <td className="py-2 px-3 text-right font-bold text-slate-900 whitespace-nowrap">
                  R$ {r.valor.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      <div className="p-3 border-t border-slate-100 bg-slate-50/50 flex items-center justify-between text-xs text-slate-600">
        <div>
          Página <span className="font-bold text-slate-900">{currentPage}</span> de{" "}
          <span className="font-bold text-slate-900">{totalPages}</span> (Total: {filtered.length} registros)
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            className="p-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40 cursor-pointer"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
            className="p-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40 cursor-pointer"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
