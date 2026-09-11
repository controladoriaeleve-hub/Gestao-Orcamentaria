import os
import io
import re
from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

# Carregar variáveis de ambiente se existirem (.env)
load_dotenv()

# Configuração da Página do Streamlit
st.set_page_config(
    page_title="Controladoria & Auditoria Financeira",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------------------
# ESTILOS E FORMATAÇÃO CSS
# --------------------------------------------------------------------------------------
st.markdown("""
<style>
    .main-title {
        font-size: 26px;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 2px;
    }
    .sub-title {
        font-size: 13px;
        color: #64748b;
        margin-bottom: 18px;
    }
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 14px 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .metric-title {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        color: #64748b;
    }
    .metric-value {
        font-size: 20px;
        font-weight: 800;
        color: #0f172a;
        margin-top: 4px;
    }
    .badge-pill {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 9999px;
        font-size: 10px;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------------------------------------------
# DADOS DE EXEMPLO (FALLBACK CASO NÃO FAÇA UPLOAD)
# --------------------------------------------------------------------------------------
@st.cache_data
def get_mock_datasets():
    # 1. BASE
    base_data = [
        # JAN/2026
        {"Status": "PAGO", "Mês": "JAN/2026", "Data": "2026-01-05", "Lançamento": "FOLHA PJ - DESENVOLVIMENTO DE SOFTWARE", "Razão Social": "TECH SOLUCOES DIGITAIS LTDA", "CPF/CNPJ": "12.345.678/0001-90", "Valor (R$)": 28500.0, "Cód Grupo": "GRP-01", "Grupo": "PESSOAL / TERCEIROS", "Cód. Natureza": "NAT-101", "Descrição Natureza": "Serviços de T.I. Terceirizados", "TIPO": "FIXA"},
        {"Status": "PAGO", "Mês": "JAN/2026", "Data": "2026-01-05", "Lançamento": "ALUGUEL SEDE OPERACIONAL SP", "Razão Social": "IMOBILIARIA METROPOLITANA S/A", "CPF/CNPJ": "04.987.654/0001-12", "Valor (R$)": 18500.0, "Cód Grupo": "GRP-02", "Grupo": "DESPESAS IMOBILIÁRIAS", "Cód. Natureza": "NAT-102", "Descrição Natureza": "Aluguel Predial", "TIPO": "FIXA"},
        {"Status": "PAGO", "Mês": "JAN/2026", "Data": "2026-01-07", "Lançamento": "FGTS COMPETÊNCIA DEZEMBRO", "Razão Social": "CAIXA ECONOMICA FEDERAL", "CPF/CNPJ": "00.360.305/0001-04", "Valor (R$)": 14200.0, "Cód Grupo": "GRP-03", "Grupo": "ENCARGOS SOCIAIS", "Cód. Natureza": "NAT-103", "Descrição Natureza": "Encargos Trabalhistas", "TIPO": "FIXA"},
        {"Status": "PAGO", "Mês": "JAN/2026", "Data": "2026-01-10", "Lançamento": "LICENCIAMENTO ERP MENSAL", "Razão Social": "TOTVS S/A", "CPF/CNPJ": "53.113.791/0001-22", "Valor (R$)": 9800.0, "Cód Grupo": "GRP-04", "Grupo": "T.I. E SOFTWARE", "Cód. Natureza": "NAT-104", "Descrição Natureza": "Sistemas de Gestão ERP", "TIPO": "FIXA"},
        {"Status": "PAGO", "Mês": "JAN/2026", "Data": "2026-01-10", "Lançamento": "CONTRATO MANUTENÇÃO PREVENTIVA ELEVADORES", "Razão Social": "ELEVADORES ATLAS SCHINDLER", "CPF/CNPJ": "60.422.382/0001-44", "Valor (R$)": 3200.0, "Cód Grupo": "GRP-05", "Grupo": "OUTROS", "Cód. Natureza": "NAT-999", "Descrição Natureza": "Despesas Diversas", "TIPO": "FIXA"},
        {"Status": "PAGO", "Mês": "JAN/2026", "Data": "2026-01-12", "Lançamento": "TARIFA BANCÁRIA MANUTENÇÃO CONTA CORRENTE", "Razão Social": "BANCO BRADESCO S/A", "CPF/CNPJ": "60.746.948/0001-12", "Valor (R$)": 185.0, "Cód Grupo": "GRP-06", "Grupo": "DESPESAS FINANCEIRAS", "Cód. Natureza": "NAT-106", "Descrição Natureza": "Tarifas de Serviços Bancários", "TIPO": "VARIÁVEL"},
        {"Status": "PAGO", "Mês": "JAN/2026", "Data": "2026-01-15", "Lançamento": "VALE ALIMENTAÇÃO E REFEIÇÃO EQUIPE", "Razão Social": "ALELO S/A BENEFICIOS", "CPF/CNPJ": "04.740.876/0001-25", "Valor (R$)": 11400.0, "Cód Grupo": "GRP-07", "Grupo": "BENEFÍCIOS", "Cód. Natureza": "NAT-107", "Descrição Natureza": "Alimentação Colaboradores", "TIPO": "FIXA"},
        {"Status": "PAGO", "Mês": "JAN/2026", "Data": "2026-01-18", "Lançamento": "PARCELA 14/24 FINANCIAMENTO FROTA", "Razão Social": "BANCO ITAU UNIBANCO S/A", "CPF/CNPJ": "60.701.190/0001-04", "Valor (R$)": 5200.0, "Cód Grupo": "GRP-08", "Grupo": "BANCOS / FINANCIAMENTOS", "Cód. Natureza": "NAT-108", "Descrição Natureza": "Amortização de Financiamento", "TIPO": "FIXA"},
        {"Status": "PAGO", "Mês": "JAN/2026", "Data": "2026-01-20", "Lançamento": "COMBUSTIVEL FROTA COMERCIAL", "Razão Social": "POSTO IPIRANGA CENTRAL", "CPF/CNPJ": "11.222.333/0001-44", "Valor (R$)": 4150.0, "Cód Grupo": "GRP-05", "Grupo": "OUTROS", "Cód. Natureza": "NAT-999", "Descrição Natureza": "Despesas Gerais", "TIPO": "VARIÁVEL"},
        {"Status": "PAGO", "Mês": "JAN/2026", "Data": "2026-01-22", "Lançamento": "JUROS DE MORA POR ATRASO FORNECEDOR", "Razão Social": "DISTRIBUIDORA DE EMBALAGENS LTDA", "CPF/CNPJ": "33.444.555/0001-88", "Valor (R$)": 640.0, "Cód Grupo": "GRP-06", "Grupo": "DESPESAS FINANCEIRAS", "Cód. Natureza": "NAT-109", "Descrição Natureza": "Juros e Multas Pagos", "TIPO": "VARIÁVEL"},
        {"Status": "PAGO", "Mês": "JAN/2026", "Data": "2026-01-25", "Lançamento": "PARCELA EMPRÉSTIMO CAPITAL DE GIRO", "Razão Social": "BANCO BRADESCO S/A", "CPF/CNPJ": "60.746.948/0001-12", "Valor (R$)": 15400.0, "Cód Grupo": "GRP-08", "Grupo": "BANCOS / FINANCIAMENTOS", "Cód. Natureza": "NAT-110", "Descrição Natureza": "Empréstimo Bancário", "TIPO": "FIXA"},
        {"Status": "PAGO", "Mês": "JAN/2026", "Data": "2026-01-26", "Lançamento": "PAGAMENTO PIX SEM COMPROVANTE CADASTRO", "Razão Social": "NAN", "CPF/CNPJ": "", "Valor (R$)": 3800.0, "Cód Grupo": "GRP-05", "Grupo": "OUTRAS DESPESAS", "Cód. Natureza": "NAT-999", "Descrição Natureza": "Despesas Diversas", "TIPO": "VARIÁVEL"},
        {"Status": "PAGO", "Mês": "JAN/2026", "Data": "2026-01-28", "Lançamento": "IOF RETENÇÃO OPERAÇÃO CRÉDITO", "Razão Social": "RECEITA FEDERAL DO BRASIL", "CPF/CNPJ": "00.394.460/0058-87", "Valor (R$)": 920.0, "Cód Grupo": "GRP-06", "Grupo": "DESPESAS FINANCEIRAS", "Cód. Natureza": "NAT-111", "Descrição Natureza": "Impostos Operações Financeiras", "TIPO": "VARIÁVEL"},
        {"Status": "PAGO", "Mês": "JAN/2026", "Data": "2026-01-30", "Lançamento": "PARCELA CONSÓRCIO IMOBILIÁRIO SEDE", "Razão Social": "BANCO SANTANDER BRASIL S/A", "CPF/CNPJ": "90.400.888/0001-42", "Valor (R$)": 8250.0, "Cód Grupo": "GRP-08", "Grupo": "BANCOS / FINANCIAMENTOS", "Cód. Natureza": "NAT-112", "Descrição Natureza": "Consórcio", "TIPO": "FIXA"},
        # FEV/2026
        {"Status": "PAGO", "Mês": "FEV/2026", "Data": "2026-02-05", "Lançamento": "FOLHA PJ - DESENVOLVIMENTO DE SOFTWARE", "Razão Social": "TECH SOLUCOES DIGITAIS LTDA", "CPF/CNPJ": "12.345.678/0001-90", "Valor (R$)": 28500.0, "Cód Grupo": "GRP-01", "Grupo": "PESSOAL / TERCEIROS", "Cód. Natureza": "NAT-101", "Descrição Natureza": "Serviços de T.I. Terceirizados", "TIPO": "FIXA"},
        {"Status": "PAGO", "Mês": "FEV/2026", "Data": "2026-02-05", "Lançamento": "ALUGUEL SEDE OPERACIONAL SP", "Razão Social": "IMOBILIARIA METROPOLITANA S/A", "CPF/CNPJ": "04.987.654/0001-12", "Valor (R$)": 18500.0, "Cód Grupo": "GRP-02", "Grupo": "DESPESAS IMOBILIÁRIAS", "Cód. Natureza": "NAT-102", "Descrição Natureza": "Aluguel Predial", "TIPO": "FIXA"},
        {"Status": "PAGO", "Mês": "FEV/2026", "Data": "2026-02-07", "Lançamento": "FGTS COMPETÊNCIA JANEIRO", "Razão Social": "CAIXA ECONOMICA FEDERAL", "CPF/CNPJ": "00.360.305/0001-04", "Valor (R$)": 14650.0, "Cód Grupo": "GRP-03", "Grupo": "ENCARGOS SOCIAIS", "Cód. Natureza": "NAT-103", "Descrição Natureza": "Encargos Trabalhistas", "TIPO": "FIXA"},
        {"Status": "PAGO", "Mês": "FEV/2026", "Data": "2026-02-10", "Lançamento": "LICENCIAMENTO ERP MENSAL", "Razão Social": "TOTVS S/A", "CPF/CNPJ": "53.113.791/0001-22", "Valor (R$)": 9800.0, "Cód Grupo": "GRP-04", "Grupo": "T.I. E SOFTWARE", "Cód. Natureza": "NAT-104", "Descrição Natureza": "Sistemas de Gestão ERP", "TIPO": "FIXA"},
        {"Status": "PAGO", "Mês": "FEV/2026", "Data": "2026-02-10", "Lançamento": "CONSULTORIA CONTÁBIL E AUDITORIA", "Razão Social": "AUDITEX AUDITORES INDEPENDENTES", "CPF/CNPJ": "77.888.999/0001-11", "Valor (R$)": 7500.0, "Cód Grupo": "GRP-09", "Grupo": "SERVIÇOS PROFISSIONAIS", "Cód. Natureza": "NAT-113", "Descrição Natureza": "Honorários Contábeis", "TIPO": "FIXA"},
        {"Status": "PAGO", "Mês": "FEV/2026", "Data": "2026-02-12", "Lançamento": "MANUTENÇÃO CORRETIVA SISTEMA DE AR CONDICIONADO", "Razão Social": "CLIMAFRIO REFRIGERACAO LTDA", "CPF/CNPJ": "88.999.000/0001-22", "Valor (R$)": 4850.0, "Cód Grupo": "GRP-05", "Grupo": "DIVERSOS", "Cód. Natureza": "NAT-999", "Descrição Natureza": "Despesas Gerais", "TIPO": "VARIÁVEL"},
        {"Status": "PAGO", "Mês": "FEV/2026", "Data": "2026-02-15", "Lançamento": "VALE ALIMENTAÇÃO E REFEIÇÃO EQUIPE", "Razão Social": "ALELO S/A BENEFICIOS", "CPF/CNPJ": "04.740.876/0001-25", "Valor (R$)": 11400.0, "Cód Grupo": "GRP-07", "Grupo": "BENEFÍCIOS", "Cód. Natureza": "NAT-107", "Descrição Natureza": "Alimentação Colaboradores", "TIPO": "FIXA"},
        {"Status": "PAGO", "Mês": "FEV/2026", "Data": "2026-02-18", "Lançamento": "PARCELA 15/24 FINANCIAMENTO FROTA", "Razão Social": "BANCO ITAU UNIBANCO S/A", "CPF/CNPJ": "60.701.190/0001-04", "Valor (R$)": 5200.0, "Cód Grupo": "GRP-08", "Grupo": "BANCOS / FINANCIAMENTOS", "Cód. Natureza": "NAT-108", "Descrição Natureza": "Amortização de Financiamento", "TIPO": "FIXA"},
        {"Status": "PAGO", "Mês": "FEV/2026", "Data": "2026-02-20", "Lançamento": "FORNECIMENTO DE EMBALAGENS LOTE 01", "Razão Social": "DISTRIBUIDORA DE EMBALAGENS LTDA", "CPF/CNPJ": "33.444.555/0001-88", "Valor (R$)": 8450.0, "Cód Grupo": "GRP-10", "Grupo": "INSUMOS / PRODUÇÃO", "Cód. Natureza": "NAT-114", "Descrição Natureza": "Matéria Prima e Insumos", "TIPO": "VARIÁVEL"},
        {"Status": "PAGO", "Mês": "FEV/2026", "Data": "2026-02-20", "Lançamento": "FORNECIMENTO DE EMBALAGENS LOTE 01 (REPETIDO)", "Razão Social": "DISTRIBUIDORA DE EMBALAGENS LTDA", "CPF/CNPJ": "33.444.555/0001-88", "Valor (R$)": 8450.0, "Cód Grupo": "GRP-10", "Grupo": "INSUMOS / PRODUÇÃO", "Cód. Natureza": "NAT-114", "Descrição Natureza": "Matéria Prima e Insumos", "TIPO": "VARIÁVEL"},
        {"Status": "PAGO", "Mês": "FEV/2026", "Data": "2026-02-25", "Lançamento": "PARCELA EMPRÉSTIMO CAPITAL DE GIRO", "Razão Social": "BANCO BRADESCO S/A", "CPF/CNPJ": "60.746.948/0001-12", "Valor (R$)": 15400.0, "Cód Grupo": "GRP-08", "Grupo": "BANCOS / FINANCIAMENTOS", "Cód. Natureza": "NAT-110", "Descrição Natureza": "Empréstimo Bancário", "TIPO": "FIXA"},
        {"Status": "PAGO", "Mês": "FEV/2026", "Data": "2026-02-28", "Lançamento": "PARCELA CONSÓRCIO IMOBILIÁRIO SEDE", "Razão Social": "BANCO SANTANDER BRASIL S/A", "CPF/CNPJ": "90.400.888/0001-42", "Valor (R$)": 8250.0, "Cód Grupo": "GRP-08", "Grupo": "BANCOS / FINANCIAMENTOS", "Cód. Natureza": "NAT-112", "Descrição Natureza": "Consórcio", "TIPO": "FIXA"},
        # MAR/2026
        {"Status": "EM ABERTO", "Mês": "MAR/2026", "Data": "2026-03-05", "Lançamento": "FOLHA PJ - DESENVOLVIMENTO DE SOFTWARE", "Razão Social": "TECH SOLUCOES DIGITAIS LTDA", "CPF/CNPJ": "12.345.678/0001-90", "Valor (R$)": 28500.0, "Cód Grupo": "GRP-01", "Grupo": "PESSOAL / TERCEIROS", "Cód. Natureza": "NAT-101", "Descrição Natureza": "Serviços de T.I. Terceirizados", "TIPO": "FIXA"},
        {"Status": "EM ABERTO", "Mês": "MAR/2026", "Data": "2026-03-10", "Lançamento": "SERVIÇOS DE LIMPEZA E FACILITIES", "Razão Social": "LIMPEZA FACIL SERVICOS TERCEIRIZADOS", "CPF/CNPJ": "44.555.666/0001-77", "Valor (R$)": 6200.0, "Cód Grupo": "GRP-05", "Grupo": "NÃO OPERACIONAIS", "Cód. Natureza": "NAT-999", "Descrição Natureza": "Despesas Gerais", "TIPO": "FIXA"},
        {"Status": "EM ABERTO", "Mês": "MAR/2026", "Data": "2026-03-18", "Lançamento": "PARCELA 16/24 FINANCIAMENTO FROTA", "Razão Social": "BANCO ITAU UNIBANCO S/A", "CPF/CNPJ": "60.701.190/0001-04", "Valor (R$)": 5200.0, "Cód Grupo": "GRP-08", "Grupo": "BANCOS / FINANCIAMENTOS", "Cód. Natureza": "NAT-108", "Descrição Natureza": "Amortização de Financiamento", "TIPO": "FIXA"},
        {"Status": "EM ABERTO", "Mês": "MAR/2026", "Data": "2026-03-25", "Lançamento": "PARCELA EMPRÉSTIMO CAPITAL DE GIRO", "Razão Social": "BANCO BRADESCO S/A", "CPF/CNPJ": "60.746.948/0001-12", "Valor (R$)": 15400.0, "Cód Grupo": "GRP-08", "Grupo": "BANCOS / FINANCIAMENTOS", "Cód. Natureza": "NAT-110", "Descrição Natureza": "Empréstimo Bancário", "TIPO": "FIXA"},
    ]
    df_base = pd.DataFrame(base_data)

    # 2. DESPESA FIXA BOARD
    board_data = [
        {"Categoria": "PESSOAL / TERCEIROS", "Descrição": "Folha de Pagamento CLT, PJ e Honorários de Diretoria", "Meta Mensal (R$)": 35000.0, "Realizado Médio (R$)": 28500.0, "Observação": "Dentro do orçamento estabelecido pelo Board."},
        {"Categoria": "ENCARGOS SOCIAIS", "Descrição": "FGTS, INSS Patronal e Provisão de Férias/13º", "Meta Mensal (R$)": 16000.0, "Realizado Médio (R$)": 14425.0, "Observação": "Varia de acordo com horas extras e comissões."},
        {"Categoria": "BENEFÍCIOS", "Descrição": "Vale Refeição, Plano de Saúde Bradesco e Vale Transporte", "Meta Mensal (R$)": 12000.0, "Realizado Médio (R$)": 11400.0, "Observação": "Alinhado ao headcount atual."},
        {"Categoria": "DESPESAS IMOBILIÁRIAS", "Descrição": "Aluguel Predial, IPTU e Taxa Condominial Sede", "Meta Mensal (R$)": 19000.0, "Realizado Médio (R$)": 18500.0, "Observação": "Contrato reajustado pelo IPCA anualmente em Outubro."},
        {"Categoria": "T.I. E SOFTWARE", "Descrição": "Licenças de ERP (Totvs), Servidores AWS e Segurança", "Meta Mensal (R$)": 11000.0, "Realizado Médio (R$)": 9800.0, "Observação": "Meta prevê folga para novos acessos no ERP."},
        {"Categoria": "DESPESAS COM MANUTENÇÃO", "Descrição": "Manutenção Preventiva de Equipamentos, Ar e Elevadores", "Meta Mensal (R$)": 5000.0, "Realizado Médio (R$)": 5725.0, "Observação": "⚠️ Realizado acima da meta devido a falhas pontuais."},
    ]
    df_board = pd.DataFrame(board_data)

    # 3. BANCOS
    bancos_data = [
        {"Banco": "BANCO BRADESCO S/A", "Tipo de Operação": "EMPRÉSTIMO", "Contrato": "CTR-GIRO-2024-8891", "Saldo Devedor (R$)": 354200.0, "Valor Parcela (R$)": 15400.0, "Parcelas Restantes": 23, "Dia Vencimento": 25, "Taxa de Juros": "1.45% a.m. (CDI + 2.8% a.a.)", "Status": "EM ABERTO"},
        {"Banco": "BANCO SANTANDER BRASIL S/A", "Tipo de Operação": "CONSÓRCIO", "Contrato": "CONSORCIO-IMO-092", "Saldo Devedor (R$)": 980000.0, "Valor Parcela (R$)": 8250.0, "Parcelas Restantes": 142, "Dia Vencimento": 30, "Taxa de Juros": "Taxa de Adm. 0.18% a.m.", "Status": "EM ABERTO"},
        {"Banco": "BANCO ITAU UNIBANCO S/A", "Tipo de Operação": "FINANCIAMENTO", "Contrato": "FIN-FROTA-2023-412", "Saldo Devedor (R$)": 62400.0, "Valor Parcela (R$)": 5200.0, "Parcelas Restantes": 12, "Dia Vencimento": 18, "Taxa de Juros": "1.20% a.m. pré-fixada", "Status": "EM ABERTO"},
        {"Banco": "BANCO SAFRA S/A", "Tipo de Operação": "EMPRÉSTIMO", "Contrato": "GIRO-EXP-2022-110", "Saldo Devedor (R$)": 0.0, "Valor Parcela (R$)": 0.0, "Parcelas Restantes": 0, "Dia Vencimento": 10, "Taxa de Juros": "Quitado em Dez/2025", "Status": "PAGO"},
    ]
    df_bancos = pd.DataFrame(bancos_data)

    return df_base, df_board, df_bancos


# --------------------------------------------------------------------------------------
# FUNÇÃO PARA LEITURA DE EXCEL (0. EXTRATO GERAL.xlsx)
# --------------------------------------------------------------------------------------
def load_excel_file(uploaded_file):
    try:
        excel_file = pd.ExcelFile(uploaded_file)
        sheet_names = [s.strip().upper() for s in excel_file.sheet_names]

        # 1. BASE
        base_sheet = None
        for s in excel_file.sheet_names:
            if "BASE" in s.upper() or "EXTRATO" in s.upper():
                base_sheet = s
                break
        if not base_sheet:
            base_sheet = excel_file.sheet_names[0]
        df_base = pd.read_excel(excel_file, sheet_name=base_sheet)

        # 2. DESPESA FIXA BOARD
        df_board = pd.DataFrame()
        for s in excel_file.sheet_names:
            if "BOARD" in s.upper() or "FIXA" in s.upper():
                df_board = pd.read_excel(excel_file, sheet_name=s)
                break

        # 3. BANCOS
        df_bancos = pd.DataFrame()
        for s in excel_file.sheet_names:
            if "BANCO" in s.upper() or "PASSIVO" in s.upper():
                df_bancos = pd.read_excel(excel_file, sheet_name=s)
                break

        # Normalizações em df_base
        col_map = {c: c.strip().upper() for c in df_base.columns}
        df_base.rename(columns=col_map, inplace=True)

        return df_base, df_board, df_bancos, True, None
    except Exception as e:
        return None, None, None, False, str(e)


# --------------------------------------------------------------------------------------
# REGRAS SEMÂNTICAS DE RECLASSIFICAÇÃO
# --------------------------------------------------------------------------------------
RECLASSIFICATION_RULES = [
    {
        "palavras": ["MANUTENÇÃO", "MANUTENCAO", "ELEVADOR", "PREVENTIVA", "AR CONDICIONADO", "CONSERTO", "HIDRÁULICA"],
        "grupo_sugerido": "DESPESAS COM MANUTENÇÃO",
        "motivo": "Termos operacionais de reparo e manutenção física/predial.",
    },
    {
        "palavras": ["VEÍCULO", "VEICULO", "FROTA", "COMBUSTÍVEL", "COMBUSTIVEL", "GASOLINA", "DIESEL", "PEDÁGIO", "ESTACIONAMENTO"],
        "grupo_sugerido": "FROTA & TRANSPORTE",
        "motivo": "Despesas operacionais de automóveis e deslocamento de frota.",
    },
    {
        "palavras": ["SOFTWARE", "LICENÇA", "LICENCA", "SISTEMA", "CLOUD", "AWS", "AZURE", "TOTVS", "SAP", "INTERNET"],
        "grupo_sugerido": "T.I. E SOFTWARE",
        "motivo": "Sistemas de informação, infraestrutura cloud e licenças.",
    },
    {
        "palavras": ["ALUGUEL", "CONDOMÍNIO", "CONDOMINIO", "IPTU", "SEDE", "LOCAÇÃO"],
        "grupo_sugerido": "DESPESAS IMOBILIÁRIAS",
        "motivo": "Ocupação predial e taxas patrimoniais.",
    },
    {
        "palavras": ["FGTS", "INSS", "GPS", "DARF PREVIDENCIÁRIO", "CONTRIBUIÇÃO SOCIAL", "FÉRIAS"],
        "grupo_sugerido": "ENCARGOS SOCIAIS",
        "motivo": "Obrigações trabalhistas e previdenciárias de pessoal.",
    },
    {
        "palavras": ["VALE REFEIÇÃO", "VALE ALIMENTAÇÃO", "PLANO DE SAÚDE", "CONVÊNIO", "VALE TRANSPORTE"],
        "grupo_sugerido": "BENEFÍCIOS",
        "motivo": "Pacote corporativo de benefícios ao colaborador.",
    },
    {
        "palavras": ["TARIFA BANCÁRIA", "IOF", "JUROS DE MORA", "MULTA POR ATRASO", "CUSTAS"],
        "grupo_sugerido": "DESPESAS FINANCEIRAS",
        "motivo": "Encargos estritamente financeiros e bancários.",
    },
]


def audit_nature_inconsistencies(df):
    ajustes = []
    for idx, row in df.iterrows():
        texto = f"{str(row.get('LANÇAMENTO', ''))} {str(row.get('DESCRIÇÃO NATUREZA', ''))}".upper()
        grupo_atual = str(row.get('GRUPO', '')).upper()

        for regra in RECLASSIFICATION_RULES:
            for palavra in regra["palavras"]:
                if palavra in texto:
                    grupo_sugerido_norm = regra["grupo_sugerido"].upper()
                    if grupo_sugerido_norm not in grupo_atual:
                        ajustes.append({
                            "Linha": idx + 1,
                            "Lançamento": row.get("LANÇAMENTO", ""),
                            "Razão Social": row.get("RAZÃO SOCIAL", ""),
                            "Valor (R$)": row.get("VALOR (R$)", 0.0),
                            "Grupo Atual": row.get("GRUPO", ""),
                            "Grupo Sugerido": regra["grupo_sugerido"],
                            "Palavra-Chave": palavra,
                            "Motivo": regra["motivo"]
                        })
                        break
            else:
                continue
            break

    return pd.DataFrame(ajustes)


# --------------------------------------------------------------------------------------
# PROVISIONAMENTO PREDITIVO
# --------------------------------------------------------------------------------------
def calculate_predictive_provisioning(df, mes_analise):
    # Encontrar fornecedores que ocorrem em múltiplos meses
    fornecedor_meses = df.groupby('RAZÃO SOCIAL')['MÊS'].nunique()
    fornecedores_recorrentes = fornecedor_meses[fornecedor_meses >= 2].index.tolist()

    df_mes = df[df['MÊS'] == mes_analise]
    fornecedores_no_mes = set(df_mes['RAZÃO SOCIAL'].unique())

    alertas = []
    for f in fornecedores_recorrentes:
        if f not in fornecedores_no_mes and f not in ["NAN", "", "NÃO IDENTIFICADO"]:
            media_valor = df[df['RAZÃO SOCIAL'] == f]['VALOR (R$)'].mean()
            categoria = df[df['RAZÃO SOCIAL'] == f]['GRUPO'].iloc[0]
            alertas.append({
                "Razão Social": f,
                "Categoria Estimada": categoria,
                "Média Mensal Histórica (R$)": media_valor,
                "Status no Mês": "NÃO LOCALIZADO NO EXTRATO",
                "Ação Recomendada": f"Provisionar R$ {media_valor:,.2f} no fluxo de caixa operacional."
            })

    return pd.DataFrame(alertas)


# --------------------------------------------------------------------------------------
# SIDEBAR / CONTROLES DE ARQUIVO E FILTROS
# --------------------------------------------------------------------------------------
st.sidebar.markdown("### 📂 Fonte de Dados")
uploaded_file = st.sidebar.file_uploader(
    "Carregar '0. EXTRATO GERAL.xlsx' ou .csv",
    type=["xlsx", "xls", "csv"],
    help="Envie a planilha contendo as abas 'BASE', 'DESPESA FIXA BOARD' e 'BANCOS'."
)

if uploaded_file is not None:
    df_base, df_board, df_bancos, success, err = load_excel_file(uploaded_file)
    if not success:
        st.sidebar.error(f"Erro ao ler arquivo: {err}")
        df_base, df_board, df_bancos = get_mock_datasets()
        is_demo = True
    else:
        st.sidebar.success(f"Arquivo '{uploaded_file.name}' carregado!")
        is_demo = False
else:
    df_base, df_board, df_bancos = get_mock_datasets()
    is_demo = True
    st.sidebar.info("💡 Operando com dados de demonstração pré-configurados.")

# Normalização de colunas
if 'VALOR (R$)' not in df_base.columns:
    for c in df_base.columns:
        if 'VALOR' in c:
            df_base.rename(columns={c: 'VALOR (R$)'}, inplace=True)
            break

# Filtros Globais
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Filtros Globais")

# 1. Filtro Mês
meses_disponiveis = ["TODOS"] + sorted(list(df_base['MÊS'].dropna().unique()))
filtro_mes = st.sidebar.selectbox("Mês de Competência", meses_disponiveis)

# 2. Filtro Status
status_disponiveis = ["TODOS"] + sorted(list(df_base['STATUS'].dropna().unique()))
filtro_status = st.sidebar.selectbox("Status de Pagamento", status_disponiveis)

# 3. Filtro Grupo
grupos_disponiveis = ["TODOS"] + sorted(list(df_base['GRUPO'].dropna().unique()))
filtro_grupo = st.sidebar.selectbox("Grupo de Despesa", grupos_disponiveis)

# 4. Busca Textual
busca_geral = st.sidebar.text_input("Busca Rápida (Histórico / Credor)", "").strip().upper()

# Aplicação dos Filtros
df_filtrado = df_base.copy()
if filtro_mes != "TODOS":
    df_filtrado = df_filtrado[df_filtrado['MÊS'] == filtro_mes]
if filtro_status != "TODOS":
    df_filtrado = df_filtrado[df_filtrado['STATUS'] == filtro_status]
if filtro_grupo != "TODOS":
    df_filtrado = df_filtrado[df_filtrado['GRUPO'] == filtro_grupo]
if busca_geral:
    df_filtrado = df_filtrado[
        df_filtrado['LANÇAMENTO'].astype(str).str.upper().str.contains(busca_geral) |
        df_filtrado['RAZÃO SOCIAL'].astype(str).str.upper().str.contains(busca_geral) |
        df_filtrado['GRUPO'].astype(str).str.upper().str.contains(busca_geral)
    ]

# --------------------------------------------------------------------------------------
# CABEÇALHO PRINCIPAL
# --------------------------------------------------------------------------------------
st.markdown('<div class="main-title">💼 Controladoria & Auditoria Financeira</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Saneamento de naturezas de gastos, otimização de liquidez de caixa e auditoria de extrato</div>',
    unsafe_allow_html=True
)

# Banner de Métricas Rápidas
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
total_volume = df_filtrado['VALOR (R$)'].sum()
total_linhas = len(df_filtrado)
abertos_volume = df_filtrado[df_filtrado['STATUS'] == 'EM ABERTO']['VALOR (R$)'].sum()
passivo_bancos_total = df_bancos['Saldo Devedor (R$)'].sum() if not df_bancos.empty and 'Saldo Devedor (R$)' in df_bancos.columns else 0.0

with col_m1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Volume Analisado</div>
        <div class="metric-value">R$ {total_volume:,.2f}</div>
        <div style="font-size:11px; color:#64748b; margin-top:2px;">{total_linhas} lançamentos filtrados</div>
    </div>
    """, unsafe_allow_html=True)

with col_m2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Despesas em Aberto</div>
        <div class="metric-value" style="color:#d97706;">R$ {abertos_volume:,.2f}</div>
        <div style="font-size:11px; color:#d97706; margin-top:2px;">Aguardando liquidação</div>
    </div>
    """, unsafe_allow_html=True)

with col_m3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Passivos Bancários (Saldo)</div>
        <div class="metric-value" style="color:#dc2626;">R$ {passivo_bancos_total:,.2f}</div>
        <div style="font-size:11px; color:#dc2626; margin-top:2px;">Contratos na aba BANCOS</div>
    </div>
    """, unsafe_allow_html=True)

