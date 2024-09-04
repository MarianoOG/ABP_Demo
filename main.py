import os
import io
import json
import promptlayer
import streamlit as st
from typing import List
from Markdown2docx import Markdown2docx
from langchain.chat_models import PromptLayerChatOpenAI
from langchain.callbacks.base import BaseCallbackHandler
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

promptlayer.api_key = os.environ.get("PROMPTLAYER_API_KEY")
openai = promptlayer.openai
openai.api_key = os.environ.get("OPENAI_API_KEY")


class StreamHandler(BaseCallbackHandler):
    def __init__(self, container, initial_text="", display_method='markdown'):
        self.container = container
        self.text = initial_text
        self.display_method = display_method
        self.markdown = ""

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.text += token
        display_function = getattr(self.container, self.display_method, None)
        if display_function is not None:
            try:
                json_data = json.loads(self.text + '"]}')
                self.markdown = format_project_in_markdown(json_data)
            except:
                try:
                    json_data = json.loads(self.text + '"}')
                    self.markdown = format_project_in_markdown(json_data)
                except:
                    pass
            display_function(self.markdown)
        else:
            raise ValueError(f"Invalid display_method: {self.display_method}")


# Define your desired data structure.
class Project(BaseModel):
    Summary: str = Field(description="Una descripción del projecto")
    Objetivos: List[str] = Field(description="Lista de objetivos pedagógicos principales del proyecto")
    Materiales: List[str] = Field(descripción="La lista de materiales que van a ser necesarios para el projecto")
    Actividades: List[str] = Field(descripción="Una lista con las actividades que realizarán los alumnos")
    Entregables: List[str] = Field(descripción="La lista de entregables que realizarán los alumnos")
    Evaluation: str = Field(descripción="Evaluación del projecto y puntos a considerar")

    def to_json(self):
        json_data = {"Summary": self.Summary,
                     "Objetivos": self.Objetivos,
                     "Materiales": self.Materiales,
                     "Actividades": self.Actividades,
                     "Entregables": self.Entregables,
                     "Evaluation": self.Evaluation}
        return json_data


def format_project_in_markdown(json_data):
    json_data = json_data.copy()
    markdown_text = ""
    if "Summary" in json_data:
        markdown_text += "## Descripción\n\n"
        markdown_text += json_data.pop("Summary") + "\n\n"

    for key, val in json_data.items():
        if key == "Evaluation":
            markdown_text += "## Evaluación\n\n"
            markdown_text += val + "\n\n"
        else:
            markdown_text += f"## {key}\n\n"
            markdown_text += "\n".join([f"- {i}" for i in val]) + "\n\n"

    return markdown_text


def generar_proyecto(grado, materia, acceso_internet, tema, contenido):
    # Prompt
    template_dict = promptlayer.prompts.get("ABPDescription", langchain=True)
    parser = PydanticOutputParser(pydantic_object=Project)
    prompt_format_instructions = parser.get_format_instructions()
    prompt_materias = ', '.join(materia) if len(materia) > 1 else materia[0]
    prompt_internet = "con" if acceso_internet else "sin"
    messages = template_dict.format_prompt(formato=prompt_format_instructions,
                                           grado=grado,
                                           materias=prompt_materias,
                                           internet=prompt_internet,
                                           tema=tema).to_messages()

    stream_handler = StreamHandler(contenido)
    chatllm = PromptLayerChatOpenAI(callbacks=[stream_handler],
                                    pl_tags=["ABP", grado] + materia,
                                    return_pl_id=True,
                                    temperature=0.5,
                                    streaming=True)

    # Response and template
    response = chatllm.generate([messages])
    project, pl_request_id = "", None
    for res in response.generations:
        pl_request_id = res[0].generation_info["pl_request_id"]
        project = parser.parse(res[0].text)
        input_variables = {"grado": grado, "materias": prompt_materias, "internet": prompt_internet, "tema": tema}
        promptlayer.track.prompt(request_id=pl_request_id,
                                 prompt_name="ABPDescription",
                                 prompt_input_variables=input_variables)

    return project, pl_request_id


def generar_rubrica():
    prompt = "Para el proyecto anterior genera una rúbrica de evaluación en formato de tabla con las columnas: " \
             "Criterio, Excelente (5), Bueno (4), Regular (3), Insuficiente (2), No logrado (1)."

    return prompt


def render():
    titulo = st.empty()
    titulo.title("Aprendizaje Basado en Proyectos")
    contenido = st.empty()

    with st.sidebar:
        grado = st.selectbox("Selecciona el grado:", [
            "1° de primaria", "2° de primaria", "3° de primaria", "4° de primaria",
            "5° de primaria", "6° de primaria", "1° de secundaria", "2° de secundaria",
            "3° de secundaria"
        ])

        materia = st.multiselect("Selecciona la materia:", [
            "Matemáticas", "Ciencias Naturales", "Historia", "Geografía",
            "Español", "Inglés", "Arte", "Educación Física"
        ], max_selections=3)

        acceso_internet = st.checkbox("Mis alumnos cuentan con acceso a internet")

        tema = st.text_input("Tema del proyecto:")

        if st.button("Generar Proyecto"):
            if not tema:
                st.warning("Por favor ingresa un tema para el proyecto.")
                return

            project_name = f"# Proyecto: {tema}\n\n"
            titulo.markdown(project_name)
            project, pl_id = generar_proyecto(grado, materia, acceso_internet, tema, contenido)
            with open("proyecto.md", "w+") as file:
                file.write(project_name + format_project_in_markdown(project.to_json()))
        else:
            contenido.info("Usa el panel de la izquierda para generar un nuevo proyecto.")

    # Descarga markdown
    if os.path.exists("proyecto.md"):
        # Convert to docx
        project = Markdown2docx('proyecto')
        project.eat_soup()

        # Transform to BytesIO
        bio = io.BytesIO()
        project.doc.save(bio)

        # Download file
        st.download_button('Descarga en formato DOCX', data=bio.getvalue(), file_name="proyecto.docx", mime="docx")
        os.remove("proyecto.md")


if __name__ == "__main__":
    render()
