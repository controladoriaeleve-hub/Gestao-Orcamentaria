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
# UTILITÁRIOS DE NORMALIZAÇÃO DE DATAFRAMES & LEITURA INTELIGENTE
# --------------------------------------------------------------------------------------
def clean_col_name(col: str) -> str:
    """Remove acentos, espaços extras e converte para maiúsculo."""
    nfkd = unicodedata.normalize('NFKD', str(col))
    cleaned = ''.join([c for c in nfkd if not unicodedata.combining(c)])
    return cleaned.strip().upper()


def fmt_brl(val) -> str:
    """Formata valor estritamente positivo em moeda brasileira R$ 1.234.567,89."""
    if pd.isna(val) or val is None:
        return "R$ 0,00"
    try:
        v = abs(float(val))
        formatted = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {formatted}"
    except:
        return "R$ 0,00"


def clean_valor(val, force_abs: bool = True) -> float:
    """Converte com segurança valores monetários (BR ou US) para float, forçando valor positivo por padrão."""
    if pd.isna(val) or val is None:
        return 0.0
    if isinstance(val, (int, float)):
        res = float(val) if not pd.isna(val) else 0.0
        return abs(res) if force_abs else res
    s = str(val).strip()
    if not s or s in ["-", "--", "nan", "NAN", "null", "NULL", ""]:
        return 0.0
    # Remove símbolos de moeda e espaços
    s = re.sub(r"[R$\s]", "", s)
    # Formato brasileiro com milhar em ponto e decimal em vírgula: "5.214,09" -> "5214.09"
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s and "." not in s:
        s = s.replace(",", ".")
    try:
        res = float(s)
        return abs(res) if force_abs else res
    except:
        m = re.search(r"[-+]?\d*\.?\d+", s)
        res = float(m.group()) if m else 0.0
        return abs(res) if force_abs else res


MES_NOMES = {
    1: "01 - JAN", 2: "02 - FEV", 3: "03 - MAR", 4: "04 - ABR",
    5: "05 - MAI", 6: "06 - JUN", 7: "07 - JUL", 8: "08 - AGO",
    9: "09 - SET", 10: "10 - OUT", 11: "11 - NOV", 12: "12 - DEZ",
    "1": "01 - JAN", "2": "02 - FEV", "3": "03 - MAR", "4": "04 - ABR",
    "5": "05 - MAI", "6": "06 - JUN", "7": "07 - JUL", "8": "08 - AGO",
    "9": "09 - SET", "10": "10 - OUT", "11": "11 - NOV", "12": "12 - DEZ",
    "01": "01 - JAN", "02": "02 - FEV", "03": "03 - MAR", "04": "04 - ABR",
    "05": "05 - MAI", "06": "06 - JUN", "07": "07 - JUL", "08": "08 - AGO",
    "09": "09 - SET",
}


def format_mes_val(val, data_val=None) -> str:
    """Formata mês numérico ou textual para exibição consistente."""
    if pd.isna(val) or val is None:
        s = ""
    else:
        s = str(val).strip()

    if re.match(r"^\d+\.0$", s):
        s = s.split(".")[0]

    if s in MES_NOMES:
        if data_val and not pd.isna(data_val):
            try:
                dt = pd.to_datetime(data_val, errors='coerce')
                if pd.notna(dt):
                    return f"{MES_NOMES[s].split(' - ')[1]}/{dt.year}"
            except:
                pass
        return MES_NOMES[s]

    if not s or s.upper() in ["NAN", "NONE", "NULL"]:
        if data_val and not pd.isna(data_val):
            try:
                dt = pd.to_datetime(data_val, errors='coerce')
                if pd.notna(dt):
                    return dt.strftime('%b/%Y').upper()
            except:
                pass
        return "GERAL"

    return s.upper()


def safe_series(df: pd.DataFrame, col_name: str, default_val=None) -> pd.Series:
    """
    Retorna com garantia uma pd.Series 1D mesmo se houver colunas duplicadas
    com o mesmo nome ou se a coluna não existir no DataFrame.
    """
    if df is None or df.empty or col_name not in df.columns:
        idx = df.index if df is not None and not df.empty else [0]
        return pd.Series([default_val] * len(idx), index=idx)
    col_obj = df[col_name]
    if isinstance(col_obj, pd.DataFrame):
        # Múltiplas colunas com o mesmo nome: pega a primeira coluna
        col_obj = col_obj.iloc[:, 0]
    return col_obj


