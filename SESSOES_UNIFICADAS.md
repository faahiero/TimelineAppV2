# 📂 Sessões Unificadas - Guia de Uso

## 🎯 Funcionalidade

A funcionalidade de **Sessões Unificadas** permite carregar uma sessão salva e escolher entre visualizá-la ou trabalhar com ela (adicionando novas personalidades), oferecendo máxima flexibilidade no gerenciamento de coleções.

## 🔄 Como Funciona

### Fluxo Unificado:
1. Fazer buscas iniciais → Salvar como sessão
2. **Carregar sessão** → Escolher modo:
   - **Visualização**: Apenas gerar gráficos (não modifica)
   - **Trabalho**: Adicionar novas buscas e expandir a coleção
3. Salvar sessão atualizada quando desejar

## 📋 Opções do Menu

- **[4]** - Salvar dados da busca atual como sessão
- **[5]** - **Carregar sessão (visualizar ou adicionar buscas)** ⭐ (UNIFICADO)

## 🚀 Exemplo Prático

### Cenário: Criando uma coleção "Escritores Brasileiros"

1. **Primeira sessão:**
   ```
   [1] Buscar: "Machado de Assis"
   [1] Buscar: "Clarice Lispector"
   [4] Salvar como sessão: "escritores_brasileiros"
   ```

2. **Trabalhando com a sessão:**
   ```
   [5] Carregar sessão: "escritores_brasileiros"
   → Escolher: [1] Carregar para trabalho
   [1] Buscar: "Carlos Drummond de Andrade"
   [1] Buscar: "Cecília Meireles"
   [2] Gerar visualização (agora com 4 escritores)
   [4] Salvar sessão atualizada
   ```

3. **Apenas visualizando:**
   ```
   [5] Carregar sessão: "escritores_brasileiros"
   → Escolher: [2] Apenas visualizar
   (Gera visualização sem modificar a sessão original)
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

- **Função**: `manage_sessions(sessions_dir, "load")` com escolha de modo
- **Arquivo**: `modules/utils.py`
- **Status**: `get_current_session_info()` e `show_session_status()`
- **Menu**: Opção [5] unificada substituindo [5] e [7] anteriores
- **Retorno**: Dicionário com `{"type": "work|view", "file": nome, "path": caminho}`