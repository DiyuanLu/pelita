#!/usr/bin/python3
# -*- coding:utf-8 -*-

import itertools
import math
import queue
from collections import defaultdict, namedtuple

import numpy as np

def sort_ranks(teams):
    l = len(teams)
    if l % 2 != 0:
        bonus = [teams[-1]]
    else:
        bonus = []
    good_teams = teams[:l//2]
    bad_teams = reversed(teams[l//2:2*(l//2)])
    return [team for pair in zip(good_teams, bad_teams) for team in pair] + bonus


class MatrixElem:
    def size(self):
        return len(self.to_s())

    def box(self, team, *, prefix=None, postfix=None, size=None, padLeft="", padRight="", fillElem="─"):
        if prefix is None:
            prefix = ""
        if postfix is None:
            postfix = ""

        if size is None:
            size = 0
        else:
            size = size - len(prefix) - len(postfix)
        padded = "{padLeft}{team}{padRight}".format(team=team, padLeft=padLeft, padRight=padRight)
        return "{prefix}{team:{fillElem}<{size}}{postfix}".format(team=padded, prefix=prefix, postfix=postfix, size=size, fillElem=fillElem)

class Team(namedtuple("Team", ["name"]), MatrixElem):
    def to_s(self, size=None):
        return self.box(self.name, size=size, prefix="", padLeft=" ", padRight=" ")

class Bye(namedtuple("Bye", ["team"]), MatrixElem):
    def to_s(self, size=None):
        prefix = "──"
        # return show_team("…", prefix=prefix, padLeft=" ", padRight=" ", size=size)
        return self.box("", size=size)

class Match(namedtuple("Match", ["t1", "t2"]), MatrixElem):
    def __init__(self, *args, **kwargs):
        self.winner = None

    def __repr__(self):
        return "Match(t1={}, t2={}, winner={})".format(self.t1, self.t2, self.winner)

    def to_s(self, size=None):
        prefix = "├─"
        name = self.winner if self.winner else "unknown"
        return self.box(name, prefix=prefix, padLeft=" ", padRight=" ", size=size)

class FinalMatch(namedtuple("FinalMatch", ["t1", "t2"]), MatrixElem):
    def __init__(self, *args, **kwargs):
        self.winner = None
    def to_s(self, size=None):
        prefix = "├──┨"
        postfix = "┃"
        fillElem = " "
        name = self.winner if self.winner else "unknown"
        return self.box(name, prefix=prefix, postfix=postfix, padLeft=" ", padRight=" ", fillElem=fillElem, size=size)

class Element(namedtuple("Element", ["char"]), MatrixElem):
    def to_s(self, size=None):
        return self.box(self.char, size=size, fillElem=" ")

class Empty(namedtuple("Empty", []), MatrixElem):
    def to_s(self, size=None):
        return self.box(" ", size=size, fillElem=" ")

class BorderTop(namedtuple("BorderTop", ["team", "tight"]), MatrixElem):
    def to_s(self, size=None):
        prefix = "│  " if not self.tight else "┐  "
        padRight = ""
        padLeft = "┏"
        postfix = "┓"
        fillElem = "━"
        return self.box("", prefix=prefix, postfix=postfix, padLeft=padLeft, padRight=padRight, fillElem=fillElem, size=size)

class BorderBottom(namedtuple("BorderBottom", ["team", "tight"]), MatrixElem):
    def to_s(self, size=None):
        prefix = "│  " if not self.tight else "┘  "
        padRight = ""
        padLeft = "┗"
        postfix = "┛"
        fillElem = "━"
        return self.box("", prefix=prefix, postfix=postfix, padLeft=padLeft, padRight=padRight, fillElem=fillElem, size=size)

def knockout_matrix(*teams):
    """
    For now teams is a list (cols) of list (rows) of teams
    """

    initial_teams = teams[0]
    N = len(initial_teams)
    height = N * 2 - 1
    width = math.ceil(math.log(N, 2)) + 1
    matrix = np.empty([height, width], dtype=np.object_)

    matrix.fill(Empty())

    matrix[::2, 0] = [Team(t) for t in initial_teams]

    for col in range(1, width):
        start = None
        end = None
        last_match = None
        rowIdx = 0
        for row in range(height):
            left_elem = matrix[row, col - 1]
            if isinstance(left_elem, Team) or isinstance(left_elem, Match) or isinstance(left_elem, Bye):
                # left of us is a team
                if start is None:
                    start = row
                else:
                    end = row
                    middle = math.floor(start + (end - start) / 2)
                    t1 = matrix[start, col - 1]
                    t2 = matrix[end, col - 1]
                    match = Match(t1=t1, t2=t2)
                    match.winner=teams[col][rowIdx]
                    rowIdx += 1
                    matrix[start:end, col].fill(Element('│'))
                    matrix[start, col] = Element('┐')
                    matrix[end, col] = Element('┘')
                    matrix[middle, col] = match
                    last_match = (middle, col)
                    start = end = None
        else:
            if start is not None:
                team = matrix[start, col - 1]
                matrix[start, col] = Bye(team=team)
                last_match = (start, col)

    # Decorate the winner column
    isMatch = np.vectorize(lambda elem: not isinstance(elem, Empty))

    return matrix, last_match

def print_knockout(*teams, bonusmatch=False):
    if bonusmatch:
        bonus_team = teams[0][-1]
        bonus_final = teams[-1][0]

        teams = [t[:] for t in teams]
        del teams[0][-1]
        del teams[-1]
        matrix, final_match = knockout_matrix(*teams)
        winner_row = final_match[0]

        enlarged_height = matrix.shape[0] + 2
        enlarged_width = matrix.shape[1] + 1
        enlarged_matrix = np.empty([enlarged_height, enlarged_width], dtype=np.object_)
        enlarged_matrix.fill(Empty())
        for row in range(matrix.shape[0]):
            for col in range(0, matrix.shape[1]):
                enlarged_matrix[row, col] = matrix[row, col]
        matrix = enlarged_matrix

        matrix[-1, 0] = Team(bonus_team)
        matrix[-1, 1:-1].fill(Bye(team=matrix[-1, 0]))

        col = -1
        start = winner_row
        end = matrix.shape[0] - 1
        middle = math.floor(start + (end - start) / 2)

        matrix[start:end, col].fill(Element('│'))
        matrix[start, col] = Element('┐')
        matrix[end, col] = Element('┘')
        matrix[middle, col] = Match(".", ".")
        matrix[middle, col].winner = teams[col][0]

        final_match = (middle, col)
    else:
        matrix, final_match = knockout_matrix(*teams)

    winner_row = final_match[0]
    winning_team = matrix[final_match].winner
    winner = matrix[final_match] = FinalMatch(* matrix[final_match])
    winner.winner = winning_team

    def is_tight(elem):
        return not isinstance(elem, Empty) and not isinstance(elem, Element)

    matrix[winner_row - 1, -1] = BorderTop(winner, is_tight(matrix[winner_row - 1, -2]))
    matrix[winner_row + 1, -1] = BorderBottom(winner, is_tight(matrix[winner_row + 1, -2]))

    colwidths = np.amax(np.vectorize(lambda self: self.size())(matrix), axis=0)

    for row in range(matrix.shape[0]):
        for col in range(0, matrix.shape[1]):
            try:
                print(matrix[row, col].to_s(colwidths[col]), end="")
            except AttributeError:
                print("Here:", end="")
                print(row, col, matrix[row, col])
                raise
        print()

def makepairs(matches):
    if len(matches) == 0:
        raise ValueError("Cannot prepare matches (no teams given).")
    while not len(matches) == 1:
        m = []
        pairs = itertools.zip_longest(matches[::2], matches[1::2])
        for p1, p2 in pairs:
            if p2 is not None:
                m.append(Match(p1, p2)) #  winner=None))
            else:
                m.append(Bye(p1))
        matches = m
    return matches[0]

def prepare_matches(teams, bonusmatch=False):
    final_match = makepairs([Team(t) for t in teams])
    return final_match

def print_tree(tree, bonusmatch=False):
    enumerated = tree_enumerate(tree)
    def show(elem):
        if isinstance(elem, Match):
            if elem.winner is not None:
                return elem.winner
            else:
                return "???"
        if isinstance(elem, Team):
            return elem.name
        if isinstance(elem, Bye):
            return show(elem.team)
    enumerated = [
        [show(elem) for elem in elems] for elems in enumerated
    ]

    return print_knockout(*enumerated, bonusmatch=bonusmatch)


def is_balanced(tree):
    if isinstance(tree, Match):
        return is_balanced(tree.t1) and is_balanced(tree.t2) and tree_depth(tree.t1) == tree_depth(tree.t2)
    if isinstance(tree, Bye):
        return True
    if isinstance(tree, Team):
        return True

def tree_depth(tree):
    if isinstance(tree, Match):
        return 1 + max(tree_depth(tree.t1), tree_depth(tree.t2))
    if isinstance(tree, Bye):
        return 1 + tree_depth(tree.team)
    if isinstance(tree, Team):
        return 1

def tree_enumerate(tree):
    enumerated = defaultdict(list)

    nodes = queue.Queue()
    nodes.put((tree, 0))
    while not nodes.empty():
        node, generation = nodes.get()
        if isinstance(node, Match):
            nodes.put((node.t1, generation + 1))
            nodes.put((node.t2, generation + 1))
        if isinstance(node, Bye):
            nodes.put((node.team, generation + 1))
        if isinstance(node, Team):
            pass
        enumerated[generation].append(node)

    generations = []
    for idx in sorted(enumerated.keys()):
        generations.append(enumerated[idx])
    generations.reverse()
    return generations


