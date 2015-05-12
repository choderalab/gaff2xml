import mdtraj as md
import tempfile
import logging
from .utils import getoutput

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format="LOG: %(message)s")


# http://ambermd.org/tutorials/advanced/tutorial15/Tutorial2.xhtml
# Run tLEaP with input file:
# $ tleap -f commands.in

TLEAP_TEMPLATE_MIX = """
source leaprc.gaff
%(mol2_section)s
box = loadPdb %(box_filename)s
%(amberparams_section)s
setbox box centers
saveAmberParm box %(prmtop_filename)s %(inpcrd_filename)s
quit
"""


TLEAP_TEMPLATE = """
source leaprc.gaff
loadAmberParams %(amberparams_section)s
peptide = loadMol2 %(mol2_section)s
saveAmberParm peptide %(prmtop_filename)s %(inpcrd_filename)s
quit
"""


#loadmol2_section will look something like this:
#BMI = loadmol2 bmi.mol2
#BF4 = loadmol2 bf4.mol2
#ACN = loadmol2 acn.mol2

#loadamberparams_section looks like this:
#loadamberparams frcmod.bf4
#loadamberparams frcmod.bmi
#loadamberparams frcmod.acn


def build_mixture_prmtop(mol2_filenames, frcmod_filenames, box_filename, prmtop_filename, inpcrd_filename):
    """Create a prmtop and inpcrd from a collection of mol2 and frcmod files
    as well as a single box PDB.  We have used this for setting up
    simulations of neat liquids or binary mixtures.  

    Parameters
    ----------
    mol2_filenames : list(str)
        Filenames of GAFF flavored mol2 files.  Each must contain exactly
        ONE ligand.
    frcmod_filenames : str
        Filename of input GAFF frcmod filenames.
    box_filename : str
        Filename of PDB containing an arbitrary box of the mol2 molecules.
    prmtop_filename : str
        output prmtop filename.  Should have suffix .prmtop
    inpcrd_filename : str
        output inpcrd filename.  Should have suffix .inpcrd

    Returns
    -------
    tleap_commands : str
        The string of commands piped to tleap for building the prmtop 
        and inpcrd files.  This will *already* have been run, but the
        output can be useful for debugging or archival purposes.
        
    Notes
    -----
    This can be easily broken if there are missing, duplicated, or
    inconsistent ligand residue names in your box, mol2, and frcmod files.
    You can use mdtraj to edit the residue names with something like
    this: trj.top.residue(0).name = "L1"
    """
    
    # Check for one residue name per mol2 file and uniqueness between all mol2 files
    all_names = set()
    for filename in mol2_filenames:
        t = md.load(filename)
        names = set([r.name for r in t.top.residues])
        
        if len(names) != 1:
            raise(ValueError("Must have a SINGLE residue name in each mol2 file."))
        
        all_names = all_names.union(list(names))

    if len(all_names) != len(mol2_filenames):
        raise(ValueError("Must have UNIQUE residue names in each mol2 file."))
    
    all_names = [md.load(filename).top.residue(0).name for filename in mol2_filenames]
    
    mol2_section = "\n".join("%s = loadmol2 %s" % (all_names[k], filename) for k, filename in enumerate(mol2_filenames))
    amberparams_section = "\n".join("loadamberparams %s" % (filename) for k, filename in enumerate(frcmod_filenames))

    tleap_commands = TLEAP_TEMPLATE_MIX % dict(mol2_section=mol2_section, amberparams_section=amberparams_section, box_filename=box_filename, prmtop_filename=prmtop_filename, inpcrd_filename=inpcrd_filename)
    print(tleap_commands)
    
    file_handle = tempfile.NamedTemporaryFile('w')  # FYI Py3K defaults to 'wb' mode, which won't work here.
    file_handle.writelines(tleap_commands)
    file_handle.flush()

    cmd = "tleap -f %s " % file_handle.name
    logger.debug(cmd)

    output = getoutput(cmd)
    logger.debug(output)

    file_handle.close()

    return tleap_commands



def build_prmtop(mol2_filename, frcmod_filename, prmtop_filename, inpcrd_filename):
    """Create a prmtop and inpcrd for a molecule from mol2 and frcmod files
       without solvating the molecule

    Parameters
    ----------
    mol2_filename : str
    Filename of GAFF flavored mol2 file.  
    frcmod_filename : str
    Filename of input GAFF frcmod filenames.
    prmtop_filename : str
    output prmtop filename.  Should have suffix .prmtop
    inpcrd_filename : str
    output inpcrd filename.  Should have suffix .inpcrd
        
    Returns
    -------
    tleap_commands : str
    The string of commands piped to tleap for building the prmtop
    and inpcrd files.  This will *already* have been run, but the
    output can be useful for debugging or archival purposes.
        
    Notes
    -----
    This can be easily broken if there are missing, duplicated, or
    inconsistent ligand residue names in the mol2, and frcmod files.
    """

    tleap_commands = TLEAP_TEMPLATE % dict(mol2_section=mol2_filename, amberparams_section=frcmod_filename, prmtop_filename=prmtop_filename, inpcrd_filename=inpcrd_filename)

    file_handle = tempfile.NamedTemporaryFile('w')
    file_handle.writelines(tleap_commands)
    file_handle.flush()


    cmd = "tleap -f %s " % file_handle.name
    logger.debug(cmd)

    output = getoutput(cmd)
    logger.debug(output)
    
    file_handle.close()

    return tleap_commands
