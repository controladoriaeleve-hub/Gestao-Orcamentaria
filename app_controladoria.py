import os
import io
import re
import unicodedata
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
# UTILITÁRIOS DE NORMALIZAÇÃO DE DATAFRAMES (PREVENÇÃO DE KEYERROR)
# --------------------------------------------------------------------------------------
def clean_col_name(col: str) -> str:
    """Remove acentos, espaços extras e converte para maiúsculo."""
    nfkd = unicodedata.normalize('NFKD', str(col))
    cleaned = ''.join([c for c in nfkd if not unicodedata.combining(c)])
    return cleaned.strip().upper()


def normalize_base_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Garante mapeamento robusto de colunas e colunas obrigatórias."""
    if df is None or df.empty:
        df = pd.DataFrame()

    col_mapping = {}
    for col in df.columns:
        norm = clean_col_name(col)
        if norm in ["MES", "COMPETENCIA", "PERIODO", "MES ANO", "MES/ANO"]:
            col_mapping[col] = "MÊS"
        elif norm in ["STATUS", "SITUACAO", "ESTADO"]:
            col_mapping[col] = "STATUS"
        elif norm in ["DATA", "VENCIMENTO", "PAGAMENTO", "DATA PAGAMENTO", "DT PAGTO"]:
            col_mapping[col] = "DATA"
        elif norm in ["LANCAMENTO", "HISTORICO", "DESCRICAO", "DESCRICAO LANCAMENTO"]:
            col_mapping[col] = "LANÇAMENTO"
        elif norm in ["RAZAO SOCIAL", "FORNECEDOR", "CREDOR", "BENEFICIARIO", "CLIENTE", "FAVORECIDO"]:
            col_mapping[col] = "RAZÃO SOCIAL"
        elif norm in ["CPF/CNPJ", "CNPJ", "CPF", "DOC", "DOCUMENTO"]:
            col_mapping[col] = "CPF/CNPJ"
        elif norm in ["VALOR (R$)", "VALOR", "VALOR R$", "VALOR LIQUIDO", "TOTAL", "VALOR PAGO"]:
            col_mapping[col] = "VALOR (R$)"
        elif norm in ["GRUPO", "CENTRO DE CUSTO", "CATEGORIA", "CLASSIFICACAO", "GRUPO DESPESA"]:
            col_mapping[col] = "GRUPO"
        elif norm in ["COD GRUPO", "COD. GRUPO", "CODIGO GRUPO"]:
            col_mapping[col] = "CÓD GRUPO"
        elif norm in ["COD NATUREZA", "COD. NATUREZA", "CODIGO NATUREZA"]:
            col_mapping[col] = "CÓD. NATUREZA"
        elif norm in ["DESCRICAO NATUREZA", "NATUREZA", "CONTA CONTABIL"]:
            col_mapping[col] = "DESCRIÇÃO NATUREZA"
        elif norm in ["TIPO", "TIPO DESPESA", "TIPO CUSTO"]:
            col_mapping[col] = "TIPO"

    df = df.rename(columns=col_mapping)

    # 1. MÊS
    if "MÊS" not in df.columns:
        if "DATA" in df.columns:
            try:
                df["MÊS"] = pd.to_datetime(df["DATA"], errors='coerce').dt.strftime('%b/%Y').str.upper()
                df["MÊS"] = df["MÊS"].fillna("GERAL")
            except:
                df["MÊS"] = "GERAL"
        else:
            df["MÊS"] = "GERAL"
    else:
        df["MÊS"] = df["MÊS"].fillna("GERAL").astype(str).str.strip().str.upper()

    # 2. STATUS
    if "STATUS" not in df.columns:
        df["STATUS"] = "PAGO"
    else:
        df["STATUS"] = df["STATUS"].fillna("PAGO").astype(str).str.strip().str.upper()

    # 3. VALOR (R$)
    if "VALOR (R$)" not in df.columns:
        for c in df.columns:
            if "VALOR" in clean_col_name(c):
                df["VALOR (R$)"] = df[c]
                break
        else:
            df["VALOR (R$)"] = 0.0

    if "VALOR (R$)" in df.columns:
        if df["VALOR (R$)"].dtype == object:
            df["VALOR (R$)"] = (
                df["VALOR (R$)"]
                .astype(str)
                .str.replace("R$", "", regex=False)
                .str.replace(".", "", regex=False)
                .str.replace(",", ".", regex=False)
                .str.strip()
            )
        df["VALOR (R$)"] = pd.to_numeric(df["VALOR (R$)"], errors="coerce").fillna(0.0)

    # 4. GRUPO
    if "GRUPO" not in df.columns:
        df["GRUPO"] = "OUTROS"
    else:
        df["GRUPO"] = df["GRUPO"].fillna("OUTROS").astype(str).str.strip().str.upper()

    # 5. RAZÃO SOCIAL
    if "RAZÃO SOCIAL" not in df.columns:
        df["RAZÃO SOCIAL"] = "NÃO IDENTIFICADO"
    else:
        df["RAZÃO SOCIAL"] = df["RAZÃO SOCIAL"].fillna("NÃO IDENTIFICADO").astype(str).str.strip()

    # 6. LANÇAMENTO
    if "LANÇAMENTO" not in df.columns:
        df["LANÇAMENTO"] = "Sem histórico"
    else:
        df["LANÇAMENTO"] = df["LANÇAMENTO"].fillna("Sem histórico").astype(str).str.strip()

    # 7. DATA
    if "DATA" not in df.columns:
        df["DATA"] = "2026-01-01"
    else:
        df["DATA"] = df["DATA"].astype(str).str.strip()

    # 8. CPF/CNPJ
    if "CPF/CNPJ" not in df.columns:
        df["CPF/CNPJ"] = ""
    else:
        df["CPF/CNPJ"] = df["CPF/CNPJ"].fillna("").astype(str).str.strip()

    # 9. DESCRIÇÃO NATUREZA
    if "DESCRIÇÃO NATUREZA" not in df.columns:
        df["DESCRIÇÃO NATUREZA"] = ""
    else:
        df["DESCRIÇÃO NATUREZA"] = df["DESCRIÇÃO NATUREZA"].fillna("").astype(str).str.strip()

    # 10. TIPO
    if "TIPO" not in df.columns:
        df["TIPO"] = "VARIÁVEL"
    else:
        df["TIPO"] = df["TIPO"].fillna("VARIÁVEL").astype(str).str.strip().str.upper()

    return df


def normalize_board_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza o dataframe da aba DESPESA FIXA BOARD."""
    if df is None or df.empty:
        return pd.DataFrame(columns=["Categoria", "Descrição", "Meta Mensal (R$)", "Realizado Médio (R$)", "Observação"])

    col_map = {}
    for col in df.columns:
        norm = clean_col_name(col)
        if "CATEGORIA" in norm or "GRUPO" in norm:
            col_map[col] = "Categoria"
        elif "DESCRICAO" in norm or "DETALHE" in norm:
            col_map[col] = "Descrição"
        elif "META" in norm or "ORCADO" in norm:
            col_map[col] = "Meta Mensal (R$)"
        elif "REALIZADO" in norm or "MEDIO" in norm or "ATUAL" in norm:
            col_map[col] = "Realizado Médio (R$)"
        elif "OBSERVACAO" in norm or "NOTAS" in norm:
            col_map[col] = "Observação"

    df = df.rename(columns=col_map)
    for col in ["Categoria", "Descrição", "Observação"]:
        if col not in df.columns:
            df[col] = ""
    for col in ["Meta Mensal (R$)", "Realizado Médio (R$)"]:
        if col not in df.columns:
            df[col] = 0.0
        else:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    return df


