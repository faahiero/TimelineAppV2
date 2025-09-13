# 📂 Sessões Incrementais - Guia de Uso

## 🎯 Funcionalidade

A funcionalidade de **Sessões Incrementais** permite carregar uma sessão salva e continuar adicionando novas personalidades a ela, criando coleções temáticas ou expandindo pesquisas existentes.

## 🔄 Como Funciona

### Fluxo Tradicional (antes):
1. Fazer buscas → Gerar visualização → Dados movidos para `data/`
2. Novas buscas começam do zero

### Fluxo Incremental (novo):
1. Fazer buscas iniciais → Salvar como sessão
2. **Carregar sessão incremental** → Adicionar novas buscas → Visualizar tudo junto
3. Salvar sessão atualizada quando desejar

## 📋 Opções do Menu

- **[4]** - Salvar dados da busca atual como sessão
- **[5]** - Carregar sessão e gerar visualização (somente leitura)
- **[7]** - **Carregar sessão para adicionar novas buscas** ⭐ (NOVO)

## 🚀 Exemplo Prático

### Cenário: Criando uma coleção "Escritores Brasileiros"

1. **Primeira sessão:**
   ```
   [1] Buscar: "Machado de Assis"
   [1] Buscar: "Clarice Lispector"
   [4] Salvar como sessão: "escritores_brasileiros"
   ```

2. **Expandindo a sessão:**
   ```
   [7] Carregar sessão incremental: "escritores_brasileiros"
   [1] Buscar: "Carlos Drummond de Andrade"
   [1] Buscar: "Cecília Meireles"
   [2] Gerar visualização (agora com 4 escritores)
   [4] Salvar sessão atualizada
   ```

## 📊 Status da Sessão

O menu agora mostra informações detalhadas da sessão ativa:

```
📊 STATUS DA SESSÃO ATUAL:
   • 4 personalidade(s) única(s)
   • 1 país(es) diferente(s)
   • 2 século(s) diferente(s)
   • Personalidades: Machado de Assis, Clarice Lispector, Carlos Drummond...
```

## 💡 Casos de Uso

### 🎭 **Coleções Temáticas**
- Escritores de um país
- Cientistas de uma época
- Artistas de um movimento

### 🌍 **Pesquisas Comparativas**
- Personalidades de diferentes países
- Evolução temporal de uma área
- Influências geográficas

### 📚 **Pesquisa Acadêmica**
- Construir base de dados gradualmente
- Adicionar descobertas ao longo do tempo
- Manter contexto entre sessões

## ⚠️ Observações Importantes

1. **Arquivo Ativo**: A sessão carregada substitui o `person_info.csv` atual
2. **Backup Automático**: Sessões são sempre salvas com timestamp
3. **Duplicatas**: O sistema evita adicionar a mesma personalidade duas vezes
4. **Visualização**: Todos os gráficos incluem dados da sessão completa

## 🔧 Implementação Técnica

- **Função**: `manage_sessions(sessions_dir, "load_incremental")`
- **Arquivo**: `modules/utils.py`
- **Status**: `get_current_session_info()` e `show_session_status()`
- **Menu**: Opção [7] adicionada ao fluxo principal