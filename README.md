# SISURB MCP Juiz de Fora — V10

V10 atualiza a análise do envelope M3A com conferência do Anexo 8 da Lei 6.910/1986 e mantém a regra de não inventar parâmetros que não estejam suficientemente seguros para cálculo geométrico.

## M3A confirmado nesta versão
- Taxa de ocupação: 100% do 1º ao 3º pavimento, até 9,20 m de altura.
- Demais pavimentos: 65%.
- O CA de 2,8 permanece tratado como coeficiente condicionado pela marcação (*) do Anexo 8 e pela aplicabilidade ao lote/uso; o SISURB é usado para informar o parâmetro cadastral aplicável.
- 9,20 m NÃO é tratado como gabarito máximo total da edificação; é o limite da faixa de TO de 100%.

## Ainda pendente
- Recuo frontal e afastamentos laterais/fundos do M3A para cálculo geométrico automático.
- Gabarito/altura máxima total como regra legal.
- Efeito normativo das restrições espaciais identificadas pelo SISURB.

## Ferramentas
- `consultar_envelope_m3a_jf`: separa TO, faixa de altura e recuos/afastamentos.
- `comparar_limitantes_sisurb`: compara CA e TO×pavimentos como limites independentes; não multiplica CA×TO×pavimentos.

## Fonte oficial principal
Câmara Municipal de Juiz de Fora — Lei 6.910/1986 e alterações:
https://www.camarajf.mg.gov.br/sal/norma.php?njc=&njn=06910&njt=LEI

Anexo 8 oficial disponibilizado pela Câmara:
https://www.camarajf.mg.gov.br/sal/anexo.php?cod=55&t=nj
