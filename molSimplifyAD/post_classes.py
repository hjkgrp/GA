import glob
import string
import sys
import os,shutil,datetime
import numpy as np
import math
import random
import string
import numpy
import subprocess
from ga_tools import *
from molSimplify.Classes import *
from optgeo_extract import *
from molSimplify.Informatics.autocorrelation import*
from molSimplify.Informatics.misc_descriptors import*
from molSimplify.Informatics.coulomb_analyze import*
from molSimplify.Informatics.graph_analyze import*
from molSimplify.Informatics.geo_analyze import *

########### UNIT CONVERSION

HF_to_Kcal_mol = 627.509###

###########################

class DFTRun:
    """ This is a class for each run"""
    numRuns = 0
    def __init__(self,name):
        self.numRuns += 1
        ## basic info
        self.name = name
        self.status = 'undef'
        self.time = 'undef'
        self.energy = 'undef'
        self.initial_energy = 'undef'
        self.charge = 'undef'
        self.idn = 'undef'
        self.solvent_cont = False
        self.thermo_cont = False
        self.init_energy = False
        self.spin = 'undef'
        self.eqlig_ind = 'undef'
        self.axlig1_ind = 'undef'
        self.axlig2_ind = 'undef'
        self.eqlig = 'undef'
        self.axlig1 = 'undef'
        self.axlig2 = 'undef'
        self.ax1_MLB = 'undef'
        self.ax2_MLB = 'undef'
        self.eq_MLB = 'undef'
        self.init_ax1_MLB = 'undef'
        self.init_ax2_MLB = 'undef'
        self.init_eq_MLB = 'undef'
        ## paths
        self.outpath  = 'undef'
        self.geopath = 'undef'
        self.init_geopath = 'undef'               
        ## diagnositcs
        self.time = 'undef'
        self.logpath = False
        self.attempted  = False
        self.progpath  = 'undef'
        self.converged  = 'undef'
        self.geostatus = False
        self.thermo_status = False
        self.imag = False
        self.rmsd = 'undef'
        self.geo_exists = False
        self.progstatus = False
        self.prog_exists = False
        self.output_exists = False
        self.converged = False 
        self.mop_converged = False 
        self.islive = False
        self.ss_target = 0
        self.ss_act =   0
        self.coord = 0 
        self.maxd = 'undef' #max dist to detect detected atoms
        self.thermo_time = 'undef'
        self.solvent_time = 'undef'
        self.terachem_version = 'undef'
        self.terachem_detailed_version = 'undef'
        self.basis = 'undef'
        self.alpha_level_shift = 'undef'
        self.beta_level_shift = 'undef'
        self.functional = 'undef'
        self.comment = ''
 
        ## mopac statistics
        self.mop_energy = 'undef'
        self.mop_coord = 0
        
        ## descriptors
        self.set_desc = False
        self.descriptors =  list()
        self.descriptor_names =  list()

    def obtain_mopac_mol(self):
        this_mol = mol3D()
        if os.path.exists(self.mop_geopath):
                this_mol.readfromxyz(self.mop_geopath)
                print('looking for mopac mol at ' +self.mop_geopath)
                self.mop_mol = this_mol
    def obtain_mol3d(self):
        this_mol = mol3D()
        if os.path.exists(self.geopath):
                this_mol.readfromxyz(self.geopath)
                print('looking for mol at ' +self.geopath)
        elif  os.path.exists(self.progpath):
                this_mol.readfromxyz(self.progpath)
                print('looking for mol at ' +self.progpath)
        self.mol = this_mol
    def obtain_init_mol3d(self):
        this_mol = mol3D()
        print('looking for init mol at ' +self.init_geopath)
        if os.path.exists(self.init_geopath):
                this_mol.readfromxyz(self.init_geopath)
                print('found  init mol at ' +self.init_geopath)
        self.init_mol = this_mol
    def extract_prog(self):
         self.progstatus = extract_file_check(self.scrpath,self.progpath)
    def extract_geo(self):
         self.geostatus = extract_file_check(self.scrpath,self.geopath)
    def obtain_rsmd(self):
         self.rmsd = self.mol.rmsd(self.init_mol)
    def obtain_ML_dists(self):
        try:
                self.mind = minimum_ML_dist(self.mol)
                self.maxd = maximum_any_dist(self.mol)
                self.meand = mean_ML_dist(self.mol)
                ax_dist,eq_dist = getOctBondDistances(self.mol)
                if len(ax_dist)<2:
                        ax_dist.append(ax_dist[0])
                self.ax1_MLB = np.mean(ax_dist[0])
                self.ax2_MLB = np.mean(ax_dist[1])
                total_eq_distance = 0
                counter  = 0
                for eqligs in eq_dist:
                        for bonds in eqligs:
                                total_eq_distance+=bonds
                                counter += 1
                self.eq_MLB = total_eq_distance/counter
        except: 
                #self.coord = 'error'
                self.eq_MLB = 'error'
                self.ax1_MLB = 'error'
                self.ax2_MLB = 'error'
        try:
                ## get init data if avail
                ax_dist,eq_dist = getOctBondDistances(self.init_mol)
                if len(ax_dist)<2:
                        ax_dist.append(ax_dist[0])
                self.init_ax1_MLB = np.mean(ax_dist[0])
                self.init_ax2_MLB = np.mean(ax_dist[1])
                total_eq_distance = 0
                counter  = 0
                for eqligs in eq_dist:
                        for bonds in eqligs:
                                total_eq_distance+=bonds
                                counter += 1
                self.init_eq_MLB = total_eq_distance/counter
        except:
                #self.init_coord = 'error'
                self.init_eq_MLB = 'error'
                self.init_ax1_MLB = 'error'
                self.init_ax2_MLB = 'error'
        
             
    def configure(self,metal,ox,eqlig,axlig1,axlig2,spin,alpha,spin_cat):
        self.metal = metal
        self.ox = ox
        self.spin = spin
        self.eqlig = eqlig
        self.axlig1 = axlig1
        self.axlig2 = axlig2
        self.spin_cat=spin_cat
        self.alpha=alpha
        
    def test_prog(self):
        ok = False
        natoms = 0
        this_prog_mol = mol3D()
        if  os.path.exists(self.progpath):
            this_prog_mol.readfromxyz(self.progpath)
        try:
            natoms = this_prog_mol.natoms
        except:
            pass
        if natoms >0:
            ok = True
        return(ok)    
    def estimate_if_job_live(self):	
        modtime = os.stat(self.outpath).st_mtime