def find_sheet_header_and_read(excel_file, sheet_name: str) -> pd.DataFrame:
    """
    Localiza dinamicamente a linha de cabeçalho do Excel e retorna o DataFrame
    limpo, mesmo se a linha 1 for vazia ou contiver banners/cabeçalhos deslocados.
    """
    try:
        df_raw = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
        if df_raw.empty:
            return pd.DataFrame()

        keywords = [
            "STATUS", "MES", "DATA", "LANCAMENTO", "HISTORICO",
            "RAZAO SOCIAL", "RAZAO", "FORNECEDOR", "CREDOR",
            "CPF", "CNPJ", "VALOR", "GRUPO", "NATUREZA", "TIPO",
            "BANCO", "SALDO", "PARCELA", "CATEGORIA", "DESCRICAO", "META"
        ]

        header_idx = 0
        best_score = 0

        # Analisa até as 25 primeiras linhas para encontrar a linha do cabeçalho
        for r_idx in range(min(25, len(df_raw))):
            row_vals = df_raw.iloc[r_idx].dropna().tolist()
            score = 0
            for val in row_vals:
                norm = clean_col_name(str(val))
                for kw in keywords:
                    if kw in norm:
                        score += 1
                        break
            if score > best_score:
                best_score = score
                header_idx = r_idx

        if best_score >= 2:
            df = pd.read_excel(excel_file, sheet_name=sheet_name, header=header_idx)
        else:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)

        # Remove colunas e linhas totalmente vazias (ex: Coluna A em branco no Excel)
        df = df.dropna(how="all", axis=1)
        df = df.dropna(how="all", axis=0)

        # Limpar espaços nos nomes das colunas e deduplicar
        df.columns = [str(c).strip() for c in df.columns]
        df = df.loc[:, ~df.columns.duplicated(keep="first")].copy()

        return df
    except Exception:
        try:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            df = df.dropna(how="all", axis=1).dropna(how="all", axis=0)
            df.columns = [str(c).strip() for c in df.columns]
            df = df.loc[:, ~df.columns.duplicated(keep="first")].copy()
            return df
        except:
            return pd.DataFrame()


