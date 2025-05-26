import json
from openai import OpenAI, APIError
from typing import Dict, Any, List, Optional

from ..core.config import get_settings
from ..models_schemas import (
    TextProcessingRequest, TextProcessingResponse,
    GlobalImagePrompt, EscenaProcesada, OrigenContenidoEscena, SceneImagePrompt,
    SegmentoNarrativo
)

async def _llamar_openai_api(prompt_content: str, funcion_descripcion: str) -> Dict[str, Any]:
    settings = get_settings()
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    print(f"Servicio Texto: Realizando llamada a OpenAI para: {funcion_descripcion}")
    # Descomenta la siguiente línea para ver el prompt que se envía (puede ser muy largo)
    # print(f"Servicio Texto: Enviando prompt para '{funcion_descripcion}' (primeros 1000 chars):\n{prompt_content[:1000]}...")

    response_content = None 
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini", 
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "Eres un asistente experto en procesamiento de lenguaje y generación de contenido. Responde EXCLUSIVAMENTE en formato JSON y sigue estrictamente la estructura de salida solicitada."},
                {"role": "user", "content": prompt_content}
            ],
            temperature=0.3 # Un valor bajo para tareas que requieren precisión
        )
        
        response_content = completion.choices[0].message.content
        if not response_content: 
            raise ValueError(f"La respuesta de OpenAI para '{funcion_descripcion}' no contiene contenido.")
        
        # Limpiar ```json ... ``` si el modelo lo añade a pesar del modo JSON
        if response_content.strip().startswith("```json"): 
            response_content = response_content.strip()[7:-3].strip()
        
        parsed_response = json.loads(response_content)
        print(f"Servicio Texto: Respuesta de OpenAI parseada para '{funcion_descripcion}'.")
        return parsed_response
    except APIError as e:
        print(f"Servicio Texto: Error de API OpenAI ({funcion_descripcion}): {e}")
        status_code = getattr(e, "status_code", "N/A")
        message = getattr(e, "message", str(e))
        error_message = f"Error en la API de OpenAI ({funcion_descripcion}). Código: {status_code}. Error: {message}"
        if status_code != "N/A": # Intentar dar mensajes más específicos
            if status_code == 429: error_message = f"Límite de tasa excedido con la API de OpenAI ({funcion_descripcion}). {message}"
            elif status_code == 401: error_message = f"Error de autenticación con la API de OpenAI ({funcion_descripcion}). Verifica tu API Key. {message}"
            elif status_code == 400 and "policy" in str(message).lower(): error_message = f"El contenido infringe las políticas de OpenAI ({funcion_descripcion}). {message}"
        raise ValueError(error_message)
    except json.JSONDecodeError as e:
        print(f"Servicio Texto: Error al parsear JSON de OpenAI ({funcion_descripcion}): {e}\nRespuesta recibida: {response_content}")
        raise ValueError(f"La respuesta de OpenAI no pudo ser interpretada como JSON válido ({funcion_descripcion}). Respuesta original: {response_content}")
    except Exception as e:
        print(f"Servicio Texto: Error inesperado llamando a OpenAI ({funcion_descripcion}): {type(e).__name__} - {e}")
        raise ValueError(f"Error inesperado durante la comunicación con OpenAI ({funcion_descripcion}). Error: {type(e).__name__}")

def _construir_input_json_para_llm1(datos_entrada: TextProcessingRequest) -> str:
    comentarios_originales_struct = []
    for i, comentario in enumerate(datos_entrada.comentarios):
        com_struct = {
            "id_original_comentario": f"c{i+1}",
            "texto_original_comentario": comentario.texto_comentario,
            "subcomentarios_originales": []
        }
        for j, subcomentario in enumerate(comentario.subcomentarios):
            sub_struct = {
                "id_original_subcomentario": f"c{i+1}_s{j+1}",
                "texto_original_subcomentario": subcomentario.texto_comentario
            }
            com_struct["subcomentarios_originales"].append(sub_struct)
        comentarios_originales_struct.append(com_struct)
    contenido_a_procesar = {
        "titulo_original": datos_entrada.titulo,
        "cuerpo_post_original": datos_entrada.cuerpo_historia,
        "comentarios_originales": comentarios_originales_struct
    }
    return json.dumps(contenido_a_procesar, indent=2, ensure_ascii=False)

