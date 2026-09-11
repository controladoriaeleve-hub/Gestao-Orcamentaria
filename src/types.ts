export interface BaseRecord {
  id: number;
  status: "PAGO" | "EM ABERTO" | string;
  mes: string;
  data: string; // ISO or YYYY-MM-DD
  dataRaw?: string | number | Date;
  lancamento: string;
  razaoSocial: string;
  cpfCnpj: string;
  valor: number;
  codGrupo: string;
  grupo: string;
  codNatureza: string;
  descricaoNatureza: string;
  tipo: "FIXA" | "VARIÁVEL" | "FINANCEIRA" | "INVESTIMENTO" | string;
}

export interface BoardFixedExpense {
  categoria: string;
  descricao: string;
  metaMensal: number;
  realizadoMedio?: number;
  observacao?: string;
}

export interface BankLiability {
  id: number;
  banco: string;
  tipoOperacao: "EMPRÉSTIMO" | "CONSÓRCIO" | "FINANCIAMENTO" | "TARIFA / TAXA" | string;
  contrato: string;
  saldoDevedor: number;
  valorParcela: number;
  parcelasRestantes: number;
  vencimentoDia: number;
  taxaJuros: string;
  status: "EM ABERTO" | "PAGO" | string;
}

export interface FinancialDrainItem {
  id: number;
  data: string;
  mes: string;
  lancamento: string;
  razaoSocial: string;
  valor: number;
  tipoDreno: "TARIFA" | "IOF" | "JUROS" | "MULTA" | "CUSTAS";
}

export interface ReclassificationAdjustment {
  idLinha: number;
  lancamento: string;
  razaoSocial: string;
  valor: number;
  grupoAtual: string;
  grupoSugerido: string;
  motivo: string;
  palavraChave: string;
  statusAprovacao?: "PENDENTE" | "APROVADO" | "DESCARTADO";
}

export interface ProvisionAlert {
  razaoSocial: string;
  mesesRecorrentes: number;
  valorMedioMensal: number;
  ultimoMesPago: string;
  categoriaEstimada: string;
  estaProvisionado: boolean;
  diasAtrasoEstimado?: number;
}

export interface AbcSupplier {
  razaoSocial: string;
  valorTotal: number;
  qtdLancamentos: number;
  percentual: number;
  percentualAcumulado: number;
  classe: "A" | "B" | "C";
}

export interface DuplicateAlert {
  razaoSocial: string;
  mes: string;
  valor: number;
  qtd: number;
  registros: BaseRecord[];
}

export interface GlobalFilters {
  mes: string;
  status: string;
  grupo: string;
  fornecedor: string;
  buscaGeral: string;
}
