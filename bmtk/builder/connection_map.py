# Allen Institute Software License - This software license is the 2-clause BSD license plus clause a third
# clause that prohibits redistribution for commercial purposes without further permission.
#
# Copyright 2017. Allen Institute. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
# following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following
# disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
# disclaimer in the documentation and/or other materials provided with the distribution.
#
# 3. Redistributions for commercial purposes are not permitted without the Allen Institute's written permission. For
# purposes of this license, commercial purposes is the incorporation of the Allen Institute's software into anything for
# which you will charge fees or other compensation. Contact terms@alleninstitute.org for commercial licensing
# opportunities.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
import connector
import iterator


class ConnectionMap(object):
    """Class for keeping track of connection rules.

    For every connection from source --> target this keeps track of rules (functions, literals, lists) for
      1. the number of synapses between source and target
      2. Used defined parameters (syn-weight, synaptic-location) for every synapse.

    The number of synapses rule (1) is stored as a connector. Individual synaptic parameters, if they exists, are stored
    as ParamsRules.
    """

    class ParamsRules(object):
        """A subclass to store indvidiual synpatic parameter rules"""
        def __init__(self, names, rule, rule_params, dtypes):
            self._names = names
            self._rule = rule
            self._rule_params = rule_params
            self._dtypes = self.__create_dtype_dict(names, dtypes)

        def __create_dtype_dict(self, names, dtypes):
            if isinstance(names, list):
                # TODO: compare size of names and dtypes
                return {n: dt for n, dt in zip(names, dtypes)}
            else:
                return {names: dtypes}

        @property
        def names(self):
            return self._names

        @property
        def rule(self):
            return connector.create(self._rule, **(self._rule_params or {}))

        @property
        def dtypes(self):
            return self._dtypes

        def get_prop_dtype(self, prop_name):
            return self._dtypes[prop_name]

    def __init__(self, sources=None, targets=None, connector=None, connector_params=None, iterator='one_to_one',
                 edge_type_properties=None):
        self._source_nodes = sources  # source nodes
        self._target_nodes = targets  # target nodes
        self._connector = connector  # function, list or value that determines connection between sources and targets
        self._connector_params = connector_params  # parameters passed into connector
        self._iterator = iterator  # rule for iterating between sources and targets
        self._edge_type_properties = edge_type_properties

        self._params = []

    @property
    def params(self):
        return self._params

    @property
    def source_nodes(self):
        return self._source_nodes

    @property
    def target_nodes(self):
        return self._target_nodes

    @property
    def connector(self):
        return self._connector

    @property
    def connector_params(self):
        return self._connector_params

    @property
    def iterator(self):
        return self._iterator

    @property
    def edge_type_properties(self):
        return self._edge_type_properties or {}

    @property
    def edge_type_id(self):
        # TODO: properly implement edge_type
        return self._edge_type_properties['node_type_id']

    def add_properties(self, names, rule, rule_params=None, dtypes=None):
        """A a synaptic property

        :param names: list, or single string, of the property
        :param rule: function, list or value of property
        :param rule_params: when rule is a function, rule_params will be passed into function when called.
        :param dtypes: expected property type
        """
        self._params.append(self.ParamsRules(names, rule, rule_params, dtypes))

    def connection_itr(self):
        """Returns a generator that will iterate through the source/target pairs (as specified by the iterator function,
        and create a connection rule based on the connector.
        """
        conr = connector.create(self.connector, **(self.connector_params or {}))
        itr = iterator.create(self.iterator, conr, **({}))
        return itr(self.source_nodes, self.target_nodes, conr)