#        print('opttest modifed on '+ str(modtime))
        print('age is '+ str((time.time() - modtime)))
        if (time.time() - modtime) >= 1000:
            return(False)
        else:
            return(True)
    def check_coordination(self):
        try:
            this_metal = self.mol.findMetal()[0]
            these_neighbours = self.mol.getBondedAtomsOct(this_metal)
            self.coord = len(these_neighbours)	
        except:
            self.coord = 0
        try:
            this_metal = self.mop_mol.findMetal()[0]
            these_neighbours = self.mop_mol.getBondedAtomsOct(this_metal)
            self.mop_coord = len(these_neighbours)	
        except:
            self.mop_coord = 0
        try:
            this_metal = self.init_mol.findMetal()[0]
            these_neighbours = self.init_mol.getBondedAtomsOct(this_metal)
            self.init_coord = len(these_neighbours)	
        except:
            self.init_coord = 0
    def write_new_inputs(self):
        path_dictionary = setup_paths()
        guess_string = 'guess ' + get_run_dir() + 'scr/geo/' +self.name + '/ca0'+ ' '+ get_run_dir() + 'scr/geo/' +self.name + '/cb0'
        self.thermo_inpath = path_dictionary['thermo_infiles'] + self.name + '.in'
        self.solvent_inpath =path_dictionary['solvent_infiles'] + self.name + '.in'  
        self.init_sp_inpath =path_dictionary['sp_infiles']  + self.name + '.in'
        ### check thermo
        if not os.path.exists(self.thermo_inpath):
            f_thermo = open(self.thermo_inpath,'w')
            f_thermo.write('run frequencies \n')
            f_thermo.write('coordinates '+self.geopath + ' \n')
            f_thermo.write('scrdir scr/thermo/  \n')
            f_thermo.write(guess_string)
            with open(self.inpath,'r') as ref:
                for line in ref:
                     if not ("coordinates" in line) and (not "end" in line) and not ("scrdir" in line) and not("run" in line) and not ("maxit" in line) and not ("new_minimizer" in line):
                     ## these lines should be common 
                        f_thermo.write(line)
            f_thermo.write('end')
            f_thermo.close()
        ### check init SP
        if not os.path.exists(self.init_sp_inpath):
            f_insp = open(self.init_sp_inpath,'w')
            ## write solvent
            f_insp.write('run energy \n') 
            f_insp.write('scrdir scr/init_sp/  \n')
            f_insp.write('coordinates '+self.init_geopath + ' \n')
            f_insp.write('guess ' + get_run_dir() + 'scr/geo/' +self.name + '/ca0'+ ' '+ get_run_dir() + 'scr/geo/' +self.name + '/cb0')
            with open(self.inpath,'r') as ref:
                for line in ref:
                    if not ("coordinates" in line) and (not "end" in line) and not ("scrdir" in line) and not("run" in line) and not ("maxit" in line) and not ("new_minimizer" in line):
                    ## these lines should be common 
                        f_insp.write(line)
            f_insp.write('end')
            f_insp.close()
           ### check solvent
        if not os.path.exists(self.solvent_inpath):
            f_solvent = open(self.solvent_inpath,'w')
            ## write solvent
            f_solvent.write('run energy \n') 
            f_solvent.write('pcm cosmo \n')
            f_solvent.write('pcm_grid iswig \n')
            f_solvent.write('epsilon 78.39 \n')
            f_solvent.write('pcm_radii read \n')
            f_solvent.write('print_ms yes \n')
            f_solvent.write('pcm_radii_file /home/jp/pcm_radii \n')
            f_solvent.write('scrdir scr/thermo/  \n')
            f_solvent.write('coordinates '+self.geopath + ' \n')
            f_solvent.write(guess_string)
            with open(self.inpath,'r') as ref:
                for line in ref:
                    if not ("coordinates" in line) and (not "end" in line) and not ("scrdir" in line) and not("run" in line) and not ("maxit" in line) and not ("new_minimizer" in line):
                    ## these lines should be common 
                        f_solvent.write(line)
            f_solvent.write('end')
            f_solvent.close()

    def write_HFX_inputs(self):
        path_dictionary = setup_paths()
        guess_string = 'guess ' + get_run_dir() + 'scr/geo/' +self.name + '/ca0'+ ' '+ get_run_dir() + 'scr/geo/' +self.name + '/cb0'
        self.thermo_inpath = path_dictionary['thermo_infiles'] + self.name + '.in'
        ### check thermo
        if not os.path.exists(self.thermo_inpath):
            f_thermo = open(self.thermo_inpath,'w')
            f_thermo.write('run frequencies \n')
            f_thermo.write('coordinates '+self.geopath + ' \n')
            f_thermo.write('scrdir scr/thermo/  \n')
            f_thermo.write(guess_string)
            with open(self.inpath,'r') as ref:
                for line in ref:
                     if not ("coordinates" in line) and (not "end" in line) and not ("scrdir" in line) and not("run" in line) and not ("maxit" in line) and not ("new_minimizer" in line):
                     ## these lines should be common 
                        f_thermo.write(line)
            f_thermo.write('end')
            f_thermo.close()

        
            
    def append_descriptors(self,list_of_names,list_of_props,prefix,suffix):
        for names in list_of_names:
            if hasattr(names, '__iter__'):
                names = ["-".join([prefix,str(i),suffix]) for i in names]
                self.descriptor_names += names
            else:
                names = "-".join([prefix,str(names),suffix])
                self.descriptor_names.append(names)
        for values in list_of_props:
            if hasattr(values, '__iter__'):
                self.descriptors.extend(values)
            else:
                self.descriptors.append(values)