with col_m4:
    status_base_txt = "Base Demonstração (0. EXTRATO GERAL)" if is_demo else uploaded_file.name
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Status do Arquivo</div>
        <div class="metric-value" style="font-size:15px; color:#059669;">{'✅ Carregado' if not is_demo else '📌 Demo'}</div>
        <div style="font-size:11px; color:#64748b; margin-top:2px;">{status_base_txt[:28]}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --------------------------------------------------------------------------------------
# ABAS DO APLICATIVO
# --------------------------------------------------------------------------------------
tab_caixa, tab_despesas, tab_auditoria, tab_provisao, tab_ia, tab_extrato = st.tabs([
    "💧 1. Fluxo de Caixa",
    "📉 2. Redução de Despesas",
    "🛡️ 3. Auditoria de Naturezas",
    "⏰ 4. Provisionamento Preditivo",
    "🧠 5. Diagnóstico IA Gemini",
    "📋 Extrato Geral Completo"
])

# --------------------------------------------------------------------------------------
# TAB 1: FLUXO DE CAIXA
# --------------------------------------------------------------------------------------
with tab_caixa:
    st.markdown("### 💧 Oportunidades de Fluxo de Caixa & Gestão de Liquidez")

    subtab_drenos, subtab_descascamento, subtab_passivos = st.tabs([
        "Drenos Financeiros", "Descascamento Diário", "Passivos Bancários"
    ])

    with subtab_drenos:
        termos_drenos = ["TARIFA", "IOF", "JUROS", "MULTA", "CUSTAS", "ENCARGOS", "MORA"]
        pattern = "|".join(termos_drenos)
        df_drenos = df_filtrado[
            df_filtrado['LANÇAMENTO'].astype(str).str.upper().str.contains(pattern) |
            df_filtrado['GRUPO'].astype(str).str.upper().str.contains("FINANCEIRA")
        ].copy()

        total_drenos = df_drenos['VALOR (R$)'].sum()
        col_dr1, col_dr2 = st.columns([1, 2])

        with col_dr1:
            st.metric("Total de Drenos Financeiros", f"R$ {total_drenos:,.2f}", f"{len(df_drenos)} saídas")
            st.info("💡 Custos com tarifas de conta, IOF de crédito, juros de mora e encargos por atraso de títulos.")

        with col_dr2:
            if not df_drenos.empty:
                fig_drenos = px.pie(
                    df_drenos,
                    names='GRUPO',
                    values='VALOR (R$)',
                    title="Composição dos Drenos por Grupo",
                    hole=0.4,
                    color_discrete_sequence=px.colors.sequential.Reds_r
                )
                st.plotly_chart(fig_drenos, use_container_width=True)

        st.dataframe(
            df_drenos[['DATA', 'STATUS', 'LANÇAMENTO', 'RAZÃO SOCIAL', 'VALOR (R$)', 'GRUPO']],
            use_container_width=True
        )

    with subtab_descascamento:
        st.markdown("#### Distribuição Diária de Pagamentos (Prevenção de Picos de Saída)")
        df_daily = df_filtrado.groupby('DATA')['VALOR (R$)'].agg(['sum', 'count']).reset_index()
        df_daily.rename(columns={'sum': 'Total (R$)', 'count': 'Qtd Lançamentos'}, inplace=True)
        media_diaria = df_daily['Total (R$)'].mean() if not df_daily.empty else 0

        df_daily['Pico'] = df_daily['Total (R$)'] > (media_diaria * 1.5)

        fig_daily = go.Figure()
        fig_daily.add_trace(go.Bar(
            x=df_daily['DATA'],
            y=df_daily['Total (R$)'],
            name="Desembolso Diário",
            marker_color=['#ef4444' if p else '#059669' for p in df_daily['Pico']]
        ))
        fig_daily.add_hline(
            y=media_diaria,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Média Diária: R$ {media_diaria:,.2f}"
        )
        fig_daily.update_layout(
            title="Desembolsos Diários (Barras Vermelhas: Picos > 150% da Média)",
            xaxis_title="Data",
            yaxis_title="Total Desembolsado (R$)"
        )
        st.plotly_chart(fig_daily, use_container_width=True)

        st.dataframe(df_daily.sort_values(by='Total (R$)', ascending=False), use_container_width=True)

    with subtab_passivos:
        st.markdown("#### Contratos Bancários, Financiamentos e Consórcios (Aba BANCOS)")
        if df_bancos.empty:
            st.warning("Nenhum registro encontrado na aba BANCOS.")
        else:
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                st.metric("Saldo Devedor Total", f"R$ {df_bancos['Saldo Devedor (R$)'].sum():,.2f}")
            with col_b2:
                st.metric("Compromisso Mensal (Parcelas)", f"R$ {df_bancos['Valor Parcela (R$)'].sum():,.2f}")

            st.dataframe(df_bancos, use_container_width=True)


