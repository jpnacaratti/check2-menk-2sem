# Azure Computer Vision: descrição de imagem

Aplicativo de linha de comando que envia uma imagem local ao recurso Azure Computer Vision e imprime a descrição retornada.

## Configuração

1. Copie `.env.example` para `.env`.
2. Preencha `AZURE_VISION_ENDPOINT`, `AZURE_VISION_KEY_1` e `AZURE_VISION_KEY_2` no `.env`.
3. Use Python 3.10 ou posterior. O script não precisa de pacotes adicionais.

O arquivo `.env` está no `.gitignore` para que as chaves não sejam incluídas no GitHub.

## Executar

No PowerShell, a partir desta pasta:

```powershell
python .\visao_computacional.py "Caminho da imagem"
```

Por padrão, o script usa a chave 1. Para usar a chave 2:

```powershell
python .\visao_computacional.py "Caminho da imagem" --chave 2
```

O script usa a operação `Analyze Image` da API Computer Vision v3.2, envia os bytes do arquivo local e solicita `Tags` e `Description` em português.
