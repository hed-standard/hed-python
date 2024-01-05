""" A map of containing the number of times a particular sequence of values in a column of an event file. """

import pandas as pd
from hed.tools.util.data_util import get_key_hash


class SequenceMapNew:
    """ A map of unique sequences of column values of a particular length appear in an event file.

    Attributes:
        
        name (str):       An optional name of this remap for identification purposes.

    Notes: This mapping converts all columns in the mapping to strings.
    The remapping does not support other types of columns.

    """

    def __init__(self, codes=None, name='', seq=[0, -1]):
        """ Information for setting up the maps.

        Parameters:
            codes (list or None): If None use all codes, otherwise only include listed codes in the map.
            name (str):          Name associated with this remap (usually a pathname of the events file).

        """

        self.codes = codes
        self.name = name
        self.seq = seq
        self.nodes = {}  # Node keys to node names
        self.node_counts = {}  # Node values to count  
        self.sequences = {}  # Sequence keys to sequence
        self.seq_counts = {}  # Sequence keys to counts
        self.edges = {}  # map of edge keys to 2-element sequence keys
        self.edge_counts = {}  # edge keys to edge counts

    @property
    def __str__(self):
        node_counts = [f"{value}({str(count)})" for value, count in self.node_counts.items()]
        node_str = (" ").join(node_counts)
        return node_str
        # temp_list = [f"{self.name} counts for key [{str(self.key_cols)}]:"]
        # for index, row in self.col_map.iterrows():
        #     key_hash = get_row_hash(row, self.columns)
        #     temp_list.append(f"{str(list(row.values))}:\t{self.count_dict[key_hash]}")
        # return "\n".join(temp_list)

    def dot_str(self, group_spec={}):
        """ Produce a DOT string representing this sequence map.
        
        
        """
        base = 'digraph g { \n'
        if self.codes:
            node_list = [f"{node};" for node in self.codes if node not in self.node_counts]
            if node_list:
                base = base + 'subgraph cluster_unused {\n bgcolor="#cAcAcA";\n' + ("\n").join(node_list) + "\n}\n"
        if group_spec:
            for group, spec in group_spec.items():
                group_list = [f"{node};" for node in self.node_counts if node in spec["nodes"]]
                if group_list:
                    spec_color = spec["color"]
                    if spec_color[0] == '#':
                        spec_color = f'"{spec_color}"'
                    base = base + 'subgraph cluster_' + group + '{\n' + f'bgcolor={spec_color};\n' + \
                           '\n'.join(group_list) + '\n}\n'
        edge_list = self.get_edge_list(sort=True)

        dot_str = base + ("\n").join(edge_list) + "}\n"
        return dot_str

    def edge_to_str(self, key):
        value = self.edges.get(key, [])
        if value:
            x = ("+").join(value[0])
            y = ("+").join(value[1])
            return f"{str(self.sequences[value[0]])} -> {str(self.sequences[value[1]])} "
        else:
            return ""

    def get_edge_list(self, sort=True):
        """Produces a DOT format edge list with the option of sorting by edge counts.
        
        Parameters:
            sort (bool): if true the edge list is sorted by edge counts
            
        Returns:
            list:  list of DOT strings representing the edges labeled by counts.
        
        """

        df = pd.DataFrame(list(self.edge_counts.items()), columns=['Key', 'Counts'])
        if sort:
            df = df.sort_values(by='Counts', ascending=False)
        edge_list = []
        for index, row in df.iterrows():
             edge_list.append(f"{self.edge_to_str(row['Key'])} [label={str(self.edge_counts[row['Key']])}];")
        return edge_list

    def filter_edges(self):
        print("to here")

    def update(self, data):
        filtered = self.get_sequence_data(data)
        last_seq_key = None
        for index, row in filtered.iterrows():
            # Update node counts
            this_node = row['value']
            self.node_counts[this_node] = self.node_counts.get(this_node, 0) + 1
            this_seq = row['seq']
            if not this_seq:
                last_seq_key = None
                continue;
            this_seq_key = get_key_hash(this_seq)
            self.sequences[this_seq_key] = this_seq
            self.seq_counts[this_seq_key] = self.seq_counts.get(this_seq_key, 0) + 1
            if last_seq_key:
                this_edge_key = get_key_hash([last_seq_key, this_seq_key])
                self.edges[this_edge_key] = [last_seq_key, this_seq_key]
                self.edge_counts[this_edge_key] = self.edge_counts.get(this_edge_key, 0) + 1
            last_seq_key = this_seq_key

    def get_sequence_data(self, data):
        filtered = self.prep(data)
        empty_lists = [[] for _ in range(len(filtered))]

        # Create a DataFrame
        df = pd.DataFrame({'value': filtered.values, 'seq': empty_lists})

        for index, row in df.iterrows():
            df.at[index, 'seq'] = self.get_sequence(df, index)
        return df

    def get_sequence(self, df, index):
        seq_list = []
        for i, val in enumerate(self.seq):
            df_ind = val + index
            if df_ind < 0 or df_ind >= len(df):
                return []
            seq_list.append(df.iloc[df_ind, 0])
        return seq_list

    @staticmethod
    def prep(data):
        """ Remove quotes from the specified columns and convert to string.

        Parameters:
            data (Series):   Dataframe to process by removing quotes.
            
        Returns: Series
        Notes:
            - Replacement is done in place.
        """

        filtered = data.astype(str)
        filtered.fillna('n/a').astype(str)
        filtered = filtered.str.replace('"', '')
        filtered = filtered.str.replace("'", "")
        return filtered