def normalize_base_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Garante mapeamento 1-para-1 de colunas e dados numéricos/textuais da BASE,
    construindo um novo DataFrame estritamente estruturado e sem duplicidades.
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=[
            "STATUS", "MÊS", "DATA", "LANÇAMENTO", "RAZÃO SOCIAL",
            "CPF/CNPJ", "VALOR (R$)", "CÓD GRUPO", "GRUPO",
            "CÓD. NATUREZA", "DESCRIÇÃO NATUREZA", "TIPO"
        ])

    # Remover colunas duplicadas
    df = df.loc[:, ~df.columns.duplicated(keep="first")].copy()
    cols_clean = {c: clean_col_name(str(c)) for c in df.columns}

    def pick_col(exact_list, contains_list=None, exclude=None):
        exclude = exclude or set()
        for exact in exact_list:
            ex_norm = clean_col_name(exact)
            for orig, norm in cols_clean.items():
                if norm == ex_norm and orig not in exclude:
                    return orig
        if contains_list:
            for cont in contains_list:
                cont_norm = clean_col_name(cont)
                for orig, norm in cols_clean.items():
                    if cont_norm in norm and orig not in exclude:
                        return orig
        return None

    used = set()

    # 1. VALOR
    col_valor = pick_col(["VALOR (R$)", "VALOR R$", "VALOR LIQUIDO", "VALOR", "TOTAL", "VALOR PAGO"], ["VALOR", "TOTAL", "LIQUIDO"], used)
    if col_valor: used.add(col_valor)

    # 2. STATUS
    col_status = pick_col(["STATUS", "SITUACAO", "ESTADO", "SITUAÇÃO"], ["STATUS", "SITUAC"], used)
    if col_status: used.add(col_status)

    # 3. DATA
    col_data = pick_col(["DATA", "DATA PAGAMENTO", "VENCIMENTO", "DT PAGTO", "DATA VENCIMENTO", "PAGAMENTO"], ["DATA", "VENCIMENTO", "PAGTO"], used)
    if col_data: used.add(col_data)

    # 4. MÊS
    col_mes = pick_col(["MES", "MÊS", "COMPETENCIA", "PERIODO", "COMPETÊNCIA", "MES ANO", "MES/ANO"], ["MES"], used)
    if col_mes: used.add(col_mes)

    # 5. CÓD GRUPO (antes de GRUPO)
    col_cod_grupo = pick_col(["COD GRUPO", "CÓD GRUPO", "COD. GRUPO", "CODIGO GRUPO"], ["COD GRUPO", "COD. GRUPO"], used)
    if col_cod_grupo: used.add(col_cod_grupo)

    # 6. GRUPO
    col_grupo = pick_col(["GRUPO", "CENTRO DE CUSTO", "CATEGORIA", "CLASSIFICACAO", "GRUPO DESPESA"], ["GRUPO", "CENTRO"], used)
    if col_grupo: used.add(col_grupo)

    # 7. CÓD NATUREZA (antes de DESCRIÇÃO NATUREZA)
    col_cod_nat = pick_col(["COD NATUREZA", "CÓD. NATUREZA", "COD. NATUREZA", "CODIGO NATUREZA"], ["COD NATUREZA", "COD. NAT"], used)
    if col_cod_nat: used.add(col_cod_nat)

    # 8. DESCRIÇÃO NATUREZA
    col_desc_nat = pick_col(["DESCRICAO NATUREZA", "DESCRIÇÃO NATUREZA", "NATUREZA", "CONTA CONTABIL"], ["NATUREZA", "CONTA"], used)
    if col_desc_nat: used_cols_set = used.add(col_desc_nat)

    # 9. RAZÃO SOCIAL
    col_razao = pick_col(["RAZAO SOCIAL", "RAZÃO SOCIAL", "FORNECEDOR", "CREDOR", "BENEFICIARIO", "CLIENTE", "FAVORECIDO"], ["RAZAO", "FORNECEDOR", "CREDOR", "FAVORECIDO"], used)
    if col_razao: used.add(col_razao)

    # 10. LANÇAMENTO
    col_lanc = pick_col(["LANCAMENTO", "LANÇAMENTO", "HISTORICO", "HISTÓRICO", "DESCRICAO", "DESCRICAO LANCAMENTO"], ["LANCAMENTO", "HISTOR"], used)
    if col_lanc: used.add(col_lanc)

    # 11. CPF/CNPJ
    col_cpf = pick_col(["CPF/CNPJ", "CNPJ", "CPF", "DOC", "DOCUMENTO"], ["CNPJ", "CPF", "DOCUMENTO"], used)
    if col_cpf: used.add(col_cpf)

    # 12. TIPO
    col_tipo = pick_col(["TIPO", "TIPO DESPESA", "TIPO CUSTO"], ["TIPO"], used)
    if col_tipo: used.add(col_tipo)

    # Construção de novo DataFrame estritamente estruturado
    out = pd.DataFrame(index=df.index)

    # Valor
    s_val = safe_series(df, col_valor, 0.0) if col_valor else pd.Series(0.0, index=df.index)
    out["VALOR (R$)"] = s_val.apply(clean_valor)

    # Status
    def clean_status_val(v):
        s = str(v).strip().upper()
        if "ABERTO" in s:
            return "EM ABERTO"
        if "PAGO" in s or "LIQUIDADO" in s or "BAIXADO" in s:
            return "PAGO"
        if "CANCEL" in s:
            return "CANCELADO"
        return s if s and s != "NAN" else "PAGO"
    s_status = safe_series(df, col_status, "PAGO") if col_status else pd.Series("PAGO", index=df.index)
    out["STATUS"] = s_status.apply(clean_status_val)

    # Data
    s_data = safe_series(df, col_data, "2026-01-01") if col_data else pd.Series("2026-01-01", index=df.index)
    out["DATA"] = s_data.astype(str).str.strip()

    # Mês
    if col_mes:
        s_mes = safe_series(df, col_mes, "")
        out["MÊS"] = [format_mes_val(m, d) for m, d in zip(s_mes, out["DATA"])]
    else:
        out["MÊS"] = [format_mes_val(None, d) for d in out["DATA"]]

    # Lançamento
    s_lanc = safe_series(df, col_lanc, "Sem histórico") if col_lanc else pd.Series("Sem histórico", index=df.index)
    out["LANÇAMENTO"] = s_lanc.fillna("Sem histórico").astype(str).str.strip()

    # Razão Social
    s_razao = safe_series(df, col_razao, "NÃO IDENTIFICADO") if col_razao else pd.Series("NÃO IDENTIFICADO", index=df.index)
    razao_clean = s_razao.fillna("NÃO IDENTIFICADO").astype(str).str.strip()
    out["RAZÃO SOCIAL"] = razao_clean.replace({"": "NÃO IDENTIFICADO", "nan": "NÃO IDENTIFICADO", "NAN": "NÃO IDENTIFICADO", "-": "NÃO IDENTIFICADO", "None": "NÃO IDENTIFICADO"})

    # CPF/CNPJ
    s_cpf = safe_series(df, col_cpf, "") if col_cpf else pd.Series("", index=df.index)
    out["CPF/CNPJ"] = s_cpf.fillna("").astype(str).str.strip()

    # Cód Grupo
    s_cg = safe_series(df, col_cod_grupo, "") if col_cod_grupo else pd.Series("", index=df.index)
    out["CÓD GRUPO"] = s_cg.fillna("").astype(str).str.strip()

    # Grupo
    s_grupo = safe_series(df, col_grupo, "OUTROS") if col_grupo else pd.Series("OUTROS", index=df.index)
    out["GRUPO"] = s_grupo.fillna("OUTROS").astype(str).str.strip().str.upper()

    # Cód Natureza
    s_cn = safe_series(df, col_cod_nat, "") if col_cod_nat else pd.Series("", index=df.index)
    out["CÓD. NATUREZA"] = s_cn.fillna("").astype(str).str.strip()

    # Descrição Natureza
    s_dn = safe_series(df, col_desc_nat, "") if col_desc_nat else pd.Series("", index=df.index)
    out["DESCRIÇÃO NATUREZA"] = s_dn.fillna("").astype(str).str.strip()

    # Tipo
    s_tipo = safe_series(df, col_tipo, "VARIÁVEL") if col_tipo else pd.Series("VARIÁVEL", index=df.index)
    out["TIPO"] = s_tipo.fillna("VARIÁVEL").astype(str).str.strip().str.upper()

    return out


