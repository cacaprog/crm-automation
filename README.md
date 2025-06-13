# **Lead Manager \- Automação de Captação e Distribuição**

## **Visão Geral**

O **Lead Manager** é um sistema de automação robusto, desenvolvido em Python e projetado para ser implantado na Google Cloud Platform (GCP). Sua principal função é centralizar, processar e distribuir leads de marketing de múltiplas fontes para equipes de vendas, de forma automática e organizada.  
O sistema é capaz de:

- **Capturar leads** de fontes diversas, como **Meta/Facebook Ads** e e-mails de formulários de sites.
- **Centralizar** todos os leads em uma única **Planilha Google (Google Sheets)**.
- **Enriquecer e normalizar** os dados para garantir consistência.
- **Distribuir os leads** entre múltiplas equipes de vendas com base em uma proporção configurável.
- **Integrar com um CRM externo**, enviando os dados dos leads formatados via API.
- **Operar de forma autônoma e agendada**, utilizando o Cloud Scheduler e o Cloud Run.

## **Arquitetura e Fluxo de Trabalho**

O sistema foi projetado para ser serverless, escalável e de baixa manutenção, utilizando os serviços gerenciados do Google Cloud.  
*O fluxo de trabalho completo está descrito nas seções anteriores.*

## **Estrutura do Projeto**

```
.
├── Dockerfile              # NOVO: Define o ambiente de contêiner
├── .dockerignore           # NOVO: Exclui arquivos desnecessários do build
├── main.py                 # Ponto de entrada da aplicação Flask
├── requirements.txt        # Dependências do projeto
├── models/
│   └── lead.py             # Data class que representa um lead
└── core/
    ├── email_processor.py  # Módulo para ler e processar e-mails (IMAP)
    ├── sheet_manager.py    # Módulo para interagir com o Google Sheets
    ├── lead_distributor.py # Módulo com a lógica de distribuição de leads
    └── crm_client.py       # Cliente para a API do CRM

```

## **Containerização com Docker**

Este projeto usa o Docker para criar um ambiente de execução padronizado e portátil.

- **Dockerfile**: Contém todas as instruções para construir a imagem do contêiner, desde a instalação do Python e das dependências até a configuração do servidor de produção gunicorn.
- **.dockerignore**: Garante que arquivos locais de desenvolvimento (como ambientes virtuais) não sejam incluídos na imagem final, mantendo-a otimizada.

## **Guia de Instalação e Deploy (Google Cloud)**

Siga os passos abaixo para configurar e implantar o sistema.

### **Pré-requisitos**

- Uma conta no **Google Cloud Platform** com um projeto ativo.
- **Google Cloud SDK (gcloud CLI)** instalado e autenticado.
- **Docker** instalado e em execução na sua máquina local.

### **1. Configuração da Planilha Google (Google Sheets)**

Crie uma nova Planilha Google e obtenha seu ID (presente na URL: .../spreadsheets/d/SPREADSHEET_ID/...).

A planilha deve conter duas abas (ex: leads e meta), com as colunas necessárias para seus leads. O sistema é flexível e mapeia as colunas pelos nomes no cabeçalho. Como exemplo:

Aba leads:
Timestamp | Name | Email | Phone | Unit | Source | Notes | Status

Aba meta:
Timestamp | Lead ID | Full Name | Email | Phone | Question 1 | Question 2 | Status

### **2. Configuração no Google Cloud**

a. Habilitar APIs


No seu projeto GCP, habilite as seguintes APIs:
- Cloud Run API
- Cloud Scheduler API
- Secret Manager API
- Google Sheets API

b. Conta de Serviço (Service Account)

O Cloud Run utiliza uma conta de serviço para operar. Garanta que ela tenha as seguintes permissões (papéis de IAM):
- `Editor`: Permissão ampla para interagir com os serviços do projeto.
- `Acessor de secrets do Secret Manager`: Para acessar as senhas e tokens.

Conceda acesso à sua conta de serviço na Planilha Google. Copie o e-mail da conta de serviço e compartilhe a planilha com ela, dando permissão de Editor.

c. Secret Manager

Armazene as credenciais sensíveis de forma segura. Crie os seguintes secrets:
- `CRM_API_TOKEN`: Cole o token de autenticação da API do seu CRM.
- `IMAP_PASSWORD`: Cole a senha da conta de e-mail que será lida.

### **3\. Deploy no Cloud Run**

1. **Clone o repositório:**  
  git clone \<url-do-seu-repositorio\>  
  cd \<nome-do-repositorio\>
  
2. Execute o comando de deploy:  
  Substitua os placeholders \<...\> pelos seus próprios valores. O gcloud CLI usará o Dockerfile presente no diretório para construir a imagem, enviá-la para o Artifact Registry e, em seguida, implantá-la no Cloud Run.  
  gcloud run deploy lead-manager \\  
   \--platform managed \\  
   \--region us-central1 \\  
   \--allow-unauthenticated \\  
   \--set-env-vars="SPREADSHEET\_ID=\<SEU\_SPREADSHEET\_ID\>" \\  
   \--set-env-vars="IMAP\_USER=\<SEU\_EMAIL\_IMAP\>" \\  
   \--set-env-vars="IMAP\_HOST=\<SEU\_PROVEDOR\_IMAP\>" \\  
   \--set-env-vars="TEAM\_A\_NAME=\<NOME\_EQUIPE\_A\>" \\  
   \--set-env-vars="TEAM\_B\_NAME=\<NOME\_EQUIPE\_B\>" \\  
   \--set-env-vars="DISTRIBUTION\_PERCENTAGE\_A=0.7" \\  
   \--set-secrets="C2S\_API\_JWT\_SECRET\_ID=CRM\_API\_TOKEN:latest" \\  
   \--set-secrets="IMAP\_PASSWORD\_SECRET\_ID=IMAP\_PASSWORD:latest"
  
  - **Nota:** O parâmetro \--source . não é mais necessário, pois o gcloud detectará o Dockerfile e o usará por padrão.
3. Após o deploy, copie a **URL do serviço** gerada pelo Cloud Run.
  

### **4. Configuração do Cloud Scheduler**

- Vá para o Cloud Scheduler no Console do GCP.
- Crie um novo Job.
- Frequência: Defina a frequência de execução usando a sintaxe cron (ex: */5 * * * * para executar a cada 5 minutos).
- Fuso Horário: Selecione o fuso horário apropriado.
- Destino (Target): HTTP.
- URL: Cole a URL do seu serviço Cloud Run.
- Método HTTP: POST.

Clique em Criar. O sistema agora está totalmente configurado e automatizado.


## **Monitoramento**

Os logs de execução podem ser visualizados na seção **Logs** do seu serviço no **Cloud Run**.

## **Dependências**

As dependências Python estão listadas no arquivo requirements.txt.
```
Flask
gspread
google-auth
google-cloud-secret-manager
requests
gunicorn
```
