# 📓 Cadernos Jupyter de Teste e Depuração

Este diretório contém os cadernos interativos do Jupyter para testes unitários dos nós e depuração do grafo do **Chrono S. Thompson**.

## 🚀 Como Executar

### 1. Executando via `uv` (Recomendado)

Você pode iniciar o servidor do Jupyter Notebook diretamente usando o gerenciador de pacotes `uv`:

```bash
uv run jupyter notebook notebooks/chrono_graph_testing.ipynb
```

Ou usando o VS Code / PyCharm:
1. Abra o arquivo [`chrono_graph_testing.ipynb`](file:///d:/chrono-s-thompson/notebooks/chrono_graph_testing.ipynb).
2. Selecione o ambiente virtual `.venv` como o kernel Python.

---

## 🧪 Estrutura do Notebook `chrono_graph_testing.ipynb`

| Seção | Conteúdo |
|---|---|
| **0. Configuração do Ambiente** | Configuração de `sys.path`, `nest_asyncio` e logs |
| **1. Inspeção de Estado** | Validação das instâncias de `ChronoState` e Schemas Pydantic |
| **2. Fetcher Node** | Teste isolado da integração MCP Server (`fetch_events_node`) |
| **3. Ranker Node** | Teste isolado da curadoria com Structured Output (`rank_events_node`) |
| **4. Correlator Node** | Teste isolado da síntese contemporânea Tavily/LLM (`correlate_modern_node`) |
| **5. Writer Node** | Geração e visualização do artigo em Markdown (`write_article_node`) |
| **6. Grafo Completo** | Execução end-to-end com visualização Mermaid e `astream()` |
| **7. Playground** | Injeção de estados customizados para testes rápidos de borda |
