import {
  BaseRecord,
  FinancialDrainItem,
  AbcSupplier,
  DuplicateAlert,
  ReclassificationAdjustment,
  ProvisionAlert,
} from "../types.ts";

export interface CashFlowDrainsResult {
  total: number;
  qtd: number;
  itens: FinancialDrainItem[];
  porTipo: { tipo: string; total: number; qtd: number }[];
}

export function calculateFinancialDrains(records: BaseRecord[]): CashFlowDrainsResult {
  const drainKeywords = [
    { termo: "TARIFA", tipo: "TARIFA" as const },
    { termo: "IOF", tipo: "IOF" as const },
    { termo: "JUROS", tipo: "JUROS" as const },
    { termo: "MULTA", tipo: "MULTA" as const },
    { termo: "CUSTAS", tipo: "CUSTAS" as const },
    { termo: "ENCARGOS", tipo: "JUROS" as const },
    { termo: "MORA", tipo: "JUROS" as const },
    { termo: "PROTESTO", tipo: "CUSTAS" as const },
  ];

  const itens: FinancialDrainItem[] = [];

  records.forEach((r) => {
    const textToSearch = `${r.lancamento} ${r.descricaoNatureza} ${r.grupo}`.toUpperCase();
    for (const d of drainKeywords) {
      if (textToSearch.includes(d.termo)) {
        itens.push({
          id: r.id,
          data: r.data,
          mes: r.mes,
          lancamento: r.lancamento,
          razaoSocial: r.razaoSocial,
          valor: r.valor,
          tipoDreno: d.tipo,
        });
        break;
      }
    }
  });

  const total = itens.reduce((acc, i) => acc + i.valor, 0);

  // Group by tipo
  const tipoMap = new Map<string, { total: number; qtd: number }>();
  itens.forEach((i) => {
    const prev = tipoMap.get(i.tipoDreno) || { total: 0, qtd: 0 };
    tipoMap.set(i.tipoDreno, { total: prev.total + i.valor, qtd: prev.qtd + 1 });
  });

  const porTipo = Array.from(tipoMap.entries()).map(([tipo, data]) => ({
    tipo,
    total: data.total,
    qtd: data.qtd,
  }));

  return {
    total,
    qtd: itens.length,
    itens,
    porTipo,
  };
}

export interface DailyCashFlowItem {
  data: string;
  dataFormatada: string;
  totalDia: number;
  qtdLancamentos: number;
  isPico: boolean;
  fornecedoresPrincipais: string;
}

export function calculateDailyCashFlow(records: BaseRecord[]): {
  dias: DailyCashFlowItem[];
  mediaDiaria: number;
  maiorPico: { data: string; valor: number };
} {
  const diaMap = new Map<string, { valor: number; qtd: number; fornecedores: string[] }>();

  records.forEach((r) => {
    const d = r.data || "Sem Data";
    const curr = diaMap.get(d) || { valor: 0, qtd: 0, fornecedores: [] };
    curr.valor += r.valor;
    curr.qtd += 1;
    if (r.razaoSocial && r.razaoSocial !== "NAN" && !curr.fornecedores.includes(r.razaoSocial)) {
      curr.fornecedores.push(r.razaoSocial);
    }
    diaMap.set(d, curr);
  });

  const rawDias = Array.from(diaMap.entries())
    .map(([data, d]) => ({
      data,
      totalDia: d.valor,
      qtdLancamentos: d.qtd,
      fornecedoresPrincipais: d.fornecedores.slice(0, 3).join(", "),
    }))
    .sort((a, b) => a.data.localeCompare(b.data));

  const totalGeral = rawDias.reduce((acc, d) => acc + d.totalDia, 0);
  const mediaDiaria = rawDias.length > 0 ? totalGeral / rawDias.length : 0;

  let maiorPico = { data: "", valor: 0 };

  const dias: DailyCashFlowItem[] = rawDias.map((d) => {
    if (d.totalDia > maiorPico.valor) {
      maiorPico = { data: d.data, valor: d.totalDia };
    }
    // format date DD/MM
    const parts = d.data.split("-");
    const dataFormatada = parts.length === 3 ? `${parts[2]}/${parts[1]}` : d.data;

    return {
      data: d.data,
      dataFormatada,
      totalDia: d.totalDia,
      qtdLancamentos: d.qtdLancamentos,
      isPico: d.totalDia > mediaDiaria * 1.5,
      fornecedoresPrincipais: d.fornecedoresPrincipais,
    };
  });

  return { dias, mediaDiaria, maiorPico };
}

