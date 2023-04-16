import streamlit as st
from Markdown2docx import Markdown2docx
import openai
import os
import io

openai.api_key = os.environ["OPENAI_API_KEY"]


def generar_proyecto(grado, materia, acceso_internet, tema, contenido):
    prompt_internet = "con acceso a internet" if acceso_internet else "sin acceso a internet"
    prompt = f"Generar un proyecto de aprendizaje basado en proyectos para estudiantes de grado {grado} " \
             f"en la materia de {materia} {prompt_internet}. El tema del proyecto es: {tema}. " \
             f"Proporcionar descripción, objetivos, actividades, entregables y recursos necesarios."

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system",
             "content": "Eres un experto en creación de proyectos para el aprendizaje basado en proyectos (ABP)."
                        "Usas formato markdown para todas tus respuestas."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
        stream=True
    )

    proyecto = ""
    for chunk in response:
        if "content" in chunk.choices[0].delta.keys():
            proyecto += chunk.choices[0].delta.content
            contenido.write(proyecto)

    return proyecto


def generar_rubrica():
    prompt = f"Para el proyecto anterior genera una rúbrica de evaluación en formato de tabla con las columnas: " \
             f"Criterio, Excelente (5), Bueno (4), Regular (3), Insuficiente (2), No logrado (1)."

    return prompt


def render():
    contenido = st.empty()

    with st.sidebar:
        grado = st.selectbox("Selecciona el grado:", [
            "1° de primaria", "2° de primaria", "3° de primaria", "4° de primaria",
            "5° de primaria", "6° de primaria", "1° de secundaria", "2° de secundaria",
            "3° de secundaria"
        ])

        materia = st.selectbox("Selecciona la materia:", [
            "Matemáticas", "Ciencias Naturales", "Historia", "Geografía",
            "Español", "Inglés", "Arte", "Educación Física"
        ])

        acceso_internet = st.checkbox("Mis alumnos cuentan con acceso a internet")

        tema = st.text_input("Tema del proyecto:")

        if st.button("Generar Proyecto"):
            if not tema:
                st.warning("Por favor ingresa un tema para el proyecto.")
                return

            proyecto = generar_proyecto(grado, materia, acceso_internet, tema, contenido)
            with open("proyecto.md", "w+") as file:
                file.write(proyecto)
        else:
            contenido.info("Usa el panel de la izquierda para generar un nuevo proyecto.")

    # Descarga markdown
    if os.path.exists("proyecto.md"):
        # Convert to docx
        project = Markdown2docx('proyecto')
        project.eat_soup()

        # Tansform to BytesIO
        bio = io.BytesIO()
        project.doc.save(bio)

        # Download file
        st.download_button('Descarga en formato DOCX', data=bio.getvalue(), file_name="proyecto.docx", mime="docx")
        os.remove("proyecto.md")


if __name__ == "__main__":
    render()
