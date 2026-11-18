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

# Estilização Visual Limpa (Padrão 5S)
st.markdown("""
    <style>
    .main { background-color: #F4F9F4; }
    .stButton>button { background-color: #1B4D3E; color: white; border-radius: 8px; font-weight: bold; border: none; width: 100%; padding: 0.6rem; }
    .stButton>button:hover { background-color: #123528; color: white; }
    h1, h2, h3 { color: #1B4D3E; }
    </style>
""", unsafe_allow_html=True)

# Garantir pastas necessárias
os.makedirs("assets/logos_unidades", exist_ok=True)
os.makedirs("temp", exist_ok=True)

# Cabeçalho Principal
st.title("👷‍♂️ TM Engenharia e Serviços")
st.subheader("Gerador de Laudos de SST & Inspeção de Campo")
st.markdown("---")

# Carregar unidades disponíveis com segurança
unidades_disponiveis = []
if os.path.exists("assets/logos_unidades"):
    unidades_disponiveis = [
        f.split(".")[0].replace("_", " ").title()
        for f in os.listdir("assets/logos_unidades")
        if f.endswith((".png", ".jpg", ".jpeg"))
    ]

# Barra lateral para configurações essenciais
with st.sidebar:
    if os.path.exists("assets/logo_tm.png"):
        st.image("assets/logo_tm.png", width=140)
    st.header("⚙️ Configurações")
    
    api_key = st.secrets.get("GEMINI_API_KEY") or st.text_input("Chave API Gemini", type="password")
    
    st.markdown("---")
    st.subheader("📁 Cadastrar Unidade / Logo")
    novo_cliente = st.text_input("Nome da Unidade", placeholder="Ex: Fazenda Boa Esperança")
    logo_file = st.file_uploader("Logotipo (PNG/JPG)", type=["png", "jpg", "jpeg"])
    
    if st.button("Salvar Logotipo"):
        if novo_cliente and logo_file:
            path_logo = os.path.join("assets/logos_unidades", f"{novo_cliente.strip().lower().replace(' ', '_')}.png")
            Image.open(logo_file).save(path_logo)
            st.success(f"Logo de '{novo_cliente}' salvo! Atualize a página.")
        else:
            st.error("Informe o nome e envie o arquivo.")

# Formulário Principal (Layout em Página Única, Igual ao 5S)
st.markdown("### 📋 1. Dados da Inspeção")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if unidades_disponiveis:
        cliente_sel = st.selectbox("Unidade / Cliente", options=["Selecione..."] + unidades_disponiveis)
    else:
        cliente_sel = st.text_input("Unidade / Cliente", placeholder="Digite o nome da unidade")
with col2:
    local_inspecao = st.text_input("Localização / Município", placeholder="Ex: Rio Verde - GO")
with col3:
    responsavel_tst = st.text_input("Técnico Responsável (TST)", placeholder="Flávio Otávio - MTE 029826/GO")
with col4:
    data_inspecao = st.date_input("Data da Inspeção")

st.markdown("---")
st.markdown("### 📸 2. Evidência Fotográfica e Contexto")

c_foto, c_obs = st.columns([1, 1])

with c_foto:
    metodo = st.radio("Forma de inserção da foto", ["Tirar com a Câmera", "Enviar da Galeria"])
    imagem_obj = None
    if metodo == "Tirar com a Câmera":
        foto_cam = st.camera_input("Capturar foto")
        if foto_cam:
            imagem_obj = Image.open(foto_cam)
    else:
        foto_arq = st.file_uploader("Selecionar arquivo de imagem", type=["jpg", "jpeg", "png"])
        if foto_arq:
            imagem_obj = Image.open(foto_arq)

with c_obs:
    observacao = st.text_area(
        "✍️ Observações de Campo / Contexto",
        placeholder="Descreva o desvio encontrado (Ex: Operador sem EPI em altura...)",
        height=200
    )

