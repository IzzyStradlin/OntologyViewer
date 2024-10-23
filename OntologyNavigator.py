import rdflib
import networkx as nx
import plotly.graph_objects as go
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox, scrolledtext
import re
import threading

# Function to load TTL or RDF file (ontology)
def load_ontology(ttl_file):
    g = rdflib.Graph()
    g.parse(ttl_file, format="ttl")
    return g

# Function to check if a string is alphanumeric and longer than 20 characters
def is_alphanumeric(s):
    return bool(re.match(r'^[a-zA-Z0-9]{15,}$', s))

# Function to create the graph with NetworkX, hiding nodes with alphanumeric labels longer than 20 characters
def create_graph(ontology):
    G = nx.DiGraph()
    
    for subj, pred, obj in ontology:
        if not (is_alphanumeric(str(subj)) or is_alphanumeric(str(obj))):
            G.add_edge(subj, obj, label=pred)
    
    return G

# Function to visualize the graph in 3D with Plotly
def visualize_graph(graph):
    pos = nx.spring_layout(graph, dim=3)  # Position of nodes in 3D

    # Nodes
    nodes_x = [pos[n][0] for n in graph.nodes()]
    nodes_y = [pos[n][1] for n in graph.nodes()]
    nodes_z = [pos[n][2] for n in graph.nodes()]

    # Node colors based on the number of connections
    nodes_color = [len(list(graph.neighbors(n))) for n in graph.nodes()]
    nodes_color = [(c - min(nodes_color)) / (max(nodes_color) - min(nodes_color)) for c in nodes_color]  # Normalize colors

    # Edges
    edges_x = []
    edges_y = []
    edges_z = []
    edge_labels = []
    for edge in graph.edges(data=True):
        edges_x += [pos[edge[0]][0], pos[edge[1]][0], None]
        edges_y += [pos[edge[0]][1], pos[edge[1]][1], None]
        edges_z += [pos[edge[0]][2], pos[edge[1]][2], None]
        edge_labels.append(str(edge[2]['label']))

    # Create the 3D visualization with Plotly
    trace_nodes = go.Scatter3d(
        x=nodes_x,
        y=nodes_y,
        z=nodes_z,
        mode='markers',
        marker=dict(size=[max(10, 40 * c) for c in nodes_color], color=nodes_color, colorscale='Viridis', showscale=True),
        hoverinfo='text',
        name='nodes',
        text=[]  # Leave empty here
    )

    trace_edges = go.Scatter3d(
        x=edges_x,
        y=edges_y,
        z=edges_z,
        mode='lines',
        line=dict(width=2, color='gray'),
        hoverinfo='text',
        name='edges',
        text=edge_labels  # Show edge label (predicate) on hover
    )

    # Add the link as part of the node tooltip
    nodes_tooltip = []
    for node in graph.nodes():
        link = f"http://{node}"  # Ensure nodes contain valid URLs
        nodes_tooltip.append(f"{node}<br><a href='{link}' target='_blank'>Open link</a>")

    # Set tooltips
    trace_nodes.text = nodes_tooltip

    # Create a new figure
    fig = go.Figure(data=[trace_edges, trace_nodes])

    layout = go.Layout(
        title='RDF Graph Visualization in 3D',
        showlegend=False,
        hovermode='closest',
        margin=dict(b=0, l=0, r=0, t=40),
        scene=dict(
            xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(showgrid=False, zeroline=False),
            zaxis=dict(showgrid=False, zeroline=False)
        )
    )

    fig.update_layout(layout)
    fig.show()

# Function to execute a SPARQL query
def execute_query(ontology, query):
    try:
        result = ontology.query(query)
        return "\n".join([str(row) for row in result])
    except Exception as e:
        return f"Error executing query: {e}"

# Function to manage file loading through the GUI
def load_file():
    ttl_file = filedialog.askopenfilename(
        title="Select Ontology file (TTL or RDF)", 
        filetypes=[("TTL or RDF files", "*.ttl *.rdf")]
    )
    
    if ttl_file:
        try:
            global ontology
            ontology = load_ontology(ttl_file)
            graph = create_graph(ontology)
            threading.Thread(target=visualize_graph, args=(graph,)).start()  # Run visualization in a separate thread
        except Exception as e:
            messagebox.showerror("Error", f"Error loading the file: {e}")
    else:
        messagebox.showwarning("Warning", "No file selected")

# Function to manage SPARQL query execution
def execute_sparql_query():
    query = query_text.get("1.0", tk.END).strip()
    if ontology:
        result = execute_query(ontology, query)
        result_text.delete("1.0", tk.END)
        result_text.insert(tk.END, result)
    else:
        messagebox.showwarning("Warning", "Please load a .ttl or .rdf file first")

# Create the Tkinter window
def create_interface():
    root = tk.Tk()
    root.title("RDF Ontology Viewer with SPARQL Query")
    
    # Window configuration
    label = tk.Label(root, text="Load a TTL or RDF file to visualize the RDF graph and run SPARQL queries")
    label.pack(pady=20)
    
    # Button to load the file
    btn_load = tk.Button(root, text="Load Ontology", command=load_file)
    btn_load.pack(pady=10)
    
    # Text for entering the SPARQL query
    global query_text
    query_text = scrolledtext.ScrolledText(root, height=8, width=60)
    query_text.pack(pady=10)
    query_text.insert(tk.END, "Enter your SPARQL query here...")
    
    # Button to execute the query
    btn_execute = tk.Button(root, text="Execute SPARQL Query", command=execute_sparql_query)
    btn_execute.pack(pady=10)
    
    # Text to display the query results
    global result_text
    result_text = scrolledtext.ScrolledText(root, height=10, width=60)
    result_text.pack(pady=10)
    
    # Start the GUI
    root.geometry("700x600")
    root.mainloop()

# Start the interface
ontology = None  # Global variable to store the loaded ontology
create_interface()
