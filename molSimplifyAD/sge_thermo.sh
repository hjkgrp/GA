#$ -S bin/bash		#shell
#$ -l h_rt=24:00:00	#runtime max
#$ -l h_rss=8G		#memory req
#$ -q gpus|gpusnew	        #gpus
#$ -l gpus=1            #
#$ -pe smp 1 		#number parrallel jobs
#$ -cwd

module load cuda/8.0
module load intel/16.0.109
module load OpenMM/7.1.1
module load mpich2/1.4.1p1
export LD_LIBRARY_PATH=/opt/terachem/120318-cuda8-intel16/lib:$LD_LIBRARY_PATH
export TeraChem=/opt/terachem/120318-cuda8-intel16
export NBOEXE=/opt/terachem/120318-cuda8-intel16/nbo6/bin/nbo6.i4.exe
export PATH=/opt/terachem/120318-cuda8-intel16:$PATH
export PATH=/opt/terachem/120318-cuda8-intel16/bin:$PATH


fullpath="$1"

echo "full path is $fullpath"
generalpath=`echo $(dirname $fullpath) | sed "s,/*[^/]\*$,,"`
#echo "gen path is $generalpath"

gennumpath=$(basename $generalpath)
#echo "gen path is $generalpath"

generalpath=`echo $(dirname $generalpath) | sed "s,/*[^/]\*$,,"`
#echo "gen path is $generalpath"

generalpath=`echo $(dirname $generalpath) | sed "s,/*[^/]\*$,,"`
echo "gen path is $generalpath"

namebase=`echo $fullpath | sed "s/[.]in//"| sed "s:.*/::"`

echo "Begining calcualtion run"
echo "general path is $generalpath"
export OMP_NUM_THREADS=1
echo "gen path  $generalpath "
echo " gen num path $gennumpath"
echo "base name is  $namebase "
sourcepath=$fullpath
inpath=$generalpath/thermo_infiles/$gennumpath/$namebase.in
outpath=$generalpath/thermo_outfiles/$gennumpath/$namebase.out
scrpath=$generalpath/scr/thermo/$gennumpath/
echo "scr will be copied to  $scrpath"
echo "paths set"
## set local, workdir related paths and copy files
localoutpath=$namebase.out
echo "begining"
echo "file is  $namebase"
echo "this current home: $HOME"
echo "this current SGE_JOB_SPOOL_DIR: $SGE_JOB_SPOOL_DIR"
echo "this SGE WORKDIR: $SGE_O_WORKDIR"
echo "this SGE_O_PATH: $SGE_O_PATH"
echo "this SGE shell current DIR: $PWD"

cd $SGE_O_WORKDIR
echo "moved to"
pwd
mkdir -p scr
mkdir -p scr/thermo/$gennumpath
spacer='_'

##begin geo-optimization

echo "Launching thermo calc: $namebase"
terachem $inpath >  $outpath
echo "Complete"
## copy back complete cases 
#mv $localoutpath $outpath
#mv scr/geo/$gennumpath/$namebase $scrpath


