import * as XLSX from "xlsx";
import { BaseRecord, BoardFixedExpense, BankLiability, ReclassificationAdjustment } from "../types.ts";

export interface ParsedExcelResult {
  base: BaseRecord[];
  despesasFixas: BoardFixedExpense[];
  bancos: BankLiability[];
  sheetNames: string[];
  filename: string;
}

function cleanString(val: any): string {
  if (val === null || val === undefined) return "";
  return String(val).trim();
}

function parseNumber(val: any): number {
  if (typeof val === "number") return isNaN(val) ? 0 : val;
  if (!val) return 0;
  const str = String(val).trim();
  // Remove currency symbols, fix Brazilian vs US decimal formats
  const cleanStr = str
    .replace(/[R$\s]/g, "")
    .replace(/\./g, "")
    .replace(/,/g, ".");
  const num = parseFloat(cleanStr);
  return isNaN(num) ? 0 : num;
}

function formatDate(val: any): string {
  if (!val) return new Date().toISOString().split("T")[0];
  if (val instanceof Date) {
    return val.toISOString().split("T")[0];
  }
  if (typeof val === "number") {
    // Excel serial date to JS Date
    const date = new Date(Math.round((val - 25569) * 86400 * 1000));
    return isNaN(date.getTime()) ? new Date().toISOString().split("T")[0] : date.toISOString().split("T")[0];
  }
  const str = String(val).trim();
  // Check if DD/MM/YYYY
  if (/^\d{2}\/\d{2}\/\d{4}$/.test(str)) {
    const parts = str.split("/");
    return `${parts[2]}-${parts[1]}-${parts[0]}`;
  }
  return str;
}

