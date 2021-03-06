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
from .. import nrn
from base_schema import CellTypes, PropertySchema as BaseSchema


class PropertySchema(BaseSchema):

    def get_cell_type(self, node_params):
        # TODO: A lookup table may be faster
        model_type = node_params['model_type']
        if model_type == 'biophysical':
            return CellTypes.Biophysical
        elif model_type == 'point_IntFire1':
            return CellTypes.Point
        elif model_type == 'virtual':
            return CellTypes.Virtual
        elif model_type == 'biophysical_adjusted':
            return CellTypes.Biophysical
        else:
            return CellTypes.Unknown

    def get_positions(self, node_params):
        if 'positions' in node_params:
            return node_params['positions']
        else:
            return None

    def get_edge_weight(self, src_node, trg_node, edge):
        # TODO: check to see if weight function is None or non-existant
        return edge['syn_weight']
        #weight_fnc = nrn.py_modules.synaptic_weight(edge['syn_weight'])
        #return weight_fnc(trg_node, src_node, edge)

    def preselected_targets(self):
        return True

    def target_sections(self, edge):
        if 'sec_id' in edge:
            return edge['sec_id']
        return None

    def target_distance(self, edge):
        if 'sec_x' in edge:
            return edge['sec_x']
        return None

    def nsyns(self, edge):
        if 'nsyns' in edge:
            return edge['nsyns']
        return 1

    def get_params_column(self):
        return 'dynamics_params'

    def model_type(self, node):
        return node['model_type']

    """
    @staticmethod
    def load_cell_hobj(node):
        print PropertySchema.model_type(node)
        exit()
        #model_type_str = PropertySchema.model_type_str(node)
        #print model_type_str
        # print node.model_params
        # print model_type_str
        cell_fnc = nrn.py_modules.cell_model(model_type_str)
        return cell_fnc(node)
        #if model_type_str in nrn.py_modules.cell_models:
        #   nrn.py_modules.cell_model()
        # print node.model_params
        #exit()
    """