export function calculateAbcCurve(records: BaseRecord[]): {
  fornecedores: AbcSupplier[];
  classeA: AbcSupplier[];
  classeB: AbcSupplier[];
  classeC: AbcSupplier[];
  totalGeral: number;
} {
  const map = new Map<string, { valorTotal: number; qtd: number }>();

  records.forEach((r) => {
    const nome = r.razaoSocial && r.razaoSocial !== "NAN" ? r.razaoSocial : "NÃO IDENTIFICADO / AVULSO";
    const curr = map.get(nome) || { valorTotal: 0, qtd: 0 };
    map.set(nome, { valorTotal: curr.valorTotal + r.valor, qtd: curr.qtd + 1 });
  });

  const totalGeral = records.reduce((acc, r) => acc + r.valor, 0);
  if (totalGeral === 0) {
    return { fornecedores: [], classeA: [], classeB: [], classeC: [], totalGeral: 0 };
  }

  // Sort descending
  const sorted = Array.from(map.entries())
    .map(([razaoSocial, d]) => ({
      razaoSocial,
      valorTotal: d.valorTotal,
      qtdLancamentos: d.qtd,
      percentual: (d.valorTotal / totalGeral) * 100,
      percentualAcumulado: 0,
      classe: "C" as "A" | "B" | "C",
    }))
    .sort((a, b) => b.valorTotal - a.valorTotal);

  let accPercent = 0;
  const fornecedores = sorted.map((s) => {
    accPercent += s.percentual;
    let classe: "A" | "B" | "C" = "C";
    if (accPercent <= 80 || s.percentual >= 10) {
      classe = "A";
    } else if (accPercent <= 95) {
      classe = "B";
    } else {
      classe = "C";
    }
    return {
      ...s,
      percentualAcumulado: Math.min(100, accPercent),
      classe,
    };
  });

  const classeA = fornecedores.filter((f) => f.classe === "A");
  const classeB = fornecedores.filter((f) => f.classe === "B");
  const classeC = fornecedores.filter((f) => f.classe === "C");

  return { fornecedores, classeA, classeB, classeC, totalGeral };
}

export function detectDuplicatesAndAnomalies(records: BaseRecord[]): DuplicateAlert[] {
  const map = new Map<string, BaseRecord[]>();

  records.forEach((r) => {
    if (r.valor > 0) {
      const key = `${r.mes}|${r.razaoSocial}|${r.valor.toFixed(2)}`;
      const list = map.get(key) || [];
      list.push(r);
      map.set(key, list);
    }
  });

  const duplicates: DuplicateAlert[] = [];

  map.forEach((list, key) => {
    if (list.length > 1) {
      const [mes, razaoSocial, valorStr] = key.split("|");
      duplicates.push({
        mes,
        razaoSocial,
        valor: parseFloat(valorStr),
        qtd: list.length,
        registros: list,
      });
    }
  });

  return duplicates.sort((a, b) => b.valor * b.qtd - a.valor * a.qtd);
}

export function calculateTrashAccounts(records: BaseRecord[]): {
  total: number;
  qtd: number;
  itens: BaseRecord[];
  gruposIdentificados: string[];
} {
  const trashKeywords = [
    "OUTROS",
    "OUTRAS DESPESAS",
    "DIVERSOS",
    "DESPESAS DIVERSAS",
    "NÃO OPERACIONAIS",
    "NAO OPERACIONAIS",
    "NÃO CLASSIFICADO",
    "INDEFINIDO",
    "GERAL",
  ];

  const itens = records.filter((r) => {
    const g = (r.grupo || "").toUpperCase();
    return trashKeywords.some((kw) => g === kw || g.includes(kw));
  });

  const total = itens.reduce((acc, i) => acc + i.valor, 0);
  const gruposIdentificados = Array.from(new Set(itens.map((i) => i.grupo)));

  return {
    total,
    qtd: itens.length,
    itens,
    gruposIdentificados,
  };
}

