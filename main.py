import os
import io
import pandas as pd
import streamlit as st
from typing import List
from Markdown2docx import Markdown2docx
from pydantic import BaseModel, Field
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


class CriterioParaRubrica(BaseModel):
    Criterio: str = Field(description="Criterio de evaluación")
    Excelente: str = Field(description="Descripción de la calificación Excelente")
    Bueno: str = Field(description="Descripción de la calificación Bueno")
    Regular: str = Field(description="Descripción de la calificación Regular")
    Insuficiente: str = Field(description="Descripción de la calificación Insuficiente")
    No_logrado: str = Field(description="Descripción de la calificación No logrado")


class Proyecto(BaseModel):
    Descripcion: str = Field(description="Una descripción del projecto")
    Objetivos: List[str] = Field(description="Lista de objetivos pedagógicos principales del proyecto")
    Entregable: str = Field(descripción="Descripción del entregable que realizarán los alumnos")
    Actividades: List[str] = Field(descripción="Una lista con las actividades que realizarán los alumnos")
    Materiales: List[str] = Field(descripción="La lista de materiales que van a ser necesarios para el projecto")
    Evaluacion: str = Field(descripción="Evaluación del projecto y puntos a considerar")
    Rubrica: List[CriterioParaRubrica] = Field(descripción="La rúbrica de evaluación del projecto")
    Titulo: str = Field(description="El titulo del proyecto")


@st.cache_resource(show_spinner=False)
def generar_proyecto(grado, materia, acceso_internet, tema) -> Proyecto:
    prompt_materias = ', '.join(materia) if len(materia) > 1 else materia[0]
    prompt_internet = "con" if acceso_internet else "sin"
    
    messages = [
        {"role": "system", "content": "Eres un asistente especializado en crear proyectos educativos."},
        {"role": "user", "content": f"Crea un proyecto de Aprendizaje Basado en Proyectos para {grado} en la(s) materia(s) de {prompt_materias}, {prompt_internet} acceso a internet, sobre el tema: {tema}"}
    ]

    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=messages,
            response_format=Proyecto,
            temperature=0.7,
        )
        return completion.choices[0].message.parsed
    except Exception as e:
        st.error(f"Error al generar el proyecto: {e}")
        return None


def projecto_a_markdown(project: Proyecto):
    markdown = f"# {project.Titulo}\n\n"
    markdown += f"{project.Descripcion}\n\n"

    markdown += "## Objetivos\n\n"
    for objetivo in project.Objetivos:
        markdown += f"- {objetivo}\n"
    
    markdown += "## Entregable\n\n"
    markdown += f"{project.Entregable}\n\n"
    
    markdown += "### Actividades\n\n"
    for i, actividad in enumerate(project.Actividades, 1):
        markdown += f"{i}. {actividad}\n"
    
    markdown += "### Materiales\n\n"
    for material in project.Materiales:
        markdown += f"- {material}\n"
    
    markdown += "## Evaluación\n\n"
    markdown += f"{project.Evaluacion}\n\n"
    markdown += "### Rúbrica\n\n"
    df = pd.DataFrame([r.model_dump() for r in project.Rubrica])
    df.columns = ["Criterio", "Excelente", "Bueno", "Regular", "Insuficiente", "No logrado"]
    markdown += df.to_markdown(index=False)

    return markdown


def render():
    main_content = st.empty()
    info_content = st.empty()
    main_content.title("Aprendizaje Basado en Proyectos")
    info_content.info("Usa el panel de la izquierda para generar un nuevo proyecto.")

    with st.sidebar:
        grado = st.selectbox("Selecciona el grado:", [
            "1° de primaria", 
            "2° de primaria", 
            "3° de primaria", 
            "4° de primaria",
            "5° de primaria", 
            "6° de primaria", 
            "1° de secundaria", 
            "2° de secundaria",
            "3° de secundaria"
        ])
        materia = st.multiselect("Selecciona la materia:", [
            "Matemáticas", 
            "Ciencias Naturales", 
            "Historia", 
            "Geografía",
            "Español", 
            "Inglés", 
            "Arte", 
            "Educación Física"
        ], max_selections=3)
        tema = st.text_input("Tema del proyecto:")
        acceso_internet = st.checkbox("Mis alumnos cuentan con acceso a internet")

        if not st.button("Generar Proyecto", disabled=not grado or not materia or not tema):
            return
        
    info_content.empty()
    with st.spinner("Generando proyecto..."):
        proyecto = generar_proyecto(grado, materia, acceso_internet, tema)
        markdown = projecto_a_markdown(proyecto)
    st.balloons()
    main_content.markdown(markdown)
    info_content.caption("Este contenido es generado por Inteligencia Artificial.")

    # Guarda el archivo markdown
    with open("proyecto.md", "w+") as file:
        file.write(markdown)

    # Descarga markdown
    if os.path.exists("proyecto.md"):
        # Convert to docx
        project = Markdown2docx('proyecto')
        project.eat_soup()

        # Transform to BytesIO
        bio = io.BytesIO()
        project.doc.save(bio)

        # Download file
        st.download_button('Descarga en formato DOCX', data=bio.getvalue(), file_name=f"{proyecto.Titulo}.docx", mime="docx")
        os.remove("proyecto.md")


if __name__ == "__main__":
    render()
