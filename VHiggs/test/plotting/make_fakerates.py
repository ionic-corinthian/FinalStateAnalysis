#!/usr/bin/env python

'''

Make a .C ROOT Macro file with C++ versions of the different fake rate
functions.

Reads the input parameters from fake_rates.json, which is produced by
combineFakeRates.py

Author: Evan K. Friis, UW Madison

'''

import json
import logging
import sys
import FinalStateAnalysis.Utilities.CppTools as cpp

log = logging.getLogger("make_fakerates")
h1 = logging.StreamHandler(sys.stdout)
h1.level = logging.INFO
log.addHandler(h1)

# Make the class name easier to write
Bins = cpp.CppKinematicBinning
Func = cpp.CppFunctionWrapper

log.info("Loading fake rate definitions from fake_rates.json")
fake_rate_file = open('fake_rates.json', 'r')
fake_rates = json.load(fake_rate_file)

log.info("Writing fake rate macros to fake_rates.C")
macro_file = open('fake_rates.C', 'w')

macro_file.write('''
// Fake rate functions used to weight events in the VH analysis.
// This file auto-generated by make_fakerates.py
#include "TMath.h"
#include <iostream>

''')

# Keep track of all the fake rate functions we make so we can build a weight
# function
built_functions = []

# Some fake rates are split by barrel and endcap
# Figure out the list of fake rates to make
fr_to_make_noeta = set([])
fr_to_make_eta = set([])
for fr in fake_rates.keys():
    log.info("Parsing raw fake rate %s", fr)
    if 'barrel' in fr or 'endcap' in fr:
        log.info("Found eta dependent rate %s", fr.split('_')[0])
        fr_to_make_eta.add(fr.split('_')[0])
    else:
        log.info("Found eta independent rate %s", fr)
        fr_to_make_noeta.add(fr)

# Make non-eta dependent fake rates (additionally the ones w/ no kinematic dep)
for fr in fr_to_make_noeta:
    fr_info = fake_rates[fr]
    fitted_func = fr_info['fitted_func']
    log.info("Defining independent fake rate: %s = %s", fr, fitted_func)
    function = Func(
        'fakerate_' + fr,
        '    return %s;\n' % fitted_func.replace('VAR', 'pt'),
        'pt', 'eta', unused=['eta'])
    macro_file.write(str(function) + '\n')
    built_functions.append(fr)
    # Make the same fake rate but w/o any pt dependence
    flat_func = Func(
        'fakerate_' + fr + '_flat',
        '    return %f;\n' % fr_info['combined_eff'],
        'pt', 'eta', unused=['pt', 'eta'])
    macro_file.write(str(flat_func) + '\n')
    built_functions.append(fr + '_flat')

for fr in fr_to_make_eta:
    fr_info_barrel = fake_rates[fr + '_barrel']
    fr_info_endcap = fake_rates[fr + '_endcap']
    fitted_func_barrel = fr_info_barrel['fitted_func']
    fitted_func_endcap = fr_info_endcap['fitted_func']
    log.info("Defining barrel fake rate: %s = %s", fr, fitted_func_barrel)
    log.info("Defining endcap fake rate: %s = %s", fr, fitted_func_endcap)
    function = Func(
        'fakerate_' + fr + '_eta',
        Bins([('eta', None, 1.44,
               ' '*10 + 'return ' + fitted_func_barrel.replace('VAR', 'pt') + ';\n'),
              ('eta', 1.44, None,
               ' '*10 + 'return ' + fitted_func_endcap.replace('VAR', 'pt') + ';\n')],
            indent=1),
        'pt', 'eta',
        default=-999,
        warn='std::cerr << "Warning out of bounds in function {name}" << std::endl;\n',
    )
    macro_file.write(str(function) + '\n')
    built_functions.append(fr + '_eta')

    # Make the same fake rate but w/o any pt dependence
    flat_func = Func(
        'fakerate_' + fr + '_eta_flat',
        Bins([('eta', None, 1.44,
               #' '*10 + ('return %f;\n' % fr_info_barrel['combined_eff'])
               fr_info_barrel['combined_eff']
              ),
              ('eta', 1.44, None,
               #' '*10 + ('return %f;\n'  % fr_info_endcap['combined_eff'])
               fr_info_endcap['combined_eff']
              )],
            indent=1),
        'pt', 'eta', unused=['pt'],
        default=-999,
        warn='std::cerr << "Warning out of bounds in function {name}" << std::endl;\n',
    )
    macro_file.write(str(flat_func) + '\n')
    built_functions.append(fr + '_eta_flat')

# Now build all the weighting functions
macro_file.write('''
// ############################################################################
// Corresponding weight functions #############################################
// ############################################################################
''')

for fr in built_functions:
    # Compute the corrected weight
    template =  '''    float fakerate = fakerate_%s(pt, eta);
    float result = fakerate/(1. - fakerate);
    return result;\n''' % fr
    weight_func = Func(
        'weight_' + fr,
        template,
        'pt', 'eta'
    )
    macro_file.write(str(weight_func) + '\n')
