import dash
from dash import html, dcc, Input, Output, clientside_callback
import dash_bootstrap_components as dbc

class NoUiSlider:
    """Componente NoUiSlider para Dash - Alternativa ao dcc.RangeSlider"""
    
    @staticmethod
    def create_component(min_val=-50, max_val=50, default_min=-10, default_max=20, 
                         component_id='nouislider-range', marks=None):
        """
        Cria um slider NoUi como componente Dash
        
        Args:
            min_val: Valor mínimo do slider
            max_val: Valor máximo do slider  
            default_min: Valor inicial do handle esquerdo
            default_max: Valor inicial do handle direito
            component_id: ID do componente
            marks: Dicionário de marks personalizados
        """
        
        if marks is None:
            marks = {
                -50: '50 a.C.',
                -25: '25 a.C.',
                0: '0',
                25: '25 d.C.',
                50: '50 d.C.'
            }
        
        return html.Div([
            # Container do slider
            html.Div(id=component_id, style={
                'margin': '20px 0',
                'height': '40px'
            }),
            
            # Input oculto para armazenar valores
            dcc.Input(id=f'{component_id}-value', type='text', style={'display': 'none'}),
            
            # CSS e JS do NoUiSlider
            html.Link(
                rel="stylesheet", 
                href="https://cdnjs.cloudflare.com/ajax/libs/noUiSlider/15.7.1/nouislider.min.css"
            ),
            
            # Script de inicialização
            html.Script(f"""
                document.addEventListener('DOMContentLoaded', function() {{
                    var sliderContainer = document.getElementById('{component_id}');
                    var hiddenInput = document.getElementById('{component_id}-value');
                    
                    if (sliderContainer && !sliderContainer.noUiSlider) {{
                        noUiSlider.create(sliderContainer, {{
                            start: [{default_min}, {default_max}],
                            connect: true,
                            behaviour: 'drag',
                            range: {{
                                'min': {min_val},
                                'max': {max_val}
                            }},
                            step: 1,
                            tooltips: true,
                            format: {{
                                to: function(value) {{
                                    return value > 0 ? value + ' d.C.' : Math.abs(value) + ' a.C.';
                                }},
                                from: function(value) {{
                                    if (typeof value === 'string') {{
                                        if (value.includes('a.C.')) {{
                                            return -parseInt(value);
                                        }} else if (value.includes('d.C.')) {{
                                            return parseInt(value);
                                        }}
                                    }}
                                    return parseFloat(value);
                                }}
                            }},
                            pips: {{
                                mode: 'positions',
                                values: [0, 25, 50, 75, 100],
                                density: 4
                            }}
                        }});
                        
                        // Event listener para mudanças
                        sliderContainer.noUiSlider.on('change', function(values) {{
                            hiddenInput.value = JSON.stringify(values);
                            hiddenInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        }});
                    }}
                }});
            """),
            
            # Script principal do NoUiSlider
            html.Script(src="https://cdnjs.cloudflare.com/ajax/libs/noUiSlider/15.7.1/nouislider.min.js"),
            
        ], style={'width': '100%'})


# Função de integração para substituir o range_slider.py existente
def create_nouislider_for_centuries(dataframe, component_id='seculo-slider-nouislider'):
    """
    Adaptador para manter compatibilidade com a estrutura atual
    
    Args:
        dataframe: DataFrame com dados dos séculos
        component_id: ID do componente
        
    Returns:
        Componente NoUiSlider configurado
    """
    
    # Extrair valores dos séculos como no código original
    seculo_values = dataframe['Século'].unique()
    seculo_values_int = []
    
    for valor in seculo_values:
        if "a.C." in str(valor):
            valor_int = -int(valor.replace(" a.C.", ""))
        else:
            valor_int = int(valor)
        seculo_values_int.append(valor_int)
    
    if not seculo_values_int:
        seculo_min, seculo_max = -50, 50
    else:
        seculo_min = min(seculo_values_int)
        seculo_max = max(seculo_values_int)
    
    # Correção para evitar crash quando min == max
    if seculo_min == seculo_max:
        seculo_min -= 1
        seculo_max += 1
    
    return NoUiSlider.create_component(
        min_val=seculo_min,
        max_val=seculo_max,
        default_min=seculo_min,
        default_max=seculo_max,
        component_id=component_id
    )