class Comp:
    """ This is a class for each unique composition and configuration"""
    def __init__(self,name):
        self.name = name
        self. gene = "undef"
        self.alpha = 'undef'
        self.time = "undef"
        self.metal= 'undef'
        self.axlig1 = 'undef'
        self.axlig2 = 'undef'
        self.eqlig = 'undef'
        self.axlig1_ind = 'undef'
        self.axlig2_ind = 'undef'
        self.eqlig_ind = 'undef'
        self.convergence =  0
        self.attempted = 0        
        self.repmol = mol3D()
        self.set_desc = False
        self.descriptors =  list()
        self.descriptor_names =  list()
        self.ox2RN = 0;
        self.ox3RN = 0
        ## spins_and_charge
        self.ox_2_HS_spin = 'undef'
        self.ox_2_LS_spin = 'undef'
        self.ox_3_LS_spin = 'undef'
        self.ox_3_HS_spin = 'undef'
        self.ox_2_HS_charge = 'undef'
        self.ox_2_LS_charge = 'undef'
        self.ox_3_LS_charge = 'undef'
        self.ox_3_HS_charge = 'undef'

        ## convergence
        self.ox_2_HS_attempted = False
        self.ox_2_LS_attempted = False
        self.ox_3_LS_attempted = False
        self.ox_3_HS_attempted = False
        self.ox_2_HS_converged = False
        self.ox_2_LS_converged = False
        self.ox_3_LS_converged = False
        self.ox_3_HS_converged = False
        self.ox_2_HS_mop_converged = False
        self.ox_2_LS_mop_converged = False
        self.ox_3_LS_mop_converged = False
        self.ox_3_HS_mop_converged = False
        self.ox_2_HS_time = False
        self.ox_2_LS_time= False
        self.ox_3_LS_time = False
        self.ox_3_HS_time= False
        ## energies
        self.ox_2_HS_energy = 'undef'
        self.ox_2_LS_energy = 'undef'
        self.ox_3_LS_energy = 'undef'
        self.ox_3_HS_energy = 'undef'
        self.ox_2_HS_mop_energy = 'undef'
        self.ox_2_LS_mop_energy = 'undef'
        self.ox_3_LS_mop_energy = 'undef'
        self.ox_3_HS_mop_energy = 'undef'
        ### coords
        self.ox_2_LS_coord  = 'undef'
        self.ox_2_HS_coord  = 'undef'
        self.ox_3_LS_coord  = 'undef'
        self.ox_3_HS_coord  = 'undef'
        self.ox_2_LS_mop_coord  = 'undef'
        self.ox_2_HS_mop_coord  = 'undef'
        self.ox_3_LS_mop_coord  = 'undef'
        self.ox_3_HS_mop_coord  = 'undef'
        ### rmsds
        self.ox_2_LS_rmsd  = 'undef'
        self.ox_2_HS_rmsd  = 'undef'
        self.ox_3_LS_rmsd  = 'undef'
        self.ox_3_HS_rmsd  = 'undef'
        self.ox_2_LS_maxd  = 'undef'
        self.ox_2_HS_maxd  = 'undef'
        self.ox_3_LS_maxd  = 'undef'
        self.ox_3_HS_maxd  = 'undef'
        ### thermo
        self.ox_2_LS_thermo_cont  = 'undef'
        self.ox_2_HS_thermo_cont  = 'undef'
        self.ox_3_LS_thermo_cont  = 'undef'
        self.ox_3_HS_thermo_cont  = 'undef'
        ### imag
        self.ox_2_LS_imag  = 'undef'
        self.ox_2_HS_imag  = 'undef'
        self.ox_3_LS_imag  = 'undef'
        self.ox_3_HS_imag  = 'undef'
        ### solvent
        self.ox_2_LS_solvent_cont  = 'undef'
        self.ox_2_HS_solvent_cont  = 'undef'
        self.ox_3_LS_solvent_cont = 'undef'
        self.ox_3_HS_solvent_cont  = 'undef'
        ### initial
        self.ox_2_LS_init_energy  = 'undef'
        self.ox_2_HS_init_energy  = 'undef'
        self.ox_3_LS_init_energy =  'undef'
        self.ox_3_HS_init_energy  = 'undef'
        ### status
        self.ox_2_LS_status  = 'undef'
        self.ox_2_HS_status  = 'undef'
        self.ox_3_LS_status =  'undef'
        self.ox_3_HS_status  = 'undef'
        self.ox_2_LS_comment  = 'undef'
        self.ox_2_HS_comment  = 'undef'
        self.ox_3_LS_comment =  'undef'
        self.ox_3_HS_comment  = 'undef'
        
        ### MOPAC
        self.mop_convergence = 0
        ### Coulomb
        self.cmmat = list()
        self.cmdescriptor = list()
        ### spin splitting
        self.ox2split = 'undef'
        self.ox3split = 'undef'
        
        ### bond lengths 
        self.ox_3_LS_ax1_MLB = 'undef'
        self.ox_3_HS_ax1_MLB = 'undef'
        self.ox_2_LS_ax1_MLB = 'undef'
        self.ox_2_HS_ax1_MLB = 'undef'
        
        self.ox_3_LS_ax2_MLB = 'undef'
        self.ox_3_HS_ax2_MLB = 'undef'
        self.ox_2_LS_ax2_MLB = 'undef'
        self.ox_2_HS_ax2_MLB = 'undef'
        
        self.ox_3_LS_eq_MLB = 'undef'
        self.ox_3_HS_eq_MLB = 'undef'
        self.ox_2_LS_eq_MLB = 'undef'
        self.ox_2_HS_eq_MLB = 'undef'
        
        ### initial bond lengths
        self.ox_3_LS_init_ax1_MLB = 'undef'
        self.ox_3_HS_init_ax1_MLB = 'undef'
        self.ox_2_LS_init_ax1_MLB = 'undef'
        self.ox_2_HS_init_ax1_MLB = 'undef'
        
        self.ox_3_LS_init_ax2_MLB = 'undef'
        self.ox_3_HS_init_ax2_MLB = 'undef'
        self.ox_2_LS_init_ax2_MLB = 'undef'
        self.ox_2_HS_init_ax2_MLB = 'undef'
        
        self.ox_3_LS_init_eq_MLB = 'undef'
        self.ox_3_HS_init_eq_MLB = 'undef'
        self.ox_2_LS_init_eq_MLB = 'undef'
        self.ox_2_HS_init_eq_MLB = 'undef'

        ### spin contam diag
        self.ox_3_LS_ss_act = 'undef'
        self.ox_3_HS_ss_act = 'undef'
        self.ox_2_LS_ss_act = 'undef'
        self.ox_2_HS_ss_act = 'undef'
        
        self.ox_3_LS_ss_target = 'undef'
        self.ox_3_HS_ss_target = 'undef'
        self.ox_2_LS_ss_target = 'undef'
        self.ox_2_HS_ss_target = 'undef'
        
        ### geopaths
        self.ox_3_LS_geopath = 'undef'
        self.ox_3_HS_geopath = 'undef'
        self.ox_2_LS_geopath = 'undef'
        self.ox_2_HS_geopath = 'undef'

        ### raw spins
        self.ox_3_LS_spin = 'undef'
        self.ox_3_HS_spin= 'undef'
        self.ox_2_LS_spin = 'undef'
        self.ox_2_HS_spin= 'undef'

       ### data provenance 
        self.ox_3_LS_terachem_version = 'undef'
        self.ox_3_HS_terachem_version = 'undef'
        self.ox_2_LS_terachem_version = 'undef'
        self.ox_2_HS_terachem_version = 'undef'
        self.ox_3_LS_terachem_detailed_version = 'undef'
        self.ox_3_HS_terachem_detailed_version = 'undef'
        self.ox_2_LS_terachem_detailed_version = 'undef'
        self.ox_2_HS_terachem_detailed_version = 'undef'
        self.ox_3_LS_basis = 'undef'
        self.ox_3_HS_basis = 'undef'
        self.ox_2_LS_basis = 'undef'
        self.ox_2_HS_basis = 'undef'
        self.ox_3_LS_functional = 'undef'
        self.ox_3_HS_functional = 'undef'
        self.ox_2_LS_functional = 'undef'
        self.ox_2_HS_functional = 'undef'
        self.ox_3_LS_alpha_level_shift = 'undef'
        self.ox_3_HS_alpha_level_shift = 'undef'
        self.ox_2_LS_alpha_level_shift = 'undef'
        self.ox_2_HS_alpha_level_shift= 'undef'

        self.ox_3_LS_beta_level_shift = 'undef'
        self.ox_3_HS_beta_level_shift = 'undef'
        self.ox_2_LS_beta_level_shift = 'undef'
        self.ox_2_HS_beta_level_shift= 'undef'

    def set_properties(self,this_run):
        self.metal = this_run.metal
        self.axlig1 = this_run.axlig1
        self.axlig2 = this_run.axlig2
        self.eqlig = this_run.eqlig
        self.axlig1_ind = this_run.axlig1_ind
        self.axlig2_ind = this_run.axlig2_ind
        self.eqlig_ind = this_run.eqlig_ind
        self.alpha =this_run.alpha
    def set_rep_mol(self,this_run):
        self.mol = this_run.mol
    def get_descriptor_vector(self,loud=False,name=False):
        results_dictionary = generate_all_ligand_misc(self.mol,loud)
        self.append_descriptors(results_dictionary['colnames'],results_dictionary['result_ax'],'misc','ax')
        self.append_descriptors(results_dictionary['colnames'],results_dictionary['result_eq'],'misc','eq')
        results_dictionary = generate_all_ligand_autocorrelations(self.mol,depth=3,loud=True,name=name)
        self.append_descriptors(results_dictionary['colnames'],results_dictionary['result_ax_full'],'f','ax')
        self.append_descriptors(results_dictionary['colnames'],results_dictionary['result_eq_full'],'f','eq')
        self.append_descriptors(results_dictionary['colnames'],results_dictionary['result_ax_con'],'lc','ax')
        self.append_descriptors(results_dictionary['colnames'],results_dictionary['result_eq_con'],'lc','eq')
        results_dictionary = generate_metal_autocorrelations(self.mol,depth=3,loud=loud)
        self.append_descriptors(results_dictionary['colnames'],results_dictionary['results'],'mc','all')
        results_dictionary = generate_full_complex_autocorrelations(self.mol,depth=3,loud=loud)
        self.append_descriptors(results_dictionary['colnames'],results_dictionary['results'],'f','all')
        ### delta metrics 
        results_dictionary = generate_all_ligand_deltametrics(self.mol,depth=3,loud=True,name=name)
        self.append_descriptors(results_dictionary['colnames'],results_dictionary['result_ax_con'],'D_lc','ax')
        self.append_descriptors(results_dictionary['colnames'],results_dictionary['result_eq_con'],'D_lc','eq')
        results_dictionary = generate_metal_deltametrics(self.mol,depth=3,loud=loud)
        self.append_descriptors(results_dictionary['colnames'],results_dictionary['results'],'D_mc','all')
        self.set_desc = True
    def append_descriptors(self,list_of_names,list_of_props,prefix,suffix):
        for names in list_of_names:
            if hasattr(names, '__iter__'):
                names = ["-".join([prefix,str(i),suffix]) for i in names]
                self.descriptor_names += names
            else:
                names = "-".join([prefix,str(names),suffix])
                self.descriptor_names.append(names)
        for values in list_of_props:
            if hasattr(values, '__iter__'):
                self.descriptors.extend(values)
            else:
                self.descriptors.append(values)
    def get_ox2_split(self):
		self.ox2split = float(self.ox_2_HS_energy) - float(self.ox_2_LS_energy)  
    def get_coulomb_descriptor(self,size):
		self.cmol = pad_mol(self.mol,size)
		self.cmmat = create_columb_matrix(self.cmol)
		w, v = np.linalg.eig(self.cmmat)
		self.cmdescriptor = list(w)

    def process(self):
        self.split = str((float(self.HS_energy) - float(self.LS_energy))*HF_to_Kcal_mol)