def normalize_board_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza o dataframe da aba DESPESA FIXA BOARD sem risco de duplicidade."""
    if df is None or df.empty:
        return pd.DataFrame(columns=["Categoria", "Descrição", "Meta Mensal (R$)", "Realizado Médio (R$)", "Observação"])

    df = df.loc[:, ~df.columns.duplicated(keep="first")].copy()
    cols_clean = {c: clean_col_name(str(c)) for c in df.columns}

    def pick_col(exact_list, contains_list=None):
        for exact in exact_list:
            ex_norm = clean_col_name(exact)
            for orig, norm in cols_clean.items():
                if norm == ex_norm:
                    return orig
        if contains_list:
            for cont in contains_list:
                cont_norm = clean_col_name(cont)
                for orig, norm in cols_clean.items():
                    if cont_norm in norm:
                        return orig
        return None

    c_cat = pick_col(["CATEGORIA", "GRUPO"], ["CATEGORIA", "GRUPO"])
    c_desc = pick_col(["DESCRICAO", "DESCRIÇÃO", "ITEM", "DETALHE"], ["DESCRICAO", "ITEM"])
    c_meta = pick_col(["META MENSAL (R$)", "META", "ORCADO", "ORÇADO", "PREVISTO"], ["META", "ORCADO", "PREVISTO"])
    c_real = pick_col(["REALIZADO MEDIO (R$)", "REALIZADO", "MEDIO", "ATUAL", "GASTO"], ["REALIZADO", "MEDIO", "GASTO"])
    c_obs = pick_col(["OBSERVACAO", "OBSERVAÇÃO", "NOTA", "STATUS"], ["OBSERVACAO", "NOTA"])

    out = pd.DataFrame(index=df.index)
    s_cat = safe_series(df, c_cat, "") if c_cat else pd.Series("", index=df.index)
    out["Categoria"] = s_cat.fillna("").astype(str).str.strip()

    s_desc = safe_series(df, c_desc, "") if c_desc else pd.Series("", index=df.index)
    out["Descrição"] = s_desc.fillna("").astype(str).str.strip()

    s_meta = safe_series(df, c_meta, 0.0) if c_meta else pd.Series(0.0, index=df.index)
    out["Meta Mensal (R$)"] = s_meta.apply(clean_valor)

    s_real = safe_series(df, c_real, 0.0) if c_real else pd.Series(0.0, index=df.index)
    out["Realizado Médio (R$)"] = s_real.apply(clean_valor)

    s_obs = safe_series(df, c_obs, "") if c_obs else pd.Series("", index=df.index)
    out["Observação"] = s_obs.fillna("").astype(str).str.strip()

    return out


def normalize_bancos_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza o dataframe da aba BANCOS com garantia de tipos e sem duplicidades."""
    if df is None or df.empty:
        return pd.DataFrame(columns=[
            "Banco", "Tipo de Operação", "Contrato", "Saldo Devedor (R$)",
            "Valor Parcela (R$)", "Parcelas Restantes", "Dia Vencimento", "Taxa de Juros", "Status"
        ])

    df = df.loc[:, ~df.columns.duplicated(keep="first")].copy()
    cols_clean = {c: clean_col_name(str(c)) for c in df.columns}

    def pick_col(exact_list, contains_list=None):
        for exact in exact_list:
            ex_norm = clean_col_name(exact)
            for orig, norm in cols_clean.items():
                if norm == ex_norm:
                    return orig
        if contains_list:
            for cont in contains_list:
                cont_norm = clean_col_name(cont)
                for orig, norm in cols_clean.items():
                    if cont_norm in norm:
                        return orig
        return None

    c_banco = pick_col(["BANCO", "INSTITUICAO", "CREDOR"], ["BANCO", "INSTITU"])
    c_op = pick_col(["TIPO DE OPERACAO", "OPERACAO", "MODALIDADE", "TIPO"], ["OPERACAO", "MODALIDADE"])
    c_ctr = pick_col(["CONTRATO", "NUMERO CONTRATO", "NUMERO"], ["CONTRATO", "NUM"])
    c_saldo = pick_col(["SALDO DEVEDOR (R$)", "SALDO DEVEDOR", "SALDO"], ["SALDO", "DEVEDOR"])
    c_parc = pick_col(["VALOR PARCELA (R$)", "VALOR PARCELA", "PARCELA"], ["PARCELA", "MENSAL"])
    c_rest = pick_col(["PARCELAS RESTANTES", "QTD PARCELAS", "PRAZO"], ["RESTANTE", "QTD", "PRAZO"])
    c_venc = pick_col(["DIA VENCIMENTO", "VENCIMENTO", "DIA"], ["VENCIMENTO", "DIA"])
    c_taxa = pick_col(["TAXA DE JUROS", "TAXA", "JUROS"], ["TAXA", "JUROS"])
    c_status = pick_col(["STATUS", "SITUACAO"], ["STATUS", "SITUAC"])

    out = pd.DataFrame(index=df.index)
    s_banco = safe_series(df, c_banco, "") if c_banco else pd.Series("", index=df.index)
    out["Banco"] = s_banco.fillna("").astype(str).str.strip()

    s_op = safe_series(df, c_op, "EMPRÉSTIMO") if c_op else pd.Series("EMPRÉSTIMO", index=df.index)
    out["Tipo de Operação"] = s_op.fillna("EMPRÉSTIMO").astype(str).str.strip()

    s_ctr = safe_series(df, c_ctr, "") if c_ctr else pd.Series("", index=df.index)
    out["Contrato"] = s_ctr.fillna("").astype(str).str.strip()

    s_saldo = safe_series(df, c_saldo, 0.0) if c_saldo else pd.Series(0.0, index=df.index)
    out["Saldo Devedor (R$)"] = s_saldo.apply(clean_valor)

    s_parc = safe_series(df, c_parc, 0.0) if c_parc else pd.Series(0.0, index=df.index)
    out["Valor Parcela (R$)"] = s_parc.apply(clean_valor)

    s_rest = safe_series(df, c_rest, 0) if c_rest else pd.Series(0, index=df.index)
    out["Parcelas Restantes"] = pd.to_numeric(s_rest, errors="coerce").fillna(0).astype(int)

    s_venc = safe_series(df, c_venc, 10) if c_venc else pd.Series(10, index=df.index)
    out["Dia Vencimento"] = pd.to_numeric(s_venc, errors="coerce").fillna(10).astype(int)

    s_taxa = safe_series(df, c_taxa, "") if c_taxa else pd.Series("", index=df.index)
    out["Taxa de Juros"] = s_taxa.fillna("").astype(str).str.strip()

    s_stat = safe_series(df, c_status, "EM ABERTO") if c_status else pd.Series("EM ABERTO", index=df.index)
    out["Status"] = s_stat.fillna("EM ABERTO").astype(str).str.strip()

    return out


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
        file_name = getattr(uploaded_file, "name", "").lower()

        # Suporte a arquivos CSV diretos
        if file_name.endswith(".csv"):
            try:
                df_raw = pd.read_csv(uploaded_file, sep=None, engine="python")
            except Exception:
                uploaded_file.seek(0)
                df_raw = pd.read_csv(uploaded_file, sep=";")
            
            df_base = normalize_base_dataframe(df_raw)
            df_board = normalize_board_dataframe(pd.DataFrame())
            df_bancos = normalize_bancos_dataframe(pd.DataFrame())
            return df_base, df_board, df_bancos, True, None

        excel_file = pd.ExcelFile(uploaded_file)
        
        # 1. BASE
        base_sheet = None
        for s in excel_file.sheet_names:
            s_clean = clean_col_name(s)
            if "BASE" in s_clean or "EXTRATO" in s_clean or "LANCAMENTO" in s_clean or "GERAL" in s_clean:
                base_sheet = s
                break
        if not base_sheet:
            base_sheet = excel_file.sheet_names[0]
        
        df_base_raw = find_sheet_header_and_read(excel_file, base_sheet)
        df_base = normalize_base_dataframe(df_base_raw)

        # 2. DESPESA FIXA BOARD
        df_board = pd.DataFrame()
        for s in excel_file.sheet_names:
            s_clean = clean_col_name(s)
            if "BOARD" in s_clean or ("FIXA" in s_clean and "DESPESA" in s_clean) or "ORCADO" in s_clean:
                df_board_raw = find_sheet_header_and_read(excel_file, s)
                df_board = normalize_board_dataframe(df_board_raw)
                break
        if df_board.empty:
            df_board = normalize_board_dataframe(df_board)

        # 3. BANCOS
        df_bancos = pd.DataFrame()
        for s in excel_file.sheet_names:
            s_clean = clean_col_name(s)
            if "BANCO" in s_clean or "PASSIVO" in s_clean or "DIVIDA" in s_clean or "EMPRESTIMO" in s_clean:
                df_bancos_raw = find_sheet_header_and_read(excel_file, s)
                df_bancos = normalize_bancos_dataframe(df_bancos_raw)
                break
        if df_bancos.empty:
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
                "Ação Recomendada": f"Provisionar {fmt_brl(media_valor)} no fluxo de caixa operacional."
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
# Garantir que todos os valores de despesa sejam estritamente positivos
if 'VALOR (R$)' in df_filtrado.columns:
    df_filtrado['VALOR (R$)'] = df_filtrado['VALOR (R$)'].apply(lambda v: clean_valor(v, force_abs=True))

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
# CABEÇALHO PRINCIPAL (ESTRUTURA IDENTICA AO PREVIEW)
# --------------------------------------------------------------------------------------
status_badge_text = f"Arquivo: {uploaded_file.name}" if not is_demo and uploaded_file else "Demonstração (0. EXTRATO GERAL)"
status_badge_style = "background:#ecfdf5; color:#065f46; border:1px solid #a7f3d0;" if not is_demo else "background:#fef3c7; color:#92400e; border:1px solid #fde68a;"

