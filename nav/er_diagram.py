import os
from graphviz import Digraph

# Create a new directed graph for the Entity-Relationship (ER) Diagram
er_diagram = Digraph('ER Diagram', format='png')
er_diagram.attr(rankdir='LR')  # Setter layout til vannrett (Left to Right)

# Add entities (tables) with their attributes
er_diagram.node('Medlemmer', shape='box',
                label='Medlemmer\n- Medlemsnummer (PK)\n- Fornavn\n- Etternavn\n-  Fødselsdato\n- Kjønn\n-  Medlemstype\n- Gateadresse'
                      '\n -  Postnummer\n- Poststed')
er_diagram.node('Betalinger', shape='box',
                label='Betalinger\n- Medlemsnummer (FK)\n- Beløp\n Periode\n- Innbetalt_dato')
er_diagram.node('Kontingent', shape='box',
                label='Kontingent\n- Medlemstype (PK)\n- Periode (PK)\n- Kontingent\n -Aldersgrupe\n')
er_diagram.edge('Medlemmer', 'Betalinger', label='1:M\nvia Medlemsnummer')
er_diagram.edge('Medlemmer', 'Kontingent', label='1:M\nvia Medlemstype')

# Add an indirect relationship between 'Betalinger' and 'Kontingent'
er_diagram.edge('Betalinger', 'Kontingent', label='Indirekte\nvia Medlemstype og Periode', style='dotted')

# Save and render the ER diagram as a PNG file and display it

chart_dir = os.path.dirname(__file__) + '/flow_charts/'

if not os.path.exists(chart_dir):
    os.makedirs(chart_dir)

er_diagram.render(chart_dir + 'er_diagram', view=True)
