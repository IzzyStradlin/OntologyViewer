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
    trace_nodes = go.Scatter3d(
        x=nodes_x,
        y=nodes_y,
        z=nodes_z,
        mode='markers',
        marker=dict(size=[max(10, 40 * c) for c in nodes_color], color=nodes_color, colorscale='Viridis', showscale=True),
        hoverinfo='text',
        name='nodes',
        text=list(graph.nodes())  # Display node names
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

# Function to format SPARQL results for better readability
def format_sparql_results(results):
    formatted_result = "SalesOrder Results:\n"
    formatted_result += "=" * 120 + "\n"
    formatted_result += "{:<50} {:<20} {:<50} {:<50} {:<50}\n".format(
        "SalesOrder", "Label", "TransportOrder", "InvolvedParty", "Contract"
    )
    formatted_result += "-" * 120 + "\n"

    for row in results:
        sales_order = str(row[0]) if row[0] else "N/A"
        label = str(row[1]) if row[1] else "N/A"
        transport_order = str(row[2]) if row[2] else "N/A"
        involved_party = str(row[3]) if row[3] else "N/A"
        contract = str(row[4]) if row[4] else "N/A"

        formatted_result += "{:<50} {:<20} {:<50} {:<50} {:<50}\n".format(
            sales_order, label, transport_order, involved_party, contract
        )

    formatted_result += "=" * 120 + "\n"
    return formatted_result

# Function to execute SPARQL query and display results
def execute_sparql_query():
    try:
        query = sparql_query_text.get("1.0", "end-1c").strip()
        if not query:
            messagebox.showwarning("Warning", "Please enter a SPARQL query.")
            return

        # Execute the query
        results = ontology.query(query)

        # Format the results
        formatted_results = format_sparql_results(results)

        # Display the results in the result box
        sparql_result_text.configure(state="normal")
        sparql_result_text.delete("1.0", "end")
        sparql_result_text.insert("1.0", formatted_results)
        sparql_result_text.configure(state="disabled")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while executing the query: {e}")

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

# Function to handle placeholder text in text boxes
def add_placeholder(widget, placeholder_text):
    widget.insert("1.0", placeholder_text)
    widget.bind("<FocusIn>", lambda event: clear_placeholder(widget, placeholder_text))
    widget.bind("<FocusOut>", lambda event: restore_placeholder(widget, placeholder_text))

def clear_placeholder(widget, placeholder_text):
    if widget.get("1.0", "end-1c") == placeholder_text:
        widget.delete("1.0", "end")

def restore_placeholder(widget, placeholder_text):
    if not widget.get("1.0", "end-1c").strip():
        widget.insert("1.0", placeholder_text)

# Create the Tkinter window
def create_interface():
    root = ttk.Window(themename="cosmo")  # Use a modern theme like "cosmo", "flatly", "darkly"
    root.title("Ontology Viewer with SPARQL and Natural Language Queries")
    root.geometry("1200x800")  # Reduced window height to fit better on screens

    # Load Ontology Section
    load_frame = ttk.Frame(root, padding=10)
    load_frame.pack(fill=X, pady=5)

    load_label = ttk.Label(load_frame, text="Load a TTL, RDF, OWL, or XML file:", font=("Arial", 12))
    load_label.pack(side=LEFT, padx=5)

    btn_load = ttk.Button(load_frame, text="Load Ontology", bootstyle=PRIMARY, command=load_file)
    btn_load.pack(side=LEFT, padx=5)

    btn_load_uri = ttk.Button(load_frame, text="Load Ontology from URI", bootstyle=INFO, command=load_ontology_from_uri)
    btn_load_uri.pack(side=LEFT, padx=5)

    # SPARQL Query Section
    sparql_frame = ttk.Labelframe(root, text="SPARQL Query", padding=10, bootstyle=INFO)
    sparql_frame.pack(fill=BOTH, expand=True, pady=5)

    global sparql_query_text
    sparql_query_text = ttk.ScrolledText(sparql_frame, height=8, width=90, font=("Courier", 10))
    sparql_query_text.pack(pady=5)
    add_placeholder(sparql_query_text, "Enter your SPARQL query here...")

    btn_execute_sparql = ttk.Button(sparql_frame, text="Execute SPARQL Query", bootstyle=SUCCESS, command=execute_sparql_query)
    btn_execute_sparql.pack(pady=5)

    global sparql_result_text
    sparql_result_text = ttk.ScrolledText(sparql_frame, height=10, width=90, font=("Courier", 10))
    sparql_result_text.pack(pady=5)

    # Natural Language Query Section
    natural_frame = ttk.Labelframe(root, text="Natural Language Query", padding=10, bootstyle=WARNING)
    natural_frame.pack(fill=BOTH, expand=True, pady=5)

    global natural_query_text
    natural_query_text = ttk.ScrolledText(natural_frame, height=8, width=90, font=("Courier", 10))
    natural_query_text.pack(pady=5)
    add_placeholder(natural_query_text, "Enter your natural language query here...")

    btn_execute_natural = ttk.Button(natural_frame, text="Generate and Execute SPARQL Query", bootstyle=PRIMARY, command=execute_natural_language_query)
    btn_execute_natural.pack(pady=5)

    global natural_result_text
    natural_result_text = ttk.ScrolledText(natural_frame, height=10, width=90, font=("Courier", 10))
    natural_result_text.pack(pady=5)

    root.mainloop()

# Start the interface
ontology = None  # Global variable to store the loaded ontology
create_interface()
