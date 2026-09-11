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
  if (["-", "--", "nan", "NAN", "null", "NULL", ""].includes(str)) return 0;

  // Remove currency symbols and spaces
  let cleanStr = str.replace(/[R$\s]/g, "");
  // Brazilian format: 5.214,09 -> 5214.09
  if (cleanStr.includes(",") && cleanStr.includes(".")) {
    cleanStr = cleanStr.replace(/\./g, "").replace(/,/g, ".");
  } else if (cleanStr.includes(",") && !cleanStr.includes(".")) {
    cleanStr = cleanStr.replace(/,/g, ".");
  }
  const num = parseFloat(cleanStr);
  return isNaN(num) ? 0 : num;
}

const MES_MAP: Record<string, string> = {
  "1": "01 - JAN", "2": "02 - FEV", "3": "03 - MAR", "4": "04 - ABR",
  "5": "05 - MAI", "6": "06 - JUN", "7": "07 - JUL", "8": "08 - AGO",
  "9": "09 - SET", "10": "10 - OUT", "11": "11 - NOV", "12": "12 - DEZ",
  "01": "01 - JAN", "02": "02 - FEV", "03": "03 - MAR", "04": "04 - ABR",
  "05": "05 - MAI", "06": "06 - JUN", "07": "07 - JUL", "08": "08 - AGO",
  "09": "09 - SET"
};