def normalize_bancos_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza o dataframe da aba BANCOS."""
    if df is None or df.empty:
        return pd.DataFrame(columns=[
            "Banco", "Tipo de Operação", "Contrato", "Saldo Devedor (R$)",
            "Valor Parcela (R$)", "Parcelas Restantes", "Dia Vencimento", "Taxa de Juros", "Status"
        ])

    col_map = {}
    for col in df.columns:
        norm = clean_col_name(col)
        if "BANCO" in norm or "INSTITUICAO" in norm:
            col_map[col] = "Banco"
        elif "OPERACAO" in norm or "TIPO" in norm:
            col_map[col] = "Tipo de Operação"
        elif "CONTRATO" in norm:
            col_map[col] = "Contrato"
        elif "SALDO" in norm or "DEVEDOR" in norm:
            col_map[col] = "Saldo Devedor (R$)"
        elif "PARCELA" in norm and ("VALOR" in norm or "R$" in norm):
            col_map[col] = "Valor Parcela (R$)"
        elif "RESTANTE" in norm or "QTD" in norm:
            col_map[col] = "Parcelas Restantes"
        elif "VENCIMENTO" in norm or "DIA" in norm:
            col_map[col] = "Dia Vencimento"
        elif "TAXA" in norm or "JUROS" in norm:
            col_map[col] = "Taxa de Juros"
        elif "STATUS" in norm:
            col_map[col] = "Status"

    df = df.rename(columns=col_map)
    for col in ["Banco", "Tipo de Operação", "Contrato", "Taxa de Juros", "Status"]:
        if col not in df.columns:
            df[col] = ""
    for col in ["Saldo Devedor (R$)", "Valor Parcela (R$)"]:
        if col not in df.columns:
            df[col] = 0.0
        else:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    for col in ["Parcelas Restantes", "Dia Vencimento"]:
        if col not in df.columns:
            df[col] = 0
        else:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    return df


# --------------------------------------------------------------------------------------
# DADOS DE EXEMPLO (DEMO EMBUTIDA)
# --------------------------------------------------------------------------------------
@st.cache_data
def get_mock_datasets():
    # 1. BASE
    base_data = [
        # JAN/2026
        {"STATUS": "PAGO", "MÊS": "JAN/2026", "DATA": "2026-01-05", "LANÇAMENTO": "FOLHA PJ - DESENVOLVIMENTO DE SOFTWARE", "RAZÃO SOCIAL": "TECH SOLUCOES DIGITAIS LTDA", "CPF/CNPJ": "12.345.678/0001-90", "VALOR (R$)": 28500.0, "CÓD GRUPO": "GRP-01", "GRUPO": "PESSOAL / TERCEIROS", "CÓD. NATUREZA": "NAT-101", "DESCRIÇÃO NATUREZA": "Serviços de T.I. Terceirizados", "TIPO": "FIXA"},
        {"STATUS": "PAGO", "MÊS": "JAN/2026", "DATA": "2026-01-05", "LANÇAMENTO": "ALUGUEL SEDE OPERACIONAL SP", "RAZÃO SOCIAL": "IMOBILIARIA METROPOLITANA S/A", "CPF/CNPJ": "04.987.654/0001-12", "VALOR (R$)": 18500.0, "CÓD GRUPO": "GRP-02", "GRUPO": "DESPESAS IMOBILIÁRIAS", "CÓD. NATUREZA": "NAT-102", "DESCRIÇÃO NATUREZA": "Aluguel Predial", "TIPO": "FIXA"},
        {"STATUS": "PAGO", "MÊS": "JAN/2026", "DATA": "2026-01-07", "LANÇAMENTO": "FGTS COMPETÊNCIA DEZEMBRO", "RAZÃO SOCIAL": "CAIXA ECONOMICA FEDERAL", "CPF/CNPJ": "00.360.305/0001-04", "VALOR (R$)": 14200.0, "CÓD GRUPO": "GRP-03", "GRUPO": "ENCARGOS SOCIAIS", "CÓD. NATUREZA": "NAT-103", "DESCRIÇÃO NATUREZA": "Encargos Trabalhistas", "TIPO": "FIXA"},
        {"STATUS": "PAGO", "MÊS": "JAN/2026", "DATA": "2026-01-10", "LANÇAMENTO": "LICENCIAMENTO ERP MENSAL", "RAZÃO SOCIAL": "TOTVS S/A", "CPF/CNPJ": "53.113.791/0001-22", "VALOR (R$)": 9800.0, "CÓD GRUPO": "GRP-04", "GRUPO": "T.I. E SOFTWARE", "CÓD. NATUREZA": "NAT-104", "DESCRIÇÃO NATUREZA": "Sistemas de Gestão ERP", "TIPO": "FIXA"},
        {"STATUS": "PAGO", "MÊS": "JAN/2026", "DATA": "2026-01-10", "LANÇAMENTO": "CONTRATO MANUTENÇÃO PREVENTIVA ELEVADORES", "RAZÃO SOCIAL": "ELEVADORES ATLAS SCHINDLER", "CPF/CNPJ": "60.422.382/0001-44", "VALOR (R$)": 3200.0, "CÓD GRUPO": "GRP-05", "GRUPO": "OUTROS", "CÓD. NATUREZA": "NAT-999", "DESCRIÇÃO NATUREZA": "Despesas Diversas", "TIPO": "FIXA"},
        {"STATUS": "PAGO", "MÊS": "JAN/2026", "DATA": "2026-01-12", "LANÇAMENTO": "TARIFA BANCÁRIA MANUTENÇÃO CONTA CORRENTE", "RAZÃO SOCIAL": "BANCO BRADESCO S/A", "CPF/CNPJ": "60.746.948/0001-12", "VALOR (R$)": 185.0, "CÓD GRUPO": "GRP-06", "GRUPO": "DESPESAS FINANCEIRAS", "CÓD. NATUREZA": "NAT-106", "DESCRIÇÃO NATUREZA": "Tarifas de Serviços Bancários", "TIPO": "VARIÁVEL"},
        {"STATUS": "PAGO", "MÊS": "JAN/2026", "DATA": "2026-01-15", "LANÇAMENTO": "VALE ALIMENTAÇÃO E REFEIÇÃO EQUIPE", "RAZÃO SOCIAL": "ALELO S/A BENEFICIOS", "CPF/CNPJ": "04.740.876/0001-25", "VALOR (R$)": 11400.0, "CÓD GRUPO": "GRP-07", "GRUPO": "BENEFÍCIOS", "CÓD. NATUREZA": "NAT-107", "DESCRIÇÃO NATUREZA": "Alimentação Colaboradores", "TIPO": "FIXA"},
        {"STATUS": "PAGO", "MÊS": "JAN/2026", "DATA": "2026-01-18", "LANÇAMENTO": "PARCELA 14/24 FINANCIAMENTO FROTA", "RAZÃO SOCIAL": "BANCO ITAU UNIBANCO S/A", "CPF/CNPJ": "60.701.190/0001-04", "VALOR (R$)": 5200.0, "CÓD GRUPO": "GRP-08", "GRUPO": "BANCOS / FINANCIAMENTOS", "CÓD. NATUREZA": "NAT-108", "DESCRIÇÃO NATUREZA": "Amortização de Financiamento", "TIPO": "FIXA"},
        {"STATUS": "PAGO", "MÊS": "JAN/2026", "DATA": "2026-01-20", "LANÇAMENTO": "COMBUSTIVEL FROTA COMERCIAL", "RAZÃO SOCIAL": "POSTO IPIRANGA CENTRAL", "CPF/CNPJ": "11.222.333/0001-44", "VALOR (R$)": 4150.0, "CÓD GRUPO": "GRP-05", "GRUPO": "OUTROS", "CÓD. NATUREZA": "NAT-999", "DESCRIÇÃO NATUREZA": "Despesas Gerais", "TIPO": "VARIÁVEL"},
        {"STATUS": "PAGO", "MÊS": "JAN/2026", "DATA": "2026-01-22", "LANÇAMENTO": "JUROS DE MORA POR ATRASO FORNECEDOR", "RAZÃO SOCIAL": "DISTRIBUIDORA DE EMBALAGENS LTDA", "CPF/CNPJ": "33.444.555/0001-88", "VALOR (R$)": 640.0, "CÓD GRUPO": "GRP-06", "GRUPO": "DESPESAS FINANCEIRAS", "CÓD. NATUREZA": "NAT-109", "DESCRIÇÃO NATUREZA": "Juros e Multas Pagos", "TIPO": "VARIÁVEL"},
        {"STATUS": "PAGO", "MÊS": "JAN/2026", "DATA": "2026-01-25", "LANÇAMENTO": "PARCELA EMPRÉSTIMO CAPITAL DE GIRO", "RAZÃO SOCIAL": "BANCO BRADESCO S/A", "CPF/CNPJ": "60.746.948/0001-12", "VALOR (R$)": 15400.0, "CÓD GRUPO": "GRP-08", "GRUPO": "BANCOS / FINANCIAMENTOS", "CÓD. NATUREZA": "NAT-110", "DESCRIÇÃO NATUREZA": "Empréstimo Bancário", "TIPO": "FIXA"},
        {"STATUS": "PAGO", "MÊS": "JAN/2026", "DATA": "2026-01-26", "LANÇAMENTO": "PAGAMENTO PIX SEM COMPROVANTE CADASTRO", "RAZÃO SOCIAL": "NAN", "CPF/CNPJ": "", "VALOR (R$)": 3800.0, "CÓD GRUPO": "GRP-05", "GRUPO": "OUTRAS DESPESAS", "CÓD. NATUREZA": "NAT-999", "DESCRIÇÃO NATUREZA": "Despesas Diversas", "TIPO": "VARIÁVEL"},
        {"STATUS": "PAGO", "MÊS": "JAN/2026", "DATA": "2026-01-28", "LANÇAMENTO": "IOF RETENÇÃO OPERAÇÃO CRÉDITO", "RAZÃO SOCIAL": "RECEITA FEDERAL DO BRASIL", "CPF/CNPJ": "00.394.460/0058-87", "VALOR (R$)": 920.0, "CÓD GRUPO": "GRP-06", "GRUPO": "DESPESAS FINANCEIRAS", "CÓD. NATUREZA": "NAT-111", "DESCRIÇÃO NATUREZA": "Impostos Operações Financeiras", "TIPO": "VARIÁVEL"},
        {"STATUS": "PAGO", "MÊS": "JAN/2026", "DATA": "2026-01-30", "LANÇAMENTO": "PARCELA CONSÓRCIO IMOBILIÁRIO SEDE", "RAZÃO SOCIAL": "BANCO SANTANDER BRASIL S/A", "CPF/CNPJ": "90.400.888/0001-42", "VALOR (R$)": 8250.0, "CÓD GRUPO": "GRP-08", "GRUPO": "BANCOS / FINANCIAMENTOS", "CÓD. NATUREZA": "NAT-112", "DESCRIÇÃO NATUREZA": "Consórcio", "TIPO": "FIXA"},
        # FEV/2026
        {"STATUS": "PAGO", "MÊS": "FEV/2026", "DATA": "2026-02-05", "LANÇAMENTO": "FOLHA PJ - DESENVOLVIMENTO DE SOFTWARE", "RAZÃO SOCIAL": "TECH SOLUCOES DIGITAIS LTDA", "CPF/CNPJ": "12.345.678/0001-90", "VALOR (R$)": 28500.0, "CÓD GRUPO": "GRP-01", "GRUPO": "PESSOAL / TERCEIROS", "CÓD. NATUREZA": "NAT-101", "DESCRIÇÃO NATUREZA": "Serviços de T.I. Terceirizados", "TIPO": "FIXA"},
        {"STATUS": "PAGO", "MÊS": "FEV/2026", "DATA": "2026-02-05", "LANÇAMENTO": "ALUGUEL SEDE OPERACIONAL SP", "RAZÃO SOCIAL": "IMOBILIARIA METROPOLITANA S/A", "CPF/CNPJ": "04.987.654/0001-12", "VALOR (R$)": 18500.0, "CÓD GRUPO": "GRP-02", "GRUPO": "DESPESAS IMOBILIÁRIAS", "CÓD. NATUREZA": "NAT-102", "DESCRIÇÃO NATUREZA": "Aluguel Predial", "TIPO": "FIXA"},
        {"STATUS": "PAGO", "MÊS": "FEV/2026", "DATA": "2026-02-07", "LANÇAMENTO": "FGTS COMPETÊNCIA JANEIRO", "RAZÃO SOCIAL": "CAIXA ECONOMICA FEDERAL", "CPF/CNPJ": "00.360.305/0001-04", "VALOR (R$)": 14650.0, "CÓD GRUPO": "GRP-03", "GRUPO": "ENCARGOS SOCIAIS", "CÓD. NATUREZA": "NAT-103", "DESCRIÇÃO NATUREZA": "Encargos Trabalhistas", "TIPO": "FIXA"},
        {"STATUS": "PAGO", "MÊS": "FEV/2026", "DATA": "2026-02-10", "LANÇAMENTO": "LICENCIAMENTO ERP MENSAL", "RAZÃO SOCIAL": "TOTVS S/A", "CPF/CNPJ": "53.113.791/0001-22", "VALOR (R$)": 9800.0, "CÓD GRUPO": "GRP-04", "GRUPO": "T.I. E SOFTWARE", "CÓD. NATUREZA": "NAT-104", "DESCRIÇÃO NATUREZA": "Sistemas de Gestão ERP", "TIPO": "FIXA"},
        {"STATUS": "PAGO", "MÊS": "FEV/2026", "DATA": "2026-02-10", "LANÇAMENTO": "CONSULTORIA CONTÁBIL E AUDITORIA", "RAZÃO SOCIAL": "AUDITEX AUDITORES INDEPENDENTES", "CPF/CNPJ": "77.888.999/0001-11", "VALOR (R$)": 7500.0, "CÓD GRUPO": "GRP-09", "GRUPO": "SERVIÇOS PROFISSIONAIS", "CÓD. NATUREZA": "NAT-113", "DESCRIÇÃO NATUREZA": "Honorários Contábeis", "TIPO": "FIXA"},
        {"STATUS": "PAGO", "MÊS": "FEV/2026", "DATA": "2026-02-12", "LANÇAMENTO": "MANUTENÇÃO CORRETIVA SISTEMA DE AR CONDICIONADO", "RAZÃO SOCIAL": "CLIMAFRIO REFRIGERACAO LTDA", "CPF/CNPJ": "88.999.000/0001-22", "VALOR (R$)": 4850.0, "CÓD GRUPO": "GRP-05", "GRUPO": "DIVERSOS", "CÓD. NATUREZA": "NAT-999", "DESCRIÇÃO NATUREZA": "Despesas Gerais", "TIPO": "VARIÁVEL"},
        {"STATUS": "PAGO", "MÊS": "FEV/2026", "DATA": "2026-02-15", "LANÇAMENTO": "VALE ALIMENTAÇÃO E REFEIÇÃO EQUIPE", "RAZÃO SOCIAL": "ALELO S/A BENEFICIOS", "CPF/CNPJ": "04.740.876/0001-25", "VALOR (R$)": 11400.0, "CÓD GRUPO": "GRP-07", "GRUPO": "BENEFÍCIOS", "CÓD. NATUREZA": "NAT-107", "DESCRIÇÃO NATUREZA": "Alimentação Colaboradores", "TIPO": "FIXA"},
        {"STATUS": "PAGO", "MÊS": "FEV/2026", "DATA": "2026-02-18", "LANÇAMENTO": "PARCELA 15/24 FINANCIAMENTO FROTA", "RAZÃO SOCIAL": "BANCO ITAU UNIBANCO S/A", "CPF/CNPJ": "60.701.190/0001-04", "VALOR (R$)": 5200.0, "CÓD GRUPO": "GRP-08", "GRUPO": "BANCOS / FINANCIAMENTOS", "CÓD. NATUREZA": "NAT-108", "DESCRIÇÃO NATUREZA": "Amortização de Financiamento", "TIPO": "FIXA"},
        {"STATUS": "PAGO", "MÊS": "FEV/2026", "DATA": "2026-02-20", "LANÇAMENTO": "FORNECIMENTO DE EMBALAGENS LOTE 01", "RAZÃO SOCIAL": "DISTRIBUIDORA DE EMBALAGENS LTDA", "CPF/CNPJ": "33.444.555/0001-88", "VALOR (R$)": 8450.0, "CÓD GRUPO": "GRP-10", "GRUPO": "INSUMOS / PRODUÇÃO", "CÓD. NATUREZA": "NAT-114", "DESCRIÇÃO NATUREZA": "Matéria Prima e Insumos", "TIPO": "VARIÁVEL"},
        {"STATUS": "PAGO", "MÊS": "FEV/2026", "DATA": "2026-02-20", "LANÇAMENTO": "FORNECIMENTO DE EMBALAGENS LOTE 01 (REPETIDO)", "RAZÃO SOCIAL": "DISTRIBUIDORA DE EMBALAGENS LTDA", "CPF/CNPJ": "33.444.555/0001-88", "VALOR (R$)": 8450.0, "CÓD GRUPO": "GRP-10", "GRUPO": "INSUMOS / PRODUÇÃO", "CÓD. NATUREZA": "NAT-114", "DESCRIÇÃO NATUREZA": "Matéria Prima e Insumos", "TIPO": "VARIÁVEL"},
        {"STATUS": "PAGO", "MÊS": "FEV/2026", "DATA": "2026-02-25", "LANÇAMENTO": "PARCELA EMPRÉSTIMO CAPITAL DE GIRO", "RAZÃO SOCIAL": "BANCO BRADESCO S/A", "CPF/CNPJ": "60.746.948/0001-12", "VALOR (R$)": 15400.0, "CÓD GRUPO": "GRP-08", "GRUPO": "BANCOS / FINANCIAMENTOS", "CÓD. NATUREZA": "NAT-110", "DESCRIÇÃO NATUREZA": "Empréstimo Bancário", "TIPO": "FIXA"},
        {"STATUS": "PAGO", "MÊS": "FEV/2026", "DATA": "2026-02-28", "LANÇAMENTO": "PARCELA CONSÓRCIO IMOBILIÁRIO SEDE", "RAZÃO SOCIAL": "BANCO SANTANDER BRASIL S/A", "CPF/CNPJ": "90.400.888/0001-42", "VALOR (R$)": 8250.0, "CÓD GRUPO": "GRP-08", "GRUPO": "BANCOS / FINANCIAMENTOS", "CÓD. NATUREZA": "NAT-112", "DESCRIÇÃO NATUREZA": "Consórcio", "TIPO": "FIXA"},
        # MAR/2026
        {"STATUS": "EM ABERTO", "MÊS": "MAR/2026", "DATA": "2026-03-05", "LANÇAMENTO": "FOLHA PJ - DESENVOLVIMENTO DE SOFTWARE", "RAZÃO SOCIAL": "TECH SOLUCOES DIGITAIS LTDA", "CPF/CNPJ": "12.345.678/0001-90", "VALOR (R$)": 28500.0, "CÓD GRUPO": "GRP-01", "GRUPO": "PESSOAL / TERCEIROS", "CÓD. NATUREZA": "NAT-101", "DESCRIÇÃO NATUREZA": "Serviços de T.I. Terceirizados", "TIPO": "FIXA"},
        {"STATUS": "EM ABERTO", "MÊS": "MAR/2026", "DATA": "2026-03-10", "LANÇAMENTO": "SERVIÇOS DE LIMPEZA E FACILITIES", "RAZÃO SOCIAL": "LIMPEZA FACIL SERVICOS TERCEIRIZADOS", "CPF/CNPJ": "44.555.666/0001-77", "VALOR (R$)": 6200.0, "CÓD GRUPO": "GRP-05", "GRUPO": "NÃO OPERACIONAIS", "CÓD. NATUREZA": "NAT-999", "DESCRIÇÃO NATUREZA": "Despesas Gerais", "TIPO": "FIXA"},
        {"STATUS": "EM ABERTO", "MÊS": "MAR/2026", "DATA": "2026-03-18", "LANÇAMENTO": "PARCELA 16/24 FINANCIAMENTO FROTA", "RAZÃO SOCIAL": "BANCO ITAU UNIBANCO S/A", "CPF/CNPJ": "60.701.190/0001-04", "VALOR (R$)": 5200.0, "CÓD GRUPO": "GRP-08", "GRUPO": "BANCOS / FINANCIAMENTOS", "CÓD. NATUREZA": "NAT-108", "DESCRIÇÃO NATUREZA": "Amortização de Financiamento", "TIPO": "FIXA"},
        {"STATUS": "EM ABERTO", "MÊS": "MAR/2026", "DATA": "2026-03-25", "LANÇAMENTO": "PARCELA EMPRÉSTIMO CAPITAL DE GIRO", "RAZÃO SOCIAL": "BANCO BRADESCO S/A", "CPF/CNPJ": "60.746.948/0001-12", "VALOR (R$)": 15400.0, "CÓD GRUPO": "GRP-08", "GRUPO": "BANCOS / FINANCIAMENTOS", "CÓD. NATUREZA": "NAT-110", "DESCRIÇÃO NATUREZA": "Empréstimo Bancário", "TIPO": "FIXA"},
    ]
    df_base = normalize_base_dataframe(pd.DataFrame(base_data))

    # 2. DESPESA FIXA BOARD
    board_data = [
        {"Categoria": "PESSOAL / TERCEIROS", "Descrição": "Folha de Pagamento CLT, PJ e Honorários de Diretoria", "Meta Mensal (R$)": 35000.0, "Realizado Médio (R$)": 28500.0, "Observação": "Dentro do orçamento estabelecido pelo Board."},
        {"Categoria": "ENCARGOS SOCIAIS", "Descrição": "FGTS, INSS Patronal e Provisão de Férias/13º", "Meta Mensal (R$)": 16000.0, "Realizado Médio (R$)": 14425.0, "Observação": "Varia de acordo com horas extras e comissões."},
        {"Categoria": "BENEFÍCIOS", "Descrição": "Vale Refeição, Plano de Saúde Bradesco e Vale Transporte", "Meta Mensal (R$)": 12000.0, "Realizado Médio (R$)": 11400.0, "Observação": "Alinhado ao headcount atual."},
        {"Categoria": "DESPESAS IMOBILIÁRIAS", "Descrição": "Aluguel Predial, IPTU e Taxa Condominial Sede", "Meta Mensal (R$)": 19000.0, "Realizado Médio (R$)": 18500.0, "Observação": "Contrato reajustado pelo IPCA anualmente em Outubro."},
        {"Categoria": "T.I. E SOFTWARE", "Descrição": "Licenças de ERP (Totvs), Servidores AWS e Segurança", "Meta Mensal (R$)": 11000.0, "Realizado Médio (R$)": 9800.0, "Observação": "Meta prevê folga para novos acessos no ERP."},
        {"Categoria": "DESPESAS COM MANUTENÇÃO", "Descrição": "Manutenção Preventiva de Equipamentos, Ar e Elevadores", "Meta Mensal (R$)": 5000.0, "Realizado Médio (R$)": 5725.0, "Observação": "⚠️ Realizado acima da meta devido a falhas pontuais."},
    ]
    df_board = normalize_board_dataframe(pd.DataFrame(board_data))

    # 3. BANCOS
    bancos_data = [
        {"Banco": "BANCO BRADESCO S/A", "Tipo de Operação": "EMPRÉSTIMO", "Contrato": "CTR-GIRO-2024-8891", "Saldo Devedor (R$)": 354200.0, "Valor Parcela (R$)": 15400.0, "Parcelas Restantes": 23, "Dia Vencimento": 25, "Taxa de Juros": "1.45% a.m. (CDI + 2.8% a.a.)", "Status": "EM ABERTO"},
        {"Banco": "BANCO SANTANDER BRASIL S/A", "Tipo de Operação": "CONSÓRCIO", "Contrato": "CONSORCIO-IMO-092", "Saldo Devedor (R$)": 980000.0, "Valor Parcela (R$)": 8250.0, "Parcelas Restantes": 142, "Dia Vencimento": 30, "Taxa de Juros": "Taxa de Adm. 0.18% a.m.", "Status": "EM ABERTO"},
        {"Banco": "BANCO ITAU UNIBANCO S/A", "Tipo de Operação": "FINANCIAMENTO", "Contrato": "FIN-FROTA-2023-412", "Saldo Devedor (R$)": 62400.0, "Valor Parcela (R$)": 5200.0, "Parcelas Restantes": 12, "Dia Vencimento": 18, "Taxa de Juros": "1.20% a.m. pré-fixada", "Status": "EM ABERTO"},
        {"Banco": "BANCO SAFRA S/A", "Tipo de Operação": "EMPRÉSTIMO", "Contrato": "GIRO-EXP-2022-110", "Saldo Devedor (R$)": 0.0, "Valor Parcela (R$)": 0.0, "Parcelas Restantes": 0, "Dia Vencimento": 10, "Taxa de Juros": "Quitado em Dez/2025", "Status": "PAGO"},
    ]
    df_bancos = normalize_bancos_dataframe(pd.DataFrame(bancos_data))

    return df_base, df_board, df_bancos


# --------------------------------------------------------------------------------------
# FUNÇÃO PARA LEITURA DE EXCEL (0. EXTRATO GERAL.xlsx)
# --------------------------------------------------------------------------------------
def load_excel_file(uploaded_file):
    try:
        excel_file = pd.ExcelFile(uploaded_file)
        
        # 1. BASE
        base_sheet = None
        for s in excel_file.sheet_names:
            s_clean = clean_col_name(s)
            if "BASE" in s_clean or "EXTRATO" in s_clean:
                base_sheet = s
                break
        if not base_sheet:
            base_sheet = excel_file.sheet_names[0]
        df_base = pd.read_excel(excel_file, sheet_name=base_sheet)
        df_base = normalize_base_dataframe(df_base)

        # 2. DESPESA FIXA BOARD
        df_board = pd.DataFrame()
        for s in excel_file.sheet_names:
            s_clean = clean_col_name(s)
            if "BOARD" in s_clean or "FIXA" in s_clean:
                df_board = pd.read_excel(excel_file, sheet_name=s)
                break
        df_board = normalize_board_dataframe(df_board)

        # 3. BANCOS
        df_bancos = pd.DataFrame()
        for s in excel_file.sheet_names:
            s_clean = clean_col_name(s)
            if "BANCO" in s_clean or "PASSIVO" in s_clean:
                df_bancos = pd.read_excel(excel_file, sheet_name=s)
                break
        df_bancos = normalize_bancos_dataframe(df_bancos)

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
    if df is None or df.empty:
        return pd.DataFrame()

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
    if df is None or df.empty or 'MÊS' not in df.columns or 'RAZÃO SOCIAL' not in df.columns:
        return pd.DataFrame()

    fornecedor_meses = df.groupby('RAZÃO SOCIAL')['MÊS'].nunique()
    fornecedores_recorrentes = fornecedor_meses[fornecedor_meses >= 2].index.tolist()

    df_mes = df[df['MÊS'] == mes_analise]
    fornecedores_no_mes = set(df_mes['RAZÃO SOCIAL'].unique())

    alertas = []
    for f in fornecedores_recorrentes:
        if f not in fornecedores_no_mes and f not in ["NAN", "", "NÃO IDENTIFICADO"]:
            subset_f = df[df['RAZÃO SOCIAL'] == f]
            media_valor = subset_f['VALOR (R$)'].mean() if not subset_f.empty else 0.0
            categoria = subset_f['GRUPO'].iloc[0] if not subset_f.empty else "DIVERSOS"
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

# Garantia de integridade pós-carga
df_base = normalize_base_dataframe(df_base)
df_board = normalize_board_dataframe(df_board)
df_bancos = normalize_bancos_dataframe(df_bancos)

# Filtros Globais Seguros
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Filtros Globais")

# 1. Filtro Mês
meses_unicos = [str(m).strip() for m in df_base['MÊS'].dropna().unique() if str(m).strip()]
meses_disponiveis = ["TODOS"] + sorted(list(set(meses_unicos)))
filtro_mes = st.sidebar.selectbox("Mês de Competência", meses_disponiveis)

# 2. Filtro Status
status_unicos = [str(s).strip() for s in df_base['STATUS'].dropna().unique() if str(s).strip()]
status_disponiveis = ["TODOS"] + sorted(list(set(status_unicos)))
filtro_status = st.sidebar.selectbox("Status de Pagamento", status_disponiveis)

# 3. Filtro Grupo
grupos_unicos = [str(g).strip() for g in df_base['GRUPO'].dropna().unique() if str(g).strip()]
grupos_disponiveis = ["TODOS"] + sorted(list(set(grupos_unicos)))
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
total_volume = df_filtrado['VALOR (R$)'].sum() if 'VALOR (R$)' in df_filtrado.columns else 0.0
total_linhas = len(df_filtrado)
abertos_volume = df_filtrado[df_filtrado['STATUS'] == 'EM ABERTO']['VALOR (R$)'].sum() if 'VALOR (R$)' in df_filtrado.columns else 0.0
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
    status_base_txt = "Base Demonstração (0. EXTRATO GERAL)" if is_demo else (uploaded_file.name if uploaded_file else "Manual")
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

        total_drenos = df_drenos['VALOR (R$)'].sum() if not df_drenos.empty else 0.0
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

        if not df_drenos.empty:
            cols_show = [c for c in ['DATA', 'STATUS', 'LANÇAMENTO', 'RAZÃO SOCIAL', 'VALOR (R$)', 'GRUPO'] if c in df_drenos.columns]
            st.dataframe(df_drenos[cols_show], use_container_width=True)
        else:
            st.success("Nenhum dreno financeiro identificado nos filtros atuais.")

    with subtab_descascamento:
        st.markdown("#### Distribuição Diária de Pagamentos (Prevenção de Picos de Saída)")
        if not df_filtrado.empty and 'DATA' in df_filtrado.columns:
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
        else:
            st.info("Sem dados diários para exibição.")

    with subtab_passivos:
        st.markdown("#### Contratos Bancários, Financiamentos e Consórcios (Aba BANCOS)")
        if df_bancos.empty:
            st.warning("Nenhum registro encontrado na aba BANCOS.")
        else:
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                saldo_bancos = df_bancos['Saldo Devedor (R$)'].sum() if 'Saldo Devedor (R$)' in df_bancos.columns else 0.0
                st.metric("Saldo Devedor Total", f"R$ {saldo_bancos:,.2f}")
            with col_b2:
                parcela_bancos = df_bancos['Valor Parcela (R$)'].sum() if 'Valor Parcela (R$)' in df_bancos.columns else 0.0
                st.metric("Compromisso Mensal (Parcelas)", f"R$ {parcela_bancos:,.2f}")

            st.dataframe(df_bancos, use_container_width=True)


# --------------------------------------------------------------------------------------
# TAB 2: REDUÇÃO DE DESPESAS
# --------------------------------------------------------------------------------------
with tab_despesas:
    st.markdown("### 📉 Redução & Eficiência de Despesas")

    sub_abc, sub_dup, sub_board = st.tabs(["Curva ABC (Pareto)", "Duplicidades & Anomalias", "Metas Board vs Realizado"])

    with sub_abc:
        st.markdown("#### Curva de Pareto dos Maiores Credores")
        if not df_filtrado.empty and 'RAZÃO SOCIAL' in df_filtrado.columns and 'VALOR (R$)' in df_filtrado.columns:
            df_fornecedores = df_filtrado.groupby('RAZÃO SOCIAL')['VALOR (R$)'].sum().reset_index()
            df_fornecedores.sort_values(by='VALOR (R$)', ascending=False, inplace=True)
            total_desp = df_fornecedores['VALOR (R$)'].sum()
            if total_desp > 0:
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
            else:
                st.info("Sem valores para calcular Curva ABC.")
        else:
            st.info("Sem dados para análise de fornecedores.")

    with sub_dup:
        st.markdown("#### Detecção de Pagamentos Duplicados / Idênticos")
        st.info("Varredura de lançamentos no mesmo mês, mesmo credor e com o mesmo valor exato.")

        if not df_filtrado.empty:
            dup_cols = [c for c in ['MÊS', 'RAZÃO SOCIAL', 'VALOR (R$)'] if c in df_filtrado.columns]
            if len(dup_cols) == 3:
                df_dup = df_filtrado[df_filtrado.duplicated(subset=dup_cols, keep=False)].copy()
                if df_dup.empty:
                    st.success("✅ Nenhuma duplicidade identificada!")
                else:
                    st.warning(f"⚠️ {len(df_dup)} lançamentos potencialmente duplicados encontrados.")
                    st.dataframe(df_dup.sort_values(by=['RAZÃO SOCIAL', 'VALOR (R$)']), use_container_width=True)
            else:
                st.info("Colunas insuficientes para checagem de duplicidade.")
        else:
            st.info("Nenhum dado selecionado.")

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

    sub_matriz, sub_lixeira, sub_sem_cad = st.tabs([
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

        total_lix = df_lixeira['VALOR (R$)'].sum() if not df_lixeira.empty else 0.0
        st.metric("Total em Contas Genéricas", f"R$ {total_lix:,.2f}", f"{len(df_lixeira)} itens")
        if not df_lixeira.empty:
            cols_lix = [c for c in ['DATA', 'LANÇAMENTO', 'RAZÃO SOCIAL', 'VALOR (R$)', 'GRUPO'] if c in df_lixeira.columns]
            st.dataframe(df_lixeira[cols_lix], use_container_width=True)

    with sub_sem_cad:
        st.markdown("#### Pagamentos sem CPF/CNPJ ou Razão Social")
        df_sem_cad = df_filtrado[
            (df_filtrado['CPF/CNPJ'].isna()) | (df_filtrado['CPF/CNPJ'].astype(str).str.strip() == "") |
            (df_filtrado['RAZÃO SOCIAL'].astype(str).str.upper().isin(["NAN", "NULL", "", "NÃO IDENTIFICADO"]))
        ]
        total_sem = df_sem_cad['VALOR (R$)'].sum() if not df_sem_cad.empty else 0.0
        st.metric("Risco Fiscal (Sem Cadastro)", f"R$ {total_sem:,.2f}", f"{len(df_sem_cad)} itens")
        if not df_sem_cad.empty:
            cols_sem = [c for c in ['DATA', 'LANÇAMENTO', 'RAZÃO SOCIAL', 'CPF/CNPJ', 'VALOR (R$)'] if c in df_sem_cad.columns]
            st.dataframe(df_sem_cad[cols_sem], use_container_width=True)


# --------------------------------------------------------------------------------------
# TAB 4: PROVISIONAMENTO PREDITIVO
# --------------------------------------------------------------------------------------
with tab_provisao:
    st.markdown("### ⏰ Necessidade de Provisionamento Preditivo")

    opcoes_meses = [m for m in meses_disponiveis if m != "TODOS"]
    if not opcoes_meses:
        opcoes_meses = ["TODOS"]

    idx_sel = len(opcoes_meses) - 1 if len(opcoes_meses) > 0 else 0
    mes_corte = st.selectbox(
        "Selecione o Mês para Avaliar Provisões Ausentes",
        opcoes_meses,
        index=idx_sel
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

                    drenos_val = df_drenos['VALOR (R$)'].sum() if 'df_drenos' in locals() and not df_drenos.empty else 0.0
                    lixeira_val = df_lixeira['VALOR (R$)'].sum() if 'df_lixeira' in locals() and not df_lixeira.empty else 0.0
                    sem_cad_val = df_sem_cad['VALOR (R$)'].sum() if 'df_sem_cad' in locals() and not df_sem_cad.empty else 0.0
                    ajustes_len = len(df_ajustes) if 'df_ajustes' in locals() and not df_ajustes.empty else 0

                    prompt = f"""
Você é um Auditor e Perito em Controladoria Financeira Sênior (CFO / Diretor de Auditoria).
Analise os dados sumarizados da empresa referentes ao relatório '0. EXTRATO GERAL.xlsx' e elabore um PARECER EXECUTIVO DE CONTROLADORIA E AUDITORIA.

MÉTRICAS DO RELATÓRIO:
- Volume Total Analisado: R$ {total_volume:,.2f} ({total_linhas} lançamentos)
- Despesas em Aberto: R$ {abertos_volume:,.2f}
- Drenos Financeiros (Tarifas/Juros/IOF): R$ {drenos_val:,.2f}
- Saldo Devedor Bancário: R$ {passivo_bancos_total:,.2f}
- Contas Lixeira ('OUTROS'/'DIVERSOS'): R$ {lixeira_val:,.2f}
- Despesas sem CNPJ/Razão Social: R$ {sem_cad_val:,.2f}
- Inconsistências de Natureza Contábil: {ajustes_len} lançamentos identificados

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