export function calculateMissingRegistration(records: BaseRecord[]): {
  total: number;
  qtd: number;
  itens: BaseRecord[];
} {
  const itens = records.filter((r) => {
    const semCnpj = !r.cpfCnpj || r.cpfCnpj.trim() === "" || r.cpfCnpj.trim() === "0" || r.cpfCnpj === "-";
    const semRazao =
      !r.razaoSocial ||
      r.razaoSocial.toUpperCase() === "NAN" ||
      r.razaoSocial.toUpperCase() === "NULL" ||
      r.razaoSocial.trim() === "";
    return semCnpj || semRazao;
  });

  const total = itens.reduce((acc, i) => acc + i.valor, 0);

  return { total, qtd: itens.length, itens };
}

export const RECLASSIFICATION_RULES: {
  palavras: string[];
  grupoSugerido: string;
  motivo: string;
}[] = [
  {
    palavras: ["MANUTENÇÃO", "MANUTENCAO", "ELEVADOR", "PREVENTIVA", "AR CONDICIONADO", "GERADOR", "CONSERTO", "HIDRÁULICA", "HIDRAULICA"],
    grupoSugerido: "DESPESAS COM MANUTENÇÃO",
    motivo: "Termos operacionais de conserto e manutenção predial/equipamento.",
  },
  {
    palavras: ["VEÍCULO", "VEICULO", "FROTA", "COMBUSTÍVEL", "COMBUSTIVEL", "GASOLINA", "DIESEL", "PEDÁGIO", "PEDAGIO", "ESTACIONAMENTO", "PNEU", "TROCA DE ÓLEO"],
    grupoSugerido: "FROTA & TRANSPORTE",
    motivo: "Despesas diretas vinculadas a automóveis e logística de frota.",
  },
  {
    palavras: ["SOFTWARE", "LICENÇA", "LICENCA", "SISTEMA", "CLOUD", "AWS", "AZURE", "TOTVS", "SAP", "DOMÍNIO", "HOSTING", "INTERNET", "LINK DEDICADO"],
    grupoSugerido: "T.I. E SOFTWARE",
    motivo: "Sistemas corporativos, computação em nuvem e conectividade.",
  },
  {
    palavras: ["ALUGUEL", "CONDOMÍNIO", "CONDOMINIO", "IPTU", "SEDE", "LOCAÇÃO SALA", "GALPÃO"],
    grupoSugerido: "DESPESAS IMOBILIÁRIAS",
    motivo: "Ocupação física, locação e encargos patrimoniais de imóveis.",
  },
  {
    palavras: ["FGTS", "INSS", "GPS", "DARF PREVIDENCIÁRIO", "CONTRIBUIÇÃO PATRONAL", "FÉRIAS", "13º SALÁRIO"],
    grupoSugerido: "ENCARGOS SOCIAIS",
    motivo: "Obrigações trabalhistas e previdenciárias legais.",
  },
  {
    palavras: ["VALE REFEIÇÃO", "VALE ALIMENTAÇÃO", "PLANO DE SAÚDE", "CONVÊNIO MÉDICO", "VALE TRANSPORTE", "SEGURO DE VIDA"],
    grupoSugerido: "BENEFÍCIOS",
    motivo: "Pacote corporativo de benefícios ao colaborador.",
  },
  {
    palavras: ["FRETE", "TRANSPORTE DE CARGAS", "LOGÍSTICA", "EXPEDIÇÃO", "MOTOBOY", "CORREIOS"],
    grupoSugerido: "LOGÍSTICA E FRETES",
    motivo: "Despesas de movimentação e entrega de mercadorias.",
  },
  {
    palavras: ["CONTABILIDADE", "HONORÁRIOS ADVOCATÍCIOS", "CONSULTORIA", "AUDITORIA EXTERNA", "JURÍDICO"],
    grupoSugerido: "SERVIÇOS PROFISSIONAIS",
    motivo: "Honorários técnicos especializados de terceiros.",
  },
  {
    palavras: ["TARIFA BANCÁRIA", "IOF", "JUROS DE MORA", "MULTA POR ATRASO", "TAXA DE COBRANÇA"],
    grupoSugerido: "DESPESAS FINANCEIRAS",
    motivo: "Custos estritamente financeiros e bancários.",
  },
];