export async function parseExcelFile(file: File): Promise<ParsedExcelResult> {
  const arrayBuffer = await file.arrayBuffer();
  const workbook = XLSX.read(arrayBuffer, { type: "array", cellDates: true });

  const sheetNames = workbook.SheetNames;

  // 1. Locate BASE Sheet
  const baseSheetName =
    sheetNames.find((s) => s.toUpperCase() === "BASE") ||
    sheetNames.find((s) => s.toUpperCase().includes("EXTRATO") || s.toUpperCase().includes("LANC")) ||
    sheetNames[0];

  const baseRawRows: any[] = baseSheetName
    ? XLSX.utils.sheet_to_json(workbook.Sheets[baseSheetName], { defval: "" })
    : [];

  const base: BaseRecord[] = baseRawRows.map((row, idx) => {
    // Flexible header mapping
    const getField = (keys: string[]) => {
      for (const k of Object.keys(row)) {
        const cleanK = k.trim().toUpperCase();
        if (keys.some((target) => cleanK === target.toUpperCase() || cleanK.includes(target.toUpperCase()))) {
          return row[k];
        }
      }
      return "";
    };

    const statusVal = cleanString(getField(["STATUS"])) || "PAGO";
    const mesVal = cleanString(getField(["MÊS", "MES"])) || "GERAL";
    const dataVal = formatDate(getField(["DATA", "VENCIMENTO", "PAGAMENTO"]));
    const lancamentoVal = cleanString(getField(["LANÇAMENTO", "LANCAMENTO", "HISTÓRICO", "DESCRICAO", "DESCRIÇÃO"]));
    const razaoVal = cleanString(getField(["RAZÃO SOCIAL", "RAZAO SOCIAL", "FORNECEDOR", "CREDOR", "BENEFICIÁRIO"]));
    const cpfCnpjVal = cleanString(getField(["CPF/CNPJ", "CNPJ", "CPF", "DOCUMENTO"]));
    const valorVal = parseNumber(getField(["VALOR (R$)", "VALOR", "VALOR R$", "VALOR LIQUIDO", "TOTAL"]));
    const codGrupoVal = cleanString(getField(["CÓD GRUPO", "COD GRUPO", "COD. GRUPO", "CODIGO GRUPO"]));
    const grupoVal = cleanString(getField(["GRUPO", "CENTRO DE CUSTO", "CATEGORIA", "CLASSIFICAÇÃO"])) || "OUTROS";
    const codNaturezaVal = cleanString(getField(["CÓD. NATUREZA", "COD NATUREZA", "COD. NATUREZA"]));
    const descNaturezaVal = cleanString(getField(["DESCRIÇÃO NATUREZA", "DESCRICAO NATUREZA", "NATUREZA"]));
    const tipoVal = cleanString(getField(["TIPO", "TIPO DESPESA"])) || "VARIÁVEL";

    return {
      id: idx + 1,
      status: statusVal.toUpperCase().includes("ABERTO") ? "EM ABERTO" : "PAGO",
      mes: mesVal.toUpperCase(),
      data: dataVal,
      dataRaw: getField(["DATA"]),
      lancamento: lancamentoVal.toUpperCase(),
      razaoSocial: razaoVal ? razaoVal.toUpperCase() : "NAN",
      cpfCnpj: cpfCnpjVal,
      valor: valorVal,
      codGrupo: codGrupoVal,
      grupo: grupoVal.toUpperCase(),
      codNatureza: codNaturezaVal,
      descricaoNatureza: descNaturezaVal,
      tipo: tipoVal.toUpperCase(),
    };
  });

  // 2. Locate DESPESA FIXA BOARD Sheet
  const boardSheetName = sheetNames.find(
    (s) =>
      s.toUpperCase().includes("BOARD") ||
      s.toUpperCase().includes("FIXA") ||
      s.toUpperCase().includes("ORCADO")
  );

  let despesasFixas: BoardFixedExpense[] = [];
  if (boardSheetName) {
    const boardRawRows: any[] = XLSX.utils.sheet_to_json(workbook.Sheets[boardSheetName], { defval: "" });
    despesasFixas = boardRawRows.map((row) => ({
      categoria: cleanString(row["Categoria"] || row["CATEGORIA"] || row["Grupo"] || Object.values(row)[0]),
      descricao: cleanString(row["Descrição"] || row["Descricao"] || row["DESCRICAO"] || row["Item"] || ""),
      metaMensal: parseNumber(row["Meta Mensal (R$)"] || row["Meta"] || row["Orçado"] || row["META"] || row["Valor"]),
      realizadoMedio: parseNumber(row["Realizado"] || row["Realizado Médio"] || 0),
      observacao: cleanString(row["Observação"] || row["Observacao"] || row["Status"] || ""),
    }));
  }

  // 3. Locate BANCOS Sheet
  const bancosSheetName = sheetNames.find(
    (s) =>
      s.toUpperCase().includes("BANCO") ||
      s.toUpperCase().includes("PASSIVO") ||
      s.toUpperCase().includes("EMPRESTIMO")
  );

  let bancos: BankLiability[] = [];
  if (bancosSheetName) {
    const bancosRawRows: any[] = XLSX.utils.sheet_to_json(workbook.Sheets[bancosSheetName], { defval: "" });
    bancos = bancosRawRows.map((row, idx) => ({
      id: idx + 1,
      banco: cleanString(row["Banco"] || row["Instituição"] || row["BANCO"] || "Banco"),
      tipoOperacao: cleanString(row["Tipo de Operação"] || row["Tipo"] || row["Modalidade"] || "EMPRÉSTIMO"),
      contrato: cleanString(row["Contrato"] || row["Nº Contrato"] || `CTR-${idx + 1}`),
      saldoDevedor: parseNumber(row["Saldo Devedor (R$)"] || row["Saldo Devedor"] || row["Saldo"]),
      valorParcela: parseNumber(row["Valor Parcela (R$)"] || row["Parcela"] || row["Valor Parcela"]),
      parcelasRestantes: parseInt(cleanString(row["Parcelas Restantes"] || row["Qtd Parcelas"] || "12"), 10) || 0,
      vencimentoDia: parseInt(cleanString(row["Dia Vencimento"] || row["Vencimento"] || "20"), 10) || 10,
      taxaJuros: cleanString(row["Taxa de Juros"] || row["Taxa"] || "CDI + spread"),
      status: cleanString(row["Status"] || "EM ABERTO").toUpperCase().includes("PAGO") ? "PAGO" : "EM ABERTO",
    }));
  }

  return {
    base,
    despesasFixas,
    bancos,
    sheetNames,
    filename: file.name,
  };
}

