import networkx as nx
import numpy as np
import pandas as pd
import pytest

import treedata as td
from treedata._utils import get_root


@pytest.fixture
def tree():
    tree = nx.balanced_tree(r=2, h=3, create_using=nx.DiGraph)
    tree = nx.relabel_nodes(tree, {i: str(i) for i in tree.nodes})
    root = get_root(tree)
    depths = nx.single_source_shortest_path_length(tree, root)
    nx.set_node_attributes(tree, values=depths, name="depth")
    yield tree


@pytest.fixture
def tdata(tree):
    df = pd.DataFrame({"anno": range(8)}, index=[str(i) for i in range(7, 15)])
    yield td.TreeData(X=np.zeros((8, 8)), obst={"tree": tree}, vart={"tree": tree}, obs=df, var=df)


def test_views(tdata):
    # check that subset is view
    assert tdata[:, 0].is_view
    assert tdata[:2, 0].X.shape == (2, 1)
    tdata_subset = tdata[:2, [0, 1]]
    assert tdata_subset.is_view
    # now transition to actual object
    with pytest.warns(UserWarning):
        tdata_subset.obs["test"] = range(2)
    assert not tdata_subset.is_view
    assert tdata_subset.obs["test"].tolist() == list(range(2))


def test_views_subset_tree(tdata):
    expected_edges = [
        ("0", "1"),
        ("0", "2"),
        ("1", "3"),
        ("2", "5"),
        ("3", "7"),
        ("3", "8"),
        ("5", "11"),
    ]
    # subset with index
    tdata_subset = tdata[[0, 1, 4], :]
    edges = list(tdata_subset.obst["tree"].edges)
    assert edges == expected_edges
    # subset with names
    tdata_subset = tdata[["7", "8", "11"], :]
    edges = list(tdata_subset.obst["tree"].edges)
    assert edges == expected_edges


def test_views_mutability(tdata):
    # can mutate attributes of graph
    nx.set_node_attributes(tdata.obst["tree"], False, "in_subset")
    subset_leaves = ["7", "8"]
    tdata_subset = tdata[subset_leaves, :]
    nx.set_node_attributes(tdata_subset.obst["tree"], True, "in_subset")
    expected_subset_nodes = ["8", "0", "3", "7", "1"]
    subset_nodes = [
        node for node in tdata_subset.obst["tree"].nodes if tdata_subset.obst["tree"].nodes[node]["in_subset"]
    ]
    assert set(subset_nodes) == set(expected_subset_nodes)
    # cannot mutate structure of graph
    with pytest.raises(nx.NetworkXError):
        tdata_subset.obst["tree"].remove_node("8")
