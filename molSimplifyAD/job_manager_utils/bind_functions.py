import os
import glob
import numpy as np
from molSimplify.job_manager.classes import textfile
from molSimplify.job_manager.manager_io import get_scf_progress


def bind_direct(this_run, jobname, basedir, case, keyinout, suffix=''):
    case_attr = case + suffix
    setattr(this_run, case_attr, False)
    outfile = basedir + "/" + "%s_%s" % (jobname, case) + "/" + "%s_%s.out" % (
        jobname, case)  ## we know the name of outfile
    if os.path.isfile(outfile):
        setattr(this_run, case_attr, np.nan)
        output = textfile(outfile)
        v = output.wordgrab([keyinout[0]], [keyinout[1]], last_line=True)[0]
        if not v == None:
            setattr(this_run, case_attr, v)


def bind_with_search(this_run, jobname, basedir, case, keyinout, ref=False):
    setattr(this_run, case, False)
    search_dir = basedir + "/" + "%s_%s" % (jobname, case)
    if os.path.isdir(search_dir):
        setattr(this_run, case, dict())
        for dirpath, dirs, files in os.walk(search_dir):
            for file in sorted(files):
                if file.split('.')[-1] == 'out' and not any(
                        "_v%d.out" % x in file for x in range(10)):  # search for outfiles
                    outfile = dirpath + '/' + file
                    # key = file.strip('out').strip(jobname).strip('.')
                    key = dirpath.split('/')[-1]
                    output = textfile(outfile)
                    energy = output.wordgrab([keyinout[0]], [keyinout[1]], last_line=True)[0]
                    is_oscalliting_scf = get_scf_progress(outfile)
                    if not is_oscalliting_scf:
                        if isinstance(energy, str):
                            energy = float(energy.split(':')[-1])
                        if not ref:
                            if not energy == None:
                                getattr(this_run, case).update({key: energy})
                            else:
                                getattr(this_run, case).update({key: False})
                        else:
                            if not energy == None:
                                getattr(this_run, case).update({key: energy - (this_run.energy)})
                            else:
                                getattr(this_run, case).update({key: False})
                    else:
                        print("oscillaing scf: ", outfile)
                        getattr(this_run, case).update({key: np.nan})


def bind_water(this_run, jobname, basedir):
    bind_direct(this_run, jobname, basedir,
                case='water',
                keyinout=['C-PCM contribution to final energy:', -2],
                suffix='_cont')


def bind_thermo(this_run, jobname, basedir):
    bind_direct(this_run, jobname, basedir,
                case='thermo',
                keyinout=['Thermal vibrational energy (ZPE + <E>)', -2],
                suffix='_cont')


def bind_solvent(this_run, jobname, basedir):
    bind_with_search(this_run, jobname, basedir,
                     case="solvent",
                     keyinout=['C-PCM contribution to final energy:', 4],
                     ref=False)


def bind_vertIP(this_run, jobname, basedir):
    bind_with_search(this_run, jobname, basedir,
                     case="vertIP",
                     keyinout=['FINAL ENERGY:', -2],
                     ref=True)


def bind_vertEA(this_run, jobname, basedir):
    bind_with_search(this_run, jobname, basedir,
                     case="vertEA",
                     keyinout=['FINAL ENERGY:', -2],
                     ref=True)


def bind_functionals(this_run, jobname, basedir):
    bind_with_search(this_run, jobname, basedir,
                     case="functionalsSP",
                     keyinout=['FINAL ENERGY:', -2],
                     ref=True)


def bind_ligdissociate(this_run, jobname, basedir):
    bind_with_search(this_run, jobname, basedir,
                     case="dissociation",
                     keyinout=['FINAL ENERGY:', -2],
                     ref=False)
