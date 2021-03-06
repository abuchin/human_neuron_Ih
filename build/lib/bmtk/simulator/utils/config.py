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
import os
import json
import shutil
import re
import copy


def from_json(config_file, validator=None):
    """Builds and validates a configuration json file.

    :param config_file: File object or path to a json file.
    :param validator: A SimConfigValidator object to validate json file. Won't validate if set to None
    :return: A dictionary, verified against json validator and with manifest variables resolved.
    """
    if isinstance(config_file, file):
        conf = json.load(config_file)
    elif isinstance(config_file, basestring):
        conf = json.load(open(config_file, 'r'))
    else:
        raise Exception('{} is not a file or file path.'.format(config_file))

    # insert file path into dictionary
    if 'config_path' not in conf:
        conf['config_path'] = os.path.abspath(config_file)

    # Will resolve manifest variables and validate
    return from_dict(conf, validator)


def from_dict(config_dict, validator=None):
    """Builds and validates a configuration json dictionary object. Best to directly use from_json when possible.

    :param config_dict: Dictionary object
    :param validator: A SimConfigValidator object to validate json file. Won't validate if set to None
    :return: A dictionary, verified against json validator and with manifest variables resolved.
    """
    assert(isinstance(config_dict, dict))
    conf = copy.deepcopy(config_dict) # Since the functions will mutate the dictionary we will copy just-in-case.

    if 'config_path' not in conf:
        conf['config_path'] = os.path.abspath(__file__)

    # Build the manifest and resolve variables.
    # TODO: Check that manifest exists
    manifest = __build_manifest(conf)
    conf['manifest'] = manifest
    __recursive_insert(conf, manifest)

    # In our work with Blue-Brain it was agreed that 'network' and 'simulator' parts of config may be split up into
    # separate files. If this is the case we build each sub-file separately and merge into this one
    for childconfig in ['network', 'simulation']:
        if childconfig in conf and isinstance(conf[childconfig], basestring):
            # Try to resolve the path of the network/simulation config files. If an absolute path isn't used find
            # the file relative to the current config file. TODO: test if this will work on windows?
            conf_str = conf[childconfig]
            conf_path = conf_str if conf_str.startswith('/') else os.path.join(conf['config_path'], conf_str)

            # Build individual json file and merge into parent.
            child_json = from_json(conf_path)
            del child_json['config_path'] # we don't want 'config_path' of parent being overwritten.
            conf.update(child_json)

    # Run the validator
    if validator is not None:
        validator.validate(conf)

    return conf


def copy_config(conf):
    """Copy configuration file to different directory, with manifest variables resolved.

    :param conf: configuration dictionary
    """
    output_dir = conf["output"]["output_dir"]
    config_name = os.path.basename(conf['config_path'])
    output_path = os.path.join(output_dir, config_name)
    with open(output_path, 'w') as fp:
        json.dump(conf, fp, indent=2)


def __special_variables(conf):
    """A list of preloaded variables to insert into the manifest, containing things like path to run-time directory,
    configuration directory, etc.
    """
    pre_manifest = dict()
    pre_manifest['$workingdir'] = os.path.dirname(os.getcwd())
    if 'config_path' in conf:
        pre_manifest['$configdir'] = os.path.dirname(conf['config_path'])  # path of configuration file
        pre_manifest['$configfname'] = conf['config_path']
    return pre_manifest


def __build_manifest(conf):
    """Resolves the manifest section and resolve any internal variables"""
    if 'manifest' not in conf:
        return __special_variables(conf)

    manifest = conf["manifest"]
    resolved_manifest = __special_variables(conf)
    resolved_keys = set()
    unresolved_keys = set(manifest.keys())

    # No longer using recursion since that can lead to an infinite loop if the person who writes the config file isn't
    # careful. Also added code to allow for ${VAR} format in-case user wants to user "$.../some_${MODEl}_here/..."
    while unresolved_keys:
        for key in unresolved_keys:
            # Find all variables in manifest and see if they can be replaced by the value in resolved_manifest
            value = __find_variables(manifest[key], resolved_manifest)

            # If value no longer has variables, and key-value pair to resolved_manifest and remove from unresolved-keys
            if value.find('$') < 0:
                resolved_manifest[key] = value
                resolved_keys.add(key)

        # remove resolved key-value pairs from set, and make sure at every iteration unresolved_keys shrinks to prevent
        # infinite loops
        n_unresolved = len(unresolved_keys)
        unresolved_keys -= resolved_keys
        if n_unresolved == len(unresolved_keys):
            msg = "Unable to resolve manifest variables: {}".format(unresolved_keys)
            raise Exception(msg)

    return resolved_manifest


def __recursive_insert(json_obj, manifest):
    """Loop through the config and substitute the path variables (e.g.: $MY_DIR) with the values from the manifest

    :param json_obj: A json dictionary object that may contain variables needing to be resolved.
    :param manifest: A dictionary of variable values
    :return: A new json dictionar config file with variables resolved
    """
    if isinstance(json_obj, basestring):
        return __find_variables(json_obj, manifest)

    elif isinstance(json_obj, list):
        new_list = []
        for itm in json_obj:
            new_list.append(__recursive_insert(itm, manifest))
        return new_list

    elif isinstance(json_obj, dict):
        for key, val in json_obj.items():
            if key == 'manifest':
                continue
            json_obj[key] = __recursive_insert(val, manifest)

        return json_obj

    else:
        return json_obj


def __find_variables(json_str, manifest):
    """Replaces variables (i.e. $VAR, ${VAR}) with their values from the manifest.

    :param json_str: a json string that may contain none, one or multiple variable
    :param manifest: dictionary of variable lookup values
    :return: json_str with resolved variables. Won't resolve variables that don't exist in manifest.
    """
    variables = [m for m in re.finditer('\$\{?[\w]+\}?', json_str)]
    for var in variables:
        var_lookup = var.group()
        if var_lookup.startswith('${') and var_lookup.endswith('}'):
            # replace ${VAR} with $VAR
            var_lookup = "$" + var_lookup[2:-1]
        if var_lookup in manifest:
            json_str = json_str.replace(var.group(), manifest[var_lookup])

    return json_str



