import cohere
import rdflib
import networkx as nx
import plotly.graph_objects as go
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox, scrolledtext, simpledialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import re
import threading
import pyperclip  # For copying text to clipboard

# Initialize Coherence API
co = cohere.ClientV2("BHVtdp8pxKtkUZGtyNGmxjpp0E7KDMX2QI8XYGsv")

# Function to load TTL, RDF, OWL, or XML file (ontology)
def load_ontology(file_path):
    g = rdflib.Graph()
    # Determine the format based on the file extension
    if file_path.endswith(".ttl"):
        g.parse(file_path, format="ttl")
    elif file_path.endswith(".rdf") or file_path.endswith(".owl") or file_path.endswith(".xml"):
        g.parse(file_path, format="xml")  # RDF/XML format
    else:
        raise ValueError("Unsupported file format. Please select a .ttl, .rdf, .owl, or .xml file.")
    return g

# Function to load ontology from a URI
def load_ontology_from_uri():
    # Custom dialog for entering the URI
    uri_window = tk.Toplevel()
    uri_window.title("Enter Ontology URI")
    uri_window.geometry("1200x200")  # Enlarged window size

    tk.Label(uri_window, text="Enter the URI of the ontology:", font=("Arial", 12)).pack(pady=10)
    uri_entry = tk.Entry(uri_window, width=80, font=("Arial", 12))
    uri_entry.pack(pady=5)

    def submit_uri():
        uri = uri_entry.get().strip()
        if not uri:
            messagebox.showwarning("Warning", "No URI provided.")
            uri_window.destroy()
            return

        try:
            global ontology
            ontology = rdflib.Graph()
            print(f"Loading ontology from URI: {uri}")
            ontology.parse(uri, format="xml")
            print("Ontology loaded successfully.")
            graph = create_graph(ontology)
            threading.Thread(target=visualize_graph, args=(graph,)).start()  # Run visualization in a separate thread
            messagebox.showinfo("Success", f"Ontology loaded successfully from URI: {uri}")
        except Exception as e:
            print(f"Error loading ontology: {e}")
            show_error_window(f"Error loading ontology from URI: {e}")
        finally:
            uri_window.destroy()

    tk.Button(uri_window, text="Load Ontology", command=submit_uri, font=("Arial", 10), bg="#4CAF50", fg="white").pack(pady=10)

# Function to show an error window with copy functionality
def show_error_window(error_message):
    error_window = tk.Toplevel()
    error_window.title("Error")
    error_window.geometry("500x300")

    tk.Label(error_window, text="An error occurred:", font=("Arial", 12, "bold")).pack(pady=10)
    error_text = scrolledtext.ScrolledText(error_window, height=10, width=60, font=("Courier", 10))
    error_text.pack(pady=5)
    error_text.insert("1.0", error_message)
    error_text.configure(state="disabled")  # Make the text read-only

    def copy_to_clipboard():
        pyperclip.copy(error_message)
        messagebox.showinfo("Copied", "Error message copied to clipboard.")

    tk.Button(error_window, text="Copy Error", command=copy_to_clipboard, font=("Arial", 10), bg="#2196F3", fg="white").pack(pady=10)

# Function to check if a string is alphanumeric and longer than 20 characters
def is_alphanumeric(s):
    return bool(re.match(r'^[a-zA-Z0-9]{15,}$', s))

# Function to create the graph with NetworkX, including relationships
def create_graph(ontology):
    G = nx.DiGraph()

    # Iterate through all triples in the ontology
    for subj, pred, obj in ontology:
        subj_str = str(subj)
        pred_str = str(pred)
        obj_str = str(obj)

        # Add nodes for the subject and object
        G.add_node(subj_str, label=subj_str)
        G.add_node(obj_str, label=obj_str)

        # Add an edge for the predicate (relationship)
        G.add_edge(subj_str, obj_str, label=pred_str)

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
    node_urls = [n if n.startswith("http") else "" for n in graph.nodes()]

    trace_nodes = go.Scatter3d(
        x=nodes_x,
        y=nodes_y,
        z=nodes_z,
        mode='markers',
        marker=dict(size=[max(10, 40 * c) for c in nodes_color], color=nodes_color, colorscale='Viridis', showscale=True),
        hoverinfo='text',
        name='nodes',
        text=[f'<a href="{n}" target="_blank">{n}</a>' if n.startswith("http") else n for n in graph.nodes()],
        customdata=node_urls,
        hovertemplate='%{text}<extra></extra>'  # node hyperlink
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
        title="Select Ontology file (TTL, RDF, OWL, or XML)", 
        filetypes=[("Ontology files", "*.ttl *.rdf *.owl *.xml")]
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
        messagebox.showwarning("Warning", "Please load a .ttl, .rdf, .owl, or .xml file first")

# Function to handle natural language query execution with Cohere API
def execute_natural_language_query():
    natural_query = natural_query_text.get("1.0", tk.END).strip()
    if not natural_query:
        messagebox.showwarning("Warning", "Please enter a natural language query.")
        return

    try:
        # Call the Cohere API to generate a SPARQL query
        response = co.chat(
            model="command-a-03-2025", 
            messages=[{"role": "user", "content": natural_query}],
            temperature=0.7
        )
        sparql_query = response['choices'][0]['message']['content']
        sparql_query = sparql_query.strip()  # Clean up the SPARQL query

        # Display the generated SPARQL query
        sparql_query_text.delete("1.0", tk.END)
        sparql_query_text.insert(tk.END, sparql_query)

        # Execute the SPARQL query
        if ontology:
            result = execute_query(ontology, sparql_query)
            sparql_result_text.delete("1.0", tk.END)
            sparql_result_text.insert(tk.END, result)
        else:
            messagebox.showwarning("Warning", "Please load an ontology file first.")
    except Exception as e:
        messagebox.showerror("Error", f"Error generating SPARQL query: {e}")

# GUI setup
root = ttk.Window(themename="superhero")
root.title("Ontology RDF Viewer")
root.geometry("800x600")

# Buttons and text boxes for interaction
file_button = ttk.Button(root, text="Load Ontology", command=load_file)
file_button.pack(pady=10)

natural_query_text = tk.Text(root, height=5, width=60)
natural_query_text.pack(pady=10)

execute_nl_button = ttk.Button(root, text="Execute Natural Language Query", command=execute_natural_language_query)
execute_nl_button.pack(pady=10)

sparql_query_text = tk.Text(root, height=5, width=60)
sparql_query_text.pack(pady=10)

sparql_result_text = scrolledtext.ScrolledText(root, height=10, width=60)
sparql_result_text.pack(pady=10)

# Run the main loop for the GUI
root.mainloop()
