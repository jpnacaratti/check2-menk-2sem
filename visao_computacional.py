#!/usr/bin/env python3
"""Envia uma imagem local ao Azure Computer Vision e imprime sua descrição."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def carregar_configuracao_local() -> None:
    """Carrega variáveis de um .env local sem exigir bibliotecas externas."""
    arquivo_env = Path(__file__).resolve().with_name(".env")
    if not arquivo_env.is_file():
        return

    for linha in arquivo_env.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue

        nome, valor = linha.split("=", 1)
        nome = nome.strip()
        valor = valor.strip().strip('"').strip("'")
        if nome and valor:
            os.environ.setdefault(nome, valor)


def analisar_imagem(
    caminho: Path, numero_chave: str
) -> tuple[str, float | None, list[dict[str, object]]]:
    carregar_configuracao_local()

    endpoint = os.environ.get("AZURE_VISION_ENDPOINT", "").strip().rstrip("/")
    chave = os.environ.get(f"AZURE_VISION_KEY_{numero_chave}", "").strip()

    if not endpoint:
        raise ValueError("Defina AZURE_VISION_ENDPOINT no arquivo .env.")
    if not chave:
        raise ValueError(
            f"Defina AZURE_VISION_KEY_{numero_chave} no arquivo .env "
            f"ou escolha --chave {1 if numero_chave == '2' else 2}."
        )

    parametros = urlencode(
        {
            "overload": "stream",
            "visualFeatures": "Tags,Description",
            "language": "pt",
        }
    )
    url = f"{endpoint}/vision/v3.2/analyze?{parametros}"
    requisicao = Request(
        url,
        data=caminho.read_bytes(),
        headers={
            "Ocp-Apim-Subscription-Key": chave,
            "Content-Type": "application/octet-stream",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(requisicao, timeout=60) as resposta:
            resultado = json.loads(resposta.read().decode("utf-8"))
    except HTTPError as erro:
        corpo = erro.read().decode("utf-8", errors="replace")
        try:
            detalhe = json.loads(corpo).get("error", {}).get("message", corpo)
        except json.JSONDecodeError:
            detalhe = corpo or erro.reason
        raise RuntimeError(f"Azure respondeu HTTP {erro.code}: {detalhe}") from erro
    except URLError as erro:
        raise RuntimeError(f"Não foi possível conectar à Azure: {erro.reason}") from erro
    except json.JSONDecodeError as erro:
        raise RuntimeError("A Azure retornou uma resposta que não é JSON válido.") from erro

    legendas = resultado.get("description", {}).get("captions", [])
    if not legendas or not legendas[0].get("text"):
        raise RuntimeError(
            "A API respondeu, mas não retornou uma descrição para esta imagem."
        )

    tags = resultado.get("tags", [])
    return legendas[0]["text"], legendas[0].get("confidence"), tags


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera uma descrição em português para uma imagem usando o Azure Computer Vision."
    )
    parser.add_argument("imagem", type=Path, help="Caminho da imagem local")
    parser.add_argument(
        "--chave",
        choices=("1", "2"),
        default="1",
        help="Chave da Azure a usar (padrão: 1)",
    )
    argumentos = parser.parse_args()

    caminho = argumentos.imagem.expanduser()
    if not caminho.is_file():
        print(f"Arquivo de imagem não encontrado: {caminho}", file=sys.stderr)
        return 2

    print(f"Enviando imagem: {caminho}")
    try:
        descricao, confianca, tags = analisar_imagem(caminho, argumentos.chave)
    except (OSError, ValueError, RuntimeError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1

    print(f"Resposta da API: {descricao}")
    if isinstance(confianca, (int, float)):
        print(f"Confiança: {confianca:.1%}")
    if tags:
        print("Tags:")
        for tag in tags:
            nome = tag.get("name")
            if not nome:
                continue
            score = tag.get("confidence")
            if isinstance(score, (int, float)):
                print(f"- {nome} ({score:.1%})")
            else:
                print(f"- {nome}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
