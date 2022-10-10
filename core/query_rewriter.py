from mo_sql_parsing import parse
from mo_sql_parsing import format
import numbers
import sqlparse
from typing import Any

from core.rule_parser import VarType, VarTypesInfo


VarStart = VarTypesInfo[VarType.Var]['internalBase']
VarListStart = VarTypesInfo[VarType.VarList]['internalBase']


class QueryRewriter:

    # Beautify a query string
    # 
    @staticmethod
    def beautify(query: str) -> str:
        return sqlparse.format(query, reindent=True)

    # Rewrite query using the rules iteratively
    #   An example rule in rules list:
    #     rule = {
    #       'id': 1,
    #       'key': 'remove_cast',
    #       'name': 'Remove Cast',
    #       'pattern': json.loads('{"cast": ["V1", {"date": {}}]}'),
    #       'constraints': 'TYPE(x) = DATE',
    #       'rewrite': json.loads('"V1"'),
    #       'actions': ''
    #     }
    # 
    @staticmethod
    def rewrite(query: str, rules: list) -> str:
        
        query_ast = parse(query)

        new_query = True
        while new_query is True:
            new_query = False
            for rule in rules:
                memo = {}  # keep track of the matched substrees of the rule, Vars, and VarLists
                if QueryRewriter.match(query_ast, rule, memo):
                    query_ast = QueryRewriter.take_actions(query_ast, rule, memo)
                    query_ast = QueryRewriter.replace(query_ast, rule, memo)
                    new_query = True
                    break

        return format(query_ast)
    
    # Traverse query AST tree, and check if rule->pattern matches any node of in query
    # 
    @staticmethod
    def match(query: Any, rule: dict, memo: dict) -> bool:
        
        # Breadth-First-Search on query
        # 
        queue = [query]
        while len(queue) > 0:
            curr_node = queue.pop(0)
            if QueryRewriter.match_node(curr_node, rule['pattern_json'], rule, memo):
                memo['rule'] = curr_node
                return True
            if type(curr_node) is dict:
                for child in curr_node.values():
                    queue.append(child)
            elif type(curr_node) is list:
                for child in curr_node:
                    queue.append(child)
        return False
    
    # Recursively check if the query_node matches the rule_node for the given rule
    # 
    @staticmethod
    def match_node(query_node: Any, rule_node: Any, rule: dict, memo: dict) -> bool:
        
        # Case-1: rule_node is a Var, it can match a constant or a dict
        # 
        if QueryRewriter.is_var(rule_node):
            if QueryRewriter.is_constant(query_node) or QueryRewriter.is_dict(query_node):
                # TODO - resolve conflicts if one Var matched more than once
                # 
                memo[rule_node] = query_node
                return True
        
        # Case-2: rule_node is a VarList, it can match a list
        # 
        if QueryRewriter.is_varList(rule_node):
            if QueryRewriter.is_list(query_node):
                # TODO - resolve conflicts if one VarList matched more than once
                # 
                memo[rule_node] = query_node
                return True
        
        # Case-3: rule_node is a constant, it can match a constant
        if QueryRewriter.is_constant(rule_node):
            if QueryRewriter.is_constant(query_node):
                return QueryRewriter.match_constant(query_node, rule_node, rule, memo)
        
        # Case-4: rule_node is a dict, it can match a dict
        # 
        if QueryRewriter.is_dict(rule_node):
            if QueryRewriter.is_dict(query_node):
                return QueryRewriter.match_dict(query_node, rule_node, rule, memo)
                
        # Case-5: rule_node is a list, it can match a list
        # 
        if QueryRewriter.is_list(rule_node):
            if QueryRewriter.is_list(query_node):
                return QueryRewriter.match_list(query_node, rule_node, rule, memo)
            
        # Case-6: rule_node is a dot expression, it can match a dot expression
        if QueryRewriter.is_dot_expression(rule_node):
            if QueryRewriter.is_dot_expression(query_node):
                return QueryRewriter.match_dot_expression(query_node, rule_node, rule, memo)
        
        # Special case for value of 'select' and 'from':
        #   e.g., query_node = [{"value": "e1.name"}, {"value": "e1.age"}, {"value": "e2.salary"}]
        #         rule_node = {"value": "VL1"}
        #   The idea is escalate the "VL1" from inside {"value": "VL1"} to outside
        # 
        if QueryRewriter.is_dict(rule_node) and 'value' in rule_node.keys() and QueryRewriter.is_varList(rule_node['value']):
            memo[rule_node['value']] = query_node
            return True

        return False

    # Check if two strings of query_node and rule_node match each other
    # 
    @staticmethod
    def match_string(query_node: Any, rule_node: Any) -> bool:
        return type(query_node) is str and type(rule_node) is str and query_node.lower() == rule_node.lower()
    
    # Check if two numbers of query_node and rule_node match each other
    # 
    @staticmethod
    def match_number(query_node: Any, rule_node: Any) -> bool:
        return type(query_node) is numbers and type(rule_node) is numbers and query_node == rule_node

    # Check if the two constants of query_node and rule_node match each other
    # 
    @staticmethod
    def match_constant(query_node: Any, rule_node: Any, rule: dict, memo: dict) -> bool:
        return QueryRewriter.match_string(query_node, rule_node) \
            or QueryRewriter.match_number(query_node, rule_node)

    # Check if the two dot expressions of query_node and rule_node match each other
    # 
    @staticmethod
    def match_dot_expression(query_node: str, rule_node: str, rule: dict, memo: dict) -> bool:
        query_nodes = query_node.split('.')
        rule_nodes = rule_node.split('.')
        # both have to be in the same format, i.e., "x.y"
        if len(query_nodes) != 2 or len(rule_nodes) != 2:
            return False
        # both positions have to match each other
        return QueryRewriter.match_node(query_nodes[0], rule_nodes[0], rule, memo) and \
            QueryRewriter.match_node(query_nodes[1], rule_nodes[1], rule, memo)

    # Check if the two dicts of query_node and rule_node match each other
    # TODO - We assume that keys in rule_node can NOT be Var or VarList
    #   - Each value in rule_node should match the value in query_node of the same key
    # 
    @staticmethod
    def match_dict(query_node: dict, rule_node: dict, rule: dict, memo: dict) -> bool:
        for key in rule_node.keys():
            if key in query_node.keys():
                if not QueryRewriter.match_node(query_node[key], rule_node[key], rule, memo):
                    return False
            else:
                return False
        return True
    
    # Check if the two lists of query_node and rule_node match each other
    # TODO - We assume that a list in query_node can ONLY contain constants and dicts
    #   - Part-1) Constants in rule_node should match constants in query_node
    #   - Part-2) The remaining constants and dicts in query_node should be matched by 
    #               dicts, Vars and VarList in rule_node
    # 
    @staticmethod
    def match_list(query_node: list, rule_node: list, rule: dict, memo: dict) -> bool:
        # coner case
        # 
        if query_node is None and rule_node is None:
            return True
        if len(query_node) == 0 and len(rule_node) == 0:
            return True

        # - Part-1) Constants in rule_node should match constants in query_node
        # 
        # 1.1) Find constants and remaining in rule_node
        # 
        constants_in_rule = [] 
        remaining_in_rule = []
        for element in rule_node:
            if QueryRewriter.is_constant(element):
                constants_in_rule.append(element)
            else:
                remaining_in_rule.append(element)
        
        # 1.2) Match constants in rule_node to query_node
        #        and find remaining in query_node
        remaining_in_query = query_node.copy()
        for constant in constants_in_rule:
            if constant not in query_node:
                return False
            else:
                remaining_in_query.remove(constant)
        
        # - Part-2) The remaining dicts, Vars and VarList in rule_node should
        #             match the remaining constants and dicts in query_node 
        # 
        # Exaust the combinations of different ways to match them
        #   For each element in remaining of rule_node:
        for rule_element in remaining_in_rule:
            for query_element in remaining_in_query:
                if QueryRewriter.match_node(query_element, rule_element, rule, memo):
                    query_list = remaining_in_query.copy()
                    query_list.remove(query_element)
                    rule_list = remaining_in_rule.copy()
                    rule_list.remove(rule_element)
                    if QueryRewriter.match_list(query_list, rule_list, rule, memo):
                        return True
            # TODO - short-cut match the entire remaining list of query list if rule_element is a VarList,
            #        come up with a better way to combine this case with the exaustive combination loop
            # 
            if QueryRewriter.is_varList(rule_element):
                return QueryRewriter.match_node(remaining_in_query, rule_element, rule, memo)
        return False

    # Check if a given node in AST is a Var
    # 
    @staticmethod
    def is_var(node: Any) -> bool:
        if type(node) is str and not QueryRewriter.is_dot_expression(node) and node.startswith(VarStart) and not node.startswith(VarListStart):
            return True
        else:
            return False
    
    # Check if a given node in AST is a VarList
    # 
    @staticmethod
    def is_varList(node: Any) -> bool:
        if type(node) is str and not QueryRewriter.is_dot_expression(node) and node.startswith(VarListStart):
            return True
        else:
            return False
    
    # Check if a given node in AST is a constant
    # 
    @staticmethod
    def is_constant(node: Any) -> bool:
        if type(node) is str:
            if not QueryRewriter.is_dot_expression(node) and not QueryRewriter.is_var(node) and not QueryRewriter.is_varList(node):
                return True
        if isinstance(node, numbers.Number):
            return True
        return False
    
    # Check if a given node in AST is a string
    # 
    @staticmethod
    def is_string(node: Any) -> bool:
        if type(node) is str:
            if not QueryRewriter.is_dot_expression(node) and not QueryRewriter.is_var(node) and not QueryRewriter.is_varList(node):
                return True
        return False
    
    # Check if a given node in AST is a dot expression (e.g., 't1.a1')
    @staticmethod
    def is_dot_expression(node: Any) -> bool:
        if type(node) is str:
            if '.' in node:
                return True
        return False
    
    # Check if a given node in AST is a dict
    # 
    @staticmethod
    def is_dict(node: Any) -> bool:
        return type(node) is dict
    
    # Check if a given node in AST is a list
    # 
    @staticmethod
    def is_list(node: Any) -> bool:
        return type(node) is list
    
    # Take actions on the query AST defined in the rule's actions
    # 
    @staticmethod
    def take_actions(query: Any, rule: dict, memo: dict) -> Any:
        
        for action in rule['actions_json']:
            func = action['function']
            # TODO - fetch functions by names dynamically in run time
            # 
            if func == 'substitute':
                variables = action['variables']
                if len(variables) == 3:
                    scope = variables[0]
                    source = memo[variables[1]]
                    target = memo[variables[2]]
                    # traverse the subtree of scope and substitute
                    memo[scope] = QueryRewriter.substitute(memo[scope], source, target)

        return query

    # Action: Substitute
    # 
    @staticmethod
    def substitute(sub_ast: Any, source: str, target: str) -> Any:
        # sub_ast is a string
        if type(sub_ast) == str:
            if sub_ast == source:
                return target
            if '.' in sub_ast:
                return '.'.join([QueryRewriter.substitute(x, source, target) for x in sub_ast.split('.')])
        
        # sub_ast is a number
        if type(sub_ast) == numbers.Number:
            if str(sub_ast) == source:
                return target
        
        # sub_ast is a dict
        if type(sub_ast) == dict:
            for key in sub_ast.keys():
                sub_ast[key] = QueryRewriter.substitute(sub_ast[key], source, target)
            return sub_ast
                
        # sub_ast is a list
        if type(sub_ast) == list:
            return [QueryRewriter.substitute(x, source, target) for x in sub_ast]
        
        return sub_ast

    # Replace the subtree of query AST matched by rule to rule's rewrite
    # 
    @staticmethod
    def replace(query: Any, rule: dict, memo: dict) -> Any:
        
        # Special case for value of 'select' and 'from':
        #   e.g., query = {"value": "VL1"}
        #         memo["VL1"] = [{"value": "e1.name"}, {"value": "e1.age"}, {"value": "e1.salary"}]
        #   The idea is escalate the "VL1" from inside {"value": "VL1"} to outside
        # 
        if QueryRewriter.is_dict(query) and 'value' in query.keys() and QueryRewriter.is_varList(query['value']):
            return memo[query['value']]
        
        # Special case for VarList in "and" list:
        #   e.g., query = [{...}, "VL2"]
        #         memo["VL2"] = [{"gt": [...]}, {"gt": [...]}]
        #   The idea is escalate the "VL2" from a list inside the list to merged into the outside list
        # 
        if QueryRewriter.is_list(query):
            for var in query:
                if QueryRewriter.is_varList(var):
                    if QueryRewriter.is_list(memo[var]):
                        query.remove(var)
                        query.extend(memo[var])

        # Special case, rewrite's Var in a string
        #   e.g., {"literal": "%V2%"}
        #                       ^
        #                       query
        # 
        if QueryRewriter.is_string(query):
            return QueryRewriter.replace_var_in_str(query, memo)
        
        # 1st case, find the matched part by the rule
        # 
        if query is memo['rule']:
            # replace query by rule's rewrite
            # 
            query = rule['rewrite_json']

        # 2nd case, find rewrite's Var or VarList
        # 
        if QueryRewriter.is_var(query) or QueryRewriter.is_varList(query):
            # replace query by Var or VarList's value
            return memo[query]

        # Depth-First-Search on query
        # 
        if QueryRewriter.is_dict(query):
            for key, child in query.items():
                query[key] = QueryRewriter.replace(child, rule, memo)
        if QueryRewriter.is_list(query):
            ans = []
            for child in query:
                ans.append(QueryRewriter.replace(child, rule, memo))
            query = ans
        
        return query
    
    # Replace the Var in a string - a spectial case
    #   e.g., {"literal": "%V2%"}
    # 
    @staticmethod
    def replace_var_in_str(query: str, memo: dict) -> str:
        for key in memo.keys():
            if QueryRewriter.is_var(key):
                if key in query:
                    return query.replace(key, memo[key])
        return query