# Controladoria & Auditoria Financeira ('0. EXTRATO GERAL.xlsx')

Este projeto oferece **duas formas de execução**:

---

## Opção 1: Executar em Python (Streamlit)

Se você deseja executar o script Python para simulações e análise rápida via Streamlit:

### 1. Pré-requisitos
Certifique-se de ter o Python 3.10+ instalado no seu computador.

### 2. Instalar as dependências
Abra o Prompt de Comando (CMD) ou PowerShell na pasta do projeto e execute:

```bash
pip install -r requirements.txt
```
*(Ou instale manualmente: `pip install streamlit pandas openpyxl plotly google-genai python-dotenv`)*

### 3. Executar o aplicativo
No terminal, execute:

```bash
streamlit run app_controladoria.py
```

O Streamlit abrirá automaticamente seu navegador em `http://localhost:8501`.

---

## Opção 2: Executar a Versão Web Completa (React + TypeScript + Node/Express)

O projeto também conta com uma aplicação web interativa em tempo real com backend seguro para chamadas da API Gemini:

### 1. Instalar as dependências do Node.js
Na pasta do projeto, execute no terminal:

```bash
npm install
```

### 2. Iniciar o servidor de desenvolvimento
Execute:

```bash
npm run dev
```

Abra seu navegador em: **`http://localhost:3000`**

---

## Estrutura do Arquivo de Entrada (`0. EXTRATO GERAL.xlsx`)
O aplicativo processa automaticamente as 3 abas principais:
1. **`BASE`**: Lançamentos detalhados com Status, Mês, Data, Lançamento, Razão Social, CPF/CNPJ, Valor (R$), Cód Grupo, Grupo, Cód. Natureza, Descrição Natureza, TIPO.
2. **`DESPESA FIXA BOARD`**: Metas orçamentárias da diretoria e comparativo realizado.
3. **`BANCOS`**: Empréstimos, consórcios, financiamentos, saldo devedor e parcelas.
