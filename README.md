# SISURB Juiz de Fora MCP — V11

Versão 11 do conector MCP para análise urbanística preliminar em Juiz de Fora/MG.

## Alterações principais da V11

- **Não converte mais o campo cadastral `gabarito` do SISURB em número de pavimentos.**
- `consultar_envelope_m3a_jf` agora recebe apenas `pavimentos_confirmados`; o padrão é zero/PENDENTE.
- `calcular_potencial_preliminar` não calcula `TO × pavimentos` sem número de pavimentos legalmente confirmado.
- `comparar_limitantes_sisurb` não declara o CA como fator limitante global enquanto pavimentos, recuos/envelope ou efeitos normativos relevantes estiverem pendentes.
- A consulta de restrições passa a solicitar a geometria das feições e calcula, localmente com **Shapely**, a área de interseção em m² e o percentual do lote atingido.
- O total de área restrita usa união geométrica para evitar dupla contagem quando houver sobreposição entre restrições.
- O cálculo espacial da restrição é separado do seu **efeito jurídico/normativo**, que continua PENDENTE até confirmação legal.

## Regra M3A preservada

A ferramenta mantém como referência confirmada para M3A a faixa de TO de 100% do 1º ao 3º pavimento até 9,20 m e 65% nos demais pavimentos. Os 9,20 m **não são tratados como gabarito máximo total**. Recuos/afastamentos ainda permanecem pendentes de confirmação segura para cálculo geométrico.

## Implantação no Render

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
python server.py
```

Endpoint MCP:

```text
https://projeto-sisurb-mcp.onrender.com/mcp
```

## Teste recomendado

No Claude, após o deploy, digite somente:

```text
Rua São Mateus, 490
```

No novo relatório, verifique especialmente:

1. `gabarito = 3` aparece apenas como dado cadastral, sem virar automaticamente 3 pavimentos;
2. `TO × pavimentos` fica PENDENTE enquanto o número legal de pavimentos não estiver confirmado;
3. o fator limitante global fica PENDENTE se houver parâmetros essenciais ainda pendentes;
4. a restrição informa **área intersectada (m²)** e **percentual do lote (%)**, quando a geometria da camada estiver disponível.