# --------------------------------------------------------------------------------------
# TAB 2: REDUÇÃO DE DESPESAS
# --------------------------------------------------------------------------------------
with tab_despesas:
    st.markdown("### 📉 Redução & Eficiência de Despesas")

    sub_abc, sub_dup, sub_board = st.tabs(["Curva ABC (Pareto)", "Duplicidades & Anomalias", "Metas Board vs Realizado"])

    with sub_abc:
        st.markdown("#### Curva de Pareto dos Maiores Credores")
        df_fornecedores = df_filtrado.groupby('RAZÃO SOCIAL')['VALOR (R$)'].sum().reset_index()
        df_fornecedores.sort_values(by='VALOR (R$)', ascending=False, inplace=True)
        total_desp = df_fornecedores['VALOR (R$)'].sum()
        df_fornecedores['% do Total'] = (df_fornecedores['VALOR (R$)'] / total_desp) * 100
        df_fornecedores['% Acumulado'] = df_fornecedores['% do Total'].cumsum()

        def classificar_abc(pct):
            if pct <= 80:
                return "Classe A"
            elif pct <= 95:
                return "Classe B"
            return "Classe C"

        df_fornecedores['Classe'] = df_fornecedores['% Acumulado'].apply(classificar_abc)

        top15 = df_fornecedores.head(15)

        fig_pareto = go.Figure()
        fig_pareto.add_trace(go.Bar(
            x=top15['RAZÃO SOCIAL'],
            y=top15['VALOR (R$)'],
            name="Valor (R$)",
            marker_color="#059669"
        ))
        fig_pareto.add_trace(go.Scatter(
            x=top15['RAZÃO SOCIAL'],
            y=top15['% Acumulado'],
            name="% Acumulado",
            yaxis="y2",
            line=dict(color="#2563eb", width=3)
        ))
        fig_pareto.update_layout(
            title="Top 15 Fornecedores vs % Acumulado",
            yaxis=dict(title="Valor Desembolsado (R$)"),
            yaxis2=dict(title="% Acumulado", overlaying="y", side="right", range=[0, 100]),
            xaxis_tickangle=-30
        )
        st.plotly_chart(fig_pareto, use_container_width=True)

        st.dataframe(df_fornecedores, use_container_width=True)

    with sub_dup:
        st.markdown("#### Detecção de Pagamentos Duplicados / Idênticos")
        st.info("Varredura de lançamentos no mesmo mês, mesmo credor e com o mesmo valor exato.")

        df_dup = df_filtrado[df_filtrado.duplicated(subset=['MÊS', 'RAZÃO SOCIAL', 'VALOR (R$)'], keep=False)].copy()
        if df_dup.empty:
            st.success("✅ Nenhuma duplicidade identificada!")
        else:
            st.warning(f"⚠️ {len(df_dup)} lançamentos potencialmente duplicados encontrados.")
            st.dataframe(df_dup.sort_values(by=['RAZÃO SOCIAL', 'VALOR (R$)']), use_container_width=True)

    with sub_board:
        st.markdown("#### Comparativo Orçado vs Realizado (Aba DESPESA FIXA BOARD)")
        if df_board.empty:
            st.warning("Nenhum dado na aba DESPESA FIXA BOARD.")
        else:
            st.dataframe(df_board, use_container_width=True)


