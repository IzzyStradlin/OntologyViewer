import rdflib
import networkx as nx
import plotly.graph_objects as go
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox, scrolledtext
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import re
import threading

# Function to load TTL, RDF, or OWL file (ontology)
def load_ontology(file_path):
    g = rdflib.Graph()
    # Determine the format based on the file extension
    if file_path.endswith(".ttl"):
        g.parse(file_path, format="ttl")
    elif file_path.endswith(".rdf"):
        g.parse(file_path, format="xml")  # RDF/XML format
    elif file_path.endswith(".owl"):
        g.parse(file_path, format="xml")  # OWL files are typically in RDF/XML format
    else:
        raise ValueError("Unsupported file format. Please select a .ttl, .rdf, or .owl file.")
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
    file_path = filedialog.askopenfilename(
        title="Select Ontology file (TTL, RDF, or OWL)", 
        filetypes=[("Ontology files", "*.ttl *.rdf *.owl")]
    )
    
    if file_path:
        try:
            global ontology
            ontology = load_ontology(file_path)
            graph = create_graph(ontology)
            threading.Thread(target=visualize_graph, args=(graph,)).start()  # Run visualization in a separate thread
        except Exception as e:
            messagebox.showerror("Error", f"Error loading the file: {e}")
    else:
        messagebox.showwarning("Warning", "No file selected")

# Function to manage SPARQL query execution
def execute_sparql_query():
    query = sparql_query_text.get("1.0", tk.END).strip()
    if ontology:
        result = execute_query(ontology, query)
        sparql_result_text.delete("1.0", tk.END)
        sparql_result_text.insert(tk.END, result)
    else:
        messagebox.showwarning("Warning", "Please load a .ttl, .rdf, or .owl file first")

# Function to handle natural language query execution
def execute_natural_language_query():
    natural_query = natural_query_text.get("1.0", tk.END).strip()
    if not natural_query:
        messagebox.showwarning("Warning", "Please enter a natural language query.")
        return

    # Placeholder for LLM integration
    sparql_query = f"Generated SPARQL query for: {natural_query}"  # Replace with actual LLM logic

    # Display the generated SPARQL query
    natural_result_text.delete("1.0", tk.END)
    natural_result_text.insert(tk.END, f"Generated SPARQL Query:\n{sparql_query}\n\n")

    # Execute the SPARQL query if an ontology is loaded
    if ontology:
        result = execute_query(ontology, sparql_query)
        natural_result_text.insert(tk.END, f"Query Results:\n{result}")
    else:
        natural_result_text.insert(tk.END, "No ontology loaded. Please load an ontology to execute the query.")

# Create the Tkinter window
def create_interface():
    root = ttk.Window(themename="cosmo")  # Usa un tema moderno come "cosmo", "flatly", "darkly"
    root.title("Ontology Viewer with SPARQL and Natural Language Queries")
    root.geometry("900x900")

    # Load Ontology Section
    load_frame = ttk.Frame(root, padding=10)
    load_frame.pack(fill=X, pady=10)

    load_label = ttk.Label(load_frame, text="Load a TTL, RDF, or OWL file:", font=("Arial", 12))
    load_label.pack(side=LEFT, padx=5)

    btn_load = ttk.Button(load_frame, text="Load Ontology", bootstyle=PRIMARY, command=load_file)
    btn_load.pack(side=LEFT, padx=5)

    # SPARQL Query Section
    sparql_frame = ttk.Labelframe(root, text="SPARQL Query", padding=10, bootstyle=INFO)
    sparql_frame.pack(fill=BOTH, expand=True, pady=10)

    global sparql_query_text
    sparql_query_text = ttk.ScrolledText(sparql_frame, height=8, width=80)
    sparql_query_text.pack(pady=5)
    sparql_query_text.insert("1.0", "Enter your SPARQL query here...")

    btn_execute_sparql = ttk.Button(sparql_frame, text="Execute SPARQL Query", bootstyle=SUCCESS, command=execute_sparql_query)
    btn_execute_sparql.pack(pady=5)

    global sparql_result_text
    sparql_result_text = ttk.ScrolledText(sparql_frame, height=10, width=80)
    sparql_result_text.pack(pady=5)

    # Natural Language Query Section
    natural_frame = ttk.Labelframe(root, text="Natural Language Query", padding=10, bootstyle=WARNING)
    natural_frame.pack(fill=BOTH, expand=True, pady=10)

    global natural_query_text
    natural_query_text = ttk.ScrolledText(natural_frame, height=8, width=80)
    natural_query_text.pack(pady=5)
    natural_query_text.insert("1.0", "Enter your natural language query here...")

    btn_execute_natural = ttk.Button(natural_frame, text="Generate and Execute SPARQL Query", bootstyle=PRIMARY, command=execute_natural_language_query)
    btn_execute_natural.pack(pady=5)

    global natural_result_text
    natural_result_text = ttk.ScrolledText(natural_frame, height=10, width=80)
    natural_result_text.pack(pady=5)

    root.mainloop()

# Start the interface
ontology = None  # Global variable to store the loaded ontology
create_interface()