export function auditNatureInconsistencies(records: BaseRecord[]): {
  ajustes: ReclassificationAdjustment[];
  totalValor: number;
  totalQtd: number;
} {
  const ajustes: ReclassificationAdjustment[] = [];

  records.forEach((row) => {
    const textoCompleto = `${row.lancamento} ${row.descricaoNatureza}`.toUpperCase();
    const grupoAtual = (row.grupo || "").toUpperCase();

    for (const regra of RECLASSIFICATION_RULES) {
      for (const palavra of regra.palavras) {
        if (textoCompleto.includes(palavra)) {
          // Check if current group does NOT contain the suggested group keywords
          const grupoSugeridoNorm = regra.grupoSugerido.toUpperCase();
          const matchesCurrent =
            grupoAtual.includes(grupoSugeridoNorm) ||
            (grupoSugeridoNorm.includes("T.I.") && (grupoAtual.includes("T.I") || grupoAtual.includes("TI"))) ||
            (grupoSugeridoNorm.includes("FROTA") && (grupoAtual.includes("FROTA") || grupoAtual.includes("VEICULO")));

          if (!matchesCurrent) {
            ajustes.push({
              idLinha: row.id,
              lancamento: row.lancamento,
              razaoSocial: row.razaoSocial,
              valor: row.valor,
              grupoAtual: row.grupo,
              grupoSugerido: regra.grupoSugerido,
              motivo: regra.motivo,
              palavraChave: palavra,
              statusAprovacao: "PENDENTE",
            });
            return; // Move to next record once matched
          }
        }
      }
    }
  });

  const totalValor = ajustes.reduce((acc, a) => acc + a.valor, 0);

  return {
    ajustes,
    totalValor,
    totalQtd: ajustes.length,
  };
}

export function runPredictiveProvisioning(
  allRecords: BaseRecord[],
  mesAnalise: string
): {
  recorrentesHistoricos: { razaoSocial: string; mesesDistintos: number; valorMedio: number; categoria: string }[];
  alertasFaltaProvisao: ProvisionAlert[];
  totalRiscoNaoProvisionado: number;
} {
  // 1. Map occurrences across distinct months
  const fornecedorMesesMap = new Map<string, { meses: Set<string>; valores: number[]; grupos: string[] }>();

  allRecords.forEach((r) => {
    const nome = r.razaoSocial;
    if (nome && nome !== "NAN" && nome.trim() !== "") {
      const curr = fornecedorMesesMap.get(nome) || {
        meses: new Set<string>(),
        valores: [],
        grupos: [],
      };
      curr.meses.add(r.mes);
      curr.valores.push(r.valor);
      if (r.grupo && !curr.grupos.includes(r.grupo)) {
        curr.grupos.push(r.grupo);
      }
      fornecedorMesesMap.set(nome, curr);
    }
  });

  // Eligible recurring: appears in at least 2 different months
  const recorrentesHistoricos: {
    razaoSocial: string;
    mesesDistintos: number;
    valorMedio: number;
    categoria: string;
  }[] = [];

  fornecedorMesesMap.forEach((data, razaoSocial) => {
    if (data.meses.size >= 2) {
      const valorMedio = data.valores.reduce((a, b) => a + b, 0) / data.valores.length;
      recorrentesHistoricos.push({
        razaoSocial,
        mesesDistintos: data.meses.size,
        valorMedio,
        categoria: data.grupos[0] || "Despesa Recorrente",
      });
    }
  });

  // 2. Check what's in the analyzed month
  const registrosMes = allRecords.filter((r) => r.mes === mesAnalise);
  const fornecedoresNoMes = new Set(registrosMes.map((r) => r.razaoSocial));

  const alertasFaltaProvisao: ProvisionAlert[] = [];

  recorrentesHistoricos.forEach((rec) => {
    const estaProvisionado = fornecedoresNoMes.has(rec.razaoSocial);
    if (!estaProvisionado) {
      alertasFaltaProvisao.push({
        razaoSocial: rec.razaoSocial,
        mesesRecorrentes: rec.mesesDistintos,
        valorMedioMensal: rec.valorMedio,
        ultimoMesPago: "Histórico consolidado",
        categoriaEstimada: rec.categoria,
        estaProvisionado: false,
      });
    }
  });

  const totalRiscoNaoProvisionado = alertasFaltaProvisao.reduce((acc, a) => acc + a.valorMedioMensal, 0);

  return {
    recorrentesHistoricos,
    alertasFaltaProvisao: alertasFaltaProvisao.sort((a, b) => b.valorMedioMensal - a.valorMedioMensal),
    totalRiscoNaoProvisionado,
  };
}