// Export Reclassification Matrix to CSV
export function exportAdjustmentsToCsv(adjustments: ReclassificationAdjustment[]) {
  const headers = [
    "ID_Linha",
    "Lançamento",
    "Razão Social",
    "Valor (R$)",
    "Grupo Atual",
    "Grupo Sugerido",
    "Palavra-Chave Detectada",
    "Motivo do Ajuste",
    "Status Aprovação",
  ];

  const rows = adjustments.map((adj) => [
    adj.idLinha,
    `"${(adj.lancamento || "").replace(/"/g, '""')}"`,
    `"${(adj.razaoSocial || "").replace(/"/g, '""')}"`,
    adj.valor.toFixed(2),
    `"${(adj.grupoAtual || "").replace(/"/g, '""')}"`,
    `"${(adj.grupoSugerido || "").replace(/"/g, '""')}"`,
    `"${adj.palavraChave}"`,
    `"${(adj.motivo || "").replace(/"/g, '""')}"`,
    adj.statusAprovacao || "PENDENTE",
  ]);

  const csvContent = "\uFEFF" + [headers.join(";"), ...rows.map((r) => r.join(";"))].join("\r\n");
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.setAttribute("href", url);
  link.setAttribute("download", `matriz_reclassificacao_contabil_${new Date().toISOString().slice(0, 10)}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// Generate Downloadable 0. EXTRATO GERAL.xlsx Sample File
export function generateSampleExcelWorkbook(
  base: BaseRecord[],
  board: BoardFixedExpense[],
  bancos: BankLiability[]
) {
  const wb = XLSX.utils.book_new();

  // Sheet 1: BASE
  const baseData = base.map((r) => ({
    Status: r.status,
    Mês: r.mes,
    Data: r.data,
    Lançamento: r.lancamento,
    "Razão Social": r.razaoSocial,
    "CPF/CNPJ": r.cpfCnpj,
    "Valor (R$)": r.valor,
    "Cód Grupo": r.codGrupo,
    Grupo: r.grupo,
    "Cód. Natureza": r.codNatureza,
    "Descrição Natureza": r.descricaoNatureza,
    TIPO: r.tipo,
  }));
  const wsBase = XLSX.utils.json_to_sheet(baseData);
  XLSX.utils.book_append_sheet(wb, wsBase, "BASE");

  // Sheet 2: DESPESA FIXA BOARD
  const boardData = board.map((b) => ({
    Categoria: b.categoria,
    Descrição: b.descricao,
    "Meta Mensal (R$)": b.metaMensal,
    "Realizado Médio (R$)": b.realizadoMedio || 0,
    Observação: b.observacao || "",
  }));
  const wsBoard = XLSX.utils.json_to_sheet(boardData);
  XLSX.utils.book_append_sheet(wb, wsBoard, "DESPESA FIXA BOARD");

  // Sheet 3: BANCOS
  const bancosData = bancos.map((bk) => ({
    Banco: bk.banco,
    "Tipo de Operação": bk.tipoOperacao,
    Contrato: bk.contrato,
    "Saldo Devedor (R$)": bk.saldoDevedor,
    "Valor Parcela (R$)": bk.valorParcela,
    "Parcelas Restantes": bk.parcelasRestantes,
    "Dia Vencimento": bk.vencimentoDia,
    "Taxa de Juros": bk.taxaJuros,
    Status: bk.status,
  }));
  const wsBancos = XLSX.utils.json_to_sheet(bancosData);
  XLSX.utils.book_append_sheet(wb, wsBancos, "BANCOS");

  XLSX.writeFile(wb, "0. EXTRATO GERAL_MODELO.xlsx");
}