function formatMes(val: any, dataStr?: string): string {
  if (val === null || val === undefined) val = "";
  let s = String(val).trim();
  if (s.endsWith(".0")) s = s.split(".")[0];
  if (MES_MAP[s]) {
    if (dataStr && !isNaN(Date.parse(dataStr))) {
      const year = new Date(dataStr).getFullYear();
      return `${MES_MAP[s].split(" - ")[1]}/${year}`;
    }
    return MES_MAP[s];
  }
  if (!s || s.toUpperCase() === "NAN" || s.toUpperCase() === "NULL") {
    if (dataStr && !isNaN(Date.parse(dataStr))) {
      const d = new Date(dataStr);
      const mNames = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"];
      return `${mNames[d.getMonth()]}/${d.getFullYear()}`;
    }
    return "GERAL";
  }
  return s.toUpperCase();
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

/**
 * Lê uma aba do Excel procurando inteligentemente a linha de cabeçalho
 * mesmo que as primeiras linhas sejam vazias ou títulos mesclados.
 */
function sheetToSmartJson(sheet: XLSX.WorkSheet): any[] {
  if (!sheet) return [];
  const rawData: any[][] = XLSX.utils.sheet_to_json(sheet, { header: 1, defval: "" });
  if (!rawData || rawData.length === 0) return [];

  const keywords = [
    "STATUS", "MES", "DATA", "LANCAMENTO", "HISTORICO", "RAZAO",
    "FORNECEDOR", "CREDOR", "CPF", "CNPJ", "VALOR", "GRUPO", "NATUREZA",
    "TIPO", "BANCO", "SALDO", "PARCELA", "CATEGORIA", "DESCRICAO", "META"
  ];

  let headerRowIndex = 0;
  let maxScore = 0;

  for (let r = 0; r < Math.min(25, rawData.length); r++) {
    const row = rawData[r];
    if (!Array.isArray(row)) continue;
    let score = 0;
    for (const cell of row) {
      if (cell !== undefined && cell !== null) {
        const cellStr = String(cell)
          .normalize("NFD")
          .replace(/[\u0300-\u036f]/g, "")
          .toUpperCase()
          .trim();
        for (const kw of keywords) {
          if (cellStr.includes(kw)) {
            score++;
            break;
          }
        }
      }
    }
    if (score > maxScore) {
      maxScore = score;
      headerRowIndex = r;
    }
  }

  if (maxScore >= 2) {
    const headers = (rawData[headerRowIndex] || []).map((h: any) => String(h || "").trim());
    const dataRows: any[] = [];
    for (let i = headerRowIndex + 1; i < rawData.length; i++) {
      const row = rawData[i];
      if (!Array.isArray(row) || row.every((c) => c === "" || c === null || c === undefined)) continue;
      const obj: Record<string, any> = {};
      headers.forEach((h: string, colIdx: number) => {
        if (h) {
          obj[h] = row[colIdx] !== undefined ? row[colIdx] : "";
        }
      });
      dataRows.push(obj);
    }
    return dataRows;
  }

  return XLSX.utils.sheet_to_json(sheet, { defval: "" });
}

export async function parseExcelFile(file: File): Promise<ParsedExcelResult> {
  const arrayBuffer = await file.arrayBuffer();
  const workbook = XLSX.read(arrayBuffer, { type: "array", cellDates: true });

  const sheetNames = workbook.SheetNames;

  // 1. Locate BASE Sheet
  const baseSheetName =
    sheetNames.find((s) => s.toUpperCase() === "BASE") ||
    sheetNames.find((s) => s.toUpperCase().includes("EXTRATO") || s.toUpperCase().includes("LANC") || s.toUpperCase().includes("GERAL")) ||
    sheetNames[0];

  const baseRawRows: any[] = baseSheetName
    ? sheetToSmartJson(workbook.Sheets[baseSheetName])
    : [];

  const base: BaseRecord[] = baseRawRows.map((row, idx) => {
    // Flexible header mapping
    const getField = (keys: string[]) => {
      for (const k of Object.keys(row)) {
        const cleanK = k
          .normalize("NFD")
          .replace(/[\u0300-\u036f]/g, "")
          .trim()
          .toUpperCase();
        if (
          keys.some((target) => {
            const cleanTarget = target
              .normalize("NFD")
              .replace(/[\u0300-\u036f]/g, "")
              .trim()
              .toUpperCase();
            return cleanK === cleanTarget || cleanK.includes(cleanTarget);
          })
        ) {
          return row[k];
        }
      }
      return "";
    };

    const statusVal = cleanString(getField(["STATUS"])) || "PAGO";
    const dataVal = formatDate(getField(["DATA", "VENCIMENTO", "PAGAMENTO"]));
    const mesVal = formatMes(getField(["MÊS", "MES"]), dataVal);
    const lancamentoVal = cleanString(getField(["LANÇAMENTO", "LANCAMENTO", "HISTÓRICO", "DESCRICAO", "DESCRIÇÃO"]));
    let razaoVal = cleanString(getField(["RAZÃO SOCIAL", "RAZAO SOCIAL", "FORNECEDOR", "CREDOR", "BENEFICIÁRIO"]));
    if (!razaoVal || razaoVal === "-" || razaoVal.toUpperCase() === "NAN") {
      razaoVal = "NÃO IDENTIFICADO";
    }
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
      lancamento: lancamentoVal.toUpperCase() || "SEM HISTÓRICO",
      razaoSocial: razaoVal ? razaoVal.toUpperCase() : "NÃO IDENTIFICADO",
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
    const boardRawRows: any[] = sheetToSmartJson(workbook.Sheets[boardSheetName]);
    despesasFixas = boardRawRows.map((row) => {
      const getBoardField = (keys: string[]) => {
        for (const k of Object.keys(row)) {
          const cleanK = k.normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim().toUpperCase();
          if (keys.some((target) => cleanK.includes(target.toUpperCase()))) {
            return row[k];
          }
        }
        return "";
      };
      return {
        categoria: cleanString(getBoardField(["CATEGORIA", "GRUPO"]) || Object.values(row)[0] || "GERAL"),
        descricao: cleanString(getBoardField(["DESCRICAO", "ITEM", "DETALHE"])),
        metaMensal: parseNumber(getBoardField(["META", "ORCADO", "PREVISTO", "VALOR"])),
        realizadoMedio: parseNumber(getBoardField(["REALIZADO", "MEDIO", "ATUAL", "GASTO"])),
        observacao: cleanString(getBoardField(["OBSERVACAO", "NOTA", "STATUS"])),
      };
    });
  }

  // 3. Locate BANCOS Sheet
  const bancosSheetName = sheetNames.find(
    (s) =>
      s.toUpperCase().includes("BANCO") ||
      s.toUpperCase().includes("PASSIVO") ||
      s.toUpperCase().includes("EMPRESTIMO") ||
      s.toUpperCase().includes("DIVIDA")
  );

  let bancos: BankLiability[] = [];
  if (bancosSheetName) {
    const bancosRawRows: any[] = sheetToSmartJson(workbook.Sheets[bancosSheetName]);
    bancos = bancosRawRows.map((row, idx) => {
      const getBancosField = (keys: string[]) => {
        for (const k of Object.keys(row)) {
          const cleanK = k.normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim().toUpperCase();
          if (keys.some((target) => cleanK.includes(target.toUpperCase()))) {
            return row[k];
          }
        }
        return "";
      };
      return {
        id: idx + 1,
        banco: cleanString(getBancosField(["BANCO", "INSTITUICAO", "CREDOR"]) || "Banco"),
        tipoOperacao: cleanString(getBancosField(["OPERACAO", "MODALIDADE", "TIPO"]) || "EMPRÉSTIMO"),
        contrato: cleanString(getBancosField(["CONTRATO", "NUMERO"]) || `CTR-${idx + 1}`),
        saldoDevedor: parseNumber(getBancosField(["SALDO", "DEVEDOR"])),
        valorParcela: parseNumber(getBancosField(["PARCELA", "MENSAL"])),
        parcelasRestantes: parseInt(cleanString(getBancosField(["RESTANTE", "QTD", "PRAZO"]) || "12"), 10) || 0,
        vencimentoDia: parseInt(cleanString(getBancosField(["VENCIMENTO", "DIA"]) || "20"), 10) || 10,
        taxaJuros: cleanString(getBancosField(["TAXA", "JUROS"]) || "CDI + spread"),
        status: cleanString(getBancosField(["STATUS", "SITUACAO"]) || "EM ABERTO").toUpperCase().includes("PAGO") ? "PAGO" : "EM ABERTO",
      };
    });
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
