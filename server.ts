import express, { Request, Response } from "express";
import path from "path";
import dotenv from "dotenv";
import { GoogleGenAI } from "@google/genai";
import { createServer as createViteServer } from "vite";

dotenv.config();

const app = express();
const PORT = 3000;

app.use(express.json({ limit: "50mb" }));
app.use(express.urlencoded({ extended: true, limit: "50mb" }));

// Server-side Gemini Client
function getGeminiClient(): GoogleGenAI | null {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) {
    return null;
  }
  return new GoogleGenAI({
    apiKey,
    httpOptions: {
      headers: {
        "User-Agent": "aistudio-build",
      },
    },
  });
}

// Health check
app.get("/api/health", (_req: Request, res: Response) => {
  res.json({
    status: "ok",
    hasGeminiKey: Boolean(process.env.GEMINI_API_KEY),
    timestamp: new Date().toISOString(),
  });
});

// Module 5: Executive Diagnosis & Audit via Gemini AI
app.post("/api/gemini/diagnostico", async (req: Request, res: Response) => {
  try {
    const ai = getGeminiClient();
    if (!ai) {
      return res.status(503).json({
        error: "GEMINI_API_KEY_MISSING",
        message:
          "Chave da API Gemini não configurada no servidor (.env / Secrets).",
      });
    }

    const {
      resumoGeral,
      drenosFinanceiros,
      contasLixeira,
      inconsistencias,
      semCadastro,
      alertasProvisao,
      curvaAbcTop,
      despesasFixasVsRealizado,
      contextoExtra,
    } = req.body;

    const prompt = `
Você é um CFO (Chief Financial Officer) e Controller Sênior especialista em Finanças Corporativas brasileiras, normas CPC/IFRS, Auditoria de Balancete e Otimização de Capital de Giro.

Analise o relatório consolidado gerado a partir do extrato financeiro da empresa ('0. EXTRATO GERAL.xlsx') e elabore um PARECER EXECUTIVO E RELATÓRIO DE AUDITORIA DE CONTROLADORIA de alto nível para a Diretoria e Conselho de Administração.

--- DADOS DA AUDITORIA E CONTROLADORIA ---
1. RESUMO GERAL:
   - Volume Total Analisado: R$ ${Number(resumoGeral?.totalVolume || 0).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
   - Quantidade de Lançamentos: ${resumoGeral?.qtdLancamentos || 0}
   - Período / Meses: ${resumoGeral?.meses || "Diversos"}
   - Status: R$ ${Number(resumoGeral?.totalPago || 0).toLocaleString("pt-BR", { minimumFractionDigits: 2 })} Pagos vs R$ ${Number(resumoGeral?.totalAberto || 0).toLocaleString("pt-BR", { minimumFractionDigits: 2 })} Em Aberto

2. DRENOS FINANCEIROS (Tarifas, IOF, Juros, Custas):
   - Total Gasto em Drenos: R$ ${Number(drenosFinanceiros?.total || 0).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
   - Principais Itens de Dreno: ${JSON.stringify(drenosFinanceiros?.itensPrincipais || [])}

3. AUDITORIA CONTÁBIL - CONTAS "LIXEIRA" / GENÉRICAS (Ex: Outros, Diversos, Não Operacionais):
   - Total Alocado em Contas Genéricas: R$ ${Number(contasLixeira?.total || 0).toLocaleString("pt-BR", { minimumFractionDigits: 2 })} (${contasLixeira?.qtd || 0} lançamentos)
   - Amostras de Lançamentos Críticos: ${JSON.stringify(contasLixeira?.amostras || [])}

4. AUDITORIA CONTÁBIL - INCONSISTÊNCIAS DE NATUREZA (Descrição x Grupo Contábil):
   - Total de Inconsistências Detectadas: ${inconsistencias?.totalQtd || 0} itens
   - Valor Total Envolvido: R$ ${Number(inconsistencias?.totalValor || 0).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
   - Principais desvios encontrados: ${JSON.stringify(inconsistencias?.principaisDesvios || [])}

5. CADASTRO & COMPLIANCE FISCAL (Lançamentos sem CNPJ/CPF ou sem Razão Social):
   - Total sem Fornecedor/CNPJ identificado: R$ ${Number(semCadastro?.total || 0).toLocaleString("pt-BR", { minimumFractionDigits: 2 })} (${semCadastro?.qtd || 0} lançamentos)

6. MOTOR DE PROVISIONAMENTO PREDITIVO:
   - Fornecedores/Despesas Recorrentes Históricas não provisionadas no mês em aberto: ${alertasProvisao?.length || 0} itens
   - Lista de Fornecedores em Risco de Falta de Provisão: ${JSON.stringify(alertasProvisao || [])}

7. CURVA ABC DE FORNECEDORES (Concentração de Credores):
   - Top 5 Fornecedores (Maiores Credores): ${JSON.stringify(curvaAbcTop || [])}

8. DESPESAS FIXAS vs METAS DO BOARD:
   - Desvio Realizado vs Meta Fixa: ${JSON.stringify(despesasFixasVsRealizado || "Sem meta cadastrada")}

${contextoExtra ? `Contexto adicional solicitado pelo usuário: ${contextoExtra}` : ""}

--- INSTRUÇÕES DE FORMATAÇÃO DA RESPOSTA ---
Estruture sua resposta de forma executiva, clara, elegante e diretamente acionável em Markdown:

### 1. 📌 Parecer Executivo & Diagnóstico de Riscos (CFO View)
- Avaliação crítica da saúde do fluxo de caixa e nível de maturidade da controladoria.
- Alertas de risco de liquidez (descascamento diário, picos de vencimento e passivos bancários).

### 2. 🔍 Auditoria Contábil & Matriz de Reclassificação
- Diagnóstico sobre o impacto fiscal/gerencial das contas "Lixeira" e lançamentos sem CNPJ (risco de glosa de despesas pelo Fisco, DRE distorcida).
- Recomendações práticas e imediatas para reclassificação das naturezas de gastos apontadas.

### 3. 💸 Plano de Ação para Otimização de Caixa & Redução de Drenos
- Estratégia de corte ou renegociação de tarifas bancárias, IOF e juros moratórios.
- Ações para negociação na Curva ABC com os maiores credores (alongamento de prazo ou descontos à vista).

### 4. 🔮 Mitigação de Riscos de Provisionamento
- Providências para os credores recorrentes não provisionados no contas a pagar do mês corrente.

### 5. 🏛️ Recomendações de Governança e Políticas Internas
- Regras de aprovação (Alçadas), política de cadastro prévio obrigatório de CNPJ antes de pagar PIX/boletos, e bloqueio de contas genéricas no ERP.
`;

    const response = await ai.models.generateContent({
      model: "gemini-3.8-flash",
      contents: prompt,
      config: {
        systemInstruction:
          "Você é um Chief Financial Officer (CFO) e Auditor Contábil sênior. Forneça análises técnicas, contábeis e estratégicas profundas, com linguagem corporativa impecável e orientada a resultados.",
        temperature: 0.3,
      },
    });

    const textoParecer = response.text || "Parecer gerado com sucesso.";

    return res.json({
      success: true,
      parecer: textoParecer,
      timestamp: new Date().toISOString(),
    });
  } catch (err: any) {
    console.error("Erro no diagnóstico Gemini:", err);
    return res.status(500).json({
      error: "GEMINI_ERROR",
      message: err?.message || "Falha ao gerar diagnóstico com o Gemini.",
    });
  }
});

// Vite Middleware for dev / Static file serving for prod
async function start() {
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (_req: Request, res: Response) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Controladoria App rodando em http://localhost:${PORT}`);
  });
}

start();