# --------------------------------------------------------------------------------------
# TAB 3: AUDITORIA DE NATUREZAS
# --------------------------------------------------------------------------------------
with tab_auditoria:
    st.markdown("### 🛡️ Auditoria de Naturezas de Gastos & Erros Contábeis")

    sub_lixeira, sub_sem_cad, sub_matriz = st.tabs([
        "Matriz de Reclassificação", "Contas 'Lixeira'", "Sem Beneficiário / CNPJ"
    ])

    with sub_matriz:
        st.markdown("#### Inconsistências Semânticas (Texto vs. Grupo Contábil)")
        df_ajustes = audit_nature_inconsistencies(df_filtrado)

        if df_ajustes.empty:
            st.success("✅ Nenhuma divergência de natureza identificada com as regras atuais.")
        else:
            st.warning(f"⚠️ {len(df_ajustes)} lançamentos com sugestão de reclassificação.")
            st.dataframe(df_ajustes, use_container_width=True)

            # Exportar CSV de ajustes
            csv_ajustes = df_ajustes.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Baixar Matriz de Ajustes Contábeis (.csv)",
                data=csv_ajustes,
                file_name=f"ajustes_contabeis_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

    with sub_lixeira:
        st.markdown("#### Lançamentos em Contas 'Lixeira' (OUTROS, DIVERSOS, NÃO OPERACIONAIS)")
        grupos_lixeira = ["OUTROS", "DIVERSOS", "OUTRAS DESPESAS", "NÃO OPERACIONAIS", "NAO OPERACIONAIS"]
        df_lixeira = df_filtrado[df_filtrado['GRUPO'].astype(str).str.upper().isin(grupos_lixeira)]

        st.metric("Total em Contas Genéricas", f"R$ {df_lixeira['VALOR (R$)'].sum():,.2f}", f"{len(df_lixeira)} itens")
        st.dataframe(df_lixeira[['DATA', 'LANÇAMENTO', 'RAZÃO SOCIAL', 'VALOR (R$)', 'GRUPO']], use_container_width=True)

    with sub_sem_cad:
        st.markdown("#### Pagamentos sem CPF/CNPJ ou Razão Social")
        df_sem_cad = df_filtrado[
            (df_filtrado['CPF/CNPJ'].isna()) | (df_filtrado['CPF/CNPJ'].astype(str).str.strip() == "") |
            (df_filtrado['RAZÃO SOCIAL'].astype(str).str.upper().isin(["NAN", "NULL", ""]))
        ]
        st.metric("Risco Fiscal (Sem Cadastro)", f"R$ {df_sem_cad['VALOR (R$)'].sum():,.2f}", f"{len(df_sem_cad)} itens")
        st.dataframe(df_sem_cad[['DATA', 'LANÇAMENTO', 'RAZÃO SOCIAL', 'CPF/CNPJ', 'VALOR (R$)']], use_container_width=True)


