import itertools
from typing import Set, List, Tuple

from gurobipy import *

from model.abstract_model import AbstractModel


class HanziSquareModelGurobi(AbstractModel):
    def __init__(self,
                 graph,
                 time_limit,
                 mip_gap,
                 bound: int = None,
                 fixed_nodes: Set[str] = None,
                 cutoff_sols: List[Tuple[List[str], List[str]]] = None):
        """
        Initialization of the model
        :param graph: the graph of strokes and characters
        :param bound: an educational guess of bound (optional)
        :param fixed_nodes: strokes and must be chosen (optional)
        :param cutoff_sols: solutions which will be cutoff (optional)
        """
        self.graph = graph
        self.bound = bound
        self.time_limit = time_limit
        self.mip_gap = mip_gap
        self.model = Model('HanziSquare')
        if bound:
            self.big_m = bound
        else:
            self.big_m = len(self.graph.nodes)
        if fixed_nodes:
            self.fixed_nodes = fixed_nodes
        else:
            self.fixed_nodes = set()
        if cutoff_sols is None:
            self.cutoff_sols = list()
        else:
            self.cutoff_sols = cutoff_sols
        return

    def _set_iterables(self):
        # As gurobi cannot accept chinese characters, convert them to indices
        self.nodes_to_indices = {
            node: idx
            for idx, node in enumerate(self.graph.nodes)
        }
        self.indices_to_nodes = {
            idx: node
            for node, idx in self.nodes_to_indices.items()
        }
        self.arcs = {(self.nodes_to_indices[i], self.nodes_to_indices[j])
                     for (i, j) in self.graph.arcs}
        self.chars_to_indices = {
            char: idx
            for idx, char in enumerate(self.graph.chars)
        }
        self.indices_to_chars = {
            idx: char
            for char, idx in self.chars_to_indices.items()
        }
        self.fixed_nodes = [self.nodes_to_indices[i] for i in self.fixed_nodes]

        temp_sols = list()
        for (x_list, y_list) in self.cutoff_sols:
            temp_sols.append(([self.nodes_to_indices[i] for i in x_list],
                              [self.nodes_to_indices[j] for j in y_list]))
        self.cutoff_sols = temp_sols

        self.forward = dict()
        self.backward = dict()
        for (i, j) in self.arcs:
            self.forward.setdefault(i, set()).add(j)
            self.backward.setdefault(j, set()).add(i)
        return

    def _set_variables(self):
        self.x = self.model.addVars(list(self.indices_to_nodes.keys()),
                                    vtype=GRB.BINARY,
                                    name='x')
        self.y = self.model.addVars(list(self.indices_to_nodes.keys()),
                                    vtype=GRB.BINARY,
                                    name='y')
        self.z = self.model.addVars(self.arcs, vtype=GRB.BINARY, name='z')
        self.u = self.model.addVars(list(self.indices_to_chars.keys()),
                                    vtype=GRB.BINARY,
                                    name='u')
        self.v = self.model.addVar(vtype=GRB.INTEGER, name='v')
        return

    def _set_objective(self):
        self.model.setObjective(self.v, sense=GRB.MAXIMIZE)
        return

    def _set_constraints(self):
        self.model.addConstr(
            (quicksum(self.x[i] for i in self.indices_to_nodes) == self.v),
            name='eq1')
        self.model.addConstr(
            (quicksum(self.y[j] for j in self.indices_to_nodes) == self.v),
            name='eq2')

        self.model.addConstrs((self.z[i, j] >= self.x[i] + self.y[j] - 1
                               for (i, j) in self.arcs),
                              name='linear1')
        self.model.addConstrs(
            (self.z[i, j] <= self.x[i] for (i, j) in self.arcs), name='linear2')
        self.model.addConstrs(
            (self.z[i, j] <= self.y[j] for (i, j) in self.arcs), name='linear3')

        self.model.addConstrs(
            (self.x[i] + self.y[i] <= 1 for i in self.indices_to_nodes),
            name='either')

        # For any i, j in N and (i, j) not in A, add x_i + y_j <= 1,
        # numerically slow as we generate too many constraints
        # self.model.addConstrs(
        #     (self.x[i] + self.y[j] <= 1
        #      for (i, j) in itertools.product(self.indices_to_nodes, repeat=2)
        #      if (i, j) not in self.arcs),
        #     name='cut')

        self.model.addConstrs(
            (quicksum(self.z[i, j]
                      for j in self.forward[i]) <= self.v + self.big_m *
             (1 - self.x[i]) for i in self.indices_to_nodes),
            name='eq1')
        self.model.addConstrs(
            (quicksum(self.z[i, j]
                      for j in self.forward[i]) >= self.v + self.big_m *
             (self.x[i] - 1) for i in self.indices_to_nodes),
            name='eq2')
        self.model.addConstrs(
            (quicksum(self.z[i, j]
                      for i in self.backward[j]) <= self.v + self.big_m *
             (1 - self.y[j]) for j in self.indices_to_nodes),
            name='eq3')
        self.model.addConstrs(
            (quicksum(self.z[i, j]
                      for i in self.backward[j]) >= self.v + self.big_m *
             (self.y[j] - 1) for j in self.indices_to_nodes),
            name='eq4')

        for c, arcs in self.graph.chars.items():
            c_idx = self.chars_to_indices[c]
            self.model.addConstr((self.u[c_idx] == quicksum(
                self.z[self.nodes_to_indices[i], self.nodes_to_indices[j]]
                for (i, j) in arcs)),
                                 name=f'char_{c_idx}')

        self.model.addConstrs((self.x[i] == 1 for i in self.fixed_nodes),
                              name='fixed')

        # Cut off solutions (two constraints as x and y are interchangeable)
        for idx, (x_sol, y_sol) in enumerate(self.cutoff_sols):
            self.model.addConstr(
                (quicksum(self.x[i] for i in x_sol) + quicksum(self.y[j]
                                                               for j in y_sol)
                 <= len(x_sol) + len(y_sol) - 1),
                name=f'sol1_{idx}')
            self.model.addConstr(
                (quicksum(self.y[i] for i in x_sol) + quicksum(self.x[j]
                                                               for j in y_sol)
                 <= len(x_sol) + len(y_sol) - 1),
                name=f'sol2_{idx}')
        return

    def _optimize(self):
        self.model.write('test.lp')
        self.model.Params.timelimit = self.time_limit
        self.model.Params.mip_gap = self.mip_gap
        self.model.optimize()
        return

    def _is_feasible(self):
        if self.model.Status == GRB.INFEASIBLE:
            return False
        else:
            return True

    def _process_infeasible_case(self):
        return list(), list()

    def _post_process(self):
        x_lst, y_lst = list(), list()
        for i in self.graph.nodes:
            if self.x[self.nodes_to_indices[i]].x > 0.9:
                x_lst.append(i)
            if self.y[self.nodes_to_indices[i]].x > 0.9:
                y_lst.append(i)
        return x_lst, y_lst
