# Exportação Completa de Vulnerabilidades (Histórico Total) ☆彡

Checkmarx One: Exportação Completa de Vulnerabilidades

## Visão Geral

Este projeto disponibiliza um script em **Python** para extração do **histórico completo de vulnerabilidades** do ambiente **Checkmarx One (CxOne)** utilizando **APIs oficiais**.

Diferentemente da interface gráfica (UI), que impõe limitações temporais (ex.: 365 dias), este script acessa **todo o histórico real existente no tenant**, incluindo scans antigos e vulnerabilidades históricas, tornando-o ideal para:

- Auditorias
- Compliance
- Análises históricas
- Relatórios corporativos offline

---

## Objetivo

- Extrair **todas as vulnerabilidades** do tenant
- Percorrer **todos os projetos e scans**
- Acessar o **histórico completo**, sem cortes de data
- Obter informações como:
  - `firstFoundAt`
  - `lastFoundAt`
- Gerar relatórios reutilizáveis em **CSV** e **Excel**

---

## Arquitetura Utilizada

### Serviços do Checkmarx One

| Serviço | Endpoint |
|-------|---------|
| AST API (Projects / Scans / Results) | `https://<region>.ast.checkmarx.net` |
| IAM (OAuth2) | `https://<region>.iam.checkmarx.net` |

**Exemplos de região:** `eu`, `us`, `us2`, `eu2`

> **Importante**  
> O IAM é **regional**. AST e IAM devem pertencer à **mesma região**, caso contrário ocorrerá erro de autenticação (404 / 401).

---

## Autenticação

O script utiliza **OAuth2 – Client Credentials**.

### Credenciais Necessárias

- `TENANT_NAME`
- `CLIENT_ID`
- `CLIENT_SECRET`

### Endpoint de Autenticação

```
POST /auth/realms/{TENANT}/protocol/openid-connect/token
```

### Header Utilizado

```
Authorization: Bearer <access_token>
```

O token é:
- Renovado automaticamente
- Reutilizado durante a execução
- Tratado com retry em falhas transitórias

---

## Funcionalidades

- Autenticação automática via OAuth2
- Renovação automática de token
- Retry automático (429 / 5xx)
- Paginação real (`limit + offset`)
- Coleta completa de:
  - Projetos
  - Scans
  - Vulnerabilidades (Results)
- Exportação em **CSV** e **Excel**
- Execução sem limite de data

---

## Estrutura dos Dados Exportados

Cada linha do relatório representa **uma vulnerabilidade encontrada em um scan**, contendo no mínimo:

- Project Name
- Project ID
- Scan ID
- Scan Type (SAST / SCA / IaC / KICS)
- Severity
- Vulnerability Type
- Result ID
- First Found At
- Last Found At
- Scan Date

---

## Sobre o Histórico (Muito Importante)

- **Não existe filtro de data no script**
- Todos os scans existentes no tenant são processados
- O limite de 365 dias existe **apenas na UI**
- A API **não aplica corte temporal**

> Isso garante acesso ao **histórico completo e real** das vulnerabilidades.

---

## Pré-requisitos

### Ambiente

- Python **3.9 ou superior**

### Bibliotecas Python

- `requests`
- `pandas`
- `openpyxl`

### Instalação

```bash
pip install requests pandas openpyxl
```

---

## Configuração

Edite diretamente no script os seguintes valores:

```python
TENANT_NAME   = "SEU_TENANT"
CLIENT_ID     = "SEU_CLIENT_ID"
CLIENT_SECRET = "SEU_CLIENT_SECRET"

AST_API_BASE  = "https://eu.ast.checkmarx.net"
IAM_BASE      = "https://eu.iam.checkmarx.net"
```

Certifique-se de que **AST e IAM pertencem à mesma região**.

---

## Execução

Execute o script com:

```bash
python export_cxone_full_history.py
```

---

## Arquivos Gerados

Ao final da execução, os arquivos serão gerados com timestamp:

- `cxone_vulnerabilities_full_history_YYYYMMDD_HHMMSS.xlsx`
- `cxone_vulnerabilities_full_history_YYYYMMDD_HHMMSS.csv`

Esses arquivos podem ser utilizados diretamente em:
- Excel
- Power BI
- Ferramentas de BI
- Auditorias externas

---

## Status

- Solução validada  
- Utiliza apenas APIs oficiais  
- Sem limitação temporal  
- Pronta para uso corporativo e auditoria  

---

☆彡
