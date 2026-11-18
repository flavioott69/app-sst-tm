import os
from PIL import Image
import streamlit as st
from google import genai
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import HRFlowable, Image as RLImage, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# Configuração da Página
st.set_page_config(page_title="SST Vision | TM Engenharia", page_icon="👷‍♂️", layout="wide")

# Estilização Visual (Verde Claro e Verde Escuro Institucional)
st.markdown(
    """
    <style>
    .main { background-color: #F4F9F4; }
    .stButton>button { background-color: #1B4D3E; color: white; border-radius: 8px; font-weight: bold; border: none; }
    .stButton>button:hover { background-color: #123528; color: white; }
    h1, h2, h3 { color: #1B4D3E; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Pastas de ativos
os.makedirs("assets/logos_unidades", exist_ok=True)
os.makedirs("temp", exist_ok=True)

st.title("👷‍♂️ TM Engenharia e Serviços — Gerador de Laudos de SST")
st.markdown("Inspeção de campo inteligente com cruzamento normativo automatizado (NRs).")

# Chave da API Gemini (via Streamlit Secrets ou barra lateral)
api_key = st.secrets.get("GEMINI_API_KEY") or st.sidebar.text_input("Chave da API Gemini", type="password")

# --- BARRA LATERAL ---
st.sidebar.header("📋 Dados da Inspeção & Logos")

# Cadastro prévio de logos de unidades
st.sidebar.subheader("Gerenciar Logos de Unidades")
novo_cliente = st.sidebar.text_input("Nome da Unidade/Cliente", placeholder="Ex: Fazenda Boa Esperança")
logo_file = st.sidebar.file_uploader("Logotipo da Unidade (PNG/JPG)", type=["png", "jpg", "jpeg"])

if st.sidebar.button("💾 Salvar Logotipo"):
  if novo_cliente and logo_file:
    path_logo = os.path.join("assets/logos_unidades", f"{novo_cliente.strip().lower().replace(' ', '_')}.png")
    Image.open(logo_file).save(path_logo)
    st.sidebar.success(f"Logo de '{novo_cliente}' salvo com sucesso!")
  else:
    st.sidebar.error("Informe o nome e envie o arquivo do logo.")

st.sidebar.markdown("---")

# Parâmetros do laudo atual
unidades_disponiveis = [
    f.split(".")[0].replace("_", " ").title()
    for f in os.listdir("assets/logos_unidades")
    if f.endswith((".png", ".jpg", ".jpeg"))
]
cliente_sel = st.sidebar.selectbox("Selecione a Unidade / Cliente", options=["Selecione..."] + unidades_disponive)
local_inspecao = st.sidebar.text_input("Localização / Município", placeholder="Ex: Montividiu - GO")
responsavel_tst = st.sidebar.text_input("Técnico Responsável", placeholder="Nome do TST")
data_inspecao = st.sidebar.date_input("Data da Inspeção")

# --- ÁREA PRINCIPAL ---
st.subheader("📸 Captura de Evidência em Campo")
metodo = st.radio("Como deseja inserir a foto?", ["Tirar Foto com a Câmera", "Enviar da Galeria / Arquivo"])

imagem_obj = None
if metodo == "Tirar Foto com a Câmera":
  foto_cam = st.camera_input("Tire a foto da condição encontrada")
  if foto_cam:
    imagem_obj = Image.open(foto_cam)
else:
  foto_arq = st.file_uploader("Selecione o arquivo da foto", type=["jpg", "jpeg", "png"])
  if foto_arq:
    imagem_obj = Image.open(foto_arq)

observacao = st.text_area(
    "✍️ Observações complementares de campo (Opcional)",
    placeholder="Ex: Trabalhador em altura sem cinto próximo à borda do silo.",
)

if imagem_obj is not None:
  c1, c2 = st.columns([1, 1])
  with c1:
    st.image(imagem_obj, caption="Evidência Registrada", use_container_width=True)
  with c2:
    st.markdown("### Resumo")
    st.markdown(f"**Cliente:** {cliente_sel}")
    st.markdown(f"**Local:** {local_inspecao}")
    st.markdown(f"**Técnico:** {responsavel_tst}")
    analisar = st.button("🚀 Processar Análise com IA", type="primary", use_container_width=True)

  if analisar:
    if not api_key:
      st.error("⚠️ Insira a chave da API do Gemini.")
    elif cliente_sel == "Selecione..." or not responsavel_tst:
      st.warning("⚠️ Selecione a unidade e preencha o nome do técnico.")
    else:
      with st.spinner("🔍 Analisando imagem e gerando fundamentação legal..."):
        try:
          client = genai.Client(api_key=api_key)

          # Prompt especialista alinhado com o que estruturamos no AI Studio
          prompt_sistema = (
              "Você é um Engenheiro de Segurança do Trabalho sênior e Auditor da TM Engenharia e Serviços. "
              "Analise esta imagem tirada em campo e o contexto fornecido: "
              f"{observacao if observacao else 'Nenhum contexto adicional.'}\n\n"
              "Elabore o laudo técnico estruturado rigidamente nos seguintes tópicos:\n"
              "1. **ITEM E TÍTULO DO DESVIO:** (Título claro identificando a não conformidade).\n"
              "2. **SITUAÇÃO EVIDENCIADA E ANÁLISE DE RISCO:** (Descrição técnica detalhada dos perigos e do potencial dano físico/jurídico).\n"
              "3. **FUNDAMENTAÇÃO LEGAL (NRs):** (Normas Regulamentadoras aplicáveis — com ênfase na NR-31, NR-33, NR-12, NR-35, NR-10 — citando itens e alíneas violados).\n"
              "4. **AÇÃO CORRETIVA EXIGIDA (DETALHADA):** (Passo a passo prático e mandatório para correção da falha)."
          )

          response = client.models.generate_content(model="gemini-2.5-flash", contents=[imagem_obj, observado := imagem_obj, prompt_sistema])

          st.success("✅ Laudo gerado com sucesso!")
          st.markdown("---")
          st.markdown("### 📄 Resultado Técnico")
          st.markdown(response.text)

          # Salvando imagem temporária para o PDF
          temp_img = "temp/evidencia.jpg"
          imagem_obj.save(temp_img)


          def gerar_pdf(conteudo, cli, loc, resp, dt, img_p, logo_cli_p):
            pdf_name = f"temp/Relatorio_SST_{cli.replace(' ', '_')}.pdf"
            doc = SimpleDocTemplate(pdf_name, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
            styles = getSampleStyleSheet()
            story = []

            st_titulo = ParagraphStyle(
                "T", parent=styles["Heading1"], fontSize=13, textColor=colors.HexColor("#1B4D3E"), alignment=1
            )
            st_corpo = ParagraphStyle("C", parent=styles["Normal"], fontSize=9.5, leading=13, spaceAfter=6)

            # Cabeçalho com Logos
            logo_tm_path = "assets/logo_tm.png"
            l_esq = (
                RLImage(logo_tm_path, width=90, height=35)
                if os.path.exists(logo_tm_path)
                else Paragraph("<b>TM ENGENHARIA</b>", st_corpo)
            )
            l_dir = (
                RLImage(logo_cli_p, width=90, height=35)
                if os.path.exists(logo_cli_p)
                else Paragraph(f"<b>{cli}</b>", st_corpo)
            )

            cab_table = Table(
                [[l_esq, Paragraph("<b>RELATÓRIO TÉCNICO DE INSPEÇÃO DE SST</b>", st_titulo), l_dir]],
                colWidths=[110, 295, 110],
            )
            cab_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (-1, -1), "CENTER")]))

            story.append(cab_table)
            story.append(Spacer(1, 10))
            story.append(HRFlowable(width="100%", thickness=1.2, color=colors.HexColor("#1B4D3E"), spaceAfter=10))

            info_txt = f"""
                    <b>Empresa Auditada:</b> {cli}<br/>
                    <b>Localização:</b> {loc}<br/>
                    <b>Prestadora:</b> TM Engenharia e Serviços<br/>
                    <b>Responsável Técnico:</b> {resp}<br/>
                    <b>Data:</b> {dt.strftime('%d/%m/%Y')}
                    """
            story.append(Paragraph(info_txt, st_corpo))
            story.append(Spacer(1, 8))

            for linha in conteudo.split("\n"):
              if linha.strip():
                story.append(Paragraph(linha, st_corpo))

            story.append(Spacer(1, 8))
            if os.path.exists(img_p):
              story.append(Paragraph("<b>Registro Fotográfico:</b>", st_corpo))
              story.append(RLImage(img_p, width=220, height=160))

            doc.build(story)
            return pdf_name

          logo_path_cliente = os.path.join("assets/logos_unidades", f"{cliente_sel.strip().lower().replace(' ', '_')}.png")
          pdf_path = gerar_pdf(
              response.text, cliente_sel, local_inspecao, responsavel_tst, data_inspecao, temp_img, logo_path_cliente
          )

          with open(pdf_path, "rb") as f_pdf:
            st.download_button(
                label="📥 Baixar Laudo Técnico em PDF",
                data=f_pdf,
                file_name=f"Laudo_SST_{cliente_sel.replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

        except Exception as err:
          st.error(f"❌ Erro ao gerar laudo: {err}")