st.markdown(f"""
<div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:14px; flex-wrap:wrap; gap:12px;">
    <div style="display:flex; align-items:center; gap:12px;">
        <div style="background:#022c22; color:#10b981; border-radius:10px; width:44px; height:44px; display:flex; align-items:center; justify-content:center; font-size:22px; box-shadow:0 1px 3px rgba(0,0,0,0.1);">🏛️</div>
        <div>
            <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
                <span style="font-size:22px; font-weight:800; color:#0f172a;">Controladoria & Auditoria Financeira</span>
                <span style="{status_badge_style} font-size:11px; padding:2px 8px; border-radius:9999px; font-weight:700;">{status_badge_text}</span>
            </div>
            <div style="font-size:13px; color:#64748b; margin-top:2px;">Saneamento de naturezas de despesas, otimização de fluxo de caixa e diagnóstico de governança</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Banner de Métricas Rápidas
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
total_volume = df_filtrado['VALOR (R$)'].sum() if 'VALOR (R$)' in df_filtrado.columns else 0.0
total_linhas = len(df_filtrado)
abertos_volume = df_filtrado[df_filtrado['STATUS'] == 'EM ABERTO']['VALOR (R$)'].sum() if 'VALOR (R$)' in df_filtrado.columns else 0.0

# Se a aba BANCOS tiver saldo, usa dela; caso contrário, extrai despesas bancárias reais do extrato filtrado
passivo_bancos_total = df_bancos['Saldo Devedor (R$)'].sum() if not df_bancos.empty and 'Saldo Devedor (R$)' in df_bancos.columns else 0.0
if passivo_bancos_total == 0:
    bancos_kws = ["BANCO", "ITAU", "BRADESCO", "SANTANDER", "BRASIL", "SAFRA", "CAIXA", "SICOOB", "SICREDI", "INTER", "TARIFA", "IOF", "FINANC", "EMPRESTIMO"]
    pat_bancos = "|".join(bancos_kws)
    df_bancos_ext = df_filtrado[
        df_filtrado['LANÇAMENTO'].astype(str).str.upper().str.contains(pat_bancos) |
        df_filtrado['RAZÃO SOCIAL'].astype(str).str.upper().str.contains(pat_bancos) |
        df_filtrado['GRUPO'].astype(str).str.upper().str.contains("FINANCEIRA|BANCO")
    ]
    passivo_bancos_total = df_bancos_ext['VALOR (R$)'].sum() if not df_bancos_ext.empty else 0.0
    passivo_label = "Despesas Bancárias (Extrato)"
    passivo_sub = f"{len(df_bancos_ext)} lançamentos bancários"
else:
    passivo_label = "Passivos Bancários (Saldo)"
    passivo_sub = "Contratos na aba BANCOS"

with col_m1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Volume Analisado</div>
        <div class="metric-value">{fmt_brl(total_volume)}</div>
        <div style="font-size:11px; color:#64748b; margin-top:2px;">{total_linhas} lançamentos filtrados</div>
    </div>
    """, unsafe_allow_html=True)

