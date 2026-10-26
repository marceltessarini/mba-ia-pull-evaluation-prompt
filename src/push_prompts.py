"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

DICAS DE IMPLEMENTAÇÃO:

- O push é feito pelo cliente do LangSmith:

      from langsmith import Client
      from langchain_core.prompts import ChatPromptTemplate

      client = Client()
      prompt = ChatPromptTemplate.from_messages([
          ("system", system_prompt),
          ("user", user_prompt),
      ])
      url = client.push_prompt(
          f"{username}/bug_to_user_story_v2",
          object=prompt,
          is_public=True,
          description="...",
          tags=[...],
      )

- `username` vem de USERNAME_LANGSMITH_HUB no .env e precisa ser o seu handle
  do Hub. Se você ainda não tem um handle, veja as instruções no .env.example.

- A variável do template precisa ser {bug_report}, que é a chave de entrada
  usada no dataset de avaliação.

- Use `load_yaml` de utils.py para ler o arquivo .yml.
"""

import os
import sys
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header

load_dotenv()


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    user_name = os.getenv("USERNAME_LANGSMITH_HUB", "")

    keys = list(prompt_data.keys())
    if len(keys) == 1 and isinstance(prompt_data[keys[0]], dict):
        content = prompt_data[keys[0]]
    else:
        content = prompt_data

    system_prompt = content.get("system_prompt")
    user_prompt = content.get("user_prompt")
    description = content.get("description", "")
    tags = content.get("tags", [])

    if not system_prompt or not user_prompt:
        print("Erro: 'system_prompt' ou 'user_prompt' não encontrados nos dados do prompt.")
        return False

    try:
        client = Client()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", user_prompt),
        ])
        
        url = client.push_prompt(
            f"{user_name}/{prompt_name}",
            object=prompt,
            is_public=True,
            description=description,
            tags=tags,
        )
        
        print(f"Prompt enviado com sucesso! URL: {url}")
        return True
        
    except Exception as e:
        print(f"Erro ao realizar o push para o LangSmith: {e}")
        return False

def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    errors = []

    if not (isinstance(prompt_data, dict) and prompt_data):
        return False, ["O prompt_data deve ser um dicionário não vazio."]

    # Trata caso o YAML venha encapsulado por uma chave raiz (ex: bug_to_user_story_v2)
    keys = list(prompt_data.keys())
    if len(keys) == 1 and isinstance(prompt_data[keys[0]], dict):
        content = prompt_data[keys[0]]
    else:
        content = prompt_data

    # Definição dos campos obrigatórios e seus respectivos tipos esperados
    required_fields = {
        "description": str,
        "system_prompt": str,
        "user_prompt": str,
        "version": str,
        "created_at": str,
        "tags": list
    }

    # Validação de presença e tipo de cada campo obrigatório
    for field, expected_type in required_fields.items():
        if field not in content:
            errors.append(f"O campo obrigatório '{field}' está ausente.")
        elif not isinstance(content[field], expected_type):
            type_name = expected_type.__name__
            errors.append(f"O campo '{field}' deve ser do tipo {type_name}.")

    is_valid = len(errors) == 0
    return is_valid, errors


def main():
    prompt_name = "bug_to_user_story_v2"
    file_path = "prompts/{name}.yml".format(name=prompt_name)
    prompt_data = load_yaml(file_path)

    is_valid, errors = validate_prompt(prompt_data)

    if not is_valid:
        print(f"Atenção! O prompt em '{file_path}' apresenta erros de estrutura:")
        for error in errors:
            print(f"  - {error}")
        return

    print(f"Sucesso! O prompt em '{file_path}' está perfeitamente válido.")

    push_prompt_to_langsmith(prompt_name, prompt_data)



if __name__ == "__main__":
    sys.exit(main())
