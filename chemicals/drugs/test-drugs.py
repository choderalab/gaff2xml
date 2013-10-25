#!/usr/bin/env python

import os
import os.path
import tempfile
import sys

from openeye.oechem import *

import amber

def test_molecule(molecule, verbose=True, charge_method=None):
    
    # Get molecule name.
    molecule_name = molecule.GetTitle()
    if verbose: print molecule_name

    # Create temporary directory.
    tmp_path = 'tmp' # DEBUG
    if not os.path.exists(tmp_path): os.makedirs(tmp_path)
    if verbose: print 'temporary directory created in %s' % tmp_path
    cwd = os.getcwd()
    os.chdir(tmp_path)
    
    # Write molecule as Tripos mol2.
    tripos_mol2_filename = molecule_name + '.tripos.mol2'
    ofs = oemolostream(tripos_mol2_filename)
    ofs.SetFormat(OEFormat_MOL2)
    OEWriteMolecule(ofs, molecule)
    ofs.close()

    # AMBER environment
    amberhome_path = os.environ['AMBERHOME']

    # Run Antechamber to generate parameters.
    gaff_mol2_filename = molecule_name + '.gaff.mol2'
    frcmod_filename = molecule_name + '.frcmod'
    cmd = "antechamber -i %s -fi mol2 -o %s -fo mol2 -s 2" % (tripos_mol2_filename, gaff_mol2_filename)
    if charge_method:
        cmd += ' -c %s' % charge_method
    if verbose: print cmd
    output = os.system(cmd)
    if verbose: print output
    cmd = "parmchk -i %s -f mol2 -o %s" % (gaff_mol2_filename, frcmod_filename)
    if verbose: print cmd
    output = os.system(cmd)
    if verbose: print output

    # Run tleap to generate prmtop/inpcrd.
    tleap_input = """
source leaprc.ff99SB
source leaprc.gaff
LIG = loadmol2 %(gaff_mol2_filename)s
check LIG
loadamberparams %(molecule_name)s.frcmod
saveoff LIG %(molecule_name)s.lib
saveamberparm LIG %(molecule_name)s.prmtop %(molecule_name)s.inpcrd
quit

""" % vars()
    leap_input_filename = 'leap.in'
    outfile = open(leap_input_filename, 'w')
    outfile.writelines(tleap_input)
    outfile.close()
    cmd = "tleap -f %s " % leap_input_filename
    output = os.system(cmd)
    if verbose: print output

    # Generate ffxml file.
    amber_parser = amber.AmberParser()
    gaff_dat_filename = os.path.join(amberhome_path, 'dat', 'leap', 'parm', 'gaff.dat')
    print gaff_dat_filename
    amber_parser.parse_filenames(gaff_dat_filename)
    amber_parser.parse_filenames(gaff_mol2_filename)
    amber_parser.parse_filenames(frcmod_filename)
    amber_parser.print_xml() # DEBUG
    if verbose: print cmd
    output = os.system(cmd)
    if verbose: print output
    
    # Restore current working directory.
    os.chdir(cwd)

    return

if __name__ == '__main__':

    # Test downloaded drug database.
    database_filename = 'Zdd.mol2.gz' # mol2 database source
    ifs = oemolistream(database_filename)
    for molecule in ifs.GetOEGraphMols():
        # Test molecule.
        test_molecule(molecule)
        stop # DEBUG
