from fpdf import FPDF
import streamlit as st
import pandas as pd
from Simulador import SimuladorBNDES

# Classe para geração de PDF com tabelas e quebra de página
class PDF(FPDF):
    def header(self):
        self.set_font("Arial", size=12)
        self.cell(0, 10, "Resultados da Simulação BNDES", ln=True, align="C")

    def add_table(self, data, column_widths, headers):
        self.set_font("Arial", size=10)
        self.set_fill_color(200, 200, 200)  # Cinza claro para cabeçalho
        self.set_text_color(0)
        self.set_draw_color(50, 50, 100)
        self.set_line_width(0.3)

        # Cabeçalho da tabela
        for i, header in enumerate(headers):
            self.cell(column_widths[i], 7, header, border=1, align="C", fill=True)
        self.ln()

        # Dados da tabela
        self.set_fill_color(240, 240, 240)  # Fundo alternado para linhas
        fill = False
        for row in data:
            if self.get_y() > 260:  # Verifica se o espaço restante é suficiente
                self.add_page()  # Adiciona uma nova página
                for i, header in enumerate(headers):  # Reescreve o cabeçalho na nova página
                    self.cell(column_widths[i], 7, header, border=1, align="C", fill=True)
                self.ln()
            for i, cell in enumerate(row):
                self.cell(column_widths[i], 6, str(cell), border=1, align="C", fill=fill)
            self.ln()
            fill = not fill  # Alterna a cor de fundo para as linhas


st.set_page_config(
    page_title="Simulador BNDES",
    layout="wide"
)
# Adicionando a logo do BNDES
st.image("banco-bndes.svg", width= 250)
# Título do app
st.title("Simulador de Pagamentos BNDES")
# Regras de prazo máximo e carência
regras = {
    "BK Aquisição e Comercialização (FINAME)": {"prazo_max": 120, "carencia_max": 24, "taxa_bndes_fixo": 0.95},
    "BNDES Automático - Projeto de Investimento": {"prazo_max": 240, "carencia_max": 36, "taxa_bndes_fixo": 0.95},
    "BNDES Finame - Baixo Carbono": {"prazo_max": 120, "carencia_max": 24, "taxa_bndes_fixo": 0.75},
}


# Entradas do usuário
st.write("### Configurações do Simulador")
erro = False  # Controla a exibição do botão de simulação


# Seleção do produto
produto = st.selectbox(
    "Produto",
    ["BK Aquisição e Comercialização (FINAME)", "BNDES Automático - Projeto de Investimento", "BNDES Finame - Baixo Carbono"],
)

# Obtém os valores máximos com base no produto selecionado
prazo_max = regras[produto]["prazo_max"]
carencia_max = regras[produto]["carencia_max"]
taxa_bndes_fixo = regras[produto]["taxa_bndes_fixo"]



# Primeira linha de inputs
col1, col2 = st.columns(2)
with col1:
    carencia = st.number_input("Carência (meses)", min_value=3, max_value=carencia_max, step=3, value=3)
with col2:
    prazo_amortizacao = st.number_input("Amortização (meses)", min_value=1, value=24)

valor_liberado = st.number_input("Valor do financiamento", min_value=0.0, max_value=50_000_000.0)



# Validações
if carencia % 3 != 0:
    st.error("A carência deve ser múltiplo de 3.")
    erro = True

if valor_liberado <= 0 or valor_liberado > 50000000:
    st.error("O valor do financiamento deve ser maior que zero e não pode ultrapassar 50 milhões.")
    erro = True

prazo_total = carencia + prazo_amortizacao
if prazo_total > prazo_max:
    st.error(f"O prazo total não pode exceder {prazo_max} meses.")
    erro = True

# Botão de simular só aparece se não houver erros
if not erro:
    if st.button("Simular"):
        try:
            # Inicializa o simulador com os parâmetros fornecidos
            simulador = SimuladorBNDES(

                valor_liberado=valor_liberado,
                carencia=carencia,
                periodic_juros=3,
                prazo_amortizacao=prazo_amortizacao,
                periodic_amortizacao=1,
                juros_prefixados_aa=0.0,
                ipca_mensal=0.0,
                spread_bndes_aa=taxa_bndes_fixo,
                spread_banco_aa=5.75,
            )

            # Gera os resultados da simulação
            resultados_df, configuracoes = simulador.exibir_dados_pagamento()
            # Atualizar o valor da chave
            configuracoes["Periodicidade de Juros (meses)"] = "Trimestral"
            configuracoes["Periodicidade de Amortização (meses)"] = "Mensal"


            # Geração do PDF
            pdf = PDF()
            pdf.add_page()

            # Configurações como texto
            pdf.set_font("Arial", size=8)
            pdf.cell(0, 8, f"Simulação do Produto: {produto}", ln=True)
            for key, value in configuracoes.items():
                pdf.cell(0, 8, f"{key}: {value}", ln=True)

            pdf.ln(8)  # Linha em branco para separação

            # Resultados como tabela
            headers = list(resultados_df.columns)
            data = resultados_df.values.tolist()
            column_widths = [15 if i < 2 else 28 for i in range(len(headers))]

            # Adiciona a tabela ao PDF com as larguras personalizadas
            pdf.add_table(data=data, column_widths=column_widths, headers=headers)

            # Salva o PDF em memória
            pdf_output = pdf.output(dest="S").encode("latin1")

            # Botão de download do PDF
            st.download_button(
                label="Baixar PDF da Simulação",
                data=pdf_output,
                file_name="simulacao_bndes.pdf",
                mime="application/pdf",
            )

            # Exibe os resultados em uma tabela
            st.write(f"### Resultados da Simulação\n {produto}")

            st.dataframe(resultados_df, use_container_width=True)



            st.write("### Configurações da Simulação")
            configuracoes =  pd.DataFrame({
                "Parâmetros": configuracoes.keys(),
                "Valores": configuracoes.values()
                })
            configuracoes = configuracoes.reset_index(drop=True)
            st.table(configuracoes)


        except Exception as e:
            st.error(f"Ocorreu um erro ao processar a simulação: {e}")
