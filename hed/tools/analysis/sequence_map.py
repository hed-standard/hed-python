""" A map of containing the number of times a particular sequence of values in a column of a columnar file. """


import pandas as pd
from hed.tools.util import data_util


class SequenceMap:
    # TODO: This class is partially implemented.
    """ A map of unique sequences of column values of a particular length appear in a columnar file.

    Attributes:

        name (str):       An optional name of this remap for identification purposes.

    Notes: This mapping converts all columns in the mapping to strings.
    The remapping does not support other types of columns.

    """
    def __init__(self, codes=None, name=''):
        """ Information for setting up the maps.

        Parameters:
            codes (list or None): If None use all codes, otherwise only include listed codes in the map.
            name (str):   Name associated with this remap (usually a pathname of the events file).

        """

        self.codes = codes
        self.name = name
        self.node_counts = {}
        self.edges = {}     # map of keys to n-element sequences
        self.edge_counts = {}  # Keeps a running count of the number of times a key appears in the data

    @property
    def __str__(self):
        """ Return a version of this sequence map serialized to a string. """
        node_counts = [f"{value}({str(count)})" for value, count in self.node_counts.items()]
        node_str = " ".join(node_counts)
        return node_str
        # temp_list = [f"{self.name} counts for key [{str(self.key_cols)}]:"]
        # for index, row in self.col_map.iterrows():
        #     key_hash = get_row_hash(row, self.columns)
        #     temp_list.append(f"{str(list(row.values))}:\t{self.count_dict[key_hash]}")
        # return "\n".join(temp_list)

    def dot_str(self, group_spec={}):
        """ Produce a DOT string representing this sequence map. """
        base = 'digraph g { \n'
        if self.codes:
            node_list = [f"{node};" for node in self.codes if node not in self.node_counts]
            if node_list:
                base = base + 'subgraph cluster_unused {\n bgcolor="#cAcAcA";\n' + "\n".join(node_list) + "\n}\n"
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

        dot_str = base + "\n".join(edge_list) + "}\n"
        return dot_str

    def edge_to_str(self, key):
        """ Convert a graph edge to a DOT string.

        Parameters:
            key(str):  Hashcode string representing a graph edge.

        """
        value = self.edges.get(key, [])
        if value:
            return f"{value[0]} -> {value[1]} "
        else:
            return ""

    def get_edge_list(self, sort=True):
        """ Return a DOT format edge list with the option of sorting by edge counts.

        Parameters:
            sort (bool): If True (the default), the edge list is sorted by edge counts.

        Returns:
            list:  list of DOT strings representing the edges labeled by counts.

        """

        df = pd.DataFrame(list(self.edge_counts.items()), columns=['Key', 'Counts'])
        if sort:
            df = df.sort_values(by='Counts', ascending=False)
        edge_list = [f"{self.edge_to_str(row['Key'])} [label={str(self.edge_counts[row['Key']])}];"
                     for index, row in df.iterrows()]
        return edge_list

    def filter_edges(self):
        pass

    def update(self, data):
        """ Update the existing map with information from data.

        Parameters:
            data (Series): DataFrame or filename of an events file or event map.
            allow_missing (bool):  If True allow missing keys and add as n/a columns.

        Raises:
            HedFileError: If there are missing keys and allow_missing is False.

        """
        filtered = self.prep(data)
        if self.codes:
            mask = filtered.isin(self.codes)
            filtered = filtered[mask]
        for index, value in filtered.items():
            if value not in self.node_counts:
                self.node_counts[value] = 1
            else:
                self.node_counts[value] = self.node_counts[value] + 1
            if index + 1 >= len(filtered):
                break
            key_list = filtered[index:index+2].tolist()
            key = data_util.get_key_hash(key_list)
            if key in self.edges:
                self.edge_counts[key] = self.edge_counts[key] + 1
            else:
                self.edges[key] = key_list
                self.edge_counts[key] = 1

    # def update(self, data):
    #     """ Update the existing map with information from data.
    #
    #     Parameters:
    #         data (Series):     DataFrame or filename of an events file or event map.
    #         allow_missing (bool):        If true allow missing keys and add as n/a columns.
    #
    #     :raises HedFileError:
    #         - If there are missing keys and allow_missing is False.
    #
    #     """
    #     filtered = self.prep(data)
    #     if self.codes:
    #         mask = filtered.isin(self.codes)
    #         filtered = filtered[mask]
    #     for index, value in filtered.items():
    #         if value not in self.node_counts:
    #             self.node_counts[value] = 1
    #         else:
    #             self.node_counts[value] = self.node_counts[value] + 1
    #         if index + 1 >= len(filtered):
    #             break
    #         key_list = filtered[index:index + 2].tolist()
    #         key = get_key_hash(key_list)
    #         if key in self.edges:
    #             self.edge_counts[key] = self.edge_counts[key] + 1
    #         else:
    #             self.edges[key] = key_list
    #             self.edge_counts[key] = 1

    @staticmethod
    def prep(data):
        """ Remove quotes from the specified columns and convert to string.

        Parameters:
            data (Series):   Dataframe to process by removing quotes.

        Returns:
            Series

        Notes:
            - Replacement is done in place.
        """

        filtered = data.astype(str)
        filtered.fillna('n/a').astype(str)
        filtered = filtered.str.replace('"', '')
        filtered = filtered.str.replace("'", "")
        return filtered