if imagem_obj is not None:
    st.markdown("---")
    st.markdown("### 🚀 3. Processamento da Análise")
    
    col_img, col_btn = st.columns([1, 2])
    with col_img:
        st.image(imagem_obj, caption="Evidência Registrada", use_container_width=True)
    with col_btn:
        cliente_txt = cliente_sel if isinstance(cliente_sel, str) else "Unidade"
        st.info(f"**Resumo da Auditoria:**\n- **Cliente/Unidade:** {cliente_txt}\n- **Local:** {local_inspecao}\n- **TST:** {responsavel_tst}")
        analisar = st.button("✨ Gerar Laudo Técnico com Inteligência Artificial", type="primary")

    if analisar:
        if not api_key:
            st.error("⚠️ Insira a chave da API do Gemini na barra lateral.")
        elif not cliente_sel or cliente_sel == "Selecione..." or not responsavel_tst:
            st.warning("⚠️ Preencha a unidade e o nome do técnico responsável.")
        else:
            with st.spinner("🔍 Analisando imagem e cruzando com Normas Regulamentadoras (NRs)..."):
                try:
                    client = genai.Client(api_key=api_key)
                    
                    prompt_sistema = (
                        "Você é um Engenheiro de Segurança do Trabalho sênior e Auditor da TM Engenharia e Serviços. "
                        f"Analise esta imagem tirada em campo no cliente {cliente_txt} e o contexto fornecido: "
                        f"{observacao if observacao else 'Nenhum contexto adicional.'}\n\n"
                        "Elabore o laudo técnico estruturado rigidamente nos seguintes tópicos:\n"
                        "1. **ITEM E TÍTULO DO DESVIO:** (Título claro identificando a não conformidade).\n"
                        "2. **SITUAÇÃO EVIDENCIADA E ANÁLISE DE RISCO:** (Descrição técnica detalhada dos perigos e do potencial dano físico/jurídico).\n"
                        "3. **FUNDAMENTAÇÃO LEGAL (NRs):** (Normas Regulamentadoras aplicáveis — com ênfase na NR-31, NR-33, NR-12, NR-35, NR-10 — citando itens e alíneas violados).\n"
                        "4. **AÇÃO CORRETIVA EXIGIDA (DETALHADA):** (Passo a passo prático e mandatório para correção da falha)."
                    )
                    
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[imagem_obj, prompt_sistema]
                    )
                    
                    st.success("✅ Laudo gerado com sucesso!")
                    st.markdown("---")
                    st.markdown("### 📄 Resultado Técnico")
                    st.markdown(response.text)
                    
                    temp_img = "temp/evidencia.jpg"
                    imagem_obj.save(temp_img)
                    
                    def gerar_pdf(conteudo, cli, loc, resp, dt, img_p):
                        cli_str = str(cli)
                        pdf_name = f"temp/Relatorio_SST_{cli_str.replace(' ', '_')}.pdf"
                        doc = SimpleDocTemplate(pdf_name, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
                        styles = getSampleStyleSheet()
                        story = []
                        
                        st_titulo = ParagraphStyle('T', parent=styles['Heading1'], fontSize=12, textColor=colors.HexColor("#1B4D3E"), alignment=1)
                        st_corpo = ParagraphStyle('C', parent=styles['Normal'], fontSize=9, leading=13, spaceAfter=6)
                        
                        logo_tm_path = "assets/logo_tm.png"
                        l_esq = RLImage(logo_tm_path, width=80, height=30) if os.path.exists(logo_tm_path) else Paragraph("<b>TM ENGENHARIA</b>", st_corpo)
                        
                        logo_cli_path = os.path.join("assets/logos_unidades", f"{cli_str.strip().lower().replace(' ', '_')}.png")
                        l_dir = RLImage(logo_cli_path, width=80, height=30) if os.path.exists(logo_cli_path) else Paragraph(f"<b>{cli_str}</b>", st_corpo)
                        
                        cab_table = Table([[l_esq, Paragraph("<b>RELATÓRIO TÉCNICO DE INSPEÇÃO DE SST</b>", st_titulo), l_dir]], colWidths=[100, 315, 100])
                        cab_table.setStyle(TableStyle([
                            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                            ('ALIGN', (0,0), (-1,-1), 'CENTER')
                        ]))
                        
                        story.append(cab_table)
                        story.append(Spacer(1, 8))
                        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1B4D3E"), spaceAfter=8))
                        
                        info_txt = f"""
                        <b>Empresa Auditada:</b> {cli_str} | <b>Local:</b> {loc}<br/>
                        <b>Prestadora:</b> TM Engenharia e Serviços | <b>Responsável Técnico:</b> {resp}<br/>
                        <b>Data da Inspeção:</b> {dt.strftime('%d/%m/%Y')}
                        """
                        story.append(Paragraph(info_txt, st_corpo))
                        story.append(Spacer(1, 6))
                        
                        for linha in conteudo.split('\n'):
                            if linha.strip():
                                story.append(Paragraph(linha, st_corpo))
                                
                        story.append(Spacer(1, 6))
                        if os.path.exists(img_p):
                            story.append(Paragraph("<b>Registro Fotográfico de Campo:</b>", st_corpo))
                            story.append(RLImage(img_p, width=200, height=150))
                            
                        doc.build(story)
                        return pdf_name
                        
                    pdf_path = gerar_pdf(response.text, cliente_sel, local_inspecao, responsavel_tst, data_inspecao, temp_img)
                    
                    with open(pdf_path, "rb") as f_pdf:
                        st.download_button(
                            label="📥 Baixar Laudo Técnico Oficial em PDF",
                            data=f_pdf,
                            file_name=f"Laudo_SST_{cliente_sel if isinstance(cliente_sel, str) else 'Unidade'}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                        
                except Exception as err:
                    st.error(f"❌ Erro ao gerar laudo: {err}")