async def generar_contenido_procesado(datos_entrada: TextProcessingRequest) -> TextProcessingResponse:
    print(f"Servicio Texto: Iniciando generar_contenido_procesado para id_proyecto: {datos_entrada.id_proyecto}")
    settings = get_settings()

    # == LLAMADA A OPENAI #1: Calidad del Lenguaje (Detección, Traducción, Corrección) ==
    input_json_llm1 = _construir_input_json_para_llm1(datos_entrada)
    prompt_llm1 = f"""Eres un asistente experto en procesamiento de lenguaje multilingüe, con habilidades de edición y corrección de estilo. Te voy a proporcionar un conjunto de textos extraídos de un post de Reddit en formato JSON.

Tu tarea consta de los siguientes pasos:
1.  Analiza TODO el contenido textual proporcionado para determinar su idioma principal predominante.
2.  Procesamiento del texto:
    a.  Si el idioma principal detectado NO es español ('es'):
        i.  Traduce CADA UNO de los textos (`titulo_original`, `cuerpo_post_original`, y cada `texto_original_comentario` y `texto_original_subcomentario`) al ESPAÑOL.
        ii. Asegúrate de que la traducción sea precisa, natural, gramaticalmente correcta y esté bien redactada.
    b.  Si el idioma principal detectado YA ES español ('es'):
        i.  Revisa CADA UNO de los textos para identificar y corregir posibles errores gramaticales, de ortografía o de puntuación.
        ii. Mejora la claridad, la coherencia y la fluidez de la redacción si es necesario, sin alterar el significado o el tono original del autor de manera significativa. El objetivo es un español estándar y bien escrito.
3.  Devuelve tu respuesta EXCLUSIVAMENTE en formato JSON. El JSON debe tener la siguiente estructura:
    {{
      "idioma_detectado": "CODIGO_ISO_639-1_DEL_IDIOMA_QUE_DETECTASTE",
      "titulo_original": "TEXTO_DEL_TITULO_YA_PROCESADO_EN_ESPAÑOL",
      "cuerpo_post_original": "TEXTO_DEL_CUERPO_DEL_POST_YA_PROCESADO_EN_ESPAÑOL",
      "comentarios_originales": [
        {{
          "id_original_comentario": "ID_DEL_COMENTARIO_ORIGINAL_1", 
          "texto_original_comentario": "TEXTO_DEL_COMENTARIO_1_YA_PROCESADO_EN_ESPAÑOL",
          "subcomentarios_originales": [
            {{
              "id_original_subcomentario": "ID_DEL_SUBCOMENTARIO_ORIGINAL_1_1",
              "texto_original_subcomentario": "TEXTO_DEL_SUBCOMENTARIO_1_1_YA_PROCESADO_EN_ESPAÑOL"
            }}
          ]
        }}
      ]
    }}

A continuación, te proporciono los textos dentro de una estructura JSON. Modifica los valores de los campos de texto según las instrucciones anteriores y añade el campo "idioma_detectado" al nivel superior del JSON de respuesta. Asegúrate de mantener los IDs originales en los comentarios y subcomentarios.

Contenido a procesar:
{input_json_llm1}
"""
    respuesta_llm1 = await _llamar_openai_api(prompt_llm1, "Paso1_CalidadLenguaje")
    print(f"Servicio Texto: RESPUESTA COMPLETA de LLM #1 (Paso1_CalidadLenguaje): {json.dumps(respuesta_llm1, indent=2, ensure_ascii=False)}")

    idioma_detectado = respuesta_llm1.get("idioma_detectado", "desconocido")
    titulo_procesado_es = respuesta_llm1.get("titulo_original", datos_entrada.titulo) 
    cuerpo_post_procesado_es = respuesta_llm1.get("cuerpo_post_original", datos_entrada.cuerpo_historia)
    comentarios_con_texto_procesado_llm1 = respuesta_llm1.get("comentarios_originales", [])
    print(f"Servicio Texto: (Paso 1) Idioma: {idioma_detectado}, Título: '{titulo_procesado_es[:30]}...'")

    # == LÓGICA PYTHON: Ensamblaje del Guion y Pre-estructura de Escenas (CON SEGMENTOS NARRATIVOS) ==
    print("Servicio Texto: Ensamblando guion y pre-estructurando escenas con segmentos...")
    partes_del_guion: List[str] = []
    escenas_pre_estructuradas: List[Dict[str, Any]] = []
    id_escena_counter = 1
    
    autores_originales_map_comentarios = {f"c{i+1}": com.autor for i, com in enumerate(datos_entrada.comentarios)}
    autor_post_original_scraper = "Autor del Post" # Placeholder; idealmente vendría del scraper para el post

    segmentos_post: List[SegmentoNarrativo] = []
    texto_escena_post_completo = ""
    if titulo_procesado_es:
        partes_del_guion.append(titulo_procesado_es)
        segmentos_post.append(SegmentoNarrativo(tipo_segmento="titulo_post", texto_es=titulo_procesado_es, autor=autor_post_original_scraper, id_original_segmento="post_titulo"))
        texto_escena_post_completo = titulo_procesado_es
    if cuerpo_post_procesado_es: # Solo añadir si existe
        partes_del_guion.append(cuerpo_post_procesado_es)
        segmentos_post.append(SegmentoNarrativo(tipo_segmento="cuerpo_post", texto_es=cuerpo_post_procesado_es, autor=autor_post_original_scraper, id_original_segmento="post_cuerpo"))
        if texto_escena_post_completo: texto_escena_post_completo += "\n\n"
        texto_escena_post_completo += cuerpo_post_procesado_es
    
    if texto_escena_post_completo.strip():
        escenas_pre_estructuradas.append({
            "id_escena": f"escena_{id_escena_counter:02d}_post",
            "texto_escena_es": texto_escena_post_completo.strip(),
            "origen_contenido": OrigenContenidoEscena(tipo="post_principal", autor_original=autor_post_original_scraper, id_referencia_original="post_principal"),
            "segmentos_narrativos": segmentos_post,
            "referencia_contenido_original_id": "post_principal",
            "titulo_escena": None 
        })
        id_escena_counter += 1

    for com_llm_data in comentarios_con_texto_procesado_llm1:
        id_orig_com = com_llm_data.get("id_original_comentario")
        texto_com_proc = com_llm_data.get("texto_original_comentario", "")
        autor_com = autores_originales_map_comentarios.get(id_orig_com, "un usuario")
        if not texto_com_proc: continue
        segmentos_de_esta_escena_com: List[SegmentoNarrativo] = []
        segmentos_de_esta_escena_com.append(SegmentoNarrativo(
            tipo_segmento="comentario_principal", autor=autor_com, texto_es=texto_com_proc, id_original_segmento=id_orig_com
        ))
        partes_del_guion.append(texto_com_proc)
        texto_concatenado_para_escena_com = texto_com_proc
        subs_llm_data = com_llm_data.get("subcomentarios_originales", [])
        for sub_llm_data in subs_llm_data:
            id_orig_sub = sub_llm_data.get("id_original_subcomentario")
            texto_sub_proc = sub_llm_data.get("texto_original_subcomentario", "")
            autor_sub = "otro participante" # Placeholder para autor de subcomentario
            if texto_sub_proc:
                segmentos_de_esta_escena_com.append(SegmentoNarrativo(
                    tipo_segmento="subcomentario", autor=autor_sub, texto_es=texto_sub_proc, id_original_segmento=id_orig_sub
                ))
                partes_del_guion.append(texto_sub_proc)
                texto_concatenado_para_escena_com += f"\n\n{texto_sub_proc}"
        escenas_pre_estructuradas.append({
            "id_escena": f"escena_{id_escena_counter:02d}_com_{id_orig_com}",
            "texto_escena_es": texto_concatenado_para_escena_com.strip(),
            "origen_contenido": OrigenContenidoEscena(tipo="comentario_con_subs", autor_original=autor_com, id_referencia_original=id_orig_com),
            "segmentos_narrativos": segmentos_de_esta_escena_com,
            "referencia_contenido_original_id": id_orig_com,
            "titulo_escena": None
        })
        id_escena_counter += 1
    guion_narrativo_completo_es = "\n\n".join(partes_del_guion).strip()
    print(f"Servicio Texto: (Paso 2) Guion ensamblado. {len(escenas_pre_estructuradas)} escenas pre-estructuradas.")

    # == LLAMADA A OPENAI #2: Titulación de Escena Principal ==
    if escenas_pre_estructuradas and escenas_pre_estructuradas[0]["referencia_contenido_original_id"] == "post_principal":
        escena_post_dict = escenas_pre_estructuradas[0]
        prompt_llm2 = f"""Eres un experto en crear títulos llamativos y concisos para segmentos de historias.
Te proporcionaré el texto de la sección principal de una historia extraída de Reddit: "{escena_post_dict["texto_escena_es"]}"
Tu tarea es generar un título corto, descriptivo y atractivo en español (máximo 5-8 palabras) para esta sección de la historia.
El título debe capturar la esencia del texto proporcionado.
Devuelve tu respuesta EXCLUSIVAMENTE en formato JSON con la siguiente estructura:
{{
  "titulo_escena_generado": "EL_TITULO_QUE_HAS_CREADO"
}}"""
        try:
            respuesta_llm2 = await _llamar_openai_api(prompt_llm2, f"Paso3_TituloEscena_{escena_post_dict['id_escena']}")
            escena_post_dict["titulo_escena"] = respuesta_llm2.get("titulo_escena_generado")
        except ValueError as e: 
            print(f"Servicio Texto: Error titulando escena post: {e}. Título será None.")
            escena_post_dict["titulo_escena"] = None # Asegurar que el campo exista
    print(f"Servicio Texto: (Paso 3) Titulación escena principal completada. Título: {escenas_pre_estructuradas[0].get('titulo_escena') if escenas_pre_estructuradas else 'N/A'}")
    
    # == LLAMADA A OPENAI #3: Elementos Globales (Keywords y Prompts IA) ==
    palabras_clave_globales_generadas: List[str] = []
    prompts_globales_ia_obj_list: List[GlobalImagePrompt] = []
    prompt_llm3 = f"""Eres un analista de contenido y director creativo experto en la producción de videos para YouTube. Te proporcionaré el guion narrativo completo de un video basado en una historia de Reddit.
Tu tarea es analizar este guion y generar:
1.  Una lista de 3 a 7 **palabras clave globales** (en español) que representen los temas principales, el ambiente o los elementos más destacados de toda la historia. Usar para buscar imágenes/videos de stock. Concisas y efectivas.
2.  Una lista de 1 a 3 **prompts globales para imágenes IA**. Para miniaturas, intros, o imágenes conceptuales. Cada prompt debe incluir: `id_prompt_global` (ej: "global_img_prompt_1"), `descripcion_visual` (detallada), `estilo_sugerido` (ej: "cinemático").
Devuelve tu respuesta EXCLUSIVAMENTE en formato JSON con la siguiente estructura:
{{
  "palabras_clave_globales_stock": ["palabra_clave_1", ...],
  "prompts_globales_imagenes_ia": [ {{ "id_prompt_global": "ID_1", "descripcion_visual": "...", "estilo_sugerido": "..." }} ]
}}
Guion narrativo completo:
---
{guion_narrativo_completo_es}
---
"""
    try:
        respuesta_llm3 = await _llamar_openai_api(prompt_llm3, "Paso4_ElementosGlobales")
        palabras_clave_globales_generadas = respuesta_llm3.get("palabras_clave_globales_stock", [])
        for p_data in respuesta_llm3.get("prompts_globales_imagenes_ia", []):
            try: prompts_globales_ia_obj_list.append(GlobalImagePrompt(**p_data))
            except Exception as val_err: print(f"Servicio Texto: Error validando prompt global IA: {val_err}, Data: {p_data}")
    except ValueError as e: print(f"Servicio Texto: Error generando elementos globales: {e}.")
    print(f"Servicio Texto: (Paso 4) Elementos globales generados. Keywords: {len(palabras_clave_globales_generadas)}, Prompts: {len(prompts_globales_ia_obj_list)}")

    # == LLAMADAS A OPENAI #4...N: Elementos por Escena (Keywords y Prompts IA) ==
    print(f"Servicio Texto: (Paso 5) Iniciando generación de elementos para {len(escenas_pre_estructuradas)} escenas.")
    for escena_dict in escenas_pre_estructuradas:
        titulo_para_prompt_escena = escena_dict.get("titulo_escena", "")
        texto_para_prompt_escena = escena_dict["texto_escena_es"]
        id_escena_actual = escena_dict["id_escena"]
        prompt_llm_escena = f"""Eres un analista de contenido y director de arte. Te proporcionaré el texto y título (si existe) de UNA escena.
Tu tarea es generar:
1.  Una lista de 2 a 5 **palabras clave específicas de la escena** (en español) relevantes para ESTA escena.
2.  Una lista de 1 a 2 **prompts específicos para imágenes IA para esta escena**. Cada prompt: `id_prompt_escena` (ej: "{id_escena_actual}_img_1"), `descripcion_visual` (detallada para la escena), `personajes_clave` (opcional), `emocion_principal` (opcional), `estilo_sugerido`.
Devuelve tu respuesta EXCLUSIVAMENTE en formato JSON:
{{
  "palabras_clave_stock_escena": ["palabra_1", ...],
  "prompts_imagenes_ia_escena": [ {{ "id_prompt_escena": "...", "descripcion_visual": "...", ... }} ]
}}
Contenido de la escena a procesar:
---
TITULO_DE_LA_ESCENA (si existe): {titulo_para_prompt_escena if titulo_para_prompt_escena else "N/A"}
TEXTO_DE_LA_ESCENA:
{texto_para_prompt_escena}
---
"""
        try:
            respuesta_llm_escena = await _llamar_openai_api(prompt_llm_escena, f"Paso5_ElementosEscena_{id_escena_actual}")
            escena_dict["palabras_clave_stock_escena"] = respuesta_llm_escena.get("palabras_clave_stock_escena", [])
            prompts_escena_obj_list_temp: List[SceneImagePrompt] = []
            for p_data in respuesta_llm_escena.get("prompts_imagenes_ia_escena", []):
                try:
                    if "id_prompt_escena" not in p_data or not p_data["id_prompt_escena"]:
                        p_data["id_prompt_escena"] = f"{id_escena_actual}_img_prompt_{len(prompts_escena_obj_list_temp)+1}"
                    prompts_escena_obj_list_temp.append(SceneImagePrompt(**p_data))
                except Exception as val_err: print(f"Servicio Texto: Error validando prompt de escena {id_escena_actual}: {val_err}, Data: {p_data}")
            escena_dict["prompts_imagenes_ia_escena"] = prompts_escena_obj_list_temp
        except ValueError as e:
            print(f"Servicio Texto: Error generando elementos para escena {id_escena_actual}: {e}.")
            escena_dict["palabras_clave_stock_escena"] = []
            escena_dict["prompts_imagenes_ia_escena"] = []
        escena_dict["duracion_estimada_narracion_seg"] = 0.0 # Inicializar antes de calcular
    print(f"Servicio Texto: (Paso 5) Elementos por escena generados.")

    # == LÓGICA PYTHON: Cálculo de Duración Estimada por Escena ==
    palabras_por_minuto = settings.NARRATION_PPM
    if palabras_por_minuto <= 0: palabras_por_minuto = 140 
    for escena_dict in escenas_pre_estructuradas:
        texto_duracion = escena_dict.get("texto_escena_es", "")
        num_palabras = len(texto_duracion.split()) if texto_duracion else 0
        escena_dict["duracion_estimada_narracion_seg"] = round((num_palabras / palabras_por_minuto) * 60, 2) if num_palabras > 0 else 0.0
    print(f"Servicio Texto: (Paso 6) Cálculo de duración completado.")

    # == LÓGICA PYTHON: Ensamblaje Final de la Respuesta TextProcessingResponse ==
    escenas_final_obj_list: List[EscenaProcesada] = []
    for esc_dict in escenas_pre_estructuradas:
        segmentos_narrativos_obj = [seg if isinstance(seg, SegmentoNarrativo) else SegmentoNarrativo(**seg) for seg in esc_dict.get("segmentos_narrativos", [])]
        prompts_imgs_obj = [p if isinstance(p, SceneImagePrompt) else SceneImagePrompt(**p) for p in esc_dict.get("prompts_imagenes_ia_escena", [])]
        
        escenas_final_obj_list.append(
            EscenaProcesada(
                id_escena=esc_dict["id_escena"],
                titulo_escena=esc_dict.get("titulo_escena"),
                texto_escena_es=esc_dict["texto_escena_es"],
                origen_contenido=esc_dict["origen_contenido"],
                segmentos_narrativos=segmentos_narrativos_obj,
                palabras_clave_stock_escena=esc_dict.get("palabras_clave_stock_escena", []),
                prompts_imagenes_ia_escena=prompts_imgs_obj,
                duracion_estimada_narracion_seg=esc_dict.get("duracion_estimada_narracion_seg")
            )
        )
    
    resumen_general_es_final = "Resumen general del contenido (aún no implementada su generación)."

    final_response = TextProcessingResponse(
        id_proyecto=datos_entrada.id_proyecto,
        idioma_original_detectado=idioma_detectado,
        titulo_procesado_es=titulo_procesado_es,
        guion_narrativo_completo_es=guion_narrativo_completo_es,
        resumen_general_es=resumen_general_es_final,
        palabras_clave_globales_stock=palabras_clave_globales_generadas,
        prompts_globales_imagenes_ia=prompts_globales_ia_obj_list,
        escenas=escenas_final_obj_list
    )
    print("Servicio Texto: (Paso 7) Ensamblaje final de TextProcessingResponse completado.")
    return final_response