with col_m2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Despesas em Aberto</div>
        <div class="metric-value" style="color:#d97706;">{fmt_brl(abertos_volume)}</div>
        <div style="font-size:11px; color:#d97706; margin-top:2px;">Aguardando liquidação</div>
    </div>
    """, unsafe_allow_html=True)

with col_m3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">{passivo_label}</div>
        <div class="metric-value" style="color:#2563eb;">{fmt_brl(passivo_bancos_total)}</div>
        <div style="font-size:11px; color:#64748b; margin-top:2px;">{passivo_sub}</div>
    </div>
    """, unsafe_allow_html=True)

with col_m4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Status do Arquivo</div>
        <div class="metric-value" style="font-size:16px; color:#059669;">{'✅ Carregado' if not is_demo else '📌 Demo'}</div>
        <div style="font-size:11px; color:#64748b; margin-top:2px;">{uploaded_file.name if uploaded_file else '0. EXTRATO GERAL'}</div>
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
            st.metric("Total de Drenos Financeiros", fmt_brl(total_drenos), f"{len(df_drenos)} saídas")
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
                annotation_text=f"Média Diária: {fmt_brl(media_diaria)}"
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
        st.markdown("#### Contratos Bancários, Financiamentos e Consórcios")
        if df_bancos.empty or df_bancos['Saldo Devedor (R$)'].sum() == 0:
            st.info("💡 A aba BANCOS não possui contratos estruturados nesta planilha. A Controladoria realizou uma varredura automática no próprio extrato para identificar movimentações com instituições financeiras.")
            bancos_kws = ["BANCO", "ITAU", "BRADESCO", "SANTANDER", "BRASIL", "SAFRA", "CAIXA", "SICOOB", "SICREDI", "INTER", "TARIFA", "IOF", "FINANC", "EMPRESTIMO"]
            pat_bancos = "|".join(bancos_kws)
            df_bancos_ext = df_filtrado[
                df_filtrado['LANÇAMENTO'].astype(str).str.upper().str.contains(pat_bancos) |
                df_filtrado['RAZÃO SOCIAL'].astype(str).str.upper().str.contains(pat_bancos) |
                df_filtrado['GRUPO'].astype(str).str.upper().str.contains("FINANCEIRA|BANCO")
            ].copy()
            
            if not df_bancos_ext.empty:
                col_eb1, col_eb2, col_eb3 = st.columns(3)
                with col_eb1:
                    st.metric("Total de Movimentações Bancárias", fmt_brl(df_bancos_ext['VALOR (R$)'].sum()))
                with col_eb2:
                    st.metric("Saídas Identificadas", f"{len(df_bancos_ext)} lançamentos")
                with col_eb3:
                    abertos_banco = df_bancos_ext[df_bancos_ext['STATUS'] == 'EM ABERTO']['VALOR (R$)'].sum()
                    st.metric("Aguardando Liquidação", fmt_brl(abertos_banco))
                
                st.markdown("##### Detalhamento das Despesas Bancárias no Extrato:")
                cols_b_show = [c for c in ['DATA', 'STATUS', 'MÊS', 'LANÇAMENTO', 'RAZÃO SOCIAL', 'VALOR (R$)', 'GRUPO'] if c in df_bancos_ext.columns]
                st.dataframe(df_bancos_ext[cols_b_show], use_container_width=True)
            else:
                st.warning("Nenhum passivo bancário ou despesa financeira identificada no extrato.")
        else:
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                saldo_bancos = df_bancos['Saldo Devedor (R$)'].sum() if 'Saldo Devedor (R$)' in df_bancos.columns else 0.0
                st.metric("Saldo Devedor Total", fmt_brl(saldo_bancos))
            with col_b2:
                parcela_bancos = df_bancos['Valor Parcela (R$)'].sum() if 'Valor Parcela (R$)' in df_bancos.columns else 0.0
                st.metric("Compromisso Mensal (Parcelas)", fmt_brl(parcela_bancos))

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
        st.metric("Total em Contas Genéricas", fmt_brl(total_lix), f"{len(df_lixeira)} itens")
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
        st.metric("Risco Fiscal (Sem Cadastro)", fmt_brl(total_sem), f"{len(df_sem_cad)} itens")
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
        st.error(f"⚠️ Risco de Caixa Oculto: {fmt_brl(total_risco_provisao)} em {len(df_provisao)} despesas recorrentes não faturadas em {mes_corte}.")
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
- Volume Total Analisado: {fmt_brl(total_volume)} ({total_linhas} lançamentos)
- Despesas em Aberto: {fmt_brl(abertos_volume)}
- Drenos Financeiros (Tarifas/Juros/IOF): {fmt_brl(drenos_val)}
- Saldo Devedor Bancário: {fmt_brl(passivo_bancos_total)}
- Contas Lixeira ('OUTROS'/'DIVERSOS'): {fmt_brl(lixeira_val)}
- Despesas sem CNPJ/Razão Social: {fmt_brl(sem_cad_val)}
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