# --------------------------------------------------------------------------------------
# TAB 4: PROVISIONAMENTO PREDITIVO
# --------------------------------------------------------------------------------------
with tab_provisao:
    st.markdown("### ⏰ Necessidade de Provisionamento Preditivo")

    mes_corte = st.selectbox(
        "Selecione o Mês para Avaliar Provisões Ausentes",
        [m for m in meses_disponiveis if m != "TODOS"],
        index=len([m for m in meses_disponiveis if m != "TODOS"]) - 1 if len(meses_disponiveis) > 1 else 0
    )

    df_provisao = calculate_predictive_provisioning(df_base, mes_corte)

    if df_provisao.empty:
        st.success(f"✅ Todas as contas recorrentes históricas constam no mês {mes_corte}!")
    else:
        total_risco_provisao = df_provisao['Média Mensal Histórica (R$)'].sum()
        st.error(f"⚠️ Risco de Caixa Oculto: R$ {total_risco_provisao:,.2f} em {len(df_provisao)} despesas recorrentes não faturadas em {mes_corte}.")
        st.dataframe(df_provisao, use_container_width=True)


# --------------------------------------------------------------------------------------
# TAB 5: DIAGNÓSTICO IA GEMINI
# --------------------------------------------------------------------------------------
with tab_ia:
    st.markdown("### 🧠 Diagnóstico Executivo de Controladoria com Gemini AI")
    st.write("Gere um parecer pericial completo consolidando riscos de liquidez, erros contábeis e recomendações.")

    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    if not gemini_key:
        gemini_key = st.text_input("Insira sua Chave GEMINI_API_KEY (ou configure no ambiente):", type="password")

    diretrizes_personalizadas = st.text_area(
        "Diretrizes Adicionais para a IA (Opcional)",
        placeholder="Ex: Focar no impacto fiscal das contas lixeira e na renegociação dos empréstimos bancários..."
    )

    if st.button("🚀 Gerar Diagnóstico Executivo com Gemini", type="primary"):
        if not gemini_key:
            st.error("Chave GEMINI_API_KEY não informada.")
        else:
            with st.spinner("Analisando extrato financeiro e compilando diagnóstico pericial..."):
                try:
                    from google import genai
                    client = genai.Client(api_key=gemini_key)

                    prompt = f"""
Você é um Auditor e Perito em Controladoria Financeira Sênior (CFO / Diretor de Auditoria).
Analise os dados sumarizados da empresa referentes ao relatório '0. EXTRATO GERAL.xlsx' e elabore um PARECER EXECUTIVO DE CONTROLADORIA E AUDITORIA.

MÉTRICAS DO RELATÓRIO:
- Volume Total Analisado: R$ {total_volume:,.2f} ({total_linhas} lançamentos)
- Despesas em Aberto: R$ {abertos_volume:,.2f}
- Drenos Financeiros (Tarifas/Juros/IOF): R$ {df_drenos['VALOR (R$)'].sum():,.2f}
- Saldo Devedor Bancário: R$ {passivo_bancos_total:,.2f}
- Contas Lixeira ('OUTROS'/'DIVERSOS'): R$ {df_lixeira['VALOR (R$)'].sum():,.2f}
- Despesas sem CNPJ/Razão Social: R$ {df_sem_cad['VALOR (R$)'].sum():,.2f}
- Inconsistências de Natureza Contábil: {len(df_ajustes)} lançamentos identificados

INSTRUÇÃO COMPLEMENTAR DO AUDITOR:
{diretrizes_personalizadas}

ESTRUTURE SEU PARECER COM OS SEGUINTES CAPÍTULOS:
1. SUMÁRIO EXECUTIVO & DIAGNÓSTICO DE RISCO (Nota de Governança de 0 a 10)
2. AUDITORIA DE CONTAS E SANEAMENTO CONTÁBIL (Riscos de Glosa, Contas Lixeira e Reclassificações)
3. VULNERABILIDADES DE FLUXO DE CAIXA (Drenos em Tarifas/Juros, Descascamento Diário e Picos)
4. ENDIVIDAMENTO E PASSIVOS BANCÁRIOS (Avaliação da alavancagem financeira)
5. PLANO DE AÇÃO IMEDIATO EM 5 PASSOS (Checklist de implementação para o CFO)
"""
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt
                    )

                    st.markdown("---")
                    st.markdown(response.text)

                    # Botão para baixar parecer
                    st.download_button(
                        label="📥 Baixar Parecer Executivo (.md)",
                        data=response.text.encode('utf-8'),
                        file_name=f"parecer_controladoria_{datetime.now().strftime('%Y%m%d')}.md",
                        mime="text/markdown"
                    )

                except Exception as ex:
                    st.error(f"Erro ao conectar com Gemini: {ex}")


# --------------------------------------------------------------------------------------
# TAB 6: EXTRATO GERAL COMPLETO
# --------------------------------------------------------------------------------------
with tab_extrato:
    st.markdown("### 📋 Extrato Geral - Todos os Lançamentos")
    st.dataframe(df_filtrado, use_container_width=True)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_filtrado.to_excel(writer, sheet_name='BASE_FILTRADA', index=False)
        df_board.to_excel(writer, sheet_name='DESPESA FIXA BOARD', index=False)
        df_bancos.to_excel(writer, sheet_name='BANCOS', index=False)

    st.download_button(
        label="📥 Exportar Base Filtrada para Excel (.xlsx)",
        data=buffer.getvalue(),
        file_name=f"extrato_geral_export_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
